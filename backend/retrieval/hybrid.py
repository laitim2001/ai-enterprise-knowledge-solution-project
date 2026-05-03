"""Azure AI Search hybrid retrieval REST client (per architecture.md §3.1 + components/C04 §1).

W2 baseline: BM25 + vector hybrid via Azure AI Search built-in RRF (no custom fusion).
Filter clause: `enabled eq true and low_value_flag eq false` per architecture.md §3.6.

Response shape (Azure AI Search /docs/search):
    {
      "value": [
        {
          "@search.score": 0.7234,
          "chunk_id": "kb-drive_doc-A_chunk-0007",
          ...all retrievable fields per index schema...
        }, ...
      ]
    }
"""

from __future__ import annotations

import json
from dataclasses import dataclass

import httpx
import structlog
from tenacity import (
    retry,
    retry_if_exception_type,
    stop_after_attempt,
    wait_exponential,
)

_API_VERSION = "2024-07-01"
_DEFAULT_FILTER = "enabled eq true and low_value_flag eq false"

logger = structlog.get_logger(__name__)


@dataclass(slots=True, frozen=True)
class HybridSearchHit:
    """One result from /docs/search. score + raw fields dict from index."""

    score: float
    fields: dict


class HybridSearcher:
    """Async REST client for Azure AI Search hybrid (BM25 + vector RRF) query."""

    def __init__(
        self,
        endpoint: str,
        admin_key: str,
        index_name: str,
        api_version: str = _API_VERSION,
    ) -> None:
        self.endpoint = endpoint.rstrip("/")
        self.admin_key = admin_key
        self.index_name = index_name
        self.api_version = api_version
        self._client: httpx.AsyncClient | None = None

    async def __aenter__(self) -> HybridSearcher:
        self._client = httpx.AsyncClient(
            timeout=httpx.Timeout(30.0, connect=10.0),
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
    async def search(
        self,
        query_text: str,
        query_vector: list[float],
        top_k: int = 50,
        filter_clause: str | None = _DEFAULT_FILTER,
    ) -> list[HybridSearchHit]:
        """Hybrid retrieval — BM25 (search) + vector (vectorQueries) → built-in RRF."""
        assert self._client is not None, "use 'async with' to manage searcher lifecycle"
        url = (
            f"{self.endpoint}/indexes/{self.index_name}"
            f"/docs/search?api-version={self.api_version}"
        )
        payload: dict = {
            "search": query_text,
            "vectorQueries": [
                {
                    "kind": "vector",
                    "vector": query_vector,
                    "k": top_k,
                    "fields": "content_vector",
                },
            ],
            "top": top_k,
            "queryType": "semantic",
            "semanticConfiguration": "ekp-semantic-config",
        }
        if filter_clause:
            payload["filter"] = filter_clause

        response = await self._client.post(url, content=json.dumps(payload))

        if response.status_code >= 500 or response.status_code == 429:
            response.raise_for_status()
        if response.status_code != 200:
            response.raise_for_status()

        body = response.json()
        hits: list[HybridSearchHit] = []
        for item in body.get("value", []):
            score = float(item.get("@search.score", 0.0))
            # Strip Azure AI Search system fields; keep all schema fields
            fields = {k: v for k, v in item.items() if not k.startswith("@search.")}
            hits.append(HybridSearchHit(score=score, fields=fields))

        logger.debug(
            "hybrid_search_returned",
            index=self.index_name,
            count=len(hits),
            top_k=top_k,
        )
        return hits
