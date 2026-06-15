# W79 plan — Profile 人手覆寫 write surface(ADR-0058 落地)

**Status**: closed(2026-06-15,full PASS — backend + frontend + browser override 端到端 PASS)
**Kickoff**: 2026-06-15
**Phase 類型**: backend + frontend feature(H1 architectural — 新 endpoint + schema;ADR-0058 已 Accepted)
**ADR**: ADR-0058(profile manual override write surface)— 用戶 confirm scope = ① override only(② threshold 不做)

---

## §1 Context / 緣起

W78 落地 profiling frontend 三層 UI,但 **L3 override `select` static**(無 backend write,W78 §4-2)。用戶
2026-06-15 confirm 做 ① Profile override write surface。ADR-0058 定機制:override → 套對應 preset 落 per-doc
config(reuse `preset_for` + ADR-0050)+ `DocProfileInfo` 加 `manual_override` annotation(保 system fact +
可解釋)+ D6 守 reuse W73。

**落點 grounding(plan kickoff)**:
- `_run_ingest_pipeline`(`documents.py:609`)profile persist line 813-821 + route preset(`_route_profile_preset`
  834-866,D6 守 skip-if-manual)
- `DocProfileInfo`(`api/schemas/doc_profile.py`,W76)— 加 `manual_override`
- `doc_config_store.py`(ADR-0050)+ `preset_for`(`profile_presets.py` W73)— override 套 preset reuse
- L3 = `doc-config-tab.tsx`(W78 override select static)/ L2 = `kb/[id]/page.tsx` `ProfileBadge`(W78)

---

## §2 Scope / Deliverables

### F1 — backend override write surface
- **F1.1** `DocProfileInfo` 加 `manual_override: str | None = None`(向後相容 default null;系統 auto
  profile/confidence/signals 保留)。
- **F1.2** 新 endpoint `PUT /kb/{kb_id}/docs/{doc_id}/profile` body `ProfileOverrideRequest {profile: str}`:
  ① `preset_for(profile)` → `doc_config_store.upsert`(**覆蓋** 現有 per-doc config,explicit user action,
  唔用 `_route_profile_preset` D6 skip)② read 現有 `DocProfileInfo`(system auto)→ set `manual_override` →
  `doc_profile_store.upsert` ③ return updated `DocProfileInfo`。404 if no stored profile(未 ingest 唔可 override)。
- **F1.3** re-ingest preserve override — `_run_ingest_pipeline` profile persist(813-821)upsert 前 read 舊
  profile,如有 `manual_override` 保留(re-detect system fact 更新,override annotation 不失)。
- **F1.4** L2 summary resolve effective — `list_documents` join profile 時 `summary.profile = manual_override
  ?? profile`(L2 badge 顯示 effective;confidence 保留 auto)。
- **F1.5** test `test_doc_profile_override.py`(H6 backend route)— override 套 preset + manual_override persist
  + 覆蓋現有 config + 404 未 ingest + re-ingest preserve + summary effective resolve。
- **acceptance**:mypy --strict 新 code 0 + ruff 0 + pytest pass + 無 regression。

### F2 — frontend L3 override wire + effective 顯示
- **F2.1** `documents.ts` `DocProfileInfo` 加 `manual_override?: string | null`;新 `documentsApi.overrideProfile`
  (PUT /docs/{id}/profile)。
- **F2.2** L3 `doc-config-tab.tsx` override `select` wire onChange → mutation `overrideProfile` → invalidate
  doc-detail + doc-config + toast;如有 `manual_override` 標「已人手覆寫(系統原判 X)」+ select 預設 effective。
- **F2.3** L2 `kb/[id]/page.tsx` — backend resolve effective 後 badge 自動顯示 override 值(frontend 無需改
  badge 邏輯;確認 effective 正確顯示)。
- **acceptance**:type-check 0 + lint 零新 warning + build ✓;對齊 mockup(override select 由 static → functional,
  視覺不變 H7 OK)。

### F3 — 驗證 + closeout
- type-check + lint + build + pytest 全綠;browser 驗 override(服務 running:揀 profile → persist → L3/L2 反映)。
- closeout:plan closed + progress retro + ADR-0058 README index + memory。

---

## §3 設計原則(ADR-0058)

1. **保 system fact 分層**(W76)— override 唔改 system auto profile/confidence/signals,加 `manual_override`
   annotation;UI effective = `manual_override ?? profile`。
2. **reuse 最多現有基建** — `preset_for` / `doc_config_store` / W73 D6 守 — 新 code 最少。
3. **可解釋**(D6)— L3 同時見 system auto + human override;L2 顯示 effective。
4. **override 覆蓋 per-doc config**(D3「套 preset」非 merge)— user 可之後 L3 fine-tune;UI hint 提示。

---

## §4 Non-goals(明確唔做)
- **threshold persist**(② sub-feature)— 用戶 scope override only;Settings threshold 維持 static(W78 §4-2)。
- **改 profiler**(system detect 不變)。
- **per-KB / global profile override**(per-doc only,ADR-0050 layer)。
- **override → re-profile / re-route**(override 只套 preset + 記 label,唔重跑 profiler)。

---

## §5 Risks
- **R1 re-ingest preserve override edge case** — 緩解:F1.3 upsert 前 read 舊 merge + F1.5 test cover。
- **R2 override 覆蓋 user 手調 config** — per D3 預期行為;緩解:UI hint 提示 + L3 可重新 fine-tune。
- **R3 schema 加 field 向後相容** — `DocProfileInfo(**row)` 對舊 row 無 `manual_override` key → default null;
  緩解:optional default + F1.5 test deserialize 舊 shape。

---

## §6 紀律自檢(kickoff)
- **H1** ✅ architectural(新 endpoint + schema)— ADR-0058 已 Accepted(用戶 confirm scope)。
- **H2** ✅ 零新 dep(reuse psycopg / 現有 store)。
- **H4** ✅ 層 A override,無 Tier 2 feature。
- **H6** ✅ backend route test(F1.5)。
- **H7** ✅ L3 override select static → functional,**視覺不變**(唔 trigger H7)。
- **Karpathy** ✅ reuse 基建(preset_for / doc_config_store / W73 守)、surgical(現有 endpoint + schema 加)、
  goal(每 F acceptance + F3 全綠 + browser 驗)、think-before(ground 落點 + ADR-0058 設計決定 surface)。

---

## §7 Changelog
- 2026-06-15 kickoff — plan active,F1-F3 scope locked;ADR-0058 Accepted(用戶 confirm override only);落點 ground。
- 2026-06-15 F1 backend(commit `1adf2e0`)— DocProfileInfo.manual_override + PUT /docs/{id}/profile endpoint
  (套 preset_for 覆蓋 + 記 override + 404/422/503)+ re-ingest preserve + L2 effective(override→confidence null)
  + test 8 tests。**偏離**:override endpoint 用單獨 store helper(唔用 `_ingestion_deps_or_503`,嗰個 require
  embedder/populator/chunker 否則 503 — override 唔需 ingestion services)。
- 2026-06-15 F2 frontend(commit `1adf2e0`)— documents.ts type + overrideProfile API + L3 select wire
  (onChange → mutation → invalidate + toast)+ effective 顯示 + 已覆寫標示(系統原判保留)。
- 2026-06-15 **F3.2 browser 驗 override 端到端 PASS** — 起全套 infra + ingest 臨時 doc + L3 揀 P1_sop_imgdense →
  backend persist(manual_override + preset cap 80 覆蓋 + system auto 保留)+ L3/L2 effective + 系統原判保留。
  **坑記錄**:backend 改 code 後要重啟先 pick up 新 endpoint(初次撞 404 = running backend 舊 code;TaskStop
  + 重起後 PASS;store Postgres persist 過 restart)。
- 2026-06-15 closeout — plan closed full PASS,F1-F3 全 tick。
