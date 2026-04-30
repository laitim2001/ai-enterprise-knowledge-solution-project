"""Sample manual structure inspector (per OQ-Q17 + Q18 in docs/decision-form.md §3).

Inspect .docx files to answer:
- Q17: Heading style consistency (H1/H2/H3 usage rate, fallback to font-size hardcoding)
- Q18: Embedded image format coverage (PNG / JPG / WMF / EMF / SVG / HEIC)

Usage (run from repo root):
    backend/.venv/Scripts/python.exe -m scripts.inspect_docx_structure <path-to-docx-or-dir>

Exit codes:
    0  Inspection report printed
    1  Path not found / no .docx files

Stdlib only (zipfile + xml.etree). No Docling / python-docx dependency in W1
— W2 ingestion pipeline switches to Docling per architecture.md §3.3.
"""

from __future__ import annotations

import sys
import zipfile
from collections import Counter
from pathlib import Path
from xml.etree import ElementTree as ET

_W_NS = "{http://schemas.openxmlformats.org/wordprocessingml/2006/main}"
_DOCUMENT_XML = "word/document.xml"
_MEDIA_PREFIX = "word/media/"
_HEADING_STYLES = {"Heading1", "Heading2", "Heading3", "Heading4", "Heading5"}


def _iter_paragraphs(document_xml: bytes):
    root = ET.fromstring(document_xml)
    body = root.find(f"{_W_NS}body")
    if body is None:
        return
    yield from body.iter(f"{_W_NS}p")


def _paragraph_style(p: ET.Element) -> str | None:
    p_pr = p.find(f"{_W_NS}pPr")
    if p_pr is None:
        return None
    p_style = p_pr.find(f"{_W_NS}pStyle")
    return p_style.get(f"{_W_NS}val") if p_style is not None else None


def _paragraph_has_hardcoded_font_size(p: ET.Element) -> bool:
    """Detect if paragraph relies on hardcoded font size instead of style."""
    for r_pr in p.iter(f"{_W_NS}rPr"):
        sz = r_pr.find(f"{_W_NS}sz")
        if sz is not None:
            return True
    return False


def inspect_docx(path: Path) -> dict[str, object]:
    """Inspect a single .docx; return summary dict."""
    summary: dict[str, object] = {
        "path": str(path),
        "size_kb": round(path.stat().st_size / 1024, 1),
    }

    with zipfile.ZipFile(path) as zf:
        names = zf.namelist()

        media_files = [n for n in names if n.startswith(_MEDIA_PREFIX) and n != _MEDIA_PREFIX]
        format_counts = Counter(Path(n).suffix.lower().lstrip(".") for n in media_files)
        summary["embedded_images_count"] = len(media_files)
        summary["embedded_image_formats"] = dict(format_counts)

        if _DOCUMENT_XML not in names:
            summary["error"] = "no word/document.xml — not a valid .docx"
            return summary

        with zf.open(_DOCUMENT_XML) as f:
            document_xml = f.read()

    style_counter: Counter[str] = Counter()
    paragraphs_with_hardcoded_size = 0
    paragraphs_total = 0
    table_count = sum(1 for _ in ET.fromstring(document_xml).iter(f"{_W_NS}tbl"))

    for p in _iter_paragraphs(document_xml):
        paragraphs_total += 1
        style = _paragraph_style(p)
        if style:
            style_counter[style] += 1
        if _paragraph_has_hardcoded_font_size(p):
            paragraphs_with_hardcoded_size += 1

    heading_paragraphs = sum(c for s, c in style_counter.items() if s in _HEADING_STYLES)
    summary["paragraphs_total"] = paragraphs_total
    summary["table_count"] = table_count
    summary["heading_style_counts"] = {
        s: style_counter[s] for s in sorted(style_counter) if s in _HEADING_STYLES
    }
    summary["other_style_counts"] = {
        s: style_counter[s] for s in sorted(style_counter) if s not in _HEADING_STYLES
    }
    summary["paragraphs_with_hardcoded_font_size"] = paragraphs_with_hardcoded_size
    summary["heading_coverage_pct"] = (
        round(heading_paragraphs / paragraphs_total * 100, 1) if paragraphs_total else 0.0
    )

    return summary


def aggregate(reports: list[dict[str, object]]) -> dict[str, object]:
    total_images = sum(int(r.get("embedded_images_count", 0)) for r in reports)
    fmt_total: Counter[str] = Counter()
    for r in reports:
        for fmt, count in (r.get("embedded_image_formats") or {}).items():  # type: ignore[union-attr]
            fmt_total[fmt] += int(count)
    return {
        "total_files": len(reports),
        "total_embedded_images": total_images,
        "image_formats_aggregate": dict(fmt_total),
    }


def _print_report(reports: list[dict[str, object]]) -> None:
    for r in reports:
        print(f"\n=== {r['path']} ({r['size_kb']} KB) ===")
        if "error" in r:
            print(f"  ERROR: {r['error']}")
            continue
        print(f"  paragraphs: {r['paragraphs_total']}, tables: {r['table_count']}")
        print(
            f"  heading style coverage: {r['heading_coverage_pct']}% "
            f"({r['heading_style_counts']})",
        )
        print(f"  paragraphs w/ hardcoded font size: {r['paragraphs_with_hardcoded_font_size']}")
        print(
            f"  embedded images: {r['embedded_images_count']} "
            f"(formats={r['embedded_image_formats']})",
        )

    if len(reports) > 1:
        agg = aggregate(reports)
        print("\n=== Aggregate ===")
        print(f"  total files: {agg['total_files']}")
        print(f"  total embedded images: {agg['total_embedded_images']}")
        print(f"  image formats: {agg['image_formats_aggregate']}")


def main(argv: list[str]) -> int:
    if len(argv) < 2:
        print("usage: python -m scripts.inspect_docx_structure <path-to-docx-or-dir>", file=sys.stderr)
        return 1
    target = Path(argv[1])
    if not target.exists():
        print(f"path not found: {target}", file=sys.stderr)
        return 1

    paths = (
        sorted(target.rglob("*.docx"))
        if target.is_dir()
        else [target]
        if target.suffix.lower() == ".docx"
        else []
    )
    if not paths:
        print(f"no .docx files at {target}", file=sys.stderr)
        return 1

    reports = [inspect_docx(p) for p in paths]
    _print_report(reports)
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv))
