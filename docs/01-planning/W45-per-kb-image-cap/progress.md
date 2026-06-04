# W45 — Per-KB Ingest-Time Chunker Image Cap · Progress

> Daily progress + decisions + commits + 結尾 retro。每 daily commit 對應一個 Day-N entry(R2)。

---

## Day 1 — 2026-06-04

### Context / kickoff
W44 closed(Gate PARTIAL→PASS,全域 chunker cap 8 落地)+ pushed(`708c091`)。用戶揀 W45 candidate = **per-KB 圖數 cap → KbConfig**(roadmap W44 carry-over)。

### 決策
- **H1 觸發 + 批准**:per-KB 圖數 cap 改 `architecture.md §3.3` chunker 參數化模型 + 加 `KbConfig` 欄 + ingest-time config-scope(ADR-0040 只 cover query-time)→ H1。Chris AskUserQuestion 批准「H1 + ADR-0042」。
- **None 語意**:Chris 揀「None=繼承,正整數=cap」(最簡;per-KB 不能設無 cap,只全域 level 設得到)。解決 W43 `None`=inherit 同 chunker `None`=無cap 嘅撞車。
- **R6 grep 驗證(plan kickoff)**:確認 `kb_config` 已 thread 到 ingest(`documents.py:556-582`,W20 F4.2),wiring 缺口只剩 chunker 全域 singleton 化 per-KB。避免 plan 估錯實際 surface。

### Done
- F0.1 ADR-0042 寫成 Accepted(`docs/adr/0042-per-kb-ingest-time-chunker-image-cap.md`)— 延伸 ADR-0040 到 ingest-time + ADR-0041 全域 cap 到 per-KB;factory wiring + inherit 路徑 reuse singleton;5 alternatives documented
- F0.2 ADR README index 加 0042 row + next available 0042 → 0043
- R1 phase 三件套建立(plan/checklist/progress)

### F1-F3 implementation(同日)
- **F1**:`KbConfig` 加 `chunker_max_images_per_chunk: int | None = None`(`backend/api/schemas/kb.py`)+ docstring 解 None=inherit / +int=cap / per-KB 不能設無 cap。經既有 `PATCH /kb/{kb_id}/settings`(`kb.py:219` full-replacement)自動可設,無新 endpoint。
- **F2 wiring**:
  - `server.py` 加 `_make_ingestion_chunker(cap)` factory → `app.state.make_ingestion_chunker`;全域 singleton `app.state.ingestion_chunker` 保留(inherit 路徑 + 既有 caller)
  - `documents.py` 加純 helper `_select_chunker(deps, kb_config)`:`cap_override=None`(或無 kb_config / 無 factory)→ singleton(零 construct);設值 → factory 砌 per-ingest chunker。`_IngestionDeps` 加 `make_chunker` 欄;`_run_ingest_pipeline` orchestrator construct 改用 `_select_chunker(deps, kb_config)`
  - route 同 concrete `LayoutAwareChunker` 解耦(只 call factory)
- **F3 tests**:`test_per_kb_image_cap.py` +5 test(None→singleton 且 factory 唔 call / 無 kb_config→singleton / per-KB cap→factory(N) 且 chunker.max_images_per_chunk==N / factory 缺→fallback singleton / KbConfig back-compat 缺 key→None)

### 驗證(三軸)
- pytest:新 5 passed;既有受影響 129 passed(test_chunker 48 / test_orchestrator / test_documents_route / test_kb_metadata_patch / test_effective_config / test_kb_management / test_documents_detail / test_kb_reindex)= **0 regression**
- ruff check + format:我改動 file 全 clean(test import 排序 + documents.py format 已修)
- mypy --strict(全 import 解析):我改動行(kb.py 欄 / server.py factory / documents.py 116-148 + call site / test)**零 new error**;132 pre-existing 散落 42 file(eval/ / crag.py / query.py / routes/kb.py:253 等)與我無關,唔掂(Karpathy §1.3)

### Commits
- `af4b94d` F0 — ADR-0042 + phase kickoff(plan/checklist/progress)
- _(pending — F1-F3 code + checklist/progress tick)_

### Next
- F4 doc-sync(architecture.md §3.3/§4.5 inline + roadmap)→ F5 closeout

### Blockers / carry-over
- 無。R4(live reindex verify 需 Azure + backend)= nice-to-have,pytest 覆蓋 resolution 邏輯 + W44 已測 chunker force-split 機制。
