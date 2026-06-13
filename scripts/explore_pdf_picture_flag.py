"""W72-prep(throwaway):驗 D2 — Docling generate_picture_images flag 對 born-digital PDF 抽圖嘅影響。

坐實 review D2:EKP `pdf_parser.py` 用預設 DocumentConverter()(generate_picture_images
=False)→ PDF 圖抽唔到(get_image 返 None)。本 script 對照 False(EKP 現狀)vs True
(修復方向),數 PICTURE items 同 get_image 成功數,確認「開 flag 即解」係咪事實。
"""

from __future__ import annotations

import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "backend"))
SAMPLE = ROOT / "docs" / "06-reference" / "01-sample-doc"

from docling.datamodel.base_models import InputFormat  # noqa: E402
from docling.datamodel.pipeline_options import PdfPipelineOptions  # noqa: E402
from docling.document_converter import DocumentConverter, PdfFormatOption  # noqa: E402
from docling_core.types.doc import DocItemLabel  # noqa: E402

TARGET = SAMPLE / "AI-Governance-Procedure.pdf"  # born-digital text PDF,有圖文,15 頁


def count_pics(generate: bool):
    opts = PdfPipelineOptions()
    opts.generate_picture_images = generate
    conv = DocumentConverter(
        format_options={InputFormat.PDF: PdfFormatOption(pipeline_options=opts)}
    )
    t0 = time.monotonic()
    doc = conv.convert(TARGET).document
    pics = got = 0
    for item, _ in doc.iterate_items():
        if getattr(item, "label", None) == DocItemLabel.PICTURE:
            pics += 1
            try:
                if item.get_image(doc) is not None:
                    got += 1
            except Exception:  # noqa: BLE001
                pass
    dt = time.monotonic() - t0
    print(f"generate_picture_images={generate}: PICTURE items={pics}, "
          f"get_image 非 None={got}, 耗時={dt:.1f}s", flush=True)
    return pics, got


def main():
    print(f"=== D2 驗證:{TARGET.name} Docling picture flag 對照 ===", flush=True)
    p0, g0 = count_pics(False)   # EKP 現狀(預設)
    p1, g1 = count_pics(True)    # 修復方向
    print("\n=== 結論 ===")
    print(f"現狀(flag off):{p0} 張 PICTURE,成功抽 {g0} 張 → EKP 入庫 {g0} 張")
    print(f"修復(flag on) :{p1} 張 PICTURE,成功抽 {g1} 張 → 開 flag 後入庫 {g1} 張")
    if g0 == 0 and g1 > 0:
        print("→ 坐實:PDF 圖入唔到 index 係 generate_picture_images 預設 False 所致;開 flag 即解。")
    elif g0 == 0 and g1 == 0 and p1 > 0:
        print("→ 更深問題:開 flag 都抽唔到,要再查 Docling backend / scale。")
    elif p1 == 0:
        print("→ 此 PDF 根本無 Docling PICTURE label(圖可能係 vector / 背景)— 換有 raster 圖嘅 PDF 再驗。")


if __name__ == "__main__":
    main()
