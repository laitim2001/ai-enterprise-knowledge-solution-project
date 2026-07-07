"""Ingestion orchestrator unit tests (per CLAUDE.md §5.6 H6 — pipeline is critical).

Synthetic parser/chunker/embedder/uploader stand-ins exercise the assembly logic:
chunk_id pattern, prev/next links, image resolution, failure propagation.
"""

from __future__ import annotations

import asyncio
import threading
from pathlib import Path
from unittest.mock import AsyncMock

import pytest

from ingestion.chunker.base import ChunkSpec
from ingestion.embedding.base import EmbeddingResult
from ingestion.orchestrator import IngestionOrchestrator
from ingestion.parsers.base import EmbeddedImage, ParserResult
from ingestion.screenshots.uploader import UploadResult


class _FakeParser:
    doc_format = "docx"

    def __init__(self, result: ParserResult) -> None:
        self._result = result

    def parse(self, source: Path) -> ParserResult:  # noqa: ARG002
        return self._result


class _FakeChunker:
    def __init__(self, chunks: list[ChunkSpec]) -> None:
        self._chunks = chunks

    def chunk(self, parser_result: ParserResult) -> list[ChunkSpec]:  # noqa: ARG002
        return self._chunks


class _FakeEmbedder:
    embedding_dimension = 1024

    def __init__(self, vectors: list[list[float]] | None = None) -> None:
        self._vectors = vectors

    async def embed(self, text: str) -> EmbeddingResult:  # noqa: ARG002
        return EmbeddingResult(vector=[0.0] * 1024, input_tokens=1)

    async def embed_batch(self, texts: list[str]) -> list[EmbeddingResult]:
        if self._vectors is not None:
            return [EmbeddingResult(vector=v, input_tokens=1) for v in self._vectors]
        return [EmbeddingResult(vector=[0.0] * 1024, input_tokens=1) for _ in texts]


def _spec(
    idx: int,
    title: str,
    text: str = "body",
    images: list[str] | None = None,
    marked: str = "",
) -> ChunkSpec:
    return ChunkSpec(
        section_path=[title],
        chunk_title=title,
        chunk_text=text,
        chunk_token_count=len(text),
        chunk_kind="text",
        chunk_index=idx,
        low_value_flag=False,
        embedded_image_positions=images or [],
        heading_anchor=f"t{idx}",
        chunk_text_marked=marked,
    )


def _parser_result(images: list[EmbeddedImage] | None = None) -> ParserResult:
    return ParserResult(
        source_path=Path("synthetic.docx"),
        doc_format="docx",
        doc_title="Test Doc",
        paragraphs=[],
        embedded_images=images or [],
        tables=[],
    )


@pytest.mark.asyncio
async def test_ingest_emits_chunks_with_correct_chunk_id_pattern() -> None:
    pr = _parser_result()
    chunks = [_spec(0, "S1"), _spec(1, "S2"), _spec(2, "S3")]
    orch = IngestionOrchestrator(
        parser=_FakeParser(pr),
        chunker=_FakeChunker(chunks),
        embedder=_FakeEmbedder(),
        uploader=None,
    )

    result = await orch.ingest(Path("x.docx"), kb_id="drive", doc_id="manual-A")

    assert result.failure is None
    assert len(result.chunks) == 3
    assert result.chunks[0].chunk_id == "kb-drive_doc-manual-A_chunk-0000"
    assert result.chunks[1].chunk_id == "kb-drive_doc-manual-A_chunk-0001"
    assert result.chunks[2].chunk_id == "kb-drive_doc-manual-A_chunk-0002"


@pytest.mark.asyncio
async def test_ingest_links_prev_next_chunk_ids() -> None:
    pr = _parser_result()
    chunks = [_spec(i, f"S{i}") for i in range(3)]
    orch = IngestionOrchestrator(
        parser=_FakeParser(pr),
        chunker=_FakeChunker(chunks),
        embedder=_FakeEmbedder(),
        uploader=None,
    )

    result = await orch.ingest(Path("x.docx"), kb_id="kb", doc_id="d")

    assert result.chunks[0].prev_chunk_id is None
    assert result.chunks[0].next_chunk_id == result.chunks[1].chunk_id
    assert result.chunks[1].prev_chunk_id == result.chunks[0].chunk_id
    assert result.chunks[1].next_chunk_id == result.chunks[2].chunk_id
    assert result.chunks[2].next_chunk_id is None


@pytest.mark.asyncio
async def test_ingest_computes_profile() -> None:
    # W73 / ADR-0056 層 A — orchestrator computes IngestionResult.profile best-effort.
    # An empty parse → profiler classifies "too_small"; assert the profile is populated.
    pr = _parser_result()
    orch = IngestionOrchestrator(
        parser=_FakeParser(pr),
        chunker=_FakeChunker([_spec(0, "S1")]),
        embedder=_FakeEmbedder(),
        uploader=None,
    )

    result = await orch.ingest(Path("x.docx"), kb_id="kb", doc_id="d")

    assert result.profile is not None
    assert result.profile.profile == "too_small"  # empty paragraphs → too_small


@pytest.mark.asyncio
async def test_ingest_parse_failed_returns_failure_record() -> None:
    pr = ParserResult(
        source_path=Path("broken.docx"),
        doc_format="docx",
        doc_title="Broken",
        paragraphs=[],
        parse_failed=True,
        parse_error="zip corrupt",
    )
    orch = IngestionOrchestrator(
        parser=_FakeParser(pr),
        chunker=_FakeChunker([]),
        embedder=_FakeEmbedder(),
        uploader=None,
    )

    result = await orch.ingest(Path("broken.docx"), kb_id="kb", doc_id="d")

    assert result.chunks == []
    assert result.failure is not None
    assert result.failure.stage == "parse"
    assert "zip corrupt" in result.failure.error


@pytest.mark.asyncio
async def test_ingest_empty_chunks_returns_failure_record() -> None:
    pr = _parser_result()
    orch = IngestionOrchestrator(
        parser=_FakeParser(pr),
        chunker=_FakeChunker([]),  # parser ok but chunker emits 0
        embedder=_FakeEmbedder(),
        uploader=None,
    )

    result = await orch.ingest(Path("empty.docx"), kb_id="kb", doc_id="d")

    assert result.chunks == []
    assert result.failure is not None
    assert result.failure.stage == "parse"


@pytest.mark.asyncio
async def test_ingest_embed_failure_propagates_as_failure_record() -> None:
    pr = _parser_result()
    chunks = [_spec(0, "S1")]

    class _BadEmbedder:
        embedding_dimension = 1024

        async def embed(self, text: str) -> EmbeddingResult:
            raise RuntimeError("rate limited too long")

        async def embed_batch(self, texts: list[str]) -> list[EmbeddingResult]:  # noqa: ARG002
            raise RuntimeError("rate limited too long")

    orch = IngestionOrchestrator(
        parser=_FakeParser(pr),
        chunker=_FakeChunker(chunks),
        embedder=_BadEmbedder(),
        uploader=None,
    )

    result = await orch.ingest(Path("x.docx"), kb_id="kb", doc_id="d")

    assert result.chunks == []
    assert result.failure is not None
    assert result.failure.stage == "embed"
    assert "RuntimeError" in result.failure.error


@pytest.mark.asyncio
async def test_ingest_resolves_embedded_images_to_blob_urls() -> None:
    img = EmbeddedImage(
        image_bytes=b"\x89PNG",
        alt_text="figure",
        doc_order=5,
        ext="png",
        sha256="a" * 64,
    )
    pr = _parser_result(images=[img])
    chunks = [_spec(0, "S1", images=["img@5"])]

    mock_uploader = AsyncMock()
    mock_uploader.upload_many = AsyncMock(
        return_value=[
            UploadResult(
                sha256="a" * 64,
                blob_url="http://blob/screenshots/a.png",
                deduped=False,
                bytes_uploaded=4,
            ),
        ],
    )

    orch = IngestionOrchestrator(
        parser=_FakeParser(pr),
        chunker=_FakeChunker(chunks),
        embedder=_FakeEmbedder(),
        uploader=mock_uploader,
    )

    result = await orch.ingest(Path("x.docx"), kb_id="kb", doc_id="d")

    assert result.failure is None
    assert len(result.chunks[0].embedded_images) == 1
    img_ref = result.chunks[0].embedded_images[0]
    assert img_ref.blob_url == "http://blob/screenshots/a.png"
    assert img_ref.checksum_sha256 == "a" * 64
    assert img_ref.alt_text == "figure"
    assert result.images_uploaded == 1
    assert result.images_deduped == 0


@pytest.mark.asyncio
async def test_ingest_uploader_none_skips_image_resolution() -> None:
    """uploader=None (R12 deferred) → embedded_images stays empty for chunks."""
    img = EmbeddedImage(
        image_bytes=b"x",
        alt_text="",
        doc_order=0,
        ext="png",
        sha256="b" * 64,
    )
    pr = _parser_result(images=[img])
    chunks = [_spec(0, "S1", images=["img@0"])]

    orch = IngestionOrchestrator(
        parser=_FakeParser(pr),
        chunker=_FakeChunker(chunks),
        embedder=_FakeEmbedder(),
        uploader=None,
    )
    result = await orch.ingest(Path("x.docx"), kb_id="kb", doc_id="d")

    assert result.chunks[0].embedded_images == []
    assert result.images_uploaded == 0


@pytest.mark.asyncio
async def test_ingest_image_upload_batch_failure_is_non_fatal() -> None:
    """Per design: image upload batch fail → ChunkRecord still emits, images empty."""
    img = EmbeddedImage(
        image_bytes=b"x",
        alt_text="",
        doc_order=0,
        ext="png",
        sha256="c" * 64,
    )
    pr = _parser_result(images=[img])
    chunks = [_spec(0, "S1", images=["img@0"])]

    failing_uploader = AsyncMock()
    failing_uploader.upload_many = AsyncMock(side_effect=ConnectionError("blob down"))

    orch = IngestionOrchestrator(
        parser=_FakeParser(pr),
        chunker=_FakeChunker(chunks),
        embedder=_FakeEmbedder(),
        uploader=failing_uploader,
    )

    result = await orch.ingest(Path("x.docx"), kb_id="kb", doc_id="d")

    # Doc still ingests; chunks emit; images list empty
    assert result.failure is None
    assert len(result.chunks) == 1
    assert result.chunks[0].embedded_images == []


@pytest.mark.asyncio
async def test_ingest_chunk_total_field_set_correctly() -> None:
    pr = _parser_result()
    chunks = [_spec(i, f"S{i}") for i in range(5)]
    orch = IngestionOrchestrator(
        parser=_FakeParser(pr),
        chunker=_FakeChunker(chunks),
        embedder=_FakeEmbedder(),
        uploader=None,
    )

    result = await orch.ingest(Path("x.docx"), kb_id="kb", doc_id="d")

    assert all(c.chunk_total == 5 for c in result.chunks)
    # chunk_index 0..4 sequential
    assert [c.chunk_index for c in result.chunks] == [0, 1, 2, 3, 4]


@pytest.mark.asyncio
async def test_ingest_embedding_attached_in_record_order() -> None:
    """Each ChunkRecord.embedding matches the corresponding chunk_text in batch."""
    pr = _parser_result()
    chunks = [_spec(0, "S1"), _spec(1, "S2"), _spec(2, "S3")]
    distinct_vectors = [
        [1.0] + [0.0] * 1023,
        [0.0, 1.0] + [0.0] * 1022,
        [0.0, 0.0, 1.0] + [0.0] * 1021,
    ]

    orch = IngestionOrchestrator(
        parser=_FakeParser(pr),
        chunker=_FakeChunker(chunks),
        embedder=_FakeEmbedder(vectors=distinct_vectors),
        uploader=None,
    )
    result = await orch.ingest(Path("x.docx"), kb_id="kb", doc_id="d")

    assert result.chunks[0].embedding[0] == 1.0
    assert result.chunks[1].embedding[1] == 1.0
    assert result.chunks[2].embedding[2] == 1.0


# Sanity: orchestrator shape when used as a fixture in async tests
@pytest.mark.asyncio
async def test_ingest_concurrent_callable_via_gather() -> None:
    pr = _parser_result()
    chunks = [_spec(0, "S1")]
    orch = IngestionOrchestrator(
        parser=_FakeParser(pr),
        chunker=_FakeChunker(chunks),
        embedder=_FakeEmbedder(),
        uploader=None,
    )

    results = await asyncio.gather(
        orch.ingest(Path("a.docx"), kb_id="kb", doc_id="a"),
        orch.ingest(Path("b.docx"), kb_id="kb", doc_id="b"),
    )

    assert len(results) == 2
    assert results[0].chunks[0].doc_id == "a"
    assert results[1].chunks[0].doc_id == "b"


# ── ADR-0066 / W90 P2.1 — retrieval-layer ACL stamp ───────────────────────────


@pytest.mark.asyncio
async def test_ingest_stamps_allowed_principals_on_every_chunk() -> None:
    """The caller-resolved KB principals stamp onto every emitted chunk (chunk
    inherits the KB ACL, F2 §1), and each chunk gets its OWN list copy so a later
    mutation of one chunk's list can't bleed into the others."""
    pr = _parser_result()
    chunks = [_spec(i, f"S{i}") for i in range(3)]
    orch = IngestionOrchestrator(
        parser=_FakeParser(pr),
        chunker=_FakeChunker(chunks),
        embedder=_FakeEmbedder(),
        uploader=None,
    )

    result = await orch.ingest(
        Path("x.docx"),
        kb_id="kb",
        doc_id="d",
        allowed_principals=["user-a", "grp-eng"],
        classification="restricted",
    )

    assert all(c.allowed_principals == ["user-a", "grp-eng"] for c in result.chunks)
    assert all(c.classification == "restricted" for c in result.chunks)
    # Each chunk owns its list — mutating one must not bleed into siblings.
    result.chunks[0].allowed_principals.append("leak")
    assert result.chunks[1].allowed_principals == ["user-a", "grp-eng"]


@pytest.mark.asyncio
async def test_ingest_acl_defaults_fail_open() -> None:
    """Omitted ACL args = fail-open transition: empty allowed_principals (the P2.2
    filter treats empty as public) + internal classification. This is the BC path
    for callers that pass no ACL (the existing suite + scripts)."""
    pr = _parser_result()
    chunks = [_spec(0, "S1")]
    orch = IngestionOrchestrator(
        parser=_FakeParser(pr),
        chunker=_FakeChunker(chunks),
        embedder=_FakeEmbedder(),
        uploader=None,
    )

    result = await orch.ingest(Path("x.docx"), kb_id="kb", doc_id="d")

    assert result.chunks[0].allowed_principals == []
    assert result.chunks[0].classification == "internal"


# ─── W70 / ADR-0055 inline image markers — sha8 rewrite pass ────────


@pytest.mark.asyncio
async def test_w70_marked_placeholders_rewritten_to_sha8() -> None:
    """ADR-0055 — [IMG@<doc_order>] → [IMG#<sha8>] for uploaded images."""
    img = EmbeddedImage(
        image_bytes=b"\x89PNG",
        alt_text="fig",
        doc_order=5,
        ext="png",
        sha256="a" * 64,
    )
    pr = _parser_result(images=[img])
    chunks = [_spec(0, "S1", images=["img@5"], marked="S1\n\nbody\n\n[IMG@5]")]

    mock_uploader = AsyncMock()
    mock_uploader.upload_many = AsyncMock(
        return_value=[
            UploadResult(
                sha256="a" * 64,
                blob_url="http://blob/screenshots/a.png",
                deduped=False,
                bytes_uploaded=4,
            ),
        ],
    )

    orch = IngestionOrchestrator(
        parser=_FakeParser(pr),
        chunker=_FakeChunker(chunks),
        embedder=_FakeEmbedder(),
        uploader=mock_uploader,
    )
    result = await orch.ingest(Path("x.docx"), kb_id="kb", doc_id="d")

    assert result.failure is None
    assert result.chunks[0].chunk_text_marked == "S1\n\nbody\n\n[IMG#aaaaaaaa]"
    # Clean text untouched by the rewrite pass.
    assert result.chunks[0].chunk_text == "body"


@pytest.mark.asyncio
async def test_w70_marker_for_skipped_image_stripped() -> None:
    """ADR-0055 — a marker whose image the uploader skipped is stripped (same
    drop condition as the ImageRef list); blank-paragraph runs collapse."""
    imgs = [
        EmbeddedImage(
            image_bytes=b"\x89PNG", alt_text="a", doc_order=2, ext="png", sha256="a" * 64
        ),
        EmbeddedImage(
            image_bytes=b"\x89PNG", alt_text="b", doc_order=4, ext="png", sha256="b" * 64
        ),
    ]
    pr = _parser_result(images=imgs)
    chunks = [
        _spec(
            0,
            "S1",
            images=["img@2", "img@4"],
            marked="S1\n\nstep one\n\n[IMG@2]\n\nstep two\n\n[IMG@4]",
        ),
    ]

    mock_uploader = AsyncMock()
    # BUG-030 best-effort contract: per-image failure → None in upload_many result.
    mock_uploader.upload_many = AsyncMock(
        return_value=[
            None,  # img a failed to upload
            UploadResult(
                sha256="b" * 64,
                blob_url="http://blob/screenshots/b.png",
                deduped=False,
                bytes_uploaded=4,
            ),
        ],
    )

    orch = IngestionOrchestrator(
        parser=_FakeParser(pr),
        chunker=_FakeChunker(chunks),
        embedder=_FakeEmbedder(),
        uploader=mock_uploader,
    )
    result = await orch.ingest(Path("x.docx"), kb_id="kb", doc_id="d")

    marked = result.chunks[0].chunk_text_marked
    assert marked == "S1\n\nstep one\n\nstep two\n\n[IMG#bbbbbbbb]"
    assert "\n\n\n" not in marked
    # Marker set mirrors the ImageRef list (only the uploaded image).
    assert [r.checksum_sha256 for r in result.chunks[0].embedded_images] == ["b" * 64]


@pytest.mark.asyncio
async def test_w70_marked_empty_when_no_marker_survives() -> None:
    """ADR-0055 — all markers stripped (uploader=None → nothing uploaded) →
    chunk_text_marked degrades to "" (non-empty == has markers invariant)."""
    img = EmbeddedImage(
        image_bytes=b"x",
        alt_text="",
        doc_order=0,
        ext="png",
        sha256="c" * 64,
    )
    pr = _parser_result(images=[img])
    chunks = [_spec(0, "S1", images=["img@0"], marked="S1\n\n[IMG@0]\n\nbody")]

    orch = IngestionOrchestrator(
        parser=_FakeParser(pr),
        chunker=_FakeChunker(chunks),
        embedder=_FakeEmbedder(),
        uploader=None,
    )
    result = await orch.ingest(Path("x.docx"), kb_id="kb", doc_id="d")

    assert result.chunks[0].chunk_text_marked == ""
    assert result.chunks[0].embedded_images == []


@pytest.mark.asyncio
async def test_w70_markerless_chunk_passes_through_empty() -> None:
    """ADR-0055 — a chunk the chunker left marker-less stays "" (no rewrite)."""
    pr = _parser_result()
    chunks = [_spec(0, "S1")]  # marked defaults to ""
    orch = IngestionOrchestrator(
        parser=_FakeParser(pr),
        chunker=_FakeChunker(chunks),
        embedder=_FakeEmbedder(),
        uploader=None,
    )
    result = await orch.ingest(Path("x.docx"), kb_id="kb", doc_id="d")

    assert result.chunks[0].chunk_text_marked == ""


@pytest.mark.asyncio
async def test_ingest_kb_config_extract_embedded_images_false_skips_extraction() -> None:
    """W20 F4.2 — `extract_embedded_images=False` short-circuits ScreenshotExtractor.

    The parser-provided embedded images are skipped entirely, so each chunk's
    `embedded_images` list comes out empty even though the uploader could have
    accepted them. (Backward-compat: `kb_config=None` keeps the W2 baseline,
    asserted by every other test in this module.)
    """
    from api.schemas.kb import KbConfig

    img = EmbeddedImage(
        image_bytes=b"\x89PNG",
        alt_text="x",
        doc_order=0,
        ext="png",
        sha256="c" * 64,
    )
    pr = _parser_result(images=[img])
    chunks = [_spec(0, "S1", images=["img@0"])]

    mock_uploader = AsyncMock()
    mock_uploader.upload_many = AsyncMock(return_value=[])

    orch = IngestionOrchestrator(
        parser=_FakeParser(pr),
        chunker=_FakeChunker(chunks),
        embedder=_FakeEmbedder(),
        uploader=mock_uploader,
    )

    config = KbConfig(extract_embedded_images=False)
    result = await orch.ingest(
        Path("x.docx"),
        kb_id="kb",
        doc_id="d",
        kb_config=config,
    )

    # Extraction skipped → uploader never called.
    mock_uploader.upload_many.assert_not_called()
    assert result.failure is None
    assert result.images_uploaded == 0
    assert result.chunks[0].embedded_images == []


@pytest.mark.asyncio
async def test_ingest_kb_config_extract_embedded_images_true_preserves_w2_path() -> None:
    """W20 F4.2 — `extract_embedded_images=True` matches the W2 baseline path."""
    from api.schemas.kb import KbConfig

    img = EmbeddedImage(
        image_bytes=b"\x89PNG",
        alt_text="figure",
        doc_order=0,
        ext="png",
        sha256="d" * 64,
    )
    pr = _parser_result(images=[img])
    chunks = [_spec(0, "S1", images=["img@0"])]

    mock_uploader = AsyncMock()
    mock_uploader.upload_many = AsyncMock(
        return_value=[
            UploadResult(
                sha256="d" * 64,
                blob_url="http://blob/screenshots/d.png",
                deduped=False,
                bytes_uploaded=4,
            ),
        ],
    )

    orch = IngestionOrchestrator(
        parser=_FakeParser(pr),
        chunker=_FakeChunker(chunks),
        embedder=_FakeEmbedder(),
        uploader=mock_uploader,
    )

    config = KbConfig(extract_embedded_images=True)
    result = await orch.ingest(
        Path("x.docx"),
        kb_id="kb",
        doc_id="d",
        kb_config=config,
    )

    mock_uploader.upload_many.assert_called_once()
    assert result.failure is None
    assert result.chunks[0].embedded_images[0].blob_url.endswith("d.png")
    assert result.images_uploaded == 1


# ─── BUG-040 — sync parse/chunk/profile offloaded off the event loop ─────────


@pytest.mark.asyncio
async def test_ingest_offloads_parse_and_chunk_to_worker_thread() -> None:
    """BUG-040 — parse + chunk are sync + CPU-bound; they MUST run via
    asyncio.to_thread so a large file can't block the uvicorn event loop and hang
    every concurrent request. Assert both executed on a worker thread, not the
    loop's own thread (thread-id check is deterministic — no timing flakiness)."""
    loop_thread_id = threading.get_ident()
    ran_on: dict[str, int] = {}

    class _ThreadRecordingParser:
        doc_format = "docx"

        def parse(self, source: Path) -> ParserResult:  # noqa: ARG002
            ran_on["parse"] = threading.get_ident()
            return _parser_result()

    class _ThreadRecordingChunker:
        def chunk(self, parser_result: ParserResult) -> list[ChunkSpec]:  # noqa: ARG002
            ran_on["chunk"] = threading.get_ident()
            return [_spec(0, "S1")]

    orch = IngestionOrchestrator(
        parser=_ThreadRecordingParser(),
        chunker=_ThreadRecordingChunker(),
        embedder=_FakeEmbedder(),
        uploader=None,
    )

    result = await orch.ingest(Path("big.docx"), kb_id="kb", doc_id="d")

    assert result.failure is None
    assert ran_on["parse"] != loop_thread_id, "parse must run off the event loop thread"
    assert ran_on["chunk"] != loop_thread_id, "chunk must run off the event loop thread"


@pytest.mark.asyncio
async def test_ingest_blocking_parse_keeps_event_loop_responsive() -> None:
    """BUG-040 — while a large parse blocks inside its worker thread, the event
    loop stays live: a concurrent coroutine keeps advancing. Without the
    asyncio.to_thread offload the sync parse would freeze the loop and this test
    would hang (parse_entered would never be observed before the timeout)."""
    parse_entered = threading.Event()
    release_parse = threading.Event()

    class _BlockingParser:
        doc_format = "docx"

        def parse(self, source: Path) -> ParserResult:  # noqa: ARG002
            parse_entered.set()
            # Block the WORKER thread — with to_thread this must NOT freeze the loop.
            assert release_parse.wait(timeout=5), "release signal never arrived"
            return _parser_result()

    orch = IngestionOrchestrator(
        parser=_BlockingParser(),
        chunker=_FakeChunker([_spec(0, "S1")]),
        embedder=_FakeEmbedder(),
        uploader=None,
    )
    ingest_task = asyncio.create_task(orch.ingest(Path("big.docx"), kb_id="kb", doc_id="d"))

    # The loop must schedule this poll even though parse is blocking — if the loop
    # were frozen we'd never see parse_entered set (proving the offload works).
    for _ in range(500):
        if parse_entered.is_set():
            break
        await asyncio.sleep(0.001)
    assert parse_entered.is_set(), "event loop stalled — parse never entered its thread"

    release_parse.set()
    result = await asyncio.wait_for(ingest_task, timeout=5)
    assert result.failure is None
    assert len(result.chunks) == 1
