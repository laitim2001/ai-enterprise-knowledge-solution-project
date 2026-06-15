# W79 progress — Profile 人手覆寫 write surface(ADR-0058)

## Day 1 — 2026-06-15(kickoff)

**Context**:W78 落地 profiling frontend 三層 UI(L3 override select static)。用戶 2026-06-15 揀 write surface
scope = ① Profile override(② threshold persist 不做 — threshold 五輪實證已最佳,改門檻 risk>reward)。

**ADR-0058 Accepted**(本 session):override 機制 = 套 `preset_for(profile)` 落 per-doc config(reuse ADR-0050
`doc_config_store`)+ `DocProfileInfo` 加 `manual_override` annotation(保 W76 read-only system fact 分層 +
可解釋)+ D6 守 reuse W73。Alternatives:A 改 system profile field(reject — 破壞分層失可解釋)/ B 純套 preset
唔記 label(reject — UI 唔反映 override)/ C(採用)套 preset + annotation。

**落點 ground(plan kickoff)**:
- profile persist + route preset 喺 `_run_ingest_pipeline`(documents.py:609,persist 813-821)+
  `_route_profile_preset`(834-866,D6 守 skip-if-manual)
- doc config CRUD 喺 `doc_config.py`(separate route);override 套 preset **唔用** `_route_profile_preset`
  (嗰個 D6 skip manual)→ explicit user action 直接 `preset_for` + `doc_config_store.upsert` 覆蓋
- `DocProfileStore`(W76)profile JSONB 存全 `DocProfileInfo` → 加 field 自動 serialize;舊 row deserialize
  `DocProfileInfo(**row)` 無 `manual_override` key → default null(向後相容)

**設計決定**:
- L2 summary.profile = effective(`manual_override ?? profile`,backend resolve);L3 detail 透明見 system auto
  + human override(可解釋)
- override 套 preset = **覆蓋** per-doc config(per D3「套 preset」非 merge);user 可之後 L3 fine-tune

**紀律自檢**:H1 ✅(ADR-0058 Accepted)/ H2 ✅(零新 dep)/ H4 ✅(層 A)/ H6 ✅(F1.5 route test)/ H7 ✅
(override select static → functional,視覺不變)/ Karpathy ✅(reuse preset_for/doc_config_store/W73 守)。

**Plan 落地**:W79 folder + plan.md(active)+ checklist.md(F1-F3)+ progress.md + ADR-0058。

**F1-F2 implement(Day 1)**:
- **F1 backend**:`DocProfileInfo` 加 `manual_override`(保 system fact);`PUT /kb/{kb_id}/docs/{doc_id}/profile`
  + `ProfileOverrideRequest`(套 `preset_for` 覆蓋 per-doc config + 記 override;404 未 ingest / 422 無 preset /
  503 無 store;用單獨 store helper 唔 require ingestion services);`_run_ingest_pipeline` re-ingest preserve
  manual_override;`list_documents` L2 effective(override → confidence null);`test_doc_profile_override` 8 tests。
- **F2 frontend**:`documents.ts` `manual_override` + `overrideProfile` API;L3 `doc-config-tab` select wire
  (onChange → mutation → invalidate doc-detail + doc-config + toast)+ `DocProfileBadge` effective + 已覆寫標示。

**F3 驗證 + browser override(Day 1)**:
- **F3.1**:pytest 22 passed(override 8 + read-surface 14,zero regression)+ ruff 0 + mypy 新 code clean
  (剩 line 116 `_engine_or_503` Any pre-existing baseline)+ frontend type-check 0 + lint 零新 warning +
  build ✓ 15/15 pages。**mypy 修**:`preset_for(payload.profile)` str vs DocProfile Literal → `cast(DocProfile, ...)`
  (runtime-safe,invalid → .get None → 422)。
- **F3.2 browser override 端到端 PASS**:起全套 infra(backend 重啟 pick up 新 endpoint)+ ingest 臨時 doc
  (n8n P1_sop_text 0.85)→ playwright L3 揀 P1_sop_imgdense → **backend persist**:profile(auto)=P1_sop_text 保留 +
  manual_override=P1_sop_imgdense + per-doc config max_images=80/section_anchored=True/anchor_cap=5(P1_sop_imgdense
  preset 覆蓋舊 cap=20)+ L2 effective(profile=P1_sop_imgdense,confidence null)。**UI**:L3 badge「P1 圖密SOP · 已人手
  覆寫」+ override 標「已覆寫 · 系統原判 P1 文字SOP」+ select=P1_sop_imgdense + signals 不變(可解釋)。驗完 DELETE
  temp doc 還原 6 docs 零污染。

**Retro(Day 1)**:
- **backend 改 code 必須重啟先生效**(關鍵坑):初次 override 撞 **PUT /profile 404** — running backend 係改
  endpoint **之前**起嘅舊 code(Python 唔 hot-reload,uvicorn 無 --reload)。`TaskStop` + 重起 backend(dual-process
  TaskStop 乾淨殺 + port free)後 PASS。**教訓**:改 backend route/schema 後,browser/API 驗前必須重啟 backend。
- **store 用單獨 helper 唔塞 ingestion deps**:override 只需 doc_profile_store + doc_config_store,**唔用**
  `_ingestion_deps_or_503`(嗰個 require embedder/populator/chunker 否則 503)→ override 唔需 ingestion services。
- **保 system fact 分層 = 可解釋核心**(ADR-0058 C):override 後 system auto profile/confidence/signals **全部保留**,
  manual_override 額外 annotation;UI 同時見「P1 圖密SOP(effective)」+「系統原判 P1 文字SOP」→ 人可介入 + 可追溯。
- **DocProfileStore Postgres persist**:backend restart 後 n8n profile + override 仍喺(DATABASE_URL set → Postgres)。
- **mypy cast for API-boundary str → Literal**:`payload.profile`(free-form str)→ `preset_for` 期望 DocProfile
  Literal;`.get` runtime handle invalid(None → 422),用 `cast` narrow 騙 mypy(runtime guard 已 safe)。
- **交棒**:② threshold persist 不做(實證已最佳);per-KB/global profile override 未有需求;override → re-route 唔做。

**Commits**:
- `a7eb758` docs(planning): W79 kickoff + ADR-0058 — profile override write surface
- `1adf2e0` feat(api): W79 F1-F2 profile override write surface (ADR-0058)
- (closeout)docs(planning): W79 closeout — full PASS
