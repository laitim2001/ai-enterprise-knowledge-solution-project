"""W85 F0.3.1 — dump candidate-profile chunks to diagnose existing-chunker harm.

DIAGNOSTIC ONLY — zero production change. Dumps layout_aware (production auto=layout
for docx) chunk detail for the two F0.1 candidates so the F0.3 gate can judge whether
a profile truly needs a DISTINCT chunker class (and what the concrete harm is):
  - P5 form (frag 9-10: a single heading section hard-split into 9-10 chunks)
  - P1 imgdense SOP (frag 2.4 + image-dense chunks; but W59-83 already addressed images)

Run: backend/.venv/Scripts/python.exe -m scripts.w85_chunk_dump
"""

from __future__ import annotations

from pathlib import Path

from ingestion.chunker.strategies import select_chunker
from ingestion.parsers import select_parser

_SAMPLE_DIR = Path(__file__).resolve().parents[2] / "docs" / "06-reference" / "01-sample-doc"


def _dump(name: str, fname: str, *, top_n_by_images: int | None = None) -> None:
    src = _SAMPLE_DIR / fname
    if not src.exists():
        print(f"\n### MISSING: {fname}")
        return
    result = select_parser(src).parse(src)
    if result.parse_failed:
        print(f"\n### PARSE FAILED: {fname}")
        return
    chunks = select_chunker(result.doc_format, "layout_aware").chunk(result)
    print(f"\n{'=' * 80}\n{name}: {fname}")
    print(f"  total chunks={len(chunks)} fmt={result.doc_format} embedded_images={len(result.embedded_images)}")

    selected = list(enumerate(chunks))
    if top_n_by_images is not None:
        selected = sorted(selected, key=lambda kv: -len(kv[1].embedded_image_positions))[:top_n_by_images]
        print(f"  (showing top {top_n_by_images} chunks by image count)")

    for idx, c in selected:
        text = c.chunk_text.replace("\n", " / ")[:160]
        print(
            f"  [#{idx:>2}] sec={c.section_path} tok={c.chunk_token_count} "
            f"img={len(c.embedded_image_positions)} kind={c.chunk_kind} low={c.low_value_flag}"
        )
        print(f"        text: {text}")


def main() -> None:
    # P5 form — dump ALL chunks (only 9-10; see how a single section is硬切)
    _dump("P5_form", "AI_Project_Registration_Form.docx")
    # P1 imgdense SOP — dump the 6 most image-dense chunks (see image-dense structure)
    _dump(
        "P1_FA",
        "DRIVE_User Manual_0603(FA)_FNA-Fixed Asset Management_v0.02.docx",
        top_n_by_images=6,
    )


if __name__ == "__main__":
    main()
