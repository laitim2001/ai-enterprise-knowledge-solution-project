"""W72-prep 勘查(throwaway):scan PDF P4 偵測驗證 — text-layer 空比例信號。

閉合 ADR-0056 OQ-A(P4 scan 0 樣本)。用 pypdfium2 抽 text-layer(唔 OCR,秒級),
統計每份 scan PDF 嘅:總頁 / text-layer 空頁比例 / 平均 chars/page。

P4 核心假設:純 image scan 嘅 text-layer 空(冇文字層)→ 空比例高 = 可靠 P4 信號。
若 scan 已做過 OCR(text-layer 有字),則要靠次級信號(低 heading + 無 list + 表格密)。
"""

from __future__ import annotations

from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SCAN_DIR = ROOT / "docs" / "06-reference" / "01-sample-doc" / "scanned_pdf_sample"

import pypdfium2 as pdfium  # noqa: E402

EMPTY_CHAR_THRESHOLD = 10  # 一頁 < 10 chars 視為 text-layer 空


def probe(path: Path):
    pdf = pdfium.PdfDocument(str(path))
    n = len(pdf)
    chars = []
    for i in range(n):
        t = (pdf[i].get_textpage().get_text_range() or "").strip()
        chars.append(len(t))
    empty = sum(1 for c in chars if c < EMPTY_CHAR_THRESHOLD)
    avg = sum(chars) / n if n else 0
    return n, empty, round(empty / n, 2) if n else 0, round(avg, 1), chars[:6]


def main():
    files = sorted(SCAN_DIR.glob("*.pdf"))
    print(f"=== scan PDF P4 探測({len(files)} 份)===\n")
    print("| 文件 | 頁數 | 空頁 | 空比例 | 平均 chars/頁 | 判定 |")
    print("|---|---|---|---|---|---|")
    p4_count = 0
    ocrd = 0
    for f in files:
        n, empty, ratio, avg, head = probe(f)
        if ratio >= 0.5:
            verdict = "P4_scan(text-layer 空)"
            p4_count += 1
        elif avg < 200:
            verdict = "P4-ish(text-layer 稀薄)"
            p4_count += 1
        else:
            verdict = "有 text-layer(OCR'd / 數碼生成?)"
            ocrd += 1
        print(f"| {f.name} | {n} | {empty} | {ratio} | {avg} | {verdict} |")
        print(f"|   ↳ 頭幾頁 chars: {head} | | | | | |")
    print(f"\n=== 小結 ===")
    print(f"判 P4(scan / text-layer 空或稀薄):{p4_count}/{len(files)}")
    print(f"有實質 text-layer(OCR'd 或數碼):{ocrd}/{len(files)}")
    print("\n註:text-layer 空 = pypdfium2 抽唔到字 → 純 image scan → P4 信號成立。")
    print("    若有 text-layer = 已 OCR / 數碼發票 → 要次級信號(低 heading + 表格密)分辨。")


if __name__ == "__main__":
    main()
