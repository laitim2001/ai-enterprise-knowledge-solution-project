---
phase: W16-beta-deploy
plan_ref: ./plan.md
checklist_ref: ./checklist.md
status: active                     # F5 partial-active flip 2026-05-10 — F1-F4 preserved draft pending Track A IT cred trigger
last_updated: 2026-05-10
---

# Phase W16 — Progress(Daily Journal + Decisions + Retro)

> Daily progress entries per CLAUDE.md §10 R2(每 commit reference progress.md Day-N entry)。
> Status:`draft` — pending W16 D1 active flip post Track A IT cred populate event trigger + R-B1 closure(rolling JIT — non same-day collapse fit per real Beta deploy stakeholder + cohort coordination dependencies)。

---

## Day 0 — Pre-kickoff Setup(W15 D5 F5 closeout cascade 2026-06-10)

> **Note**:呢個 Day 0 entry 屬 W15 D5 F5 closeout cascade carry-over governance prep,而非 W16 implementation start。**W16 D1 implementation start** = post Track A IT cred populate event trigger + R-B1 closure(blocking external dependency per W11 retro CO16;non rolling JIT same-day collapse fit per real Beta deploy stakeholder coordination)。

### Setup completed pre-W16 D1

| Artifact | Commit | Status |
|---|---|---|
| W15 phase Gate PASS WITH SMOKE-USER-DEFERRED CAVEAT verdict landed | _W15 D5 F5 closeout commit_ | 🟡 in flight(this session) |
| W15 progress.md retro 7 sections + Tier 1 UI sprint cycle FINAL retrospective complete | _W15 D5 F5 closeout commit_ | 🟡 in flight(this session) |
| W15 frontmatter active → closed cascade(plan + checklist + progress) | _W15 D5 F5 closeout commit_ | 🟡 in flight(this session) |
| W16 phase folder skeleton(plan.md + checklist.md + progress.md) | _W15 D5 F5 closeout commit_ | 🟡 in flight(this session) |
| F1 V5 Eval Console implementation | `bf01091` | ✅ landed W15 D1 |
| F2 V6 Debug View implementation | `00b2262` | ✅ landed W15 D2 |
| F3 polish + token cleanup MILESTONE(entire frontend oklch=0)| `60c812d` | ✅ landed W15 D3 |
| F4 Playwright E2E + pixel diff baseline harness | `88320b9` | ✅ landed W15 D4 |
| Tier 1 UI sprint cycle FINAL marker landed(architecture.md v6 §13.12 amendment 完整 implemented;9 views × 6+ components × hybrid auth × ACS email × responsive/a11y/E2E/pixel diff baseline) | _W15 D5 F5 closeout commit_ | 🟡 in flight(this session) |

### Pending W16 D1 active flip pre-conditions(blocking external dependencies)

- ⏳ **Track A IT cred populate event trigger received** — blocking pre-condition per W11 retro CO16(stakeholder + IT engagement dependency;non same-day collapse fit per real-world IT process timing)
- ⏳ **R-B1 closure verification ready** — risk register live update prerequisite
- ⏳ **CO_W14_process_grep_verify FORMALIZED pre-active flip checklist** applied at W16 D1 active flip per W15 retro decision(spec ref grep verification step prevents 10th occurrence of plan literal vs actual code drift pattern)
- ⏳ W16 plan/checklist/progress frontmatter `draft → active` flip on W16 D1 active trigger

### W16 immediate scope alignment with W15 retro Carry-overs

#### Immediate W16 D1 priority
- **Track A IT cred consumption** → **W16 F1**(deliverable exact match)
- **R-B1 closure verification** → **W16 F1**
- **W12+W13+W14+W15 user smoke 3-step workflow first execution** → **W16 F4**(deliverable exact match)

#### Backend follow-ups immediate Beta hardening
- **CO_F3a/b/c**(W14)→ **W16 F5.1-F5.3**(deliverable exact match)
- **CO_W15_F1_backend** → **W16 F5.4**(deliverable exact match)
- **CO_W15_F1_eval_set_v1** → **W16 F5.x** thin checklist
- **CO_W15_F2_backend** → **W16 F5.5**(deliverable exact match)
- **CO_W15_F2_langfuse_url** → **W16 F5.x** thin checklist

#### Polish + a11y + test backlog Beta hardening(non-W16 priority — W17+ candidates)
- CO_W15_F3_aria_full_audit / CO_W15_F3_dark_mode_visual_verify / CO_W15_F4_browser_binaries(W16 F4.1 if blocked)/ CO_W15_F4_baseline_capture(W16 F4.2 deliverable)/ CO_W15_F4_vitest_baseline_gap / CO_W15_F4_interactive_flow_E2E

#### Process improvement formalization
- **CO_W14_process_grep_verify FORMALIZED** → **W16 D1 active flip pre-checklist** applied(per W15 retro decision empirical signal 9 cumulative occurrences)

### W16 critical path

- **W16 D1-D2** F1 Track A IT cred consumption + R-B1 closure verification(blocking dependency timing)
- **W16 D3-D4** F2 25% Beta cohort rollout activation(stakeholder + cohort coordination)
- **W16 D5** F3 daily metric monitor + Q15 first weekly signal report
- **W16 D6** F4 user smoke first run(W12+W13+W14+W15 manual smoke deferred backlog systematic subsume target actualized)
- **W16 D7-D9** F5 backend stub closure cascade(4 stub endpoints W3+/W4 implementations)
- **W16 D10** F5 finalize + W16 phase Gate closeout

### W17+ phase entry

- W16 closes Beta deploy production launch resume sprint;W17+ = Beta cohort expansion beyond 25% + persistent backing migration + Tier 2 evaluation triggers
- W17+ D1 implementation start trigger = W16 D10 retro post-Beta deploy assessment + Q15 first weekly signal report outcome
- **W17+ phase folder 唔 pre-create** per CLAUDE.md §10 R1 rolling-JIT discipline preserved

---

## Day 1 — F5 partial-active flip + backend stub closure cascade(2026-05-10)

> **Note**:Day 1 entry triggered by **Path A pivot**(post user prompt 2026-05-10 — F5 backend stub closure cascade AI fully controllable)。**F1-F4 sequence preserved draft** pending Track A IT cred populate event trigger + R-B1 closure(blocking external dependency per W11 retro CO16);**F5 partial-active flip** allowed per W16 plan §3 PARTIAL PASS condition + Path A scope decision。

### F5 partial-active flip pre-checklist applied(CO_W14_process_grep_verify FORMALIZED 5-step)

Per W15 retro decision empirical signal 9 cumulative occurrences + W16 D1 active flip pre-checklist requirement:

1. **Read plan literal acceptance criteria** ✅ — F5.1-F5.5 + F5.x scope read from W16 plan.md §2
2. **Grep code base for referenced files / functions / patterns** ✅ — comprehensive grep findings:
   - F5.1 stubs identified:`documents.py:8` GET /kb/{id}/documents + `chunks.py:16` GET /kb/{id}/documents/{id}/chunks(both 501)
   - F5.2 mismatch:`PATCH /kb/{id}/settings`(`kb.py:62`)接收 KbConfig 唔接收 name+description → new endpoint needed per Decision A.1
   - F5.3 mismatches:`POST /kb/{id}/reindex` per-KB level NOT EXIST(only per-doc reindex `documents.py:41`)→ new endpoint needed;`DELETE /kb/{id}` 已 impl in-memory(`kb.py:45`)→ Azure cleanup defer Track A per Decision B.1
   - F5.4 stubs identified:`eval.py:18` POST /eval/run + `eval.py:28` POST /eval/shootout(both 501)
   - F5.5 stub identified:`debug.py:8` GET /debug/trace/{trace_id}(501)
   - F5.x.1 finding:`docs/eval-set-v1.yaml` does NOT exist;`docs/eval-set-v1-draft.yaml` only → W17+ candidate
   - F5.x.2 finding:`NEXT_PUBLIC_LANGFUSE_URL` 未 wired anywhere(only mentioned in W15+W16 planning docs)→ env var add needed
3. **Surface mismatches via Karpathy §1.1 think-before-coding upfront** ✅ — 7 mismatches surfaced + 4 decision points proposed to user
4. **Document deviations in plan §7 changelog at plan kickoff** ✅ — W16 plan §7 row 2026-05-10 added documenting partial-active flip + scope decisions
5. **Adjust acceptance criteria per actual reality** ✅ — F5.1-F5.5 + F5.x checklist sub-items expanded inline per findings

### Scope decisions confirmed(Path A)

- **Decision A.1** — F5.2 NEW `PATCH /kb/{kb_id}` body={name, description} endpoint(separation of concern preserved;`/settings` reserve KbConfig)
- **Decision B.1** — F5.3 DELETE Azure cleanup defer Track A IT cred trigger;in-memory baseline preserved
- **Decision C.1** — F5.4 BOTH `/eval/run` + `/eval/shootout` full implementation(heavy work)
- **Decision D.2** — F5.5 full Langfuse SDK integration(unblocks ADR-0020 frontend Session 2 Drift #3 V6 9-stage)
- **Decision E.1** — single session F5.1-F5.5 ambitious(per V2 same-day collapse precedent W12-W15)

### F5 implementation sequence(ordered by dependency)— ✅ ALL COMPLETED 2026-05-10

| # | Deliverable | Commit | Tests | Status |
|---|---|---|---|---|
| 0 | F5 partial-active flip governance prep | `61eba52` | — | ✅ |
| 1 | F5.1 KB documents/chunks listing(CO_F3a)| `507cbff` | 10 passed | ✅ |
| 2 | F5.2 KB name+description PATCH(CO_F3b;Decision A.1 NEW endpoint)| `cb30e8e` | 6 passed | ✅ |
| 3 | F5.3 KB-level reindex + DELETE annotate(CO_F3c;Decision B.1 defer Track A)| `5a357e7` | 4 passed | ✅ |
| 4 | F5.4 eval/run + eval/shootout(CO_W15_F1;Decision C.1 + W17+ RAGAs deferral)| `4046b24` | 9 passed | ✅ |
| 5 | F5.5 debug/trace Langfuse(CO_W15_F2;Decision D.2 full SDK)+ F5.x.2 env var + skeleton fixups | `1dbcdf3` | 6 passed | ✅ |

### F5 closeout snapshot 2026-05-10

- **6 commits landed**(governance + 5 implementation)
- **35 NEW tests passed**(10 F5.1 + 6 F5.2 + 4 F5.3 + 9 F5.4 + 6 F5.5)
- **Full backend regression**:**578 passed + 7 skipped**(was 553 baseline post Phase 4 P1;+25 NEW;0 regressions including 2 skeleton-test fixups for stub-asserting tests cascaded with F5.4 + F5.5 implementation)
- **ruff**:All checks passed across all touched files
- **Drift #3 frontend Session 2 unblocked** — ADR-0020 V6 6→9 stage `PipelineStageCollapsible` can now wire to `GET /debug/trace/{trace_id}`(F5.5 closure cascading benefit per audit-W15-d5-vs-spec.md §10)

### W17+ deferred items captured in code

- F5.4 RAGAs 4-metric full integration(faithfulness / answer_relevancy / context_precision / context_recall)— `backend/eval/orchestrator.py` docstring
- F5.4 voyage/zeroentropy/azure shootout via endpoint — point to `scripts/run_reranker_shootout.py` CLI driver
- F5.3 Azure cleanup(index drop + Blob container drop)on DELETE — Decision B.1 deferral note in `routes/kb.py:delete_kb` docstring
- F5.x.1 eval-set-v1.yaml finalization — pending Beta cohort real-query collection per Q6 + Q15 trigger
- F5.4 background task pattern(FastAPI BackgroundTasks)— scale escape hatch if synchronous eval response exceeds Beta UX tolerance

### Carry-overs preserved unchanged(F1-F4 still pending Track A trigger)

- F1 Track A IT cred consumption + R-B1 closure verification — blocked external
- F2 25% Beta cohort rollout activation — blocked F1
- F3 Daily metric monitor + Q15 first weekly signal report — blocked F2
- F4 User smoke first run(Playwright E2E baseline capture)— ADR-0017 R8 trigger candidate;blocked F4.1 install attempt

### ADR-0020 Phase 3 Session 2 — landed Day 1(outside W16 plan F1-F5 scope;audit campaign tail)

> Not a W16 plan deliverable — continuation of an approved ADR's implementation, tracked via `docs/adr/0020-…` §Implementation Deliverables + `audit-W15-d5-vs-spec.md` §10 ledger #24(同 Session 1 `cffb391` 嘅 pattern)。Recorded here per R2(commit-on-this-day ↔ progress entry)。

- **`cb15c3d`** `feat(frontend,observability)` — V6 Debug View 6→9 conceptual stages(adds Query Rewriter / Re-retrieve / Context Expander)+ Context Expander Langfuse trace wiring(`emit_stage_metadata` at source + `_extract_stage` reads `observation.metadata`→`TraceStage.details` + `TraceStage.details` schema)+ `lib/api/debug.ts` contract sync to the live `/debug/trace` shape + status-field branching replaces 501-stub-mitigation
- **Tests**:5 NEW(3 `test_observe.py` + 2 `test_debug_trace.py`)→ **583 passed + 7 skipped**(was 578+7;0 regressions);ruff clean;`tsc --noEmit` EXIT_CODE=0;eslint clean on changed files
- **Browser smoke**(dev server,user-authorized this session)— `/debug/{id}` renders 9-stage scaffold + vendor tags + collapsible toggle(`aria-expanded`)+ error-banner branch(Azure dev backend still serves the old 501 stub)+ Open-in-Langfuse fallback URL;no SSR/layout breakage。Interactive visual/pixel verification deferred W16 F4(Playwright pixel baseline re-capture;R8 corp-proxy blocked)per ADR-0020 §C
- **`<later docs commit>`** `docs(architecture)` — audit §10 ledger #24 + Drift #3 → **FULLY CLOSED** + ADR-0020 §Implementation Deliverables checkboxes ticked + this progress entry(landed `14e6650`)

### ADR-0021 + Drift #5 — landed Day 1(outside W16 plan F1-F5 scope;audit campaign tail)

> Not a W16 plan deliverable — implements an approved ADR; tracked via `docs/adr/0021-…` §Implementation Deliverables + `audit-W15-d5-vs-spec.md` §10 ledger #25-26. `HybridSearcher.search()` `mode` param touches C04 §3 RAG Core interface → H1 ADR per strict reading; user-approved "write ADR-0021 (strict mode)" 2026-05-10.

- **`1ea08b0`** `docs(adr)` — ADR-0021(V4 Retrieval Testing tab §5.5.4 deliver + `HybridSearcher` search-mode param)+ README index updated(next NNNN now 0022)
- **`9582fa4`** `feat(retrieval,frontend)` — `HybridSearcher.search()` + `RetrievalEngine.retrieve()` gain `mode`("hybrid" default unchanged / "vector" / "fulltext")+ `rerank: bool`；NEW `POST /kb/{kb_id}/retrieval-test`(pure retrieval — no CRAG / no synthesis)+ NEW `api/schemas/retrieval_test.py`；V4 `RetrievalTab` rewritten into "Retrieval test" panel(mode Select + Top K Slider + Score Threshold Slider + Rerank Switch → ranked chunks + scores)+ "End-to-end query" panel(CRAG Switch + LLM Select → synthesis,reuses `/query/stream`)；Reranker dropdown lists only Cohere v4.0-pro + "None"(Voyage/ZeroEntropy dropped per ADR-0012;§5.5.4 not amended)+ NEW `lib/api/retrieval-test.ts`
- **Tests**:10 NEW(2 `test_retrieval.py` mode payload-shape + 8 `test_retrieval_test_endpoint.py`)→ **593 passed + 7 skipped**(was 583+7;0 regressions);ruff clean(`server.py` 18 pre-existing E402 from truststore-inject pattern NOT touched);`tsc --noEmit` EXIT_CODE=0;eslint clean on changed files
- **Browser smoke 受限** — local dev server's Azure backend has no seeded KB → KB-detail page can't render the tab there;`/admin/kb` list renders fine(page.tsx module loads)。Coverage relies on tsc/eslint + the `test_retrieval_test_endpoint.py` route/schema/error-path tests + the `test_retrieval.py` mode payload-shape tests。RetrievalTab interactive browser smoke deferred until a KB is seeded in a reachable dev backend
- **`(this docs commit)`** `docs(architecture)` — audit §10 ledger #25-26 + 偏差 #5 → **FULLY CLOSED**(5/5 major drifts closed;only #1 sample-PDF un-skip pending Chris)+ ADR-0021 §Implementation Deliverables checkboxes ticked + this progress entry
- Pre-existing `frontend/app/admin/page.tsx` unused-import lint error(`CardTitle`)— still NOT touched(out of scope per Karpathy §1.3;noted for W17+ housekeeping)

### ADR-0021 follow-up — RetrievalTab browser smoke executed + local-dev CORS + dev-server policy(Day 1 cont, 2026-05-10)

> Triggered by user request to run the RetrievalTab browser smoke that was deferred above (line ~157). Needed a local backend with a seeded KB; the only blocker was missing CORS for local cross-origin frontend → backend — a latent local-dev gap per setup.md §8.5.

- **`84d030e`** `fix(api)` — `backend/api/server.py` adds `CORSMiddleware`(`allow_origin_regex` `http://localhost:\d+`,outermost so preflight short-circuits before rate-limit/audit;production domain won't match → no-op)。Verified at runtime(OPTIONS preflight returns expected `Access-Control-*` headers)+ backend pytest **593 passed / 7 skipped**(0 regressions vs ADR-0021 baseline);ruff `server.py` now 19 E402(+1 of the existing truststore-ordering pattern — no clean alternative since the new import must also follow `truststore.inject_into_ssl()`)
- **`3a509c4`** `docs(ai-assistant)` — `01-session-start.md §13` dev-server policy amendment(per user directive):moved「唔啟動長期 server process」out of「唔做」into「必做」as positive authorization — AI may start/restart local services(uvicorn / next dev / docker-compose / Azurite),prefer background mode;destructive service ops(delete volume / `down -v` / kill the user's own process)still require confirmation。Update-history row added。CLAUDE.md §14 micro-tuning scope(not an H1–H6 change)
- **Backend live smoke**(local uvicorn + root `.env` real Azure creds + `FEATURE_AUTH_MOCK=true` + seeded `kb_id=drive_user_manuals` → `ekp-kb-drive-v1`)— 11 curl cases PASS against real Azure AI Search + Cohere v4.0-pro:hybrid+rerank(Cohere scores 0.876/0.863/…);vector(faster — no semantic config);fulltext(`embed_latency_ms=0`,`score_threshold` ignored,`queryType=simple`);rerank=false(`reranker=none`,raw RRF scores 0.033/…,different ordering);`score_threshold=0.85`(filters 5→2,ranks re-numbered #1 #2);empty query → 422;`mode=semantic` → 422;`top_k=99` → 422;unknown kb → 404;no auth → 401
- **Browser smoke**(local `next dev -p 3002` → `localhost:8000`,Playwright,user's :3001 instance untouched)— `/admin/kb` lists the seeded KB → KB-detail page loads(the earlier "Loading KB…" was simply the missing seeded KB, **not a code bug**)→ **Retrieval Testing tab renders fully**(Test-query textbox / Search-mode Select 3 options / Top-K slider=5 / Score-threshold slider / Rerank switch + "Cohere v4.0-pro (Tier 1 locked — ADR-0012 / Q21)" + End-to-end-query panel with CRAG switch + LLM Select)→ Full-Text mode **disables** the threshold slider + flips its value to `n/a` + helper to "BM25 scores have no 0–1 range — threshold disabled" → **Test retrieval runs end-to-end** → summary line(`mode` / `reranker` / `hits` / per-stage embed·search·rerank·total ms)+ 5 ranked chunks(rank / chunk title / doc title / section-path breadcrumb / score badge descending / preview / chunk_id — real D365 F&O AP·FA manual content)→ Rerank-off re-run flips `reranker→none` + drops the rerank-ms line + conditional copy("Final chunk count." vs "(after rerank).") + raw RRF scores + different doc ordering。Pixel-diff baseline re-capture still deferred → W16 F4(R8 Playwright-binary CDN block)
- Line ~157 above "Browser smoke 受限" → **superseded** — RetrievalTab smoke now executed against a local backend
- **`(this docs commit)`** `docs(planning)` — this progress sub-entry

---

## Day 2 → Day 10 — _(W16 D2-D10 placeholders;F1-F4 sequence post Track A IT cred trigger;F5 closeout absorbed Day 1 per E.1 same-day collapse)_

_(W16 D2+ entries deferred until F1 Track A IT cred trigger received;F5 partial-active closeout sub-entries appended Day 1 above as commits land)_

---

## Retro(填於 W16 D10 末)

### What worked
_(W16 D10 末 fill — Track A IT cred consumption smoothness / Beta cohort rollout reception / backend stub closure cascade efficiency / user smoke first run W12+W13+W14+W15 manual smoke backlog clearance)_

### What didn't
_(W16 D10 末 fill — friction points / blockers / unexpected complexity)_

### Surprises / discoveries
_(W16 D10 末 fill — non-obvious findings about Track A IT process / Beta cohort feedback / backend implementation gotchas / Playwright first run learnings)_

### Decisions
_(W16 D10 末 fill — R-B1 closure verification verdict / cohort feedback action items / backend stub priority adjustment / CO_W14_process_grep_verify pre-active flip checklist refinement)_

### Carry-overs to W17+
_(W16 D10 末 fill — items deferred to W17+;categorize:Beta cohort expansion / persistent backing migration / Tier 2 triggers / a11y polish backlog / interactive E2E expansion)_

### Time tracking
_(W16 D10 末 fill — actual hours per F1-F5 vs estimated ~10 working days;non same-day collapse fit per Beta deploy stakeholder + cohort coordination dependencies — calibration data point distinct from W12-W15 UI sprint cycle pattern)_

### Spec ref alignment
_(W16 D10 末 fill — verify all W16 deliverables trace back to architecture.md v6 §6.4 Production launch sequencing + W11 plan F1+F2+F3 + W6 demo-prep.md beta-plan-v1 + ADR-0014/0015/0016 spec citations)_

---

**Lifecycle reminder**:呢份 progress.md 屬 phase journal,daily entries + retro 必須 commit incrementally per R2。Day 0 setup entry 屬 W15 D5 F5 closeout cascade carry-over prep。**W16 D1 active implementation start** = post Track A IT cred populate event trigger received + R-B1 closure verification ready(non same-day collapse fit per real Beta deploy timing dependencies)。
