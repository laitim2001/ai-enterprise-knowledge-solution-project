---
phase: W24c-users-rbac
plan_ref: ./plan.md
status: active
last_updated: 2026-05-21  # F3 active-flip → F3.0-F3.4 complete (role vocab unified + acl.py require_role + AuthenticatedUser.role; backend pytest 839)
---

# W24c-users-rbac — Checklist

> Derived from `plan.md §2 F0-F12 deliverables`。延後項標 🚧 + reason(per CLAUDE.md sacred rule — 唔可以刪未勾 `[ ]`)。
> Large phase(~20 backend days)— F2-F12 sketched at kickoff,acceptance items refine per-deliverable at active-flip + may sub-split per plan §2 + §7 R3。

## F0 — Kickoff cascade

- [x] **F0.1** W24c folder `plan.md`(this folder)+ `checklist.md` + `progress.md` created `status: active` 2026-05-21
- [x] **F0.2** NO `frontend/` or `backend/` code change at kickoff(F0 governance only — per W19-W24b F0 precedent)
- [x] **F0.3** `architecture.md v6 §3.7` amendment deferred to F1(F0 = doc-folder governance only)
- [x] **F0.4** Pre-active-flip 5-step grep audit recursive(per CLAUDE.md §10 R6)completed,documented `progress.md` Day 0 + plan §7:`ekp-page-users.jsx` exists / `backend/api/auth/{users_store,postgres_users_store,users_repo}.py` exist / `backend/api/middleware/` has audit_log+rate_limit(NEW acl.py needed)/ **`audit_log` table ALREADY EXISTS** → ADR-0027「6 NEW tables」實際 5 NEW / `frontend/app/(app)/users/` does NOT exist(NET NEW route)
- [x] **F0.5** W24c kickoff cascade committed `(this commit)`

## F1 — Spec amendment + Entra Graph approach + C16/C11 decision

> R6 finding(plan §7 Day 1):**(a)** ADR-0027「amend §3.7 + add §3.8」§-pointer 錯(§3.7 = C13 Email Verification)→ amendment 落 **§5** inline block per ADR-0024/0025/0026 convention;**(b)** Entra Graph SDK fork → Chris pick **managed-REST**(`azure-identity`+`httpx` W24-c1 已裝)→ F1.4 install no-op;**(c)** C16 vs C11 → pick **C16 NEW Users Service**。

- [x] **F1.1** `architecture.md v6 §5.0` inline-tagged `> **Amendment(/users Tier 1.5 RBAC + Access tab activation)**` block(R6-corrected from ADR-0027 §3.7 → §5;doc version held;ADR-0027 authoritative)— RBAC「Tier 2 hook」→「Tier 1.5 minimum」
- [x] **F1.2** `/users` 4-tab + per-KB ACL + Access-tab-activation reference 入同一 §5 amendment block(R6-corrected from「NEW §3.8」— `/users` 屬 UI view → §5)
- [x] **F1.3** C16 vs C11 decision — pick **C16 NEW Users Service**(authorization concern distinct from C11 authentication;~20 backend days weight)logged plan §7 Day 1 + `COMPONENT_CATALOG.md` C16 card landed
- [x] **F1.4** Entra Graph approach — **managed-REST**(Chris AskUserQuestion 2026-05-21):既有 `azure-identity` token + `httpx` `GET graph.microsoft.com/v1.0/groups`;**no `msgraph-sdk` install**(零新 dep / 零 H2 / 零 R8 — per ADR-0017「managed-REST > heavy SDK」)→ F1.4 install no-op
- [x] **F1.5** `backend/pyproject.toml` — **no change**(`azure-identity>=1.20` + `httpx>=0.27` W24-c1 已存在);F1 無 backend code change(`entra_graph.py` managed-REST module 落 F6 — mypy 屆時 verify)

## F2 — RBAC schema layer(5 NEW Postgres tables + storage)

> R6 Day 2 finding(plan §7):**(1)** PERMISSIONS_MATRIX 實際 = **23** permissions 非 24(plan-text contamination)→ F2.4「24→23」;**(2)** F2.2「column ADD」需同步 `UserRecord.role` + `PostgresUsersStore` 4 處否則 dead schema;**(3)** F2 Protocol 只暴露 `roles`+`role_permissions`,`groups`/`group_members`/`kb_acl` table declared-ahead 但 Protocol method 留 F6/F8。

- [x] **F2.1** 5 NEW Postgres tables(`roles` + `role_permissions` + `groups` + `group_members` + `kb_acl`)idempotent `CREATE TABLE IF NOT EXISTS` — `rbac_postgres.py` `_CREATE_TABLES` 一次建 5 table；`roles`+`role_permissions` 有 `sort_order` column 供 `ORDER BY`
- [x] **F2.2** `users.role` column ADD(default `'user'`,additive migration)— `postgres_users_store.py` `users` CREATE 加 `role` + `ALTER TABLE … ADD COLUMN IF NOT EXISTS` + `_USER_COLS`/`_row_to_user`/`add_user`/`replace_user` 同步 + `UserRecord.role: str = "user"` field
- [x] **F2.3** RBAC storage Protocol + InMemory + Postgres impls + factory(lazy-import per ADR-0023)— `RbacBackend` async Protocol + `InMemoryRbacBackend` + `PostgresRbacBackend` + `make_rbac_backend`
- [x] **F2.4** Seed:3 active roles(Admin / Editor / End User)+ Power User Tier 2 `active=False` disabled + PERMISSIONS_MATRIX 5 areas × **23** permissions per mockup `ekp-page-users.jsx` lines 26-60(R6 finding #1:plan「24」→ actual 23)— `seed_defaults` idempotent → 4 roles + 92 role_permission rows

## F3 — ACL middleware + auth-time role claim

> R6 Day 3 finding(plan §7,5 findings):**(1)** `AuthenticatedUser` 無 `role` field → server-side resolve 非 cookie-carried;**(2)** `@requires_*`「decorator」→ FastAPI `Depends()` factory;**(3)** `require_kb_acl` defer F8(連 `kb_acl` storage method);**(4)** F3.4「every endpoint」→ F3 = mechanism + 403 test,per-endpoint apply F4-F10;**(5)** role key vocabulary 衝突 → Chris pick「統一 short」→ NEW F3.0。

- [x] **F3.0** role key vocabulary 統一(R6 #5 — Chris AskUserQuestion 2026-05-21「short form」)— W24-c1 `admin_identity` long-form → RBAC-core short,9 files(backend `admin_identity.py` import `rbac.RoleKey` / `identity.py` / `admin_identity_storage.py` seed / `test_admin_identity.py`;frontend `admin.ts` `EkpRoleKey` + NEW `EKP_ROLE_LABELS` / `identity.ts` `ekpRoleKeySchema` / `settings-identity.tsx` 顯示改 label map 修 H7 drift / `settings-6tab.test` + `settings-identity-form.test` mock 改 `importOriginal`)
- [x] **F3.1** `backend/api/middleware/acl.py` NEW — `require_role(*roles)` FastAPI dependency factory(R6 #2 — `Depends()` 非 Python decorator);**`@requires_kb_acl` 🚧 deferred F8** — 連 `kb_acl` storage method 一齊(R6 #3 — Karpathy §1.2 no stub-only)
- [x] **F3.2** auth-time role claim — `AuthenticatedUser.role` field + 三路徑 server-side resolve(R6 #1 — self-register `UserRecord.role` / mock `Settings.auth_mock_role` / MSAL app-role claim;role 非真存 session/cookie)
- [x] **F3.3** mock-auth `Settings.auth_mock_role` default `admin`;real-MSAL `_role_from_claims`(Entra app-role claim,Tier-1-grantable `{admin,editor,user}`,`power` downgrade per H4)
- [x] **F3.4** `require_role` 403-on-unauthorized contract test-verified(`test_acl_middleware.py` 11 cases);**per-endpoint apply 🚧 F4-F10 inline** — R6 #4 + plan §4 R-W24c-3「opt-in per endpoint」,F3 交付 mechanism

## F4 — `/users` Members tab backend

- [ ] **F4.1** `GET /users` list + filter seg(all/admin/editor/user/pending)
- [ ] **F4.2** `POST /users/invite` + `POST /users/{id}/suspend` + `PATCH /users/{id}/role`
- [ ] **F4.3** audit_log writes on Members mutations

## F5 — `/users` Roles tab backend

- [ ] **F5.1** `GET /roles` 4 role cards(3 active + Power User Tier 2 disabled)
- [ ] **F5.2** permissions matrix endpoint(read — custom roles Tier 2 per H4)

## F6 — `/users` Groups tab backend + sync-from-entra

- [ ] **F6.1** `GET /groups` + `group_members`
- [ ] **F6.2** `POST /groups/sync-from-entra`(Entra Graph SDK call;graceful fallback when Entra config unset)

## F7 — Audit log expansion

- [ ] **F7.1** `AuditAction` Literal extended with RBAC action types(`role.changed` / `user.invited` / `kb.access.granted` / `kb.config.changed` / `user.suspended`)
- [ ] **F7.2** audit_log writes wired on protected-endpoint mutations + 90d retention policy

## F8 — per-KB ACL(`kb_acl`)

- [ ] **F8.1** `kb_acl` CRUD endpoints(Manage/Edit/Query role override + add member + add Entra group)
- [ ] **F8.2** ACL middleware consults `kb_acl` for per-KB authorization

## F9 — frontend `/users` 4-tab page + `useRole()` hook

- [ ] **F9.1** `/users` NET NEW route 4 tabs(Members / Roles / Groups / Audit log)per mockup `ekp-page-users.jsx`
- [ ] **F9.2** `useRole()` hook + role-gated view rendering
- [ ] **F9.3** H7 per-tab fidelity verify

## F10 — frontend `/kb/[id]` Access tab activation

- [ ] **F10.1** `/kb/[id]` 8th tab Access activated(disabled affordance removed per ADR-0025)
- [ ] **F10.2** `<TabKbAccess>` per-KB ACL UI per mockup lines 390-519 + H7 fidelity verify

## F11 — Tests

- [ ] **F11.1** backend pytest — RBAC storage + ACL middleware(≥80% per H6)+ endpoints
- [ ] **F11.2** Vitest — `/users` tabs + `useRole()` hook
- [ ] **F11.3** Playwright — `/users` render-smoke + Access tab
- [ ] **F11.4** verify gates — `tsc` exit 0 + `next lint` clean + `[oklch`=0 + `mypy --strict` RBAC modules

## F12 — Closeout cascade

- [ ] **F12.1** Phase Gate verdict published per `progress.md` retro
- [ ] **F12.2** 7-section retro per F-deliverable
- [ ] **F12.3** plan/checklist/progress frontmatter `active → closed`
- [ ] **F12.4** W24d+ candidates noted in retro **NOT pre-created** per CLAUDE.md §10 R1
- [ ] **F12.5** `session-start.md` 6 places synced
- [ ] **F12.6** `COMPONENT_CATALOG.md` C16/C11/C08/C02 W24c amendments
- [ ] **F12.7** `PAGE_INVENTORY.md` row 12 `/users` + `/kb/[id]` Access tab status amendments
- [ ] **F12.8** ADR-0027 + ADR-0025 Implementation Status section amendments

---

**Lifecycle reminder**:新加 acceptance item 必先入 `plan.md §2 F-deliverables`,然後再加 checklist。延後項標 🚧 + reason,唔可以刪。F2-F12 acceptance items 係 kickoff sketch — active-flip refine 時新增 detail item 先入 plan §2 再入 checklist。
