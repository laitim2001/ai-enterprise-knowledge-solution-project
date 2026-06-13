"""DocumentProfiler unit tests (ADR-0056 層 A profiler; per CLAUDE.md §5.6 H6).

Coverage:
- _classify rule v3 各分支:P1_sop_imgdense / P1_sop_text / P2_prose /
  P3_slide_imgdense/_text / P5_form (tickbox + heading-sparse) / too_small
- D7 低信心 fallback:unknown → P2_prose + fallback_applied + confidence < 0.5
- PDF pre-OCR 分流 (_classify_pdf_preocr):P4 (empty-ratio / thin-avg) / P3 (low avg) / None
- _extract_signals 數值正確 (img_density / list_ratio / head_density) + 空 doc 唔 div-by-zero
- deterministic (H4):同 input 兩次 → bit-identical 判決
- PDF text-layer probe integration (真 scan sample,skipif 缺 sample = CI)

Synthetic ParserResult — sample-doc gitignored,unit tests 唔依賴真 file (CI-safe);
真文件 accuracy 驗證喺 scripts/profiler_accuracy_harness.py (local,≥90% gate)。
"""

from __future__ import annotations

from pathlib import Path
from typing import Any

import pytest

from ingestion.parsers.base import (
    DocFormat,
    EmbeddedImage,
    ParagraphItem,
    ParserResult,
    Table,
)
from ingestion.profiler import DocumentProfiler, ProfileSignals

PROFILER = DocumentProfiler()


def _pr(
    fmt: DocFormat,
    paras: int,
    headings: int,
    lists: int,
    images: int = 0,
    tables: int = 0,
    max_depth: int = 1,
    extra_text: str = "",
) -> ParserResult:
    """Synthetic ParserResult carrying the given structural counts."""
    items: list[ParagraphItem] = []
    order = 0
    for _ in range(headings):
        items.append(
            ParagraphItem(text="Heading", kind="heading", doc_order=order, heading_level=max_depth)
        )
        order += 1
    for _ in range(lists):
        items.append(ParagraphItem(text="step item", kind="list_item", doc_order=order))
        order += 1
    for _ in range(max(paras - headings - lists, 0)):
        items.append(ParagraphItem(text=f"body text {extra_text}", kind="text", doc_order=order))
        order += 1
    imgs = [
        EmbeddedImage(image_bytes=b"x", alt_text="", doc_order=0, ext="png", sha256=f"s{i}")
        for i in range(images)
    ]
    tbls = [Table(rows=[["a"]], headers=None, doc_order=0) for _ in range(tables)]
    return ParserResult(
        source_path=Path(f"/synthetic/doc.{fmt}"),
        doc_format=fmt,
        doc_title="synthetic",
        paragraphs=items,
        embedded_images=imgs,
        tables=tbls,
    )


def _sig(**overrides: Any) -> ProfileSignals:
    """ProfileSignals with sane defaults; override only the fields under test."""
    base: dict[str, Any] = {
        "paragraphs": 100,
        "headings": 10,
        "max_depth": 2,
        "list_items": 10,
        "images": 0,
        "tables": 0,
        "img_density": 0.0,
        "head_density": 0.1,
        "list_ratio": 0.1,
        "tickbox_density": 0.0,
    }
    base.update(overrides)
    return ProfileSignals(**base)


# --- classify rule v3 各分支 (docx/pptx — profile() 唔 call pypdfium2) ---


def test_p1_sop_imgdense_drive_manual() -> None:
    # DRIVE manual signature: depth=4 + img_density~0.43 + list_ratio~0.6 (三重信號)
    r = PROFILER.profile(_pr("docx", 585, 50, 354, images=253, max_depth=4), Path("/x.docx"))
    assert r.profile == "P1_sop_imgdense"
    assert r.confidence >= 0.9
    assert not r.fallback_applied


def test_p1_sop_text_runbook() -> None:
    # n8n runbook: list_ratio~0.15 + headings=14, 低圖
    r = PROFILER.profile(_pr("docx", 292, 14, 45, images=0, max_depth=2), Path("/x.docx"))
    assert r.profile == "P1_sop_text"


def test_p2_prose_guideline() -> None:
    # AI-Governance-Guideline: head_density~0.11 + list_ratio~0.08
    r = PROFILER.profile(_pr("docx", 219, 25, 18, images=0, max_depth=2), Path("/x.docx"))
    assert r.profile == "P2_prose"


def test_p3_slide_imgdense_pptx() -> None:
    # pptx 一律 P3;img_density 0.165 ≥ 0.12 → imgdense 子型
    r = PROFILER.profile(_pr("pptx", 237, 18, 0, images=39), Path("/x.pptx"))
    assert r.profile == "P3_slide_imgdense"


def test_p3_slide_text_pptx() -> None:
    r = PROFILER.profile(_pr("pptx", 643, 29, 0, images=0), Path("/x.pptx"))
    assert r.profile == "P3_slide_text"


def test_p5_form_heading_sparse() -> None:
    # Registration form: headings=0 + list=0 + images=0
    r = PROFILER.profile(_pr("docx", 84, 0, 0, images=0), Path("/x.docx"))
    assert r.profile == "P5_form"


def test_p5_form_tickbox_density() -> None:
    # Questionnaire: heading 多但 tick-box / Q-marker 密 → P5_form 在 P2 之前救
    r = PROFILER.profile(
        _pr("docx", 40, 6, 0, images=0, extra_text="□ Q1: your answer:"),
        Path("/x.docx"),
    )
    assert r.profile == "P5_form"


def test_too_small_noise() -> None:
    r = PROFILER.profile(_pr("docx", 7, 3, 0), Path("/x.docx"))
    assert r.profile == "too_small"


def test_fallback_unknown_to_p2_prose() -> None:
    # 21 paras (≥20 v3 門檻) 唔 too_small;list_ratio 0.14 + headings 3 → 無 rule 命中
    # → D7 fallback P2_prose + low confidence + fallback_applied
    r = PROFILER.profile(_pr("docx", 21, 3, 3, max_depth=2), Path("/x.docx"))
    assert r.profile == "P2_prose"
    assert r.fallback_applied
    assert r.confidence < 0.5


# --- PDF pre-OCR 分流 (_classify_pdf_preocr 直接,避真 file) ---


def test_pdf_preocr_scan_empty_ratio() -> None:
    assert PROFILER._classify_pdf_preocr(_sig(pdf_empty_ratio=0.8, pdf_avg_chars=5.0)) == (
        "P4_scan_imgdense",
        0.95,
        False,
    )


def test_pdf_preocr_scan_thin_avg() -> None:
    verdict = PROFILER._classify_pdf_preocr(_sig(pdf_empty_ratio=0.2, pdf_avg_chars=120.0))
    assert verdict is not None
    assert verdict[0] == "P4_scan_imgdense"


def test_pdf_preocr_slide_low_avg() -> None:
    # born-digital deck ~300 chars/page → P3
    verdict = PROFILER._classify_pdf_preocr(_sig(pdf_empty_ratio=0.0, pdf_avg_chars=300.0))
    assert verdict is not None
    assert verdict[0] == "P3_slide_text"


def test_pdf_preocr_text_pdf_falls_through() -> None:
    # procedure ~2000 chars/page → None (落通用結構規則)
    assert PROFILER._classify_pdf_preocr(_sig(pdf_empty_ratio=0.0, pdf_avg_chars=2000.0)) is None


def test_pdf_preocr_none_when_probe_failed() -> None:
    # probe 失敗 (all None) → 唔 short-circuit,落 structural
    assert PROFILER._classify_pdf_preocr(_sig()) is None


# --- signal extraction ---


def test_extract_signals_densities() -> None:
    s = PROFILER._extract_signals(
        _pr("docx", 100, 10, 20, images=30, tables=5, max_depth=3), Path("/x.docx")
    )
    assert (s.paragraphs, s.headings, s.list_items, s.images, s.tables, s.max_depth) == (
        100,
        10,
        20,
        30,
        5,
        3,
    )
    assert s.img_density == pytest.approx(0.3)
    assert s.list_ratio == pytest.approx(0.2)
    assert s.head_density == pytest.approx(0.1)


def test_extract_signals_empty_doc_no_div_zero() -> None:
    s = PROFILER._extract_signals(_pr("docx", 0, 0, 0), Path("/x.docx"))
    assert s.img_density == 0.0  # denom guarded to 1


def test_extract_signals_tickbox_counted() -> None:
    s = PROFILER._extract_signals(
        _pr("docx", 30, 0, 0, extra_text="□ Q3: your answer:"), Path("/x.docx")
    )
    assert s.tickbox_density > 0.0


# --- deterministic (H4: pure rule, no LLM) ---


def test_deterministic() -> None:
    pr = _pr("docx", 585, 50, 354, images=253, max_depth=4)
    a = PROFILER.profile(pr, Path("/x.docx"))
    b = PROFILER.profile(pr, Path("/x.docx"))
    assert (a.profile, a.confidence, a.fallback_applied) == (
        b.profile,
        b.confidence,
        b.fallback_applied,
    )


# --- PDF text-layer probe integration (真 scan sample;skipif 缺 sample) ---

_SCAN_DIR = (
    Path(__file__).resolve().parents[2]
    / "docs"
    / "06-reference"
    / "01-sample-doc"
    / "scanned_pdf_sample"
)


@pytest.mark.skipif(not _SCAN_DIR.exists(), reason="scan sample gitignored (local-only)")
def test_pdf_probe_real_scan_is_p4() -> None:
    scans = sorted(_SCAN_DIR.glob("*.pdf"))
    assert scans, "scan sample dir empty"
    # 空 ParserResult (skip Docling OCR) + source_path → profiler 行 pypdfium2 pre-OCR
    pr = ParserResult(source_path=scans[0], doc_format="pdf", doc_title=scans[0].stem)
    r = PROFILER.profile(pr, scans[0])
    assert r.profile == "P4_scan_imgdense"
    assert r.signals.pdf_empty_ratio is not None
    assert r.signals.pdf_empty_ratio >= 0.5
