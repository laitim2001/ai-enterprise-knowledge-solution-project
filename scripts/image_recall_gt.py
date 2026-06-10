"""W59 F2 — image-recall ground-truth worksheet builder + section→checksum expander.

Pure file ops (no Azure) — turns the F1 image catalog + an eval-set into a
section-range labeling worksheet, then expands the human-filled `expected_sections`
into `expected_images` checksums as a self-contained image-recall eval-set.

Two subcommands:

  worksheet  — build a labeling worksheet from --catalog (F1 dump) + --eval-set.
               Groups the doc's images into a `section_index` (each section gets a
               short `section_id` like S05, its image count + doc_order range +
               checksums), and lists the module's non-OOS queries with an empty
               `expected_sections: []` to fill. 222 images → you pick SECTIONS, not
               individual images (W59 plan §4 R1 + user decision 2026-06-10).

  expand     — read a filled worksheet, expand each query's `expected_sections`
               (section_id list) into the union of those sections' checksums →
               write a self-contained image-recall eval-set with
               ground_truth.expected_images (the F3 harness match key) +
               expected_image_sections (human-readable provenance). Does NOT touch
               the source eval-set (keeps its comments / keyword GT intact).

Usage (from project root):
    python -m scripts.image_recall_gt worksheet \
        --catalog reports/image_catalog_drive-images-1_<doc>.yaml \
        --eval-set docs/eval-set-v1-draft.yaml --module AR
    # ...fill expected_sections in the worksheet...
    python -m scripts.image_recall_gt expand \
        --worksheet reports/image_recall_worksheet_AR.yaml \
        --out docs/eval-set-image-recall-ar.yaml
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

import yaml

_LABELER_INSTRUCTIONS = (
    "Fill `expected_sections` for each query with the section_id(s) (e.g. [S05, S06]) "
    "from section_index whose images SHOULD accompany a correct answer. Pick SECTIONS, "
    "not individual images. Use section_path + doc_order_range + image_count to locate "
    "each section against the source document; open a checksum's blob_url from the F1 "
    "catalog if you need to eyeball a figure. Leave empty to exclude a query from the "
    "image-recall metric. Then run: python -m scripts.image_recall_gt expand."
)


def _load_yaml(path: Path) -> dict:
    return yaml.safe_load(path.read_text(encoding="utf-8"))


def _build_section_index(catalog: dict) -> list[dict]:
    """Group the catalog's images by source_section → ordered section_index.

    Each section keyed by its full source_section tuple; ordered by the section's
    minimum doc_order (reading flow). Sections with no source_section collapse under
    a "(no section)" bucket.
    """
    groups: dict[tuple[str, ...], dict] = {}
    for img in catalog.get("images", []):
        sec = img.get("source_section") or []
        key = tuple(str(s) for s in sec) if sec else ("(no section)",)
        g = groups.setdefault(key, {"checksums": [], "doc_orders": []})
        g["checksums"].append(str(img.get("checksum_sha256", "")))
        g["doc_orders"].append(int(img.get("doc_order", 0) or 0))

    ordered = sorted(groups.items(), key=lambda kv: min(kv[1]["doc_orders"]))
    index: list[dict] = []
    for i, (key, g) in enumerate(ordered, start=1):
        index.append(
            {
                "section_id": f"S{i:02d}",
                "section_path": list(key),
                "image_count": len(g["checksums"]),
                "doc_order_range": [min(g["doc_orders"]), max(g["doc_orders"])],
                "checksums": sorted(set(g["checksums"])),
            }
        )
    return index


def _is_module_query(q: dict, module: str) -> bool:
    """Non-OOS query whose keyword GT carries a `<MODULE>0x` section code (e.g. AR01)."""
    gt = q.get("ground_truth", {})
    if gt.get("expected_refusal", False):
        return False
    prefix = f"{module.upper()}0"
    return any(
        str(k).upper().startswith(prefix)
        for k in (gt.get("expected_answer_keywords") or [])
    )


def _cmd_worksheet(
    catalog_path: Path, eval_set_path: Path, module: str, out_path: Path
) -> int:
    catalog = _load_yaml(catalog_path)
    eval_set = _load_yaml(eval_set_path)
    cat_meta = catalog.get("metadata", {})

    section_index = _build_section_index(catalog)
    queries = [
        {
            "query_id": str(q.get("query_id", "")),
            "query_text": str(q.get("query_text", "")),
            "expected_answer_keywords": list(
                q.get("ground_truth", {}).get("expected_answer_keywords") or []
            ),
            "expected_sections": [],  # ← FILL ME with section_id(s) from section_index
        }
        for q in eval_set.get("queries", [])
        if _is_module_query(q, module)
    ]

    if not queries:
        print(
            f"No non-OOS '{module}' queries found in {eval_set_path} "
            f"(filter: keyword startswith '{module.upper()}0').",
            file=sys.stderr,
        )
        return 1

    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(
        yaml.safe_dump(
            {
                "metadata": {
                    "purpose": "W59 F2 image-recall GT labeling worksheet (section-range).",
                    "instructions": _LABELER_INSTRUCTIONS,
                    "module": module.upper(),
                    "kb_id": cat_meta.get("kb_id"),
                    "doc_id": cat_meta.get("doc_id"),
                    "doc_title": cat_meta.get("doc_title"),
                    "source_catalog": str(catalog_path),
                    "source_eval_set": str(eval_set_path),
                    "distinct_images_in_doc": cat_meta.get("distinct_images"),
                    "section_count": len(section_index),
                    "query_count": len(queries),
                },
                "section_index": section_index,
                "queries": queries,
            },
            sort_keys=False,
            allow_unicode=True,
        ),
        encoding="utf-8",
    )
    print(f"Worksheet written: {out_path}")
    print(
        f"{len(queries)} '{module.upper()}' queries, {len(section_index)} sections. "
        "Fill expected_sections per query, then run: expand.",
    )
    return 0


def _cmd_expand(worksheet_path: Path, out_path: Path) -> int:
    ws = _load_yaml(worksheet_path)
    meta = ws.get("metadata", {})
    sec_by_id = {s["section_id"]: s for s in ws.get("section_index", [])}

    queries_out: list[dict] = []
    labeled = 0
    unknown_ids: set[str] = set()
    for q in ws.get("queries", []):
        sections = list(q.get("expected_sections") or [])
        checksums: list[str] = []
        for sid in sections:
            sec = sec_by_id.get(str(sid))
            if sec is None:
                unknown_ids.add(str(sid))
                continue
            checksums.extend(sec.get("checksums", []))
        if sections:
            labeled += 1
        queries_out.append(
            {
                "query_id": q.get("query_id"),
                "query_text": q.get("query_text"),
                "kb_id": meta.get("kb_id"),
                "doc_id": meta.get("doc_id"),
                "ground_truth": {
                    "expected_images": sorted(set(checksums)),
                    "expected_image_sections": sections,
                },
            }
        )

    if unknown_ids:
        print(
            f"WARNING: unknown section_id(s) ignored: {sorted(unknown_ids)} "
            "(check the worksheet's section_index).",
            file=sys.stderr,
        )

    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(
        yaml.safe_dump(
            {
                "metadata": {
                    "eval_set": "image-recall (W59 F2)",
                    "module": meta.get("module"),
                    "kb_id": meta.get("kb_id"),
                    "doc_id": meta.get("doc_id"),
                    "source_eval_set": meta.get("source_eval_set"),
                    "source_catalog": meta.get("source_catalog"),
                    "source_worksheet": str(worksheet_path),
                    "total_queries": len(queries_out),
                    "labeled_queries": labeled,
                },
                "queries": queries_out,
            },
            sort_keys=False,
            allow_unicode=True,
        ),
        encoding="utf-8",
    )
    print(f"Image-recall eval-set written: {out_path}")
    print(f"{labeled}/{len(queries_out)} queries labeled with expected_sections.")
    return 0


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    sub = parser.add_subparsers(dest="cmd", required=True)

    ws = sub.add_parser(
        "worksheet", help="build labeling worksheet from catalog + eval-set"
    )
    ws.add_argument("--catalog", required=True, type=Path)
    ws.add_argument("--eval-set", required=True, type=Path)
    ws.add_argument("--module", default="AR")
    ws.add_argument("--out", type=Path, default=None)

    ex = sub.add_parser(
        "expand", help="expand filled worksheet → image-recall eval-set"
    )
    ex.add_argument("--worksheet", required=True, type=Path)
    ex.add_argument("--out", required=True, type=Path)

    args = parser.parse_args()
    if args.cmd == "worksheet":
        out = (
            args.out
            or Path("reports") / f"image_recall_worksheet_{args.module.upper()}.yaml"
        )
        return _cmd_worksheet(args.catalog, args.eval_set, args.module, out)
    if args.cmd == "expand":
        return _cmd_expand(args.worksheet, args.out)
    return 2


if __name__ == "__main__":
    raise SystemExit(main())
