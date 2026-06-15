# ADR-0058: Profile 人手覆寫 write surface(L3 override → 套 preset + manual_override annotation)

**Date**: 2026-06-15
**Status**: Accepted — 用戶 2026-06-15 session confirm scope =「先做 ① Profile override」(write surface 兩個 sub-feature 揀其一;② threshold persist 留後續 / 不做)
**Approver**: Chris(技術 Lead,H1 架構)+ Stakeholder(scope)— 用戶 2026-06-15 AskUserQuestion confirm

## Context

ADR-0056 D4 定咗三層 UI(L2 一鍵 override / L3 逐 knob)+ D6「admin override 永遠優先於自動偵測」。
W76 落地 profile read surface(`DocProfileStore` + `DocumentDetail.profile` expose),W78 落地 frontend
三層 UI(L1/L2/L3 + Settings tab),但 **L3 override `select` 係 static**(無 backend write endpoint,per
W78 plan §4-2)。用戶 2026-06-15 confirm 做 ① Profile override write surface,令 L3 override 真正可用。

**既有基建(reuse,非重寫)**:
- `profile_presets.py`(W73)`preset_for(profile)` → 每 profile 對應 per-doc `DocConfig` preset。
- `doc_config_store.py`(ADR-0050)per-doc config CRUD(`PUT /kb/{id}/docs/{id}/config`)。
- W73 routing(`documents.py:_run_ingest_pipeline`)— ingest 套 auto preset **ONLY when no manual
  per-doc config**(D6 守已存在)。
- `DocProfileStore`(W76)`document_profiles(kb_id, doc_id, profile JSONB)`,profile = `DocProfileInfo`。

**關鍵 W76 分層**(`doc_profile_store.py` docstring):**profile 係 READ-ONLY system-detected fact**
(img density / 結構信號 → 分類),distinct from user-tunable `DocConfig`。override 設計必須保住呢個分層
——override 唔可以污染 system-detected profile(否則失可解釋:無法睇返系統原判 vs 人手改)。

## Decision

新 endpoint **`PUT /kb/{kb_id}/docs/{doc_id}/profile`** body `{profile: "<DocProfile label>"}`,行為:

1. **套對應 preset 落 per-doc config** — `preset_for(profile)` → `doc_config_store.upsert`(reuse ADR-0050
   layer)。override 即生效 query(per-doc config 已含 override preset)。preset 覆蓋現有 per-doc config 嘅
   preset-defined fields(per ADR-0056 D3「套 preset」+ mockup hint「改 profile 會套對應 preset 落下方旋鈕」;
   user 可之後 L3 逐 knob fine-tune)。
2. **`DocProfileInfo` 加 `manual_override: str | None`** annotation — **保留** system auto
   profile/confidence/signals,額外記人手覆寫 label(null = 無 override)。`DocProfileStore.upsert` 寫回。
3. **UI effective profile = `manual_override ?? profile`** — L2 badge / L3 card 顯示 override 值(優先),
   但保留 system auto 記錄(可解釋:睇返原判)+ 標「已人手覆寫」。

**D6 守 reuse W73 既有**:override 套 manual per-doc config → 將來 re-ingest `_run_ingest_pipeline` 套 auto
preset only when no manual config → **override 後唔覆蓋**。profile re-detect 仍 upsert system fact,但
**preserve `manual_override`**(re-ingest upsert 時 read 舊 profile 嘅 manual_override 保留)。

**唔做**(scope 收窄):
- **threshold persist**(② sub-feature)— 用戶 confirm scope = override only。profiler threshold 維持
  hardcode(`profiler.py` D2 v3 constant,五輪實證調好);Settings 文件分類規則 tab 嘅 threshold 維持 static
  display(W78 §4-2)。
- **改 profiler**(system detect 不變)。
- **profile override → re-route / re-profile**(override 只套 preset + 記 label,唔重跑 profiler)。

## Alternatives Considered

### A. override 直接改 profile store 嘅 system `profile` field
- **Reject**:破壞 W76 read-only system fact 分層 + 失可解釋(覆蓋後無法睇返系統原判)。違 ADR-0056 D6
  「保住可解釋」核心。

### B. override 純套 preset,唔記 label(無 manual_override field)
- **Reject**:L2/L3 badge 仍顯示 auto profile,override 唔反映喺 UI;mockup hint「改 profile」+ D6
  「override 優先顯示」唔兌現。

### C.(採用)套 preset 落 per-doc config + `DocProfileInfo` 加 `manual_override` annotation
- **Accept**:reuse 最多現有基建(`preset_for` / `doc_config_store` / W73 D6 守);保留 system fact +
  可解釋(system auto vs human override 都喺記錄);UI effective 反映 override;D6 兌現。

## Consequences

**Positive**:
- L3 override `select` 真正可用(W78 static → functional);mockup hint「改 profile 套 preset」兌現。
- reuse `preset_for` + `doc_config_store` + W73 D6 守 — 新 code 最少(schema 加 1 field + 1 endpoint +
  override 邏輯)。
- 可解釋:system auto profile/confidence/signals 保留,manual_override 額外 layer,UI effective = override ?? auto。

**Negative**:
- `DocProfileInfo` schema 加 `manual_override` field = read API contract 改 → frontend TS type 要同步
  (向後相容:optional field default null,舊 row deserialise OK)。
- override 套 preset **覆蓋現有 per-doc manual config** 嘅 preset-defined fields(per D3;非 merge)— user
  手調 knobs 會被 override preset 覆蓋,需 L3 重新 fine-tune。記 plan changelog + UI hint 提示。
- re-ingest preserve `manual_override` = edge case,需 `_run_ingest_pipeline` profile upsert 時 read 舊 merge。

**Neutral**:
- threshold persist(②)唔做 — Settings threshold 維持 static,profiler hardcode 不變(實證已最佳)。
- override 係 per-doc(ADR-0050 layer);per-KB / global profile override 不在 scope(未有需求)。

## References
- 前置 ADR:ADR-0056(文件畫像 D3 套 preset / D4 三層 UI / D6 override 優先)/ ADR-0050(per-doc config scope)
- 基建:`backend/ingestion/profile_presets.py`(W73 `preset_for`)/ `backend/kb_management/doc_config_store.py`
  (ADR-0050)/ `backend/kb_management/doc_profile_store.py`(W76)/ `documents.py:_run_ingest_pipeline`(W73 D6 守)
- read surface:`backend/api/schemas/doc_profile.py`(`DocProfileInfo`,W76)
- frontend:W78 L3 `doc-config-tab.tsx`(override select static → 本 ADR wire)
- 約束:CLAUDE.md §5.1 H1(architectural — 新 endpoint + schema)/ §5.6 H6(backend route test)
- 用戶 vision:memory `project_per_kb_tunable_config_vision`
