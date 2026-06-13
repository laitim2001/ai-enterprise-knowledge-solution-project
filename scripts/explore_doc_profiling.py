"""W72-prep 勘查(throwaway,非 production):rule-based document profiling 信號驗證。

目的:用 EKP 現有 parser(DoclingDocx / DoclingPdf / Pptx)parse `docs/06-reference/
01-sample-doc` 下嘅真實文件,抽結構信號(heading 數 / 深度 / 圖密度 / list 比例 /
table 數),用透明 rule 初判 profile(P1-P5),睇信號分唔分得開、邊界 case 多唔多。

呢個係 discuss 階段嘅 evidence-gathering,唔改任何 production code。跑完得出數據
就刪 / 或留 scripts/ 重跑。
"""

from __future__ import annotations

import sys
import traceback
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "backend"))
SAMPLE_DIR = ROOT / "docs" / "06-reference" / "01-sample-doc"

from ingestion.parsers import select_parser  # noqa: E402


def extract_signals(result) -> dict:
    paras = result.paragraphs
    P = len(paras) or 1
    headings = [p for p in paras if p.kind == "heading"]
    lists = [p for p in paras if p.kind == "list_item"]
    H = len(headings)
    L = len(lists)
    I = len(result.embedded_images)
    T = len(result.tables)
    depth = max((p.heading_level or 0 for p in headings), default=0)
    return {
        "format": result.doc_format,
        "paras": len(paras),
        "headings": H,
        "depth": depth,
        "lists": L,
        "images": I,
        "tables": T,
        "img_density": round(I / P, 3),
        "head_density": round(H / P, 3),
        "list_ratio": round(L / P, 3),
        "img_per_head": round(I / H, 2) if H else 0.0,
    }


def classify(s: dict) -> tuple[str, str]:
    """Initial transparent rule — 呢個就係要驗證準唔準嘅嘢(threshold 靠估)。"""
    fmt = s["format"]
    if fmt == "pptx":
        return "P3_slide", "format=pptx"
    H, depth, I = s["headings"], s["depth"], s["images"]
    img_d, head_d, list_r = s["img_density"], s["head_density"], s["list_ratio"]
    if I >= 10 and H <= 3:
        return "P4_scan_imgdense", f"images={I} headings={H}"
    if H >= 8 and depth >= 2 and img_d >= 0.1:
        return "P1_structured_sop", f"H={H} depth={depth} img_d={img_d}"
    if head_d < 0.04 and img_d < 0.05:
        return "P2_prose", f"head_d={head_d} img_d={img_d}"
    return "P5_mixed", "no clear signal"


def main() -> None:
    files = sorted(SAMPLE_DIR.iterdir())
    print(f"=== 勘查 {len(files)} 份文件 ===\n")
    rows = []
    unsupported = []
    for f in files:
        if not f.is_file():
            continue
        suffix = f.suffix.lower()
        if suffix not in (".docx", ".pdf", ".pptx"):
            unsupported.append((f.name, suffix))
            print(f"[SKIP unsupported] {f.name} ({suffix})")
            continue
        try:
            print(f"[parsing] {f.name} ...", flush=True)
            result = select_parser(f).parse(f)
            if result.parse_failed:
                print(f"  [parse_failed] {result.parse_error}")
                rows.append((f.name, {"format": suffix[1:], "ERROR": result.parse_error}, "PARSE_FAIL", ""))
                continue
            sig = extract_signals(result)
            prof, reason = classify(sig)
            rows.append((f.name, sig, prof, reason))
            print(f"  -> {prof}  ({reason})")
        except Exception as e:  # noqa: BLE001
            print(f"  [EXC] {type(e).__name__}: {e}")
            traceback.print_exc()
            rows.append((f.name, {"EXC": str(e)}, "EXCEPTION", ""))

    print("\n\n=== 信號表(markdown)===\n")
    hdr = "| 文件 | fmt | paras | head | depth | lists | imgs | tbl | img_d | head_d | list_r | → profile |"
    print(hdr)
    print("|---|---|---|---|---|---|---|---|---|---|---|---|")
    for name, s, prof, _ in rows:
        if "format" in s and "ERROR" not in s and "EXC" not in s:
            short = name if len(name) <= 42 else name[:39] + "..."
            print(
                f"| {short} | {s['format']} | {s['paras']} | {s['headings']} | "
                f"{s['depth']} | {s['lists']} | {s['images']} | {s['tables']} | "
                f"{s['img_density']} | {s['head_density']} | {s['list_ratio']} | **{prof}** |"
            )
        else:
            print(f"| {name} | — | — | — | — | — | — | — | — | — | — | {prof} |")

    print("\n=== profile 分佈 ===")
    from collections import Counter
    dist = Counter(prof for _, _, prof, _ in rows)
    for p, c in dist.most_common():
        print(f"  {p}: {c}")
    if unsupported:
        print(f"\n=== unsupported(EKP 唔 parse)===")
        for name, suf in unsupported:
            print(f"  {name} ({suf})")


if __name__ == "__main__":
    main()
