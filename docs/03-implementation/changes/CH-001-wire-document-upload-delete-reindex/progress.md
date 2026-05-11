---
change_id: CH-001
spec_ref: ./spec.md
checklist_ref: ./checklist.md
status: in-progress
last_updated: 2026-05-11
---

# CH-001 — Progress

> Day-N entries during execution + 結尾 closeout summary。
> 每 commit 對應一個 Day-N entry mention(R2 binding rule per PROCESS.md §5)。

---

## Day 0 — Kickoff(2026-05-11)

### Trigger
- User trigger:2026-05-11 dev test session — `/kb/new` Pipeline wizard step 3 hit 501 on `POST /kb/{kb_id}/documents`(screenshot `Screenshot 2026-05-11 102613.png`)
- Diagnosis confirmed:`backend/api/routes/documents.py:72-102` is a 3-route hardcoded 501-stub cascade(POST upload + DELETE doc + POST reindex);session-start.md §11 lists this as **CO_F3a** carry-over("per-doc upload/reindex/delete stays 501 stub — W2 ingestion + Track A")
- "Track A" deferral label was over-broad — the actual block is `.env.production` for prod deploy, but the dev `.env` already has Azure OpenAI + AI Search cred(W2 Gate 1 PASS R@5=0.9722 was driven by these);so this is unblocked **now**

### Done(this session)
- ✅ Confirmed diagnosis by reading `backend/api/routes/documents.py` + grepping for the 501 stub text + confirming the W2 ingestion machinery exists(`backend/ingestion/orchestrator.py` + `parsers/{docx,pptx,pdf}_parser.py` + `parsers/__init__.py` `select_parser` factory + `chunker/layout_aware.py` + `embedding/azure_openai_embedder.py` + `indexing/populate.py`)+ `scripts/run_populate_sanity.py` as the canonical caller pattern
- ✅ PROCESS.md §1 classification = **Change**(behavior change 501 stub → real implementation;not a Phase deliverable — no active phase;not a Bug-fix — no regression)
- ✅ Surfaced **Decision A**(reindex semantics)to the user:**(i)** 422 + hint / **(ii)** replace-in-place / **(iii)** source-doc store
- ✅ User picked scope **(b)**(POST + DELETE + reindex 一齊做)+ Decision A = **(ii) replace-in-place reindex**
- ✅ Wrote `spec.md` v1.1 — status `draft` → `approved`(2026-05-11);§2.3 locked to (ii) with the doc_id-match safety check;§3 AC9 broken into AC9.1 (happy path) / AC9.2 (missing file) / AC9.3 (mid-pipeline failure + mismatch);§7 changelog row added
- ✅ Derived `checklist.md` from spec §2.2 In Scope + §3 AC — 7 phases × T-items(T1.1-T7.7 ≈ 40 atomic items)+ Cross-Cutting

### Decisions
- **Decision A = (ii) replace-in-place reindex**(per user 2026-05-11). Rationale per spec §2.3:real semantics(atomic replace, one API call), honest about the source-store gap(user provides the source), 90% code reuse with POST + DELETE, closes CO_F3a properly. (i) rejected as technical-but-not-real close;(iii) rejected as genuinely Tier 2(R12 Azurite mismatch + scope creep).
- **Approach A vs B** for lifespan(spec §6.2):commit to **A** in implementation unless the embedder isn't safely shareable across query + ingest contexts(then B as fallback). Lifespan-init for `app.state.ingestion_orchestrator` + `app.state.index_populator` alongside the existing `app.state.retrieval_engine` etc.
- **`uploader=None`** per the existing `scripts/run_populate_sanity.py` precedent(R12 Azurite signature mismatch still open;screenshots extracted but blob upload skipped;text retrieval unaffected per architecture.md §3.5).
- **doc_id derivation = slugified filename stem**(not UUID)— traceability over opacity;duplicate doc_id within the same KB → 409 with hint.
- **No new ADR + no new dep**(spec §6.4 + §6.5 — H1/H2 both verified clean).

### Blockers
- None at kickoff — all W2 machinery already implemented, Azure dev cred presumed in `.env`(if missing → spec AC5 surfaces the 503 cleanly, not a CH-001 blocker)

### Effort
- Planned (today, kickoff only):~1.5h(diagnosis + spec + checklist + progress)
- Actual:~1.5h(this session)
- Variance:0

### Commits
| Hash | Subject |
|---|---|
| _(pending)_ | docs(planning): CH-001 spec + checklist + progress — approved Decision A = (ii) replace-in-place reindex |

### Next
- **T1.1-T1.5**(backend service wiring)+ **T2.x**(POST handler);commit per phase or per logical chunk;run `pytest backend/tests/api/test_documents_route.py` + `mypy --strict` + `ruff check` after each phase

---

## Day 1 — _pending_(YYYY-MM-DD)

### Done
- _(fill as items complete)_

### Decisions
- _(if any design choices land here)_

### Blockers
- _(if any)_

### Effort
- Planned:{h};Actual:{h};Variance:{±h}

### Commits
| Hash | Subject |
|---|---|

---

## Closeout(填於 status=done)

### Acceptance verification(against spec §3 AC1-AC17)
- _(verify each AC ✅ / ⚠️ partial / ❌ failed at closeout)_

### Effort summary
| Day | Planned (h) | Actual (h) | Variance |
|---|---|---|---|
| Day 0 (kickoff) | 1.5 | 1.5 | 0 |
| Day 1 (impl) | TBD | — | — |

### Lessons
- **What worked**:_(fill at closeout)_
- **What didn't / unexpected friction**:_(fill at closeout)_
- **Carry-overs**:_(if any deferred to other tasks)_

### Component design note status updates
- **C01**(Ingestion):`v1-active`(orchestrator path now also exercised via HTTP route, not just `scripts/run_populate_sanity.py` — no spec/interface change → no version bump)
- **C03**(Indexing):if `IndexPopulator.delete_doc` was added — note in components/C03-*.md;else no change
- **C08**(API Gateway):`v1-active`(stub-cascade fully closed — POST/DELETE/reindex all real;append `Status` row note)

### CO_F3a status flip
- session-start.md §11 — flip from "stays 501 stub — W2 ingestion + Track A" to **"CLOSED by CH-001 YYYY-MM-DD"**

---

**End of CH-001 progress**
