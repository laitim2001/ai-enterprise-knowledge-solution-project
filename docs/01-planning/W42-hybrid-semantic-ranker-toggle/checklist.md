---
phase: W42-hybrid-semantic-ranker-toggle
plan_ref: ./plan.md
status: active
last_updated: 2026-05-29
---

# W42 — Checklist

> 原子化勾選項。Option ① drop semantic ranker config flag — F1 implementation GATED on H1 confirm + ADR-0039 Accept。F2 eval safety gate(Gate 1 re-verify)+ F3 LIVE chat UI full pipeline(user goal)+ F4 closeout。

## F0 — 啟動

- [x] F0.1 建立 `docs/01-planning/W42-hybrid-semantic-ranker-toggle/` folder
- [x] F0.2 R6 Day 0 7 catches — (1) queryType=semantic 只喺 hybrid.py:371 production-hot path;(2) chat UI 固定 hybrid 係 flag main beneficiary;(3) flag 同 mode param 正交;(4) semantic_config_name hard-coded literal 需 parametrize;(5) Gate 1 0.9722 measured WITH semantic → F2 re-verify mandatory;(6) test_hybrid_search_payload_shape_matches_spec assert semantic → 保留 + 加 flag-False test;(7) flag OFF hybrid = BM25+vector+RRF 自動 fusion 仍 work
- [x] F0.3 起草 `plan.md` 7 段(含 §5 H1 boundary 評估)
- [x] F0.4 起草 `checklist.md`(本文件)
- [x] F0.5 起草 `progress.md` Day 0
- [x] F0.6 起草 `docs/adr/0039-hybrid-semantic-ranker-toggle.md` DRAFT(Proposed)
- [ ] F0.7 F0 commit
- [ ] F0.8 session-start.md §10 W42 row append active 2026-05-29 + W42+ → W43+ placeholder rename
- [ ] **F0.9 STOP+ask user confirm H1 boundary + ADR-0039 Accept(F1 GATE per CLAUDE.md §5.1 H1)**

## F1 — Implementation(GATED — post H1 confirm + ADR-0039 Accept)

- [ ] F1.1 `storage/settings.py` NEW field `hybrid_use_semantic_ranker: bool = True`(default preserve W2 baseline)+ comment block
- [ ] F1.2 `retrieval/hybrid.py` `HybridSearcher.__init__` add `use_semantic_ranker: bool = True` + `semantic_config_name: str = "ekp-semantic-config"` params + store
- [ ] F1.3 `retrieval/hybrid.py` search() hybrid branch — wrap `payload["queryType"]="semantic"` + `payload["semanticConfiguration"]` 喺 `if self._use_semantic_ranker:`;flag False → BM25 + vector + RRF(Azure 自動 fusion)
- [ ] F1.4 `api/server.py` HybridSearcher init wire `use_semantic_ranker=settings.hybrid_use_semantic_ranker` + `semantic_config_name=settings.azure_semantic_config_name`
- [ ] F1.5 NEW unit tests:
  - [ ] F1.5.a `test_w42_hybrid_semantic_disabled_drops_query_type` — flag False → payload 無 queryType=semantic + 無 semanticConfiguration 但有 search text + vectorQueries
  - [ ] F1.5.b existing `test_hybrid_search_payload_shape_matches_spec` default True 仍 PASS(default preserve)
- [ ] F1.6 backend pytest preserve + ruff PASS + mypy W42 edits self-clean + ADR-0039 Accepted
- [ ] F1.7 commit

## F2 — Eval safety gate(H1 re-verify Gate 1)

- [ ] F2.1 Pre-flight per CLAUDE.md §10.3 step 5b(Langfuse 200 + Postgres SELECT 1)
- [ ] F2.2 `.env` `HYBRID_USE_SEMANTIC_RANKER=false` + backend kill + restart per ghost-Python pattern
- [ ] F2.3 Gate 1 retrieval eval `eval-set-v0` hybrid mode flag-OFF(Free tier work 因無 semantic)→ R@5 collect
- [ ] F2.4 G2 gate — R@5 ≥ 0.92 within tolerance vs W2 baseline 0.9722?

## F3 — LIVE chat UI full pipeline(user goal)

- [ ] F3.1 `.env` flag OFF preserved + backend restart + frontend dev launch
- [ ] F3.2 Chat UI `/chat` hybrid mode Q-W25-I07「show me all the Integration scenarios」→ HTTP 200 無 402 + full pipeline citations ⭐
- [ ] F3.3 Q-W25-I01 control「what is the high level architecture」+ image retrieval query「show me the diagram of Scenario A」
- [ ] F3.4 G3 gate — chat UI 全 pipeline 喺 Free tier work confirmed

## F4 — 收尾 + 跨文件同步 + commit + push

### A. 跨文件同步
- [ ] A.1 plan.md frontmatter status flip per outcome(closed / closed_strong / closed_partial)
- [ ] A.2 checklist.md cross-cutting tick(本文件)
- [ ] A.3 progress.md retro 7 段
- [ ] A.4 session-start.md §10 W42 row flip active → closed*
- [ ] A.5 `.env` REVERT flag(production preserve default True)OR 視 F2 outcome 決定 default
- [ ] A.6 ADR-0039 final status confirm
- [ ] A.7 RISK_REGISTER R-W38-1 update(W42 提供 Free-tier full-pipeline workaround,Azure billing 仍 IT-side gate for production semantic-on)

### B. W43+ priority queue
- [ ] B.1 W43+ candidate:production default flip(`hybrid_use_semantic_ranker=False` default)若 F2 confirm no regression — sequential per W26 PC1
- [ ] B.2 W43+ HIGHEST preserved:Hybrid mode billing-resolved re-verify(若 GA 決定升 paid tier 用 semantic)
- [ ] B.3 W43+ preserved:W40 F1+F2 deboost production default flip ADR(per W41 STRONG evidence)
- [ ] B.4 Long-term carry-over 維持
- [ ] B.5 永久 OUT path (a) judge LLM 升級

### C. commit + push
- [ ] C.1 F4 收尾 commit
- [ ] C.2 push origin/main confirmed

---

## Cross-Cutting

- [ ] All deliverables committed to git(F4 closeout commit pending)
- [ ] All OQ status changes 反映於 decision-form.md — 無 OQ 變動
- [ ] ADR-0039 documented + status Accepted(post H1 confirm)
- [ ] progress.md retro section 寫好 7 段 per F4 closeout
- [ ] progress.md frontmatter status flipped per outcome
- [ ] Phase W43+ kickoff trigger 標記於 retro

---

**Lifecycle reminder**:本 checklist 隨 plan deliverables 衍生。F1 GATED on H1 confirm — 唔可以未 confirm 就寫 retrieval code。
