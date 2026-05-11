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
- ✅ Derived `checklist.md` v1.1 from spec §2.2 In Scope + §3 AC — 7 phases × T-items(T1.1-T7.7 ≈ 40 atomic items)+ Cross-Cutting
- ✅ **Decision B discovery + approval**(post Phase 1 read-only investigation):while reading `backend/api/routes/kb.py:22-31` + `backend/storage/kb_naming.py` + ADR-0018 to plan the lifespan wiring,surfaced the **multi-KB Azure AI Search index provisioning gap** ── `POST /kb` only creates the KB storage record but does NOT provision the per-KB index `ekp-kb-{kb_id}-v1`(legacy `drive_user_manuals` was manually provisioned at W2 D1 via `scripts/create_index.py`);user's screenshot workflow(`copilot-cowork-document-1` new KB)would still fail post-CH-001-v1.1 with Azure 404 not 501. **User picked (β) scope expansion**:(1)user's screenshot was a new-KB workflow → (α) didn't solve it;(2)ADR-0018 Phase 3 was over-deferred(Track A blocks prod deploy, not dev `.env` admin-key);(3)同 W16 F5.3 Decision B.1 一齊 unblock;(4)避免 CH-001/CH-002 切割成本。
- ✅ **Updated spec to v1.2** — title extended;§1.5 NEW "discovered scope gap" subsection;§2.1 split into A (document routes) + B (KB routes auto-provisioning);§2.2 added S14-S20(create_index_for_kb / delete_index / delete_doc / upload kb_id-dynamic / POST kb wiring / DELETE kb wiring / docstring cleanup / test extension);§2.4 added 3 new explicit out-of-scopes;§3 added AC18-AC22;§4 added R9-R11;§5 effort 4-6h → 6-9h;§6.5 reaffirmed clean(implementation of existing ADR-0018, not new architecture);§6.6 NEW ADR-0018 status touch note;§7 v1.2 changelog row。
- ✅ **Extended checklist to v1.2** — NEW Phase 1.5(T1.5.1-T1.5.10, multi-KB index provisioning);Phase 2 T2.5 updated(`upload(kb_id=kb_id)` per T1.5.5);Phase 3 T3.1 referenced T1.5.4 not T1.2;Phase 5 added T5.14-T5.19(AC18-AC22 tests);Phase 6 T6.2 changed to use a NEW kb_id(was vague)+ added T6.4 + T6.6 Azure-direct verifies;Phase 7 T7.2/T7.3/T7.4 extended + T7.5 NEW(ADR-0018 update)

### Decisions
- **Decision A = (ii) replace-in-place reindex**(per user 2026-05-11). Rationale per spec §2.3:real semantics(atomic replace, one API call), honest about the source-store gap(user provides the source), 90% code reuse with POST + DELETE, closes CO_F3a properly. (i) rejected as technical-but-not-real close;(iii) rejected as genuinely Tier 2(R12 Azurite mismatch + scope creep).
- **Decision B = (β) scope expansion**(per user 2026-05-11):include multi-KB index provisioning(`POST /kb` auto-creates Azure index;`DELETE /kb` drops it;`IndexPopulator.upload(kb_id=)` BC-preserving signature;close ADR-0018 Phase 3 upload-side). Rationale per spec §1.5 + §7 changelog v1.2 row:user's screenshot workflow needs it,ADR-0018 was over-deferred,dev cred is already there,avoid CH-001/CH-002 split cost. (α) rejected because it doesn't solve the user's actual workflow ── only renames the wall.
- **Approach A vs B** for lifespan(spec §6.2):commit to **A** in implementation unless the embedder isn't safely shareable across query + ingest contexts(then B as fallback). Lifespan-init for `app.state.embedder`(exposed for ingestion)+ `app.state.index_populator` + `app.state.ingestion_chunker` alongside the existing `app.state.retrieval_engine` etc.
- **`uploader=None`** per the existing `scripts/run_populate_sanity.py` precedent(R12 Azurite signature mismatch still open;screenshots extracted but blob upload skipped;text retrieval unaffected per architecture.md §3.5). Per-KB blob container provisioning(ADR-0018 Phase 3 blob-side)stays deferred per R11 + spec §6.6 — needs R12 resolution first.
- **doc_id derivation = slugified filename stem**(not UUID)— traceability over opacity;duplicate doc_id within the same KB → 409 with hint.
- **`upload` signature BC**:keep `kb_id=None` optional default(falls back to `self.index_name` legacy behavior)so existing W2-era callers like `scripts/run_populate_sanity.py` + W2 tests don't break. Karpathy §1.3 surgical.
- **POST /kb storage rollback on Azure failure**:storage record deleted via `service.delete(kb_id)` if `populator.create_index_for_kb` raises;rollback failure itself is logged but the user-facing 502 still surfaces(R10 documented).
- **No new ADR + no new dep**(spec §6.4 + §6.5 — H1/H2 both verified clean;Decision B = implementation of existing ADR-0018, not a new architectural decision).
- **ADR-0018 stays `Accepted`** post-CH-001(NOT `done`)— Phase 3 upload-side closed,blob-side still R12-deferred(R11 + spec §6.6)

### Blockers
- None at kickoff — all W2 machinery already implemented, Azure dev cred presumed in `.env`(if missing → spec AC5 surfaces the 503 cleanly, not a CH-001 blocker)

### Effort
- Planned (today, kickoff + Decision B scope-expansion + spec/checklist/progress v1.1 → v1.2):~2.5h(initial 1.5h + ~1h for Decision B discovery + spec/checklist/progress update)
- Actual:~2.5h(this session)
- Variance:0

### Commits
| Hash | Subject |
|---|---|
| `671a925` | docs(planning): CH-001 spec + checklist + progress — approved Decision A = (ii) replace-in-place reindex (close CO_F3a) |
| _(pending)_ | docs(planning): CH-001 spec v1.2 + checklist + progress — Decision B = (β) scope expansion (multi-KB index provisioning; close ADR-0018 Phase 3 upload-side) |

### Next
- Commit the v1.2 pre-doc bundle update;then start **Phase 1**(T1.1-T1.5 backend service wiring)+ **Phase 1.5**(T1.5.1-T1.5.10 multi-KB index provisioning ── `IndexPopulator.create_index_for_kb` + `delete_index` + `delete_doc` + `upload(kb_id=)` BC ext + POST/DELETE /kb wiring)+ **Phase 2-4**(documents.py routes);commit per phase or per logical chunk;run `pytest` + `mypy --strict` + `ruff check` after each phase

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
