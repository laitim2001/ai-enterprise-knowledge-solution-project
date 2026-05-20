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

<!-- Day 1+ F1 entries land at F1 active flip per CLAUDE.md §10 R2 -->
