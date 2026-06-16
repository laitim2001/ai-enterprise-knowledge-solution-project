"""W85 F0.1 — offline chunk-structure comparison: heading_aware vs layout_aware per profile.

DIAGNOSTIC ONLY — zero production change. Reads representative docx samples, parses each
once, runs BOTH chunkers, and reports structure metrics so the W85 F0 gate can judge
whether profile-differentiated chunking has structural merit (before investing in the
H1 framework).

Scope: docx only — pptx resolves to slide_based(=layout) and scan/pdf OCR resolves to
layout, so heading-vs-layout contrast only exists for docx (per plan §1 grounding).

Metrics per (sample, strategy):
  - chunks            : total chunk count
  - tokens            : mean / p50 / max / min of chunk_token_count
  - sections          : unique section_path count
  - frag(chunks/sec)  : mean chunks per section (1.0 = each section is one whole chunk;
                        >1 = sections split across chunks; heading_aware should be ~1)
  - max_frag          : worst-case chunks for a single section
  - images            : total embedded images / chunks carrying images / max in one chunk
  - low_value         : chunks flagged low_value_flag

Run: backend/.venv/Scripts/python.exe scripts/w85_chunk_structure_compare.py
"""

from __future__ import annotations

from collections import Counter
from pathlib import Path
from statistics import mean, median

from ingestion.chunker.strategies import select_chunker
from ingestion.parsers import select_parser
from ingestion.profiler import DocumentProfiler

# Representative docx per profile (docs/06-reference/01-sample-doc/). docx-only by design.
_SAMPLE_DIR = Path(__file__).resolve().parents[2] / "docs" / "06-reference" / "01-sample-doc"
_SAMPLES: list[str] = [
    "DRIVE_User Manual_0603(FA)_FNA-Fixed Asset Management_v0.02.docx",  # expect P1 圖密SOP
    "DRIVE_User Manual_0605(GL)_FNA-General Ledger Management_v0.02.docx",  # expect P1 圖密SOP
    "AI-Governance-Guideline-for-Employees.docx",  # expect P2 散文
    "DCE_Integration_Platform_Implementation_Plan.docx",  # expect P2 散文 / 報告
    "AI_Project_Registration_Form.docx",  # expect P5 表單
]
_STRATEGIES = ["heading_aware", "layout_aware"]

_PROFILER = DocumentProfiler()


def _struct_metrics(chunks: list) -> dict[str, object]:
    if not chunks:
        return {"chunks": 0}
    toks = [c.chunk_token_count for c in chunks]
    sec_counter: Counter[tuple[str, ...]] = Counter()
    for c in chunks:
        sec_counter[tuple(c.section_path)] += 1
    img_counts = [len(c.embedded_image_positions) for c in chunks]
    return {
        "chunks": len(chunks),
        "tok_mean": round(mean(toks)),
        "tok_p50": round(median(toks)),
        "tok_max": max(toks),
        "tok_min": min(toks),
        "sections": len(sec_counter),
        "frag": round(mean(sec_counter.values()), 2),
        "max_frag": max(sec_counter.values()),
        "img_total": sum(img_counts),
        "img_chunks": sum(1 for x in img_counts if x > 0),
        "img_max": max(img_counts),
        "low_value": sum(1 for c in chunks if c.low_value_flag),
    }


def main() -> None:
    for name in _SAMPLES:
        src = _SAMPLE_DIR / name
        if not src.exists():
            print(f"\n### MISSING: {name}")
            continue
        parser = select_parser(src)
        result = parser.parse(src)
        if result.parse_failed:
            print(f"\n### PARSE FAILED: {name} — {result.parse_error}")
            continue
        prof = _PROFILER.profile(result, src)
        print(f"\n{'=' * 78}")
        print(f"{name}")
        print(
            f"  profile={prof.profile} conf={prof.confidence:.2f} "
            f"fmt={result.doc_format} embedded_images={len(result.embedded_images)}"
        )
        for strategy in _STRATEGIES:
            chunker = select_chunker(result.doc_format, strategy)
            chunks = chunker.chunk(result)
            m = _struct_metrics(chunks)
            print(
                f"  [{strategy:13}] chunks={m['chunks']:>3} "
                f"tok(mean/p50/max/min)={m.get('tok_mean')}/{m.get('tok_p50')}/"
                f"{m.get('tok_max')}/{m.get('tok_min')}  "
                f"sections={m.get('sections')} frag={m.get('frag')} "
                f"max_frag={m.get('max_frag')}  "
                f"img(tot/chunks/max)={m.get('img_total')}/{m.get('img_chunks')}/"
                f"{m.get('img_max')}  low_value={m.get('low_value')}"
            )


if __name__ == "__main__":
    main()
