---
phase: W05-optimization
plan_ref: ./plan.md
status: closed
last_updated: 2026-05-04
---

# Phase W05 — Checklist

> Atomic checkbox(每 item ≤ 0.5–1 hour effort per W4 carry-over C11 calibration)。
> Status:`draft` 直到 W4 D5 closeout sign-off + W5 kickoff approval + procurement landing trigger。
> 全 unchecked 至 W5 D1 implementation start。

## F1 — Gate 2 LIVE verdict close(blocking gate)

- [x] F1.1 Cohere `.env` populate ✅ W5 D1 — Chris populated post user "已經補上"signal;`cohere_endpoint=https://<dep>.<region>.models.ai.azure.com` Path A Marketplace + `cohere_api_key` set;`cohere_rerank_model=Cohere-rerank-v4.0-pro`(spec drift v3.5→v4.0-pro accepted per Path 1 user decision — same-vendor model upgrade,non H1+H2 violation;architecture.md §3.2 amendment ticket reserved for W5 retro)
- [x] **DROPPED W5 D1 per Karpathy §1.2** F1.2 Voyage api_key procurement — Cohere + Azure semantic 2-way 已 satisfies Gate 2 verdict policy;W4 D3 VoyageReranker class + tests preserved as future-proof scaffold;driver skip-row fallback handles SKIPPED row automatically
- [x] **DROPPED W5 D1 per Karpathy §1.2** F1.2 ZeroEntropy api_key procurement — same rationale as Voyage drop
- [x] F1.3 Azure semantic config verify ✅ W5 D1 — service-level enabled(Free tier per Chris screenshot),index-level config `ekp-semantic-config` already 落地 W2 D5 schema(NOT `ekp-semantic-default`)。Bug C(Settings typo)+ Bug D(api-version=2024-07-01 deprecated `queryLanguage`)+ Bug E(mojibake)fixed `4c43e96`;F1.6 LIVE 3-way 全 evaluated post-fix
- [ ] **DEFERRED Chris SME** F1.4 chunk_id labeling cascade Q001-Q030 + Q036-Q055(target ≥ 45/55 validated;keyword-mode fallback acceptable for 1st-pass Gate 2 verdict if SME cycles slip — F1.7 LIVE n=5 RAGAs already used reference fallback `expected_keywords` per W5 D1 evaluator,strict-mode 留 W6+ Chris SME cycle)
- [x] F1.5 `scripts/run_cohere_lift_smoke.py` LIVE run ✅ W5 D1(--subset 10 keyword-mode):hybrid-only R@5 = 1.0 / cohere R@5 = 1.0 / lift = 0(simple accounting queries 喺 keyword-mode saturate;真實 differential signal 留 F1.7 RAGAs 4-metric)。Pre-fix F1.5 first-pass($2.85 cost overshoot)surfaced Bug B subset cost containment(fixed `5a00bcd`)
- [x] F1.6 `scripts/run_reranker_shootout.py` LIVE run ✅ W5 D1(--subset 10 keyword-mode):hybrid-only R@5 = 1.0 / cohere R@5 = 1.0 / azure R@5 = 1.0(post Bug C+D+E fix;3-way 全 evaluated)/ voyage + zeroentropy SKIPPED clean。Comparison data 留 F1.7 RAGAs(keyword-mode 對 simple queries saturate 全 1.0,3-way 唔 differentiate)
- [x] F1.7 `scripts/run_ragas_eval.py` LIVE run ✅ **PARTIAL**(--subset 5 sanity):**Cohere v4.0-pro baseline 4-metric** faithfulness 0.989 / answer_relevancy 0.815 / context_precision 0.978 / context_recall 1.000(全 evaluated 5/5;n=5 sample size underpowered for Gate 2 robust verdict)。Bug F+G(temperature + AsyncAzureOpenAI;`38ea9b1`)+ Bug H Path A(monkey-patch GPT-5 param translation;`8b1c3da`)required 之前先 LIVE-runnable
- [x] F1.7-extended Phase 1 ✅ W5 D2 — `--subset 20` Cohere v4.0-pro baseline LIVE:faithfulness 0.944 / answer_relevancy 0.795 / context_precision 0.986 / context_recall 1.000(n=18 evaluated,2 errored due to Bug I ragas judge max_completion_tokens too small — non-blocking)
- [x] **Phase 2 SKIPPED per Option 1b variant decision tree** ✅ W5 D2 — 3-of-4 metric ≥ 0.85,1 borderline(rel 0.795 in 0.75-0.85 range);全部 variance < 0.20;faith 0.944 > 0.80。Azure 2-way 互換 carry-over W6 Gate 3 demo prep per W4 plan §F10 fallback policy
- [x] F1.8 Gate 2 LIVE verdict landed ✅ W5 D2 — **PARTIAL PASS — Cohere baseline robust;answer_relevancy 邊緣 follow-up + Azure 2-way 互換 carry-over W6**;**L2 CRAG NOT dropped**(drop-L2 trigger condition 4-metric within-5pp 互換 FAIL 未觸發;partial verdict 仍 PASS path)
- [x] F1.9 Q5 + Q21 + relevant OQ follow-up note ✅ W5 D2 — Q5 Resolved(Path A + v3.5→v4.0-pro accept architecture.md §3.2 amendment 留 W5 retro);Q21 tentatively `Cohere v4.0-pro`(verify W6 Azure 2-way);Q14 SME labeling pending(keyword-mode acceptable for current verdict)

## F2 — CRAG threshold empirical fine-tune(W4 R6 close)

- [x] F2.1 LIVE confidence distribution analysed ✅ W5 D3 — `scripts/run_crag_grade_smoke.py` driver + 20-query run:mean 0.970 / median 0.975 / p25 0.960 / p75 1.000 / p95 1.000;0/20 trigger at any candidate threshold {0.65,0.70,0.75,0.80};report `reports/crag-grade-smoke.json`
- [x] F2.2 Calibration decision ✅ W5 D3 — Path A KEEP 0.70 selected(empirical p25 floor 0.960 → no candidate threshold differentiates sample);Path B(0.95)+ Path C(0.85)data-unsupported;Path D(per-corpus dynamic)defer Tier 2 per H4
- [x] F2.3 `Settings.crag_confidence_threshold` NO CHANGE ✅ W5 D3 — 維持 W4 D1 baseline 0.70 per Karpathy §1.2 simplicity-first("data say no change → no change");留 wide margin for future Tier 2 GraphRAG / multi-corpus low-quality retrieval cases
- [x] F2.4 W5 D3 progress entry threshold rationale + LIVE distribution stats ✅ W5 D3 — inline above + W5 retro narrative integration deferred

## F3 — L3 routing conditional implementation(if Gate 2 全 PASS)

- [ ] **CONDITIONAL F1 全 PASS** F3.1 `Settings.feature_l3_routing_enabled` flag toggle(default False → True)
- [ ] **CONDITIONAL F1 全 PASS** F3.2 `CragLoop` extended:max_corrections 1 → 2-3 with knowledge-base routing
- [ ] **CONDITIONAL F1 全 PASS** F3.3 Stream path `/query/stream` 仍 L2-only(architecture.md §3.5 constraint);non-stream `/query` gains L3
- [ ] **CONDITIONAL F1 全 PASS** F3.4 Unit test:max-correction-iteration honoured + routing decision trace logged
- [ ] **CONDITIONAL F1 全 PASS** F3.5 `architecture.md §6.1 W5 row "L3 conditional"` verdict landed

## F4 — Reranker per-KB field reconsideration(W3 C5 + W4 C9 close)

- [x] F4.1 Analyse F1.6 shootout breakdown ✅ W5 D4 — F1.6 keyword-mode 3-way parity(hybrid+cohere+azure 全 R@5 1.0)+ F1.7 RAGAs strong Cohere baseline → no per-corpus divergence signal in Tier 1 single-corpus + single-tenant scope
- [x] F4.2 Decision:**NON-STICKY** ✅ W5 D4 — Cohere LOCKED + Voyage/ZeroEntropy DROPPED + Tier 1 single-tenant single-corpus → trivially "same reranker wins" branch (a) of decision tree;defer Tier 2 per H4 boundary;**no ADR-0012 trigger**
- [x] F4.3-alt NON-STICKY rationale documented ✅ W5 D4 — inline W5 progress D4 entry;closes W3 C5 + W4 C9 carry-overs;ADR-0012 reservation released(neither Gate 2 LIVE FAIL drop-L2 nor STICKY trigger fired)
- [ ] ~~F4.3 STICKY ADR-0012 + KbConfig schema extension~~ NOT TRIGGERED(NON-STICKY path)
- [ ] ~~F4.4 STICKY Tier 1 boundary verify + approval~~ NOT TRIGGERED(NON-STICKY path)

## F5 — W4 carry-overs LIVE smoke remainder closure(C7 + C8)

- [ ] **DEFERRED Chris dev server** F5.1 PPT orchestrator E2E smoke on 3 W3 D1 後段 PPT samples → `/kb/{id}/chunks` chunks visible
- [ ] **DEFERRED post F1.5** F5.2 Cohere lift summary log + decision-form Q5 follow-up note
- [ ] **DEFERRED Chris dev server** F5.3 GPT-5.5 latency baseline:p50 / p95 / per-query cost USD documented
- [ ] **DEFERRED Chris dev server browser** F5.4 Chat UI 1-2 screenshots in W4 progress backfill

## F6 — Gate 2 closeout + W5 retro + W6 kickoff prep

- [x] F6.1 Gate 2 LIVE verdict landed ✅ W5 D2 PARTIAL PASS;`architecture.md §6.3` formal amendment **ticket reserved for stakeholder approval cycle**(per CLAUDE.md §4.4 architecture content-lock — AI 不單方面 edit;narrative ready in W5 retro for vNext increment)
- [x] F6.2 W05 progress.md retro section completed ✅ W5 D5 — 7 sub-sections + Phase Gate verdict + 10 carry-overs C1-C10 + ADR triggers
- [x] F6.3 W06 phase folder kickoff ✅ W5 D5 — `docs/01-planning/W06-final-eval-demo/{plan,checklist,progress}.md` draft committed(rolling JIT — only W6 active scope draft;W7+ remains future)
- [x] F6.4 W05 progress.md frontmatter status flipped to `closed` ✅ W5 D5
- [x] F6.5 OQ Q5 + Q21 sync ✅ W5 D5 — Q5 Resolved with Path 1 v4.0-pro accept addendum;Q21 `Tentatively Resolved`(Cohere v4.0-pro;W6 Azure 2-way verify);Q14 SME labeling status unchanged(non-blocking PARTIAL PASS)

---

## Cross-Cutting

- [ ] Each commit references `progress.md` Day-N entry(R2)
- [ ] Component tag in commit message per CC-1
- [ ] OQ status sync to `decision-form.md`(R4)— Q21 final pick W5 D1-D2 critical
- [ ] Gate 2 verdict logged in `architecture.md §6.3` decision row(via ADR-0012 if FAIL → drop L2)
- [ ] RISK_REGISTER.md update if R1/R2 procurement persists OR Gate 2 FAIL surfaces as new risk

---

**Lifecycle reminder**:呢份 checklist 衍生自 `plan.md` deliverables。新加 deliverable 必須先入 plan + changelog,然後再加 checklist item。
