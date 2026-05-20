---
phase: W24c-users-rbac
name: "/users Tier 1.5 RBAC — full RBAC per ADR-0027 Option A (Members + Roles + Groups + Audit log + per-KB ACL)"
sprint_week: W24c
start_date: 2026-05-21              # real-calendar — Chris directive 2026-05-21 「Kickoff W24c — /users RBAC」(AskUserQuestion pick)
end_date: 2026-05-30                # ~10-14 plan-day window;~20 backend days compressed by W19-W24 real-calendar collapse (~1.5-12× pattern)
status: active
spec_refs:
  - ADR-0027                        # Option A full RBAC — Accepted W19 F6 Chris pick
  - ADR-0025                        # /kb/[id] Access tab — hard dep on RBAC infra (disabled affordance → active at W24c)
  - ADR-0026                        # Settings Identity & Auth role mapping reads the same role/permission matrix
  - ADR-0023                        # Postgres persistent backing — users table + PostgresUsersStore already exist
  - ADR-0014                        # hybrid auth — Entra ID group → role mapping concept
  - ADR-0017                        # R8 corp-proxy mitigation — Entra Graph SDK new dep (H2) install discipline
  - CLAUDE.md §5.1 H1               # RBAC Tier 2 hook → Tier 1.5 = architectural change (ADR-0027 covers it)
  - CLAUDE.md §5.2 H2               # Entra Graph SDK NEW dependency — pre-cleared via ADR-0027 acceptance
  - CLAUDE.md §5.4 H4               # Tier boundary — Power User role + custom roles stay Tier 2 (disabled affordance)
  - CLAUDE.md §10 R1-R6             # rolling JIT + plan-before-code + R6 pre-active-flip recursive grep audit
prior_phase: W24b-frontend-wave-c2-settings-depth   # closed 2026-05-20 PASS WITH SMOKE-USER-DEFERRED CAVEAT
related_artifacts:
  - docs/adr/0027-users-tier-1-5-rbac.md            # primary ADR — Option A full RBAC
  - docs/adr/0025-kb-detail-8-tab.md                # Access tab dep
  - references/design-mockups/ekp-page-users.jsx    # canonical visual spec — PageUsers 4 tabs + TabKbAccess
  - backend/api/auth/users_store.py                 # existing users store — role column ADD
  - backend/api/auth/postgres_users_store.py        # PostgresUsersStore per ADR-0023
  - backend/api/middleware/                         # audit_log.py + rate_limit.py exist — ACL middleware NEW
  - backend/storage/audit_log_storage.py            # audit_log table ALREADY EXISTS (W24-c1 F4) — W24c EXTENDS it
---

# Phase W24c — /users Tier 1.5 RBAC Plan

> **Authorization**:Chris directive 2026-05-21「**Kickoff W24c — /users RBAC**」(AskUserQuestion pick post-W24b closeout)+ ADR-0027 **Accepted Option A full RBAC**(W19 F6 Chris pick — Option A over the W19 F2 §6 Option B minimal recommendation)。
>
> **Wave lineage**:W19 F4 §3.6 SPLIT — Wave C(ADR-0026 + ADR-0027 combined ~42 backend days)split into sub-phases。Wave C1 = ADR-0026 Settings 6-tab backend + read-mostly frontend(W24)。Wave C2 = ADR-0026 Settings depth inline-edit(W24b)。**Wave C3 = ADR-0027 `/users` Tier 1.5 RBAC = W24c**(this phase)— the remaining Wave C work。
>
> **Scope weight**:per ADR-0027 Option A ~**20 backend days** — the largest single phase in the W-series。5 NEW Postgres tables(`audit_log` 已存在 W24-c1 — 見 R6 finding §7 Day 0)+ ACL middleware on every protected endpoint + Entra Graph SDK new dependency + NEW `/users` 4-tab route + `/kb/[id]` Access tab activation per ADR-0025 + NEW C16 Users Service component(or C11 expansion — F1 decision)。

---

## §0 Phase identity

**Trigger**:W24b-wave-c2 closeout 2026-05-20 + Chris W24c kickoff directive 2026-05-21 + ADR-0027 Accepted Option A(W19 F6)。

**Decision authority**:Chris W19 F6 ADR-0027 Accepted **Option A full RBAC**(explicitly over Option B minimal recommendation)+ W24c kickoff pick 2026-05-21。

**Scope**(ADR-0027 Option A):
- F0 Kickoff cascade(plan + checklist + progress)
- F1 `architecture.md v6 §3.7` amendment(RBAC Tier 2 hook → Tier 1.5 minimum)+ NEW §3.8 `/users` reference + Entra Graph SDK install(H2 pre-cleared / ADR-0017 Plan B)+ C16 Users Service vs C11 expansion decision
- F2 RBAC schema layer — 5 NEW Postgres tables(`roles` + `role_permissions` + `groups` + `group_members` + `kb_acl`)+ storage Protocol/InMemory/Postgres + role/permission seed(3 active roles + Power User Tier 2 + PERMISSIONS_MATRIX 5 areas × 24 permissions)
- F3 ACL middleware + auth-time role claim(role carried in session/cookie)+ mock-auth `role:'admin'` + real-MSAL Entra group → role extraction
- F4 `/users` Members tab backend(list + filter + invite + suspend + role-change endpoints)
- F5 `/users` Roles tab backend(role cards + permissions matrix endpoints)
- F6 `/users` Groups tab backend + `POST /groups/sync-from-entra`(Entra Graph SDK)
- F7 Audit log expansion — new action types(role.changed / user.invited / kb.access.granted / kb.config.changed / user.suspended)+ writes on protected endpoints + 90d retention
- F8 per-KB ACL — `kb_acl` table CRUD + Manage/Edit/Query role override + add member + add Entra group(TabKbAccess backend)
- F9 frontend `/users` 4-tab page(Members / Roles / Groups / Audit log)+ `useRole()` hook + role-gated view rendering
- F10 frontend `/kb/[id]` Access tab activation(disabled affordance → active)+ `<TabKbAccess>` per ADR-0025
- F11 Tests(backend pytest ≥80% on ACL/RBAC modules per H6 + Vitest + Playwright)
- F12 Closeout cascade(retro + Gate + session-start sync + ADR-0027 + ADR-0025 Implementation Status)

**Out of scope**(Tier 2 per ADR-0027 §Consequences + H4):
- Custom role creation(PERMISSIONS_MATRIX stays hard-coded static admin policy)
- Power User role activation(4th matrix column visible but disabled per H4)
- Multi-tenancy / tenant-scoped RBAC(Tier 2)
- Real-MSAL feature flag operational verification(W16 Track A IT cred parallel track,Q11 operational early June 2026 — mock-auth default continues per user 岔口 2)

**Authorities**:
- **ADR-0027** Status `Accepted (Option A full RBAC)` → W24c closeout amends to `Accepted + implemented`
- **ADR-0025** Access tab disabled affordance → activated at W24c F10
- **CLAUDE.md §5.1 H1** — RBAC promotion Tier 2 hook → Tier 1.5 is architectural;ADR-0027 covers it;F1 amends `architecture.md v6 §3.7`
- **CLAUDE.md §5.2 H2** — Entra Graph SDK NEW dep — pre-cleared via ADR-0027 acceptance(W19 F6 noted「Entra Graph SDK new dependency H2 trigger」);F1 install per ADR-0017 Plan B sequencing
- **CLAUDE.md §5.4 H4** — Power User + custom roles stay Tier 2(disabled affordance,not implemented)
- **CLAUDE.md §10 R1-R6** — rolling JIT;R6 pre-active-flip 5-step recursive grep audit(plan-text + code)per F-deliverable

---

## §1 Authorization + spec refs

| F-deliverable | Authorization | Spec ref |
|---|---|---|
| F0 Kickoff | this plan + Chris kickoff directive 2026-05-21 | CLAUDE.md §10 R1 + R5 + ADR-0027 §References |
| F1 Spec amendment + Entra Graph SDK | ADR-0027 §Decision + CLAUDE.md §5.1 H1 + §5.2 H2 + ADR-0017 | `architecture.md v6 §3.7`+NEW§3.8 inline-tag + `backend/pyproject.toml` Entra Graph SDK |
| F2 RBAC schema | ADR-0027 §Decision Option A 6-table(`audit_log` 已存在 → 5 NEW)| `backend/storage/` NEW rbac storage 3-file split per ADR-0023 pattern |
| F3 ACL middleware | ADR-0027 §Decision Option A ACL + ADR-0014 role claim | `backend/api/middleware/` NEW `acl.py` |
| F4 Members backend | ADR-0027 §Context Members tab | `backend/api/routes/users/` NEW router |
| F5 Roles backend | ADR-0027 §Context Roles tab + PERMISSIONS_MATRIX | `backend/api/routes/users/` roles endpoints |
| F6 Groups backend | ADR-0027 §Context Groups tab + Entra Graph SDK | `POST /groups/sync-from-entra` |
| F7 Audit log expansion | ADR-0027 §Context Audit log tab 6 action types | `backend/storage/audit_log_storage.py` extend(W24c F6 precedent — additive)|
| F8 per-KB ACL | ADR-0027 §Decision `kb_acl` + ADR-0025 Access tab | `kb_acl` table + per-KB ACL CRUD |
| F9 frontend /users | ADR-0027 §Context 4 tabs + mockup `ekp-page-users.jsx` | `frontend/app/(app)/users/` NEW route |
| F10 frontend Access tab | ADR-0025 Access tab + ADR-0027 TabKbAccess | `frontend/` KB detail Access tab activate |
| F11 Tests | CLAUDE.md §5.6 H6(ACL/RBAC ≥80%)+ W23-W24b test pattern | pytest + Vitest + Playwright |
| F12 Closeout | CLAUDE.md §10 R3 + W19-W24b closeout pattern | retro + ADR-0027 + ADR-0025 Implementation Status |

---

## §2 F0-F12 deliverables

**Rolling JIT discipline**:F0 + F1 detailed at kickoff;F2-F12 sketched — detail refines per-deliverable at active-flip per W12-W24b pattern。Per CLAUDE.md §10 R6 — pre-active-flip 5-step grep audit applied **recursively** to plan-text **and** code-at-active-flip-time。**F-deliverables may sub-split at active-flip** per actual scope(~20 backend days = large;e.g. F4 Members / F5 Roles may each sub-split)— logged in §7 changelog per R3。

### F0 — Kickoff cascade(landed at phase open — `(this commit)`)

- **Component(s)**:governance(no Cn touched at F0)
- **Spec ref**:CLAUDE.md §10 R1 + this plan §0
- **OQ deps**:Q11(Entra ID tenant — Resolved decision-level;operational early June 2026 — non-blocking,mock-auth default per user 岔口 2)
- **Acceptance criteria**:
  - F0.1 W24c folder `plan.md`(this file)+ `checklist.md` + `progress.md` created `status: active` 2026-05-21
  - F0.2 NO `frontend/` or `backend/` code change at kickoff(F0 governance only — per W19-W24b F0 precedent)
  - F0.3 `architecture.md v6 §3.7` amendment deferred to F1(not F0 — F0 is doc-folder governance only)
  - F0.4 Pre-active-flip 5-step grep audit recursive(per R6)completed at kickoff prep(documented in `progress.md` Day 0 + plan §7 changelog):
    - `references/design-mockups/ekp-page-users.jsx` confirmed exists(`PageUsers` 4 tabs + `TabKbAccess`)
    - `backend/api/auth/{users_store,postgres_users_store,users_repo}.py` confirmed — `users` table per ADR-0023 exists,`role` column ADD needed
    - `backend/api/middleware/` has `audit_log.py` + `rate_limit.py` — NEW `acl.py` needed
    - **`audit_log` Postgres table ALREADY EXISTS**(W24-c1 F4 + W24b F6 filter)→ ADR-0027「6 NEW tables」實際 = **5 NEW**(`roles` + `role_permissions` + `groups` + `group_members` + `kb_acl`);`audit_log` 係 EXTEND not CREATE
    - `frontend/app/(app)/users/` does NOT exist — `/users` route is NET NEW per ADR-0027
  - F0.5 W24c kickoff cascade committed `(this commit)`
- **Effort estimate**:0.25 day(this commit)

### F1 — Spec amendment + Entra Graph SDK install + C16/C11 decision

- **Component(s)**:**C11** Identity & Access(or NEW **C16** Users Service — F1 decision)+ **C12** DevOps & Infra(Entra Graph SDK dep)
- **Spec ref**:
  - ADR-0027 §Decision「Amend `architecture.md v6 §3.7` to promote RBAC from Tier 2 hook to Tier 1.5 minimum + add §3.8 /users page reference」
  - CLAUDE.md §5.2 H2 — Entra Graph SDK NEW dep(`msgraph-sdk` or `azure-identity` Graph scope)— **pre-cleared via ADR-0027 acceptance**(W19 F6);install per ADR-0017 §Decision-rule #5 Plan B sequencing
  - ADR-0027 §Decision Option A「New Cn:C16 Users Service(or fold into C11 Identity & Access expansion)」— F1 strategic decision
- **OQ deps**:none
- **Acceptance criteria**:
  - F1.1 `architecture.md v6 §3.7` inline-tagged amendment — RBAC「Tier 2 hook」→「Tier 1.5 minimum」per ADR-0027(doc version held — same convention as ADR-0024/0023/0022/0026 inline-tag)
  - F1.2 NEW `architecture.md v6 §3.8 /users page` reference paragraph(4 tabs + per-KB ACL)inline-tagged
  - F1.3 **C16 vs C11 decision** — Option A ~20 days + 5 tables + ACL middleware + Entra Graph SDK weight evaluated;decision logged plan §7 + `COMPONENT_CATALOG.md` updated(NEW C16 Users Service card OR C11 scope-expansion note)
  - F1.4 Entra Graph SDK install — Plan B (a) `pip install` attempt;若 R8 fail → Plan B (c) mobile hotspot(precedent:W24-c1 Key Vault SDK + Langfuse)+ ADR-0017 amendment occurrence #9
  - F1.5 `backend/pyproject.toml` + lock confirm SDK landed;`mypy --strict` clean on the import site;lazy-import per ADR-0023(unset Entra config never touches SDK — Graph SDK only loaded on `sync-from-entra`)
- **Effort estimate**:1 day(0.5 spec amendment + 0.25 SDK install + 0.25 C16/C11 decision)

### F2 — RBAC schema layer(5 NEW Postgres tables + storage)

- **Component(s)**:C16/C11 + **C08** API Gateway(schema)
- **Spec ref**:ADR-0027 §Decision Option A — `roles` + `role_permissions` + `groups` + `group_members` + `kb_acl`(5 NEW;`audit_log` already exists)+ ADR-0023 storage Protocol/InMemory/Postgres 3-file split pattern
- **OQ deps**:none
- **Acceptance criteria(sketch — refine at active-flip)**:
  - 5 NEW Postgres tables idempotent `CREATE TABLE IF NOT EXISTS`;`users.role` column ADD(default `'user'`)
  - RBAC storage Protocol + InMemory + Postgres impls + factory(lazy-import per ADR-0023)
  - Seed:3 active roles(Admin / Editor / End User)+ Power User(Tier 2 disabled)+ PERMISSIONS_MATRIX(5 areas × 24 permissions per mockup `ekp-page-users.jsx` lines 26-60)
- **Effort estimate**:~4 days

### F3 — ACL middleware + auth-time role claim

- **Component(s)**:**C08** API Gateway + **C11** Identity & Access
- **Spec ref**:ADR-0027 §Decision Option A「ACL middleware(every protected endpoint checks role + KB ACL)+ auth-time role claim」+ ADR-0014 role-from-Entra-group + §Consequences「mock provider returns role:'admin';real MSAL extracts role from group membership」
- **OQ deps**:Q11(non-blocking — mock-auth default)
- **Acceptance criteria(sketch)**:`acl.py` middleware;role in session/cookie;`@requires_role` / `@requires_kb_acl` decorators;mock-auth `role:'admin'`;real-MSAL group→role session callback
- **Effort estimate**:~3 days

### F4 — `/users` Members tab backend

- **Component(s)**:C16/C11 + C08
- **Spec ref**:ADR-0027 §Context Members tab(11 mock users + filter seg + 10-col table + invite/suspend/role-change)
- **Acceptance criteria(sketch)**:`GET /users` list + filter + `POST /users/invite` + `POST /users/{id}/suspend` + `PATCH /users/{id}/role`;audit_log writes
- **Effort estimate**:~3 days

### F5 — `/users` Roles tab backend

- **Component(s)**:C16/C11 + C08
- **Spec ref**:ADR-0027 §Context Roles tab(4 role cards + permissions matrix)
- **Acceptance criteria(sketch)**:`GET /roles` + permissions matrix endpoint(read — custom roles Tier 2 per H4)
- **Effort estimate**:~2 days

### F6 — `/users` Groups tab backend + sync-from-entra

- **Component(s)**:C16/C11 + C08 + C12(Entra Graph SDK)
- **Spec ref**:ADR-0027 §Context Groups tab + §Decision `POST /groups/sync-from-entra`
- **Acceptance criteria(sketch)**:`GET /groups` + `group_members` + `POST /groups/sync-from-entra`(Entra Graph SDK call;graceful fallback when Entra config unset — mock-auth dev)
- **Effort estimate**:~2.5 days

### F7 — Audit log expansion

- **Component(s)**:C08 + C16/C11
- **Spec ref**:ADR-0027 §Context Audit log tab(6 action types + 90d retention)— EXTENDS the existing `audit_log` table(W24-c1 F4 + W24b F6 filter/pagination)
- **Acceptance criteria(sketch)**:`AuditAction` Literal extended with RBAC action types(`role.changed` / `user.invited` / `kb.access.granted` / `kb.config.changed` / `user.suspended`)+ writes wired on protected endpoints + 90d retention policy
- **Effort estimate**:~2 days

### F8 — per-KB ACL(`kb_acl`)

- **Component(s)**:C16/C11 + C02 KB Manager + C08
- **Spec ref**:ADR-0027 §Decision `kb_acl` table + ADR-0025 Access tab(Manage/Edit/Query role override + add member + add Entra group)
- **Acceptance criteria(sketch)**:`kb_acl` CRUD endpoints;ACL middleware consults `kb_acl` for per-KB authorization
- **Effort estimate**:~2.5 days

### F9 — frontend `/users` 4-tab page + `useRole()` hook

- **Component(s)**:**C09** Admin Console UI + C11
- **Spec ref**:ADR-0027 §Context 4 tabs + mockup `ekp-page-users.jsx` PageUsers;CLAUDE.md §5.7 H7 — 100% mockup fidelity
- **Acceptance criteria(sketch)**:`/users` NET NEW route 4 tabs(Members / Roles / Groups / Audit log)+ `useRole()` hook + role-gated view rendering;H7 per-tab fidelity verify
- **Effort estimate**:~3 days

### F10 — frontend `/kb/[id]` Access tab activation

- **Component(s)**:C09 + C02
- **Spec ref**:ADR-0025 Access tab(disabled affordance Wave A → active W24c)+ ADR-0027 `TabKbAccess`(mockup lines 390-519)
- **Acceptance criteria(sketch)**:`/kb/[id]` 8th tab Access activated(disabled affordance removed)+ `<TabKbAccess>` per-KB ACL UI;H7 fidelity verify
- **Effort estimate**:~1.5 days

### F11 — Tests

- **Component(s)**:all touched
- **Spec ref**:CLAUDE.md §5.6 H6 — ACL/RBAC backend modules ≥80% coverage(`acl.py` middleware is protected-endpoint-critical)
- **Acceptance criteria(sketch)**:backend pytest(RBAC storage + ACL middleware + endpoints)+ Vitest(`/users` tabs + `useRole`)+ Playwright(`/users` render-smoke + Access tab)
- **Effort estimate**:~2 days

### F12 — Closeout cascade

- **Component(s)**:governance
- **Spec ref**:CLAUDE.md §10 R3 + W19-W24b closeout pattern
- **Acceptance criteria(sketch)**:Phase Gate verdict + 7-section retro + frontmatter `active→closed` + session-start.md 6 places + COMPONENT_CATALOG C16/C11/C08/C02 + PAGE_INVENTORY `/users` row 12 + `/kb/[id]` Access tab + ADR-0027 + ADR-0025 Implementation Status + W24d+ NOT pre-created
- **Effort estimate**:0.5 day

---

## §3 Success criteria + Gate criteria

Phase Gate **PASS** requires:

1. **All F0-F12 `[x]` complete**(~70+ atomic items — large phase)
2. **Entra Graph SDK landed**(Plan B (a) or (c)fallback per ADR-0017)
3. **5 NEW Postgres tables** + `users.role` column — idempotent migration,InMemory fallback
4. **ACL middleware working** — every protected endpoint role-checked;mock-auth `role:'admin'`;403 on unauthorized
5. **`/users` 4 tabs working** — Members(list+invite+suspend+role-change)+ Roles(matrix)+ Groups(sync)+ Audit log(feed)
6. **per-KB ACL working** — `kb_acl` CRUD + `/kb/[id]` Access tab activated per ADR-0025
7. **Audit log writes** — RBAC action types written on protected-endpoint mutations
8. **H7 fidelity preserved** — `/users` 4 tabs + Access tab 100% mockup-faithful per `ekp-page-users.jsx`
9. **H4 boundary** — Power User role + custom roles disabled affordance(NOT implemented)
10. **No regression** — backend pytest(W24b baseline 816)+ Vitest + verify gates(`tsc` / `lint` / `[oklch`=0 / `mypy --strict` on RBAC modules ≥80%)

**PARTIAL PASS allowance**:
- Entra Graph SDK R8 install fail through Plan B (c) → PARTIAL PASS + F6 `sync-from-entra` ship as graceful-degraded stub + F6 Entra-bound runtime smoke defer(CO17 umbrella precedent — W24-c1 Key Vault pattern)
- Real-MSAL role extraction runtime verify = user pre-Beta smoke(mock-auth default per user 岔口 2)— same smoke-user-deferred pattern as W18/W20/W24-c1/W24b
- F-deliverable scope explosion → sub-split per R3 changelog,not scope-cut

---

## §4 Risks

| Risk | Mitigation | Status |
|---|---|---|
| **R-W24c-1** Entra Graph SDK R8 install fail | Plan B (c) mobile hotspot per ADR-0017(3 realized precedents:Playwright / Azurite / Langfuse / Key Vault)+ amendment occurrence #9 | 🟡 active |
| **R-W24c-2** ~20 backend days = largest W-series phase,scope explosion | Rolling JIT F-deliverable sub-split at active-flip per R3;F0+F1 detailed,F2-F12 sketched | 🟡 active |
| **R-W24c-3** ACL middleware on every protected endpoint = broad blast radius | H6 ≥80% coverage on `acl.py`;additive `@requires_role` decorator(opt-in per endpoint,no silent global gate);mock-auth `role:'admin'` keeps dev unblocked | 🟡 active |
| **R-W24c-4** `audit_log` table double-ownership(W24-c1 ADR-0026 + W24c ADR-0027) | F7 EXTENDS the existing table additively(`AuditAction` Literal append)— no schema break;W24b F6 filter/pagination preserved | 🟢 mitigated |
| **R-W24c-5** H7 fidelity drift on NET NEW `/users` 4-tab surface | Per-tab H7 7-item self-verify + user-eye verify per F9;mockup `ekp-page-users.jsx` line-ref alignment | 🟡 active |
| **R-W24c-6** real-MSAL role extraction untestable without Track A IT cred | mock-auth `role:'admin'` default(per user 岔口 2);real-MSAL runtime verify = user pre-Beta smoke | 🟢 mitigated |
| **R8 corp-proxy** | Plan B (a) attempt + Plan B (c) hotspot fallback per ADR-0017 | 🟢 mitigated |

---

## §5 Component-Catalog references

| Cn | Touch | Scope |
|---|---|---|
| **C16** Users Service(NEW — or C11 expansion,F1 decision)| RBAC core | F2-F8 RBAC schema + ACL + Members/Roles/Groups/Audit/per-KB ACL |
| **C11** Identity & Access | role claim + ACL | F1 spec amendment + F3 auth-time role claim;C16 host decision F1.3 |
| **C08** API Gateway | NEW `/users/*` + `/groups/*` + `kb_acl` routes + ACL middleware | F3-F8 endpoints |
| **C09** Admin Console UI | NEW `/users` 4-tab route + Access tab | F9 + F10 |
| **C02** KB Manager | per-KB ACL consumer | F8 `kb_acl` + F10 Access tab |
| **C12** DevOps & Infra | Entra Graph SDK NEW dep | F1 install |
| **C01/C03-C07/C10/C13** | _no touch_ | preserved unchanged |

---

## §6 Carry-overs to W24d+ / rolling JIT

- **W24d+ candidates**(per W24c retro):
  - Tier 2 RBAC expansion(custom roles + Power User activation + multi-tenancy)— Q12 post-Beta governance
  - Connections deployment cap edit(Wave B+ Azure portal authoritative)
  - real-MSAL feature flag operational verification + W16 F1-F4 Track A IT cred(parallel track,Q11 early June 2026)
  - `PAGE_INVENTORY.md` row 6 `/doc-detail` staleness doc-sync(W24b F8 R6 finding carry-over)
- **W24d+ NOT pre-created** per CLAUDE.md §10 R1 rolling JIT
- **CO17 R8 umbrella** — F1.5b psycopg + F3.5b RAGAs live-verify + W24c Entra Graph SDK runtime smoke 仍 external-blocked

---

## §7 Changelog

| Day | Change | Reason |
|---|---|---|
| Day 0 2026-05-21 | Plan kickoff cascade — frontmatter / §0-§7 全部 landed `status: active` + Chris kickoff directive。**Pre-active-flip R6 audit finding**:ADR-0027 §Decision「6 NEW Postgres tables」中 `audit_log` **已存在**(W24-c1 F4 created + W24b F6 filter/pagination extended)→ W24c F2 實際 = **5 NEW tables**(`roles` + `role_permissions` + `groups` + `group_members` + `kb_acl`),`audit_log` 由 F7 **EXTEND**(additive `AuditAction` Literal append)非 create — plan §2 F2 + F7 已 reflect。**C16 vs C11 decision** deferred to F1.3(ADR-0027 leaves it open)。**Entra Graph SDK H2** pre-cleared via ADR-0027 acceptance(W19 F6)— F1 install per ADR-0017 Plan B,no fresh stop-and-ask。 | per CLAUDE.md §10 R1 + R6 + ADR-0027 §Decision Option A |

---

**End of W24c-users-rbac plan(version 1.0 kickoff)**
