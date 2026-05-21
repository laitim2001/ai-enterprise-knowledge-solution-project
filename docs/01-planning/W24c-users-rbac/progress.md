---
phase: W24c-users-rbac
plan_ref: ./plan.md
checklist_ref: ./checklist.md
status: active                      # active | closed
---

# W24c-users-rbac — Progress

## Day 0 — 2026-05-21 — Kickoff cascade(F0)

### Done

- **W24c phase folder created** — `docs/01-planning/W24c-users-rbac/{plan,checklist,progress}.md` `status: active`
- **Phase scope** — ADR-0027 **Option A full RBAC**(Chris W19 F6 pick over Option B minimal recommendation):`/users` Tier 1.5 NET NEW 4-tab surface(Members / Roles / Groups / Audit log)+ per-KB ACL + 5 NEW Postgres tables + ACL middleware + Entra Graph SDK + `/kb/[id]` Access tab activation per ADR-0025。F0-F12 deliverables(largest W-series phase,~20 backend days)。
- **Wave lineage** — Wave C3 per W19 F4 §3.6 SPLIT:Wave C1 = W24 ADR-0026 Settings backend + read-mostly;Wave C2 = W24b ADR-0026 Settings depth;**Wave C3 = W24c ADR-0027 RBAC**(this phase)。
- **F0 pre-active-flip 5-step grep audit recursive**(per CLAUDE.md §10 R6)— 讀 ADR-0027 + ADR-0025 + glob `ekp-page-users.jsx` / `backend/api/auth/users*` / `backend/api/middleware/` / `frontend/app/(app)/users/`:
  - **(2) grep** — `references/design-mockups/ekp-page-users.jsx` 存在(`PageUsers` 4 tabs + `TabKbAccess` lines 390-519);`backend/api/auth/{users_store,postgres_users_store,users_repo}.py` 存在(`users` table per ADR-0023);`backend/api/middleware/` 有 `audit_log.py` + `rate_limit.py`(NEW `acl.py` 需建);`frontend/app/(app)/users/` 不存在(`/users` route NET NEW)
  - **(3) surface** — **R6 finding**:ADR-0027 §Decision Option A 寫「6 NEW Postgres tables(`roles` + `role_permissions` + `groups` + `group_members` + `audit_log` + `kb_acl`)」,但 `audit_log` table **已存在**(W24-c1 F4 ADR-0026 created + W24b F6 加 filter/pagination)→ W24c F2 實際 = **5 NEW tables**,`audit_log` 由 F7 **EXTEND**(additive `AuditAction` Literal append)非 create
  - **(4) document** — plan §7 Day 0 row + F2/F7 acceptance reflect 5-NEW-not-6
  - **(5) adjust** — plan §2 F2 = 5 tables;F7 = audit_log EXTEND;checklist F2.1 = 5 tables
- **F0 kickoff cascade committed** `(this commit)`

### Decisions

- **D0.1 — W24c = single phase 非 further-split** — ADR-0027 Option A ~20 backend days。W19 F4 §3.6 SPLIT 係指 Wave C(ADR-0026 + ADR-0027 combined ~42 days)split 做 sub-phases — ADR-0026 已拆 W24(C1)+ W24b(C2);ADR-0027 本身係 Wave C 餘下工作,ADR 無進一步要求拆。W24c = ADR-0027 Option A 一個 phase,F0-F12(12 deliverables);F-deliverable 喺 active-flip 按實際 scope sub-split per §7 R3(rolling JIT — 唔預拆 W24c/W24d)。
- **D0.2 — `audit_log` table EXTEND 非 create**(R6 finding)— ADR-0027「6 NEW tables」其中 `audit_log` 已係 W24-c1 ADR-0026 既有 table。W24c 唔重建,F7 additively extend `AuditAction` Literal 加 RBAC action types。避免 schema double-ownership conflict — risk R-W24c-4 mitigated。
- **D0.3 — C16 Users Service vs C11 expansion = F1 decision** — ADR-0027 §Decision Option A 明文 leave open「New Cn:C16 Users Service(or fold into C11)」。F0 唔強行決定;F1.3 evaluate(~20 days + 5 tables + ACL middleware + Entra Graph SDK weight)後 log plan §7 + COMPONENT_CATALOG。
- **D0.4 — Entra Graph SDK H2 pre-cleared** — CLAUDE.md §5.2 H2 加新 dependency 要 STOP and ask + ADR。ADR-0027 **已 Accepted**(W19 F6 Chris pick)且明文列「Entra Graph SDK new dependency(H2 trigger)」→ H2 4-step 已滿足(ADR documents + Chris approved)。F1 install 跟 ADR-0017 Plan B sequencing,**無需 fresh stop-and-ask**;若 install R8-fail 至 Plan B (c)則 ADR-0017 amendment occurrence #9。

### Acceptance(plan §3 + checklist F0)

- [x] F0.1 W24c folder 3 docs created status: active
- [x] F0.2 NO frontend/backend code change at kickoff
- [x] F0.3 architecture.md §3.7 amendment deferred to F1
- [x] F0.4 Pre-active-flip 5-step grep audit recursive completed + documented
- [x] F0.5 W24c kickoff cascade committed

**Day 0 F0 Verdict**:F0 complete — W24c-users-rbac phase folder + plan(§0-§7,F0-F12 deliverables)+ checklist + progress landed `status: active`。ADR-0027 Option A full RBAC scope locked。R6 audit surfaced `audit_log`-already-exists(5 NEW tables 非 6)。F1 spec amendment + Entra Graph SDK install next。

---

## Day 1 — 2026-05-21 — F1 Spec amendment + Entra Graph approach + C16 decision

### Done

- **F1 pre-active-flip 5-step grep audit recursive**(per CLAUDE.md §10 R6)— 讀 `architecture.md §3.7` + §5 region + `backend/pyproject.toml` + `COMPONENT_CATALOG.md` C08-C12 cards:
  - **(2) grep** — `architecture.md §3.7` 實為「C13 Email Verification Service」;§3.8 不存在;§5 有 3 個 `> **Amendment**` inline block(ADR-0024 line 752 / ADR-0026 line 754 / ADR-0025 §5.5 line 887);`pyproject.toml` 有 `azure-identity>=1.20` + `httpx>=0.27`(W24-c1),**無 `msgraph`**;COMPONENT_CATALOG component cards C08-C12,C13 無 full card(per-component section 收喺 C12 後)
  - **(3) surface** — 2 findings + 1 decision(plan §7 Day 1 row)
  - **(4) document** — plan §7 Day 1 changelog row landed
  - **(5) adjust** — F1.1-F1.2 amendment 落 §5;F1.4 install no-op;F1.3 = C16 NEW
- **F1.1-F1.2** `architecture.md v6 §5.0` 加 NEW `> **Amendment(/users Tier 1.5 RBAC + Access tab activation)**` inline block — RBAC「Tier 2 hook」→「Tier 1.5 minimum」+ `/users` 4-tab(Members / Roles & permissions / Groups / Audit log)+ per-KB ACL `TabKbAccess` + `/kb/[id]` Access tab activation;4 triggers(5 NEW Postgres tables + C16 + ACL middleware + managed-REST `sync-from-entra`);H4 boundary(custom roles + Power User + multi-tenancy = Tier 2);doc version held;ADR-0027 authoritative + §-pointer 更正 note
- **F1.3** C16 vs C11 decision — **pick C16 NEW Users Service**;`COMPONENT_CATALOG.md` 加 `### C16 — Users Service(Tier 1.5)` card(10-row Field/Value table,Status 🟡 W24c active,inserted 在 §4 component cards 段尾 C12 之後)
- **F1.4** Entra Graph approach — **managed-REST**(Chris AskUserQuestion 2026-05-21)— 既有 `azure-identity` token + `httpx` REST call,**no `msgraph-sdk`**;install no-op(deps W24-c1 已在)
- **F1.5** `pyproject.toml` 無 change;F1 無 backend code change(spec + component-registry only)

### Decisions

- **D1.1 — F1.1-F1.2 amendment 落 §5 非 §3.7/§3.8**(R6 finding 1)— ADR-0027 §Decision「amend `architecture.md v6 §3.7` + add §3.8 /users」嘅 §-pointer 錯:`§3.7` = C13 Email Verification Service(v6 amendment per ADR-0014),`§3.8` 不存在。`/users` 係 UI view → 屬 §5 UI Specifications。§5 已有 3 個 ADR-driven `> **Amendment**` inline block precedent(ADR-0024 / ADR-0026 §5.0 + ADR-0025 §5.5)。**Adjust**:amendment 落 §5.0 第 3 個 inline block,對齊 convention。屬 W22 D9「plan-text-contamination」anti-pattern class(ADR draft-time §-numbering 錯,plan F1 inherit)— R6 auto-adjust,established convention 明確故不需 user escalate;ADR-0027 §-pointer 更正 note 寫入 amendment block 自身 + F12 ADR-0027 Implementation Status 會 record。
- **D1.2 — Entra Graph = managed-REST 非 SDK**(R6 finding 2,Chris AskUserQuestion 2026-05-21)— ADR-0027 寫 `sync-from-entra` 用 Entra Graph SDK(明標 new dep / H2 / R8 risk)。但 `azure-identity>=1.20` + `httpx>=0.27` W24-c1 已裝;`sync-from-entra` 本質 = `GET https://graph.microsoft.com/v1.0/groups` 一個 REST call。ADR-0017 §Decision-rule 本身明寫「stdlib > managed-REST > lazy-imported optional dep」。managed-REST(`DefaultAzureCredential` 取 Graph token + `httpx` call)= 零新 dependency / 零 H2 / 零 R8 install risk。Chris pick managed-REST。**Adjust**:F1.4 Entra Graph SDK install 變 no-op;F6 `entra_graph.py` 用 managed-REST helper(lazy `azure-identity` import per ADR-0023 — unset Entra config 唔 touch)。屬 §13「spec 同 idea 衝突 → raise + get approval」— 已 raise + Chris approve。
- **D1.3 — C16 NEW Users Service 非 fold-into-C11**(R6 finding 3 / plan F1.3)— ADR-0027 §Decision Option A leave open「New Cn:C16 Users Service(or fold into C11)」。決定 = **C16 NEW**。Rationale:(a) scope weight ~20 backend days + 5 NEW Postgres tables + ACL middleware = substantial cohesive subsystem;(b) **concern separation** — C11 Identity & Access = *authentication*(MSAL / Entra SSO / token validation),C16 Users Service = *authorization*(RBAC / role enforcement / per-KB ACL / user management)— fold 入 C11 會 overload 一個 authentication component 做埋 authorization;(c) ADR-0027 §Decision Option A 首選 phrasing 就係「C16 Users Service」。C14 / C15 維持 Tier 2 reserved slot(Training Pipeline / Workflow Engine);C16 = 首個 post-C13 Tier 1.5 component。

### Acceptance(plan §3 + checklist F1)

- [x] F1.1 architecture.md §5.0 ADR-0027 inline-amendment block(R6-corrected §3.7→§5)
- [x] F1.2 /users 4-tab + Access tab activation reference 入同一 §5 block(R6-corrected §3.8→§5)
- [x] F1.3 C16 NEW Users Service decision + COMPONENT_CATALOG C16 card
- [x] F1.4 Entra Graph = managed-REST(Chris pick)— no msgraph-sdk install
- [x] F1.5 pyproject.toml 無 change;F1 無 backend code change

**Day 1 F1 Verdict**:F1 complete — `architecture.md v6 §5.0` ADR-0027 inline-amendment block(RBAC Tier 2 hook → Tier 1.5 + `/users` 4-tab + Access tab activation)+ COMPONENT_CATALOG C16 Users Service card。3 R6 findings resolved:§-pointer 更正(§3.7→§5)/ Entra Graph managed-REST(零新 dep)/ C16 NEW component。**Zero new dependency** — ADR-0027 原假設嘅 Entra Graph SDK 經 managed-REST 避免。F2 RBAC schema layer(5 NEW Postgres tables + storage)next。

---

## Day 2 — 2026-05-21 — F2 RBAC schema layer

### Done

- **F2 pre-active-flip 5-step grep audit recursive**(per CLAUDE.md §10 R6)— 讀 mockup `ekp-page-users.jsx` lines 26-60(PERMISSIONS_MATRIX)+ `storage/{audit_log_storage,audit_log_postgres,audit_log_factory}.py`(3-file storage pattern)+ `api/auth/{users_store,postgres_users_store,users_repo}.py`(`users` table + `UserRecord`)+ `kb_management/postgres_backend.py`(`ALTER TABLE … ADD COLUMN IF NOT EXISTS` additive-migration pattern):
  - **(2) grep** — audit_log 3-file split(`*_storage.py` Protocol+InMemory / `*_postgres.py` / `*_factory.py`)= canonical pattern;`audit_log` backend 用 **async** psycopg,`users_store` 用 **sync**(綁 sync `users_repo`);mockup PERMISSIONS_MATRIX = 5 areas;`users` table 由 `postgres_users_store.py` `_CREATE_TABLES` 擁有
  - **(3) surface** — 3 findings(plan §7 Day 2 row)
  - **(4) document** — plan §7 Day 2 changelog row + §2 F2 acceptance refined + checklist F2 R6 blockquote landed
  - **(5) adjust** — F2.4 「24→23」permissions;F2.2 補完 4-處同步 surface;F2 Protocol scope = roles+permissions(groups/members/acl table declared-ahead,method 留 F6/F8)
- **F2.1** `storage/rbac_postgres.py` `_CREATE_TABLES` — 5 NEW Postgres tables idempotent `CREATE TABLE IF NOT EXISTS`:`roles`(role_key PK / label / description / tier / active / sort_order / created_at)+ `role_permissions`(PK `(role_key, permission_key)` / area / label / granted / sort_order)+ `groups`(group_key PK / source / entra_object_id)+ `group_members`(PK `(group_key, user_oid)`)+ `kb_acl`(SERIAL id / kb_id / principal_type / principal_id / access_role / UNIQUE `(kb_id, principal_type, principal_id)`)
- **F2.2** `users.role` column — `postgres_users_store.py` `users` CREATE 加 `role TEXT NOT NULL DEFAULT 'user'` + 尾加 `ALTER TABLE users ADD COLUMN IF NOT EXISTS role …`(舊 DB additive backfill)+ `_USER_COLS`/`_row_to_user`/`add_user`(9→10 placeholder)/`replace_user` 同步;`users_store.py` `UserRecord` 加 `role: str = "user"` field;`users_repo.register` 無需改(`UserRecord(...)` 不傳 role → default `'user'`)
- **F2.3** RBAC storage 3-file split — `storage/rbac_storage.py`(`RbacBackend` async Protocol + `InMemoryRbacBackend` + `_PERMISSION_MATRIX` seed constant + `permission_matrix_rows()`/`default_roles()` helpers)+ `storage/rbac_postgres.py`(`PostgresRbacBackend` async psycopg connection-per-op)+ `storage/rbac_factory.py`(`make_rbac_backend` lazy-import per ADR-0023)+ `api/schemas/rbac.py`(`Role` + `RolePermission` + `RoleKey` Literal)
- **F2.4** Seed — `seed_defaults` idempotent(InMemory empty-guard / Postgres `ON CONFLICT DO NOTHING`)→ 4 roles(Admin / Editor / End User active tier 1 + Power User `active=False` tier 2 disabled affordance per H4)+ 92 `role_permissions` rows(23 perms × 4 roles,verbatim from mockup lines 26-60)
- **F2 tests** `tests/storage/test_rbac_storage.py` NEW — 12 cases(seed 4 roles + role order + Power User tier 2/inactive + idempotent + get_role + full matrix 92 + per-role 23 + grant values 對 mockup + reset + matrix constant + factory + `UserRecord.role` smoke);plan F11.1「RBAC storage」portion 提前 F2(per D2.5)
- **F2 committed** `(this commit)`

### Decisions

- **D2.1 — RBAC backend = async**(非 sync)— audit_log / admin_provider / admin_identity 三個 W24-c1 NEW storage 全 async;`UsersStore` 係 sync 因為綁 sync `users_repo`(被 sync `get_current_user` dependency 消費)。RBAC 係 NET NEW 無此約束,將被 async `/users/*` route bodies + F3 ACL middleware 消費 → async,對齊 `AuditLogBackend` shape。
- **D2.2 — `groups`/`group_members`/`kb_acl` table declared-ahead,Protocol method 留 F6/F8**(R6 finding #3)— plan F2.1 字面「5 NEW Postgres tables」→ Postgres `_ensure_schema` 一次建 5 table(idempotent,F6/F8 不需再 migrate);但 F2 的 `RbacBackend` Protocol + `InMemoryRbacBackend` 只暴露 `roles`+`role_permissions`(F5 Roles tab backing)。groups/members/acl 的 read+write method 留 F6(Groups)/ F8(per-KB ACL)active-flip 加 — per Karpathy §1.2 不寫 speculative surface + plan §2「acceptance items refine per-deliverable at active-flip」。Postgres table 5、InMemory store 2 嘅不對稱屬 deliberate:Postgres CREATE TABLE 係 declared-ahead 慣例,InMemory 按 Protocol method 增量。
- **D2.3 — `role_permissions` 存全部 92 rows**(23 perm × 4 role,含 `granted` bool)非只存 granted-only — matrix UI(F5 + mockup)需顯示 granted + not-granted 兩種 cell;`sort_order` column = `permission_matrix_rows()` 的 iteration index(0-91),供單 column `ORDER BY sort_order` 重現 mockup area→perm→role 順序。`roles` 同樣有 `sort_order`(0-3)。InMemory 用 list 保序不需 sort_order。
- **D2.4 — schema model 放 `api/schemas/rbac.py`,storage 放 `backend/storage/`** — 對齊 audit_log(`AuditLogEntry` 在 `api/schemas/`,storage import 它)+ plan §1 表「F2 → `backend/storage/` NEW rbac storage」。`UserRecord.role` 用 plain `str` 非 `RoleKey` Literal — C11 `users_store` 唔 import C16 `api.schemas.rbac`,避免 component 反向依賴;valid-value 驗證留 RBAC layer / F4 endpoint。
- **D2.5 — F2 寫 storage test(`test_rbac_storage.py` 12 cases),plan F11.1「RBAC storage」portion 提前 F2** — Karpathy §1.4 goal-driven:F2 schema layer 的 verifiable success criteria = seed/list/reset test pass,唔可以等到 F11 先驗。F11 專注 ACL middleware + `/users/*` endpoints test。屬 R3 plan-deviation logged(plan §7 Day 2)。

### Acceptance(plan §3 + checklist F2)

- [x] F2.1 5 NEW Postgres tables idempotent `CREATE TABLE IF NOT EXISTS`(`rbac_postgres.py` `_CREATE_TABLES`)
- [x] F2.2 `users.role` column ADD + `ALTER TABLE … ADD COLUMN IF NOT EXISTS` + `UserRecord.role` field + `PostgresUsersStore` 4-處同步
- [x] F2.3 `RbacBackend` async Protocol + `InMemoryRbacBackend` + `PostgresRbacBackend` + `make_rbac_backend` factory(lazy-import per ADR-0023)
- [x] F2.4 Seed 3 active roles + Power User Tier 2 `active=False` + PERMISSIONS_MATRIX 5 areas × 23 permissions(R6-corrected from 24)→ 4 roles + 92 role_permission rows

### Verify

- **backend pytest 828 passed**(W24b baseline 816 → +12 F2 storage tests)+ 11 skipped + 0 failed — regression 0
- **mypy `--strict`** — `rbac_storage.py` / `rbac_factory.py` / `api/schemas/rbac.py` / `users_store.py` 0 error;`rbac_postgres.py` 唯一 error = `psycopg` import-not-found(CO17 R8 — `pip install psycopg[binary]` 一直 R8-blocked,與既有 `audit_log_postgres.py` / `postgres_users_store.py` 同類豁免,非 F2 引入)
- **H6 note** — RBAC storage 唔在 §5.6 H6 強制 test 清單(ingestion / retrieval / pipeline / eval),但 F2 仍同步寫 12 test(W24b F6 audit_log storage test precedent + Karpathy §1.4)

**Day 2 F2 Verdict**:F2 complete — RBAC schema layer landed(4 NEW files:`api/schemas/rbac.py` + `storage/rbac_storage.py` + `storage/rbac_postgres.py` + `storage/rbac_factory.py`;2 EDIT:`users_store.py` + `postgres_users_store.py`;1 NEW test:`tests/storage/test_rbac_storage.py`)。5 NEW Postgres tables idempotent + `users.role` column additive + `RbacBackend` async Protocol/InMemory/Postgres/factory + seed 4 roles + 92 role_permissions。3 R6 findings resolved(24→23 permissions / `users.role` 4-處同步補完 / F2 Protocol scope = roles+permissions)。backend pytest 828 + 0 fail。F3 ACL middleware + auth-time role claim next。

## Day 3 — 2026-05-21 — F3 ACL middleware + auth-time role claim

### Done

- **F3 pre-active-flip 5-step grep audit recursive**(per CLAUDE.md §10 R6)— 讀 `api/auth/{dependency,models,mock_msal,msal_provider}.py` + `api/middleware/rate_limit.py` + `api/schemas/admin_identity.py` + `storage/admin_identity_storage.py` + `api/routes/admin/identity.py` + frontend `admin.ts`/`identity.ts`/`settings-identity.tsx`:
  - **(3) surface** — 5 findings(plan §7 Day 3 row):#1 `AuthenticatedUser` 無 `role` field / #2 `@requires_*`「decorator」→ FastAPI `Depends()` / #3 `@requires_kb_acl` backing 在 F8 / #4 「every endpoint」F3 時點不可能 / #5 role key vocabulary 衝突
  - **(4) document** — plan §7 Day 3 row + §2 F3 acceptance refined + checklist F3 R6 blockquote
  - **(5) adjust** — F3.2 = `AuthenticatedUser.role` + 三路徑;F3.1 = `require_role` factory(`require_kb_acl` → F8);F3.4 = mechanism + 403 test(per-endpoint → F4-F10);NEW F3.0 vocabulary 統一
- **F3.0** role key vocabulary 統一(9 files)— backend:`admin_identity.py` 刪 `EkpRoleKey` long-form literal → import `rbac.RoleKey`;`admin_identity_storage.py` seed 4 values long→short;`identity.py` Tier 2 guard `"power_user"`→`"power"`;`test_admin_identity.py` 5 處。frontend:`admin.ts` `EkpRoleKey` union short + NEW `EKP_ROLE_LABELS` const;`identity.ts` `ekpRoleKeySchema` z.enum short;`settings-identity.tsx` role 顯示 `.replace('_',' ')` → `EKP_ROLE_LABELS[m.ekp_role]`(修 H7 drift)+ badge condition;`settings-6tab.test`/`settings-identity-form.test` mock 改 `importOriginal` partial-mock
- **F3.1** NEW `backend/api/middleware/acl.py` — `require_role(*allowed)` FastAPI dependency factory:chains `Depends(get_current_user)`,403 when role ∉ allowed,returns `AuthenticatedUser` on success。`require_kb_acl` 🚧 F8
- **F3.2** `AuthenticatedUser` 加 `role: str = "user"` field;三路徑 server-side resolve — `resolve_session`→`UserRecord.role`(F2 column)/ `authenticate_mock`→`Settings.auth_mock_role` / `authenticate_msal`→`_role_from_claims`
- **F3.3** `Settings.auth_mock_role` NEW field default `"admin"`;`msal_provider._role_from_claims` — Entra app-role claim(`roles`)→ Tier-1-grantable `{admin,editor,user}`,`power`/unknown → `"user"` fallback(least privilege)
- **F3 tests** NEW `tests/api/test_acl_middleware.py` 11 cases(`require_role` admit/reject/multi + 403/401 contract in real request flow + `AuthenticatedUser.role` default + `authenticate_mock` role + `_role_from_claims` × 3)
- **F3 committed** 2 commits — C1 F3.0 vocabulary `(commit)` + C2 F3.1-F3.5 ACL `(commit)`

### Decisions

- **D3.1 — role key vocabulary 統一 = short form**(R6 #5;Chris AskUserQuestion 2026-05-21)— W24-c1 `admin_identity.EkpRoleKey` long-form(`workspace_admin`/`knowledge_editor`/`end_user`/`power_user`,comment 自標「ADR-0027 **Option B** fallback」= 寫於 full RBAC 之前)vs F2 RBAC-core + mockup `ekp-page-users.jsx` short-form。Chris pick「統一 short form(改 admin_identity)」— mockup 係 H7 canonical 用 short,RBAC core(C16,W24c 主體)已 short,Option B-era long-form 係過時 artifact。`admin_identity` 改用 `rbac.RoleKey`(single source of truth)。兩套並存(boundary mapper)被 reject — permanent tech debt。
- **D3.2 — `acl.py` = FastAPI dependency factory 非 Python decorator**(R6 #2)— plan/checklist 字面「`@requires_role` decorator」係 plan-text contamination;FastAPI 無 endpoint-decorator-for-auth 慣例,既有 `get_current_user` 全用 `Annotated[..., Depends(...)]`。`require_role(*roles)` 返回一個 dependency callable,per-endpoint `Depends(require_role("admin"))` 或 router-level `dependencies=[...]`。
- **D3.3 — `require_kb_acl` defer F8**(R6 #3)— `@requires_kb_acl` 要 consult `kb_acl` table,但 `kb_acl` 的 storage method F2 D2.2 已 defer F8。F3 寫一個 backing 未存在的 guard = stub(Karpathy §1.2)。F3 只交付 `require_role`;`require_kb_acl` 連 `kb_acl` storage method F8 一齊做。
- **D3.4 — real-MSAL role 從 Entra app-role claim(`roles`)抽,非 group-GUID claim(`groups`)** — ADR-0027 §Consequences 寫「extracts role from group membership」係 conceptual。`groups` claim 帶 raw group GUID,要 `{guid:role}` config map + `authenticate_msal` consult identity backend(signature 只有 `(credentials, settings)` → ripple)。`roles` app-role claim 直接帶語義 role string(Entra app registration 把 security group / user assign 到 app role)→ Tier 1 簡單 + 零 ripple + Entra app role 係標準做法。`admin_identity.RoleMappingConfig`(group→role config)維持為 admin-facing **config-of-record**。real-MSAL runtime verify defer(mock-auth default,Q11 operational early June — per plan §3 PARTIAL PASS allowance)。
- **D3.5 — `auth_mock_role` NEW settings field** — mock identity 的 role 屬性,跟既有 `auth_mock_oid`/`tid`/`preferred_username` 同組;default `"admin"` 讓 dev 走過每個 guard,test 可 override drive 403 path。非 speculative config(mock identity attribute）。
- **D3.6 — `settings-identity.tsx` role 顯示修 H7 drift** — F3.0 前 `settings-identity.tsx:642` 用 `{m.ekp_role.replace('_',' ')}` 顯示「workspace admin」(lowercase);mockup `ekp-page-settings-tabs.jsx` line 664 係「Workspace Admin」(title-case)— **既有 H7 drift**。F3.0 改 short key 同時改用 `EKP_ROLE_LABELS` map → 顯示「Workspace Admin」對齊 mockup。屬 H7「修正 visual drift bug(把 implementation 更貼 mockup)」reverse direction → 不 trigger H7 STOP。
- **D3.7 — F3 拆 2 commits** — C1 F3.0 vocabulary 統一 / C2 F3.1-F3.5 ACL middleware;兩個 cohesive 主題,per CLAUDE.md §4.3 One feature per commit。

### Acceptance(plan §3 + checklist F3)

- [x] F3.0 role key vocabulary 統一(9 files long→short;`settings-identity.tsx` H7 drift 修正)
- [x] F3.1 `acl.py` NEW `require_role(*roles)` FastAPI dependency factory(`require_kb_acl` 🚧 F8)
- [x] F3.2 `AuthenticatedUser.role` field + 三路徑 server-side resolve
- [x] F3.3 mock `auth_mock_role` default `admin` + real-MSAL `_role_from_claims` app-role claim
- [x] F3.4 `require_role` 403 contract test-verified(per-endpoint apply 🚧 F4-F10 inline)

### Verify

- **backend pytest 839 passed**(F2 baseline 828 → +11 `test_acl_middleware.py`)+ 11 skipped + 0 failed — regression 0
- **mypy `--strict`** — `acl.py` / `admin_identity.py` / `models.py` / `mock_msal.py` / `users_repo.py` / `settings.py` 0 error;`msal_provider.py` reported errors(jose import-untyped + 既有 no-any-return)全部 pre-existing,`_role_from_claims` clean
- **ruff** — F3-introduced files all clean;`storage/admin_identity_storage.py:39` UP017(`timezone.utc` vs `datetime.UTC` — repo-wide pattern)+ `tests/api/test_admin_identity.py:8` I001(import order)= **pre-existing W24-c1 lint**,F3.0 只改 role values 未碰嗰 2 行,per Karpathy §1.3 surgical 未順手修
- **frontend** — `tsc --noEmit` exit 0;`next lint` no warnings/errors;Vitest 29 passed(`settings-6tab` + `settings-identity-form` + `admin-schemas`,`importOriginal` partial-mock fix);`[oklch`=0 preserved

**Day 3 F3 Verdict**:F3 complete — ACL middleware `require_role` + auth-time role claim landed。NEW `api/middleware/acl.py`(`require_role` dependency factory)+ `AuthenticatedUser.role` 三路徑 populate + `test_acl_middleware.py` 11 cases。F3.0 role key vocabulary 統一(R6 #5 — Chris pick short form;9 files long→short;`settings-identity.tsx` H7 drift 修正)。5 R6 findings resolved。backend pytest 839 + 0 fail。F4 `/users` Members tab backend next。

<!-- Day 4+ F4 entries land at F4 active flip per CLAUDE.md §10 R2 -->
