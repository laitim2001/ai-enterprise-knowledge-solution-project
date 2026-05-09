---
phase: W16-beta-deploy
name: "Beta deploy production launch resume — post Tier 1 UI sprint cycle FINAL closure (Track A IT cred event-triggered + R-B1 closure + 25% cohort rollout activation + backend stub closure cascade + Playwright E2E first user smoke + cumulative R8 mitigation Beta hardening)"
sprint_week: W16
start_date: 2026-07-14             # tentative — assumes W15 closeout 2026-07-11 + Track A IT cred populate event trigger
end_date: 2026-07-25               # ~10 working days (Beta deploy with stakeholder + cohort coordination dependencies; non same-day collapse fit)
status: active                     # active 2026-05-10 — F5 partial-active flip per Path A pivot (F1-F4 preserved draft pending Track A IT cred populate event trigger + R-B1 closure)
spec_refs:
  - architecture.md v6 §6.4              # Production launch sequencing
  - architecture.md v6 §13.12            # v5.1→v6 amendment (Tier 1 UI complete prerequisite)
  - ADR-0014                             # Hybrid auth (Beta production wiring trigger)
  - ADR-0015                             # UI Tier 1 expansion 9 views (W15 closeout complete)
  - ADR-0016                             # Password hash scrypt (Beta hardening preserved)
  - W6-final-eval-demo/artifacts/demo-prep.md       # Beta plan v1
  - W11-staged-rollout-25/plan.md F1+F2+F3          # Track A IT cred + 25% rollout + daily monitor
prior_phase: W15-polish-closeout
related_artifacts:
  - docs/01-planning/W15-polish-closeout/progress.md     # W15 retro § Carry-overs to W16+ Beta deploy + Tier 1 UI sprint cycle FINAL retrospective
  - docs/01-planning/W11-staged-rollout-25/progress.md   # W11+ Track A IT cred event trigger + R-B1 closure pre-conditions
  - docs/03-implementation/beta-plan-v1.md               # W6 D5 Beta plan v1 (cohort definitions + rollout sequence)
  - frontend/tests/e2e/                                   # W15 D4 Playwright E2E + pixel diff baseline harness ready for first user smoke
  - frontend/components/error/error-boundary.tsx          # W15 D3 entire frontend oklch=0 MILESTONE preserved
---

# Phase W16 — Beta deploy production launch resume(post Tier 1 UI sprint cycle FINAL closure)

> **Plan version**:1.0(draft 2026-06-10 W15 D5 F5 closeout cascade — rolling JIT per CLAUDE.md §10 R1)
> **Owner**:Chris(Tech Lead + stakeholder)+ AI(implementation + backend cascade)
> **Approved by**:_(pending W16 D1 active flip post Track A IT cred populate event trigger + R-B1 closure)_

---

## 1. Scope(rolling-JIT W15 D5 F5 closeout draft per pivot momentum)

W16 = **Beta deploy production launch resume sprint** — first sprint post Tier 1 UI sprint cycle FINAL closure(W12+W13+W14+W15)。Goals:

- **Track A IT cred consumption + R-B1 closure** — `.env.production` + Azure subscription IDs + Cohere Marketplace billing wiring per W6 demo-prep.md beta-plan-v1;risk register live update;blocked W11+ status flip
- **W12+W13+W14+W15 user smoke 3-step workflow first execution** — `npx playwright install chromium` + `pnpm test:e2e:update-snapshots` + `pnpm test:e2e`(systematic subsume of cumulative 4-sprint manual smoke deferred backlog per W15 F4 baseline harness ready)
- **25% Beta cohort rollout activation** per W6 demo-prep.md beta-plan-v1 cohort definitions(internal RAPO + 1-2 friendly departments per Q7 Resolved)
- **Daily metric monitor** — R@5 + Faithfulness + Correctness + Image Association threshold tracking;Q15 first weekly signal report
- **Backend stub closure cascade** — CO_W14_F3a-c(KB documents/chunks listing + name PATCH + reindex/delete)+ CO_W15_F1_backend(Eval run/shootout)+ CO_W15_F2_backend(Debug trace Langfuse correlation)= 4 separate 501 endpoints W3+/W4 implementations
- **R8 corp proxy mitigation pattern formalization** — ADR-0017 trigger if Playwright browser CDN blocks user smoke OR cumulative pattern reaches 5+ occurrences

**Out of W16 scope**(absorbed by W17+):
- Tier 2 features per architecture.md v6 §11(GraphRAG / multi-agent / multi-tenancy)
- Forgot password / 2FA / OAuth providers
- Real Langfuse trace integration beyond stub URL pattern(post-Beta proxy resolution)
- Beta cohort expansion beyond 25%(W17+ rollout cascade)
- Persistent backing migration Postgres/Cosmos DB(CO18 Beta hardening)

**Pre-condition for W16 promotion**(等 W16 D1 active flip):
- W15 D5 F5 closeout PASS WITH SMOKE-USER-DEFERRED CAVEAT verdict landed
- Tier 1 UI sprint cycle FINAL marker landed(architecture.md v6 §13.12 amendment 完整 implemented)
- **Track A IT cred populate event trigger received**(blocking external dependency per W11 retro CO16)
- **R-B1 closure verification ready**(risk register live update prerequisite)

## 2. Deliverables(F1-F5 thin skeleton — detail at W16 D1 active flip)

### F1 — Track A IT cred consumption + R-B1 closure verification

- **Component(s)**:**C12** DevOps & Infra + **C03** Indexing Service(Azure subscription wiring)
- **Spec ref**:W11 plan F1 + W6 demo-prep.md beta-plan-v1
- **Pre-condition**:Track A IT cred populate event trigger
- **Acceptance criteria**(detail at W16 D1 active flip)
- **Effort estimate**:2 days(W16 D1-D2)

### F2 — 25% Beta cohort rollout activation

- **Component(s)**:cross-cutting(C09 + C10 + C11)
- **Spec ref**:W6 demo-prep.md beta-plan-v1 cohort definitions + W11 plan F2
- **Pre-condition**:F1 IT cred + Track A populate
- **Acceptance criteria**(detail at W16 D1 active flip)
- **Effort estimate**:2 days(W16 D3-D4)

### F3 — Daily metric monitor + Q15 first weekly signal report

- **Component(s)**:**C06** Eval Framework + **C07** Observability Stack
- **Spec ref**:architecture.md v6 §6.4 + W11 plan F3 + W11 retro CO19
- **Pre-condition**:F1 + F2 cohort live
- **Acceptance criteria**(detail at W16 D1 active flip)
- **Effort estimate**:1 day(W16 D5)

### F4 — User smoke first run(Playwright E2E baseline capture + browser binary install)

- **Component(s)**:**C12** DevOps & Infra(test harness)
- **Spec ref**:W15 D4 F4 Playwright E2E + pixel diff baseline harness `tests/e2e/README.md` 3-step workflow
- **Pre-condition**:Browser binary install via `npx playwright install chromium`(R8 mitigation if needed via personal Azure dev tier per W11 retro CO17 OR ADR-0017 trigger if blocks)
- **Acceptance criteria**:
  - F4.1 Browser binary install successful(or ADR-0017 trigger documented)
  - F4.2 `pnpm test:e2e:update-snapshots` captures 5 pixel diff baseline screenshots + commits to `tests/e2e/visual-baseline.spec.ts-snapshots/`
  - F4.3 `pnpm test:e2e` 13 tests pass + 0 regression
  - F4.4 W12+W13+W14+W15 manual smoke deferred backlog systematic subsume target actualized
- **Effort estimate**:1 day(W16 D6)

### F5 — Backend stub closure cascade

- **Component(s)**:**C02** KB Manager + **C06** Eval Framework + **C07** Observability Stack
- **Spec ref**:W14 retro CO_F3a-c + W15 retro CO_W15_F1_backend + CO_W15_F2_backend
- **Pre-condition**:**relaxed for F5 partial-active flip 2026-05-10**(F1+F2 cohort live no longer prereq for backend stub closure;pure backend implementation 可 proceed pre-Track-A trigger per Path A scope decision)
- **Acceptance criteria**(adjusted post grep verification 2026-05-10 per CO_W14_process_grep_verify FORMALIZED):
  - F5.1 CO_F3a backend `GET /kb/{id}/documents` + `GET /kb/{id}/documents/{id}/chunks` listing implementation(replace 501 stubs in `documents.py:8` + `chunks.py:16`;Azure AI Search index query by kb_id + doc_id filter)
  - F5.2 CO_F3b backend **新 endpoint** `PATCH /kb/{kb_id}` body={name, description}(per Decision A.1 separation of concern;`PATCH /kb/{id}/settings` 仍 reserve KbConfig only;new endpoint NOT replace existing settings PATCH)
  - F5.3 CO_F3c backend **新 endpoint** `POST /kb/{kb_id}/reindex` per-KB level(NOT pre-existing — only per-doc reindex `POST /kb/{id}/documents/{id}/reindex` in `documents.py:41`);`DELETE /kb/{kb_id}` already implemented in-memory `kb.py:45`(Azure AI Search index drop + per-KB Blob container drop **defer Track A IT cred trigger** per Decision B.1;in-memory delete cleanup preserved baseline)
  - F5.4 CO_W15_F1_backend `POST /eval/run` + `POST /eval/shootout` W4 implementation per Decision C.1 full implementation(both endpoints;wire `backend/eval/runner.py` + `ragas_runner.py` modules;heavy work)
  - F5.5 CO_W15_F2_backend `GET /debug/trace/{trace_id}` W3+ Langfuse correlation per Decision D.2 full SDK integration(Langfuse client query + stage data correlation;`/debug/trace` UNBLOCKS ADR-0020 frontend Session 2 Drift #3 V6 9-stage)
  - F5.x CO_W15_F1_eval_set_v1 file existence verify — **finding**:`docs/eval-set-v1.yaml` does NOT exist;`docs/eval-set-v1-draft.yaml` exists(draft only)→ **W17+ candidate**(eval-set-v1 finalization post Beta cohort real-query collection per Q6 + Q15 trigger)
  - F5.x CO_W15_F2_langfuse_url `NEXT_PUBLIC_LANGFUSE_URL` Beta production endpoint env var configuration(Step 6 absorb)
- **Effort estimate**:**Path A E.1 ambitious single session ~ 1 day**(C.1 full eval implementation + D.2 full Langfuse SDK = heavy sub-items;session-collapse pattern per W12-W15 precedent)

## 3. Success Criteria(Phase Gate to W17+)

W16 phase Gate **PASS condition**(detail at W16 D1 active flip):
1. F1 Track A IT cred consumed + R-B1 closure verification landed
2. F2 25% Beta cohort rollout activation cascade complete
3. F3 Daily metric monitor + Q15 first weekly signal report
4. F4 User smoke first run successful + W12+W13+W14+W15 manual smoke backlog cleared
5. F5 Backend stub closure cascade(4 stub endpoints implemented)

W16 phase Gate **PARTIAL PASS** acceptable:
- F4.1 Browser binary install blocked by R8 → ADR-0017 trigger + personal Azure dev tier fallback per W11 retro CO17
- F5 backend stub closure partial(prioritize CO_F3a-c immediate Beta blocker > CO_W15_F1+F2 W4+W3+ implementation can defer to W17+)

W16 phase Gate **FAIL condition**:
- Track A IT cred populate event blocked beyond W16 D5
- R-B1 closure cannot proceed(persistent risk)
- Beta cohort rollout produces critical regression vs W6 baseline 4-metric

## 4. Risks(Phase-Specific)

| Risk | Likelihood | Impact | Mitigation |
|---|---|---|---|
| Track A IT cred populate event delayed | Medium | High | W16 D1 active flip blocked until trigger received;F1 acceptance criteria gate W16 progression |
| R8 corp proxy blocks Playwright browser CDN | Medium | Medium | ADR-0017 trigger candidate;personal Azure dev tier fallback per W11 retro CO17;in-network manual install via approved channels |
| Beta cohort feedback diverges from W6 baseline 4-metric | Medium | Medium | Daily metric monitor F3 + Q15 weekly signal report F3.5 catches drift;rollback flag-ready per beta-plan-v1 |
| Backend stub closure cascade scope expand | Low | Low | Karpathy §1.2 simplicity-first — prioritize CO_F3a-c immediate Beta blocker;CO_W15_F1+F2 can defer W17+ if scope expand |
| Cumulative R8 mitigation pattern reaches 5+ occurrences | Low | Low | ADR-0017 formalization triggered + general R8 mitigation pattern documented |

## 5. Day-by-Day Breakdown(rough — detail at W16 D1 active flip)

| Day | Date(tentative)| Focus |
|---|---|---|
| W16 D1 | 2026-07-14 | F1 Track A IT cred consumption begin + active flip + spec ref grep verification per CO_W14_process_grep_verify formalized |
| W16 D2 | 2026-07-15 | F1 R-B1 closure verification + risk register live update |
| W16 D3 | 2026-07-16 | F2 25% Beta cohort rollout activation begin |
| W16 D4 | 2026-07-17 | F2 cohort rollout cont + F3 daily metric monitor begin |
| W16 D5 | 2026-07-18 | F3 finalize + Q15 first weekly signal report |
| W16 D6 | 2026-07-21 | F4 user smoke first run + Playwright E2E baseline capture |
| W16 D7-D9 | 2026-07-22 → 2026-07-24 | F5 backend stub closure cascade |
| W16 D10 | 2026-07-25 | F5 finalize + W16 phase Gate closeout |

**Day-by-day caveat**:plan §5 dates tentative;Track A IT cred dependency timing affects entire W16 schedule;non same-day collapse fit per real Beta deploy stakeholder + cohort coordination dependencies。

## 6. Dependencies on Prior Phase

Carry-overs from `W15-polish-closeout/progress.md` retro § Carry-overs to W16+ Beta deploy(W15 D5 F5 closeout):

#### Immediate W16 D1 priority
- Track A IT cred consumption(F1 deliverable)
- R-B1 closure verification(F1 deliverable)
- W12+W13+W14+W15 user smoke 3-step workflow first execution(F4 deliverable)

#### Backend follow-ups immediate Beta hardening
- CO_F3a/b/c W14 backend listing/PATCH/danger zone(F5 deliverable)
- CO_W15_F1_backend Eval run/shootout(F5 deliverable)
- CO_W15_F1_eval_set_v1 file existence verify
- CO_W15_F2_backend Debug trace Langfuse correlation(F5 deliverable)
- CO_W15_F2_langfuse_url Beta production endpoint env var

#### Polish + a11y + test backlog Beta hardening(non-W16 priority;W17+ candidates)
- CO_W15_F3_aria_full_audit / CO_W15_F3_dark_mode_visual_verify / CO_W15_F4_browser_binaries / CO_W15_F4_baseline_capture / CO_W15_F4_vitest_baseline_gap / CO_W15_F4_interactive_flow_E2E

#### Process improvement formalization
- **CO_W14_process_grep_verify FORMALIZED** — Plan author "spec ref grep verification" step pre-R1 active flip checklist applied W16 D1 active flip(per W15 retro decision empirical signal 9 cumulative occurrences)

#### Inherited unchanged W11+W12+W13+W14
- CO_F5_refresh / CO_F5_cookie / CO_F6a-c W13 backend follow-ups
- CO16 Track A IT cred populate event(F1 dependency)
- CO17 AF3 + Personal Azure dev tier(ADR-0013 + ADR-0017 candidate)
- CO18 KB Manager + users_repo persistent backing(W17+ Beta hardening)
- CO19 F2.1-F2.4 25% rollout activation(W16 F2 deliverable)

## 7. Plan Changelog

| Date | Change | Reason | Approver |
|---|---|---|---|
| 2026-06-10 | Initial draft(W15 D5 F5 closeout cascade rolling-JIT)| Per CLAUDE.md §10 R1 rolling-JIT;W15 closeout cascade per F5.3 deliverable;W16 immediate scope = W15 retro Carry-overs to W16+ Beta deploy exact match;Tier 1 UI sprint cycle FINAL marker landed(architecture.md v6 §13.12 amendment 完整 implemented;ready for W16+ Beta deploy production launch per plan §F5.6) | Chris(stakeholder authorization same-session pivot momentum;W15 closeout PASS WITH SMOKE-USER-DEFERRED CAVEAT verdict landed)|
| 2026-05-10 | **F5 partial-active flip**(`status: draft → active` for F5 only;F1-F4 preserved draft pending Track A IT cred populate event trigger + R-B1 closure)+ acceptance criteria adjusted per CO_W14_process_grep_verify FORMALIZED 5-step findings + scope decisions A.1 + B.1 + C.1 + D.2 + E.1 | Per Path A pivot post user prompt 2026-05-10 — F5 backend stub closure cascade AI fully controllable scope(no external dep);grep verification surfaced 7 mismatches between W16 plan literal acceptance criteria and code reality(F5.2 endpoint design A.1 / F5.3 per-KB reindex new + DELETE Azure cleanup B.1 defer / F5.4 C.1 both endpoints / F5.5 D.2 full Langfuse SDK / F5.x eval-set-v1 W17+ candidate finding);scope decisions documented + acceptance criteria refined inline above;F1-F4 unchanged | AI(Path A pivot scope per user explicit 2026-05-10;Chris stakeholder authorization deferred to W16 D1 active flip post Track A IT cred trigger for F1-F4 sequence)|

---

**Lifecycle reminder**:呢份 plan `status=draft`(等 W16 D1 active flip post Track A IT cred populate event trigger)。重大 deviation 入第 7 節 changelog。Sister sprint W17+ phase folder **唔會** pre-create(per CLAUDE.md §10 R1 rolling-JIT — 每 phase kickoff 先建)。**CO_W14_process_grep_verify FORMALIZED** applied at W16 D1 active flip per W15 retro decision pre-active flip checklist(spec ref grep verification step)。
