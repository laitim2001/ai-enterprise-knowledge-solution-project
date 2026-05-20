---
phase: W24c-users-rbac
plan_ref: ./plan.md
status: active
last_updated: 2026-05-21  # F0 kickoff cascade landed
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

## F1 — Spec amendment + Entra Graph SDK install + C16/C11 decision

- [ ] **F1.1** `architecture.md v6 §3.7` inline-tagged amendment — RBAC「Tier 2 hook」→「Tier 1.5 minimum」per ADR-0027(doc version held)
- [ ] **F1.2** NEW `architecture.md v6 §3.8 /users page` reference paragraph inline-tagged
- [ ] **F1.3** C16 Users Service vs C11 expansion decision logged plan §7 + `COMPONENT_CATALOG.md` updated
- [ ] **F1.4** Entra Graph SDK install — Plan B (a) `pip install` → 若 R8 fail Plan B (c) mobile hotspot + ADR-0017 amendment occurrence #9
- [ ] **F1.5** `backend/pyproject.toml` + lock confirm;`mypy --strict` clean import site;lazy-import per ADR-0023

## F2 — RBAC schema layer(5 NEW Postgres tables + storage)

- [ ] **F2.1** 5 NEW Postgres tables(`roles` + `role_permissions` + `groups` + `group_members` + `kb_acl`)idempotent `CREATE TABLE IF NOT EXISTS`
- [ ] **F2.2** `users.role` column ADD(default `'user'`,additive migration)
- [ ] **F2.3** RBAC storage Protocol + InMemory + Postgres impls + factory(lazy-import per ADR-0023)
- [ ] **F2.4** Seed:3 active roles(Admin / Editor / End User)+ Power User Tier 2 disabled + PERMISSIONS_MATRIX 5 areas × 24 permissions per mockup lines 26-60

## F3 — ACL middleware + auth-time role claim

- [ ] **F3.1** `backend/api/middleware/acl.py` NEW — `@requires_role` / `@requires_kb_acl` decorators
- [ ] **F3.2** auth-time role claim — role carried in session/cookie
- [ ] **F3.3** mock-auth provider returns `role:'admin'`;real-MSAL Entra group → role session callback
- [ ] **F3.4** every protected endpoint role-checked;403 on unauthorized

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
