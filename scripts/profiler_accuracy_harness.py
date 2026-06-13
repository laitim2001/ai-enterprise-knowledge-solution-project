"""W72 F3 — profiler accuracy harness (real-parse 30+7 sample → ground truth ≥90%).

NOT throwaway: this is the ADR-0056 層 A AC1 gate verification. It real-parses every
sample-doc file via the *production* parsers (no hardcoded signals — guards R2 signal
drift between v2 勘查 hardcoded SIGNALS and real ParserResult), runs DocumentProfiler,
and compares the resulting family vs hand-labelled ground truth.

scan PDFs: fed an empty ParserResult + source_path so the profiler's pypdfium2 pre-OCR
path short-circuits to P4 WITHOUT triggering Docling OCR (avoids ~382s/file).

Local-only (sample-doc gitignored). Run from repo root:
    backend/.venv/Scripts/python.exe scripts/profiler_accuracy_harness.py
"""

from __future__ import annotations

import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "backend"))
SAMPLE = ROOT / "docs" / "06-reference" / "01-sample-doc"
SCAN = SAMPLE / "scanned_pdf_sample"

from docling.datamodel.base_models import InputFormat  # noqa: E402
from docling.datamodel.pipeline_options import PdfPipelineOptions  # noqa: E402
from docling.document_converter import DocumentConverter, PdfFormatOption  # noqa: E402

from ingestion.parsers.base import ParserResult  # noqa: E402
from ingestion.parsers.docx_parser import DoclingDocxParser  # noqa: E402
from ingestion.parsers.pdf_parser import DoclingPdfParser  # noqa: E402
from ingestion.parsers.pptx_parser import PptxParser  # noqa: E402
from ingestion.profiler import DocumentProfiler  # noqa: E402

# born-digital PDF: parse with do_ocr=False — profiler classify uses pypdfium2 pre-OCR
# page-density + text-layer heading/list counts, NEVER the OCR'd image-region text. OCR
# on image-heavy decks is slow + risks std::bad_alloc (ADR-0056 D8) with zero classify
# value, so disable it for the harness. Reuses DoclingPdfParser._parse_inner extraction
# by swapping its converter.
_PDF_PARSER_NO_OCR = DoclingPdfParser()
_pdf_opts = PdfPipelineOptions()
_pdf_opts.do_ocr = False
_PDF_PARSER_NO_OCR._converter = DocumentConverter(
    format_options={InputFormat.PDF: PdfFormatOption(pipeline_options=_pdf_opts)}
)

# ground truth: real filename → expected family (P1 / P2 / P3 / FORM / SMALL / P4)
EXPECTED: dict[str, str] = {
    # --- docx ---
    "AI_Project_Registration_Form.docx": "FORM",
    "AI-Governance-Guideline-for-Employees.docx": "P2",
    "DCE_Integration_Platform_Implementation_Plan.docx": "P2",
    "DRIVE_User Manual_0601(AR)_FNA-AR Management_v0.03.docx": "P1",
    "DRIVE_User Manual_0602(AP)_FNA-AP Management_v0.03.docx": "P1",
    "DRIVE_User Manual_0603(FA)_FNA-Fixed Asset Management_v0.02.docx": "P1",
    "DRIVE_User Manual_0604(CB)_FNA-Cash and Bank Management_v0.02.docx": "P1",
    "DRIVE_User Manual_0605(GL)_FNA-General Ledger Management_v0.02.docx": "P1",
    "DRIVE_User Manual_0606(BM)_FNA-Budget Management_v0.02.docx": "P1",
    "ekp-smoke-test.docx": "SMALL",
    "ekp-smoke-test-v2.docx": "SMALL",
    "n8n-PDT-Upgrade-Runbook.docx": "P1",
    "Virtual_Boss_3.5_Information_Intake_Questionnaire.docx": "FORM",
    "Virtual_Boss_3.5_Introduction_and_Brief.docx": "P2",
    # --- pptx (一律 P3) ---
    "AI_Automation_Team_Update_EN.pptx": "P3",
    "Day1_Master_Deck_v2 (1) (1).pptx": "P3",
    "DigitalMarketing_DCE.pptx": "P3",
    "ekp-smoke-test.pptx": "P3",
    "FY26 BP - DCE - Customer Platform Implemenation & Development (FY26).pptx": "P3",
    "FY26 BP Template V1 (1).pptx": "P3",
    "FY26_Budget_Proposal_v2.pptx": "P3",
    "How_to_Approach_Automation.pptx": "P3",
    "IT_Automation_Priority_Matrix_RBS_Workshop_Ricoh (1) (1).pptx": "P3",
    "Nagarro_Alignment_FY26.pptx": "P3",
    "Session1_AI_Governance_EN (1).pptx": "P3",
    "Session1_AI_Governance_ZH (4).pptx": "P3",
    "Workshop_Followup_Slides.pptx": "P3",
    # --- pdf ---
    "AI demonstration_20260329 (4).pdf": "P3",
    "AI-Governance-Procedure.pdf": "P1",
    "ekp-smoke-test.pdf": "SMALL",
}

PROFILER = DocumentProfiler()


def family(label: str) -> str:
    if label.startswith("P1"):
        return "P1"
    if label.startswith("P2"):
        return "P2"
    if label.startswith("P3"):
        return "P3"
    if label.startswith("P4"):
        return "P4"
    if label == "P5_form":
        return "FORM"
    if label == "too_small":
        return "SMALL"
    return "UNKNOWN"


def parse_doc(path: Path) -> ParserResult:
    ext = path.suffix.lower()
    if ext == ".docx":
        return DoclingDocxParser().parse(path)
    if ext == ".pptx":
        return PptxParser().parse(path)
    if ext == ".pdf":
        return _PDF_PARSER_NO_OCR.parse(path)
    raise ValueError(f"unsupported ext {ext}")


def main() -> None:
    rows = []
    t0 = time.monotonic()

    # content docx / pptx / born-digital pdf — real parse
    for path in sorted(SAMPLE.glob("*.*")):
        if path.suffix.lower() not in (".docx", ".pptx", ".pdf"):
            continue
        exp = EXPECTED.get(path.name)
        if exp is None:
            print(f"[skip:no-GT] {path.name}", flush=True)
            continue
        pr = parse_doc(path)
        r = PROFILER.profile(pr, path)
        rows.append((path.name, r.profile, family(r.profile), exp, r.confidence, r.fallback_applied))
        print(f"  parsed {path.name} → {r.profile}", flush=True)

    # scan pdf — empty ParserResult (skip OCR) + pypdfium2 pre-OCR P4
    for path in sorted(SCAN.glob("*.pdf")):
        pr = ParserResult(source_path=path, doc_format="pdf", doc_title=path.stem)
        r = PROFILER.profile(pr, path)
        rows.append((path.name, r.profile, family(r.profile), "P4", r.confidence, r.fallback_applied))

    # --- report ---
    print(f"\n{'=' * 88}\n=== profiler accuracy ({time.monotonic() - t0:.0f}s) ===\n{'=' * 88}")
    print("| 文件 | label | family | expected | conf | fb | 結果 |")
    print("|---|---|---|---|---|---|---|")
    for name, label, fam, exp, conf, fb in rows:
        ok = fam == exp
        short = name if len(name) <= 46 else name[:43] + "..."
        print(f"| {short} | {label} | {fam} | {exp} | {conf:.2f} | {'Y' if fb else ''} | {'OK' if ok else 'MISS'} |")

    total = len(rows)
    hit = sum(1 for _, _, fam, exp, _, _ in rows if fam == exp)
    content = [r for r in rows if r[3] != "SMALL"]
    c_hit = sum(1 for _, _, fam, exp, _, _ in content if fam == exp)
    print(f"\n全部:{hit}/{total} = {hit / total * 100:.1f}%")
    print(f"扣 SMALL 噪音 (content,AC1 gate ≥90%):{c_hit}/{len(content)} = {c_hit / len(content) * 100:.1f}%")

    misses = [(n, fam, exp) for n, _, fam, exp, _, _ in rows if fam != exp]
    print(f"\n=== MISS ({len(misses)}) ===")
    for n, fam, exp in misses:
        print(f"  {n}: rule={fam} vs GT={exp}")


if __name__ == "__main__":
    main()
