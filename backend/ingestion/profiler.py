"""Rule-based document profiler — content-format classification (per ADR-0056 層 A).

Implements ADR-0056 D1 taxonomy + D2 rule v3 signals + D7 low-confidence fallback.

**Standalone module (W72 scope)**: this profiler is NOT wired into orchestrator.py —
production ingestion behaviour is bit-identical unchanged. profile→preset routing,
the three-tier UI, and the LLM tie-break safety net are all deferred to later 層 A
segments. W72 only builds + verifies the classification engine itself.

Design notes:
- Deterministic, pure-rule classification — no LLM, no image embedding (H4 boundary).
  classify mirrors `chunker/strategies._resolve_auto` rule-of-3 純函數 style (unit-testable).
- Structural signals derive from existing `ParserResult` fields (zero contract change).
  PDF per-page text density + text-layer empty-ratio come from a profiler-owned
  pypdfium2 pre-OCR pass (per plan §1 設計決策 — NOT a ParserResult contract change:
  P4 detection already requires a pre-OCR pass, so page density rides the same pass).
- P4 scan detection MUST be pre-OCR: after Docling OCR the text-layer signal is lost
  (embedded_images=0 + heading false-positives), so pypdfium2 pre-OCR probing is the
  only reliable path (verified 7/7 on real scan invoices — explore_scan_pdf.py).
- @dataclass internal types (ParserResult-style, no API boundary validation).
"""

from __future__ import annotations

import logging
import re
from dataclasses import dataclass
from pathlib import Path
from typing import Literal

import pypdfium2 as pdfium  # type: ignore[import-untyped]  # no stubs (Docling 自帶 dep)

from ingestion.parsers.base import DocFormat, ParserResult

logger = logging.getLogger(__name__)

DocProfile = Literal[
    "P1_sop_imgdense",
    "P1_sop_text",
    "P2_prose",
    "P3_slide_imgdense",
    "P3_slide_text",
    "P4_scan_imgdense",
    "P5_form",
    "too_small",
    "unknown",
]

# --- classify thresholds (productionize explore_doc_profiling_v2 + ADR-0056 D2 v3) ---
_TOO_SMALL_PARAS = 20  # ADR D2 v3: 25→20 (救短真文件被誤殺)
_P1_IMGDENSE_DEPTH = 3
_P1_IMGDENSE_IMG_DENSITY = 0.15
_P1_IMGDENSE_LIST_RATIO = 0.3
_P1_TEXT_LIST_RATIO = 0.12
_P1_TEXT_HEADINGS = 10
_P2_HEAD_DENSITY = 0.05
_P3_IMGDENSE_IMG_DENSITY = 0.12
_FORM_TICKBOX_DENSITY = 0.15  # tickbox/Q-marker 段落比例 (F3 harness 跑真文件後調)

# --- PDF pre-OCR thresholds (pypdfium2 text-layer probe; per explore_scan_pdf.py) ---
_PDF_EMPTY_CHAR_THRESHOLD = 10  # 一頁 < 10 chars 視為 text-layer 空
_PDF_SCAN_EMPTY_RATIO = 0.5  # 空頁比例 ≥ 0.5 → P4 scan
_PDF_SCAN_THIN_AVG = 200.0  # 平均 chars/頁 < 此 → text-layer 稀薄 → P4-ish
_PDF_SLIDE_AVG_CHARS = 600.0  # born-digital PDF 每頁 < 此 → 簡報傾向 (procedure ~2000)

# tick-box / Q-marker / 問卷信號 (救 P5_form,per ADR D2 v3)
_TICKBOX_RE = re.compile(r"[□☐☑☒★]|\bQ\d+[.):]|your answer|answer\s*:", re.IGNORECASE)


def _probe_pdf_text_layer(
    source_path: Path,
) -> tuple[int | None, float | None, float | None]:
    """pypdfium2 pre-OCR text-layer probe (秒級,唔 OCR;per explore_scan_pdf.py).

    Returns (pages, empty_page_ratio, avg_chars_per_page). All None on failure so
    callers degrade to structural signals — probing MUST NOT abort profiling / ingest.

    W84 / ADR-0065 — promoted from a `DocumentProfiler` method to module-level so the
    ingest guard (`is_scan_pdf`) can reuse the SAME pre-OCR probe without instantiating
    a profiler. `DocumentProfiler._extract_signals` calls this; behaviour is identical.
    """
    try:
        pdf = pdfium.PdfDocument(str(source_path))
        n = len(pdf)
        if n == 0:
            return 0, None, None
        char_counts = [
            len((pdf[i].get_textpage().get_text_range() or "").strip()) for i in range(n)
        ]
        empty = sum(1 for c in char_counts if c < _PDF_EMPTY_CHAR_THRESHOLD)
        return n, empty / n, sum(char_counts) / n
    except Exception:  # noqa: BLE001 — probe failure must not abort profiling / ingest
        logger.warning("pdf text-layer probe failed", extra={"path": str(source_path)})
        return None, None, None


def is_scan_pdf(source_path: Path) -> bool:
    """Pre-parse P4 (scan) detection — pypdfium2 text-layer probe, NO OCR (ADR-0065).

    True when the PDF's text layer is empty/thin enough to be a scan that needs OCR —
    mirrors the profiler's `_classify_pdf_preocr` P4 branch (empty-page ratio ≥
    `_PDF_SCAN_EMPTY_RATIO` OR avg chars/page < `_PDF_SCAN_THIN_AVG`). The ingest guard
    uses it to short-circuit BEFORE the slow Docling OCR parse (8–9.5 min/file).

    Probe failure (all None) → False: the guard only blocks CONFIDENT scans, so an
    unreadable / non-PDF path lets ingest proceed (parser surfaces real errors). Caller
    should invoke only for `.pdf` (other formats have no text-layer to probe).
    """
    _pages, empty_ratio, avg_chars = _probe_pdf_text_layer(source_path)
    if empty_ratio is not None and empty_ratio >= _PDF_SCAN_EMPTY_RATIO:
        return True
    return avg_chars is not None and avg_chars < _PDF_SCAN_THIN_AVG


@dataclass(slots=True)
class ProfileSignals:
    """Transparent signal bundle — 後續 UI 段 L3「文件畫像」section 直接消費。"""

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


@dataclass(slots=True)
class ProfileResult:
    """Document profile classification + confidence (per ADR-0056 D1)."""

    profile: DocProfile
    confidence: float  # 0–1
    signals: ProfileSignals
    fallback_applied: bool = False


class DocumentProfiler:
    """Rule-based content-format profiler (ADR-0056 層 A, classification layer).

    `profile()` is deterministic and pure-rule — same input always yields the same
    ProfileResult (H4: no LLM, no image embedding). The PDF branch runs an extra
    pypdfium2 pre-OCR pass for text-layer + page-density signals.
    """

    def profile(self, parser_result: ParserResult, source_path: Path) -> ProfileResult:
        signals = self._extract_signals(parser_result, source_path)
        profile, confidence, fallback = self._classify(parser_result.doc_format, signals)
        return ProfileResult(
            profile=profile,
            confidence=confidence,
            signals=signals,
            fallback_applied=fallback,
        )

    # --- signal extraction ---

    def _extract_signals(self, pr: ParserResult, source_path: Path) -> ProfileSignals:
        paras = pr.paragraphs_total
        headings = sum(1 for p in pr.paragraphs if p.kind == "heading")
        list_items = sum(1 for p in pr.paragraphs if p.kind == "list_item")
        max_depth = max(
            (p.heading_level or 0 for p in pr.paragraphs if p.kind == "heading"),
            default=0,
        )
        images = len(pr.embedded_images)
        tables = len(pr.tables)
        tickbox = len(_TICKBOX_RE.findall(pr.raw_text))
        denom = paras or 1  # avoid div-by-zero on empty parse

        pdf_pages: int | None = None
        pdf_empty_ratio: float | None = None
        pdf_avg_chars: float | None = None
        if pr.doc_format == "pdf":
            pdf_pages, pdf_empty_ratio, pdf_avg_chars = _probe_pdf_text_layer(source_path)

        return ProfileSignals(
            paragraphs=paras,
            headings=headings,
            max_depth=max_depth,
            list_items=list_items,
            images=images,
            tables=tables,
            img_density=images / denom,
            head_density=headings / denom,
            list_ratio=list_items / denom,
            tickbox_density=tickbox / denom,
            pdf_pages=pdf_pages,
            pdf_empty_ratio=pdf_empty_ratio,
            pdf_avg_chars=pdf_avg_chars,
        )

    # --- classify (rule v3) ---

    def _classify(self, fmt: DocFormat, s: ProfileSignals) -> tuple[DocProfile, float, bool]:
        if fmt == "pptx":
            return self._classify_pptx(s)
        if fmt == "pdf":
            pdf_verdict = self._classify_pdf_preocr(s)
            if pdf_verdict is not None:
                return pdf_verdict
        # generic structural rules (docx + born-digital text PDF fall-through)
        return self._classify_structural(s)

    def _classify_pptx(self, s: ProfileSignals) -> tuple[DocProfile, float, bool]:
        # pptx 一律 P3 (豁免 too_small);按圖密度細分子型 (影響後續 image 流程)
        sub: DocProfile = (
            "P3_slide_imgdense" if s.img_density >= _P3_IMGDENSE_IMG_DENSITY else "P3_slide_text"
        )
        return sub, 0.95, False

    def _classify_pdf_preocr(self, s: ProfileSignals) -> tuple[DocProfile, float, bool] | None:
        """PDF pre-OCR 分流。返回 None = 落通用結構規則 (born-digital text PDF)。"""
        # text-layer 空 → P4 scan short-circuit (唔靠 Docling 結果,唔觸發 OCR)
        if s.pdf_empty_ratio is not None and s.pdf_empty_ratio >= _PDF_SCAN_EMPTY_RATIO:
            return "P4_scan_imgdense", 0.95, False
        # text-layer 稀薄 → P4-ish (次級信心)
        if s.pdf_avg_chars is not None and s.pdf_avg_chars < _PDF_SCAN_THIN_AVG:
            return "P4_scan_imgdense", 0.75, False
        # born-digital 簡報:每頁字數低 → P3 (PDF img_density 恆 0 → text 子型)
        if s.pdf_avg_chars is not None and s.pdf_avg_chars < _PDF_SLIDE_AVG_CHARS:
            return "P3_slide_text", 0.8, False
        return None

    def _classify_structural(self, s: ProfileSignals) -> tuple[DocProfile, float, bool]:
        # too_small 噪音過濾
        if s.paragraphs < _TOO_SMALL_PARAS:
            return "too_small", 0.9, False
        # 表單:無/極少 heading + 無 list + 無圖 (強結構信號)
        if s.headings <= 1 and s.list_items == 0 and s.images == 0:
            return "P5_form", 0.9, False
        # P1 圖密 SOP:深結構 + 圖密 + 步驟列表 (PDF img_density=0 → 自然接唔到,正確)
        if (
            s.max_depth >= _P1_IMGDENSE_DEPTH
            and s.img_density >= _P1_IMGDENSE_IMG_DENSITY
            and s.list_ratio >= _P1_IMGDENSE_LIST_RATIO
        ):
            return "P1_sop_imgdense", 0.95, False
        # P1 純文字 SOP:步驟列表密 + heading 多 (低圖;PDF / 純文字 docx 都接到)。
        # 必須先於 tickbox branch:checklist-style runbook 帶 ☐ marker 但有 SOP 結構
        # (list_ratio + headings),唔應因 tickbox 誤判 form。W72 F3 n8n-runbook miss
        # 坐實:list_r=0.154 + head=14 命中 P1,但 tickbox_d=0.188 曾喺此之前搶到 form。
        if s.list_ratio >= _P1_TEXT_LIST_RATIO and s.headings >= _P1_TEXT_HEADINGS:
            return "P1_sop_text", 0.85, False
        # 問卷式 form:tick-box / Q-marker 密 (runbook 已被 P1_sop_text 接走,剩低真問卷
        # — questionnaire list=0 唔命中 P1,tickbox_d 高 → form)
        if s.tickbox_density >= _FORM_TICKBOX_DENSITY:
            return "P5_form", 0.75, False
        # P2 散文:有 heading 結構但 list 少
        if s.head_density >= _P2_HEAD_DENSITY and s.list_ratio < _P1_TEXT_LIST_RATIO:
            return "P2_prose", 0.8, False
        # D7:無法判斷 → fallback 最保守 P2_prose (分錯寧保守不激進)
        return "P2_prose", 0.3, True
