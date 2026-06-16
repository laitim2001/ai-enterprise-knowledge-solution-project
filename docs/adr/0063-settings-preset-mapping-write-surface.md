# ADR-0063: Settings 全域 profile→preset 映射 write surface

**Date**: 2026-06-16
**Status**: Accepted
**Approver**: 用戶(2026-06-16 AskUserQuestion 揀 B 收窄版 + 編輯 UI 復用既有 form + guard 還原預設+確認）

## Context

ADR-0056 層 A(文件畫像驅動自適應 recall)三層 UI 可調願景中,Settings →「文件分類規則」tab
(W77 mockup / W78 frontend)係「admin 指揮中心」—— 調**全域** profile→preset 映射。但 W78 落地時
backend 冇 write endpoint,前端 `settings-doc-profiling.tsx` 嘅 `PRESETS` 係**硬編碼鏡像** +
「編輯」/「儲存規則」button `disabled`(註解明標「write surface 屬段③後續,需 backend write API」)。

W81 缺口分析坐實:逐文件(L3,ADR-0058 profile override + ADR-0060 image-anchor knobs)可調已通,
但**全域自動規則改唔到** → 「指揮中心得一半」(登記為 `DEFERRED_REGISTER` DD-11)。用戶 2026-06-16 揀
補呢一半(**B 收窄版**),兌現「最大限度自行調試」vision(2026-06-15 重申)。

現狀:`PROFILE_PRESETS`(`backend/ingestion/profile_presets.py`)係 module-level 硬編碼 dict,
`preset_for()` 讀佢。**三個 call site** 受映射改動影響:ingest 自動路由(`documents.py
_route_profile_preset`)、人手 override(`PUT /kb/{kb_id}/docs/{doc_id}/profile`)、backfill。

## Decision

新增**全域** profile→preset 映射 write surface:

1. **持久層** — 新 `backend/kb_management/preset_override_store.py`,verbatim mirror
   `doc_profile_store.py`(ADR-0050/0058 precedent):Postgres table
   `profile_preset_overrides(profile TEXT PRIMARY KEY, config JSONB)` + in-memory fallback
   (`DATABASE_URL` unset)。**Global**(只 key by profile label,無 `kb_id`)—— 對比 per-doc
   override(per-KB+doc)。

2. **解析語意** — 新 async `resolve_preset(profile, store)` = `store.get(profile) ?? preset_for(profile)`。
   硬編碼 `PROFILE_PRESETS` 保留做**出廠值**;「還原預設」= `store.delete(profile)`(回出廠,可逆)。
   三個 call site migrate 至 `resolve_preset`(`preset_for` 仍係出廠值 reader)。

3. **生效範圍** — **future-only**:改映射只影響新 ingest / 新人手 override / 新 backfill,**唔**回溯
   re-route 現有 per-doc config(對齊 UI copy「現有要 re-index」+ ADR-0058「override → re-route 唔做」)。

4. **API**(global scope,新 `backend/api/routes/profile_presets.py`):
   - `GET /profile-presets` → effective 映射(出廠 ?? override)+ `overridden` flag per profile。
   - `PUT /profile-presets/{profile}` → upsert override `DocConfig`(422 若 profile 非法)。
   - `DELETE /profile-presets/{profile}` → 還原出廠(刪 override;idempotent)。

5. **編輯範圍** — mockup 表格嗰幾個 `DocConfig` 欄:圖上限(`max_images_per_answer`)/ 鄰近圖
   (`enable_citation_neighbour_images` + `citation_neighbour_max_aux_images`)/ inline marker
   (`enable_inline_image_markers`)/ section 錨定(`enable_section_anchored_aux_images` +
   `section_anchor_max_per_anchor`)/ 詳細度(`answer_detail`)。

6. **Frontend** — `settings-doc-profiling.tsx` 由硬編碼 `PRESETS` 改 fetch `GET /profile-presets`
   (TanStack Query);解 disabled「編輯」—— **復用 Settings 既有 form / field / switch / seg
   primitive(視覺零發明**,用戶揀,W81 方案 A 同款)+ 儲存 confirm + 每 row「還原預設」。
   **threshold card 維持唯讀 / disabled 不變**(scope 排除)。

7. **Guard**(用戶揀)— 每 row「還原預設」(delete override → 回出廠,可逆)+ 儲存前 confirm。
   出廠 dict 永久保留,改壞可一鍵還原。

## Alternatives Considered

- **threshold 一齊可寫** — REJECT:W79 ADR-0058 已拍板 threshold persist 不做(五輪實證最佳,改門檻
  risk>reward)。本 phase 只做 preset 映射,threshold card 維持唯讀。
- **per-KB preset override** — REJECT(本 phase):無需求;global「指揮中心」先行,per-KB 留 future。
- **回溯 re-route 現有 doc** — REJECT:重 + 繞過 production-preserve;對齊 ADR-0058「override → re-route
  唔做」;改映射 → 現有要 re-index(同 UI copy)。
- **先設計 edit-form mockup(H7 正路)** — 用戶 REJECT,揀復用既有 form 模式(視覺零發明,最低 H7 風險);
  mockup 補 edit-form 設計走獨立 design sync(將來)。
- **只做 backend API 先** — REJECT:admin 指揮中心要 end-to-end 可用先有價值(同 ADR-0058 全 stack)。

## Consequences

- **Positive**:admin 指揮中心 end-to-end 可用(逐文件 + 全域兩半齊);DD-11 close;vision 兌現;
  出廠值可逆 guard。
- **Negative**:`preset_for`→`resolve_preset` 三 call site migrate(refactor 風險 → test + production-
  preserve 驗 bit-identical 緩解);全域可編輯有改壞風險(還原預設 + confirm 緩解)。
- **Neutral**:future-only(改映射唔回溯);threshold 維持唯讀;edit-form 屬 mockup 之外 design-stage
  expansion(復用既有 component 視覺零發明,記本 ADR;mockup 補設計走獨立 design sync)。

## References
- ADR-0056(層 A 文件畫像)/ ADR-0050(per-doc config-scope)/ ADR-0058(profile override write)/
  ADR-0059(backfill)/ ADR-0060(L3 image-anchor knobs,W81 缺口 A)
- W81 `progress.md` 缺口 B / `DEFERRED_REGISTER` DD-11
- `backend/ingestion/profile_presets.py` / `backend/kb_management/doc_profile_store.py` /
  `frontend/components/settings/settings-doc-profiling.tsx`
