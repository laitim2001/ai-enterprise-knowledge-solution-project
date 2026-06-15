# W76 progress — profile read surface(ADR-0056 層 A 段③ 前置)

## Day 1 — 2026-06-15(kickoff)

**Context**:用戶 review 三層 UI fit 後揀「甲 — 開 backend profile read surface」。Grounding
揭示 profiler 結果 fire-and-forget(ingest compute → route preset → profile 本身冇 persist /
冇 expose),`DocumentSummary` / `DocumentDetail` 無 profile 欄位 → 段③ UI 無 data 可 fetch。
本 phase = 段③ 之前嘅純後端前置(persist + read API)。

**R6 grounding(plan kickoff)**:
- `DocConfigStore` pattern(`doc_config_store.py`)= Protocol + InMemory + Postgres(table
  `document_configs`)+ `make_doc_config_store(settings)` factory,ADR-0023 backing → mirror 開
  `DocProfileStore`(table `document_profiles`)。
- `ProfileResult`(`profiler.py:89`)= profile(Literal 9 類)/ confidence / signals
  (`ProfileSignals` 13 field dataclass)/ fallback_applied;`@dataclass` 非 Pydantic → expose
  要轉 Pydantic schema。
- `DocumentSummary` / `DocumentDetail`(`listing.py:18/117`)全部由 Azure Search index chunks
  aggregate,**無 documents 持久化表**(doc 只活喺 index;per doc_config_store comment)→ 原文件
  bytes ingest 後冇保留 → **backfill re-profile 不可行**(§3.3 caveat)。
- ingest persist 插入點 = `documents.py:758` `_route_profile_preset` 旁(`result.profile` 已 available)。

**設計決策**(詳 plan §3):新 `DocProfileStore`(語義分離,唔塞 DocConfig)/ expose 兩粒度
(detail 完整 signals / summary 輕量 label+confidence)/ 現有 KB 要 re-index 先有 profile
(drive-images-1 production-preserve 唔 re-index,verify 用新 upload)。

**紀律自檢**:H1 ✅(ADR-0056 層 A 範圍,沿用 ADR-0023/0050 pattern)/ H2 ✅(零新 dep)/
H4 ✅(rule label,純結構信號)/ H7 ✅(零 frontend → 唔 trigger)/ H6 ✅(F4 test)。

**Plan 落地**:W76 folder + plan.md(active)+ checklist.md(F1-F5)+ progress.md。

**Commits**:
- (本 entry)docs(planning): W76 kickoff
