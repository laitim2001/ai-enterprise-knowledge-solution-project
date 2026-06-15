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

**F1-F4 implement(Day 1)**:
- **F1 schema + store**:`api/schemas/doc_profile.py`(`DocProfileInfo` + `DocProfileSignals` +
  `from_result` TYPE_CHECKING-only ingestion seam,無 runtime reverse dep)+
  `kb_management/doc_profile_store.py`(Protocol + InMemory + Postgres table `document_profiles`
  + factory,verbatim mirror `doc_config_store`)。ruff + mypy --strict 新 code 0。
- **F2 persist**:server.py lifespan wire `make_doc_profile_store` + `_IngestionDeps.doc_profile_store`
  field + `_ingestion_deps_or_503` getattr + `_run_ingest_pipeline` best-effort
  `upsert(from_result(..., profiled_at=now.isoformat()))`(advisory `profile_persist_failed`,唔 fail ingest)。
- **F3 expose**:`DocumentSummary.profile` + `profile_confidence`(L2 輕量)/ `DocumentDetail.profile`
  (L3 完整 signals)+ `_doc_profile_store(request)` helper + list(`list_for_kb` map)/ detail(`get`)
  route best-effort join(缺 → null,純 additive 既有 field bit-identical)。
- **F4 test**:`test_doc_profile_read_surface.py` 14 test(store CRUD 6 + factory 2 + from_result 2 +
  API join 4)。**regression 57 passed**(documents-listing / profile-routing / doc-config-store /
  profiler 零 break)。mypy --strict 新 code 0 + ruff 0。
- **R3 deviation**:F4.2 e2e ingest persist test 改為元件覆蓋(`from_result` + store upsert,已分別測),
  inline persist guard 邏輯 trivial(`if profile and store: upsert(...)`),唔 mock Azure orchestrator
  (Karpathy §1.2 simplicity;e2e ingest 涉 Embedder/IndexPopulator/Azure Search mock 過重)。
- **驗證註**:ruff `ruff check .` project way 報 67 pre-existing(含 server.py truststore E402 baseline);
  我新 file 零 ruff error;server.py 我加嘅 import 有 `# noqa: E402` 不增 error。mypy --strict 對
  transitive import 報 pre-existing(storage / parsers,我冇 touch),exit 非零但新 code 0(git diff 核實)。

**Commits**:
- `ff5672b` docs(planning): W76 kickoff
- (本次)feat(api): W76 profile read surface — persist + expose(F1-F4)
