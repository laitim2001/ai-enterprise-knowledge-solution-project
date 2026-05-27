---
phase: W39-f2-live-evidence-free-tier-workaround
plan_ref: ./plan.md
checklist_ref: ./checklist.md
status: active   # F0 啟動 2026-05-27
last_updated: 2026-05-27
---

# W39 — Progress Log

## Day 0 — 2026-05-27 — F0 啟動

### 啟動行動

- ✅ F0.1 建立 `docs/01-planning/W39-f2-live-evidence-free-tier-workaround/` folder
- ✅ F0.2 R6 Day 0 5 catches surfaced(per below)
- ✅ F0.3 起草 `plan.md` 7 段
- ✅ F0.4 起草 `checklist.md` 原子化勾選項
- ✅ F0.5 起草 `progress.md` Day 0(本 entry)
- ⏳ F0.6 啟動 commit pending
- ⏳ F0.7 session-start.md §10 W39 row append pending

### R6 Day 0 5 catches 報告

#### catch (1) — `/retrieval_test` endpoint 已 support mode param(Path B 0-code-change)

`backend/api/schemas/retrieval_test.py:17`:
```python
mode: Literal["hybrid", "vector", "fulltext"] = "hybrid"
```

`backend/api/routes/retrieval_test.py:74-80`:
```python
result = await engine.retrieve(
    query=payload.query, kb_id=kb_id,
    top_k=payload.top_k, mode=payload.mode, rerank=payload.rerank,
)
```

**Implication**:F1 Path B 直接 hit `POST /kb/{kb_id}/retrieval-test` with `{"mode": "vector"}` body field — 0-code-change LIVE。Skip Azure semantic ranker quota(Free tier 402 root cause)同時保留 Cohere rerank + W38 F2 deboost。

#### catch (2) — `/query` schema `QueryRequest` 不含 mode(Path A additive scope)

`backend/api/schemas/query.py:41-57` `QueryRequest`:
- top_k_retrieval / top_k_rerank / llm_model / reranker / enable_crag / enable_intent_routing — 全部 covered
- **NO `mode` field**

**Implication**:F2 Path A additive — `QueryRequest.mode: Literal["hybrid", "vector", "fulltext"] = "hybrid"` 加入,backward-compat default preserve current behavior。`query.py:128 + 308` retrieve() 2 call sites propagate `mode=payload.mode`。對齊 `/retrieval_test` schema permanent symmetry(F3 唔 revert)。

#### catch (3) — W38 F2 deboost loop mode-independent

`backend/retrieval/retrieval_engine.py:158-200` deboost loop 喺 `if do_rerank and hits:` block 內,**mode 影響 hybrid search shape 但唔影響 deboost trigger**。Cohere rerank 接收 retrieve hits(無論 hybrid/vector/fulltext),返 RerankedChunk + section_path,W38 F2 deboost loop fire regardless。

**Implication**:Path B(vector mode)同 Path A(hybrid mode after Azure resolved)應該同樣 verify W38 F2 deboost effect。Path B vector mode evidence 已 sufficient for W38 F2 verification scope。

#### catch (4) — Free tier 402 likely semantic ranker monthly quota exhausted

Azure AI Search Free tier:
- Semantic ranker monthly quota ~1000 queries/month
- W34-W38 cumulative LIVE eval(eval/run + 5+5 reproducibility runs × multiple phases)可能撞 quota
- 402 Payment Required 通常表示 quota / billing block,non-tier-feature-missing(那會 return 400 with specific message)

**Implication**:Vector mode 不消耗 semantic quota → 應該繞過 Free tier 402;F1 Path B early signal 可驗證 hypothesis。

#### catch (5) — W38 cea024f F2 infrastructure ready

W38 commit `cea024f` ship:
- `storage/settings.py` 加 NEW knobs:
  - `reranker_cross_section_deboost: float = 1.0`(disabled default)
  - `reranker_section_path_prefix_depth: int = 2`
- `retrieval/retrieval_engine.py:158-200` post-rerank deboost loop:
  - Frozen RerankedChunk rebuild pattern
  - Re-sort by rerank_score descending
  - Defensive malformed section_path skip
  - Observability log `reranker_cross_section_deboost_applied`
- 5 NEW unit tests PASS — backend pytest 1091 → 1096
- `.env` clean state preserved post W38 F4

**Implication**:W39 唔需要 code change for F2 deboost logic;只需 `.env` override `RERANKER_CROSS_SECTION_DEBOOST=0.85`(W38 F3 pattern reused)即可 LIVE 驗證。

### F-phase pre-implementation surface

#### F1 Path B execution sequence(~30min total)

```
F1.1 pre-flight Langfuse 200 + Postgres SELECT 1 (1 min)
  ↓
F1.2 .env temp override RERANKER_CROSS_SECTION_DEBOOST=0.85 + DEPTH=2 (2 min)
  ↓
F1.3 backend explicit kill + Start-Process restart + /health verify ~30s warmup (5 min)
  ↓
F1.4 write w39-f1-pathb-runner.py + run 5+5 (~15 min)
  ↓
F1.5 decision tree intersect G1+G2+G3 (5 min)
```

#### F2 Path A execution sequence(~45min total)

```
F2.1 QueryRequest.mode additive + retrieve() propagation 2 sites + 2 unit tests (15 min)
  ↓
F2.2 pytest 1096 → 1098 + ruff + commit (10 min)
  ↓
F2.3 backend kill + restart + /health verify (5 min)
  ↓
F2.4 write w39-f2-patha-runner.py + run 5+5 (~15 min)
  ↓
F2.5 decision tree intersect G1+G2+G3+G4+G5 (5 min)
```

#### F3 closeout surface

- `.env` marker block removed(W27/W29/W37/W38 pattern reused)
- `QueryRequest.mode` field preserved permanent enhancement(對齊 ADR-0021 `/retrieval_test`)
- W40+ HIGHEST candidate per F2 outcome — Settings default flip 0.85 OR hybrid mode billing-resolved re-verify

### Phase preconditions verify ✅

| Precondition | Status |
|---|---|
| W38 F2 reranker deboost infrastructure ship | ✅ commit `cea024f` |
| W38 F4 closeout `.env` clean state | ✅ commit `3d7c834` |
| ADR-0021 `/retrieval_test` mode param support | ✅ `api/schemas/retrieval_test.py:17` |
| W36 PC-W34-1 step 5b pre-flight protocol | ✅ shipped W36 |
| W36 PC-W35-1 runner cp1252 fix | ✅ shipped W36(F1+F2 runner 複用) |
| Cohere v4.0-pro endpoint reachable | ✅ `.env` cred populated(separate from Azure Search billing) |
| Working tree clean | ✅ W38 closed_partial pushed |

### Cost containment policy reminder

Per `memory/feedback_judge_llm_cost_policy.md`:
- ✅ W39 不涉及 LLM cost upgrade — F1+F2 純 retrieval-side + API schema additive,F1+F2 LIVE 用現有 backend
- ✅ W39 不觸 path (a) judge LLM 升級(永久 OUT per memory)

---

**End of W39 progress.md Day 0**
