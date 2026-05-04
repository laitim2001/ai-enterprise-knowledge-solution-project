---
phase: W06-final-eval-demo
name: "Azure 2-way Verify + Final Eval + Demo Prep + Beta Plan"
sprint_week: W6
start_date: 2026-05-29          # tentative — same Option-A 2-day-shift heuristic
end_date: 2026-06-04            # tentative,5 working days
status: draft                   # flipped to active when Chris W6 D1 sign-off + W5 D5 closeout PASS
spec_refs:
  - architecture.md §6.1 W6 row     # final eval + demo prep + Beta plan
  - architecture.md §6.3            # Gate 2 STRONG PASS upgrade path
  - architecture.md §3.2            # vendor lock + Q21 final pick
  - components/C04-retrieval.md     # Azure 2-way semantic ranker LIVE
  - components/C05-generation.md    # synthesizer prompt tuning candidate
  - components/C06-eval.md          # RAGAs full-corpus run
  - eval-methodology.md             # 4-metric definition + threshold
prior_phase: W05-optimization
---

# Phase W06 — Azure 2-way Verify + Final Eval + Demo Prep + Beta Plan

> **Plan version**:1.0(draft 2026-05-04 W5 D5 末 closeout batch — rolling JIT)
> **Owner**:Chris(Tech Lead)
> **Approved by**:_(pending Chris W5 D5 closeout sign-off + W6 kickoff approval)_

## 1. Scope

W06 closes the **POC phase**(Tier 1 12-week sprint W1-W6 portion)。**F1 = Azure 2-way 互換 verify**(W5 carry-over C1+C2)triggers Gate 2 STRONG PASS upgrade path:`Settings.reranker_kind=azure` swap + RAGAs subset=20 re-run vs Cohere baseline → 4-metric within-5pp 互換 evaluation。Cohere v4.0-pro pipeline 已 W5 D2 PARTIAL PASS;若 Azure ≥ 5pp better any metric → ADR-0012 trigger Q21 revisit;否則 Q21 final = Cohere v4.0-pro confirmed + Gate 2 STRONG PASS landed。

Same trigger 兼顧 **Bug I LIVE re-verify**(W5 carry-over C2)— ragas judge `max_completion_tokens=4096` floor 結構性 fix 已 W5 D4 landed + 7 unit tests,但 LIVE confirmation 留 W6 Azure 2-way subset=20 re-run 一齊驗。

W6 D2-D5 並行:**final eval full 55-query**(post Q14 SME chunk_id labeling cascade strict-mode RAGAs)+ **synthesizer prompt tuning**(answer_relevancy 0.841 borderline mitigation)+ **W4/W5 carry-overs LIVE smoke remainder**(C7 PPT E2E + C8 F5/F6/F7 LIVE Chris dev server)+ **demo prep**(visual identity + screenshot artifacts)+ **Beta plan stakeholder cycle**(Q7 Beta user + Q9 sensitivity + Q11 Entra ID + Q12 Tier 2 owner OQ resolve preparation)。

**Pre-condition for W6 promotion**:W5 D5 closeout PASS(structural + PARTIAL PASS Gate 2 LIVE)+ Chris kickoff sign-off + procurement carry-overs minimal(only Azure 2-way config swap + Chris SME chunk_id labeling cascade async)。Fail = HALT W6,carry W5 status forward 等 stakeholder review。

**Sprint week origin**:[`architecture.md` §6.1 W6](../../architecture.md)

## 2. Deliverables(F1-F6)

### F1 — Azure 2-way 互換 verify + Gate 2 STRONG PASS upgrade(W5 C1+C2 close)

- **Component(s)**:**C04** Retrieval(Azure semantic ranker LIVE)+ **C06** Eval(RAGAs)+ **C05** Generation(verdict downstream)
- **Spec ref**:`architecture.md §6.3 Gate 2 verdict policy`,`W4 plan §F10 fallback`,`W5 D2 progress F1.8`
- **OQ deps**:Q21 tentatively Resolved(Cohere v4.0-pro;W6 final post Azure verify)+ Q5 Resolved(Path A + v4.0-pro accept)
- **Acceptance criteria**:
  - F1.1 `Settings.reranker_kind=azure` swap(.env override or default config update for this run only)
  - F1.2 `scripts/run_ragas_eval.py --subset 20` LIVE re-run with Azure semantic ranker pipeline → emit 4-metric report `reports/ragas-azure-subset20.json`
  - F1.3 Cross-reference `reports/ragas-cohere-subset20.json`(W5 D2 baseline)vs `reports/ragas-azure-subset20.json`(F1.2)→ 4-metric within-5pp 互換 evaluation per metric
  - F1.4 Verdict landed:
    - **Azure 4-metric within ±5pp of Cohere baseline** → Gate 2 STRONG PASS upgrade;Q21 final = `Cohere v4.0-pro`(no swap rationale);ADR-0012 reservation released
    - **Azure ≥ 5pp better any metric** → ADR-0012 trigger:Q21 revisit;若 Azure overall lift > 5pp → switch reranker_kind=azure default + architecture.md §3.2 amendment "Azure built-in semantic ranker" path
    - **Azure ≥ 5pp worse any metric** → Cohere v4.0-pro reaffirmed final;ADR-0012 reservation released;document lower-bound Azure lift evidence
  - F1.5 Bug I LIVE re-verify:F1.2 same run validates `max_completion_tokens=4096` floor — 0/20 errored expected(W5 D2 had 2/20 due to legacy ~1024 limit)
  - F1.6 Q5 + Q21 follow-up note in `decision-form.md`(final reranker pick + Gate 2 STRONG PASS verdict + Bug I LIVE confirm)
  - F1.7 architecture.md §3.2 vendor lock 行 + §6.3 Gate 2 verdict 行 amendment ticket — stakeholder approval cycle 准備好 narrative for vNext increment
- **Effort estimate**:1.5h(impl trivial settings swap;LIVE run wall clock ~25 min;cross-reference analysis 0.5h)
- **Owner**:AI(driver runs + cross-reference)+ Chris(stakeholder approval cycle for architecture.md amendment)
- **Cost expected**:~$15-25 USD(judge LLM × 4 metric × 20 queries × Azure pipeline)— same shape as W5 D2 Phase 1
- **Blocking**:F2-F6 conditional on F1 verdict outcome path

### F2 — Final eval full-corpus(post Chris SME chunk_id labeling cascade strict-mode RAGAs)

- **Component(s)**:**C06** Eval(RAGAs)+ **C04** Retrieval(strict-mode evaluation)
- **Spec ref**:`W4 plan §F4`,`W5 retro carry-over C7`,`eval-methodology.md`
- **OQ deps**:Q14 SME labeling cascade(Chris async;target ≥ 45/55 validated)
- **Acceptance criteria**:
  - F2.1 Chris SME chunk_id labeling Q001-Q030 + Q036-Q055 → ≥ 45/55 queries `validated: true` per W4 plan §3 G6
  - F2.2 `eval-set-v1-draft.yaml` promoted → `eval-set-v1.yaml`(remove `-draft` suffix per W4 §F4 acceptance)
  - F2.3 RAGAs full subset=55(strict-mode where chunk_ids labeled,keyword fallback otherwise)against winning reranker(Cohere v4.0-pro per F1 verdict)→ `reports/ragas-final-v1.json`
  - F2.4 Aggregate vs W5 D2 subset=20 baseline 比較;若 statistically consistent(within ±5% per metric)→ Tier 1 quality baseline confirmed
- **Effort estimate**:1h(AI analyse;Chris labeling unbounded async)
- **Owner**:Chris(SME labeling)+ AI(driver runs + analysis)
- **Cost expected**:~$30-50 USD(55 queries × 4-metric judge LLM)
- **Conditional**:Chris labeling cascade complete(target W6 D1-D2);若 slip → defer Tier 2

### F3 — Synthesizer prompt tuning(answer_relevancy 0.841 borderline mitigation,W5 retro C4 close)

- **Component(s)**:**C05** Generation(prompt_builder)
- **Spec ref**:`W5 D2 progress F1.7`,`W5 retro carry-over C4`,`components/C05-generation.md §1 prompt design`
- **OQ deps**:none
- **Acceptance criteria**:
  - F3.1 Analyse F1.7(W5 D2)+ F1(W6)answer_relevancy distribution per query → identify systematic verbose pattern source(answer length cap missing? response format too open?)
  - F3.2 Prompt tweak candidates(test in isolation):answer length cap directive(e.g. "≤ 250 words")/ question-direct format directive(e.g. "Lead with direct answer in first sentence")/ structure constraint(e.g. "If multi-step, list as numbered steps")
  - F3.3 A/B subset=10 RAGAs run on Cohere v4.0-pro pipeline(baseline prompt vs tweaked prompt)→ delta evaluation
  - F3.4 If tweaked prompt + answer_relevancy ≥ 0.85 → land in `prompt_builder.SYSTEM_PROMPT`;若 ≤ 0.85 但 ≥ 0.83 + faith/prec/recall 不退步 → keep tweaked as marginal improvement;若 regression → revert
- **Effort estimate**:1h impl + ~$10-20 USD A/B run cost
- **Owner**:AI
- **Conditional**:non-blocking F1 verdict;parallel track

### F4 — W4/W5 carry-overs LIVE smoke remainder(C5 + C6)

- **Component(s)**:**C01** Ingestion(PPT E2E)+ **C05** Generation(GPT-5.5 latency)+ **C08** API + **C10** Chat UI(SSE smoke + screenshots)
- **Spec ref**:`W4 plan §F5`,`W5 retro carry-over C6`
- **OQ deps**:Chris dev server availability
- **Acceptance criteria**:
  - F4.1 W4 C7 PPT orchestrator E2E smoke:`scripts/run_pptx_ingest_sanity.py` against 3 W3 D1 後段 PPT samples → end-to-end ingest → chunks visible via `/kb/{id}/chunks`
  - F4.2 W4 C8 F5 Cohere lift summary log + decision-form Q5 follow-up note(post W6 F1 LIVE run output incremental)
  - F4.3 W4 C8 F6 GPT-5.5 latency baseline:p50 / p95 / per-query cost USD documented(Chris dev server + 5 real query smoke)
  - F4.4 W4 C8 F7 Chat UI 1-2 screenshots in W6 progress backfill(Chris dev server + browser smoke)
- **Effort estimate**:1h(post Chris dev server smoke runs)
- **Owner**:Chris(dev server + smoke)+ AI(documentation)
- **Conditional**:non-blocking F1;parallel track

### F5 — Demo prep + Beta plan(architecture.md §6.1 W6 row "Beta plan")

- **Component(s)**:cross-cutting governance + **C09** Admin Console UI + **C10** Chat UI
- **Spec ref**:`architecture.md §6.1 W6 row`,`§6.2 Demo readiness criteria`
- **OQ deps**:Q7 Beta user source + Q9 Sensitivity / CMK + Q10 Visual identity + Q11 Entra ID + Q12 Tier 2 owner — 全 Open;呢個 deliverable 推進 stakeholder cycle resolution preparation
- **Acceptance criteria**:
  - F5.1 Demo script narrative draft(15-min demo flow):use case 1(Drive Manual)+ ingestion E2E + query w/ citation + answer + Pipeline wizard + retro-discussion
  - F5.2 Stakeholder Q&A briefing pack(common questions + pre-canned answers + risk slides)
  - F5.3 Beta plan draft:`docs/03-implementation/beta-plan-v1.md`(scope + timeline + Q7-Q12 OQ resolution dependencies + risk register update)
  - F5.4 Demo screenshots / GIF artifacts(post F4.4)
- **Effort estimate**:2h
- **Owner**:AI(draft)+ Chris(approve;stakeholder review cycle setup)
- **Conditional**:non-blocking F1;parallel track

### F6 — Phase Gate 2 closeout(STRONG PASS or PARTIAL PASS confirmed)+ W6 retro + W7 kickoff prep

- **Component(s)**:cross-cutting governance
- **Spec ref**:`architecture.md §6.1 W7-W8 row`,`PROCESS.md §2.3 closeout`
- **OQ deps**:F1 verdict + F2 final eval + F3 prompt tuning outcomes + F5 Beta plan
- **Acceptance criteria**:
  - F6.1 Gate 2 final verdict landed(STRONG PASS upgrade OR PARTIAL PASS confirmed)+ documented in `architecture.md §6.3` decision row(stakeholder approval cycle)
  - F6.2 W06 progress.md retro 7 sections complete + Phase Gate verdict + carry-overs to W7-W8 + ADR triggers
  - F6.3 W07 phase folder kickoff:`docs/01-planning/W07-beta-deploy/{plan,checklist,progress}.md` draft(W7 = Microsoft Entra ID + rate limiting + React polish + Beta deploy per architecture.md §6.1 W7 row)
  - F6.4 W06 progress.md frontmatter status flipped to `closed`
  - F6.5 OQ Q21(reranker final)+ Q5 + relevant other Q resolution sync to `decision-form.md`
- **Effort estimate**:1h
- **Owner**:AI(draft)+ Chris(approve)

## 3. Success Criteria(Phase Gate to W7-W8)

| # | Criterion | Target | Measure | Block W7? |
|---|---|---|---|---|
| G1 | F1 Azure 2-way 互換 verify landed(STRONG PASS upgrade OR Cohere reaffirmed)| landed | F1.4 | **Yes** |
| G2 | F2 final eval full-corpus(or partial if Chris labeling slips)| ≥ 45/55 evaluable | F2.3 | No(strict-mode partial OK) |
| G3 | F3 synthesizer prompt tuning(land tweak OR document defer Tier 2)| decision landed | F3.4 | No(non-blocking) |
| G4 | F4 W4/W5 LIVE smoke remainder closed(C7 PPT + C8 F5/F6/F7) | landed | F4.1-F4.4 | No(carry W7+ if Chris dev server bottleneck) |
| G5 | F5 Demo prep + Beta plan draft committed | committed | F5.1-F5.3 | Yes |
| G6 | Backend ruff + frontend lint + type-check 0 errors | All clean | local run | Yes |
| G7 | OQ Q21 final Resolved | Resolved | decision-form.md | Yes |

## 4. Risks(Phase-Specific)

| # | Risk | Likelihood | Impact | Mitigation |
|---|---|---|---|---|
| R1 | Azure semantic 2-way ≥ 5pp better than Cohere → reranker swap | Low | Medium | ADR-0012 trigger + architecture.md §3.2 amendment;keyword-mode F1.6 already showed parity → unlikely outcome |
| R2 | Q14 chunk_id labeling slips(blocks F2 strict-mode) | Medium | Medium | Keyword-mode fallback acceptable for F2 partial verdict;backfill W7+ if SME cycles slip |
| R3 | F3 prompt tuning regression(answer_relevancy gain but faith/prec/recall drop) | Medium | Medium | A/B subset=10 cheaper validation BEFORE landing;revert if regression |
| R4 | Bug I LIVE re-verify reveals NEW ragas-GPT-5 incompatibility(beyond max_tokens / temperature / logprobs) | Low | Low | Wrapper `_DROP_PARAMS` already defensive(logprobs/top_logprobs);extend list if surfaced;long-term ragas upstream upgrade |
| R5 | Chris dev server bottleneck blocks F4 carry-over closure | High | Low | Defer to W7 polish window;non-blocking Gate 2 |
| R6 | Stakeholder review cycle for architecture.md §3.2 amendment exceeds W6 timeline(v3.5 → v4.0-pro decision lock) | Medium | Low | Inline document in W6 retro;amendment proposal queued for stakeholder cycle;can land Tier 2 kickoff window |
| R7 | R8 Ricoh corp proxy reactivation during W6 cloud-heavy work | High | High | Same mitigation as W2/W3/W4/W5:disconnect GlobalProtect VPN;pre-flight check |

## 5. Day-by-Day Breakdown(rough)

| Day | Date | Focus | Deliverables targeted |
|---|---|---|---|
| D1 | 2026-05-29 | F1 Azure 2-way LIVE verify + Gate 2 verdict | F1 |
| D2 | 2026-05-30 | F2 Chris labeling cascade kickoff + F3 prompt tuning A/B(if F1 PASS)| F2, F3 |
| D3 | 2026-05-31 | F2 strict-mode RAGAs full + F4 carry-overs LIVE smoke(Chris)| F2, F4 |
| D4 | 2026-06-01 | F5 demo prep + Beta plan draft + F4 documentation | F5, F4 |
| D5 | 2026-06-02 | F6 Gate 2 closeout + W6 retro + W7 kickoff prep | F6 |

## 6. Dependencies on Prior Phase

Carry-overs from `W05-optimization/progress.md` retro:
- **W5 C1** Azure 2-way verify → **F1**
- **W5 C2** Bug I LIVE re-verify → **F1.5**(same trigger as F1.2)
- **W5 C3** RAGAs evaluator REFUSAL_PHRASE skip enhancement → optional W6 polish
- **W5 C4** answer_relevancy GPT-5.5 verbose mitigation → **F3**
- **W5 C5** F3 L3 routing conditional → defer post-F1 STRONG PASS landing(若 W6 D1 STRONG PASS → W6 D2-D5 fork to L3 implementation)
- **W5 C6** W4 carry-overs LIVE smoke remainder → **F4**
- **W5 C7** Q14 SME labeling cascade → **F2**
- **W5 C8** architecture.md §3.2 amendment stakeholder cycle → **F6.1**
- **W5 C9** Plan estimate calibration LIVE-heavy 1.5x / static-heavy 0.3-0.5x → applied W6 plan §2 effort estimates
- **W5 C10** Tier 2 reconsideration list(Voyage + ZeroEntropy + ragas upgrade + per-KB)→ **Tier 2 kickoff doc(post W6 / Tier 2 phase)**

## 7. Plan Changelog

| Date | Change | Reason | Approver |
|---|---|---|---|
| 2026-05-04 | Initial draft(W5 D5 末 closeout batch)| Per PROCESS.md §2.3 rolling-JIT kickoff;status=draft pending Chris W5 D5 closeout sign-off + W6 kickoff approval | Chris(pending approve to flip active) |

---

**Lifecycle reminder**:呢份 plan `status=draft`(等 Chris W6 D1 sign-off flip `active`)。重大 deviation 入第 7 節 changelog。
