---
phase: W42-hybrid-semantic-ranker-toggle
status: active   # 2026-05-29 kickoff — Option ① drop semantic ranker config flag,enable Free-tier full-pipeline + chat UI test
last_updated: 2026-05-29
component_scope: C04 Retrieval Engine(hybrid.py search() semantic ranker toggle)+ C08 API Gateway(無 schema change,wire only)
adr_refs:
  - ADR-0039(NEW DRAFT Proposed)— Hybrid mode semantic ranker as configurable layer;F0 起草,F1 之前需 user confirm H1 boundary + Accept
  - Q21 Resolved 2026-05-05 — W6 D1 LIVE 2-way verify Azure semantic ranker WORSE than Cohere(faith Δ -11.76pp / rel Δ -9.81pp);ADR-0012 Cohere production reranker lock
  - architecture.md §3.2 — Azure AI Search Standard S1 vendor lock(H2,不變)
  - architecture.md §3.1 — RAG core retrieval(H1 boundary subject)
  - W2 Gate 1 R@5=0.9722 baseline(measured WITH semantic ranker → flag OFF 需 re-verify)
  - ADR-0021 — mode param hybrid/vector/fulltext(W42 同層 retrieval behavior space)
related_carry_overs:
  - 比較分析 2026-05-29 — Option ① drop semantic ranker(vs ② pgvector swap H2 / ④ Basic $75)選定
  - memory project_azure_search_tier_semantic_billing — 402 root cause = semantic ranker quota,NOT vector DB
  - memory project_v4_retrieve_only_vs_query_pipeline — V4 tab vs /query full pipeline 區分
---

# W42 — Hybrid Semantic Ranker Toggle(Free-Tier Full-Pipeline Enablement)

## §1 目標 + 範疇

**單一主要目標**:加一個 default-preserve config flag `hybrid_use_semantic_ranker`,令 hybrid mode 可以**選擇性 drop Azure semantic ranker**(`queryType="semantic"`),從而 enable **Free tier 全 pipeline + chat UI 測試**(bypass semantic ranker monthly quota 402),**唔換 vendor**、**$0**、**完全可逆**。

**Why this is the cheapest path(per 2026-05-29 trade-off 分析)**:
- 402 root cause = `hybrid.py:371` `queryType="semantic"`(Azure billable semantic ranker),NOT vector DB storage
- Semantic ranker 喺 EKP 已大致 redundant:Q21 已證佢比 Cohere WORSE,且 EKP 喺 search 之後行 Cohere 做主 reranker(同一 50 候選集)→ semantic ranker 只係被 Cohere override 嘅次等中間層
- Drop 咗 → hybrid 仍係 BM25 + vector + RRF(真正 hybrid)→ Cohere rerank → W40 deboost → synthesize → citation_expansion
- 對齊 W37-W41 knob pattern:加 flag、default preserve production、`.env` override 做測試

**⚠️ H1 BOUNDARY — 比 W37-W41 post-rerank knobs 更 core**:
- W37/W38/W40 knobs 屬 **post-rerank client-side score multiply**(non-architectural per H1 已判定)
- **W42 flag 改 Azure search query 本身嘅 semantics**(whether semantic ranker runs at search layer)→ 觸及 `architecture.md §3.1` RAG core retrieval behavior + Gate 1 / Q21 decision predicate
- **判定:H1-adjacent,需寫 ADR-0039 + Gate 1 re-verify**
- **F1 retrieval code 之前必須 STOP+ask 等 user confirm H1 boundary + ADR-0039 Accept**(F0 起草 Proposed)

**Non-goals**(W42 範疇外):
- 換 vector DB(Option ② pgvector / Qdrant — H2 vendor swap,範疇外)
- Azure tier upgrade(Option ④ Basic $75 — IT cost decision,範疇外)
- 改 Cohere reranker logic(Cohere 仍係主 reranker,不變)
- 改 W40 F1+F2 deboost / overfetch(default disabled preserve)
- chat UI 加 mode toggle UI control(out of scope — flag 喺 backend Settings level)
- 永久 production default flip(F4 視 eval outcome 決定係咪 W43+ separate decision)

**Component 範疇**:
- **C04 Retrieval Engine**(`hybrid.py` search() semantic toggle + `Settings` flag + `server.py` wire)
- 無 C08 schema change(`/query` mode field 不變)

**Real-calendar estimate**:F0 ~30min + F1 ~45min + F2 eval ~30-45min + F3 LIVE chat UI ~30min + F4 ~20min = **~2.5-3h total**(視 ADR confirm 等待)。

---

## §2 範疇 + Non-goals(逐 F-phase)

### F1 implementation(GATED on H1 confirm + ADR-0039 Accept)

1. `storage/settings.py` NEW field `hybrid_use_semantic_ranker: bool = True`(default preserve production W2 baseline behavior)
2. `retrieval/hybrid.py` `HybridSearcher.__init__` add `use_semantic_ranker: bool = True` param + store + parametrize `semantic_config_name`(currently hard-coded literal `"ekp-semantic-config"` at L372 → wire from `settings.azure_semantic_config_name`)
3. `retrieval/hybrid.py:368-372` search() hybrid branch — wrap semantic config 喺 `if self._use_semantic_ranker:`;flag False → hybrid = BM25 + vector + RRF(Azure default `queryType="simple"` + 同時有 search text + vectorQueries → Azure 自動 RRF hybrid fusion)
4. `api/server.py` HybridSearcher init wire `use_semantic_ranker=settings.hybrid_use_semantic_ranker`
5. NEW unit tests:
   - `test_w42_hybrid_semantic_disabled_drops_query_type` — flag False → payload 無 `queryType=semantic` + 無 `semanticConfiguration`,但仍有 `search` text + `vectorQueries`(true hybrid)
   - 保留 existing `test_hybrid_search_payload_shape_matches_spec`(default True → semantic present)— default preserve invariant

### F2 eval safety gate(H1 re-verify — 最關鍵)

- `.env` temporary `HYBRID_USE_SEMANTIC_RANKER=false`(flag OFF)+ restart backend
- Run Gate 1 retrieval eval(`eval-set-v0`)hybrid mode flag-OFF — **flag OFF hybrid 喺 Free tier work(無 semantic = 無 402)**
- 比較 R@5 vs W2 Gate 1 baseline 0.9722
- **G2 gate**:R@5 ≥ 0.92(within tolerance)→ 確認 drop semantic ranker 唔 regress retrieval quality(因 Cohere 反正 rerank 同一候選集)
- 若 R@5 regress below tolerance → semantic ranker DOES contribute → flag 留 default True,`.env` override 只做 dev test(仍達 chat UI 測試目標)

### F3 LIVE chat UI full pipeline(THE user goal)

- `.env` flag OFF preserved + restart backend + frontend dev
- Chat UI `/chat` hybrid mode query → **預期 HTTP 200 無 402**(semantic ranker dropped)+ full pipeline citations + answer
- Test 3 queries:Q-W25-I07 enumeration + Q-W25-I01 control + image retrieval query
- **首次 chat UI 全 pipeline 喺 Free tier work** ⭐(user 終於可以 UI 上實測)

### F4 closeout

- `.env` REVERT(production preserve default True — semantic ranker 留畀 paid GA tier)OR 視 F2 eval outcome 決定 default
- ADR-0039 status confirm
- W43+ candidate:production default flip(若 F2 confirm no regression)

---

## §3 Acceptance Criteria(6 gates)

| Gate | Criteria | Source |
|---|---|---|
| **G1 — F1 unit tests** | flag-False drops semantic + flag-True preserve 兩個 test PASS;existing `test_hybrid_search_payload_shape_matches_spec` 仍 PASS | F1.5 |
| **G2 — Gate 1 R@5 re-verify(H1 safety)** | flag-OFF hybrid Gate 1 R@5 ≥ 0.92(within tolerance vs W2 baseline 0.9722)— 確認 drop semantic 唔 regress | F2 |
| **G3 — chat UI full pipeline LIVE** | chat UI `/chat` hybrid mode flag-OFF → HTTP 200 無 402 + full pipeline citations(Q-W25-I07 + I01 + image query)| F3 |
| **G4 — pytest + ruff + mypy** | backend pytest preserve + 2 NEW W42 tests + ruff PASS + mypy W42 edits self-clean | F1.6 |
| **G5 — R6 catches + ADR-0039** | R6 Day 0 catches verified + ADR-0039 Accepted(post user confirm)| F0 + F1 gate |
| **G6 — production preserve** | default True = semantic on(W2 baseline preserve);`.env` override only for Free-tier dev/test | F4 |

**3 outcome decision matrix**:
- (a) G1+G2+G3 PASS → **STRONG PASS**:chat UI 全 pipeline 喺 Free tier $0 work + Gate 1 preserved + semantic ranker confirmed redundant → W43+ candidate production default flip(separate ADR decision per W26 PC1 sequential)
- (b) G2 R@5 regress below tolerance → **PASS WITH SEMANTIC-VALUE CAVEAT**:semantic ranker DOES contribute quality → flag default True 留,`.env` override 只做 dev test;仍達 chat UI 測試目標,但記錄 semantic ranker production value
- (c) G1 OR G3 FAIL → **re-diagnose**(mechanism not working as expected)

---

## §4 R6 Day 0 Recursive Verification(per CLAUDE.md §10 R6)

**R6 catch (1)** — `queryType="semantic"` production-hot path **只喺 `hybrid.py:371` search() hybrid branch**;`reranker/azure_semantic.py` 係**另一回事**(Azure semantic ranker AS standalone reranker,reranker_kind="azure",W4 shootout alt,production 用 cohere 唔用佢)— W42 只 toggle hybrid.py 嗰個,唔郁 reranker

**R6 catch (2)** — `/query` + `/chat` default `QueryRequest.mode="hybrid"`(W39 F2)→ 命中 semantic ranker → Free tier 402;chat UI 固定 hybrid(useChat SSE 唔 expose mode)→ 所以 chat UI 係 flag 嘅 main beneficiary

**R6 catch (3)** — V4 retrieval-test tab 已 plumb mode → vector works(W41 smoke verified);W42 flag 係 hybrid-mode-specific,同 mode param 正交(orthogonal)— flag 控制 hybrid 入面用唔用 semantic,mode 控制 hybrid/vector/fulltext

**R6 catch (4)** — `Settings.azure_semantic_config_name = "ekp-semantic-config"`(L125)存在但 hybrid.py:372 **hard-code 咗 literal string** 唔用 settings → W42 F1 順手 parametrize(wire from settings)+ 加 toggle;NO 新 semantic config 需要

**R6 catch (5)** — **Gate 1 R@5=0.9722 W2 baseline measured WITH semantic ranker** → flag OFF **必須** F2 eval re-verify(H1 safety gate);呢個係 H1 boundary 嘅核心 risk mitigation

**R6 catch (6)** — `test_retrieval.py:26-40` `test_hybrid_search_payload_shape_matches_spec` **assert hybrid 用 queryType=semantic + semanticConfiguration** → F1 default True 必須保留呢個 test PASS(default preserve)+ 加 NEW flag-False test(per W35 precedent test assertions lock behavior)

**R6 catch (7)** — flag OFF hybrid = BM25 + vector + RRF without semantic;Azure AI Search 有 `search`(text)+ `vectorQueries` 兩者 → 自動 RRF fusion(default behavior,唔需要 queryType=semantic)→ true hybrid 仍然 work,只係少咗 semantic L2 reorder layer

---

## §5 H1 Boundary 評估 + 範疇歸屬

**H1 determination:H1-adjacent,需 ADR-0039**

| H1 trigger 條件 | W42 是否觸發? |
|---|---|
| 加/改/刪 §3 RAG core component | ⚠️ **YES(部分)** — 改 §3.1 retrieval search behavior(semantic ranker on/off);但 default-preserve flag = additive,production 行為不變 |
| 改 vendor / service | ❌ NO — 仍 Azure AI Search,Cohere 仍主 reranker;唔換 vendor(H2 safe) |
| 改 storage layout | ❌ NO — index schema 不變 |
| 改 multi-KB architecture | ❌ NO |
| 改 8-view layout philosophy | ❌ NO |
| 加 Tier 2 feature | ❌ NO |

**結論**:W42 改 §3.1 retrieval search behavior(semantic ranker)= H1-adjacent。雖然 default-preserve flag 令 production 行為不變,但呢個改動觸及 Gate 1 + Q21 decision 嘅 predicate(兩者都 assume semantic ranker on)→ **需寫 ADR-0039 documenting 決定 + Gate 1 re-verify 作為 safety gate**。

**Required behavior(per CLAUDE.md §5.1 H1)**:
1. ✅ F0 plan 起草 ADR-0039(Proposed)+ H1 assessment(本節)
2. ⏳ **F1 retrieval code 之前 STOP+ask** — chat 講明 change / why / proposed + 等 user confirm「approved + ADR-0039 Accept」
3. ⏳ User confirm 後 ADR-0039 Proposed → Accepted + 開始 F1

**H1-H7 verify**:
- **H1**:H1-adjacent — ADR-0039 route(本節)
- **H2**:✅ 唔換 vendor — Azure AI Search 不變,Cohere 不變,NO new dependency
- **H3**:N/A
- **H4**:不涉 Tier 2
- **H5**:不涉 PII / secret(flag 純 config)
- **H6**:✅ F1 unit test 寫(C04 critical module)
- **H7**:N/A — pure backend

---

## §6 改動清單(4 phase + ADR)

### F0 啟動(本 doc)
- [x] D0.1 `docs/01-planning/W42-hybrid-semantic-ranker-toggle/` folder
- [x] D0.2 `plan.md`(本文件)
- [x] D0.3 `checklist.md`
- [x] D0.4 `progress.md` Day 0
- [x] D0.5 `docs/adr/0039-hybrid-semantic-ranker-toggle.md` DRAFT(Proposed)
- [ ] D0.6 F0 commit
- [ ] D0.7 session-start.md §10 W42 row append active + W42+ → W43+ rename
- [ ] **D0.8 STOP+ask user confirm H1 boundary + ADR-0039 Accept(F1 GATE)**

### F1 implementation(GATED — post H1 confirm + ADR Accept)
- [ ] F1.1 `settings.py` NEW `hybrid_use_semantic_ranker: bool = True`
- [ ] F1.2 `hybrid.py` `__init__` add `use_semantic_ranker` + `semantic_config_name` params + store
- [ ] F1.3 `hybrid.py` search() hybrid branch wrap semantic 喺 `if self._use_semantic_ranker:`
- [ ] F1.4 `server.py` wire `use_semantic_ranker=settings.hybrid_use_semantic_ranker` + `semantic_config_name=settings.azure_semantic_config_name`
- [ ] F1.5 2 NEW unit tests(flag-False drops semantic + default-True preserve)+ existing test PASS
- [ ] F1.6 pytest preserve + ruff + mypy + ADR-0039 Accepted
- [ ] F1.7 commit

### F2 eval safety gate(H1 re-verify)
- [ ] F2.1 Pre-flight per CLAUDE.md §10.3 step 5b
- [ ] F2.2 `.env` `HYBRID_USE_SEMANTIC_RANKER=false` + restart backend
- [ ] F2.3 Gate 1 retrieval eval flag-OFF → R@5 vs 0.9722 baseline
- [ ] F2.4 G2 gate intersect(R@5 ≥ 0.92 tolerance)

### F3 LIVE chat UI full pipeline
- [ ] F3.1 `.env` flag OFF preserved + restart backend + frontend dev
- [ ] F3.2 Chat UI `/chat` hybrid mode Q-W25-I07 → HTTP 200 無 402 + full pipeline citations ⭐
- [ ] F3.3 Q-W25-I01 control + image retrieval query
- [ ] F3.4 G3 gate intersect

### F4 closeout
- [ ] F4.1 Cross-doc sync(plan/checklist/progress + session-start)
- [ ] F4.2 `.env` REVERT(production preserve default True)OR 視 F2 outcome
- [ ] F4.3 ADR-0039 final status
- [ ] F4.4 W43+ candidate evaluate(production default flip 若 F2 no regression)
- [ ] F4.5 commit + push

---

## §7 Changelog

| Date | Change | Trigger |
|---|---|---|
| 2026-05-29 | Plan v1.0 ship — F0 kickoff via Chris「起 W42 plan 做 Option ①」pick(post 三方 trade-off 深入分析)| W41 closed 2026-05-28 + smoke test Free-tier 402 incident + Chris AskUserQuestion Option ① pick |
