---
phase: W06-final-eval-demo
plan_ref: ./plan.md
status: draft
last_updated: 2026-05-04
---

# Phase W06 — Checklist

> Atomic checkbox(每 item ≤ 0.5–1.5 hour effort per W5 C9 calibration:LIVE-heavy days 1.5x;static-heavy 0.3-0.5x)。
> Status:`draft` 直到 W5 D5 closeout sign-off + W6 kickoff approval。
> 全 unchecked 至 W6 D1 implementation start。

## F1 — Azure 2-way 互換 verify + Gate 2 STRONG PASS upgrade(W5 C1+C2 close)

- [ ] F1.1 `Settings.reranker_kind=azure` swap(`.env` override or default config update for this run only)
- [ ] F1.2 `scripts/run_ragas_eval.py --subset 20` LIVE re-run on Azure pipeline → emit `reports/ragas-azure-subset20.json`(cost ~$15-25 USD)
- [ ] F1.3 Cross-reference Cohere subset20 baseline vs Azure subset20 → 4-metric within-5pp 互換 evaluation per metric
- [ ] F1.4 Verdict landed(STRONG PASS upgrade / Cohere reaffirmed / Azure better → ADR-0012 trigger)
- [ ] F1.5 Bug I LIVE re-verify same run validates `max_completion_tokens=4096` floor(target 0/20 errored vs W5 D2 2/20)
- [ ] F1.6 Q5 + Q21 follow-up note in `decision-form.md`(final reranker pick + Gate 2 STRONG PASS verdict)
- [ ] F1.7 architecture.md §3.2 vendor lock + §6.3 Gate 2 verdict amendment ticket — stakeholder approval cycle 准備好 narrative

## F2 — Final eval full-corpus(post Chris SME labeling cascade strict-mode)

- [ ] **DEFERRED Chris SME** F2.1 chunk_id labeling Q001-Q030 + Q036-Q055 → ≥ 45/55 validated per W4 plan §3 G6
- [ ] F2.2 `eval-set-v1-draft.yaml` promoted → `eval-set-v1.yaml`(remove `-draft` suffix)
- [ ] F2.3 `scripts/run_ragas_eval.py --subset 55` against winning reranker(Cohere v4.0-pro per F1)→ `reports/ragas-final-v1.json`
- [ ] F2.4 Aggregate vs W5 D2 subset=20 baseline 比較;若 within ±5% per metric → Tier 1 quality baseline confirmed

## F3 — Synthesizer prompt tuning(answer_relevancy 0.841 borderline mitigation,W5 C4 close)

- [ ] F3.1 Analyse F1.7(W5 D2)+ F1(W6)answer_relevancy distribution per query → identify systematic verbose pattern source
- [ ] F3.2 Prompt tweak candidates:answer length cap / question-direct format / structure constraint
- [ ] F3.3 A/B subset=10 RAGAs run baseline vs tweaked prompt → delta evaluation
- [ ] F3.4 Decision land tweaked prompt(if rel ≥ 0.85)/ keep marginal(if 0.83-0.85 + faith/prec/recall hold)/ revert if regression

## F4 — W4/W5 carry-overs LIVE smoke remainder(C5+C6)

- [ ] **DEFERRED Chris dev server** F4.1 PPT orchestrator E2E smoke on 3 PPT samples → `/kb/{id}/chunks` chunks visible
- [ ] **DEFERRED post F1.2** F4.2 Cohere lift summary log + decision-form Q5 follow-up note
- [ ] **DEFERRED Chris dev server** F4.3 GPT-5.5 latency baseline:p50 / p95 / per-query cost USD
- [ ] **DEFERRED Chris dev server browser** F4.4 Chat UI 1-2 screenshots in W6 progress backfill

## F5 — Demo prep + Beta plan(W7-W8 stakeholder cycle prep)

- [ ] F5.1 Demo script narrative draft(15-min flow:use case 1 + ingestion E2E + query + citation + Pipeline wizard + retro)
- [ ] F5.2 Stakeholder Q&A briefing pack(common questions + risk slides)
- [ ] F5.3 Beta plan draft `docs/03-implementation/beta-plan-v1.md`(scope + timeline + Q7-Q12 dependencies + risk)
- [ ] F5.4 Demo screenshots / GIF artifacts(post F4.4)

## F6 — Phase Gate 2 closeout + W6 retro + W7 kickoff prep

- [ ] F6.1 Gate 2 final verdict landed(STRONG PASS upgrade OR PARTIAL PASS confirmed)+ architecture.md §6.3 amendment ticket
- [ ] F6.2 W06 progress.md retro 7 sections complete + Phase Gate verdict + carry-overs to W7-W8 + ADR triggers
- [ ] F6.3 W07 phase folder kickoff:`docs/01-planning/W07-beta-deploy/{plan,checklist,progress}.md` draft
- [ ] F6.4 W06 progress.md frontmatter status flipped to `closed`
- [ ] F6.5 OQ Q21 final + Q5 + relevant other Q resolution sync to `decision-form.md`

---

## Cross-Cutting

- [ ] Each commit references `progress.md` Day-N entry(R2)
- [ ] Component tag in commit message per CC-1
- [ ] OQ status sync to `decision-form.md`(R4)— Q21 final W6 D1 critical
- [ ] Gate 2 STRONG PASS verdict logged in `architecture.md §6.3` decision row(via stakeholder approval cycle)
- [ ] RISK_REGISTER.md update if R1/R6 amendment cycle persists OR Azure 2-way surfaces new risk

---

**Lifecycle reminder**:呢份 checklist 衍生自 `plan.md` deliverables。新加 deliverable 必須先入 plan + changelog,然後再加 checklist item。
