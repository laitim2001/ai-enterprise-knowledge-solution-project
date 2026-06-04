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

### Commits
- _(pending — F0 ADR + plan kickoff commit)_

### Next
- F1 KbConfig 加 `chunker_max_images_per_chunk` 欄 → F2 ingest wiring → F3 tests

### Blockers / carry-over
- 無。R4(live reindex verify 需 Azure + backend)= nice-to-have,pytest 覆蓋邏輯。
