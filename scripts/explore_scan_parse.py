"""W72-prep(throwaway):單份 scan PDF 過 EKP DoclingPdfParser — 驗 OCR 入庫可行 + robustness + 計時。

閉合 ADR-0056 OQ-A 嘅 gating 問題:P4 偵測到之後,EKP 現有 parser 能唔能真係 parse
scan(行 OCR)+ 唔 crash(之前 AI demonstration.pdf 見過 std::bad_alloc)。跑最細一份
(03_VND 5 頁)確認;OCR 慢,background 跑。
"""

from __future__ import annotations

import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "backend"))
SCAN = ROOT / "docs" / "06-reference" / "01-sample-doc" / "scanned_pdf_sample"

from ingestion.parsers import select_parser  # noqa: E402

TARGET = SCAN / "03_VND_vietnamese.pdf"  # 最細 5 頁


def main():
    print(f"[parsing] {TARGET.name}(scan,要 OCR — 慢)...", flush=True)
    t0 = time.monotonic()
    try:
        result = select_parser(TARGET).parse(TARGET)
    except Exception as e:  # noqa: BLE001
        dt = time.monotonic() - t0
        print(f"[EXCEPTION] {type(e).__name__}: {e}(耗時 {dt:.1f}s)")
        return
    dt = time.monotonic() - t0
    headings = [p for p in result.paragraphs if p.kind == "heading"]
    lists = [p for p in result.paragraphs if p.kind == "list_item"]
    print(f"\n=== 結果 ===")
    print(f"parse_failed={result.parse_failed}  error={result.parse_error}")
    print(f"耗時={dt:.1f}s")
    print(f"paras={len(result.paragraphs)}  headings={len(headings)}  "
          f"list_items={len(lists)}  images={len(result.embedded_images)}  tables={len(result.tables)}")
    rt = result.raw_text
    print(f"raw_text 長度={len(rt)} chars")
    print(f"raw_text 頭 400 字:\n{rt[:400]}")


if __name__ == "__main__":
    main()
