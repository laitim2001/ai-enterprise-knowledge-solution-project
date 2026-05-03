"""Screenshot extractor + uploader unit tests (per CLAUDE.md §5.6 H6 — ingestion is critical).

Uploader tests use AsyncMock for BlobServiceClient since R12 (Azurite signature
incompat) defers live Azurite verification to W7+ cloud deploy phase. Code path
correctness is what unit tests can guarantee.
"""

from __future__ import annotations

import hashlib
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from azure.core.exceptions import ResourceExistsError, ResourceNotFoundError

from ingestion.parsers.base import EmbeddedImage
from ingestion.screenshots.extractor import ScreenshotExtractor, ScreenshotRecord
from ingestion.screenshots.uploader import ScreenshotUploader, UploadResult

_SAMPLE_BYTES = b"\x89PNG\r\n\x1a\n" + b"x" * 60
_SAMPLE_SHA = hashlib.sha256(_SAMPLE_BYTES).hexdigest()


def _make_image(doc_order: int = 0, sha: str | None = None) -> EmbeddedImage:
    return EmbeddedImage(
        image_bytes=_SAMPLE_BYTES,
        alt_text="alt",
        doc_order=doc_order,
        ext="png",
        sha256=sha or _SAMPLE_SHA,
    )


def test_extractor_emits_one_record_per_image_with_sha256_blob_path() -> None:
    images = [_make_image(doc_order=1), _make_image(doc_order=5)]
    records = ScreenshotExtractor.extract(images, kb_id="drive_kb", doc_id="doc-A")
    assert len(records) == 2
    assert records[0].kb_id == "drive_kb"
    assert records[0].doc_id == "doc-A"
    assert records[0].blob_path == f"{_SAMPLE_SHA}.png"
    assert records[0].content_type == "image/png"


def test_extractor_content_type_mapping() -> None:
    img = EmbeddedImage(
        image_bytes=b"\xFF",
        alt_text="",
        doc_order=0,
        ext="jpg",
        sha256="x" * 64,
    )
    [r] = ScreenshotExtractor.extract([img], kb_id="kb", doc_id="d")
    assert r.content_type == "image/jpeg"


def test_extractor_unknown_ext_falls_back_to_octet_stream() -> None:
    img = EmbeddedImage(
        image_bytes=b"\xFF",
        alt_text="",
        doc_order=0,
        ext="weird",
        sha256="x" * 64,
    )
    [r] = ScreenshotExtractor.extract([img], kb_id="kb", doc_id="d")
    assert r.content_type == "application/octet-stream"


def test_extractor_preserves_alt_text_and_doc_order() -> None:
    img = EmbeddedImage(
        image_bytes=_SAMPLE_BYTES,
        alt_text="figure 1: layout diagram",
        doc_order=42,
        ext="png",
        sha256=_SAMPLE_SHA,
    )
    [r] = ScreenshotExtractor.extract([img], kb_id="kb", doc_id="d")
    assert r.alt_text == "figure 1: layout diagram"
    assert r.doc_order == 42


def _make_record() -> ScreenshotRecord:
    return ScreenshotRecord(
        image_bytes=_SAMPLE_BYTES,
        sha256=_SAMPLE_SHA,
        blob_path=f"{_SAMPLE_SHA}.png",
        content_type="image/png",
        alt_text="alt",
        doc_order=0,
        kb_id="kb",
        doc_id="d",
    )


@pytest.mark.asyncio
async def test_uploader_uploads_when_blob_does_not_exist() -> None:
    record = _make_record()

    mock_blob_client = AsyncMock()
    mock_blob_client.get_blob_properties.side_effect = ResourceNotFoundError("not found")
    mock_blob_client.upload_blob = AsyncMock(return_value=None)
    mock_blob_client.url = "http://127.0.0.1:10000/dev/screenshots/abc.png"

    mock_service_client = AsyncMock()
    mock_service_client.get_blob_client = MagicMock(return_value=mock_blob_client)
    mock_service_client.create_container.side_effect = ResourceExistsError("exists")

    with patch(
        "ingestion.screenshots.uploader.BlobServiceClient.from_connection_string",
        return_value=mock_service_client,
    ):
        async with ScreenshotUploader("conn-str", "container") as up:
            result = await up.upload(record)

    assert isinstance(result, UploadResult)
    assert result.deduped is False
    assert result.bytes_uploaded == len(_SAMPLE_BYTES)
    mock_blob_client.upload_blob.assert_awaited_once()


@pytest.mark.asyncio
async def test_uploader_dedup_skips_when_blob_exists() -> None:
    record = _make_record()

    mock_blob_client = AsyncMock()
    # get_blob_properties returns successfully → blob exists → dedup
    mock_blob_client.get_blob_properties = AsyncMock(return_value={"size": 100})
    mock_blob_client.upload_blob = AsyncMock(return_value=None)
    mock_blob_client.url = "http://127.0.0.1:10000/dev/screenshots/abc.png"

    mock_service_client = AsyncMock()
    mock_service_client.get_blob_client = MagicMock(return_value=mock_blob_client)
    mock_service_client.create_container.side_effect = ResourceExistsError("exists")

    with patch(
        "ingestion.screenshots.uploader.BlobServiceClient.from_connection_string",
        return_value=mock_service_client,
    ):
        async with ScreenshotUploader("conn-str", "container") as up:
            result = await up.upload(record)

    assert result.deduped is True
    assert result.bytes_uploaded == 0
    mock_blob_client.upload_blob.assert_not_called()  # dedup → no upload


@pytest.mark.asyncio
async def test_uploader_create_container_idempotent() -> None:
    """ResourceExistsError on create_container is not propagated (idempotent)."""
    record = _make_record()

    mock_blob_client = AsyncMock()
    mock_blob_client.get_blob_properties.side_effect = ResourceNotFoundError("nope")
    mock_blob_client.upload_blob = AsyncMock(return_value=None)
    mock_blob_client.url = "http://127.0.0.1:10000/dev/screenshots/abc.png"

    mock_service_client = AsyncMock()
    mock_service_client.get_blob_client = MagicMock(return_value=mock_blob_client)
    mock_service_client.create_container.side_effect = ResourceExistsError("exists")

    with patch(
        "ingestion.screenshots.uploader.BlobServiceClient.from_connection_string",
        return_value=mock_service_client,
    ):
        async with ScreenshotUploader("conn-str", "container") as up:
            r1 = await up.upload(record)
            r2 = await up.upload(record)  # second call should not re-create container

    assert r1.deduped is False
    assert r2.deduped is False  # mock blob_client doesn't track state, both succeed
    # ensure_container short-circuits after first call:
    assert mock_service_client.create_container.call_count == 1


@pytest.mark.asyncio
async def test_uploader_upload_many_preserves_order() -> None:
    records = [
        ScreenshotRecord(
            image_bytes=b"a", sha256="a" * 64, blob_path="a.png",
            content_type="image/png", alt_text="", doc_order=1, kb_id="kb", doc_id="d",
        ),
        ScreenshotRecord(
            image_bytes=b"b", sha256="b" * 64, blob_path="b.png",
            content_type="image/png", alt_text="", doc_order=2, kb_id="kb", doc_id="d",
        ),
    ]
    mock_blob_client = AsyncMock()
    mock_blob_client.get_blob_properties.side_effect = ResourceNotFoundError("nope")
    mock_blob_client.upload_blob = AsyncMock(return_value=None)
    mock_blob_client.url = "http://127.0.0.1:10000/dev/screenshots/x.png"

    mock_service_client = AsyncMock()
    mock_service_client.get_blob_client = MagicMock(return_value=mock_blob_client)
    mock_service_client.create_container.side_effect = ResourceExistsError("exists")

    with patch(
        "ingestion.screenshots.uploader.BlobServiceClient.from_connection_string",
        return_value=mock_service_client,
    ):
        async with ScreenshotUploader("conn-str", "container") as up:
            results = await up.upload_many(records)

    assert len(results) == 2
    assert all(r.deduped is False for r in results)
    assert results[0].sha256 == "a" * 64
    assert results[1].sha256 == "b" * 64


def test_screenshotrecord_is_frozen_dataclass() -> None:
    """ScreenshotRecord must be immutable so callers can safely cache by sha256."""
    record = _make_record()
    with pytest.raises((AttributeError, Exception)):
        record.kb_id = "other"  # type: ignore[misc]
