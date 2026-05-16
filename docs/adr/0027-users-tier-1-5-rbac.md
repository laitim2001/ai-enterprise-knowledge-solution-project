# ADR-0027: /users Tier 1.5 RBAC NET NEW surface(**option set — Chris pick at W19 F6**)

**Date**: 2026-05-16
**Status**: **Accepted (Option A full RBAC)** — W19 F6 Chris pick 2026-05-16。Chris selected Option A over Option B minimal 3-role(W19 F2 §6 recommendation)和 Option C stage。**Implications**:~20 NEW backend days + 6 NEW Postgres tables(`roles` + `role_permissions` + `groups` + `group_members` + `audit_log` + `kb_acl`)+ Entra Graph SDK new dependency(H2 trigger;R8 corp-proxy risk per ADR-0017 mitigation)+ ACL middleware on every protected endpoint + audit_log writes + new C16 Users Service component + Wave C combined with ADR-0026 Option B = ~42 backend days **MUST split Wave C into C1+C2** per F4 §3.6 trigger + CLAUDE.md §10 rolling JIT。Full RBAC Tier 1 ship = significantly higher operational maturity for Beta launch + per-KB ACL fully functional
**Approver**: Chris(Tech Lead + stakeholder)

## Context

`architecture.md v6 §3.7` 原 spec — RBAC = **Tier 2 hook**(`useRole()` hook + `users` Postgres table per ADR-0023 but role enforcement deferred);Tier 1 single-tenant assumes Workspace Admin = de-facto everyone-can-do-anything。

`references/design-mockups/ekp-page-users.jsx PageUsers`(per W19 F1 audit) implements **`/users` NET NEW Tier 1.5 surface** with 4 tabs:**Members** / **Roles & permissions** / **Groups** / **Audit log**。 Plus `TabKbAccess` per-KB ACL(used by `/kb/[id]` Access tab per ADR-0025)。

Surface details:

- **Members tab** — 11 mock users with filter seg(all/admin/editor/user/pending)+ 10-col table(checkbox / member / role / source / group / queries_7d / kbs_owned / last_login / status / more);invite + suspend + role-change actions
- **Roles tab** — 4 role cards(3 active + 1 Tier 2 Power User disabled)+ permissions matrix(5 areas × 24 permissions × 4 role columns:Admin / Editor / End User / Power User Tier 2)
- **Groups tab** — Entra ID groups sync(`grp-ekp-admins` + `grp-ekp-editors` + `grp-ekp-users`)→ EKP role mapping;`POST /groups/sync-from-entra`
- **Audit log tab** — activity feed with 6 action types(role.changed / user.invited / kb.access.granted / provider.key.rotated / kb.config.changed / user.suspended)+ 90d retention

Per ADR-0025 KB Detail Access tab dep:`TabKbAccess`(per-KB ACL with Manage/Edit/Query role override + add member + add Entra group)needs RBAC infrastructure to function — Wave A 7-tab Access tab disabled affordance until Wave C ADR-0027 acceptance。

Per W19 F2 §3.4:**NEW Postgres tables + ACL middleware** depends on scope decision:Option A full RBAC(6 NEW tables)/ Option B minimal 3-role(only `users.role` column add)/ Option C stage(B + later promote)。

Per CLAUDE.md §5.1 H1 + §5.4 H4 — promoting RBAC from Tier 2 hook to Tier 1.5 ship = architectural change + Tier boundary shift → requires ADR with explicit option set。

## Decision

Adopt **`/users` Tier 1.5 surface** + per-KB ACL(ADR-0025 Access tab dep)。Amend `architecture.md v6 §3.7` to promote RBAC from "Tier 2 hook" to "Tier 1.5 minimum" + add `§3.8 /users page` reference。Scope is the strategic call:

### Option A — Full RBAC(Tier 1.5 maximum scope)

- 4 tabs all fully functional(Members + Roles + Groups + Audit log)+ TabKbAccess per-KB ACL with Manage/Edit/Query
- **NEW Postgres tables**(per ADR-0023 base):`roles` + `role_permissions` + `groups` + `group_members` + `audit_log` + `kb_acl`(per-KB ACL)— ~6 NEW tables
- ACL middleware(every protected endpoint checks role + KB ACL)+ auth-time role claim(JWT/cookie carries role)+ frontend `useRole()` hook + role-gated view rendering
- `POST /groups/sync-from-entra`(Entra Graph SDK call)
- Audit log writes on every role/access/config change
- Backend scope:~**20 backend days**(must split Wave C into C1 + C2 sub-phases per rolling JIT)
- New Cn:**C16 Users Service**(or fold large scope into C11 Identity & Access expansion)

### Option B — Minimal 3-role hard-coded(**RECOMMENDED — per W19 F2 §6**)

- Only `users.role` column ADD to existing `users` table per ADR-0023(no new tables)
- ACL middleware checks `users.role` only against hard-coded `PERMISSIONS_MATRIX`(per prototype lines 26-60 — 5 areas × 24 permissions × 3 columns Admin/Editor/User;Power User column = Tier 2 disabled in matrix)
- Members tab = **read-only listing** of `users` table + invite + suspend actions(no role-change UI — defer to Tier 2)
- Roles tab = **read-only matrix display**(no edit / no custom roles)
- Groups tab = **disabled affordance**「Tier 2 sync from Entra」(Entra Graph SDK deferred Tier 2)
- Audit log tab = **disabled affordance**「Tier 2 audit log」(no audit_log table writes Tier 1)
- TabKbAccess per-KB ACL = **disabled affordance** ADR-0025 Access tab `「Tier 2 per-KB ACL — workspace role enforces」` — Wave A 7-tab + Access tab Tier 2 affordance
- Backend scope:**~5 backend days**(`users.role` column migration + ACL middleware + read-only endpoints)
- No new Cn(C11 Identity scope expansion only)

### Option C — Stage(Option B Tier 1 + Tier 2 governance flips to Option A)

- Initial ship = Option B minimal(`users.role` column)
- Q12 post-Beta governance trigger promotes Option B → Option A(full RBAC)
- Wave C = Option B scope(~5 days);post-Beta = Option A delta scope(~15 days)
- Trade-off:double-implementation cost(Tier 1 read-only + Tier 2 editable mucking with same surfaces)— but lower Tier 1 risk
- Same ~5 backend days Wave C

**Recommended pick**:**Option B minimal 3-role**。Rationale:Tier 1 Beta cohort is internal Ricoh small scale(per Q7),hard-coded permissions matrix suffices;Entra Graph SDK is new dependency(R8 corp-proxy concern + ADR-0017 mitigation pattern);Audit log is operationally valuable but Tier 2 timing fine(Postgres `audit_log` table additive — Tier 2 can ship without UI break since Tier 1 disables the tab)。Cost:5 backend days fits single Wave C phase alongside ADR-0026 Option C(also ~5 days)— total ~10 backend days for Wave C。

## Alternatives Considered

1. **Reject Tier 1.5 surface entirely**(stay Tier 2 hook only)— rejected。`/kb/[id]` Access tab per ADR-0025 needs *some* RBAC infrastructure;workspace-only role(everyone-is-Admin)Tier 1 = no role differentiation = Access tab is just decorative;defeats the prototype design + Beta operator's need to grant Editor-only access to certain KBs(Q7 cohort scope).
2. **Option A full RBAC Wave C** — rejected per W19 F2 §6 recommendation。~20 backend days + 6 NEW tables + Entra Graph SDK + audit_log writes = exceeds single Wave C phase budget;must split Wave C into C1+C2 against rolling JIT pre-commit (per CLAUDE.md §10 R1)。Promote to Tier 2 governance Q12 trigger when Beta cohort scale validates full RBAC need。
3. **Promote /users to top-level sidebar module**(replace Eval or Traces) — rejected。ADR-0024 5-module sidebar locked;`/users` access from Sidebar Tools sub-section + Settings → Identity & Auth role mapping covers the navigation。
4. **Roles editable Tier 1 with custom roles** — rejected。Custom role creation = Tier 2(`PERMISSIONS_MATRIX` is a static admin policy decision,not user-tweakable;keeping it hard-coded preserves Tier 1 audit clarity).
5. **Audit log enabled Tier 1 even with Option B** — considered but rejected。Audit log requires the `audit_log` Postgres table + writes on every role/access/config change = touches every protected endpoint(middleware level)= operationally valuable but expands minimal-3-role scope from ~5 days to ~7。Tier 2 promotion path preserves the UI(disabled affordance"audit log coming Tier 2")while keeping Wave C scope tight。

## Consequences

**Per Option B(recommended)**:

**Positive**:
- 3-role hard-coded(Admin / Editor / User)matches prototype `PERMISSIONS_MATRIX`(5 areas × 24 permissions × 3 columns)— sufficient for Beta cohort internal Ricoh
- `users.role` column on existing `users` table per ADR-0023 = single Postgres migration + ACL middleware add ~5 backend days
- Wave C scope tight + fits single phase alongside ADR-0026 Option C hybrid
- Tier 2 promotion path clear:promote disabled affordances(Groups / Audit log / custom roles / Power User / per-KB ACL)to active as Beta cohort scales(Q12 trigger)
- Settings → Identity & Auth tab Role mapping(per ADR-0026)reads the same 3-role hard-coded matrix — no separate config needed

**Negative**:
- Wave A KB Detail Access tab = disabled affordance(per ADR-0025)— 7-tab(`-Access`)until Wave C
- Members tab no edit/promote/demote action Tier 1(read-only)— operators manage via Entra group membership + invite + suspend only
- Audit log tab = disabled affordance Tier 1 — no role/access change history in UI(operators rely on Entra audit log + Postgres direct query for compliance review)
- Groups tab disabled affordance — Tier 1 operators manually map Entra groups → role via Settings → Identity & Auth role mapping(per ADR-0026 read-only)
- Power User role visible in PERMISSIONS_MATRIX 4th column but disabled per Tier 2 — sets expectations clearly

**Neutral**:
- `architecture.md v6 §3.7` Tier 2 hook → Tier 1.5 minimum amendment inline-tagged at W22-frontend-wave-c kickoff(same convention as ADR-0024/0023/0022)
- `users` table schema migration is additive(`role` column with default `'user'`)— no breaking change
- `COMPONENT_CATALOG.md` C11 Identity & Access row gets「Tier 1.5 RBAC Option B per ADR-0027」status + scope expansion note
- Mock-auth dev mode default(per user 岔口 2 W22 ship mock + real both):Mock provider returns `role: 'admin'`(documented),real MSAL provider extracts role from Entra ID group membership via session callback

## References

- `architecture.md v6 §3.7` Identity & Access(Tier 2 hook spec)+ §11 Tier 2 trigger matrix
- `references/design-mockups/ekp-page-users.jsx`(`PageUsers` lines 62-113;ROLES lines 19-24;PERMISSIONS_MATRIX lines 26-60;UsersTab lines 115-191;RolesTab lines 209-286;GroupsTab lines 288-322;AuditTab lines 324-377;TabKbAccess lines 390-519)
- W19 F1 audit §2.1 D3(massive H1 weight + Tier 1.5 NET NEW)
- W19 F2 backend gap map §3.4 items 14-20(Option A/B/C effort estimates)+ §6 Option B recommendation
- ADR-0023 Postgres persistent backing(users table already exists via psycopg + PostgresUsersStore)
- ADR-0014 hybrid auth model(Entra ID group → role mapping concept)
- ADR-0017 R8 corp-proxy mitigation(rationale for deferring Entra Graph SDK to Tier 2 if Option B picked)
- ADR-0025 KB Detail 8-tab(Access tab hard dep — disabled affordance Wave A,active Wave C with Option B)
- ADR-0026 Settings 6-tab(Identity & Auth tab Role mapping read-only Tier 1 + scoped to 3-role per this ADR)
- Q7 Beta cohort source(internal Ricoh + RAPO + 1-2 friendly departments)— validates "small scale,hard-coded matrix sufficient"
- Q11 Entra ID tenant Resolved 2026-05-05 + operational commit early June 2026(per W9 D1 alignment)
