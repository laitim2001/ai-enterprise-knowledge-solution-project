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
import re
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
from retrieval.contextual import build_contextual_document

logger = structlog.get_logger(__name__)
_stdlib_logger = logging.getLogger(__name__)

# ADR-0055 — the chunker's marked-text placeholder ([IMG@<doc_order>]); rewritten
# below to the global-identity form [IMG#<sha8>] (checksum_sha256 first 8 hex).
_IMG_PLACEHOLDER_RE = re.compile(r"\[IMG@(\d+)\]")
_EXCESS_NEWLINES_RE = re.compile(r"\n{3,}")


def _rewrite_image_markers(
    marked_text: str,
    position_to_sha: dict[str, str],
    sha_to_url: dict[str, str],
) -> str:
    """ADR-0055 — rewrite [IMG@<doc_order>] placeholders to [IMG#<sha8>].

    Markers whose image was not uploaded (sha unknown to the parser OR skipped
    by the uploader) are stripped — the same drop condition the ImageRef list
    applies, so a marker always corresponds to a live image. Stripping can
    leave runs of blank paragraphs, collapsed back to a single separator. If
    no marker survives the text degrades to plain chunk_text — return "" so
    the field keeps its "non-empty == has markers" semantics.
    """

    def _sub(match: re.Match[str]) -> str:
        sha = position_to_sha.get(f"img@{match.group(1)}")
        if sha is None or sha not in sha_to_url:
            return ""
        return f"[IMG#{sha[:8]}]"

    rewritten = _IMG_PLACEHOLDER_RE.sub(_sub, marked_text)
    if "[IMG#" not in rewritten:
        return ""
    return _EXCESS_NEWLINES_RE.sub("\n\n", rewritten).strip()


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
    images_deduped: int  # number of dedup-skipped


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
                result.embedded_images,
                kb_id=kb_id,
                doc_id=doc_id,
            )
        sha_to_url: dict[str, str] = {}
        sha_to_alt: dict[str, str] = {}
        # CH-009 / ADR-0046 — sha → (width, height) probed at extraction, so the
        # emitted ImageRef carries real dims (lets the chat surface flag decorative
        # icons by min-dim threshold). Absent → ImageRef dims stay 0 (probe miss).
        sha_to_dims: dict[str, tuple[int, int]] = {}
        images_uploaded = 0
        images_deduped = 0
        if self._uploader is not None and screenshot_records:
            try:
                upload_results: list[UploadResult | None] = await self._uploader.upload_many(
                    screenshot_records,
                )
                for rec, ur in zip(screenshot_records, upload_results, strict=True):
                    if ur is None:
                        continue  # BUG-030 — per-image upload failed (logged in uploader); best-effort skip
                    sha_to_url[rec.sha256] = ur.blob_url
                    sha_to_alt[rec.sha256] = rec.alt_text
                    if rec.width is not None and rec.height is not None:
                        sha_to_dims[rec.sha256] = (rec.width, rec.height)
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
        # Contextual Retrieval (ADR-0045 / CH-008): embed the section-context-
        # prefixed text so the vector candidate pool itself distinguishes
        # chapters with structurally similar chunk_text. The STORED chunk_text
        # (ChunkRecord.chunk_text below) stays the original — only the embedded
        # vector bakes in section context. section_path absent → helper falls
        # back to raw chunk_text (bit-identical to pre-CH-008 vectors).
        embed_inputs = [
            build_contextual_document(spec.section_path, spec.chunk_text) for spec in chunks
        ]
        try:
            embeddings = await self._embedder.embed_batch(embed_inputs)
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
                dims = sha_to_dims.get(sha)
                # CH-011 / ADR-0048 — recover the image's document position from the
                # "img@<doc_order>" position key (parser `doc_order`, monotonic across
                # the doc) so the chat can page-order images even within one section.
                # Defensive: malformed / non-"img@" key → 0 (legacy ordering fallback).
                doc_order = 0
                if pos.startswith("img@"):
                    try:
                        doc_order = int(pos[len("img@") :])
                    except ValueError:
                        doc_order = 0
                image_refs.append(
                    ImageRef(
                        blob_url=sha_to_url[sha],
                        alt_text=sha_to_alt.get(sha, ""),
                        checksum_sha256=sha,
                        # CH-009 / ADR-0046 — real dims from PNG IHDR probe (0 when
                        # probe missed); lets the chat surface flag decorative icons.
                        width=dims[0] if dims else 0,
                        height=dims[1] if dims else 0,
                        # BUG-026 C-ii — stamp the image with its owning chunk's
                        # section (parser-correct post-BUG-017) so a neighbour-
                        # attach later surfaces the image's TRUE section, not the
                        # citing intro/meta chunk's.
                        source_section=list(spec.section_path),
                        # CH-011 / ADR-0048 — true document position for page-ordering.
                        doc_order=doc_order,
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
                    # ADR-0055 — sha8 rewrite (or "" passthrough for marker-less
                    # chunks; _rewrite also returns "" when no marker survives).
                    chunk_text_marked=(
                        _rewrite_image_markers(
                            spec.chunk_text_marked,
                            position_to_sha,
                            sha_to_url,
                        )
                        if spec.chunk_text_marked
                        else ""
                    ),
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
