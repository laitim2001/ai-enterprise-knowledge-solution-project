"""Per-document profile read schema (W76 / ADR-0056 層 A 段③ 前置 — read surface).

Pydantic mirror of the W72 `ProfileResult` (`ingestion/profiler.py`), surfaced via
`DocumentSummary.profile` (label + confidence, lightweight) and
`DocumentDetail.profile` (full signals, L3 文件畫像 section). The profiler emits an
``@dataclass`` (no API-boundary validation); this is the validated read-API shape.

``profile`` is a free-form ``str`` here (not the `DocProfile` Literal) so the API
contract is decoupled from the ingestion taxonomy — a profiler that adds a profile
class doesn't break stored rows. ``from_result`` is the only ingestion↔schema seam
and imports `ProfileResult` under ``TYPE_CHECKING`` (no runtime reverse dependency).
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from pydantic import BaseModel

if TYPE_CHECKING:
    from ingestion.profiler import ProfileResult


class DocProfileSignals(BaseModel):
    """Transparent signal bundle (mirror `ingestion.profiler.ProfileSignals`).

    The L3「文件畫像」section renders these directly so the user can see WHY a doc
    was classified as it was (img_density / list_ratio / pdf text-layer / etc.).
    """

    paragraphs: int
    headings: int
    max_depth: int
    list_items: int
    images: int
    tables: int
    img_density: float
    head_density: float
    list_ratio: float
    tickbox_density: float
    pdf_pages: int | None = None
    pdf_empty_ratio: float | None = None
    pdf_avg_chars: float | None = None


class DocProfileInfo(BaseModel):
    """Validated read shape for a document's W72 profile + confidence + signals."""

    profile: str  # DocProfile label (e.g. "P1_sop_imgdense"); free-form to decouple
    confidence: float  # 0–1
    fallback_applied: bool = False  # True → low-confidence D7 conservative fallback
    signals: DocProfileSignals
    profiled_at: str  # ISO-8601; stamped by the caller at persist time

    @classmethod
    def from_result(cls, result: ProfileResult, *, profiled_at: str) -> DocProfileInfo:
        """Build the read schema from a profiler `ProfileResult` (ingest persist seam)."""
        s = result.signals
        return cls(
            profile=result.profile,
            confidence=result.confidence,
            fallback_applied=result.fallback_applied,
            signals=DocProfileSignals(
                paragraphs=s.paragraphs,
                headings=s.headings,
                max_depth=s.max_depth,
                list_items=s.list_items,
                images=s.images,
                tables=s.tables,
                img_density=s.img_density,
                head_density=s.head_density,
                list_ratio=s.list_ratio,
                tickbox_density=s.tickbox_density,
                pdf_pages=s.pdf_pages,
                pdf_empty_ratio=s.pdf_empty_ratio,
                pdf_avg_chars=s.pdf_avg_chars,
            ),
            profiled_at=profiled_at,
        )
