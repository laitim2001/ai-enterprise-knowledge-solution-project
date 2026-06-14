# W74 — PDF picture ingestion progress

## Day 1 — 2026-06-14 — Phase kickoff(ADR-0057 Accepted)

### 做咗咩
- 用戶開段②c → **STOP(H1)**:D8 PDF picture = ingestion behavior + storage layout change + ADR-0056 D8 明文「stakeholder 要知 + 獨立 ADR」+ re-index 成本。
- AskUserQuestion 兩決策:① generate_picture_images 開法 → **per-KB(thread `extract_embedded_images`)** ② re-index 策略 → **按需(用戶手動)**。
- 寫 **ADR-0057**(Accepted,`docs/adr/0057-pdf-picture-ingestion-per-kb.md`)+ README index entry + bottom-note next NNNN 修正(stale 0047 → 0058)。
- 建 phase folder `W74-pdf-picture-ingestion/` + plan(active,locked)+ checklist。

### 關鍵 grounding(ADR 階段做齊)
- `select_parser(path)` 只食 path(無 kb_config)→ 要加 keyword-only `extract_images`。
- `KbConfig.extract_embedded_images`(預設 False)= 現有 per-KB image toggle,可 thread 統一控制 PDF 抽圖 + extraction。
- `_run_ingest_pipeline`:kb_config 讀喺 `select_parser` 之後 → 要**移前**。
- 自訂 converter:`PdfPipelineOptions(generate_picture_images=True)` + `DocumentConverter(format_options=...)`(Docling 自帶零新 dep)。
- 成本 +19%(只 extract_embedded_images=True PDF);scan bad_alloc robustness = ADR-0056 D8 上游另議。

### 決策
- per-KB thread `extract_embedded_images`(對齊現有語意,零新旋鈕,production-preserve)。
- 按需 re-index(reindex reuse `_run_ingest_pipeline` 自動繼承 thread)。

### Commits
- (本 entry 對應 kickoff commit:ADR-0057 + README + W74 plan/checklist/progress)

### Next(F1)
- `DoclingPdfParser.__init__(generate_picture_images)` + `select_parser(extract_images)` + `_run_ingest_pipeline` wire。

### Blockers / carry-overs
- 無 blocker。段②d(方案 A)/ ③(UI)= 後續,本段唔掂。

---

## Day 1 (cont) — 2026-06-14 — F1+F2 落地 + closeout

### 做咗咩
- **F1**:`DoclingPdfParser.__init__(generate_picture_images)`(public attr + 自訂 `PdfPipelineOptions` converter / 預設 bit-identical)+ `select_parser(source, *, extract_images=False)`(`.pdf` thread)+ `documents.py:_run_ingest_pipeline`(kb_config 讀移前 + `extract_images=kb_config.extract_embedded_images`)。
- **F2**:`test_parser_factory.py` 3 thread test(pdf extract_images=True → flag / default False / docx unaffected)。

### Gate = PASS
- W74 code mypy clean(7 errors 全 pre-existing docling stub + Protocol `doc_format` str/Literal,git diff 核冇 touch error 行)。
- ruff clean + **23 pass + 7 skip**(7 skip = `test_pdf_parser.py` real-PDF deferred per ADR-0019;parser thread + reindex 唔 break)。
- 真效果由 `explore_pdf_picture_flag.py`(committed `ec18b2a`,0→10/10)背書 — 唔重複 100s real-PDF integration。

### 關鍵實作決定
- thread = keyword-only `extract_images` default False → 現有 caller + docx/pptx bit-identical。
- `generate_picture_images` public attr(對齊 `doc_format` introspection)俾 unit test 驗 thread,唔加 test-only state。
- kb_config 讀移前至 `select_parser` 之前(現時喺其後)— 唯一 reorder。
- reindex(W46)reuse `_run_ingest_pipeline` → 自動繼承 per-KB 抽圖 thread(零額外改動)。

## Closeout retro — 2026-06-14

**Phase verdict:PASS**。ADR-0057 段②c 落地完成,AC1-AC5 全過:
- AC1 per-KB 抽圖(select_parser thread)/ AC2 production-preserve(default False bit-identical)/ AC3 語意統一(thread extract_embedded_images)/ AC4 零 churn(keyword-only)/ AC5 H6 test ✅

**Commits**:
| Hash | 內容 |
|---|---|
| `6ea0559` | ADR-0057 Accepted + W74 kickoff |
| `75a0167` | F1-F2 per-KB PDF picture extraction |

**教訓**:
1. **H1 正確 STOP**:用戶開段②c,我 STOP 走 ADR(ADR-0057)而非直接 implement — D8 係 ingestion behavior + storage layout + re-index 成本,ADR-0056 D8 明文 stakeholder + 獨立 ADR。AskUserQuestion 確認 per-KB + 按需 = production-preserve 路線。
2. **thread 現有 toggle 勝過新旋鈕**:`extract_embedded_images` 已係 per-KB image gate,thread 落 parser 統一語意,零新旋鈕 + 對齊現有。
3. **真效果靠已 commit 勘查背書**:explore_pdf_picture_flag.py(0→10/10)已驗,unit thread test 驗 wiring,唔重複慢 integration。

### 段 ②d / ③ 交棒記錄
- **段 ②d 方案 A section 級錨定**(W71 §5 net-new)= `P1_sop_imgdense` 完整 render;PDF 圖入庫後(本段)+ W73 preset(markers/cap)+ 方案 A 三者齊先係 PDF 圖類完整流程。**未做**。
- **段 ③ 三層 UI**:profile badge / 文件畫像 / admin 調 PROFILE_PRESETS mapping + **`extract_embedded_images` toggle UI**(現有但 PDF 抽圖語意要 surface);卡 H7 OQ-B。
- **PDF 圖類驗證**:現有 PDF KB 開 `extract_embedded_images=True` + re-index(W46)→ 肉眼核 PDF 圖入 chat;留 smoke(用戶 trigger)。

### 本 phase 無 deferred `[ ]`(checklist 全 tick;real-PDF integration 由 explore script 背書代替)。後續 = 段②d/③,等用戶 trigger(rolling JIT)。
