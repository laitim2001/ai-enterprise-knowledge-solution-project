---
deliverable: F1.4 — Vocab mismatch analysis (manual diff)
phase: W29-reformulator-diagnose
date: 2026-05-26
inputs: [f1-1-reformulator-variants-W29-D0-raw.txt, f1-2-corpus-vocab-W29-D0-raw.txt, f1-3-rrf-top5-W29-D0-raw.txt, f1-5-reformulator-fallback-rate-W29-D0-raw.txt]
---

# W29 F1.4 — EXAMPLE 3 hypothetical variants vs corpus §8.x actual vocab

## Reference materials

- **EXAMPLE 3 (`REFORMULATOR_SYSTEM_PROMPT` line 78-84)** — Good variants list for "show me all the integration scenarios":
  1. `"customer service request submission API integration"`
  2. `"Saga-style multi-system orchestration pattern"`
  3. `"inbound event-driven flow Service Bus"`

- **Corpus §8.1-§8.5 actual chunk_title vocab** (per F1.2):
  - §8.1: `"Scenario A — Customer service request submission (async transaction)"`
  - §8.2: `"Scenario B — Real-time inventory check at checkout (sync query)"`
  - §8.3: `"Scenario C — Order placement with payment (saga orchestration)"`
  - §8.4: `"Scenario D — MPS device service alert (inbound event-driven fan-out)"`
  - §8.5: `"Scenario E — Snowflake daily ETL (batch synchronisation)"`

## Per-variant alignment analysis

| EXAMPLE 3 variant | Best-matched §8.x | Token overlap | Verdict |
|---|---|---|---|
| `customer service request submission API integration` | §8.1 `Customer service request submission (async transaction)` | "customer service request submission" 4-word literal | **EXCELLENT** (>80% lexical overlap) |
| `Saga-style multi-system orchestration pattern` | §8.3 `Order placement with payment (saga orchestration)` | "saga" + "orchestration" | **HIGH** (~60% — saga + orchestration core keywords) |
| `inbound event-driven flow Service Bus` | §8.4 `MPS device service alert (inbound event-driven fan-out)` | "inbound" + "event-driven" | **HIGH** (~50% — both core directional keywords) |

## Missing scenario coverage

EXAMPLE 3 does NOT include variants for:
- §8.2 `Real-time inventory check at checkout (sync query)` — no variant mentions inventory / checkout / sync query
- §8.5 `Snowflake daily ETL (batch synchronisation)` — no variant mentions Snowflake / ETL / batch sync

**Implication**:Even with EXAMPLE 3 strengthened reformulator working,§8.2 + §8.5 may not surface unless reformulator LLM generates beyond EXAMPLE 3 literal vocab(unlikely — LLM tends to mirror given examples)。

## Critical disconnect — RRF surface still excludes §8.1-§8.5

Despite EXAMPLE 3 alignment with §8.1 + §8.3 + §8.4 corpus vocab (3 of 5 should surface):

**W29 D0 backend `/query` actual top-5 = chunk-0044 intro / chunk-0008 / chunk-0036 / chunk-0020 / chunk-0018** — ZERO §8.1-§8.5 individual chunks despite reformulator confirmed working (Langfuse fallback=False latency=1730ms)。

3 possible explanations:
1. **Per-variant hybrid retrieve fan-out doesn't include §8.x chunks even with EXAMPLE 3-aligned queries** — hybrid retriever may rank intro chunks higher than individual scenario chunks even for specific-vocab queries
2. **RRF aggregation with k=60 dilutes per-variant rankings** — high k value gives heavy weight to multiple ranks combined; intro chunk surfacing across all variants gets RRF boost
3. **Cohere rerank kills §8.x chunks post-RRF** — final Cohere rerank may favor intro chunk-0044 + §3/§5/§7 sections per "Integration scenarios" query literal token match (intro chunk-0044 says "Integration scenarios" 5+ times)

→ Need **per-variant fan-out chunk_ids inspection** to distinguish (RRF + rerank layer) but that data is not exposed in /query response 或 Langfuse default observation。

## Vocab mismatch hypothesis FINAL verdict

**H2 REFUTED** for §8.1 + §8.3 + §8.4 (EXAMPLE 3 vocab aligns)。
**H2 PARTIALLY VALID** for §8.2 + §8.5 (EXAMPLE 3 doesn't cover)。
**Dominant blocker** is NOT vocab mismatch but **hybrid retrieve + RRF + Cohere rerank pipeline favoring intro chunks over individual walkthrough chunks despite reformulator generating well-aligned specific-vocab variants**(H1 RRF surface)。

## Implication for F3 surgical fix

**EXAMPLE 3 prompt strengthening 重點唔係 problem source** — reformulator IS doing its job(per Langfuse evidence)。**Problem 喺 retrieval ranking layer**(hybrid + RRF + rerank)。

F3 candidates (per W29 plan §2):
- **(a) Tune `query_expansion_per_variant_overfetch` 4→8/12** — increase per-variant top-K to give individual scenario chunks more headroom before RRF aggregation
- **(b) Tune `query_expansion_rrf_k` 60→30** — make RRF more aggressive about reordering, reducing intro-chunk RRF boost
- **NEW (f) Wire reformulator + fused_retrieve into `backend/eval/orchestrator.py`** — close H4 eval coverage gap so future eval-set runs actually measure reformulator effect(blocked by H1 separately for /query G1)

## Reframed conclusion

Original W29 path (iii) "reformulator prompt strengthening" target was W19+ candidate (g) framing。R6 catch revealed prompt already shipped。F1.1-F1.5 audit reveals:

- ✅ Reformulator prompt EXAMPLE 3 effective(vocab-aligned with corpus)
- ✅ Backend `/query` reformulator wired + working (93% success rate per Langfuse 14/15 obs since W25 D4)
- ❌ **Backend retrieval pipeline (hybrid + RRF + rerank) still favors intro chunks over individual walkthrough chunks**
- ❌ **Eval pipeline never wires reformulator at all** — W26-W28 G3 marginal MISS verdict reflect single-query baseline,NOT reformulator-path performance

→ G1 PRIMARY user-test acceptance (≥ 2 distinct A-E walkthrough citations) blocked by **hybrid+RRF+rerank ranking layer**(H1)not reformulator prompt。F3 surgical scope decision needed user input。
