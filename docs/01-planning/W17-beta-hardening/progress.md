---
phase: W17-beta-hardening
plan_ref: ./plan.md
checklist_ref: ./checklist.md
status: active
last_updated: 2026-05-10
---

# Phase W17 — Progress

> Daily log + decisions + commits + closing retro。每 commit 對應一個 Day-N entry mention(R2;`docs(planning):` housekeeping exempt)。
> Plan deviation → `plan.md` §7 changelog（R3）。OQ resolved → `decision-form.md` + Day-N mention（R4）。

---

## Day 0 — Kickoff(2026-05-10)

### Trigger

User directive — after the W16 audit-tail browser-smoke session(`84d030e` CORS + `3a509c4` §13 policy + `adb89e5` progress entry,pushed):「先完整地規劃和處理 類別 1（AI 可即做，無 H1/H2，無外部依賴）+ 類別 2（要先決策 / ADR）」。Category-3 Track-A-blocked items explicitly excluded(stay W16 F1-F4). W17 runs in parallel with W16's blocked state — does not depend on W16 closeout.

### H1/H2 decisions(AskUserQuestion 2026-05-10)

- **Persistent storage backend** = **Postgres via `psycopg`**(option C)— docker-compose already has a postgres service(Langfuse);add a dedicated `ekp` database. New dep → H2 + ADR-0023.
- **httpOnly cookie hardening** = **do-now-in-W17**(write ADR + implement)— auth-transport change, touches ADR-0014 → ADR-0022.
- These two answers = the「approved + write ADR」authorization per CLAUDE.md §5.1 H1 / §5.2 H2.

### Pre-kickoff exploration findings(grounding the plan)

- `GET /kb/{id}/documents` is **already implemented** backend-side(W16 F5.1.1 CO_F3a — `engine.list_documents(kb_id)` aggregates Azure AI Search chunks by doc_id → `list[DocumentSummary]`). The「501 stub」text seen in the KB-detail Documents tab is **stale frontend copy** — W17 F4.1 wires the real call + drops the copy. Other doc endpoints(per-doc upload/reindex/delete)remain 501 stub(W2 ingestion + Track A — out of W17).
- `backend/kb_management/storage.py` = `KBStorageBackend` Protocol + `InMemoryKBBackend`(docstring already anticipates a swappable backend)— `PostgresKBBackend` satisfying the same Protocol + dependency-override is the clean path. `backend/api/auth/users_repo.py` similar.
- Backend venv:`ragas` **installed**(RAGAs integration feasible — no H2);`sqlalchemy` installed(transitive);`aiosqlite` / `psycopg` / `azure-cosmos` **missing**(psycopg to be added per ADR-0023).
- `frontend` has `@radix-ui/react-select` / `react-slider` / `react-switch` etc(W17 inherits the ADR-0021 RetrievalTab — no re-work).

### Setup completed Day 0

- `docs/01-planning/W17-beta-hardening/{plan,checklist,progress}.md` created — `status: active`(per user directive, not the usual draft→active flip — the directive *is* the authorization)
- Plan §2 deliverables F0-F7:F0 = ADR-0022 + ADR-0023(H1/H2 gate);F1 = Postgres backing;F2 = cookie/CSRF/refresh;F3 = RAGAs 4-metric;F4 = frontend hardening bundle;F5 = a11y + dark-mode verify;F6 = Vitest/RTL scaffold;F7 = closeout
- W16 F1-F4 sequence preserved — W17 is a parallel track, not a successor phase(rolling-JIT note: W17 folder created at kickoff per R1;W18+ NOT pre-created)

### Carry-overs addressed by W17(from session-start.md §11 + W16 progress)

| Carry-over | W17 deliverable |
|---|---|
| CO18 KB Manager + users_repo persistent backing | F1(ADR-0023)|
| CO_F5_refresh `/auth/refresh` rotation | F2.2 |
| CO_F5_cookie httpOnly cookie hardening | F2(ADR-0022)|
| CO_W15_F1_backend RAGAs deferral | F3 |
| CO_W15_F1_eval_set_v1 file verify | F3.4 |
| CO_W15_F2_langfuse_url Beta env var | F4.3 |
| CO_W15_F3_dark_mode_visual_verify | F5.1 |
| CO_W15_F4_vitest_baseline_gap | F6 |
| `admin/page.tsx` `CardTitle` lint orphan | F4.2 |
| Cohere reranker naming inconsistency | F4.4 |

NOT addressed(stay W16 / W18+ / Tier 2):CO16 Track A IT cred(W16 F1)/ CO19 25% rollout(W16 F2)/ CO17 AF3 fix(ADR-0013 reserved)/ CO_F6a-c ACS email(Track A)/ CO_W15_F3_aria_full_audit + CO_W15_F4_interactive_flow_E2E(Tier 2)/ Azure DELETE cleanup(Track A).

### Pre-condition checks(per CO_W14_process_grep_verify FORMALIZED 5-step — plan-author spec-ref grep verification before active flip)

1. Read plan literal acceptance criteria ✅
2. Grep code base for referenced files / functions / patterns — done(see「Pre-kickoff exploration findings」above:`GET /kb/{id}/documents` already impl / `KBStorageBackend` Protocol exists / `ragas` installed / etc)
3. Surface mismatches upfront ✅(the「501 stub」stale-copy finding → F4.1 reframed from「implement backend」to「wire frontend + drop stale copy」)
4. Document deviations in plan §7 changelog at kickoff ✅(initial-draft entry)
5. Adjust acceptance criteria per actual reality ✅(F4.1 reframed;F3.2 notes the W16 F5.4 minimal-impl placeholder it replaces)

### Day 0 commits

- **`(this docs commit)`** `docs(planning)` — W17-beta-hardening phase folder kickoff(plan + checklist + progress.md Day 0;rolling-JIT per CLAUDE.md §10 R1)
- **`(ADR commit)`** `docs(adr)` — ADR-0022 auth-transport hardening + ADR-0023 KB Manager persistent backing + README index(next NNNN → 0024)

---

## Day 1 → Day 6 — _(implementation entries appended below as work lands)_

_(W17 D1+ entries:F0 ADRs → F1 Postgres → F2 cookie → F3 RAGAs → F4 frontend bundle → F5 a11y/dark-mode → F6 Vitest → F7 closeout;each commit ↔ Day-N entry per R2;same-day collapse possible per W12-W15 calibration — the `start_date`/`end_date` window is not a commitment.)_

---

## Retro(填於 W17 closeout — F7)

### What worked

_(TBD)_

### What didn't

_(TBD)_

### Surprises / discoveries

_(TBD)_

### Decisions

_(TBD — will include: storage = Postgres rationale / cookie SameSite+Secure policy / RAGAs CI-mock boundary / Cohere canonical identifier pick)_

### Carry-overs to W18+

_(TBD)_

### Time tracking

| Deliverable | Plan estimate | Actual | Variance |
|---|---|---|---|
| F0 ADRs | 0.5 day | _TBD_ | _TBD_ |
| F1 Postgres backing | 2 days | _TBD_ | _TBD_ |
| F2 auth-transport | 1.5 days | _TBD_ | _TBD_ |
| F3 RAGAs | 1.5 days | _TBD_ | _TBD_ |
| F4 frontend bundle | 0.5 day | _TBD_ | _TBD_ |
| F5 a11y/dark-mode | 0.5 day | _TBD_ | _TBD_ |
| F6 Vitest scaffold | 0.5 day | _TBD_ | _TBD_ |
| F7 closeout | 0.5 day | _TBD_ | _TBD_ |

### Spec ref alignment

_(TBD — F1 → architecture.md v6 §3.4 + ADR-0023;F2 → §3.7 + ADR-0014 + ADR-0022;F3 → §5.6 + eval-methodology.md;F4 → §5.x + ADR-0012;F6 → CLAUDE.md §3.2)_
