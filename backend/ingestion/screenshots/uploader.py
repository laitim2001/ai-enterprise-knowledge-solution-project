"""Async Blob uploader for ScreenshotRecord with SHA256 dedup (per architecture.md §4.6).

Uses azure.storage.blob.aio for async uploads. Per architecture.md §3 design decision,
SHA256-based blob path enables cross-document dedup: if two docs reference the same
logo/diagram (same content -> same SHA256 -> same blob_path), only one upload happens.

Container = settings.azure_blob_container_screenshots (single-KB Tier 1 baseline;
Tier 2 multi-tenancy will switch to per-KB containers per architecture.md §3.4).

Local dev: Azurite via connection string from settings (default DefaultEndpointsProtocol=http;
AccountName=devstoreaccount1; ...). Cloud (Beta+): managed identity via DefaultAzureCredential.
"""

from __future__ import annotations

import logging
from dataclasses import dataclass

import structlog
from azure.core.exceptions import ResourceExistsError, ResourceNotFoundError
from azure.storage.blob.aio import BlobServiceClient
from tenacity import retry, retry_if_exception_type, stop_after_attempt, wait_exponential

from ingestion.screenshots.extractor import ScreenshotRecord

logger = structlog.get_logger(__name__)
_stdlib_logger = logging.getLogger(__name__)


@dataclass(slots=True, frozen=True)
class UploadResult:
    """Outcome of a single upload attempt."""

    sha256: str
    blob_url: str
    deduped: bool  # True if blob already existed (skipped upload)
    bytes_uploaded: int  # 0 when deduped


class ScreenshotUploader:
    """Async per-KB screenshot uploader with SHA256 dedup.

    Caller manages lifecycle: `async with ScreenshotUploader(...)` recommended.
    """

    def __init__(
        self,
        connection_string: str,
        container_name: str,
    ) -> None:
        self.connection_string = connection_string
        self.container_name = container_name
        self._client: BlobServiceClient | None = None
        self._container_ensured = False

    async def __aenter__(self) -> ScreenshotUploader:
        self._client = BlobServiceClient.from_connection_string(self.connection_string)
        return self

    async def __aexit__(self, *exc_info: object) -> None:
        if self._client is not None:
            await self._client.close()
            self._client = None

    async def ensure_container(self) -> None:
        """Idempotently ensure container exists. Called automatically on first upload."""
        if self._container_ensured:
            return
        assert self._client is not None, "use 'async with' to manage uploader lifecycle"
        try:
            await self._client.create_container(self.container_name)
            logger.info("blob_container_created", container=self.container_name)
        except ResourceExistsError:
            pass  # already exists - normal
        self._container_ensured = True

    @retry(
        retry=retry_if_exception_type((ConnectionError, TimeoutError)),
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=0.5, min=0.5, max=4),
    )
    async def upload(self, record: ScreenshotRecord) -> UploadResult:
        """Upload one ScreenshotRecord, dedup-skip if blob already exists.

        Returns UploadResult with deduped=True when the blob already existed
        (no bytes transferred); deduped=False when a new upload happened.
        """
        await self.ensure_container()
        assert self._client is not None
        blob_client = self._client.get_blob_client(
            container=self.container_name, blob=record.blob_path,
        )

        # Dedup: HEAD-check via get_blob_properties (cheaper than full GET).
        try:
            await blob_client.get_blob_properties()
            blob_url = blob_client.url
            logger.debug(
                "screenshot_dedup_hit",
                sha256=record.sha256,
                blob_path=record.blob_path,
                kb_id=record.kb_id,
            )
            return UploadResult(
                sha256=record.sha256,
                blob_url=blob_url,
                deduped=True,
                bytes_uploaded=0,
            )
        except ResourceNotFoundError:
            pass  # Blob doesn't exist yet — proceed with upload

        # Upload — overwrite=False because dedup check already confirmed absent;
        # if a race created the blob in between, prefer the earlier write.
        from azure.storage.blob import ContentSettings  # sync import OK; data class only

        await blob_client.upload_blob(
            record.image_bytes,
            overwrite=False,
            content_settings=ContentSettings(content_type=record.content_type),
            metadata={
                "sha256": record.sha256,
                "kb_id": record.kb_id,
                "alt_text_present": "true" if record.alt_text else "false",
            },
        )
        bytes_count = len(record.image_bytes)
        logger.info(
            "screenshot_uploaded",
            sha256=record.sha256,
            blob_path=record.blob_path,
            bytes_count=bytes_count,
            kb_id=record.kb_id,
        )
        return UploadResult(
            sha256=record.sha256,
            blob_url=blob_client.url,
            deduped=False,
            bytes_uploaded=bytes_count,
        )

    async def upload_many(self, records: list[ScreenshotRecord]) -> list[UploadResult]:
        """Upload a batch of records concurrently (preserves caller order in result)."""
        import asyncio

        return await asyncio.gather(*(self.upload(r) for r in records))
