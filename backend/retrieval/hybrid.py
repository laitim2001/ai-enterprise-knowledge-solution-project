"""Azure AI Search hybrid retrieval REST client (per architecture.md §3.1 + components/C04 §1).

W2 baseline: BM25 + vector hybrid via Azure AI Search built-in RRF (no custom fusion).
Filter clause: `enabled eq true` (server-side OData) + client-side post-filter per
ADR-0035 W25 F5 D2 (amended 2026-05-25 per Sev2 BUG-025) — symmetric deboost:
low_value chunks retain with score × image_weight regardless of image presence;
non-low_value unchanged. Closes the `architecture.md §3.5/§3.6` "deboost" spec
wording vs W2 baseline "hard exclude" divergence. The pre-amendment asymmetric
drop branch (low_value+no-image dropped) silently regressed text-only overview/
aggregate queries — see BUG-025 postmortem for assumption-error analysis.

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


def _build_acl_filter(user_principals: list[str] | None) -> str | None:
    """ADR-0066 / W90 P2.2 — fail-open retrieval-layer ACL filter clause (G2/G4).

    `user_principals is None` → None: NO ACL filter applied. This is the BC path
    for callers that don't pass principals (internal tooling, the existing test
    suite, the V4 retrieval-test surface) — retrieval stays unfiltered by ACL. The
    authenticated query pipeline always passes a list (≥ the user's oid), so None
    only happens off that path.

    A list (even empty) → the fail-open OData disjunction::

        (not allowed_principals/any()
         or allowed_principals/any(p: search.in(p, '{principals}', ',')))

    A chunk with EMPTY allowed_principals (indexed before the P2.2 rebuild, or a KB
    with no ACL grant) matches the first disjunct → public (production-preserve
    fail-open, plan §6). A STAMPED chunk matches only when one of the user's
    principals is in its allowed list. An empty `user_principals` list → the second
    disjunct matches nothing, so the user sees only public chunks.
    """
    if user_principals is None:
        return None
    # OData: escape single quotes by doubling. search.in's delimiter is ',' — oid /
    # group keys never contain commas, so the comma-joined list is unambiguous.
    escaped = ",".join(p.replace("'", "''") for p in user_principals)
    return (
        "(not allowed_principals/any()"
        f" or allowed_principals/any(p: search.in(p, '{escaped}', ',')))"
    )


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
    """Post-filter low_value chunks per ADR-0035 W25 F5 D2 (amended 2026-05-25 BUG-025).

    Symmetric deboost (matches architecture.md §3.5 "deboost" spec literal intent
    + §3.6 line 384 amendment):

    - low_value_flag=True → retain with score × image_weight (regardless of
      image presence); spec "deboost" semantics — keep in pool but lower-ranked
    - low_value_flag=False → keep unchanged

    The pre-BUG-025 asymmetric drop branch (low_value+no-image → drop) silently
    regressed text-only overview/aggregate queries on KBs with low_value-flagged
    enumeration sections (e.g. scenario lists). Per ADR-0035 amendment 2026-05-25,
    symmetric deboost closes that regression while preserving the spec intent.

    image_weight ≤ 0 is degenerate (drops all low_value chunks — A/B measurement
    branch); preserved to enable empirical comparison between asymmetric (pre-BUG-025) /
    symmetric (post-BUG-025) / drop-all (degenerate) behaviors.
    """
    if image_weight <= 0:
        return [h for h in hits if not h.fields.get("low_value_flag", False)]

    result: list[HybridSearchHit] = []
    for hit in hits:
        if hit.fields.get("low_value_flag", False):
            result.append(replace(hit, score=hit.score * image_weight))
        else:
            result.append(hit)
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
        use_semantic_ranker: bool = True,
        semantic_config_name: str = "ekp-semantic-config",
    ) -> None:
        self.endpoint = endpoint.rstrip("/")
        self.admin_key = admin_key
        self.index_name = index_name
        self.api_version = api_version
        # Per ADR-0035 W25 F5 D2 — score multiplier for image-bearing
        # low_value chunks during post-filter. Production wired from
        # Settings.retrieval_image_low_value_weight in server.py lifespan.
        self.image_weight = image_weight
        # W42 (ADR-0039) — hybrid mode semantic ranker toggle. True (default) =
        # preserve W2 baseline (queryType="semantic"). False = hybrid drops semantic
        # ranker → BM25 + vector + RRF → Cohere rerank (Free tier 402 bypass).
        # Wired from Settings.hybrid_use_semantic_ranker in server.py lifespan.
        self.use_semantic_ranker = use_semantic_ranker
        self.semantic_config_name = semantic_config_name
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
        user_principals: list[str] | None = None,
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
        # ADR-0066 / W90 P2.2 — context expansion must trim too (else G4 confused
        # deputy leaks via expanded neighbours). None = no-op for BC callers.
        acl_filter = _build_acl_filter(user_principals)
        if acl_filter is not None:
            full_filter = f"{full_filter} and {acl_filter}"

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
    async def fetch_chunks_by_section_path(
        self,
        parent_path: list[str],
        doc_id: str,
        kb_id: str,
        *,
        max_chunks: int = 50,
        user_principals: list[str] | None = None,
    ) -> list[HybridSearchHit]:
        """Fetch all chunks within a doc whose section_path contains every segment in parent_path.

        Per ADR-0037 W26 F2 Parent-Document Retrieval — leaf primitive used by
        `backend/generation/parent_doc_retriever.py` to aggregate sibling chunks
        sharing a common parent section. The Azure AI Search index field
        `section_path` is `Collection(Edm.String)` filterable per architecture.md
        §3.6 line 364, so the elementwise existence check uses the OData `any()`
        operator (NOT `search.in()` — that operates on scalar fields only).

        Filter shape::

            kb_id eq '<kb>' and doc_id eq '<doc>' and enabled eq true
              and section_path/any(s: s eq '<seg_1>')
              and section_path/any(s: s eq '<seg_2>')
              ... (one any() clause per parent_path segment)

        Single-quote escaping per OData spec: doubled. Order by `chunk_index asc`
        preserves narrative order so the caller can concat sibling text in
        document order.

        `enabled eq true` baseline preserved per ADR-0035 W25 F5 D2 — low_value
        siblings are NOT filtered here (their inclusion in a parent section is
        a content-aggregation concern, not a retrieval-candidacy concern;
        caller decides via the post-filter applied earlier in the pipeline).

        Returns empty list on empty parent_path or empty doc_id (no API call —
        cost guard). The Tier 1 hard cap `max_chunks=50` per `Settings.
        parent_doc_max_chunks_per_parent` defends against pathological docs
        (a section with 1000+ chunks would explode latency + cost).
        """
        if not parent_path or not doc_id:
            return []
        assert self._client is not None, "use 'async with' to manage searcher lifecycle"

        # ADR-0018: dynamic per-KB index name (Option B b2 dynamic injection)
        index_name = kb_id_to_index_name(kb_id, legacy_default_index=self.index_name)
        kb_filter = kb_id_filter_clause(kb_id)

        # OData escaping — double single quotes (per Azure Search spec)
        escaped_doc = doc_id.replace("'", "''")
        section_filters = [
            f"section_path/any(s: s eq '{seg.replace(chr(39), chr(39) + chr(39))}')"
            for seg in parent_path
        ]
        full_filter = " and ".join(
            [
                kb_filter,
                f"doc_id eq '{escaped_doc}'",
                "enabled eq true",
                *section_filters,
            ]
        )
        # ADR-0066 / W90 P2.2 — parent-doc aggregation must trim too (else G4 leaks
        # via sibling chunks pulled by section). None = no-op for BC callers.
        acl_filter = _build_acl_filter(user_principals)
        if acl_filter is not None:
            full_filter = f"{full_filter} and {acl_filter}"

        url = (
            f"{self.endpoint}/indexes/{index_name}"
            f"/docs/search?api-version={self.api_version}"
        )
        # search="*" + filter + orderby = pure filtering retrieval (no BM25/vector
        # ranking) ordered by document narrative position.
        payload: dict[str, Any] = {
            "search": "*",
            "filter": full_filter,
            "orderby": "chunk_index asc",
            "top": max_chunks,
        }

        response = await self._client.post(url, content=json.dumps(payload))

        if response.status_code >= 500 or response.status_code == 429:
            response.raise_for_status()
        if response.status_code != 200:
            response.raise_for_status()

        body = response.json()
        hits: list[HybridSearchHit] = []
        for item in body.get("value", []):
            score = float(item.get("@search.score", 0.0))
            fields = {k: v for k, v in item.items() if not k.startswith("@search.")}
            hits.append(HybridSearchHit(score=score, fields=fields))

        logger.debug(
            "hybrid_fetch_chunks_by_section_path",
            index=index_name,
            kb_id=kb_id,
            doc_id=doc_id,
            parent_path_depth=len(parent_path),
            returned=len(hits),
            cap=max_chunks,
        )
        return hits

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
        user_principals: list[str] | None = None,
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
        # ADR-0066 / W90 P2.2 — AND the fail-open ACL clause (None = no-op for BC
        # callers). Trims chunks the user has no principal for, at the search layer.
        acl_filter = _build_acl_filter(user_principals)
        if acl_filter is not None:
            full_filter = f"{full_filter} and {acl_filter}"

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
        else:  # hybrid — BM25 + vector + RRF
            payload["search"] = query_text
            payload["vectorQueries"] = [vector_query]
            # W42 (ADR-0039) — semantic ranker is opt-out. With it (default), Azure
            # applies its built-in semantic L2 rerank on top of RRF. Without it, the
            # search="text" + vectorQueries combo still triggers Azure's automatic RRF
            # hybrid fusion (queryType defaults to "simple"); Cohere handles L2 rerank
            # downstream. Dropping it avoids the Free tier semantic ranker quota 402.
            if self.use_semantic_ranker:
                payload["queryType"] = "semantic"
                payload["semanticConfiguration"] = self.semantic_config_name

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
    async def list_chunks(
        self,
        kb_id: str,
        doc_id: str,
        top: int = 1000,
        user_principals: list[str] | None = None,
    ) -> list[dict[str, Any]]:
        """W16 F5.1.2 — list all chunks of a doc (kb_id + doc_id filter;
        ordered by chunk_index ascending).

        Returns list[dict] with chunk_id, doc_id, doc_title, doc_format,
        chunk_index, chunk_total, chunk_title, section_path, enabled,
        low_value_flag, embedded_images_json. chunk_text excluded — Beta
        client uses /query for text. Empty filter returns empty list.

        BUG-034 Finding B — doc_id/doc_title/doc_format added to the projection
        so citation post-hoc expansion (which materializes neighbour Citations
        from these dicts via build_citations) carries the document identity. The
        primary reranked-search chunks always had these; the list_chunks-sourced
        aux citations previously came back with empty doc_id → broken pills.
        """
        if not kb_id or not doc_id:
            return []
        assert self._client is not None, "use 'async with' to manage searcher lifecycle"

        index_name = kb_id_to_index_name(kb_id, legacy_default_index=self.index_name)
        kb_filter = kb_id_filter_clause(kb_id)
        # OData escapes single quotes by doubling — defensive against doc_id with quote
        doc_id_escaped = doc_id.replace("'", "''")
        full_filter = f"{kb_filter} and doc_id eq '{doc_id_escaped}'"
        # ADR-0066 / W90 P2.2 — citation expansion pulls a doc's neighbour chunks via
        # this method (citation_expansion.expand_citations); trim them too (else G4
        # leaks). None = no-op for the GET listing routes (P2 = query-path trimming).
        acl_filter = _build_acl_filter(user_principals)
        if acl_filter is not None:
            full_filter = f"{full_filter} and {acl_filter}"

        url = (
            f"{self.endpoint}/indexes/{index_name}"
            f"/docs/search?api-version={self.api_version}"
        )
        payload: dict[str, Any] = {
            "search": "*",
            "filter": full_filter,
            "top": top,
            "select": (
                "chunk_id,doc_id,doc_title,doc_format,"
                "chunk_index,chunk_total,chunk_title,"
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
                # BUG-034 Finding B — document identity so expansion-materialized
                # neighbour citations resolve a real doc (was empty doc_id).
                "doc_id": str(item.get("doc_id", "")),
                "doc_title": str(item.get("doc_title", "")),
                "doc_format": str(item.get("doc_format", "")),
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
