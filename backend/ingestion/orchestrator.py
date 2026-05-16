"""Ingestion orchestrator (per components/C01-ingestion.md §1 pipeline diagram).

End-to-end: parse → chunk → upload screenshots → embed chunk_texts → emit ChunkRecord.

Atomic per-doc semantics (per architecture.md §3.5 design intent + components/C01 §4):
- If parse_failed: return ([], FailureRecord("parse")).
- If any embedding call fails after retries: return ([], FailureRecord("embed", ...)).
- Screenshot upload failures are non-fatal — the affected ChunkRecord still emits with
  best-effort embedded_images list (images that did upload); failures logged via structlog.
  Rationale: text retrieval (Gate 1 R@5) does not depend on image availability per
  architecture.md §3.5 schema (embedded_images is metadata for citation render only).

The orchestrator returns either a fully-assembled list[ChunkRecord] OR an empty list
plus a FailureRecord. Caller (C02 KB Manager / scripts/run_populate_sanity.py) decides
whether to abort batch or record + continue.

W20 F4.2 — `ingest()` accepts an optional `kb_config: KbConfig | None = None`
argument so per-KB multimodal toggles flip behaviour at ingest time:

* `extract_embedded_images=False` skips the W2 F3 screenshot-extraction step
  entirely (text-only KB → no `ScreenshotExtractor.extract` call).
* `slide_screenshots` + `dedup_strategy` are forward-compat seams (R12 — the
  caller passes `uploader=None` today so these don't yet light up behaviour).
* `return_images_in_chat` is a *query-time* flag (chat surface reads it from
  the KB record); the orchestrator does not branch on it.

Callers that omit `kb_config` get the W2-baseline behaviour (extract enabled)
— this is the path the existing pytest suite + `scripts/run_populate_sanity.py`
take, so the existing call sites need no churn.
"""

from __future__ import annotations

import logging
from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path

import structlog

from api.schemas.kb import KbConfig
from indexing.schemas import ChunkRecord, ImageRef, make_chunk_id
from ingestion.chunker.base import Chunker, ChunkSpec
from ingestion.embedding.base import Embedder
from ingestion.parsers.base import Parser, ParserResult
from ingestion.screenshots.extractor import ScreenshotExtractor, ScreenshotRecord
from ingestion.screenshots.uploader import ScreenshotUploader, UploadResult

logger = structlog.get_logger(__name__)
_stdlib_logger = logging.getLogger(__name__)


@dataclass(slots=True, frozen=True)
class FailureRecord:
    """Why a doc failed to ingest. Attached by C02 KB Manager to KB.failed_documents."""

    doc_id: str
    stage: str  # "parse" | "embed" | "upload" | "unknown"
    error: str


@dataclass(slots=True, frozen=True)
class IngestionResult:
    """Output bundle: chunks emitted + failure summary (mutually exclusive: chunks OR failure)."""

    chunks: list[ChunkRecord]
    failure: FailureRecord | None
    images_uploaded: int  # number of unique blobs uploaded (post-dedup)
    images_deduped: int   # number of dedup-skipped


class IngestionOrchestrator:
    """Coordinator for parse → chunk → screenshot → embed → ChunkRecord pipeline.

    Holds parser/chunker/embedder/uploader instances; caller manages their lifecycles.
    """

    def __init__(
        self,
        parser: Parser,
        chunker: Chunker,
        embedder: Embedder,
        uploader: ScreenshotUploader | None,
    ) -> None:
        self._parser = parser
        self._chunker = chunker
        self._embedder = embedder
        self._uploader = uploader  # may be None if image upload disabled (e.g. R12 defer)

    async def ingest(
        self,
        source: Path,
        kb_id: str,
        doc_id: str,
        source_url: str = "",
        kb_config: KbConfig | None = None,
    ) -> IngestionResult:
        # 1. Parse — sync but CPU-bound; chunker also sync.
        result: ParserResult = self._parser.parse(source)
        if result.parse_failed:
            return IngestionResult(
                chunks=[],
                failure=FailureRecord(doc_id=doc_id, stage="parse", error=result.parse_error or ""),
                images_uploaded=0,
                images_deduped=0,
            )

        chunks: list[ChunkSpec] = self._chunker.chunk(result)
        if not chunks:
            return IngestionResult(
                chunks=[],
                failure=FailureRecord(doc_id=doc_id, stage="parse", error="empty doc — no chunks"),
                images_uploaded=0,
                images_deduped=0,
            )

        # 2. Upload screenshots — best-effort; per-image failure non-fatal.
        # W20 F4.2: skip extraction entirely when the KB owner opted out via
        # `KbConfig.extract_embedded_images = False`. Backward-compat = no config
        # passed → extract (W2 baseline).
        if kb_config is not None and not kb_config.extract_embedded_images:
            screenshot_records: list[ScreenshotRecord] = []
        else:
            screenshot_records = ScreenshotExtractor.extract(
                result.embedded_images, kb_id=kb_id, doc_id=doc_id,
            )
        sha_to_url: dict[str, str] = {}
        sha_to_alt: dict[str, str] = {}
        images_uploaded = 0
        images_deduped = 0
        if self._uploader is not None and screenshot_records:
            try:
                upload_results: list[UploadResult] = await self._uploader.upload_many(
                    screenshot_records,
                )
                for rec, ur in zip(screenshot_records, upload_results, strict=True):
                    sha_to_url[rec.sha256] = ur.blob_url
                    sha_to_alt[rec.sha256] = rec.alt_text
                    if ur.deduped:
                        images_deduped += 1
                    else:
                        images_uploaded += 1
            except Exception as exc:  # noqa: BLE001 — image upload best-effort
                logger.warning(
                    "screenshot_upload_batch_failed",
                    doc_id=doc_id,
                    error=f"{type(exc).__name__}: {exc}",
                )

        # 3. Embed chunk_texts in parallel.
        chunk_texts = [spec.chunk_text for spec in chunks]
        try:
            embeddings = await self._embedder.embed_batch(chunk_texts)
        except Exception as exc:  # noqa: BLE001 — embed failure is fatal for the doc
            return IngestionResult(
                chunks=[],
                failure=FailureRecord(
                    doc_id=doc_id,
                    stage="embed",
                    error=f"{type(exc).__name__}: {exc}",
                ),
                images_uploaded=images_uploaded,
                images_deduped=images_deduped,
            )

        # 4. Assemble ChunkRecord — chunk_id, prev/next links, image resolution.
        chunk_total = len(chunks)
        records: list[ChunkRecord] = []
        ingested_at = datetime.now(UTC)

        # Build sha->position lookup so we can resolve embedded_image_positions ("img@<doc_order>")
        # to ImageRef via parser's EmbeddedImage list.
        position_to_sha: dict[str, str] = {
            f"img@{img.doc_order}": img.sha256 for img in result.embedded_images
        }

        for idx, spec in enumerate(chunks):
            chunk_id = make_chunk_id(kb_id, doc_id, idx)
            prev_id = make_chunk_id(kb_id, doc_id, idx - 1) if idx > 0 else None
            next_id = make_chunk_id(kb_id, doc_id, idx + 1) if idx < chunk_total - 1 else None

            image_refs: list[ImageRef] = []
            for pos in spec.embedded_image_positions:
                sha = position_to_sha.get(pos)
                if sha is None or sha not in sha_to_url:
                    continue  # uploader skipped this image OR parser did not extract
                image_refs.append(
                    ImageRef(
                        blob_url=sha_to_url[sha],
                        alt_text=sha_to_alt.get(sha, ""),
                        checksum_sha256=sha,
                    ),
                )

            records.append(
                ChunkRecord(
                    chunk_id=chunk_id,
                    kb_id=kb_id,
                    doc_id=doc_id,
                    doc_title=result.doc_title,
                    doc_format=result.doc_format,
                    chunk_index=idx,
                    chunk_total=chunk_total,
                    chunk_title=spec.chunk_title,
                    chunk_text=spec.chunk_text,
                    chunk_token_count=spec.chunk_token_count,
                    section_path=list(spec.section_path),
                    embedded_images=image_refs,
                    prev_chunk_id=prev_id,
                    next_chunk_id=next_id,
                    tags=[],  # W2 baseline: no tag enrichment; W3+ may add domain tags
                    low_value_flag=spec.low_value_flag,
                    enabled=True,
                    source_url=source_url,
                    ingested_at=ingested_at,
                    embedding=embeddings[idx].vector,
                ),
            )

        logger.info(
            "doc_ingested",
            doc_id=doc_id,
            kb_id=kb_id,
            chunks=chunk_total,
            images_uploaded=images_uploaded,
            images_deduped=images_deduped,
            total_input_tokens=sum(e.input_tokens for e in embeddings),
        )

        return IngestionResult(
            chunks=records,
            failure=None,
            images_uploaded=images_uploaded,
            images_deduped=images_deduped,
        )
