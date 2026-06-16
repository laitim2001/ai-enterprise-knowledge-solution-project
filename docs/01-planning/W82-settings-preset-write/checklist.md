# W82 checklist — Settings 全域 preset-mapping write surface(ADR-0063)

> Atomic items per deliverable。每日 tick。Source of truth = `plan.md`。

## F1 — Backend persist store + 解析
- [ ] F1.1 新 `backend/kb_management/preset_override_store.py`(mirror `doc_profile_store.py`,global key)
  - [ ] `PresetOverrideStore` Protocol(get / upsert / delete / list_all)
  - [ ] `InMemoryPresetOverrideStore`
  - [ ] `PostgresPresetOverrideStore`(lazy psycopg + `CREATE TABLE IF NOT EXISTS profile_preset_overrides`)
  - [ ] `make_preset_override_store(settings)`(Postgres if `database_url` else in-memory)
- [ ] F1.2 `profile_presets.py` 加 async `resolve_preset(profile, store)`(`store.get ?? preset_for`)
- [ ] F1.3 unit test:InMemory CRUD + `resolve_preset` fallthrough(無 override == `preset_for` bit-identical / 有 override 用 override)
- [ ] F1 gate:mypy strict + ruff clean

## F2 — Backend write API + call-site migrate
- [ ] F2.1 新 `backend/api/routes/profile_presets.py`(GET / PUT / DELETE)
- [ ] F2.2 `server.py` wire store + router(mirror doc_profile_store DI)
- [ ] F2.3 三 call site `preset_for` → `resolve_preset`(`_route_profile_preset` / `PUT …/profile` / backfill)
- [ ] F2.4 pytest:GET effective + PUT upsert + DELETE 還原 + 422 非法 profile + 三 call-site 用 effective preset
- [ ] F2.5 回歸:無 override 時三 call site 行為 bit-identical(production-preserve)
- [ ] F2 gate:mypy strict + ruff clean + 全 backend test 綠

## F3 — Frontend wire
- [ ] F3.1 新 `frontend/lib/api/profile-presets.ts`(TS types + GET/PUT/DELETE client)
- [ ] F3.2 `settings-doc-profiling.tsx` 硬編碼 `PRESETS` → fetch `GET /profile-presets`(TanStack Query)
- [ ] F3.3 解 disabled「編輯」→ edit form(復用既有 Settings form primitive,視覺零發明)
- [ ] F3.4 儲存 → `PUT` + confirm + invalidate + toast;每 row「還原預設」→ `DELETE` + confirm
- [ ] F3.5 threshold card 維持唯讀 / disabled 不變(scope 排除,明確不動)
- [ ] F3 gate:type-check 0 + lint 零新 warning + build ✓

## F4 — Browser 驗(playwright)
- [ ] F4.1 起 infra(`ekp-restart`)+ pre-flight health check
- [ ] F4.2 Settings「文件分類規則」tab:編一個 profile 一個欄 → 儲存(confirm)→ `GET` 確認 persist
- [ ] F4.3 「還原預設」(confirm)→ 確認回出廠
- [ ] F4.4 threshold card 仍 disabled(scope 排除)
- [ ] F4.5 驗完還原全部 override 免污染
- [ ] F4 gate:edit→save→persist→還原 round-trip PASS

## F5 — closeout
- [ ] F5.1 全 gate 綠(backend test + type-check/lint/build + browser)
- [ ] F5.2 plan closed + progress retro
- [ ] F5.3 ADR-0063 README index 加 row + next NNNN → 0064
- [ ] F5.4 DD-11 由「結構性」表移去「已 Close」表 + 記證據
- [ ] F5.5 memory `project_per_kb_tunable_config_vision` 更新(W82 段)
