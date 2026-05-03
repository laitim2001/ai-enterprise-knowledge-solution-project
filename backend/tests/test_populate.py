"""IndexPopulator unit tests (per CLAUDE.md §5.6 H6 — indexing is critical pipeline)."""

from __future__ import annotations

from datetime import UTC, datetime
from unittest.mock import AsyncMock, MagicMock, patch

import httpx
import pytest

from indexing.populate import IndexPopulator, IndexUploadResult
from indexing.schemas import ChunkRecord, make_chunk_id


def _record(idx: int = 0, kb_id: str = "kb", doc_id: str = "d") -> ChunkRecord:
    return ChunkRecord(
        chunk_id=make_chunk_id(kb_id, doc_id, idx),
        kb_id=kb_id,
        doc_id=doc_id,
        doc_title="T",
        doc_format="docx",
        chunk_index=idx,
        chunk_total=10,
        chunk_title="S",
        chunk_text="body text",
        chunk_token_count=2,
        ingested_at=datetime.now(UTC),
        embedding=[0.0] * 1024,
    )


def _mock_response(status_code: int, body: dict | None = None) -> MagicMock:
    response = MagicMock(spec=httpx.Response)
    response.status_code = status_code
    response.is_success = 200 <= status_code < 300
    response.json = MagicMock(return_value=body or {"value": []})
    response.text = ""
    response.raise_for_status = MagicMock()
    return response


@pytest.mark.asyncio
async def test_upload_empty_records_returns_zero_no_call() -> None:
    with patch("indexing.populate.httpx.AsyncClient") as MockClient:
        instance = MockClient.return_value
        instance.post = AsyncMock()
        instance.aclose = AsyncMock()

        async with IndexPopulator(
            endpoint="https://x.search.windows.net",
            admin_key="key",
            index_name="ekp-kb-drive-v1",
        ) as pop:
            result = await pop.upload([])

    assert isinstance(result, IndexUploadResult)
    assert result.succeeded == 0
    assert result.failed == 0


@pytest.mark.asyncio
async def test_upload_single_doc_success() -> None:
    rec = _record(idx=0)
    body = {"value": [{"key": rec.chunk_id, "status": True, "statusCode": 201}]}

    with patch("indexing.populate.httpx.AsyncClient") as MockClient:
        instance = MockClient.return_value
        instance.post = AsyncMock(return_value=_mock_response(200, body))
        instance.aclose = AsyncMock()

        async with IndexPopulator(
            endpoint="https://x.search.windows.net",
            admin_key="key",
            index_name="ekp-kb-drive-v1",
        ) as pop:
            result = await pop.upload([rec])

    assert result.succeeded == 1
    assert result.failed == 0
    instance.post.assert_awaited_once()


@pytest.mark.asyncio
async def test_upload_payload_uses_mergeOrUpload_action() -> None:
    rec = _record(idx=0)
    body = {"value": [{"key": rec.chunk_id, "status": True, "statusCode": 201}]}

    with patch("indexing.populate.httpx.AsyncClient") as MockClient:
        instance = MockClient.return_value
        instance.post = AsyncMock(return_value=_mock_response(200, body))
        instance.aclose = AsyncMock()

        async with IndexPopulator("https://x", "k", "idx") as pop:
            await pop.upload([rec])

    call_kwargs = instance.post.await_args.kwargs
    import json
    payload = json.loads(call_kwargs["content"])
    assert payload["value"][0]["@search.action"] == "mergeOrUpload"


@pytest.mark.asyncio
async def test_upload_payload_uses_to_search_doc_serialization() -> None:
    """ChunkRecord.embedding -> content_vector + embedded_images -> embedded_images_json."""
    rec = _record(idx=0)
    body = {"value": [{"key": rec.chunk_id, "status": True, "statusCode": 201}]}

    with patch("indexing.populate.httpx.AsyncClient") as MockClient:
        instance = MockClient.return_value
        instance.post = AsyncMock(return_value=_mock_response(200, body))
        instance.aclose = AsyncMock()

        async with IndexPopulator("https://x", "k", "idx") as pop:
            await pop.upload([rec])

    import json
    payload = json.loads(instance.post.await_args.kwargs["content"])
    doc = payload["value"][0]
    assert "content_vector" in doc
    assert len(doc["content_vector"]) == 1024
    assert "embedded_images_json" in doc
    assert "embedding" not in doc  # renamed
    assert "embedded_images" not in doc  # flattened


@pytest.mark.asyncio
async def test_upload_partial_failure_counts_correctly() -> None:
    recs = [_record(idx=i) for i in range(3)]
    body = {
        "value": [
            {"key": recs[0].chunk_id, "status": True, "statusCode": 201},
            {"key": recs[1].chunk_id, "status": False, "statusCode": 400, "errorMessage": "bad"},
            {"key": recs[2].chunk_id, "status": True, "statusCode": 201},
        ],
    }

    with patch("indexing.populate.httpx.AsyncClient") as MockClient:
        instance = MockClient.return_value
        instance.post = AsyncMock(return_value=_mock_response(200, body))
        instance.aclose = AsyncMock()

        async with IndexPopulator("https://x", "k", "idx") as pop:
            result = await pop.upload(recs)

    assert result.succeeded == 2
    assert result.failed == 1
    assert recs[1].chunk_id in result.failed_keys


@pytest.mark.asyncio
async def test_upload_batches_at_1000_doc_limit() -> None:
    """With 2500 records, expect 3 POST calls (1000 + 1000 + 500)."""
    recs = [_record(idx=i) for i in range(2500)]

    def _ok_for(batch_size: int) -> dict:
        return {
            "value": [
                {"key": f"k{i}", "status": True, "statusCode": 201}
                for i in range(batch_size)
            ],
        }

    call_batches: list[int] = []

    async def _post_capture(url: str, content: str):  # noqa: ARG001
        import json
        body = json.loads(content)
        size = len(body["value"])
        call_batches.append(size)
        return _mock_response(200, _ok_for(size))

    with patch("indexing.populate.httpx.AsyncClient") as MockClient:
        instance = MockClient.return_value
        instance.post = AsyncMock(side_effect=_post_capture)
        instance.aclose = AsyncMock()

        async with IndexPopulator("https://x", "k", "idx") as pop:
            result = await pop.upload(recs)

    assert call_batches == [1000, 1000, 500]
    assert result.succeeded == 2500


@pytest.mark.asyncio
async def test_upload_retries_on_5xx_then_succeeds() -> None:
    rec = _record(idx=0)
    error_response = MagicMock(spec=httpx.Response)
    error_response.status_code = 503
    error_response.raise_for_status = MagicMock(
        side_effect=httpx.HTTPStatusError(
            "503", request=MagicMock(), response=error_response,
        ),
    )
    success_response = _mock_response(
        200, {"value": [{"key": rec.chunk_id, "status": True, "statusCode": 201}]},
    )

    with patch("indexing.populate.httpx.AsyncClient") as MockClient:
        instance = MockClient.return_value
        instance.post = AsyncMock(side_effect=[error_response, success_response])
        instance.aclose = AsyncMock()

        async with IndexPopulator("https://x", "k", "idx") as pop:
            result = await pop.upload([rec])

    assert result.succeeded == 1
    assert instance.post.await_count == 2
