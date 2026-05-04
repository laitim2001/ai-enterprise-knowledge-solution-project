---
phase: W05-optimization
name: "Gate 2 LIVE Close + Conditional Optimization + L3 Routing(if Gate 2 PASS)"
sprint_week: W5
start_date: 2026-05-22          # tentative — same Option-A 2-day-shift heuristic as W2/W3/W4 if Chris confirms; otherwise 2026-05-26 per architecture.md §6.1 original schedule
end_date: 2026-05-28            # tentative,5 working days
status: closed                  # flipped 2026-05-04 W5 D5 末 closeout — Gate 2 LIVE verdict PARTIAL PASS;Cohere v4.0-pro tentatively Q21 Resolved;Azure 2-way 互換 carry-over W6 Gate 3 demo prep per W4 plan §F10 fallback;L2 CRAG NOT dropped(drop-L2 trigger 4-metric within-5pp 互換 FAIL 未觸發)
spec_refs:
  - architecture.md §6.1 W5 row     # L3 routing conditional + optimization scope
  - architecture.md §6.3            # Gate 2 verdict policy
  - architecture.md §3.5            # CRAG L2 → L3 progression
  - components/C04-retrieval.md     # reranker per-KB field reconsideration
  - components/C05-generation.md    # CRAG threshold tuning
  - components/C06-eval.md          # RAGAs LIVE eval + 4-metric Gate 2 close
  - eval-methodology.md             # 4-metric definition + threshold
prior_phase: W04-crag-eval-shootout
---

# Phase W05 — Gate 2 LIVE Close + Conditional Optimization + L3 Routing(if Gate 2 PASS)

> **Plan version**:1.0(draft 2026-05-04 W4 D5 末 closeout batch — rolling JIT)
> **Owner**:Chris(Tech Lead)
> **Approved by**:_(pending Chris W4 D5 closeout sign-off + W5 kickoff approval + procurement landing trigger)_

## 1. Scope

W05 closes the **Gate 2 LIVE verdict deferred from W4 D5** then branches into conditional optimization。**F1 = Gate 2 LIVE close**(blocking gate for W5 D2-D5 scope determination)wires 2 procurement chains(simplified per W5 D1 user decision per Karpathy §1.2):**Cohere Marketplace endpoint populate(W4 C2)** + **eval-set chunk_id labeling per Q14 SME cascade(W4 C5)**。Once F1 lands LIVE 4-metric within-5pp 互換 verdict,W5 D2-D5 fork:**PASS** = continue Tier 1 W5+ optimization(L3 routing conditional + CRAG threshold fine-tune + reranker per-KB field if sticky + W4 C8 LIVE smoke remainder closure)/ **FAIL** = drop L2 CRAG → baseline-only scope per architecture.md §6.3,W5 D2-D5 = ADR-0012 record + W4 carry-overs cleanup + W6 demo prep early-start。

**Voyage + ZeroEntropy DROPPED**(W4 C3)per W5 D1 Karpathy §1.2 simplicity-first decision:Cohere v3.5(H2 LOCKED W3 baseline)+ Azure built-in semantic ranker(S1 SKU bundled,no procurement)2-way comparison **already satisfies** Gate 2 4-metric within-5pp 互換 verdict policy per architecture.md §6.3。Voyage / ZeroEntropy 屬於 alternative candidates,procurement burden(non-Azure path + monthly billing)+ low marginal value(Cohere 通常 +10-20% R@5 lift over hybrid baseline,satisfies Tier 1 quality)= drop pragmatically。W4 D3 落地嘅 `VoyageReranker` + `ZeroEntropyReranker` class + 21 unit tests **preserved as future-proof scaffold**(Tier 2 / Beta+ 將來 evaluate;`run_reranker_shootout.py` skip-row fallback automatically handles SKIPPED rows,driver-side無需改動)。

**Pre-condition for W5 promotion**:W4 D5 closeout PASS(structural)+ Chris kickoff sign-off + procurement landing(at minimum Cohere endpoint populate per Q5 Path A Marketplace OR Path B `https://api.cohere.com` direct;Azure semantic config ekp-semantic-default verify on `ekp-kb-drive-v1` index — non-procurement Chris index ops。Without Cohere endpoint AND Azure semantic config,partial-shootout reduces to hybrid-only baseline only,Gate 2 verdict cannot land per W4 plan §F10 fallback)。Fail = HALT W5,carry W4 status forward 等 procurement landing。

**Sprint week origin**:[`architecture.md` §6.1 W5](../../architecture.md)

## 2. Deliverables(F1-F6)

### F1 — Gate 2 LIVE verdict close(blocking gate)

- **Component(s)**:**C04** Retrieval(reranker shootout)+ **C06** Eval(RAGAs)+ **C05** Generation(CRAG verdict downstream)
- **Spec ref**:`architecture.md §6.3 Gate 2`,`W4 plan §F10 fallback path`,`W4 progress retro §Carry-overs C1-C5`
- **OQ deps**:Q5 Resolved(Cohere Path A)+ Q14 SME labeler chain(Chris)+ Q21 reranker final pick deferred to F1 outcome
- **Acceptance criteria**:
  - F1.1 Cohere `.env` endpoint populate(Chris signoff)— Path A `cohere_endpoint=https://<deployment>.<region>.models.ai.azure.com` OR Path B `cohere_endpoint=https://api.cohere.com` + `cohere_procurement_path=B`。`cohere_api_key` 已 W3 D1 後段 populated per Q5
  - F1.2 ~~Voyage + ZeroEntropy api keys~~ **DROPPED W5 D1 per Karpathy §1.2** — Cohere + Azure semantic 2-way 已 satisfies Gate 2 4-metric within-5pp verdict policy;W4 D3 落地嘅 reranker class + 21 tests preserved as future-proof scaffold;driver skip-row fallback handles SKIPPED rows automatically
  - F1.3 Azure semantic config `ekp-semantic-default` verify on `ekp-kb-drive-v1` index(W2 D5 schema check + apply if missing — non-procurement Chris index ops)
  - F1.4 Chris SME chunk_id labeling cascade per Q14:`scripts/discover_chunk_ids.py` + manual SME review for Q001-Q030(W2 baseline)+ Q036-Q055(W4 D2 expansion)— acceptable_chunk_ids: [] → real ids;target ≥ 45/55 queries validated per W4 plan §3 G6;**keyword-mode fallback acceptable for 1st-pass Gate 2 verdict** if SME cycles slip
  - F1.5 `scripts/run_cohere_lift_smoke.py` LIVE run on 10 representative queries → hybrid-only vs hybrid+Cohere R@5 lift verdict
  - F1.6 `scripts/run_reranker_shootout.py` LIVE run on full 55-query eval-set → **3-way comparison**(hybrid-only / cohere / azure)+ R@5;Voyage + ZeroEntropy rows auto-SKIPPED with reason "key/endpoint unset"
  - F1.7 `scripts/run_ragas_eval.py` LIVE run on winning reranker + Cohere baseline → 4-metric within-5pp 互換 verdict(Faithfulness / Answer Relevancy / Context Precision / Context Recall)
  - F1.8 Gate 2 verdict landed:**PASS** = 4-metric within 5pp互換 → continue F2-F6 optimization;**FAIL** = trigger ADR-0012(drop L2 CRAG)+ W5 D2-D5 fork to baseline-only + W6 demo prep early-start
  - F1.9 Q5 + Q21 follow-up note in `decision-form.md`(Cohere baseline lift confirmed / final reranker pick narrowed to Cohere vs Azure semantic 2-way / Voyage + ZeroEntropy 屬 Tier 2 candidate / 4-metric verdict)
- **Effort estimate**:2h AI(driver runs + analysis)+ Chris async procurement + SME labeling unbounded
- **Owner**:Chris(procurement + SME label + dev server smoke)+ AI(LIVE driver runs + 4-metric overlay analysis + verdict documentation)
- **Blocking**:F2-F6 全部 conditional on F1 verdict

### F2 — CRAG threshold empirical fine-tune(W4 R6 close + W4 carry-over)

- **Component(s)**:**C05** Generation(CRAG)
- **Spec ref**:`W4 plan §4 R6`,`components/C05-generation.md §2`,`W4 progress D1 §F1`
- **OQ deps**:F1 RAGAs LIVE 4-metric distribution
- **Acceptance criteria**:
  - F2.1 Analyse W4 D1 baseline threshold 0.70 vs W5 LIVE confidence distribution from F1.7 RAGAs run
  - F2.2 Calibrate threshold ∈ {0.65 / 0.70 / 0.75}— 揀最大化 4-metric average without false-correction spike
  - F2.3 Update `Settings.crag_confidence_threshold` default if calibrated value ≠ 0.70
  - F2.4 W5 progress entry document threshold rationale + LIVE distribution stats
- **Effort estimate**:0.5h
- **Owner**:AI
- **Conditional**:F1 PASS only(F1 FAIL = drop L2 CRAG = irrelevant)

### F3 — L3 routing conditional implementation(if Gate 2 全 PASS)

- **Component(s)**:**C05** Generation(CRAG L3 routing)+ **C04** Retrieval(L3 query rewriter integration)
- **Spec ref**:`architecture.md §3.5 CRAG progression L2 → L3`,`§6.1 W5 row "conditional L3"`,`components/C05-generation.md §3 L3 routing surface`
- **OQ deps**:F1 PASS verdict(if FAIL → drop L2 → L3 irrelevant)
- **Acceptance criteria**:
  - F3.1 `Settings.feature_l3_routing_enabled` flag toggle(default False — flipped True only on Gate 2 PASS)
  - F3.2 `CragLoop` extended:max_corrections from `crag_max_reformulations`(W4 default 1)→ 2-3 with knowledge-base routing(domain-aware re-fetch with query disambiguation)
  - F3.3 Stream path `/query/stream` 仍 L2-only(token-by-token UX precludes mid-stream rewrite per architecture.md §3.5);non-stream `/query` gains L3
  - F3.4 Unit test:max-correction-iteration honoured + routing decision trace logged
  - F3.5 `architecture.md §6.1 W5 row "L3 conditional"` verdict landed
- **Effort estimate**:1h
- **Owner**:AI
- **Conditional**:F1 全 PASS only

### F4 — Reranker per-KB field reconsideration(W3 C5 + W4 C9 close)

- **Component(s)**:**C04** Retrieval(KbConfig + reranker selection per-KB)+ **C02** KB Manager(KbConfig schema)
- **Spec ref**:`W3 retro §Surprises §Reranker per-KB vs global`,`W4 progress retro §Carry-overs C9`,`components/C04-retrieval.md §3 reranker swap surface`,`H1 + H4 boundary check`
- **OQ deps**:F1 verdict(particularly per-KB winner divergence — if same reranker wins across all KB types,per-KB column 非 sticky)
- **Acceptance criteria**:
  - F4.1 Analyse F1.6 shootout per-KB-type breakdown(Drive Manual technical / table-data / synthesis sub-corpora)
  - F4.2 Decision tree:(a)same reranker wins across sub-corpora → per-KB field NON-STICKY,defer to Tier 2;(b)different reranker wins per sub-corpus → per-KB field STICKY → ADR-0012 trigger(KbConfig schema extension + multi-tenancy adjacency check per H4)
  - F4.3 If STICKY:add `KbConfig.reranker_kind` field + factory wire + UI Settings exposure;若 NON-STICKY:document defer rationale in W5 progress
  - F4.4 Tier 1 boundary verify per H4(per-KB ≠ multi-tenancy;ok if 屬 single-tenant per-KB customisation;否則 defer Tier 2)
- **Effort estimate**:0.5h(NON-STICKY decision)/ 2h(STICKY implementation + ADR + tests)
- **Owner**:AI(decision)+ Chris(approve ADR if STICKY)
- **Conditional**:F1 PASS only(F1 FAIL irrelevant)

### F5 — W4 carry-overs LIVE smoke remainder closure(C7 + C8)

- **Component(s)**:**C01** Ingestion(PPT E2E)+ **C05** Generation(GPT-5.5 latency)+ **C08** API + **C10** Chat UI(SSE smoke)
- **Spec ref**:`W4 progress retro §Carry-overs C7+C8`
- **OQ deps**:F1 procurement landing + Chris dev server availability
- **Acceptance criteria**:
  - F5.1 W4 C7 PPT orchestrator E2E smoke:`scripts/run_pptx_ingest_sanity.py` against 3 W3 D1 後段 PPT samples → end-to-end ingest → chunks visible via `/kb/{id}/chunks`
  - F5.2 W4 C8 F5 Cohere lift summary log + decision-form Q5 follow-up note(post F1.5 LIVE run output)
  - F5.3 W4 C8 F6 GPT-5.5 latency baseline:p50 / p95 / per-query cost USD documented(Chris dev server + 5 real query smoke)
  - F5.4 W4 C8 F7 Chat UI 1-2 screenshots in W4 progress backfill(Chris dev server + browser smoke)
- **Effort estimate**:1h(post Chris dev server smoke runs)
- **Owner**:Chris(dev server + smoke)+ AI(documentation)
- **Conditional**:non-blocking F1;can run parallel

### F6 — Gate 2 closeout + W5 retro + W6 kickoff prep

- **Component(s)**:cross-cutting governance
- **Spec ref**:`architecture.md §6.3 Gate 2`,`§6.1 W6 row`,`PROCESS.md §2.3 closeout`
- **OQ deps**:F1-F5 verdicts + outcomes
- **Acceptance criteria**:
  - F6.1 Gate 2 LIVE verdict landed + documented in `architecture.md §6.3` decision row
  - F6.2 W05 progress.md retro section completed(7 sub-sections + Phase Gate verdict + carry-overs to W6 + ADR triggers)
  - F6.3 W06 phase folder kickoff:`docs/01-planning/W06-final-eval-demo/{plan,checklist,progress}.md` draft(W6 = final eval + demo prep + Beta plan per architecture.md §6.1 W6 row)
  - F6.4 W05 progress.md frontmatter status flipped to `closed`
  - F6.5 OQ Q21(reranker final pick)+ Q5(Cohere procurement)+ relevant OQ status sync to `decision-form.md`
- **Effort estimate**:1h
- **Owner**:AI(draft)+ Chris(approve)

## 3. Success Criteria(Phase Gate to W6)

| # | Criterion | Target | Measure | Block W6? |
|---|---|---|---|---|
| G1 | F1 Gate 2 LIVE verdict landed(PASS or FAIL — 唔可以 DEFER again) | landed | F1.8 | **Yes** |
| G2 | F1 PASS → F2-F4 conditional optimization 完成 OR explicit defer / F1 FAIL → ADR-0012 + drop L2 CRAG decision documented | path-correct | F2 / F3 / F4 / ADR | **Yes** |
| G3 | F5 LIVE smoke remainder closed(C7 PPT E2E + C8 F5/F6/F7 LIVE) | landed | F5.1-F5.4 | No(can carry W6 if Chris dev server bottleneck) |
| G4 | Backend ruff + frontend lint + type-check 0 errors | All clean | local run | Yes |
| G5 | Component design notes C04/C05 status bumped(F2/F3/F4 outcome reflected) | bumped | review | Yes |
| G6 | OQ Q21(reranker final pick)Resolved per F1 verdict | Resolved | decision-form.md | Yes |

## 4. Risks(Phase-Specific)

| # | Risk | Likelihood | Impact | Mitigation |
|---|---|---|---|---|
| R1 | Cohere endpoint populate still pending W5 D1(blocks F1.1 → Cohere shootout row)| Medium | High | Partial-shootout fallback per W4 plan §F10:hybrid-only + Azure semantic 2-way 仍可 emit baseline verdict;F1 verdict 標 "Cohere baseline pending — 1-way reranker only" + carry to W6 |
| R2 | ~~Voyage + ZeroEntropy procurement pending~~ DROPPED W5 D1 per Karpathy §1.2 — N/A | — | — | Voyage + ZeroEntropy 屬 Tier 2 alternative candidates;Cohere + Azure semantic 2-way 已 satisfies Tier 1 Gate 2 verdict policy |
| R3 | Chris SME chunk_id labeling slips(blocks F1.4 strict-mode RAGAs eval)| High | Medium | Keyword-mode RAGAs fallback acceptable for Gate 2 verdict per `eval/runner.py` mode auto-select;real chunk_id labeling for ≥ 45/55 acceptable per W4 plan §3 G6;backfill W6 |
| R4 | F1 PASS verdict but 4-metric within 5pp 邊界 case(e.g. 4.9pp)| Medium | Medium | Document specific failing metric + per-metric variance + reranker per-KB potential mitigation;NOT trigger drop L2 CRAG unless 互換 FAIL clear |
| R5 | F4 STICKY decision triggers ADR-0012 + KbConfig schema extension impacts C02 KB Manager + C09 Admin UI | Low | Medium | ADR-0012 written + schema migration + UI wire 屬於 1.5-day scope;若 W5 timeline 緊,defer F4 implementation to W6 + ADR-0012 record decision-only |
| R6 | F3 L3 routing implementation introduces non-determinism in `/query` non-stream path | Low | Low | max-correction-iteration cap + tenacity retry + fallback paths(per F1 W4 D1 design);L3 strictly opt-in via `feature_l3_routing_enabled` flag |
| R7 | R8 Ricoh corp proxy reactivation during W5 cloud-heavy work | High | High | Same mitigation as W2/W3/W4:disconnect GlobalProtect VPN;sanity scripts ready post-disconnect |

## 5. Day-by-Day Breakdown(rough — pending procurement landing pacing)

| Day | Date | Focus | Deliverables targeted |
|---|---|---|---|
| D1 | 2026-05-22 | F1.1-F1.8 Gate 2 LIVE close(procurement landing dependent;may slide if Chris dev server bottleneck) | F1 |
| D2 | 2026-05-23 | F2 CRAG threshold fine-tune + F3 L3 routing(if F1 PASS) | F2, F3 |
| D3 | 2026-05-24 | F4 reranker per-KB field decision + ADR-0012(if STICKY) | F4 |
| D4 | 2026-05-25 | F5 LIVE smoke remainder + W3+W4 carry-over closure | F5 |
| D5 | 2026-05-26 | F6 Gate 2 closeout + W5 retro + W6 kickoff prep | F6 |

(W4 same-day pattern likely 唔 repeat for W5 — F1 procurement landing 通常 calendar pacing-bound;若 Chris W5 D1 collapse procurement landing + dev server smoke 可能 same-day F1+F2+F3,但 baseline expectation = calendar pacing)

## 6. Dependencies on Prior Phase

Carry-overs from `W04-crag-eval-shootout/progress.md` retro:
- **W4 G2** Gate 2 verdict DEFERRED → **F1**
- **W4 C1** Gate 2 LIVE verdict close → **F1.5-F1.8**
- **W4 C2** Cohere Marketplace endpoint+key populate → **F1.1**
- **W4 C3** ~~Voyage + ZeroEntropy procurement~~ **DROPPED W5 D1** per Karpathy §1.2 simplicity-first user decision — Cohere + Azure semantic 2-way satisfies Gate 2 verdict policy;Voyage + ZeroEntropy 屬 Tier 2 alternative candidates;W4 D3 reranker class + 21 tests preserved as future-proof scaffold
- **W4 C4** Azure semantic config verify → **F1.3**
- **W4 C5** Chris SME chunk_id labeling → **F1.4**
- **W4 C6** Eval-set v1 promote → post F1.4 cascade
- **W4 C7** F9 PPT orchestrator E2E smoke → **F5.1**
- **W4 C8** F5/F6/F7 LIVE smoke remainder → **F5.2-F5.4**
- **W4 C9** Reranker per-KB field reconsideration → **F4**
- **W4 C10** CRAG threshold empirical fine-tune → **F2**
- **W4 C11** plan estimates calibration → W5 plan applies 0.3x heuristic(每 deliverable 0.5-1h baseline)— see §2 effort estimates above

## 7. Plan Changelog

| Date | Change | Reason | Approver |
|---|---|---|---|
| 2026-05-04 | Initial draft(W4 D5 末 closeout batch)| Per PROCESS.md §2.3 rolling-JIT kickoff;status=draft pending Chris W4 D5 closeout sign-off + W5 kickoff approval + procurement landing trigger | Chris(pending approve to flip active) |
| 2026-05-04 | **Voyage + ZeroEntropy DROPPED**(W4 C3 close as NOT NEEDED rather than deferred);F1.2 simplified to skip-row fallback note;F1.6 reduced 5-way → 3-way(hybrid-only / cohere / azure);R2 marked N/A;W4 retro carry-overs C3 updated;decision-form Q21 narrowed | Per Karpathy §1.2 simplicity-first user decision:Cohere(H2 LOCKED W3 baseline)+ Azure built-in semantic ranker(S1 SKU bundled,no procurement)2-way comparison already satisfies Gate 2 4-metric within-5pp verdict policy per architecture.md §6.3。W4 D3 落地嘅 VoyageReranker + ZeroEntropyReranker class + 21 unit tests preserved as future-proof Tier 2 scaffold — driver skip-row fallback handles SKIPPED rows automatically | User-approved per W5 D1 "如果唔係必須, 咁把它們先drop吧" signal |
| 2026-05-04 | Status `active → closed`(W5 D5 closeout per "Continue F6 closeout" signal)| Phase Gate G1(F1.8 Gate 2 LIVE verdict landed PARTIAL PASS 2026-05-04 W5 D2)+ G2(F2 CRAG threshold tuning + F4 NON-STICKY decision)+ G4(215/215 backend tests pass)+ G6(Q21 tentatively Resolved as Cohere v4.0-pro)PASS;G3(F5 Chris dev server)+ G5(C04/C05 design notes formal version increment)explicitly carry-over W6 per rolling JIT;**L2 CRAG NOT dropped**(drop-L2 trigger 4-metric within-5pp 互換 FAIL 未觸發);**Path 1 Cohere v3.5 → v4.0-pro spec drift accept** documented(architecture.md §3.2 amendment ticket reserved for stakeholder approval cycle);**Path A monkey-patch wrapper** for ragas 0.4.3 ↔ GPT-5 reasoning model API compatibility(eval-side only,non-architectural);**Bug A-I + Q014 timeline** documented in retro;**10 carry-overs C1-C10** logged → W06-final-eval-demo | User-flipped per W5 D5 closeout |

---

**Lifecycle reminder**:呢份 plan `status=draft`(等 Chris W5 D1 sign-off + procurement landing trigger flip `active`)。重大 deviation 入第 7 節 changelog。
