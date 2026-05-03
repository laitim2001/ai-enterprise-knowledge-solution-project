"""Index populator — batch POST ChunkRecord docs to Azure AI Search via REST.

Per components/C03-indexing.md §1 + §3 + §5:
- REST API path (no SDK dep) for W2 baseline; SDK swap deferred per C03 §8 todo
- Azure AI Search /docs/index endpoint accepts up to 1000 docs per batch
- Action="mergeOrUpload" — idempotent re-population safe (doc_id key dedup)
- tenacity retry on 429/5xx

Per architecture.md §3.6 the index `ekp-kb-drive-v1` schema field set is the
serialization target; ChunkRecord.to_search_doc() handles the rename
(embedding -> content_vector, embedded_images -> embedded_images_json).
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

from indexing.schemas import ChunkRecord

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
    ) -> IndexUploadResult:
        """Upload records, batching to AZURE_BATCH_LIMIT per request. Returns aggregate."""
        if not records:
            return IndexUploadResult(succeeded=0, failed=0, failed_keys=[])

        succeeded = 0
        failed = 0
        failed_keys: list[str] = []

        for i in range(0, len(records), _AZURE_BATCH_LIMIT):
            batch = records[i : i + _AZURE_BATCH_LIMIT]
            ok_count, fail_count, fail_ids = await self._upload_batch(batch, action)
            succeeded += ok_count
            failed += fail_count
            failed_keys.extend(fail_ids)

        logger.info(
            "index_populate_complete",
            index=self.index_name,
            succeeded=succeeded,
            failed=failed,
            total=len(records),
        )
        return IndexUploadResult(
            succeeded=succeeded, failed=failed, failed_keys=failed_keys,
        )

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
    ) -> tuple[int, int, list[str]]:
        """Single POST /indexes/{name}/docs/index call. Returns (ok, fail, fail_ids)."""
        assert self._client is not None, "use 'async with' to manage populator lifecycle"
        url = f"{self.endpoint}/indexes/{self.index_name}/docs/index?api-version={self.api_version}"
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
            # 4xx (other than 429) = caller error; do not retry, surface immediately
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
