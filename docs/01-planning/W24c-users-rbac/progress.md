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

## Day 4 — 2026-05-21 — F4 /users Members tab backend

### Done

- **F4 pre-active-flip 5-step grep audit recursive**(per CLAUDE.md §10 R6)— 讀 mockup `ekp-page-users.jsx` Members tab(`MOCK_USERS` + filter seg + 10-col table)+ `conversations.py`(CRUD route pattern)+ `users_store`/`users_repo` + `server.py` route registration → 6 findings(plan §7 Day 4 row)
- **F4 schema layer** — `UserRecord` 加 `status: str = "active"` field;`postgres_users_store.py` `users` table 加 `status` column + `ALTER TABLE … ADD COLUMN IF NOT EXISTS` + `_USER_COLS`/`_row_to_user`/`add_user`/`replace_user` 同步;`UsersStore` Protocol 加 `list_users()` + InMemory(newest-first)+ Postgres(`ORDER BY created_at DESC`)impl;`AuditAction` Literal +3(`user.invited`/`user.suspended`/`role.changed`)
- **F4 NEW `api/schemas/user.py`** — `UserSummary`(Members-tab row,backend subset)+ `UserListResponse{users,total}` + `InviteRequest` + `RoleChangeRequest`;`UserDisplayStatus` 4-態 Literal(`pending` 為 derived)
- **F4 `users_repo` 4 NEW management functions** — `list_users` / `invite_user`(建 `status="invited"` record,unusable random password)/ `set_user_status` / `set_user_role`(C16 concern,共用 module-level `_store` singleton)
- **F4 NEW `api/routes/users.py`** — 4 endpoints router-level `require_role("admin")`:`GET /users`(`UserListResponse`,`_to_summary` derive display status)+ `POST /users/invite`(`_reject_tier2_role` + 409 dup)+ `POST /users/{oid}/suspend` + `PATCH /users/{oid}/role`;`_audit` helper 寫 `app.state.audit_log_backend`(actor = `current_user.preferred_username`)
- **F4 route register** — `server.py` import `users` + `app.include_router(users.router)`(無 `_auth` — router 自帶 `require_role` 已 chain `get_current_user`);endpoint count 45 → **49**
- **F4 tests** NEW `tests/api/test_users_route.py` 15 cases(GET list + admin gate 403 + 401 + pending derive;invite create/power-reject/dup-409;suspend + 404;role-change + power-reject + 404;mutations-require-admin;invite/suspend audit writes)
- **F4 committed** `(this commit)`

### Decisions

- **D4.1 — `GET /users` response = backend subset**(R6 #1)— mockup `MOCK_USERS` 有 `queries_7d`/`kbs_owned`/`last_login`/`source`/`group`,但 Tier 1 backend 完全無 track(per-user query volume 需 query log Q6 open;KB ownership 需 ownership model;auth source / Entra group 需 F6 group wiring)。`GET /users` 只返回 `UserRecord` 實際有的(`oid`/`email`/`display_name`/`role`/`status`/`created_at`)— per CLAUDE.md §13 data-contract gap backend wins on field shape。mockup rich columns 喺 F9 frontend 渲染時面對(顯示「—」或省略)。
- **D4.2 — `UserRecord` 加 `status` field,不取代 `verified`**(R6 #2)— mockup status 4 態(active/pending/invited/suspended)。`UserRecord` 加 `status: str`(3 值 active/invited/suspended);**`pending` = `not verified` derive**,不存。理由:`verified` deeply 用喺 auth flow(`register`/`mark_verified`/`regenerate_verification_code`/login gate),改 `verified`→`status` 會 ripple `users_repo` + `auth.py`。`status`(account lifecycle)與 `verified`(email verification)正交並存。
- **D4.3 — invite = 建 invited record;email + accept flow defer**(R6 #3)— `POST /users/invite` 建 `UserRecord(status="invited", password_hash=hash_password(random))` — invited user 不能 login until accept。**invite email send + accept flow(set password / verify,或 self-register-detects-invited upgrade)🚧 defer** — 完整 flow 牽涉 C13 email template + `register` flow 改動,係 separate concern。invited record 已滿足 Members tab list 顯示 pending invite(mockup stat「Pending invites」)。
- **D4.4 — user-management functions 放 `users_repo`(C11 module),route `users.py` 標 C16** — `users_repo` 係 `users` table 嘅 repository,list/invite/suspend/role-change 係佢合理操作範圍;且 F4 route **必須** 共用 `users_repo._store` module-level singleton(否則 F4 `GET /users` 同 self-register/login 係唔同 store instance,睇唔到對方嘅 user)。F4 functions 標 `# W24c F4 (C16 Users Service)`;NEW `routes/users.py` 係 C16 API surface。
- **D4.5 — `AuditAction` F4 加 3,F7 加剩餘**(R6 #6)— F4.3 audit write 需 `AuditAction` 有對應 action,但 plan F7「Audit log expansion」才 extend `AuditAction`。F4 加佢需要嘅 3 個(`user.invited`/`user.suspended`/`role.changed`);F7 加 `kb.*`(`kb.access.granted`/`kb.config.changed`)+ 90d retention policy。`AuditAction` additive Literal append per F7 D0.2。
- **D4.6 — `/users` 無 server-side filter;filter seg client-side** — mockup `UsersTab` 嘅 filter(all/admin/editor/user/pending)100% client-side(`MOCK_USERS.filter`)。`GET /users` 返回全部,F9 frontend client-side filter + count。Tier 1 member count 小,無 perf 壓力。

### Acceptance(plan §3 + checklist F4)

- [x] F4.1 `GET /users` 返回全部 members(`UserListResponse`,newest-first);filter seg client-side per mockup
- [x] F4.2 `POST /users/invite`(建 invited record;email + accept flow 🚧 defer)+ `POST /users/{oid}/suspend` + `PATCH /users/{oid}/role`(power reject 422)
- [x] F4.3 audit_log writes(`user.invited`/`user.suspended`/`role.changed`)+ router-level `require_role("admin")`

### Verify

- **backend pytest 854 passed**(F3 baseline 839 → +15 `test_users_route.py`)+ 11 skipped + 0 failed — regression 0
- **mypy `--strict`** — `routes/users.py` / `schemas/user.py` / `users_repo.py` / `users_store.py` 0 error;`postgres_users_store.py` reported errors(psycopg import-not-found + 既有 `dict` type-arg + no-any-return)全部 pre-existing,F4 `list_users` 新 method clean
- **ruff** — F4 NEW files all clean;`server.py` 28 個 E402(truststore-after-imports 結構)= pre-existing — `git show HEAD:backend/api/server.py` 確認 F4 前已 28,F4 只加 `users` import(top block)+ 1 行 `include_router`,per Karpathy §1.3 surgical 未順手修
- **endpoint count** 45 → 49(+4 `/users/*`)

**Day 4 F4 Verdict**:F4 complete — `/users` Members tab backend landed。NEW `api/routes/users.py`(4 endpoints,router-level `require_role("admin")` — F3.4「per-endpoint apply」首次兌現)+ NEW `api/schemas/user.py` + `users_repo` 4 management functions + `UserRecord.status` + `UsersStore.list_users` + `AuditAction` +3。6 R6 findings resolved(全 §13 backend-wins / additive field / scope sequencing,auto-adjust)。backend pytest 854 + 0 fail。F5 `/users` Roles tab backend next。

## Day 5 — 2026-05-21 — F5 /roles Roles tab backend

### Done

- **F5 pre-active-flip 5-step grep audit recursive**(per CLAUDE.md §10 R6)— 讀 mockup `ekp-page-users.jsx` lines 19-286(`ROLES` + `PERMISSIONS_MATRIX` + `RolesTab`)+ `api/schemas/rbac.py` + `storage/rbac_storage.py`/`rbac_factory.py` + `server.py` lifespan + `routes/users.py` F4 router → 6 findings(plan §7 Day 5 row)
- **F5 NEW `api/routes/roles.py`** — 2 read-only endpoints router-level `require_role("admin")`:`GET /roles`(`RoleListResponse{roles,total}`,`backend.list_roles()`)+ `GET /roles/permissions`(`PermissionMatrixResponse{permissions,total}`,`backend.list_role_permissions()`);`_get_rbac_backend` helper 503-on-unwired per `routes/admin/identity.py` precedent
- **F5 EDIT `api/schemas/rbac.py`** — 加 2 response wrappers:`RoleListResponse{roles: list[Role], total}` + `PermissionMatrixResponse{permissions: list[RolePermission], total}`
- **F5 EDIT `api/server.py`** — lifespan 加 `rbac_backend = make_rbac_backend(settings)` + `await rbac_backend.seed_defaults()` + `app.state.rbac_backend = rbac_backend`(startup seed mandatory — `InMemoryRbacBackend` restart-wipe);import `make_rbac_backend` + `roles` route + `app.include_router(roles.router)`(無 `_auth` — router 自帶 `require_role`);endpoint count 49 → **51**
- **F5 tests** NEW `tests/api/test_roles_route.py` 14 cases(GET /roles:4-role/order/Power-User-Tier2-disabled/Tier1-active/admin-gate-403/401/503-unwired;GET /roles/permissions:92-row/23-distinct-key/5-area/admin-all-granted/user-denied-kb.create/admin-gate-403/503-unwired)
- **F5 committed** `(this commit)`

### Decisions

- **D5.1 — `app.state.rbac_backend` lifespan-wired + startup seed**(R6 #1)— F2 建咗 `make_rbac_backend` factory 但 `server.py` lifespan 從未 wire(key_vault/admin_provider/admin_identity/audit_log 都 wire 咗,RBAC 漏咗)。F5 lifespan 加 wire + `await …seed_defaults()`。`seed_defaults` 必須喺 startup await:`InMemoryRbacBackend` restart-wipe,唔 seed 則 `list_roles` 返回空;`seed_defaults` idempotent → Postgres path 已有 rows 時 no-op。用 local var(`rbac_backend = make_…` → `await` → assign)而非 `await app.state.rbac_backend.…`,因 `app.state.X` attribute 係 `Any` → mypy 失去 type-check;local var typed `RbacBackend`。
- **D5.2 — F5 = NEW `routes/roles.py` `prefix="/roles"` 獨立 module**(R6 #2)— plan §1 F5 spec-ref column 寫「`routes/users/` package」係 W22 D9 plan-text contamination(sketch-era 設想 users 係 package);plan §2 寫 literal path `GET /roles`(無 `/users` prefix)。F4 active-flip 已 deviate 到 `routes/users.py` single module(router `prefix="/users"`)。把 `/roles` 加入該 router → path 變 `/users/roles` 偏離 plan literal。roles/permissions 係 RBAC resource(非 users sub-resource);mockup 嘅 tab grouping(Roles tab 喺 `/users` page)係 frontend IA,≠ backend path nesting。F5 = 獨立 `routes/roles.py`。R6 auto-adjust(plan-text contamination,convention 明確)。
- **D5.3 — `GET /roles` 返回純 `Role` list,member count F9 client-side**(R6 #3)— mockup `RolesTab` line 225 `count = MOCK_USERS.filter(u => u.role === key).length` 100% client-side。F2 `Role` schema 無 `member_count` field。backend 加 count 要 join `users` table count-by-role = speculative surface(Karpathy §1.2)。F9 frontend `/users` page 已 fetch users list(Members tab,F4 `GET /users`)→ Roles tab client-side count。§13 backend wins on field shape;mirrors F4 D4.6(filter seg client-side)+ D4.1(backend subset)。
- **D5.4 — `GET /roles/permissions` 返回 flat `list[RolePermission]`(92-row),非 area-grouped pivot**(R6 #4)— mockup `PERMISSIONS_MATRIX` row shape = `{p, a, e, u, w}`(per-permission + 4 grants,area-grouped);F2 backend canonical = flat `RolePermission`(per-cell,92 row = 23 perm × 4 role,有 `area` field)。F5.2 返回 F2 canonical flat shape — §13 backend wins on field shape(`RolePermission` F2 已 lock)。F9 frontend pivot:group by `area` + per-permission collapse 4 role 嘅 `granted` 落一行 4-column。Backend pivot reshape = speculative。
- **D5.5 — F5 response schema 入 `api/schemas/rbac.py`,非 F4 `user.py`** — `RoleListResponse` + `PermissionMatrixResponse` 屬 roles/permissions domain → RBAC schema natural home(`rbac.py` 已有 `Role`/`RolePermission`/`RoleKey`)。F4 `user.py` 係 user-domain(`UserSummary` 等)。Roles ≠ users。
- **D5.6 — F5 router-level `require_role("admin")`**(R6 #6)— `/roles` + `/roles/permissions` 係 `/users` admin console surface 嘅一部分(mockup Roles tab 喺 admin `/users` page;permissions matrix view = admin policy surface)。一致 F4 `users.py` router-level gate — F3.4「per-endpoint apply F4-F10 inline」持續兌現。`_get_rbac_backend` 503-on-unwired helper 對齊 `routes/admin/identity.py` `_get_backend` precedent。

### Acceptance(plan §3 + checklist F5)

- [x] F5.1 `GET /roles` 返回 `RoleListResponse{roles,total}`(4 roles `_ROLE_ORDER`;Power User Tier 2 `active=False`)— NEW `routes/roles.py` + `app.state.rbac_backend` lifespan-wired + seeded;member count F9 client-side
- [x] F5.2 `GET /roles/permissions` 返回 `PermissionMatrixResponse{permissions,total}`(flat 92-row `RolePermission`;read-only,custom roles Tier 2 per H4)— router-level `require_role("admin")`

### Verify

- **backend pytest 868 passed**(F4 baseline 854 → +14 `test_roles_route.py`)+ 11 skipped + 0 failed — regression 0
- **mypy `--strict`** — `api/routes/roles.py` / `api/schemas/rbac.py` / `api/server.py` 0 error;`storage/rbac_postgres.py` reported errors(psycopg import-not-found)= CO17 R8 既有豁免(psycopg 未裝,與 `audit_log_postgres.py`/`postgres_users_store.py` 同類,非 F5 引入);jose/azure import-untyped + no-any-return pre-existing 豁免
- **ruff** — F5 NEW files(`routes/roles.py` / `tests/api/test_roles_route.py`)+ EDIT `schemas/rbac.py` all clean;`server.py` E402 34 → 35(+1 = 新 `make_rbac_backend` import line,truststore-after-imports 結構)= pre-existing structural class,`git show HEAD:backend/api/server.py` 確認 F5 前已 34,per Karpathy §1.3 surgical 未順手修
- **endpoint count** 49 → 51(+2 `/roles` + `/roles/permissions`)

**Day 5 F5 Verdict**:F5 complete — `/roles` Roles tab backend landed。NEW `api/routes/roles.py`(2 read-only endpoints,router-level `require_role("admin")`)+ `api/schemas/rbac.py` +2 response wrappers + `server.py` lifespan `app.state.rbac_backend` wire+seed(F2 factory 首次有 caller)。6 R6 findings resolved(全 §13 backend-wins / plan-text contamination / Karpathy §1.2 no-speculative,auto-adjust)。backend pytest 868 + 0 fail。F6 `/users` Groups tab backend + `sync-from-entra` next。

## Day 6 — 2026-05-21 — F6 /groups Groups tab backend + sync-from-entra

### Done

- **F6 pre-active-flip 5-step grep audit recursive**(per CLAUDE.md §10 R6)— 讀 mockup `ekp-page-users.jsx` lines 288-322(`GroupsTab`)+ `storage/rbac_postgres.py` `groups`/`group_members` schema + `storage/rbac_storage.py` Protocol + `api/schemas/admin_identity.py` `RoleMappingConfig` + `storage/settings.py` Entra config + `storage/azure_key_vault.py` `DefaultAzureCredential` pattern + `pyproject.toml` deps → 7 findings(plan §7 Day 6 row)
- **F6 NEW `api/auth/entra_graph.py`** — managed-REST Microsoft Graph client:`EntraGroup` frozen dataclass + `fetch_entra_groups()`(`azure-identity` `DefaultAzureCredential` lazy-import acquire app token for `graph.microsoft.com/.default` + `httpx` `GET /v1.0/groups`,`@odata.nextLink` pagination);零新 dependency(per F1 D1)
- **F6 NEW `api/routes/groups.py`** — 2 endpoints router-level `require_role("admin")`:`GET /groups`(`GroupListResponse`)+ `POST /groups/sync-from-entra`(`GroupSyncResult`;`azure_tenant_id` unset → graceful `status="skipped"`、Graph failure → 502);`_get_rbac_backend` 503-on-unwired helper(對齊 F5)
- **F6 EDIT `api/schemas/rbac.py`** — 加 `GroupSource` Literal + `Group{group_key,name,description,source,entra_object_id,synced_at,member_count}` + `GroupListResponse{groups,total}` + `GroupSyncResult{status,synced_count,detail}`
- **F6 EDIT `storage/rbac_storage.py`** — `RbacBackend` Protocol +2(`list_groups`/`upsert_entra_group`)+ `InMemoryRbacBackend` impl(`_groups` dict;`list_groups` sorted by name;`upsert_entra_group` stamps `source='entra'`+`synced_at`)
- **F6 EDIT `storage/rbac_postgres.py`** — `groups` table 加 `synced_at TIMESTAMPTZ`(`_CREATE_TABLES` + idempotent `_ALTER_GROUPS` ALTER ADD COLUMN IF NOT EXISTS)+ `list_groups`(`LEFT JOIN group_members … GROUP BY` member count)+ `upsert_entra_group`(`ON CONFLICT (group_key) DO UPDATE`)+ `_row_to_group` helper + docstring 更新
- **F6 EDIT `api/server.py`** — import `groups` route + `app.include_router(groups.router)`;endpoint count 51 → **53**
- **F6 tests** NEW `tests/api/test_groups_route.py` 9 cases(GET /groups:empty/admin-gate-403/401/503-unwired;sync:skipped-when-Entra-unconfigured/synced+count/synced-groups-listed-with-shape/admin-gate-403/502-on-Graph-failure;mock `entra_graph.fetch_entra_groups`)
- **F6 committed** `(this commit)`

### Decisions

- **D6.1 — `groups` table 加 `synced_at` column(additive ALTER)**(R6 #2)— mockup `GroupsTab` 有 `Synced` column(per-group last-sync time),F2 `_CREATE_TABLES` `groups` schema 無 `synced_at`。F6 加 `synced_at TIMESTAMPTZ` — `_CREATE_TABLES` 補 column(fresh DB)+ idempotent `ALTER TABLE groups ADD COLUMN IF NOT EXISTS synced_at`(F2 已建嘅 table)。對齊 F4 `users.role`/`users.status` ALTER precedent。W24c/ADR-0027 RBAC schema scope 內、additive 非 breaking → R3-changelog deviation 非 H1。F2 `rbac_storage.py`/`rbac_postgres.py` docstring「F6 add only Protocol methods, never a migration」stale claim 一併更新(per Karpathy §1.3 surgical — F6 令佢 inaccurate)。
- **D6.2 — `GET /groups` 返回純 group;`EKP role` column F9 client-side join**(R6 #3)— mockup `GroupsTab` `EKP role` column = group→role mapping,佢喺 `admin_identity.RoleMappingConfig`(`RoleMapping{ekp_role,entra_group_name,entra_group_id}`,W24-c1 F3 已有 `GET /admin/identity` endpoint),`groups` table 無 `mapped_role`。mockup card-desc 明示「group → role mapping in Settings → Identity & Auth」= separate concern。`GET /groups` 返回純 group,F9 frontend client-side join from `GET /admin/identity`。§13 backend-subset;mirrors F4 D4.1 / F5 D5.3。
- **D6.3 — group `member_count` backend-computed**(R6 #4)— `group_members` 係 `groups` 嘅直屬 child table(`PK (group_key, user_oid)`),count-by-group 係 group 自己 aggregate。對比 F5 D5.3 role member count 要 cross-domain join `users` table(→ client-side),group member count 喺直屬 child table → backend-computed 合理(Postgres `LEFT JOIN group_members … GROUP BY` / InMemory dict)。F6 值 = 0(member sync defer per D6.5);`Group.member_count` 欄位忠實 ship — `group_members` 係 real declared table、LEFT JOIN 係 real query,非 speculative(對比 F4 D4.1 dropped column 係完全無 backing 嘅 analytics)。
- **D6.4 — `sync-from-entra` = managed-REST via `azure-identity` `DefaultAzureCredential`**(R6 #5)— backend 係 resource-server-only(`settings.py` 只有 `azure_tenant_id`+`azure_client_id`,**無 `client_secret`**)。F1 D1 managed-REST decision 落實:NEW `api/auth/entra_graph.py` 用 `azure-identity` `DefaultAzureCredential`(mirror `storage/azure_key_vault.py` lazy-import — `pyproject.toml` 確認 `azure-identity>=1.20`+`httpx>=0.27` 已裝,零新 dep)acquire app token + `httpx` Graph REST call。`entra_graph.py` co-located 喺 `api/auth/`(Entra = identity infra,同 `msal_provider`/`email_provider` 一組),component-tag C16。`azure_tenant_id` unset(mock-auth dev)→ route short-circuit graceful `status="skipped"`(non-500,從不 import `azure-identity`);config-set live path = deferred pre-Beta smoke(R-W24c-6 / CO17 umbrella;route test mock `fetch_entra_groups`)。
- **D6.5 — group member sync 🚧 defer W24d+/F8**(R6 #6)— Graph `/groups/{id}/members` per-group enumeration + Entra-oid↔EKP-user(`users.oid`)matching 係 separate larger concern。F6 sync group **list** only(`upsert_entra_group`)。`group_members` table populate(member sync)+ `add_group_member` Protocol 留 W24d+ 或 F8 per-KB ACL principal wiring。per Karpathy §1.2 no speculative。
- **D6.6 — `sync-from-entra` 不加 `AuditAction`、不寫 audit row**(R6 #7)— mockup `AuditTab`(lines 324-377)action 列表(`role.changed`/`user.invited`/`user.suspended`/`kb.access.granted`/`provider.key.rotated`/`kb.config.changed`)無 group sync event;plan F7 audit action 列表亦無 group action。F6 `sync-from-entra` 純 upsert + 返回 result,無 audit。per Karpathy §1.2 — 唔加 mockup/plan 都冇嘅 `AuditAction`。
- **D6.7 — plan-text「Entra Graph SDK」+ Component C12 = pre-F1 contamination**(R6 #7)— plan §2 F6 字面「Entra Graph SDK」+「C12(Entra Graph SDK)」係 pre-F1 sketch(W22 D9 plan-text-contamination class)。F1 D1 已 decide managed-REST(零新 dep、零 C12 install)。F6 refine plan §2 用 managed-REST 字眼,Component = C16+C08。R6 auto-adjust。

### Acceptance(plan §3 + checklist F6)

- [x] F6.1 `GET /groups` 返回 `GroupListResponse{groups,total}`(`Group` 含 `member_count` backend-computed;`EKP role` F9 client-side join)— NEW `routes/groups.py` + `RbacBackend` `list_groups` + InMemory + Postgres LEFT JOIN
- [x] F6.2 `POST /groups/sync-from-entra` 返回 `GroupSyncResult` — NEW `api/auth/entra_graph.py` managed-REST(`azure-identity`+`httpx`,零新 dep)+ `RbacBackend` `upsert_entra_group` + `groups` `synced_at` ALTER;Entra unset → graceful `skipped`、Graph failure → 502;router-level `require_role("admin")`

### Verify

- **backend pytest 877 passed**(F5 baseline 868 → +9 `test_groups_route.py`)+ 11 skipped + 0 failed — regression 0
- **mypy `--strict`** — `api/auth/entra_graph.py` / `api/routes/groups.py` / `api/schemas/rbac.py` / `storage/rbac_storage.py` 0 error;`storage/rbac_postgres.py` reported errors(psycopg import-not-found)= F2 CO17 R8 既有豁免(psycopg 未裝,F6 未引入新 psycopg import);jose/azure import-untyped + no-any-return + type-arg + no-untyped-def pre-existing 豁免
- **ruff** — F6 NEW/EDIT files all clean(F6-introduced `datetime.now(timezone.utc)` UP017 → 改現代 `datetime.now(UTC)` alias,per Karpathy §1.3 清自己嘅 mess;`server.py` E402 35→35 不變 — `groups` 加入既有 `from api.routes import (…)` multi-line block,非新 import statement)
- **endpoint count** 51 → 53(+2 `/groups` + `/groups/sync-from-entra`)

**Day 6 F6 Verdict**:F6 complete — `/groups` Groups tab backend + `sync-from-entra` landed。NEW `api/auth/entra_graph.py`(managed-REST Graph client,零新 dep per F1 D1)+ `api/routes/groups.py`(2 endpoints)+ `rbac.py` +3 group schemas + `RbacBackend` +2 Protocol methods(InMemory + Postgres)+ `groups.synced_at` additive ALTER。7 R6 findings resolved(全 F2-predicted surface / additive-ALTER-F4-precedent / §13 backend-subset / Karpathy §1.2 no-speculative / plan-text-contamination,auto-adjust)。group member sync 🚧 defer W24d+/F8。backend pytest 877 + 0 fail。F7 Audit log expansion next。

## Day 7 — 2026-05-21 — F7 Audit log expansion

### Done

- **F7 pre-active-flip 5-step grep audit recursive**(per CLAUDE.md §10 R6)— 讀 `api/schemas/audit_log.py` `AuditAction` Literal + `storage/audit_log_storage.py`/`audit_log_postgres.py`(無 retention)+ `api/routes/kb.py` `update_kb_settings` + `api/routes/admin/audit_log.py` + mockup `ekp-page-users.jsx` lines 324-377(`AuditTab`)+ `tests/storage/test_audit_log.py`/`tests/test_kb_metadata_patch.py` → 6 findings(plan §7 Day 7 row)
- **F7.1 EDIT `api/schemas/audit_log.py`** — `AuditAction` Literal +2(`kb.access.granted` + `kb.config.changed`);F4 D4.5 已加 `user.invited`/`user.suspended`/`role.changed`
- **F7.2 EDIT `api/routes/kb.py`** — `update_kb_settings` 加 `request: Request` param + `kb.config.changed` audit write(`actor=None`,`resource=f"kb/{kb_id}"`,`payload=config.model_dump(mode="json")`,best-effort `getattr(app.state, "audit_log_backend", None)` skip-when-unwired);try/except restructure(`return` 移出 try,audit write 喺 success path);NEW import `AuditLogBackend`
- **F7.3 EDIT `storage/audit_log_storage.py`** — `AuditLogBackend` Protocol +`prune_expired(retention_days: int = 90) -> int` + `InMemoryAuditLogBackend` impl(list-comprehension filter `created_at >= cutoff`);`timedelta` import
- **F7.3 EDIT `storage/audit_log_postgres.py`** — `PostgresAuditLogBackend.prune_expired`(`DELETE … WHERE created_at < NOW() - make_interval(days => %s)`,`cur.rowcount`)
- **F7.3 EDIT `api/server.py`** — lifespan startup `audit_log_backend = make_audit_log_backend(settings)` + `await audit_log_backend.prune_expired(90)` + `app.state` assign(local-var pattern,mirror F5 rbac_backend)
- **F7 tests** — `tests/storage/test_audit_log.py` +3 cases(`prune_expired` removes-old / keeps-recent / respects-retention-days);`tests/test_kb_metadata_patch.py` +1 case(`test_update_kb_settings_writes_audit` — `kb.config.changed` write + payload)
- **F7 committed** `(this commit)`

### Decisions

- **D7.1 — F7 只加 2 個 `AuditAction`**(R6 #1)— plan F7.1 literal 列 5 個,其中 `user.invited`/`user.suspended`/`role.changed` F4 D4.5 已加(`audit_log.py` comment「W24c F7 adds the kb.* actions」已預告)。F7 加剩餘 2 個 `kb.*`(`kb.access.granted` + `kb.config.changed`)。
- **D7.2 — `kb.access.granted` Literal 加咗、write 🚧 defer F8**(R6 #2)— `kb.access.granted` 嘅 write site = per-KB ACL grant 操作,屬 F8 `kb_acl` CRUD endpoint;F7 時點該 endpoint 未建。F7.1 加 `AuditAction` Literal(`kb.access.granted` 可被 F8 引用),write 連 `kb_acl` CRUD endpoint 一齊喺 F8 — per F4 D4.5「F7/F8 sequencing」+ Karpathy §1.2 no write-without-endpoint。`AuditAction` Literal 加喺 F7(audit-log-expansion deliverable)係正確 home — F8 唔應該又 expand `AuditAction`。
- **D7.3 — `update_kb_settings` 只加 `request: Request`,不加 `Depends(get_current_user)` → `actor=None`**(R6 #3)— `kb.config.changed` write site = `PATCH /kb/{kb_id}/settings`。若加 `Depends(get_current_user)` 攞 actor,pre-existing `test_kb_metadata_patch.py:127 test_patch_kb_settings_unchanged_by_metadata_patch`(minimal-app,無 auth setup)會收 401 regression。`update_kb_settings` 喺 `server.py` 已 router-level `_auth`,真實 request 已 authenticated,但 minimal test app 繞過。Karpathy §1.3 surgical — 加 auth dependency 到 pre-existing endpoint + 改 pre-existing test = 擴大 blast radius。改為只加 `request: Request`(`Request` injection 唔影響 minimal test app),audit `actor=None` — 對齊 `routes/admin/identity.py` `_audit_identity_patch(actor=None)` 既有 pattern + `audit_log.py` schema doc 明示「actor ... Wave C2 promotes when ADR-0027 wires actor extraction at middleware level」。Per-endpoint actor extraction 係 middleware-level 後續 concern,非 F7 scope。
- **D7.4 — `kb.config.changed` 只 wire `update_kb_settings`,不 wire `update_kb_metadata`**(R6 #4)— mockup `AuditTab` `kb.config.changed` event(「Customer Service SOP · default_top_k 50 → 30」)係 `KbConfig` field。`kb.config.changed` 語義 = `KbConfig` change → `update_kb_settings`(`PATCH /kb/{kb_id}/settings`)。`update_kb_metadata`(`PATCH /kb/{kb_id}`,name/description)係 metadata 非 config → 不 wire(避免 over-extend per Karpathy §1.2 + W22 D6 over-extending anti-pattern;Decision A.1 separation-of-concern 已區分 metadata vs config)。
- **D7.5 — 90d retention = `prune_expired` Protocol method + lifespan startup call**(R6 #5)— `audit_log` table 無 retention 機制,Tier 1 無 background scheduler/cron。`AuditLogBackend` Protocol 加 `prune_expired(retention_days: int = 90)`(InMemory list-filter / Postgres `DELETE`)。`server.py` lifespan startup call `prune_expired(90)` — best-effort retention:server restart/deploy(常見)時 prune,~90d window 足夠(retention policy 唔需精確到秒)。90d hard-code(plan + mockup 都明寫「90d retention」),不加 `settings` field per Karpathy §1.2 no speculative config。
- **D7.6 — `kb.config.changed` payload = new `KbConfig` snapshot**(R6 #6)— mockup `AuditTab` 顯示「default_top_k 50 → 30」before→after diff,但既有 F2/F3/F4 audit payload pattern = 記 mutation content(F4 `user.invited` payload `{email,role}`、F3 `identity_patch` payload sanitized PATCH 內容),非 before/after diff。F7 payload = `config.model_dump(mode="json")`(new `KbConfig` snapshot — `KbConfig` 無 secret)。before/after diff 渲染係 frontend concern;§13 backend ships mutation payload。

### Acceptance(plan §3 + checklist F7)

- [x] F7.1 `AuditAction` Literal +2(`kb.access.granted` + `kb.config.changed`);`kb.access.granted` write 🚧 deferred F8
- [x] F7.2 `kb.config.changed` audit write on `PATCH /kb/{kb_id}/settings`(`update_kb_settings` +`request: Request`,`actor=None`,best-effort skip-when-unwired);不 wire `update_kb_metadata`
- [x] F7.3 90d retention — `AuditLogBackend` Protocol +`prune_expired` + InMemory + Postgres impl + `server.py` lifespan startup call

### Verify

- **backend pytest 881 passed**(F6 baseline 877 → +4:`test_audit_log.py` +3 `prune_expired` + `test_kb_metadata_patch.py` +1 `kb.config.changed` audit)+ 11 skipped + 0 failed — regression 0(pre-existing `test_patch_kb_settings_unchanged_by_metadata_patch` 仍 pass — `update_kb_settings` 加 `request: Request` 無 break minimal test app)
- **mypy `--strict`** — `api/schemas/audit_log.py` / `storage/audit_log_storage.py` / `api/routes/kb.py` F7 code 0 error;`kb.py:220 reindex_kb -> dict` `type-arg` = pre-existing W16 F5.3.1 signature(F7 `update_kb_settings` expansion 令行號下移,非 F7 引入,per Karpathy §1.3 surgical 未順手修);`storage/audit_log_postgres.py` psycopg import-not-found = CO17 R8 既有豁免
- **ruff** — F7 NEW code all clean(F7-introduced `tests/storage/test_audit_log.py` `datetime.now(timezone.utc)` UP017 → 改現代 `datetime.now(UTC)` alias,per Karpathy §1.3 清自己嘅 mess);pre-existing UP017(`audit_log_storage.py:23 _now()` + `test_audit_log.py` 既有 3 個 `tzinfo=timezone.utc`)未碰;`server.py` E402 35→35 不變(F7 lifespan 加 3 行,無新 import statement)
- **endpoint count** 53 → 53 不變(F7 無新 endpoint)

**Day 7 F7 Verdict**:F7 complete — Audit log expansion landed。`AuditAction` Literal +2(`kb.access.granted` + `kb.config.changed`)+ `kb.config.changed` audit write wired on `update_kb_settings` + `AuditLogBackend.prune_expired` 90d retention(InMemory + Postgres)+ `server.py` lifespan startup prune。6 R6 findings resolved(全 F4-sequenced / Karpathy §1.3 surgical avoid-regression / §1.2 no-over-extend+no-speculative-config,auto-adjust)。`kb.access.granted` write 🚧 defer F8。backend pytest 881 + 0 fail。F8 per-KB ACL(`kb_acl`)next。

## Day 8 — 2026-05-21 — F8 per-KB ACL(`kb_acl`)

### Done

- **F8 pre-active-flip 5-step grep audit recursive**(per CLAUDE.md §10 R6)— 讀 mockup `ekp-page-users.jsx` lines 389-519(`TabKbAccess`)+ `api/middleware/acl.py`(F3 `require_role`)+ `storage/rbac_storage.py`/`rbac_postgres.py`(`kb_acl` F2-declared schema)+ `api/auth/models.py`(`AuthenticatedUser.oid`)→ 8 findings(plan §7 Day 8 row)
- **F8.1 NEW `api/routes/kb_acl.py`** — 4 CRUD endpoints router-level `require_kb_acl("manage")`:`GET /kb/{kb_id}/acl`(`KbAclListResponse`)+ `POST`(`KbAclEntry` 201,upsert + `kb.access.granted` audit write,`granted_by` = actor)+ `PATCH /{entry_id}`(role override,404)+ `DELETE /{entry_id}`(204,404);`_get_rbac_backend` 503-on-unwired + `_audit` best-effort helper
- **F8.1 EDIT `api/schemas/rbac.py`** — `KbAclRole` Literal(`manage`/`edit`/`query`)+ `KbPrincipalType` Literal(`user`/`group`)+ `KbAclEntry` + `KbAclListResponse` + `KbAclGrantRequest` + `KbAclRoleChangeRequest`
- **F8.1 EDIT `storage/rbac_storage.py`** — `RbacBackend` Protocol +5(`list_kb_acl`/`add_kb_acl`/`set_kb_acl_role`/`remove_kb_acl`/`get_kb_access`)+ `InMemoryRbacBackend` impl(`_kb_acl` list;`add_kb_acl` upsert on (kb_id,principal_type,principal_id);`set`/`remove` scoped by `kb_id`)
- **F8.1 EDIT `storage/rbac_postgres.py`** — `kb_acl` 加 `granted_by` column(`_ALTER_KB_ACL` additive ALTER)+ 5 method Postgres impl(`add_kb_acl` `ON CONFLICT DO UPDATE`;`remove_kb_acl` `DELETE … RETURNING id`)+ `_row_to_kb_acl` + `_KB_ACL_COLS` + docstring 更新
- **F8.2 EDIT `api/middleware/acl.py`** — `require_kb_acl(min_role)` async dependency factory(workspace `admin` always-pass;else direct user `kb_acl` grant ≥ `min_role`,`_KB_ACL_RANK` manage>edit>query;503 when `rbac_backend` unwired)+ docstring 更新「lands with F8」stale claim
- **F8 EDIT `api/server.py`** — import `kb_acl` route + `app.include_router(kb_acl.router)`;endpoint count 53 → **57**
- **F8 tests** — NEW `tests/api/test_kb_acl_route.py` 14 cases;`tests/storage/test_rbac_storage.py` +5 `kb_acl` cases;`tests/api/test_acl_middleware.py` +5 `require_kb_acl` cases
- **F8 committed** `(this commit)`

### Decisions

- **D8.1 — `kb_acl` 加 `granted_by` column(additive ALTER)**(R6 #2)— mockup `TabKbAccess` table 有「Granted by」column,F2 `kb_acl` schema 無。F8 加 `granted_by TEXT` — `_ALTER_KB_ACL` idempotent `ALTER TABLE kb_acl ADD COLUMN IF NOT EXISTS`(對齊 F6 `synced_at` ALTER precedent;W24c/ADR-0027 RBAC schema scope 內)。`POST` 寫 `granted_by` = actor `preferred_username`。`rbac_postgres.py` docstring「兩個 additive ALTER」一併更新。
- **D8.2 — `GET /kb/{kb_id}/acl` 返回 explicit `kb_acl` grants only**(R6 #3)— mockup `TabKbAccess` table 嘅 row 唔全部係真 `kb_acl` row:`system`/auto-locked row(workspace admin)+ `inherited` row(`granted_by:"(group)"`,group membership 衍生)係 synthetic/derived,加 `Workspace role` column 係 join。`GET` 返回 `kb_acl` table explicit grants;synthetic rows + workspace-role join F10 frontend 渲染。§13 backend-subset;mirrors F4 D4.1 / F6 D6.2。
- **D8.3 — KB Visibility 🚧 defer**(R6 #4)— mockup `TabKbAccess` 有 Visibility card(private/workspace/public-Tier2),係 KB-level setting(邊個睇得到 KB),**唔係 `kb_acl`**(per-principal grant)。plan F8 scope = `kb_acl` CRUD(ADR-0027 §Decision `kb_acl` table)。KB Visibility(需 `KbStatus`/`KbConfig` enum field + endpoint,屬 C02 KB Manager metadata)defer — F10 frontend Access tab 渲染 Visibility card 時 surface,或 W24d+。per Karpathy §1.2 no over-extend。
- **D8.4 — `require_kb_acl` admin always-pass + direct user grant;group-inherited 🚧 defer**(R6 #5)— `acl.py` 加 `require_kb_acl(min_role)` async dependency factory:workspace `admin` always-pass(ADR-0027「Workspace Admins always have full access」);else `get_kb_access(kb_id, user.oid)` direct user `kb_acl` grant,role-rank `manage>edit>query`。group-based per-KB access(user 透過 group membership 得 access)需要 `group_members` membership data,但 F6 D6.5 已 defer group member sync → F8 `get_kb_access` 只 check direct `principal_type='user'` grant;group-inherited access resolution defer(連 F6 member sync)。mock-auth dev 全 admin → `require_kb_acl` always-pass,不阻礙。
- **D8.5 — NEW `routes/kb_acl.py` 獨立 module;actor 可寫真值**(R6 #6)— `/kb/{kb_id}/acl` 係 KB sub-resource,但 `kb.py`(C02)已大 + `kb_acl` 係 C16 per-KB ACL concern → 獨立 `routes/kb_acl.py`。NEW route 可加 `Depends(get_current_user)`(無 pre-existing test regression — 對比 F7 D7.3 `update_kb_settings` 係 pre-existing endpoint 不能加 auth dep → `actor=None`;F8 `kb_acl` route NEW)→ `kb.access.granted` audit 寫真 actor `current_user.preferred_username`。
- **D8.6 — `set_kb_acl_role`/`remove_kb_acl` scoped by `kb_id`** — implementation-time finding:`kb_acl.id` 係 global SERIAL。若 `set`/`remove` 只用 `entry_id`,某 KB-A 嘅 manager 可以 `PATCH /kb/KB-A/acl/{id}` 用一個屬 KB-B 嘅 entry_id 改到 KB-B 嘅 grant(`require_kb_acl("manage")` 只 authorize path 嘅 KB-A)。→ `set_kb_acl_role(kb_id, entry_id, ...)`/`remove_kb_acl(kb_id, entry_id)` 兩個都 scope by `kb_id`(InMemory match `id AND kb_id`;Postgres `WHERE id = %s AND kb_id = %s`)。per Karpathy §1.4 goal-driven — 正確 per-KB ACL 唔可以有 cross-KB entry-id leak。
- **D8.7 — `kb.access.granted` 只喺 `POST` 寫,`PATCH`/`DELETE` 不寫 audit**(R6 #7)— `kb.access.granted` `AuditAction` literal F7.1 已加。`POST`(add grant)寫 `kb.access.granted`。`PATCH`(role override)/`DELETE`(revoke)無對應 mockup `AuditTab` action / 無 `AuditAction` literal → 不寫(per Karpathy §1.2 — 唔加 mockup/plan 都冇嘅 `AuditAction`)。
- **D8.8 — `remove_kb_acl` Postgres 用 `DELETE … RETURNING id` + `fetchone() is not None`** — implementation-time finding:`return cur.rowcount > 0` 喺 psycopg-uninstalled(CO17 R8 dev env)`cur` 係 `Any` → `cur.rowcount` `Any` → `Any > 0` `Any` → mypy `no-any-return`(returning Any as bool)。`# type: ignore` 唔啱(psycopg 裝咗時 `cur.rowcount` 係 `int` → ignore 變 unused → `--strict --warn-unused-ignores` 報錯)。改用 `DELETE … RETURNING id` + `await cur.fetchone() is not None` — `is not None` 永遠產生 `bool`(無論 operand 係 `Any` 定 typed),兩種環境都 mypy-clean。

### Acceptance(plan §3 + checklist F8)

- [x] F8.1 `kb_acl` CRUD — NEW `routes/kb_acl.py` 4 endpoints + `granted_by` ALTER + `RbacBackend` Protocol +5 methods + InMemory + Postgres impl
- [x] F8.2 `acl.py` 加 `require_kb_acl(min_role)`(admin always-pass + direct user grant,role-rank)+ apply 到 `kb_acl` CRUD router;group-inherited + 其他 KB endpoint retrofit 🚧 deferred

### Verify

- **backend pytest 905 passed**(F7 baseline 881 → +24:`test_kb_acl_route.py` 14 + `test_rbac_storage.py` +5 + `test_acl_middleware.py` +5)+ 11 skipped + 0 failed — regression 0
- **mypy `--strict`** — `api/routes/kb_acl.py` / `api/middleware/acl.py` / `api/schemas/rbac.py` / `storage/rbac_storage.py` 0 error;`storage/rbac_postgres.py` 只剩 psycopg import-not-found = CO17 R8 既有豁免（F8 `remove_kb_acl` 改 `RETURNING id`+`fetchone() is not None` 避免 `cur.rowcount` `no-any-return` per D8.8）
- **ruff** — F8 NEW/EDIT files all clean;`server.py` E402 35→35 不變(`kb_acl` 加入既有 multi-line import block)
- **endpoint count** 53 → 57(+4 `/kb/{kb_id}/acl` CRUD)

**Day 8 F8 Verdict**:F8 complete — per-KB ACL(`kb_acl`)landed。NEW `api/routes/kb_acl.py`(4 CRUD endpoints router-level `require_kb_acl("manage")`)+ `acl.py` `require_kb_acl` dependency factory + `RbacBackend` +5 `kb_acl` Protocol methods(InMemory + Postgres)+ `kb_acl.granted_by` additive ALTER + F7-deferred `kb.access.granted` audit write 兌現。8 R6 findings resolved + 2 implementation-time findings(D8.6 cross-KB scope / D8.8 `no-any-return` 避免)。KB Visibility + group-inherited access + 其他 KB endpoint `require_kb_acl` retrofit 🚧 defer。backend pytest 905 + 0 fail。F9 frontend `/users` 4-tab page next。

## Day 9 — 2026-05-21 — F9.1 frontend foundation(`GET /auth/me` + users API client + `useRole()`)

### Done

- **F9 pre-active-flip 5-step grep audit recursive**(per CLAUDE.md §10 R6)— Explore agent 調研 frontend structure + 讀 `PAGE_INVENTORY.md` + `frontend/lib/providers/auth-provider.tsx` + `backend/api/routes/auth.py` → 6 findings(plan §7 Day 9 row)+ F9 sub-split F9.1-F9.4
- **F9.1 backend `GET /auth/me`** — NEW `auth.py` endpoint(`response_model=AuthenticatedUser`,`Depends(get_current_user)` non-admin — 任何 authenticated user 讀自己 role)+ test EDIT `tests/test_auth_endpoints.py` +3 cases(authenticated returns user+role / 401 unauthenticated / mock default role admin);endpoint count 57 → **58**
- **F9.1 frontend NEW `lib/api/users.ts`** — `usersApi` client + TS types mirror backend Pydantic(snake_case):F4 `UserSummary`/`UserListResponse`/`InviteRequest`/`UserDisplayStatus` + F5 `Role`/`RolePermission`/`RoleListResponse`/`PermissionMatrixResponse` + F6 `Group`/`GroupListResponse`/`GroupSyncResult` + F9.1 `MeResponse`;9 methods(`getMe`/`listUsers`/`inviteUser`/`suspendUser`/`changeUserRole`/`listRoles`/`listPermissions`/`listGroups`/`syncGroupsFromEntra`);`EkpRoleKey` import-reuse from `lib/api/admin.ts`
- **F9.1 frontend NEW `lib/hooks/use-role.ts`** — `useRole()` hook(`'use client'`,TanStack `useQuery(['auth','me'])` → `EkpRoleKey | null`,5min staleTime)
- **F9.1 committed** `(this commit)`

### Decisions

- **D9.1 — F9 sub-split F9.1-F9.4**(R6 #1)— F9 NET NEW `/users` 4-tab route + `useRole()` + role-gating + H7 全程約束 = ~3 plan days,per plan §2 + §7 R3 sub-split:F9.1 foundation / F9.2 route shell + Members tab / F9.3 Roles + Groups tabs / F9.4 Audit tab + role-gating + H7 verify + tests。原 checklist F9.1/F9.2/F9.3(route / useRole / H7-verify)scope 全數吸收。
- **D9.2 — backend NEW `GET /auth/me` 作 `useRole()` data source**(R6 #2)— frontend `AuthenticatedUser`(`lib/auth/types.ts`)只有 `oid`/`tid`/`preferredUsername`/`isMock`,**無 `role`**;`auth.py` 無 current-user endpoint。F3 D3.2 加 `role` 落 backend `AuthenticatedUser`(3-path server-resolved)但 frontend 睇唔到。F9.1 加 `GET /auth/me` 返回 current user + `role`。NOT H1(read endpoint,W24c C16/C11 scope,同 F4-F8 13 NEW endpoints 同類非架構)— R6 auto-adjust。`response_model=AuthenticatedUser`(既有 Pydantic model,無需 NEW schema per Karpathy §1.2)。
- **D9.3 — `GET /auth/me` 放 `auth.py` 非 `users.py`**(R6 #6)— `routes/users.py` router-level `require_role("admin")`;`/auth/me` 不可 admin-gate(任何 user 讀自己 role)→ 放 `auth.py`(C11,in-route `Depends(get_current_user)`,無 admin gate)。
- **D9.4 — NEW `lib/api/users.ts` 非 extend `admin.ts`**(R6 #3)— `/users`+`/roles`+`/groups` 係 top-level path(非 `/admin/*`),`adminApi` 限 `/admin/*` surface → 獨立 `lib/api/users.ts`。TS types snake_case mirror backend Pydantic(對齊 `admin.ts` 既有 convention)。`EkpRoleKey`+`EKP_ROLE_LABELS` F3.0 已 land 喺 `admin.ts` → import-reuse,不重定義(R6 #4)。
- **D9.5 — `useRole()` = TanStack `useQuery` fetch `/auth/me`** — auth store(`useAuthStore` Zustand)俾 identity,`useRole()` 獨立 fetch `/auth/me` 攞 authoritative role(backend-resolved per F3)。`useQuery(['auth','me'])` 5min staleTime cache。放 NEW `lib/hooks/use-role.ts`(`'use client'`)— hook 唔可以塞入 `users.ts` API client module(mixing concerns)。

### Acceptance(plan §2 F9 sub-split F9.1)

- [x] F9.1 backend `GET /auth/me`(current user + role,non-admin)+ `MeResponse`(= `AuthenticatedUser` reuse)+ test
- [x] F9.1 frontend `lib/api/users.ts`(`/users`+`/roles`+`/groups` client + TS types)+ `useRole()` hook

### Verify

- **backend pytest 908 passed**(F8 baseline 905 → +3 `test_auth_endpoints.py` `/auth/me`)+ 11 skipped + 0 failed — regression 0
- **mypy `--strict`** — `api/routes/auth.py` 0 error
- **ruff** — `auth.py` + `test_auth_endpoints.py` all clean
- **frontend** — `tsc --noEmit`(type-check)exit 0;`next lint` no warnings/errors;F9.1 純 TS plumbing(`users.ts` + `use-role.ts`)無 `.tsx`/`.css` → `[oklch` N/A
- **endpoint count** 57 → 58(+1 `GET /auth/me`)

**Day 9 F9.1 Verdict**:F9.1 complete — frontend foundation landed。backend `GET /auth/me`(`useRole()` data source — R6 #2 gap closed)+ frontend `lib/api/users.ts`(`/users`+`/roles`+`/groups` client mirror F4-F6 schemas)+ `useRole()` hook。6 R6 findings resolved + F9 sub-split F9.1-F9.4。backend pytest 908 + 0 fail。F9.2 `/users` route shell + Members tab next。

---

## Day 10 — 2026-05-21 — F9.2 `/users` route shell + Members tab

### Done

- **F9.2 pre-active-flip 5-step grep audit recursive**(per CLAUDE.md §10 R6)— 讀 mockup `ekp-page-users.jsx` lines 62-207(`PageUsers`+`UsersTab`+`RoleBadge`)+ `settings/page.tsx` tab pattern + `kb/page.tsx` data-fetch/placeholder pattern + `components/settings/tab-error-state.tsx` + `lib/api/admin.ts`(`EkpRoleKey`/`EKP_ROLE_LABELS`)+ `styles-mockup.css` class confirm → **10 findings**(plan §7 Day 10 row)
- **F9.2 NEW `components/users/role-badge.tsx`** — shared `RoleBadge`(Members F9.2 + Roles + Groups F9.3 三-tab consumer);per mockup `ekp-page-users.jsx` lines 193-207 + `ROLES` lines 19-24;4 role oklch token color(`admin`=`--accent`、`editor`/`user`/`power`=literal oklch);label 重用 `EKP_ROLE_LABELS`(F3.0 已 land);mockup runtime `.replace(")", " / 0.12)")` → precomputed literal token strings(identical output)
- **F9.2 NEW `app/(app)/users/page.tsx`** — `/users` route NET NEW。route shell:`<Suspense>` + page-header(title「Users & access」+ subtitle + Export CSV / Invite member 兩 inert button)+ stat-grid 4-card + 4-tab nav(`<button role="tab">` + `?tab=` deep-link per settings precedent + Members tab `.count` badge)+ local `<TabBoundary>`(reuse `ErrorBoundary` + `TabErrorState`)。Members tab(inline `UsersTab`)— client-side search(name+email)+ seg filter(All/Admin/Editor/User/Pending,counts)+ 10-col table(`useQuery(['users','list'])` → `usersApi.listUsers`;loading / error banner / empty / data 四態);`StatCard`/`TabPlaceholder` helper inline;roles/groups/audit tab = transient `<TabPlaceholder>`(F9.3/F9.4 replace)
- **F9.2 committed** `(this commit)`

### Decisions

- **D10.1 — `GET /users` backend-subset 10-col table 全 column keep + `—` placeholder**(R6 #2)— F4 D4.1 已定 `UserSummary` = `oid/email/display_name/role/status/created_at`;mockup table 有 `source`/`group`/`queries_7d`/`kbs_owned`/`last_login` 5 個無 backend field 嘅 column。per CLAUDE.md §13 v1.9 — keep 全 10 column(visual fidelity,column structure 100% 保留,**NOT** visual element removal),5 個 missing-data cell `—` placeholder per W22 B-i policy(`kb/page.tsx` `R@5 —%`/`Owner —` precedent);非 H7 deviation,R6 auto-adjust。stat-grid 同理 — 「Total members」+「Pending invites」real,「Active sessions」+「Avg queries / user」value+sub `—`。
- **D10.2 — mockup invite/suspend/role-change render inert**(R6 #4)— mockup `UsersTab`+`PageUsers` lines 62-191「Export CSV」/「Invite member」/ per-row「More」button 無 onClick / modal / menu(click-through prototype affordance)。plan §2 F9.2 text「invite/suspend/role-change」= 呢啲 mockup affordance → F9.2 reproduces them inert per mockup(對齊 `kb/page.tsx` inert More-button)。functional invite-modal / role-dropdown UI **唔喺 mockup** → 不 build(Karpathy §1.2 no speculative + W22 D6 over-extending anti-pattern);`usersApi.inviteUser/suspendUser/changeUserRole` 保持 F9.1-shipped client surface。mockup 清晰,非 STOP+ask。
- **D10.3 — search input wire client-side**(R6 #5)— mockup line 121 search `<input>` 無 value/onChange(prototype inert),seg filter 有 wire。F9.2 wire search client-side(name+email filter)consistent with seg filter(both client-side)+ `kb/page.tsx` search precedent — 令既有 rendered control functional ≠ 加 visual element;placeholder text「Search by name, email, group…」verbatim 重現 per H7(group 非 backend-searchable,但 H7 = verbatim mockup text)。
- **D10.4 — roles/groups/audit tab transient `<TabPlaceholder>`**(R6 #8)— sub-split:F9.3 build Roles+Groups,F9.4 build Audit。F9.2 render 4-tab nav(shell fidelity,mockup 4 tab)+ neutral `<TabPlaceholder>`(同 sprint F9.3/F9.4 replace)。F9.2 H7 self-verify scoped 至 shell + Members tab。
- **D10.5 — tab nav `<button role="tab">` + `?tab=` deep-link**(R6 #6/#7)— mockup 用 `<div className="tab" onClick>` + plain `useState`;`settings/page.tsx` 已 establish `<button role="tab" aria-selected>` a11y + `?tab=` `useSearchParams`+`<Suspense>` deep-link(已 H7-passed)→ F9.2 跟 settings convention;`?tab=` 係 invisible deep-link enhancement,mockup plain `useState` 係 prototype URL-state 簡化 → 非 H7 deviation(D9.5 已預定)。
- **D10.6 — `RoleBadge` 獨立 shared component**(R6 #1)— mockup inline 定義 + `window.RoleBadge` export,Members/Roles/Groups 三 tab consumer → NEW `components/users/role-badge.tsx`(genuine 3-consumer primitive);避免 F9.3 refactor。`TabBoundary` 反之 = local helper(settings 亦 local 定義,extract 去 shared 要改 settings,非 surgical per Karpathy §1.3)。

### Acceptance(plan §2 F9 sub-split F9.2)

- [x] F9.2(a)`components/users/role-badge.tsx` shared `RoleBadge`(3-tab consumer,oklch token colors per mockup lines 193-207)
- [x] F9.2(b)`app/(app)/users/page.tsx` NET NEW route shell + Members tab — `<Suspense>` + page-header + stat-grid 4-card + 4-tab nav `<button role="tab">` + `?tab=` deep-link + local `<TabBoundary>` + inline `UsersTab` + client-side search/seg filter + 10-col table + loading/error/empty/data 四態
- [x] H7 7-item self-verify(layout/spacing/typography/color tokens/interaction states/responsive/a11y)PASS for shell + Members tab — layout/spacing/typography/color 100% mockup-faithful;5 backend-subset column + 2 stat card `—` placeholder per W22 B-i(structure 保留,§13 visual-fidelity);loading/error/empty state 為 real-fetch 必需(mockup static prototype 無);a11y upgrade per settings precedent

### Verify

- **frontend `tsc --noEmit`** — exit 0(type-check clean)
- **frontend `next lint`** — `✔ No ESLint warnings or errors`(`app/(app)/users` + `components/users`)
- **`[oklch` arbitrary-class grep** = **0**(`app/(app)/users` + `components/users` — RoleBadge inline `oklch(...)` style strings 無 `[` prefix,不觸 milestone)
- **backend** — F9.2 純 frontend,無 backend change → backend pytest 不變 908
- **route** — `/users` NET NEW(`app/(app)/users/page.tsx`);endpoint count 不變 58(F9.2 無新 endpoint)
- **runtime browser smoke** — F9.4 Vitest/Playwright + interactive walkthrough = smoke-user-deferred per plan §3

**Day 10 F9.2 Verdict**:F9.2 complete — `/users` route shell + Members tab landed。NEW shared `RoleBadge` + NEW `/users` page(4-tab nav `?tab=` deep-link + stat-grid + Members tab data-bound to `GET /users`)。10 R6 findings resolved + H7 self-verify PASS(shell + Members tab)。tsc/lint/`[oklch`=0 全綠。F9.3 Roles tab + Groups tab next。

---

## Day 11 — 2026-05-21 — F9.3 Roles tab + Groups tab

### Done

- **F9.3 pre-active-flip 5-step grep audit recursive**(per CLAUDE.md §10 R6)— 讀 mockup `ekp-page-users.jsx` lines 209-322(`RolesTab`+`GroupsTab`)+ `backend/storage/rbac_storage.py`(`_PERMISSION_MATRIX`/`_DEFAULT_ROLES` seed + `permission_matrix_rows()` order)+ `lib/api/admin.ts`(`adminApi.getIdentity`/`IdentityConfig`/`RoleMapping`)+ `styles-mockup.css`(`card-body-tight`/`banner-info`/`.col` confirm)→ **10 findings**(plan §7 Day 11 row)
- **F9.3 `app/(app)/users/page.tsx` EDIT** — imports(+`Check`/`RefreshCw` lucide + `Fragment` react + `adminApi`/`EkpRoleKey`/`IdentityConfig` from admin.ts + `Group*`/`Role*`/`RolePermission` types from users.ts)+ 2 tab body swap(`roles`/`groups` `<TabPlaceholder>` → `<RolesTab/>`/`<GroupsTab/>`)
- **NEW inline `RolesTab`** — `banner-info` RBAC banner + 4 role cards(`useQuery(['roles','list'])`;member count client-side from `useQuery(['users','list'])` shared cache per F5 D5.3;`isTier2 = role.tier >= 2` → power card TIER 2 badge + opacity 0.6)+ permissions matrix(`useQuery(['roles','permissions'])` → `pivotMatrix()` flat 92-row `RolePermission[]` → area-grouped per-perm 4-grant;`<Fragment>` per area;`Check`/`—` per cell;Power column opacity 0.6)
- **NEW inline `GroupsTab`** — Entra groups table(`useQuery(['groups','list'])`)+ `EKP role` client-side join(`useQuery(['admin','identity'])` → `roleByGroupId` Map from `RoleMapping.entra_group_id` per F6 D6.3)+ `truncateOid`(first4…last4)+ `formatRelative`(`synced_at`)helpers + empty state(mock-auth dev 常 0 group)
- **NEW helpers** — `pivotMatrix()`/`MatrixArea`/`MATRIX_ROLES`(roles tab)+ `formatRelative`/`truncateOid`(groups tab)
- **F9.3 committed** `(this commit)`

### Decisions

- **D11.1 — permissions matrix client-side pivot**(R6 #2)— F5 D5.4:`GET /roles/permissions` 返回 flat `list[RolePermission]`(92 row,per-cell)。backend `permission_matrix_rows()` order = area → permission → role(`_ROLE_ORDER`),且 `_PERMISSION_MATRIX` seed grep 確認 **verbatim-mirror** mockup `PERMISSIONS_MATRIX` lines 26-60 → frontend `pivotMatrix()` first-seen accumulation(Map by area + `area::permission_key`)即得 mockup area+perm order,**無需** explicit order constant。Karpathy §1.2 — backend canonical per-cell shape lock(F2),frontend pivot 係 presentation concern。
- **D11.2 — RolesTab role metadata 全部 backend-sourced**(R6 #1)— grep `backend/storage/rbac_storage.py` `_DEFAULT_ROLES` 確認 `description` 4 條 verbatim-match mockup `ROLES[].desc`、`label` match `EKP_ROLE_LABELS` → render `role.description` + `<RoleBadge role={role.role_key}>`,**無** hardcoded role metadata constant(避免 mockup `ROLES` const 重複)。`isTier2 = role.tier >= 2`(backend `Role.tier` field,power=2)。
- **D11.3 — GroupsTab `EKP role` client-side join**(R6 #4)— F6 D6.3:`GET /groups` 返回 pure `Group`(無 role mapping)。GroupsTab fetch `adminApi.getIdentity()` → `IdentityConfig.roles.mappings`(`RoleMapping[]`)build `roleByGroupId` Map(key=`entra_group_id`)→ per-group `g.entra_object_id` lookup → `RoleBadge` 或「Not mapped」。`getIdentity()` 係 `require_role("admin")`-gated — fine(`/users` page admin-scoped;F9.4 加 `useRole()` gating)。`tenant_domain` card-desc 亦用 real `identity.tenant.tenant_domain`(非 mockup hardcoded literal)。
- **D11.4 — `Sync from Entra` / `Export` button render inert**(R6 #7)— mockup button presentational(無 onClick)。`POST /groups/sync-from-entra` 返回 `GroupSyncResult{status,detail}`,`status='skipped'` 係 mock-auth dev default(無 Entra tenant)→ 一個 wired button 需 `synced/skipped/502` result-feedback surface 而 mockup 冇 → render inert per mockup + per F9.2 D10.2 precedent(mockup presentational action button → inert;needs surface not in mockup → 不 build per W22 D6 over-extending anti-pattern)。`usersApi.syncGroupsFromEntra()` 保持 F9.1-shipped client surface。
- **D11.5 — RolesTab/GroupsTab inline + self-fetch**(R6 #8)— inline 喺 `page.tsx`(consistent F9.2 `UsersTab` inline + `kb/[id]/page.tsx` 8-tab-inline precedent);各自 `useQuery` self-fetch domain endpoint;RolesTab re-subscribe `['users','list']`(TanStack 同-key dedupe,零額外 request);shell 不 pass 額外 prop。

### Acceptance(plan §2 F9 sub-split F9.3)

- [x] F9.3 `RolesTab` — banner-info + 4 role cards(`GET /roles`,member count client-side,isTier2 TIER 2 badge)+ permissions matrix(`pivotMatrix` flat `GET /roles/permissions` 92-row → area-grouped per-perm 4-grant,backend order = mockup order)per mockup lines 209-286
- [x] F9.3 `GroupsTab` — Entra groups table(`GET /groups`)+ `EKP role` client-side join from `adminApi.getIdentity()` per F6 D6.3 + `truncateOid`/`formatRelative` + empty state per mockup lines 288-322;`Sync from Entra` inert per mockup
- [x] H7 7-item self-verify(layout/spacing/typography/color tokens/interaction states/responsive/a11y)PASS — RolesTab + GroupsTab layout/spacing/typography/color 100% mockup-faithful;loading/error/empty 為 real-fetch 必需;Check icon `aria-label` a11y upgrade

### Verify

- **frontend `tsc --noEmit`** — exit 0(type-check clean)
- **frontend `next lint`** — `✔ No ESLint warnings or errors`(`app/(app)/users` + `components/users`)
- **`[oklch` arbitrary-class grep** = **0**(`app/(app)/users/page.tsx` — matrix area-header / Check / Shield inline `oklch(...)` style strings 無 `[` prefix,不觸 milestone)
- **backend** — F9.3 純 frontend,無 backend change → backend pytest 不變 908;endpoint count 不變 58
- **runtime browser smoke** — F9.4 Vitest/Playwright + interactive walkthrough = smoke-user-deferred per plan §3

**Day 11 F9.3 Verdict**:F9.3 complete — Roles tab + Groups tab landed。`RolesTab`(banner + 4 role cards + pivoted 92-cell permissions matrix)+ `GroupsTab`(Entra groups table + client-side role-mapping join)inline 入 `page.tsx`。10 R6 findings resolved + H7 self-verify PASS(RolesTab + GroupsTab)。tsc/lint/`[oklch`=0 全綠。F9.4 Audit tab + `useRole()` role-gating + H7 全-tab verify + Vitest/Playwright next。

<!-- Day 11+ F9.4 entry lands at sub-split active flip per CLAUDE.md §10 R2 -->
