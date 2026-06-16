# W82 progress — Settings 全域 preset-mapping write surface(缺口 B,ADR-0063)

## Day 1 — 2026-06-16(kickoff)

**Context**:W81 closeout(缺口 A L3 image-anchor knobs)後,session-start gap 分析坐實**缺口 B** —
Settings「文件分類規則」tab 係「admin 指揮中心」調全域 profile→preset 映射,但 backend 冇 write
endpoint、前端 `PRESETS` 硬編碼 +「編輯」/「儲存規則」disabled。逐文件(L3,ADR-0058/0060)可調已通,
全域改唔到 →「指揮中心得一半」。

**狀況確認(code-grounded,grep 坐實非憑記憶)**:
- backend 只有 per-doc `PUT …/profile`(ADR-0058)+ `POST …/profiles/backfill`(ADR-0059),**冇**
  global preset / threshold write endpoint。
- `settings-doc-profiling.tsx` `PRESETS` 硬編碼鏡像 +「編輯」/「儲存規則」`disabled`(註解明標需
  backend write API)。

**用戶決定(2026-06-16,兩輪 AskUserQuestion)**:
1. W82 方向 = **B 收窄版**(preset 映射可寫;**threshold 維持不做** — 同 W79 ADR-0058 拍板,避免矛盾)。
2. 編輯互動 UI = **復用 Settings 既有 form 模式**(視覺零發明,W81 方案 A 同款;mockup 補 edit-form 設計
   走獨立 design sync)。
3. Guard = **還原預設 + 儲存確認**(每 row「還原預設」delete override→回出廠可逆 + 儲存前 confirm)。
4. DD-11 = **記入** `DEFERRED_REGISTER`(已記,免幻影工作項;close 條件 = 本 phase backend write API 落地)。

**Surface 過嘅 stale / 矛盾(揀之前已講清)**:
- 選項 A(D8 PDF/scan robustness)主體已 2026-06-15 探索後 defer(DD-9):robustness OK、真痛點 OCR 慢
  (Tier 2)+ 零 production scan KB → 唔行 A。
- 選項 B 原 prompt「threshold 寫入」同 W79「threshold 不做」矛盾 → 收窄為 preset 映射 only。

**ADR-0063 Accepted**(本 session):新全域 preset-mapping write surface — 持久層 mirror
`doc_profile_store.py`(global key)+ `resolve_preset` overlay(出廠值 `PROFILE_PRESETS` 不動)+
GET/PUT/DELETE API + 三 call site migrate + frontend 復用既有 form + guard。

**落點 ground(R6)**:
- 三 call site = `documents.py` `_route_profile_preset`(923)/ `PUT …/profile`(604 `preset_for`)/
  backfill(經 `_route_profile_preset`)→ 全 migrate `resolve_preset`。
- store mirror `doc_profile_store.py`(Protocol+InMemory+Postgres+factory),table 改 global
  `profile_preset_overrides(profile PRIMARY KEY, config JSONB)`。
- frontend `settings-doc-profiling.tsx`(硬編碼 `PRESETS` 20-36 / disabled 編輯 94-101)+ threshold
  card(139-146)**本 phase 不動**。

**紀律自檢**:H1 ⚠️→✅(ADR-0063 Accepted,follow persist precedent)/ H2 ✅ 零 dep / H4 ✅ 層 A admin /
H6 ✅ store+route 寫 test / H7 ⚠️→✅ edit-form design-stage expansion 用戶揀復用既有 form(視覺零發明)/
Karpathy ✅(store mirror reuse + 出廠值不動 overlay + 兩設計決定畀用戶揀 + production-preserve goal)。

**Plan 落地**:W82 folder + plan.md(active)+ checklist.md(F1-F5)+ progress.md + ADR-0063 + DD-11。

**F1 implement(Day 1)** ✅:
- **`backend/kb_management/preset_override_store.py`**(新)— verbatim mirror `doc_profile_store.py`,但
  **global key**(profile label,無 kb_id):`PresetOverrideStore` Protocol + `InMemoryPresetOverrideStore`
  + `PostgresPresetOverrideStore`(lazy psycopg + table `profile_preset_overrides(profile PRIMARY KEY,
  config JSONB)`)+ `make_preset_override_store`。value = `DocConfig`。
- **`backend/ingestion/profile_presets.py`** — 加 async `resolve_preset(profile, store)` =
  `override ?? preset_for`(出廠值 `preset_for` 不動,加 docstring 標明 factory vs effective);
  TYPE_CHECKING import `PresetOverrideStore`(零 runtime dep)。
- **`backend/tests/test_preset_override_store.py`**(新)— 14 test:InMemory CRUD(get/upsert/replace/
  delete-idempotent/list_all/copy-isolation)+ factory selection(無 DATABASE_URL→InMemory / 有→Postgres
  唔連線)+ `resolve_preset` overlay(無 override == `preset_for` bit-identical / None profile 維持 None /
  override 勝出 / override 可 route None-profile / 回傳 fresh copy 唔污染 store + factory)。
- **gate 全綠**:pytest **14 passed** / ruff **All checks passed** / mypy `--strict`
  **Success: no issues found in 2 source files**(25 個 mypy error 經核實全喺 `ingestion/parsers/*`
  docling 既有 stub debt,傳遞 import 拉入,我兩個檔零 error)。
- **production-preserve 坐實**:`test_resolve_no_override_is_bit_identical_to_factory` — 空 store 下
  `resolve_preset == preset_for` 對每個 profile;F1 純後端、零 API 接線、零 call-site 改動 →
  production 行為零影響(call-site migrate 留 F2)。

**Retro(F1)**:
- **store mirror = 零發明**:`doc_profile_store.py` 結構直接套(Protocol+InMemory+Postgres+factory),
  只改 key 由 `(kb_id, doc_id)` → global `profile`、value 由 `DocProfileInfo` → `DocConfig`。
- **出廠值不動 overlay 模式**:`preset_for` 保留做 factory reader(加 docstring 區分),`resolve_preset`
  做 effective overlay → 「還原預設」= 刪 override 自然回出廠,無需特殊邏輯。
- **mypy 全域跑會被 parser docling debt 淹**:本 phase 改檔用 `--follow-imports=silent -m <module>`
  隔離驗證(避免 file-path dup-name + 既有 parser 25 error 噪音);記低供 F2 沿用。

**F2 implement(Day 1)** ✅:
- **`backend/api/routes/profile_presets.py`**(新)— global scope route(無 KB verify):`GET /profile-presets`
  (effective factory view,`overrides ?? factory`,只列 7 個 routable profile + mockup order)+ `PUT
  /profile-presets/{profile}`(upsert override,422 非 routable label,reuse `preset_for is None` guard)+
  `DELETE /profile-presets/{profile}`(還原預設,idempotent 204)+ `PresetMappingItem`(profile/config/
  overridden)+ `_store` 503 guard(mirror `doc_config.py`)。
- **`backend/ingestion/profile_presets.py`** — `resolve_preset` 簽名改 `store: PresetOverrideStore | None`
  (None → factory,統一 graceful-degrade,call-site 零重複 guard;F1 簽名小修)。
- **`backend/api/routes/documents.py`** — 三 call site migrate `preset_for`→`resolve_preset`:`_IngestionDeps`
  加 `preset_override_store` 欄 + `_ingestion_deps_or_503` 讀 + `_preset_override_store(request)` helper +
  `_route_profile_preset` 加參數用 `resolve_preset`(ingest call site 傳 `deps.preset_override_store`)+
  `override_doc_profile`(ADR-0058 人手覆寫)用 effective preset + backfill `_backfill_one_doc_profile` 加參數
  + `run_kb_profile_backfill` 讀 store 傳入。移除 orphan import `preset_for`(Karpathy §1.3)。
- **`backend/api/server.py`** — `import make_preset_override_store` + `app.state.preset_override_store =
  make_preset_override_store(settings)`(mirror doc_profile_store lifespan)+ route module import + `include_router`。
- **`backend/tests/test_profile_presets_routes.py`**(新)+ `test_preset_override_store.py` 加 `resolve_preset(None)`
  fallback test。
- **gate 全綠**:pytest **50 passed**(新 route GET/PUT/DELETE/422×4/503 + `_route_profile_preset` 認 override
  整合 + production-preserve;regression routing/override/backfill 全綠)/ ruff non-server **All checks passed**
  (server.py E402=40 baseline 零新增,`git stash` 證)/ mypy `--strict` 4 module clean(唯一 error =
  `_engine_or_503` no-any-return `git stash` 證 baseline pre-existing,非本 phase)。
- **production-preserve 坐實**:`test_route_preset_production_preserve_without_override` —— 無 override 時
  `_route_profile_preset` 寫出 factory preset(== `preset_for`);production startup 空 store → 三條路
  bit-identical,直到 admin 編輯映射先生效。

**Retro(F2)**:
- **`resolve_preset(store | None)` 統一 graceful-degrade**:store 可 None(unwired)→ fallback factory,
  令三 call site migrate 零重複 None-guard(對齊 codebase 其他 store 全 `| None` 慣例);F1 簽名小修值得。
- **422 guard 復用既有 pattern**:`preset_for(cast(DocProfile, label)) is None` → 422,同 `override_doc_profile`
  (ADR-0058 line 604)一致,too_small/unknown/garbage 全攔。
- **mockup order 自然由 `PROFILE_PRESETS` dict insertion order 得**:`_routable_profiles` filter 非-None →
  7 個 P1-P5 順序 = mockup table 順序,零額外排序。
- **migrate 後驗 pre-existing 噪音必須 `git stash` 科學辨**:server.py E402(40 baseline)+ documents.py
  `_engine_or_503` no-any-return 都係 stash 證 baseline 已存在,非本 phase 引入(沿 W80 教訓)。

**Next**:F3 frontend wire(`settings-doc-profiling.tsx` fetch + 解 disabled 編輯復用既有 form + guard;
threshold card 不動)(等用戶 trigger)。

**Commits**:
- (kickoff)`996039d` docs(planning): W82 kickoff + ADR-0063 + DD-11 — Settings preset-mapping write surface
- (F1)`ccc628b` feat(ingestion): W82 F1 global preset-override store + resolve_preset (ADR-0063)
- (F2)feat(api): W82 F2 profile-presets write API + 三 call-site migrate resolve_preset (ADR-0063)
