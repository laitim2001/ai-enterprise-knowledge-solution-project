"""ZeroEntropy zerank-1 REST client (per architecture.md §3.2 + W4 D3 F3 shootout).

ZeroEntropy direct API. Procurement = Chris async (non-Azure path).

Endpoint:  POST https://api.zeroentropy.dev/v1/rerank
Auth:      Authorization: Bearer {api_key}
Body:
    {"model": "zerank-1", "query": "...", "documents": [...], "top_n": 5}
Response:
    {"results": [{"index": int, "relevance_score": float}, ...]}

Body schema matches Cohere shape (top_n + results container); only model id
+ host differ. Implementation deliberately mirrors CohereReranker for
predictable W4 shootout comparison.
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

_DEFAULT_ENDPOINT = "https://api.zeroentropy.dev/v1/rerank"


class ZeroEntropyReranker:
    """ZeroEntropy zerank-1 client — direct API."""

    def __init__(
        self,
        api_key: str,
        model: str = "zerank-1",
        timeout_s: float = 10.0,
        endpoint: str = _DEFAULT_ENDPOINT,
    ) -> None:
        self.endpoint = endpoint
        self.api_key = api_key
        self.model = model
        self.timeout_s = timeout_s
        self._client: httpx.AsyncClient | None = None

    async def __aenter__(self) -> ZeroEntropyReranker:
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
        assert self._client is not None, "use 'async with' to manage ZeroEntropyReranker lifecycle"

        documents = [str(h.fields.get("chunk_text", "")) for h in candidates]
        payload = {
            "model": self.model,
            "query": query,
            "documents": documents,
            "top_n": min(top_k, len(candidates)),
        }

        response = await self._client.post(self.endpoint, content=json.dumps(payload))
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
            "zeroentropy_rerank",
            model=self.model,
            candidates_in=len(candidates),
            results_out=len(out),
        )
        return out
