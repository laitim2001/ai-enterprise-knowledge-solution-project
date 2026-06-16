# W82 plan — Settings 全域 profile→preset 映射 write surface(缺口 B,ADR-0063)

**Status**: active(2026-06-16 kickoff)
**Kickoff**: 2026-06-16
**Phase 類型**: full-stack feature(backend persist + write API + frontend wire;H1-adjacent config-routing
write surface + H7 design-stage expansion edit-form;ADR-0063 Accepted)
**ADR**: ADR-0063(Settings 全域 preset-mapping write surface — B 收窄版,threshold 不做)

---

## §1 Context / 緣起

W81 缺口分析坐實**缺口 B**:Settings →「文件分類規則」tab(W77 mockup / W78 frontend)係「admin 指揮
中心」調全域 profile→preset 映射,但 backend 冇 write endpoint、前端 `PRESETS` 硬編碼 +「編輯」/
「儲存規則」`disabled`。逐文件(L3)可調已通(ADR-0058/0060),全域改唔到 →「指揮中心得一半」(DD-11)。

用戶 2026-06-16 揀補(**B 收窄版**):preset 映射可寫,**threshold 維持唔做**(W79 ADR-0058 已拍板)。
編輯 UI **復用 Settings 既有 form 模式**(視覺零發明);guard = **還原預設 + 儲存確認**。

**落點 grounding(plan kickoff,R6)**:
- `backend/ingestion/profile_presets.py` — `PROFILE_PRESETS` 硬編碼 dict + `preset_for()`(sync,讀 dict)。
  **三個 call site**:`documents.py` `_route_profile_preset`(923)/ `PUT …/profile`(604 `preset_for`)/
  backfill `_backfill_one_doc_profile`(經 `_route_profile_preset`)。
- `backend/kb_management/doc_profile_store.py` — store precedent(Protocol + InMemory + Postgres +
  `make_*` factory;`document_profiles(kb_id, doc_id, profile JSONB)`)。新 store mirror 但 **global**
  (key = profile label only)。
- `backend/api/schemas/doc_config.py` — `DocConfig`(編輯 payload type)。
- `frontend/components/settings/settings-doc-profiling.tsx` — 硬編碼 `PRESETS`(20-36)+ disabled
  「編輯」(94-101)+ threshold card「儲存規則」disabled(139-146,**本 phase 不動**)。
- 既有 Settings form primitive(`field` / `input` / `switch` / `seg` / `label` / `hint`)— 編輯 UI 復用源
  (F3 落地時 ground 具體 component;視覺零發明對齊既有 6-tab Settings form)。

---

## §2 Scope / Deliverables

### F1 — Backend persist store + 解析(`resolve_preset`)
- **F1.1** 新 `backend/kb_management/preset_override_store.py` — mirror `doc_profile_store.py`,但
  **global**(`profile_preset_overrides(profile TEXT PRIMARY KEY, config JSONB)`):Protocol(get/upsert/
  delete/list)+ `InMemoryPresetOverrideStore` + `PostgresPresetOverrideStore`(lazy psycopg)+
  `make_preset_override_store(settings)`。
- **F1.2** `profile_presets.py` 加 async `resolve_preset(profile, store)` = `store.get(profile) ??
  preset_for(profile)`(`preset_for` 仍係出廠值 reader,不動)。
- **acceptance**:mypy strict + ruff clean;unit test 蓋 InMemory store CRUD + `resolve_preset`
  fallthrough(無 override → == `preset_for`,bit-identical;有 override → 用 override)。

### F2 — Backend write API(`profile_presets.py` route)+ call-site migrate
- **F2.1** 新 `backend/api/routes/profile_presets.py`:
  - `GET /profile-presets` → `[{profile, config(effective), overridden, factory}]`(出廠 ?? override)。
  - `PUT /profile-presets/{profile}` → upsert override `DocConfig`(422 若 profile 非法 label)。
  - `DELETE /profile-presets/{profile}` → 還原出廠(刪 override;idempotent 200/204)。
- **F2.2** server.py wire store + router(mirror doc_profile_store DI)。
- **F2.3** 三 call site migrate `preset_for` → `resolve_preset`(`_route_profile_preset` /
  `PUT …/profile` / backfill)— **production-preserve**:無 override → 行為 bit-identical。
- **acceptance**:pytest 蓋 GET/PUT/DELETE + 422 + 三 call-site 用 effective preset(改 P2 override →
  下次 route P2 用新 config);mypy strict + ruff clean;**無 override 時三 call site 行為不變**(回歸 test)。

### F3 — Frontend wire(`settings-doc-profiling.tsx`)
- **F3.1** 新 `frontend/lib/api/profile-presets.ts` — TS types(mirror backend)+ `GET/PUT/DELETE` client。
- **F3.2** `settings-doc-profiling.tsx`:硬編碼 `PRESETS` → fetch `GET /profile-presets`(TanStack Query);
  解 disabled「編輯」→ 開 edit form(**復用 Settings 既有 form / field / switch / seg primitive,視覺
  零發明**)編 mockup 表格嗰幾個欄;儲存 → `PUT` + **confirm** + invalidate + toast;每 row「**還原預設**」
  → `DELETE` + confirm。
- **F3.3** **threshold card 維持唯讀 / disabled 不變**(scope 排除,明確不動)。
- **acceptance**:type-check 0 + lint 零新 warning + build ✓;編輯 UI 全用既有 primitive(H7 視覺零發明)。

### F4 — Browser 驗(playwright)
- 起 infra(per `ekp-restart`)→ Settings「文件分類規則」tab:編 P2_prose(或 test profile)一個欄 →
  儲存(confirm)→ `GET /profile-presets` 確認 persist → 「還原預設」(confirm)→ 確認回出廠。
- 驗 threshold card 仍 disabled(scope 排除)。
- **acceptance**:edit→save→persist→還原 round-trip PASS;**驗完還原全部 override 免污染**;編輯 UI
  對齊既有 Settings form 視覺。

### F5 — closeout
- backend test + type-check/lint/build + browser 全綠;plan closed + progress retro + ADR-0063 README
  index + DD-11 close(移去「已 Close」表)+ memory 更新。

---

## §3 設計原則(ADR-0063)

1. **出廠值不動 + 可逆** — `PROFILE_PRESETS` 保留做出廠值;override 係 overlay;「還原預設」= 刪 override。
2. **production-preserve** — 無 override → `resolve_preset` == `preset_for`(三 call site bit-identical)。
3. **future-only** — 改映射只影響新 ingest / override / backfill,唔回溯 re-route 現有 per-doc config。
4. **視覺零發明** — 編輯 UI 復用 Settings 既有 form primitive(用戶揀,最低 H7 風險)。
5. **store precedent** — verbatim mirror `doc_profile_store.py`(Protocol + InMemory + Postgres + factory)。

---

## §4 Non-goals(明確唔做)
- **threshold persist / 寫入**(W79 ADR-0058 已拍板不做;threshold card 維持 disabled)。
- **per-KB preset override**(本 phase global only;per-KB 留 future)。
- **回溯 re-route 現有 doc**(future-only;改映射 → 現有要 re-index,同 UI copy)。
- **改 mockup edit-form**(復用既有 form 模式;mockup 補 edit-form 設計走獨立 design sync)。
- **KB 層 section 錨定 UI**(W81 交棒,另議)。

---

## §5 Risks
- **R1 H7 edit-form design-stage expansion**(mockup 無 edit form)— 緩解:用戶 explicit 揀復用既有 Settings
  form primitive(視覺零發明)+ 記 ADR-0063;mockup 補設計走獨立 design sync。
- **R2 改壞 verified-good preset**(P1=drive-images-1 已驗 config)— 緩解:還原預設(delete→出廠,可逆)+
  儲存 confirm;出廠 dict 永久保留。
- **R3 `preset_for`→`resolve_preset` 三 call site 漏接** — 緩解:F2.3 全 migrate + production-preserve
  回歸 test(無 override bit-identical)。
- **R4 future-only 誤解為回溯** — 緩解:UI copy 已標「現有要 re-index」+ ADR 記 no retroactive re-route。
- **R5 global vs per-KB/per-doc scope 混淆** — 緩解:preset override = global(指揮中心);per-KB(ADR-0040)
  / per-doc(ADR-0050/0058)override 係另外層,不受影響;resolver 階層 per-doc > per-KB > global-preset。

---

## §6 紀律自檢(kickoff)
- **H1** ⚠️→✅ config-routing 新 write surface + persist table — ADR-0063 Accepted(用戶 AskUserQuestion
  揀 B 收窄版 + 全部設計決定);follow ADR-0023/0050/0058 persist precedent,不改 vendor / search index schema。
- **H2** ✅ 零新 dep(psycopg 已 locked)。
- **H4** ✅ 層 A admin UI,無 Tier 2。
- **H6** ✅ backend store + route 寫 test(對齊 ADR-0058/0059 test 紀律)。
- **H7** ⚠️→✅ edit-form design-stage expansion(mockup 之外)— 用戶 STOP+ask 後揀復用既有 form(視覺零發明),
  記 ADR-0063;mockup 補設計走獨立 design sync。
- **Karpathy** ✅ reuse(store mirror + 既有 form primitive)、surgical(出廠值不動 + overlay)、surface
  (H1/H7 STOP+ask + 兩個設計決定畀用戶揀)、goal(F acceptance + production-preserve 回歸 + browser round-trip)。

---

## §7 Changelog
- 2026-06-16 kickoff — plan active,F1-F5 scope locked;ADR-0063 Accepted(用戶揀 B 收窄版 / 編輯 UI 復用
  既有 form / guard 還原預設+確認);DD-11 記入 `DEFERRED_REGISTER`;落點 ground(store mirror
  `doc_profile_store.py` global + `preset_for`→`resolve_preset` 三 call site migrate + 復用既有 form primitive)。
