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


def test_w70_search_doc_fields_align_with_schema_json() -> None:
    """ADR-0055 / R2 drift guard — to_search_doc() keys must exactly match the
    schema.json field set (the model_dump-all-fields upload contract: any field
    missing from the index schema makes Azure reject the whole batch)."""
    import json
    from pathlib import Path

    schema_path = Path(__file__).resolve().parent.parent / "indexing" / "schema.json"
    schema = json.loads(schema_path.read_text(encoding="utf-8"))
    schema_fields = {f["name"] for f in schema["fields"]}

    doc = _record(idx=0).to_search_doc()
    assert set(doc.keys()) == schema_fields


def test_w70_search_doc_carries_chunk_text_marked() -> None:
    """ADR-0055 — chunk_text_marked rides to_search_doc via model_dump."""
    rec = _record(idx=0).model_copy(update={"chunk_text_marked": "body [IMG#aaaaaaaa]"})
    doc = rec.to_search_doc()
    assert doc["chunk_text_marked"] == "body [IMG#aaaaaaaa]"
    # Default stays "" for marker-less records (never None — Edm.String field).
    assert _record(idx=1).to_search_doc()["chunk_text_marked"] == ""


def test_p21_chunk_record_acl_defaults_fail_open() -> None:
    """ADR-0066 / W90 P2.1 — a record stamped without ACL is fail-open: empty
    allowed_principals (the P2.2 filter treats empty as public) + internal
    classification. This is what a pre-rebuild / backend-less chunk carries."""
    rec = _record(idx=0)
    assert rec.allowed_principals == []
    assert rec.classification == "internal"


def test_p21_search_doc_carries_acl_fields() -> None:
    """ADR-0066 / W90 P2.1 — allowed_principals + classification ride to_search_doc
    via model_dump (no rename), so Azure AI Search can filter on them (P2.2)."""
    rec = _record(idx=0).model_copy(
        update={"allowed_principals": ["user-a", "grp-eng"], "classification": "restricted"}
    )
    doc = rec.to_search_doc()
    assert doc["allowed_principals"] == ["user-a", "grp-eng"]
    assert doc["classification"] == "restricted"


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
                {"key": f"k{i}", "status": True, "statusCode": 201} for i in range(batch_size)
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
            "503",
            request=MagicMock(),
            response=error_response,
        ),
    )
    success_response = _mock_response(
        200,
        {"value": [{"key": rec.chunk_id, "status": True, "statusCode": 201}]},
    )

    with patch("indexing.populate.httpx.AsyncClient") as MockClient:
        instance = MockClient.return_value
        instance.post = AsyncMock(side_effect=[error_response, success_response])
        instance.aclose = AsyncMock()

        async with IndexPopulator("https://x", "k", "idx") as pop:
            result = await pop.upload([rec])

    assert result.succeeded == 1
    assert instance.post.await_count == 2


# ─── BUG-005: CH-001 index lifecycle 429/5xx retry ───────────────────────────


def _throttled_response() -> MagicMock:
    """A mock Azure 429 response whose raise_for_status() raises HTTPStatusError."""
    resp = MagicMock(spec=httpx.Response)
    resp.status_code = 429
    resp.text = ""
    resp.raise_for_status = MagicMock(
        side_effect=httpx.HTTPStatusError("429", request=MagicMock(), response=resp),
    )
    return resp


@pytest.mark.asyncio
async def test_create_index_for_kb_retries_on_429_then_succeeds() -> None:
    """BUG-005 — a transient Azure 429 on index-create is retried, not hard-failed."""
    created = _mock_response(201)
    with patch("indexing.populate.httpx.AsyncClient") as MockClient:
        instance = MockClient.return_value
        instance.put = AsyncMock(side_effect=[_throttled_response(), created])
        instance.aclose = AsyncMock()

        async with IndexPopulator("https://x", "k", "idx") as pop:
            await pop.create_index_for_kb("drive-sop")

    assert instance.put.await_count == 2  # retried once after the 429


@pytest.mark.asyncio
async def test_create_index_for_kb_does_not_retry_on_400() -> None:
    """BUG-005 — a 400 (bad index name) is a caller error: surface at once, no retry."""
    bad_request = MagicMock(spec=httpx.Response)
    bad_request.status_code = 400
    bad_request.text = "invalid index name"
    bad_request.raise_for_status = MagicMock(
        side_effect=httpx.HTTPStatusError("400", request=MagicMock(), response=bad_request),
    )
    with patch("indexing.populate.httpx.AsyncClient") as MockClient:
        instance = MockClient.return_value
        instance.put = AsyncMock(return_value=bad_request)
        instance.aclose = AsyncMock()

        async with IndexPopulator("https://x", "k", "idx") as pop:
            with pytest.raises(httpx.HTTPStatusError):
                await pop.create_index_for_kb("drive-sop")

    assert instance.put.await_count == 1  # 4xx other than 429 is not retried


@pytest.mark.asyncio
async def test_create_index_for_kb_raises_after_429_exhausts_retries() -> None:
    """BUG-005 — a sustained 429 surfaces after the 3-attempt budget is spent."""
    with patch("indexing.populate.httpx.AsyncClient") as MockClient:
        instance = MockClient.return_value
        instance.put = AsyncMock(return_value=_throttled_response())
        instance.aclose = AsyncMock()

        async with IndexPopulator("https://x", "k", "idx") as pop:
            with pytest.raises(httpx.HTTPStatusError):
                await pop.create_index_for_kb("drive-sop")

    assert instance.put.await_count == 3  # stop_after_attempt(3)


@pytest.mark.asyncio
async def test_delete_index_retries_on_429_then_succeeds() -> None:
    """BUG-005 — delete_index shares the same 429 retry as create_index_for_kb."""
    deleted = MagicMock(spec=httpx.Response)
    deleted.status_code = 204
    with patch("indexing.populate.httpx.AsyncClient") as MockClient:
        instance = MockClient.return_value
        instance.delete = AsyncMock(side_effect=[_throttled_response(), deleted])
        instance.aclose = AsyncMock()

        async with IndexPopulator("https://x", "k", "idx") as pop:
            result = await pop.delete_index("drive-sop")

    assert result is True
    assert instance.delete.await_count == 2


@pytest.mark.asyncio
async def test_create_index_for_kb_does_not_retry_on_quota_429() -> None:
    """BUG-005 amendment — a 429 index-quota breach is a hard limit: surface at
    once, no retry. Azure 429 covers both throttling and quota; only the body's
    "quota" wording marks the deterministic (non-retryable) case."""
    quota = MagicMock(spec=httpx.Response)
    quota.status_code = 429
    quota.text = (
        '{"error":{"message":"Index quota has been exceeded for this service. '
        'Maximum number of indexes allowed: 3"}}'
    )
    quota.raise_for_status = MagicMock(
        side_effect=httpx.HTTPStatusError("429", request=MagicMock(), response=quota),
    )
    with patch("indexing.populate.httpx.AsyncClient") as MockClient:
        instance = MockClient.return_value
        instance.put = AsyncMock(return_value=quota)
        instance.aclose = AsyncMock()

        async with IndexPopulator("https://x", "k", "idx") as pop:
            with pytest.raises(httpx.HTTPStatusError):
                await pop.create_index_for_kb("drive-sop")

    assert instance.put.await_count == 1  # quota 429 is a hard limit — not retried


# ─── W90 P2.3 / ADR-0066 — update_doc_classification (merge-restamp) ──────────


@pytest.mark.asyncio
async def test_update_doc_classification_merges_field_for_each_chunk() -> None:
    """Two-step search-then-merge: collect chunk_ids, then `merge` the classification
    field only (no re-ingest). Returns the restamped count."""
    import json

    search_body = {"value": [{"chunk_id": "kb-d-0"}, {"chunk_id": "kb-d-1"}]}
    merge_body = {
        "value": [
            {"key": "kb-d-0", "status": True, "statusCode": 200},
            {"key": "kb-d-1", "status": True, "statusCode": 200},
        ]
    }
    with patch("indexing.populate.httpx.AsyncClient") as MockClient:
        instance = MockClient.return_value
        instance.post = AsyncMock(
            side_effect=[_mock_response(200, search_body), _mock_response(200, merge_body)]
        )
        instance.aclose = AsyncMock()

        async with IndexPopulator("https://x", "k", "ekp-kb-drive-v1") as pop:
            count = await pop.update_doc_classification("drive_user_manuals", "d", "restricted")

    assert count == 2
    assert instance.post.await_count == 2  # search + one merge batch
    merge_payload = json.loads(instance.post.await_args_list[1].kwargs["content"])
    assert all(item["@search.action"] == "merge" for item in merge_payload["value"])
    assert all(item["classification"] == "restricted" for item in merge_payload["value"])
    # merge carries ONLY the key + the field being updated (leaves content/vectors/ACL).
    assert set(merge_payload["value"][0]) == {"chunk_id", "classification", "@search.action"}


@pytest.mark.asyncio
async def test_update_doc_classification_no_chunks_returns_zero_no_merge() -> None:
    """No chunks matched (doc absent) → returns 0, no merge call (route → 404)."""
    with patch("indexing.populate.httpx.AsyncClient") as MockClient:
        instance = MockClient.return_value
        instance.post = AsyncMock(return_value=_mock_response(200, {"value": []}))
        instance.aclose = AsyncMock()

        async with IndexPopulator("https://x", "k", "ekp-kb-drive-v1") as pop:
            count = await pop.update_doc_classification("drive_user_manuals", "ghost", "restricted")

    assert count == 0
    assert instance.post.await_count == 1  # search only, no merge


@pytest.mark.asyncio
async def test_update_doc_classification_index_missing_returns_zero() -> None:
    """A 404 on the search step (index never created) → 0 (fail-soft, same as delete_doc)."""
    with patch("indexing.populate.httpx.AsyncClient") as MockClient:
        instance = MockClient.return_value
        instance.post = AsyncMock(return_value=_mock_response(404))
        instance.aclose = AsyncMock()

        async with IndexPopulator("https://x", "k", "ekp-kb-drive-v1") as pop:
            count = await pop.update_doc_classification("missing_kb", "d", "restricted")

    assert count == 0
    assert instance.post.await_count == 1


def test_make_chunk_id_sanitizes_forbidden_chars() -> None:
    """Azure AI Search keys: [A-Za-z0-9_=-] only. Spaces / parens / dots → `_`."""
    cid = make_chunk_id(
        kb_id="drive_user_manuals",
        doc_id="DRIVE_User Manual_0601(AR)_FNA-AR Management_v0.03",
        chunk_index=7,
    )
    assert " " not in cid
    assert "(" not in cid
    assert ")" not in cid
    assert "." not in cid
    assert cid.endswith("_chunk-0007")
    # plain ascii doc_id passes through unchanged
    assert make_chunk_id("kb", "doc-A", 0) == "kb-kb_doc-doc-A_chunk-0000"
