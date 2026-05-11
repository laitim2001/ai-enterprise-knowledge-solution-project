"""Index populator — batch POST ChunkRecord docs to Azure AI Search via REST.

Per components/C03-indexing.md §1 + §3 + §5:
- REST API path (no SDK dep) for W2 baseline; SDK swap deferred per C03 §8 todo
- Azure AI Search /docs/index endpoint accepts up to 1000 docs per batch
- Action="mergeOrUpload" — idempotent re-population safe (doc_id key dedup)
- tenacity retry on 429/5xx

Per architecture.md §3.6 the index `ekp-kb-drive-v1` schema field set is the
serialization target; ChunkRecord.to_search_doc() handles the rename
(embedding -> content_vector, embedded_images -> embedded_images_json).

CH-001 (2026-05-12) — added per-KB index lifecycle + per-doc delete:
- `create_index_for_kb(kb_id)` provisions `ekp-kb-{kb_id}-v1` from schema.json
  (closes ADR-0018 Phase 3 upload-side; the legacy `ekp-kb-drive-v1` was
  manually provisioned at W2 D1 via scripts/create_index.py — same PUT path).
- `delete_index(kb_id)` drops the per-KB index (closes the deferred-W17+
  branch of W16 F5.3 Decision B.1).
- `delete_doc(kb_id, doc_id)` removes all chunks for a doc via search-then-
  batch-delete on the per-KB index.
- `upload(records, kb_id=...)` BC-preserving signature ext — `kb_id` resolves
  via `kb_id_to_index_name`; omitted falls back to `self.index_name` for the
  W2-era callers (scripts/run_populate_sanity.py + W2 tests).
"""

from __future__ import annotations

import json
from dataclasses import dataclass
from functools import lru_cache
from pathlib import Path
from typing import Any, cast

import httpx
import structlog
from tenacity import (
    retry,
    retry_if_exception_type,
    stop_after_attempt,
    wait_exponential,
)

from indexing.schemas import ChunkRecord
from storage.kb_naming import kb_id_filter_clause, kb_id_to_index_name

_API_VERSION = "2024-07-01"
_AZURE_BATCH_LIMIT = 1000  # Azure AI Search /docs/index hard cap per request

logger = structlog.get_logger(__name__)


@dataclass(slots=True, frozen=True)
class IndexUploadResult:
    """Aggregate of one or more batched POST /docs/index calls."""

    succeeded: int
    failed: int
    failed_keys: list[str]  # chunk_ids that returned status != 2xx in batch response


class IndexPopulator:
    """Batch uploader for ChunkRecord -> Azure AI Search index."""

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

    async def __aenter__(self) -> IndexPopulator:
        self._client = httpx.AsyncClient(
            timeout=httpx.Timeout(60.0, connect=10.0),
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

    async def upload(
        self,
        records: list[ChunkRecord],
        action: str = "mergeOrUpload",
        kb_id: str | None = None,
    ) -> IndexUploadResult:
        """Upload records, batching to AZURE_BATCH_LIMIT per request. Returns aggregate.

        `kb_id` (CH-001) — if provided, resolves the target index name via
        `kb_id_to_index_name(kb_id, legacy_default_index=self.index_name)`, so a
        single populator instance can route to any KB's per-KB index. Omitted
        kb_id preserves the W2-era behaviour (targets `self.index_name`); existing
        callers like `scripts/run_populate_sanity.py` keep working unchanged.
        """
        if not records:
            return IndexUploadResult(succeeded=0, failed=0, failed_keys=[])

        target_index = self._resolve_index_name(kb_id)

        succeeded = 0
        failed = 0
        failed_keys: list[str] = []

        for i in range(0, len(records), _AZURE_BATCH_LIMIT):
            batch = records[i : i + _AZURE_BATCH_LIMIT]
            ok_count, fail_count, fail_ids = await self._upload_batch(
                batch, action, index_name=target_index,
            )
            succeeded += ok_count
            failed += fail_count
            failed_keys.extend(fail_ids)

        logger.info(
            "index_populate_complete",
            index=target_index,
            succeeded=succeeded,
            failed=failed,
            total=len(records),
        )
        return IndexUploadResult(
            succeeded=succeeded, failed=failed, failed_keys=failed_keys,
        )

    def _resolve_index_name(self, kb_id: str | None) -> str:
        """CH-001 — per-KB index name resolution with legacy fallback.

        kb_id provided → `ekp-kb-{kb_id}-v1` (or `self.index_name` for the
        legacy `drive_user_manuals` alias per `kb_id_to_index_name`).
        kb_id None → `self.index_name` (W2-era BC default).
        """
        if kb_id is None:
            return self.index_name
        return kb_id_to_index_name(kb_id, legacy_default_index=self.index_name)

    @retry(
        retry=retry_if_exception_type((httpx.HTTPStatusError, httpx.TransportError)),
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=1, max=10),
        reraise=True,
    )
    async def _upload_batch(
        self,
        batch: list[ChunkRecord],
        action: str,
        index_name: str | None = None,
    ) -> tuple[int, int, list[str]]:
        """Single POST /indexes/{name}/docs/index call. Returns (ok, fail, fail_ids)."""
        assert self._client is not None, "use 'async with' to manage populator lifecycle"
        target_index = index_name or self.index_name
        url = f"{self.endpoint}/indexes/{target_index}/docs/index?api-version={self.api_version}"
        payload = {
            "value": [
                {**record.to_search_doc(), "@search.action": action}
                for record in batch
            ],
        }

        response = await self._client.post(url, content=json.dumps(payload))

        # Azure AI Search returns 200 even when partial failures within batch.
        # We must inspect per-doc status in the response body.
        if response.status_code >= 500 or response.status_code == 429:
            response.raise_for_status()  # let tenacity retry

        if response.status_code not in (200, 207):
            # 4xx (other than 429) = caller error; do not retry, surface immediately.
            logger.error(
                "index_upload_4xx",
                status_code=response.status_code,
                body=response.text[:2000],
                batch_size=len(batch),
                first_chunk_id=batch[0].chunk_id if batch else None,
                index=target_index,
            )
            response.raise_for_status()

        body = response.json()
        ok = 0
        fail = 0
        fail_ids: list[str] = []
        for item in body.get("value", []):
            if item.get("status") is True or 200 <= int(item.get("statusCode", 0)) < 300:
                ok += 1
            else:
                fail += 1
                fail_ids.append(item.get("key", "<unknown>"))
                logger.warning(
                    "index_upload_doc_failed",
                    key=item.get("key"),
                    error_message=item.get("errorMessage"),
                )
        return ok, fail, fail_ids

    # ─── CH-001: per-KB index lifecycle ──────────────────────────────────────

    async def create_index_for_kb(self, kb_id: str) -> None:
        """Provision the Azure AI Search index for a KB.

        PUT `/indexes/{name}?api-version=2024-07-01` with the canonical EKP
        chunk-index schema loaded from `backend/indexing/schema.json` (same
        schema the legacy `ekp-kb-drive-v1` was provisioned with at W2 D1 via
        scripts/create_index.py). The schema's `"name"` field is overridden
        with `kb_id_to_index_name(kb_id)` so each KB gets its own index per
        ADR-0018 multi-KB invariant.

        PUT is idempotent — 201 on create-new, 204 on in-place update; both
        treated as success. 4xx (e.g. Azure rejecting a non-conforming kb_id)
        raises `httpx.HTTPStatusError` for the caller to surface as 502.
        """
        assert self._client is not None, "use 'async with' to manage populator lifecycle"
        index_name = self._resolve_index_name(kb_id)
        schema = dict(_load_index_schema())  # shallow copy — only "name" is mutated
        schema["name"] = index_name

        url = f"{self.endpoint}/indexes/{index_name}?api-version={self.api_version}"
        response = await self._client.put(url, content=json.dumps(schema))

        if response.status_code not in (200, 201, 204):
            logger.error(
                "index_create_failed",
                kb_id=kb_id,
                index=index_name,
                status_code=response.status_code,
                body=response.text[:2000],
            )
            response.raise_for_status()

        logger.info("index_created", kb_id=kb_id, index=index_name)

    async def delete_index(self, kb_id: str) -> bool:
        """Drop the Azure AI Search index for a KB.

        DELETE `/indexes/{name}?api-version=2024-07-01`. Returns True on 204
        (deleted), False on 404 (index already gone — fail-soft for pre-CH-001
        legacy KBs or after a partial-create rollback). Raises on other errors.
        """
        assert self._client is not None, "use 'async with' to manage populator lifecycle"
        index_name = self._resolve_index_name(kb_id)
        url = f"{self.endpoint}/indexes/{index_name}?api-version={self.api_version}"
        response = await self._client.delete(url)

        if response.status_code == 204:
            logger.info("index_deleted", kb_id=kb_id, index=index_name)
            return True
        if response.status_code == 404:
            logger.warning("index_already_gone", kb_id=kb_id, index=index_name)
            return False

        logger.error(
            "index_delete_failed",
            kb_id=kb_id,
            index=index_name,
            status_code=response.status_code,
            body=response.text[:2000],
        )
        response.raise_for_status()
        return False  # unreachable — raise_for_status() always raises here

    async def delete_doc(self, kb_id: str, doc_id: str) -> int:
        """Delete all chunks for (kb_id, doc_id) from the per-KB index.

        Two-step against Azure AI Search:
        1. POST /docs/search with filter `kb_id eq X and doc_id eq Y`,
           select=chunk_id, top=1000 — collect the chunk_ids to delete.
        2. POST /docs/index with `@search.action: "delete"` per chunk_id —
           batched the same way as upload().

        Returns the count of chunks deleted. Returns 0 if no chunks matched
        (the route surfaces this as 404 `document.not_found` for clean
        idempotency semantics).
        """
        assert self._client is not None, "use 'async with' to manage populator lifecycle"
        index_name = self._resolve_index_name(kb_id)
        api_version = self.api_version

        # Step 1 — collect chunk_ids matching (kb_id, doc_id). Tier 1 assumption:
        # a single doc has < 1000 chunks (per components/C01-ingestion §4 +
        # HybridSearcher.list_documents `max_chunks=1000` precedent).
        search_url = f"{self.endpoint}/indexes/{index_name}/docs/search?api-version={api_version}"
        filter_clause = f"{kb_id_filter_clause(kb_id)} and doc_id eq '{doc_id}'"
        search_payload = {
            "search": "*",
            "filter": filter_clause,
            "select": "chunk_id",
            "top": _AZURE_BATCH_LIMIT,
        }
        search_response = await self._client.post(search_url, content=json.dumps(search_payload))
        if search_response.status_code == 404:
            # Index doesn't exist (KB never had chunks) — treat as zero matches.
            logger.warning("delete_doc_index_missing", kb_id=kb_id, doc_id=doc_id, index=index_name)
            return 0
        if search_response.status_code != 200:
            logger.error(
                "delete_doc_search_failed",
                kb_id=kb_id,
                doc_id=doc_id,
                status_code=search_response.status_code,
                body=search_response.text[:2000],
            )
            search_response.raise_for_status()

        rows = search_response.json().get("value", [])
        chunk_ids: list[str] = [r["chunk_id"] for r in rows if "chunk_id" in r]
        if not chunk_ids:
            return 0

        # Step 2 — batch-delete by key. Reuse the /docs/index endpoint.
        delete_url = f"{self.endpoint}/indexes/{index_name}/docs/index?api-version={api_version}"
        deleted = 0
        for i in range(0, len(chunk_ids), _AZURE_BATCH_LIMIT):
            batch = chunk_ids[i : i + _AZURE_BATCH_LIMIT]
            payload = {
                "value": [{"chunk_id": chunk_id, "@search.action": "delete"} for chunk_id in batch],
            }
            response = await self._client.post(delete_url, content=json.dumps(payload))
            if response.status_code not in (200, 207):
                logger.error(
                    "delete_doc_index_failed",
                    kb_id=kb_id,
                    doc_id=doc_id,
                    status_code=response.status_code,
                    body=response.text[:2000],
                )
                response.raise_for_status()

            body = response.json()
            for item in body.get("value", []):
                if item.get("status") is True or 200 <= int(item.get("statusCode", 0)) < 300:
                    deleted += 1

        logger.info("doc_chunks_deleted", kb_id=kb_id, doc_id=doc_id, count=deleted)
        return deleted


@lru_cache(maxsize=1)
def _load_index_schema() -> dict[str, Any]:
    """Cache the canonical EKP chunk-index schema (same schema W2 D1 used).

    Read once per process — schema.json is the authoritative shape for any
    per-KB index created via `IndexPopulator.create_index_for_kb`. lru_cache
    makes this a free no-op after the first call.
    """
    schema_path = Path(__file__).resolve().parent / "schema.json"
    return cast("dict[str, Any]", json.loads(schema_path.read_text(encoding="utf-8")))
