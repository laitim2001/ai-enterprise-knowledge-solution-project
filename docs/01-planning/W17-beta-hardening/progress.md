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

- **`86a4403`** `docs(planning)` — W17-beta-hardening phase folder kickoff(plan + checklist + progress.md Day 0;rolling-JIT per CLAUDE.md §10 R1)
- **`6edd9ef`** `docs(adr)` — ADR-0022 auth-transport hardening(`Accepted`)+ ADR-0023 KB Manager persistent backing(`Accepted`)+ README index(next NNNN → 0024) — **F0 complete**(H1/H2 gate cleared)

---

## Day 1 — F4 frontend hardening bundle(2026-05-10)

> Same-calendar-day as Day 0 — F4 is the「trivials first」start per the user directive「(A) 直接開工(F4 trivials 先,然後 F1)」。F0 ADRs landed Day 0;F1 Postgres starts after F4.

### F4 — landed `9ee636c` `feat(frontend,api)`

- **F4.1** — KB-detail Documents tab(`frontend/app/admin/kb/[id]/page.tsx`)now calls the real `GET /kb/{id}/documents`(backend already implemented W16 F5.1.1 / CO_F3a — Azure AI Search chunk aggregation by doc_id;the「501 stub」was stale *frontend* copy, not a missing backend route — surfaced upfront per the Day-0 pre-kickoff exploration). NEW `frontend/lib/api/documents.ts`(`DocumentSummary` interface + `documentsApi.list(kbId)`). `DocumentsTab` rewritten:`useQuery(['kb', kb_id, 'documents'])` → `DocumentsTable`(title + tags / format Badge / chunks tabular-nums / last-indexed slice(0,10) / doc_id mono)+ `DocumentsSkeleton` loading + destructive error banner + empty-index Upload prompt(the old「Add a document」CTA, now gated on `data.length === 0`). `BackendStubNote` component preserved(still used by ChunksTab). Top-of-file docstring F3.2 line updated to reflect the W17 wiring.
- **F4.2** — `frontend/app/admin/page.tsx`:removed the unused `CardTitle` import → `npm run lint` now **green globally**(it was the only ESLint error;Karpathy §1.3 surgical — only this orphan).
- **F4.3** — `NEXT_PUBLIC_LANGFUSE_URL` is **already** in `.env.example`(line ~101,added W16 F5.x.2 `1dbcdf3`);`frontend/app/debug/[traceId]/page.tsx` already reads it via `LANGFUSE_FALLBACK_BASE`(ADR-0020 Session 2). No change needed — effectively closed. **CO_W15_F2_langfuse_url → CLOSED.**
- **F4.4** — Cohere reranker naming canonicalized to `Cohere-rerank-v4.0-pro`(the Azure Marketplace deployment name — matches the live `.env` `COHERE_RERANK_MODEL`, which is what actually works per the W16 backend smoke):aligned `backend/storage/settings.py` `cohere_rerank_model` default + `backend/retrieval/reranker/cohere.py` `model` default + both docstrings + `.env.example` `COHERE_RERANK_MODEL`. Human display label `"Cohere v4.0-pro"` kept for UI. Grep-verified no stray `rerank-v4.0-pro`(unqualified)/ `cohere-rerank-v4-pro` in code(empty). ADR / audit-doc historical `cohere-v4.0-pro` references left per anti-pattern「keep historical narrative」. Note:Path B(direct `api.cohere.com`)would need a Cohere-native model name — flagged in the `settings.py` comment, out of W17 scope.
- **Verification**:`tsc --noEmit` clean;`next lint`(whole frontend)green;`ruff check` clean on changed backend files;mypy unaffected(string-literal + docstring changes only — no type changes). Browser smoke of the Documents tab deferred to F5(needs a local backend + seeded KB + a doc actually indexed;the W16 seeded KB had 0 in-memory docs but the Azure index `ekp-kb-drive-v1` has chunks → the real `list_documents` would return the AP/AR/FA manuals — to be confirmed in F5).

### Carry-overs closed by F4

- CO_W15_F2_langfuse_url → CLOSED(F4.3 — already-present env var verified)
- `admin/page.tsx` `CardTitle` lint orphan(W16 progress Day 1 note)→ CLOSED(F4.2)
- Cohere reranker naming inconsistency(session-start.md §11)→ CLOSED(F4.4)

### Day 1 commits

- **`9ee636c`** `feat(frontend,api)` — W17 F4 Documents-tab real backend wire + admin lint fix + Cohere naming canon(6 files;+ NEW `frontend/lib/api/documents.ts`)
- **`(this docs commit)`** `docs(planning)` — W17 checklist F0+F4 ticked + this Day-1 progress entry + Day-0 commit hashes back-filled

---

## Day 2 → Day 6 — _(implementation entries appended below as work lands)_

_(Next:F1 Postgres backing → F2 cookie/CSRF → F3 RAGAs → F5 a11y/dark-mode → F6 Vitest → F7 closeout;each commit ↔ Day-N entry per R2;same-day collapse possible per W12-W15 calibration — the `start_date`/`end_date` window is not a commitment.)_

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
