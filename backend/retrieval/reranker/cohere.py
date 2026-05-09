"""Cohere Rerank v4.0-pro REST client (per architecture.md §3.2 v5.1 + ADR-0012 + Q5 Path A).

Q5 Resolved 2026-05-04 → Path A Azure Marketplace. Q21 Resolved 2026-05-05 →
v3.5 (W3 D1 baseline) → v4.0-pro (W6 production lock per ADR-0012 same-vendor
model upgrade; API contract backward-compatible). Endpoint format:
    POST {endpoint}/v2/rerank
    Authorization: Bearer {api_key}

Path B (direct API api.cohere.com/v2) uses identical body schema; toggle
via factory.py based on `settings.cohere_procurement_path`.

Body:
    {"model": "rerank-v4.0-pro", "query": "...", "documents": [...], "top_n": 5}
Response:
    {"results": [{"index": int, "relevance_score": float}, ...]}

Document text uses `chunk_text` field per `architecture.md §3.6` index schema.
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


class CohereReranker:
    """Cohere Rerank v4.0-pro client — Marketplace (Path A) or direct API (Path B).

    Default model = `rerank-v4.0-pro` per ADR-0012 W6 production lock; `rerank-v3.5`
    accepted for backwards-compat (W3 D1 baseline) but no longer the production default.
    """

    def __init__(
        self,
        endpoint: str,
        api_key: str,
        model: str = "rerank-v4.0-pro",
        timeout_s: float = 10.0,
        path: str = "A",
    ) -> None:
        self.endpoint = endpoint.rstrip("/")
        self.api_key = api_key
        self.model = model
        self.timeout_s = timeout_s
        self.path = path  # "A" Marketplace / "B" direct API — for trace only
        self._client: httpx.AsyncClient | None = None

    async def __aenter__(self) -> CohereReranker:
        self._client = httpx.AsyncClient(
            timeout=httpx.Timeout(self.timeout_s, connect=5.0),
            headers={
                "Authorization": f"Bearer {self.api_key}",
                "Content-Type": "application/json",
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
        assert self._client is not None, "use 'async with' to manage CohereReranker lifecycle"

        documents = [str(h.fields.get("chunk_text", "")) for h in candidates]
        url = f"{self.endpoint}/v2/rerank"
        payload = {
            "model": self.model,
            "query": query,
            "documents": documents,
            "top_n": min(top_k, len(candidates)),
        }

        response = await self._client.post(url, content=json.dumps(payload))
        response.raise_for_status()
        body = response.json()

        results = body.get("results", [])
        out: list[RerankedChunk] = []
        for r in results:
            idx = int(r.get("index", -1))
            if idx < 0 or idx >= len(candidates):
                continue
            hit = candidates[idx]
            out.append(
                RerankedChunk(
                    fields=hit.fields,
                    rerank_score=float(r.get("relevance_score", 0.0)),
                    hybrid_score=float(hit.score),
                    original_index=idx,
                )
            )

        logger.info(
            "cohere_rerank",
            path=self.path,
            model=self.model,
            candidates_in=len(candidates),
            results_out=len(out),
        )
        return out
