# W72 — 文件畫像引擎 progress

## Day 1 — 2026-06-13 — Phase kickoff + R6 grounding + plan lock

### 做咗咩
- 用戶拍板「同意 ADR-0056,開始執行」→ ADR-0056 + `docs/adr/README.md` index status `Proposed`→`Accepted`(2026-06-13 用戶 session 確認;批准範圍 = 層 A 文件畫像 + 路由)。
- AskUserQuestion 確認首 phase scope → 用戶揀「**Profiler engine 先**」(層 A 三段:Profiler engine → render-side → 三層 UI)。
- R6 grounding(plan-text recursive scope):讀 `parsers/base.py`(ParserResult 契約)/ `chunker/strategies.py`(chunk_strategy=auto precedent)/ `explore_doc_profiling_v2.py`(classify_v2 + ground truth)/ ingestion module 結構。
- 建 phase folder `docs/01-planning/W72-document-profiling-engine/` + 寫 `plan.md`(active,locked)+ `checklist.md`。

### 關鍵發現(R6)
1. **ParserResult 現有欄位足夠**:`paragraphs`(kind + heading_level)/ `embedded_images` / `tables` + `@property raw_text|heading_tree|paragraphs_total` → v2 全部信號可抽,**零契約改動**。
2. **D2 每頁文字密度缺口** → **設計決策**:改由 profiler 對 PDF 自做 `pypdfium2` pre-OCR pass 順帶計,**唔改 ParserResult 契約**(Karpathy §1.3 surgical:P4 偵測本來就要 pre-OCR pass,page density 同 pass 攞;改契約影響面遠大過需求;page metadata 目前只 profiler 一 consumer = YAGNI)。**偏離 ADR D2 字面屬 implementation 非 architectural**,已記 plan §1 + plan changelog(R3)。
3. **P4 必須 pre-OCR**:Docling OCR 後 `embedded_images`=0 + heading 誤判 → 偵測信號失效;pypdfium2 pre-OCR text-layer 探測(7/7 驗證 空比例 1.0)係唯一可靠路。順帶令 scan PDF short-circuit 判 P4 **唔觸發 Docling OCR**(秒級,避 382s/檔)。
4. **profiler standalone**:本 phase 唔接入 `orchestrator.py`(接入 = routing 段),production ingestion 行為 bit-identical → **零侵入**,降低 H1 風險面。

### 決策
- 首 phase scope = 純分類引擎(D1 taxonomy + D2 rule v3 信號 + 信心度 + D7 fallback),**唔含** routing / UI / LLM 保險 / D8 PDF picture / 方案 A。
- profiler signature = `profile(parser_result, source_path)` — PDF 分支用 source_path 做 pypdfium2 pre-OCR。
- ProfileResult 帶 `signals: dict`(透明展示)→ 後續 UI 段 L3 直接消費,前瞻設計但本 phase 唔起 UI。

### Commits
- (本 entry 對應 commit:ADR-0056 Accept + W72 plan/checklist/progress kickoff)

### Next(Day 2)
- F1 起 `backend/ingestion/profiler.py`:`ProfileResult` schema + 信號抽取 + classify v3。

### Blockers / carry-overs
- 無 blocker。後續段依賴:render-side 段卡 D8 PDF picture(`generate_picture_images`)+ 方案 A net-new;UI 段卡 H7 OQ-B(profiling mockup)。本 phase 唔受影響。

---

## Day 1 (cont) — 2026-06-13 — F1+F2+F3 落地 + accuracy gate PASS

### 做咗咩
- **F1 profiler 核心**:`backend/ingestion/profiler.py` — `ProfileResult`/`ProfileSignals` schema + `DocumentProfiler`(信號抽取 + tick-box scan + classify v3 六類 + 信心度 + D7 fallback)。mypy --strict exit 0(`--explicit-package-bases --follow-imports=silent`;pypdfium2 無 stub → `# type: ignore[import-untyped]`)+ ruff clean。
- **F2 PDF pre-OCR**:`_probe_pdf_text_layer` pypdfium2 per-page(空比例 + 每頁字數),P4 short-circuit 唔觸發 Docling OCR。
- **F3 unit test**:`tests/test_profiler.py` 19 test(classify 全分支 + 信號 + D7 fallback + deterministic + 真 scan probe → P4),synthetic ParserResult CI-safe(sample-doc gitignored)+ skipif 真 scan。19 passed + ruff clean。
- **F3 accuracy harness**:`scripts/profiler_accuracy_harness.py` 真 parse 30 + 7 scan → 對照 ground truth。

### Accuracy gate(AC1)= **PASS**
- **content(扣 SMALL,gate ≥90%)= 34/34 = 100.0%**;7 scan 全判 P4(7/7);全部 35/37 = 94.6%。
- 剩 2 miss = `ekp-smoke-test-v2.docx`(P2 vs SMALL)+ `ekp-smoke-test.pdf`(P3 vs SMALL)= **SMALL artifact**,門檻 20 預期副作用(扣 SMALL 後唔計)。

### R2 信號漂移 finding(真實發生 + 已修)
- 第一次 harness:`n8n-PDT-Upgrade-Runbook.docx` 唯一 content miss(FORM vs GT P1),conf=0.75 = tickbox branch 觸發。
- probe 坐實:真 parse n8n list_r=0.154 + head=14(**命中 P1_sop_text**),但 tickbox_d=0.188(checklist ☐ marker)喺 P1 之前搶到 form。對照 questionnaire list=0(唔命中 P1)+ tickbox_d=0.736。
- **修正**:`_classify_structural` 把 tickbox→P5_form branch **移到 P1_sop_text 之後** — checklist-style runbook(有 SOP 結構)先命中 P1 救返;真問卷(list=0 唔命中 P1)仍落 tickbox 保。重跑 harness:n8n→P1,content 33/34→**34/34=100%**,零 regression。
- 教訓:tickbox 信號對「帶 checklist 嘅 SOP」vs「純問卷」有 ambiguity;結構信號(list_ratio + headings)優先級必須高於 marker 信號。

### 過程坑(已處理)
- harness 第一次跑 `AI demonstration` deck 觸發 Docling RapidOCR + `std::bad_alloc`(page 30,layout 預處理階段,ADR-0056 D8 robustness caveat)。OCR 對 profiler classify 零價值(靠 pypdfium2 pre-OCR)→ 改 harness PDF 用 `do_ocr=False`(reuse `DoclingPdfParser._parse_inner` 換 converter)。`do_ocr=False` 減 OCR 但解唔到 layout-stage bad_alloc(Docling skip 該頁 continue,profiler 靠 pypdfium2 不受影響)。

### Next(F4 收爐)
- memory 更新 + closeout retro + ADR-0056 段 ② 交棒記錄 + plan status → closed。
