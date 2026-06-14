# W74 — PDF picture ingestion checklist

> Atomic items per `plan.md` §2。`[ ]`→`[x]`,唔可刪未勾項。

## F1 — parser + select_parser + wire

- [x] `DoclingPdfParser.__init__(generate_picture_images: bool = False)` — True 用自訂 `PdfPipelineOptions` converter / False 維持預設(bit-identical)+ public attr
- [x] `select_parser(source, *, extract_images: bool = False)` — `.pdf` 傳 generate_picture_images
- [x] `_run_ingest_pipeline`:kb_config 讀移前至 select_parser 之前 + `extract_images=kb_config.extract_embedded_images`
- [x] mypy 0 + ruff 0(W74 code clean;7 errors 全 pre-existing docling stub + Protocol doc_format,git 核冇 touch)
- [x] 現有 parser_factory / documents / reindex test 全綠(23 pass + 7 skip)

## F2 — test(H6)

- [x] `select_parser(extract_images=True)` → `.pdf` parser generate_picture_images=True
- [x] `select_parser()` default / extract_images=False → generate_picture_images=False(production-preserve)
- [x] `.docx`/`.pptx` 路徑 bit-identical(`test_select_parser_docx_unaffected_by_extract_images`)
- [x] 真 born-digital PDF 抽圖 — 由 `explore_pdf_picture_flag.py`(committed,0→10/10)背書;EKP convention real-PDF deferred skip(`test_pdf_parser.py` 7 skip),唔重複 100s integration
- [x] pytest 綠(23 pass + 7 skip)

## F3 — 收爐

- [x] memory 更新(`project_inline_image_markers_w70` 或 vision — PDF picture 落地 + 連鎖)
- [x] closeout retro
- [x] 段②d(方案 A)/ ③(UI)交棒記錄
- [x] plan.md status → closed
