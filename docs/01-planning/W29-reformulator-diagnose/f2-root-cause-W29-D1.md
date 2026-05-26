---
deliverable: F2 — Root cause confirm + markdown report
phase: W29-reformulator-diagnose
date: 2026-05-26
inputs: [f1-1, f1-2, f1-3, f1-4, f1-5 W29 D0 outputs]
verdict: H1 + H4 NEW combined dominant; H2 REFUTED; H3 standalone-only (not backend-dominant)
---

# W29 F2 — Root Cause Confirm

## Executive summary

**Original W19+ candidate (g) framing** (Synthesizer enumeration-refuse fix via path iii F3 reformulator strengthening)was based on premise:reformulator prompt 未足夠強化 + Q-W25-I07 因此 refuse。

**R6 Day 0 catch + F1 audit reveal a different reality**:

1. **Reformulator prompt EXAMPLE 3 ALREADY ship** W25 F3 D4(ADR-0034)+ EXAMPLE 3 directly cover Q-W25-I07 with vocab-aligned hypothetical variants
2. **Synthesizer NO LONGER refuses** Q-W25-I07 today(`refused: False`)— W25.5 BUG-025 symmetric deboost + W26-W28 retrieval improvements 累積 close 咗 refuse pattern
3. **W26-W28 eval G3 marginal MISS verdict reflects single-query baseline,NOT reformulator-path performance** — eval pipeline 從未 wire reformulator
4. **Backend `/query` path WITH reformulator still fails G1 acceptance**(only 1 citation = chunk-0044 intro;§8.1-§8.5 individual walkthrough chunks 完全 NOT surface top-5)despite reformulator confirmed working(Langfuse 93% success rate;backend cached connections pre-corp-proxy)

## Per-hypothesis verdict

| Hypothesis | Status | Evidence |
|---|---|---|
| **H1 RRF surface** | **CONFIRMED DOMINANT for backend `/query`** | F1.3 + F1.5:reformulator confirmed working backend (Langfuse fallback=False);F1.4 EXAMPLE 3 vocab aligns with §8.1 + §8.3 + §8.4 corpus chunk_title at 60-80% token overlap;BUT W29 D0 top-5 = chunk-0044 intro + §3/§5/§7 chunks,ZERO §8.1-§8.5 surface |
| **H2 vocab-corpus mismatch** | **REFUTED** | F1.4 manual diff:EXAMPLE 3 hypothetical variants match corpus chunk_title vocab(§8.1 4-word literal,§8.3 saga + orchestration,§8.4 inbound + event-driven)— reformulator generates well-aligned variants |
| **H3 fallback gap** | **standalone-only;NOT backend-dominant** | F1.1 standalone test 100% APIConnectionError(corp proxy intercepts fresh Python httpx connections);F1.5 backend Langfuse 93.3% success rate(14/15 obs since W25 D4)— backend's lifespan-time client pool survives proxy boundary |
| **H4 NEW eval coverage gap** | **CONFIRMED DOMINANT for /eval/run** | F1.5:Langfuse ZERO obs spanning W26-W28 eval batches(~104 expected obs missing);`backend/eval/orchestrator.py:93` 直接 `engine.retrieve()` bypassing reformulator + fused_retrieve;NO `from generation.query_reformulator` import 喺 `backend/eval/*.py` |

## Combined finding

W26-W27-W28 eval G3 marginal MISS verdict 並非 due to reformulator weakness — eval pipeline 從未測試 reformulator effect。**今日 backend `/query` path WITH reformulator working,Q-W25-I07 仍 fail G1**(1 intro citation only,non-§8.1-§8.5 walkthrough)— 顯示 retrieval ranking pipeline (hybrid + RRF + Cohere rerank) **systematically favors intro chunk-0044 over individual §8.1-§8.5 walkthrough chunks** despite well-aligned reformulator variants。

## Why intro chunk-0044 always wins(hypothesis,need F3 evidence)

Most likely:**hybrid + Cohere rerank both reward token-density match against query literal "Integration scenarios"**:
- chunk-0044 = intro chunk repeating "Integration scenarios" 5+ times across paragraphs + listing A-E summaries
- §8.1 chunk-0045 = uses specific vocab "Customer service request submission (async transaction)" — query literal "Integration scenarios" 出現次數遠少
- → Cohere rerank gives chunk-0044 higher relevance score even when reformulator-variant queries surface §8.1 individual chunks at retrieve stage,rerank kills them back

## F3 surgical fix candidate paths

per user Surgical scope pick(path i synthesizer + path ii CRAG threshold OUT of W29 scope):

### Path A — Increase per-variant overfetch + reduce RRF k

| Tune | Current | Proposed | Rationale |
|---|---|---|---|
| `QUERY_EXPANSION_PER_VARIANT_OVERFETCH` | 4 | **8 or 12** | Per-variant fan-out top-K 增大,§8.x individual chunks 有更多機會 surface RRF aggregation 之前 |
| `QUERY_EXPANSION_RRF_K` | 60 | **30** | RRF k 越低,top-rank-in-each-variant 越受重視;reduce intro-chunk cross-variant RRF boost |

**Implementation**:Setting tune only(zero code change);`.env` env override + backend restart + curl `/query` verify G1。 Likely sub-1h work。

**Risks**:overfetch 8/12 may add ~100-200ms latency per variant × 3 variants = ~300-600ms total。 Within QUERY_EXPANSION_LATENCY_CAP_S=8.0 budget。

**Probability G1 PASS**:Medium(50-70%)— reduce RRF k more aggressive,可能 surface §8.1 + §8.3 + §8.4 individual chunks 但 Cohere rerank 仍 可能 kill。

### Path B — Cohere rerank tweak

Out of W29 scope per user Surgical scope pick(rerank tune potentially H1 boundary per ADR-0012 vendor lock semantics — STOP+ask + ADR-route)。

### Path C — Wire reformulator into eval/orchestrator.py(close H4)

**Implementation**:
- Edit `backend/eval/orchestrator.py:93` — wrap `engine.retrieve()` call with same `if settings.enable_query_expansion: fused_retrieve(...)` block as `backend/api/routes/query.py:110-117`
- Pass `app.state.query_reformulator` through eval orchestrator init
- 4-6h work + new tests

**Risks**:Add eval orchestrator dep on app.state(currently isolated)。

**Effect**:Allows future W30+ eval runs to actually measure reformulator effect on G3 metric。But does **NOT solve W29 G1**(backend `/query` path 仍 fail same reason)。

### Path D — No-op + PARTIAL closeout per user fallback pick

**Implementation**:Accept current state — backend `/query` enumerate-from-intro answer 已 reasonable for end-user(no refuse,5-scenario summary from chunk-0044 intro)。G1 strict (≥2 §8.x walkthrough) may be over-constrained acceptance criteria。

**Effect**:Close W29 PARTIAL per Q4 measurement-experiment-fail-policy + path (ii) CRAG threshold elevate W30+ candidate per user chose fallback。

### Path E — Hybrid:Path A + Path C combined

**Implementation**:Both Path A and Path C — Setting tune for G1 + eval orchestrator wire to measure G3 in next eval。Closes H1 + H4 simultaneously。~8-10h work。

## Recommendation

User scope pick was Surgical = path (iii) reformulator only。 But R6 catch invalidated path (iii) prompt-tune scope。 Need explicit user redirect:

- **Path A** = closest to "Surgical reformulator tune" original intent(只郁 reformulator-related Settings,no code change to other modules)
- **Path C** = orthogonal eval infrastructure fix(NOT user-visible G1 improvement;but close systemic eval blind spot for future phases)
- **Path E** = both A + C combined per "thorough" angle

Per Karpathy §1.2 simplicity + W26 PC1 一次只郁一個旋鈕,推薦:**Path A first** — try Setting tune,若 G1 PASS → close phase;若 G1 FAIL → PARTIAL closeout per Q4 + Path C + path (ii) CRAG threshold elevate W30+。
