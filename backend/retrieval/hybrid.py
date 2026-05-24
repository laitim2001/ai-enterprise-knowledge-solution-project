"""Azure AI Search hybrid retrieval REST client (per architecture.md §3.1 + components/C04 §1).

W2 baseline: BM25 + vector hybrid via Azure AI Search built-in RRF (no custom fusion).
Filter clause: `enabled eq true` (server-side OData) + client-side post-filter per
ADR-0035 W25 F5 D2 — low_value+image chunks retain with score × image_weight;
low_value+no-image dropped (preserves W2 exclusion for TOC / version-statement style
chunks); non-low_value unchanged. Closes the `architecture.md §3.5/§3.6` "deboost"
spec wording vs W2 baseline "hard exclude" divergence.

W16+ ADR-0018 Phase 3 multi-KB invariant: search() requires kb_id parameter; index_name
dynamically constructed via kb_naming.kb_id_to_index_name (with self.index_name as Tier 1
legacy alias for kb_id="drive_user_manuals"); kb_id eq filter clause prepended to any
caller-supplied filter making per-KB scoping mandatory.

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
from dataclasses import dataclass, replace
from typing import Any, Literal

import httpx
import structlog
from tenacity import (
    retry,
    retry_if_exception_type,
    stop_after_attempt,
    wait_exponential,
)

from storage.kb_naming import kb_id_filter_clause, kb_id_to_index_name

_API_VERSION = "2024-07-01"
# Per ADR-0035 W25 F5 D2 — server-side filter no longer includes
# `low_value_flag eq false`; low_value handling moved to client-side
# post-filter (see _apply_low_value_post_filter). Closes architecture.md
# §3.5/§3.6 "deboost" spec wording vs W2 baseline "hard exclude" divergence.
_DEFAULT_FILTER = "enabled eq true"
# Per ADR-0035 + W25 plan §8 Q5 locked default. Instance override via
# `HybridSearcher(image_weight=...)`; production wired from
# `Settings.retrieval_image_low_value_weight` in `api/server.py` lifespan.
_DEFAULT_IMAGE_WEIGHT = 0.7

logger = structlog.get_logger(__name__)


@dataclass(slots=True, frozen=True)
class HybridSearchHit:
    """One result from /docs/search. score + raw fields dict from index."""

    score: float
    fields: dict[str, Any]


def _apply_low_value_post_filter(
    hits: list[HybridSearchHit],
    *,
    image_weight: float,
) -> list[HybridSearchHit]:
    """Post-filter low_value chunks per ADR-0035 W25 F5 D2.

    Replaces W2 baseline server-side hard-exclude. Per architecture.md
    §3.5 line 258 ("deboost" spec intent) + §3.6 line 384 amendment:

    - low_value_flag=True + embedded_images_json non-empty → retain with
      score × image_weight (image-bearing low_value chunks deboost not drop)
    - low_value_flag=True + no images → drop (preserve W2 exclusion for
      TOC / version-statement style chunks that lack images)
    - low_value_flag=False → keep unchanged

    image_weight ≤ 0 is degenerate (effectively drops all image+low_value
    chunks — handy for A/B measurement); branch explicit to avoid retaining
    zero-score hits in the result list.
    """
    if image_weight <= 0:
        return [h for h in hits if not h.fields.get("low_value_flag", False)]

    result: list[HybridSearchHit] = []
    for hit in hits:
        if not hit.fields.get("low_value_flag", False):
            result.append(hit)
            continue
        images_json = str(hit.fields.get("embedded_images_json", "") or "")
        if images_json.strip() not in ("", "[]"):
            result.append(replace(hit, score=hit.score * image_weight))
    return result


class HybridSearcher:
    """Async REST client for Azure AI Search hybrid (BM25 + vector RRF) query."""

    def __init__(
        self,
        endpoint: str,
        admin_key: str,
        index_name: str,
        api_version: str = _API_VERSION,
        image_weight: float = _DEFAULT_IMAGE_WEIGHT,
    ) -> None:
        self.endpoint = endpoint.rstrip("/")
        self.admin_key = admin_key
        self.index_name = index_name
        self.api_version = api_version
        # Per ADR-0035 W25 F5 D2 — score multiplier for image-bearing
        # low_value chunks during post-filter. Production wired from
        # Settings.retrieval_image_low_value_weight in server.py lifespan.
        self.image_weight = image_weight
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
    async def fetch_by_chunk_ids(
        self,
        chunk_ids: list[str],
        kb_id: str,
    ) -> dict[str, dict[str, Any]]:
        """Batch fetch chunks by chunk_id list (no ranking) per ADR-0020 Context Expander.

        Single Azure AI Search /docs/search call with `search.in()` filter to retrieve
        multiple chunks in one round-trip — minimizes latency overhead vs N parallel
        single-doc lookups. kb_id required per ADR-0018 multi-KB invariant.

        Returns mapping chunk_id → fields dict; only chunks present in the index appear.
        Empty input list returns empty dict (no API call — cost guard).
        """
        if not chunk_ids:
            return {}
        assert self._client is not None, "use 'async with' to manage searcher lifecycle"

        # ADR-0018: dynamic per-KB index name (Option B b2 dynamic injection)
        index_name = kb_id_to_index_name(kb_id, legacy_default_index=self.index_name)

        # ADR-0018: prepend kb_id eq clause + chunk_id batch filter
        kb_filter = kb_id_filter_clause(kb_id)
        chunk_id_filter = f"search.in(chunk_id, '{','.join(chunk_ids)}', ',')"
        full_filter = f"{kb_filter} and {chunk_id_filter}"

        url = (
            f"{self.endpoint}/indexes/{index_name}"
            f"/docs/search?api-version={self.api_version}"
        )
        # search="*" + filter = pure filtering retrieval (no BM25/vector ranking)
        payload: dict[str, Any] = {
            "search": "*",
            "filter": full_filter,
            "top": len(chunk_ids),
        }

        response = await self._client.post(url, content=json.dumps(payload))

        if response.status_code >= 500 or response.status_code == 429:
            response.raise_for_status()
        if response.status_code != 200:
            response.raise_for_status()

        body = response.json()
        result: dict[str, dict[str, Any]] = {}
        for item in body.get("value", []):
            chunk_id = str(item.get("chunk_id", ""))
            if not chunk_id:
                continue
            fields = {k: v for k, v in item.items() if not k.startswith("@search.")}
            result[chunk_id] = fields

        logger.debug(
            "hybrid_fetch_by_chunk_ids",
            index=index_name,
            kb_id=kb_id,
            requested=len(chunk_ids),
            returned=len(result),
        )
        return result

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
        kb_id: str,
        top_k: int = 50,
        filter_clause: str | None = _DEFAULT_FILTER,
        mode: Literal["hybrid", "vector", "fulltext"] = "hybrid",
    ) -> list[HybridSearchHit]:
        """Retrieval — `mode` selects BM25 / vector / hybrid (per ADR-0021).

        - `mode="hybrid"` (default, unchanged): BM25 (`search`) + vector (`vectorQueries`)
          → built-in RRF, with `queryType="semantic"` + `semanticConfiguration` rerank.
        - `mode="vector"`: vector-only similarity search (`search="*"` so BM25 contributes
          nothing; no semantic config — the semantic ranker needs a text query).
        - `mode="fulltext"`: BM25-only keyword search (`queryType="simple"`; no vector
          query, no semantic rerank). `query_vector` is ignored.

        kb_id required per ADR-0018 multi-KB invariant — index_name dynamically
        constructed via kb_naming.kb_id_to_index_name with self.index_name as Tier 1
        legacy alias for kb_id="drive_user_manuals". Per-KB filter clause prepended
        making kb_id scoping mandatory on every search call.
        """
        assert self._client is not None, "use 'async with' to manage searcher lifecycle"

        # ADR-0018: dynamic per-KB index name (Option B b2 dynamic injection)
        index_name = kb_id_to_index_name(kb_id, legacy_default_index=self.index_name)

        # ADR-0018: prepend kb_id eq clause to filter (multi-KB scoping mandatory)
        kb_filter = kb_id_filter_clause(kb_id)
        full_filter = f"{kb_filter} and {filter_clause}" if filter_clause else kb_filter

        url = (
            f"{self.endpoint}/indexes/{index_name}"
            f"/docs/search?api-version={self.api_version}"
        )
        # ADR-0021: assemble the request payload per retrieval mode.
        payload: dict[str, Any] = {"top": top_k, "filter": full_filter}
        vector_query = {
            "kind": "vector",
            "vector": query_vector,
            "k": top_k,
            "fields": "content_vector",
        }
        if mode == "vector":
            payload["search"] = "*"
            payload["vectorQueries"] = [vector_query]
        elif mode == "fulltext":
            payload["search"] = query_text
            payload["queryType"] = "simple"
        else:  # hybrid — unchanged W2 baseline behavior
            payload["search"] = query_text
            payload["vectorQueries"] = [vector_query]
            payload["queryType"] = "semantic"
            payload["semanticConfiguration"] = "ekp-semantic-config"

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

        # ADR-0035 W25 F5 D2 — client-side post-filter low_value chunks
        # (server-side filter no longer excludes them, see _DEFAULT_FILTER).
        pre_post_count = len(hits)
        hits = _apply_low_value_post_filter(hits, image_weight=self.image_weight)

        logger.debug(
            "hybrid_search_returned",
            index=index_name,
            kb_id=kb_id,
            mode=mode,
            count=len(hits),
            pre_low_value_post_filter_count=pre_post_count,
            image_weight=self.image_weight,
            top_k=top_k,
        )
        return hits

    @retry(
        retry=retry_if_exception_type((httpx.HTTPStatusError, httpx.TransportError)),
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=1, max=8),
        reraise=True,
    )
    async def list_documents(self, kb_id: str, max_chunks: int = 1000) -> list[dict[str, Any]]:
        """W16 F5.1.1 — aggregate doc-level metadata from kb_id-scoped chunks.

        Single Azure AI Search query (search="*" + kb_id filter) returns up to
        max_chunks rows; Python aggregates by doc_id. Beta-scale assumption:
        Tier 1 KB has < 1000 chunks total (W17+ scale needs facet API or
        pagination via $skip/$top per architecture.md §3.4 multi-KB notes).

        Returns list[dict] with doc_id, doc_title, doc_format, total_chunks
        (from chunk_total field), last_indexed_at (max ingested_at observed),
        source_url, tags. Empty kb_id or empty index → empty list.
        """
        if not kb_id:
            return []
        assert self._client is not None, "use 'async with' to manage searcher lifecycle"

        index_name = kb_id_to_index_name(kb_id, legacy_default_index=self.index_name)
        kb_filter = kb_id_filter_clause(kb_id)

        url = (
            f"{self.endpoint}/indexes/{index_name}"
            f"/docs/search?api-version={self.api_version}"
        )
        payload: dict[str, Any] = {
            "search": "*",
            "filter": kb_filter,
            "top": max_chunks,
            "select": (
                "doc_id,doc_title,doc_format,chunk_total,"
                "ingested_at,source_url,tags"
            ),
        }

        response = await self._client.post(url, content=json.dumps(payload))
        if response.status_code >= 500 or response.status_code == 429:
            response.raise_for_status()
        if response.status_code != 200:
            response.raise_for_status()

        body = response.json()
        docs: dict[str, dict[str, Any]] = {}
        for item in body.get("value", []):
            doc_id = str(item.get("doc_id", ""))
            if not doc_id:
                continue
            ingested_at = str(item.get("ingested_at", ""))
            if doc_id not in docs:
                docs[doc_id] = {
                    "doc_id": doc_id,
                    "doc_title": str(item.get("doc_title", "")),
                    "doc_format": str(item.get("doc_format", "")),
                    "total_chunks": int(item.get("chunk_total", 0) or 0),
                    "last_indexed_at": ingested_at,
                    "source_url": item.get("source_url"),
                    "tags": list(item.get("tags") or []),
                }
            elif ingested_at > docs[doc_id]["last_indexed_at"]:
                docs[doc_id]["last_indexed_at"] = ingested_at

        logger.debug(
            "hybrid_list_documents",
            index=index_name,
            kb_id=kb_id,
            docs_count=len(docs),
            chunks_observed=len(body.get("value", [])),
        )
        return list(docs.values())

    @retry(
        retry=retry_if_exception_type((httpx.HTTPStatusError, httpx.TransportError)),
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=1, max=8),
        reraise=True,
    )
    async def list_chunks(self, kb_id: str, doc_id: str, top: int = 1000) -> list[dict[str, Any]]:
        """W16 F5.1.2 — list all chunks of a doc (kb_id + doc_id filter;
        ordered by chunk_index ascending).

        Returns list[dict] with chunk_id, chunk_index, chunk_total, chunk_title,
        section_path, enabled, low_value_flag. chunk_text excluded — Beta
        client uses /query for text. Empty filter returns empty list.
        """
        if not kb_id or not doc_id:
            return []
        assert self._client is not None, "use 'async with' to manage searcher lifecycle"

        index_name = kb_id_to_index_name(kb_id, legacy_default_index=self.index_name)
        kb_filter = kb_id_filter_clause(kb_id)
        # OData escapes single quotes by doubling — defensive against doc_id with quote
        doc_id_escaped = doc_id.replace("'", "''")
        full_filter = f"{kb_filter} and doc_id eq '{doc_id_escaped}'"

        url = (
            f"{self.endpoint}/indexes/{index_name}"
            f"/docs/search?api-version={self.api_version}"
        )
        payload: dict[str, Any] = {
            "search": "*",
            "filter": full_filter,
            "top": top,
            "select": (
                "chunk_id,chunk_index,chunk_total,chunk_title,"
                "section_path,enabled,low_value_flag,embedded_images_json"
            ),
            "orderby": "chunk_index asc",
        }

        response = await self._client.post(url, content=json.dumps(payload))
        if response.status_code >= 500 or response.status_code == 429:
            response.raise_for_status()
        if response.status_code != 200:
            response.raise_for_status()

        body = response.json()
        chunks: list[dict[str, Any]] = []
        for item in body.get("value", []):
            chunks.append({
                "chunk_id": str(item.get("chunk_id", "")),
                "chunk_index": int(item.get("chunk_index", 0) or 0),
                "chunk_total": int(item.get("chunk_total", 0) or 0),
                "chunk_title": str(item.get("chunk_title", "")),
                "section_path": list(item.get("section_path") or []),
                "enabled": bool(item.get("enabled", True)),
                "low_value_flag": bool(item.get("low_value_flag", False)),
                # W20 F5.2 — additive: surfaced for /kb/{id}/images aggregation.
                # JSON string (per index schema §3.6). Empty `[]` when chunk
                # has no images (uploader=None today per R12).
                "embedded_images_json": str(item.get("embedded_images_json") or "[]"),
            })

        logger.debug(
            "hybrid_list_chunks",
            index=index_name,
            kb_id=kb_id,
            doc_id=doc_id,
            chunks_count=len(chunks),
        )
        return chunks
