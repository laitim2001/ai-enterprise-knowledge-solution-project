"""Azure AI Search built-in semantic ranker (per architecture.md §3.2 + W4 D3 F3 shootout).

Azure semantic ranker is included in the Standard S1 SKU — **no extra
procurement** beyond the existing AI Search resource. Unlike Cohere /
Voyage / ZeroEntropy which rerank an arbitrary candidate list returned
by hybrid search, Azure semantic ranker is invoked **as part of the
search request** via `queryType=semantic` + `semanticConfiguration`. This
reranker therefore re-issues the search request with semantic ranking
enabled and intersects against the candidate ids passed in by
RetrievalEngine — preserving the (RetrievalEngine → reranker) flow and
the Reranker Protocol surface.

Trade-off acknowledged: this incurs a second Azure AI Search call per
query (vs Cohere/Voyage/ZeroEntropy which are pure post-processing of
the original hybrid results). For Tier 1 W4 D3 shootout this is
acceptable — comparison fairness focuses on relevance, and latency is
a secondary metric per Gate 2 criteria. Production-tier Azure semantic
adoption would consolidate hybrid+semantic into a single search call
(removing the post-processor pattern entirely); revisit W5+ if Azure
wins the shootout.

Endpoint format:  POST {endpoint}/indexes/{index}/docs/search?api-version=2024-07-01
Body adds:        {"queryType": "semantic",
                   "semanticConfiguration": "ekp-semantic-default",
                   "queryLanguage": "en-us",
                   "answers": "extractive",
                   "captions": "extractive"}
Response:         each hit has @search.rerankerScore (0..4 scale; clamped to [0, 1] post-divide-by-4 for Reranker Protocol consistency)
"""

from __future__ import annotations

import json

import httpx
import structlog
from tenacity import (
    retry,
    retry_if_exception_type,
    stop_after_attempt,
    wait_exponential,
)

from retrieval.hybrid import HybridSearchHit
from retrieval.reranker.base import RerankedChunk

logger = structlog.get_logger(__name__)

_API_VERSION = "2024-07-01"
# Azure semantic ranker emits scores on a 0-4 scale per docs; we normalise
# to [0, 1] so the Reranker Protocol's rerank_score remains comparable
# across vendors (Gate 2 4-metric within-5pp comparison).
_AZURE_SCORE_DIVISOR = 4.0


class AzureSemanticReranker:
    """Azure AI Search built-in semantic ranker — re-issues search with semantic config."""

    def __init__(
        self,
        endpoint: str,
        admin_key: str,
        index_name: str,
        semantic_config: str = "ekp-semantic-default",
        api_version: str = _API_VERSION,
        timeout_s: float = 10.0,
    ) -> None:
        self.endpoint = endpoint.rstrip("/")
        self.admin_key = admin_key
        self.index_name = index_name
        self.semantic_config = semantic_config
        self.api_version = api_version
        self.timeout_s = timeout_s
        self._client: httpx.AsyncClient | None = None

    async def __aenter__(self) -> AzureSemanticReranker:
        self._client = httpx.AsyncClient(
            timeout=httpx.Timeout(self.timeout_s, connect=5.0),
            headers={
                "Content-Type": "application/json",
                "api-key": self.admin_key,
            },
        )
        return self

    async def __aexit__(self, *exc_info: object) -> None:
        if self._client is not None:
            await self._client.aclose()
            self._client = None

    @retry(
        retry=retry_if_exception_type((httpx.HTTPStatusError, httpx.TransportError)),
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=1, max=8),
        reraise=True,
    )
    async def rerank(
        self,
        query: str,
        candidates: list[HybridSearchHit],
        top_k: int = 5,
    ) -> list[RerankedChunk]:
        if not candidates:
            return []
        assert self._client is not None, "use 'async with' to manage AzureSemanticReranker lifecycle"

        # Filter the semantic search to only the candidate chunk_ids so we
        # re-rank the same set hybrid surfaced (fair comparison vs
        # Cohere/Voyage/ZeroEntropy). Azure odata syntax: `chunk_id eq 'X' or ...`.
        candidate_ids = [str(h.fields.get("chunk_id", "")) for h in candidates]
        # `search.in(chunk_id, 'a,b,c')` is the idiomatic Azure odata multi-value
        # filter (avoids long `or` chains and odata expression length limits).
        id_csv = ",".join(c.replace(",", "_") for c in candidate_ids if c)
        if not id_csv:
            return []

        url = (
            f"{self.endpoint}/indexes/{self.index_name}/docs/search"
            f"?api-version={self.api_version}"
        )
        payload = {
            "search": query,
            "queryType": "semantic",
            "semanticConfiguration": self.semantic_config,
            "queryLanguage": "en-us",
            "filter": f"search.in(chunk_id, '{id_csv}')",
            "top": min(top_k, len(candidates)),
            "select": "chunk_id",
        }

        response = await self._client.post(url, content=json.dumps(payload))
        response.raise_for_status()
        body = response.json()

        # Build chunk_id → original index map for candidate enrichment.
        id_to_idx: dict[str, int] = {
            str(h.fields.get("chunk_id", "")): i for i, h in enumerate(candidates)
        }

        out: list[RerankedChunk] = []
        for hit in body.get("value", []):
            cid = str(hit.get("chunk_id", ""))
            if cid not in id_to_idx:
                continue  # safety: ignore any stray ids outside our candidate set
            idx = id_to_idx[cid]
            raw_score = float(hit.get("@search.rerankerScore", 0.0))
            # Normalise 0-4 → 0-1 to keep rerank_score scale comparable across
            # vendors; clamp defensively if Azure ever returns out-of-range.
            normalised = max(0.0, min(1.0, raw_score / _AZURE_SCORE_DIVISOR))
            original = candidates[idx]
            out.append(
                RerankedChunk(
                    fields=original.fields,
                    rerank_score=normalised,
                    hybrid_score=float(original.score),
                    original_index=idx,
                )
            )

        logger.info(
            "azure_semantic_rerank",
            semantic_config=self.semantic_config,
            candidates_in=len(candidates),
            results_out=len(out),
        )
        return out
