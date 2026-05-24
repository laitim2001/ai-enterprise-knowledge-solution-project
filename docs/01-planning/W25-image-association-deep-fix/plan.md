---
phase: W25-image-association-deep-fix
name: "Image-Text Association — Deep Fix(D3 chunker + D4 query expansion + D2 retrieval relax + D1 citation enrichment)"
sprint_week: W25
start_date: 2026-05-23
end_date: 2026-06-13          # planned ~3 weeks, may slip with changelog log
status: closed
spec_refs:
  - architecture.md §3.3      # chunking philosophy
  - architecture.md §3.5      # layout-aware chunker
  - architecture.md §3.6      # hybrid retrieval + low_value
  - architecture.md §3.7      # query orchestration (D4 touches)
  - architecture.md §5.5      # chat citation surface
prior_phase: W24c-users-rbac
trigger_memo: docs/03-implementation/image-chunk-retrieval-investigation-2026-05-23.md
---

# Phase W25 — Image-Text Association Deep Fix

> **Plan version**:1.0(initial)
> **Owner**:Chris(Tech Lead)
> **Approved by**:Chris(chat 2026-05-23 ——「(a) 同意 phase folder W25-image-association-deep-fix/ 命名 / (b) 同意 F1→F2→F3→F4→F5→F6→F7 順序 / (c) 5 條 design question 嘅 default OK」)
> **Trigger memo**:`docs/03-implementation/image-chunk-retrieval-investigation-2026-05-23.md`(投票結果:Path III phase-level full optimization)

## 1. Scope

BUG-009 + BUG-010 + BUG-011 closure cascade 接通晒 screenshot upload + counter + private-blob proxy + KB Images tab 真縮圖 render —— 但 chat 答案 citation **仍然從未帶圖**,即使 doc 真有相關圖。Investigation memo 2026-05-23 揭示 root cause = **two-pronged**:

- **H1 主因**(empirically observed):`sample-doc-with-image-1` 121 chunks 入面 **72(60%)被 `low_value_flag` 掃中** —— image-bearing chunks 機率上 token < 100 floor(`layout_aware.py:271-279`)→ 喺 retrieval step [2] 被 hard-filter 走 → LLM 連睇都冇睇過
- **H2 輔助**:vocabulary-overlap 競爭輸畀 TOC chunk(目錄一行就 condensed 「4. High-level architecture」phrase,密度高過 section 4 正文)

任何單一 option(D1 post-process / D2 retrieval relax / D3 chunker re-tune / D4 query expansion)**都唔係 complete 解** —— 用戶 chat 2026-05-23 explicit framing「我需要的是完整地解決圖片和文字內容的關聯問題」+ AskUserQuestion 揀 **Path III phase-level full optimization** = D3 + D4 + D2 + D1 四項組合。

**本 phase 目標**:**完整解決 chat 答案 + 圖片內容嘅關聯問題**,即:
- 用戶問 doc 內某 section 嘅 query(自然語言)→ chat 答案 LLM cite 對 section 嘅 chunk → citation 帶有對應 section 嘅 image(s)
- 即使 LLM cite 旁邊嘅 non-image chunk(adjacent section),delivery 層仍能 attach 鄰近 image chunks 嘅圖
- 不單 image association 受惠 —— **chunker re-tune 同步解 60% low_value 嘅 chunker stress signal**(可能 corpus-wide systemic 問題);query expansion 改善 **general retrieval recall**(non-image queries 都得益)

**Sprint week origin**:**W19+ rolling JIT**(per CLAUDE.md §10 R1 + session-start.md §10 W24d+ row);呢個 phase **唔喺 architecture.md §6.1 原 W1-W12 sprint 表內** —— 屬 W18 之後 trigger 出嚟嘅 architectural deep-fix(類似 W17 beta hardening / W22 frontend rebuild / W24a-c Wave C splits 嘅 rolling 性質)。

## 2. Deliverables

### F1 — D3 chunker re-tune(ADR-0033)

- **Spec ref**:`architecture.md §3.3` chunking philosophy + `§3.5` layout-aware chunker
- **H1 trigger**:**是** —— `low_value_floor` 由 100 → 60(同/或 adjacent-short-merge)係 chunker behaviour change,觸 H1 architectural-adjacent decision,必寫 ADR
- **OQ deps**:Q14 SME labeling(Resolved per W11 D2 — non-blocking for F1 chunker code,只 affects F2 eval set choice)
- **Acceptance criteria**:
  1. ADR-0033 drafted + approved by Chris(chat or AskUserQuestion confirm)— `docs/adr/0033-chunker-low-value-tuning.md`
  2. `backend/ingestion/chunker/layout_aware.py`:
     - `low_value_floor` constant **100 → 60**(per user default Q3 — 治標)
     - `_emit_chunk` accumulator 加 adjacent-short-merge logic(per user default Q3 — 治本):當下一個 paragraph event 屬同一 section_path **AND** 當前 acc.token_count < `min_chunk_floor=160`(經驗 default),merge 入當前 acc 而非 emit new chunk
     - 保留現有 _TOC_PATTERNS + version-statement low_value 規則(unchanged)
  3. Unit test `backend/tests/test_chunker_low_value.py`:
     - low_value floor edge case(60 tokens → flag;59 → flag;61 → not flag — 假設無 TOC pattern)
     - adjacent-short-merge:2 個 same-section short paras → merge into 1 chunk(token_count = sum,non-low_value if combined > 60)
     - regression:6-sample W2 corpus re-chunk → total chunk count 變化 < ±20%(loose envelope avoid chunk count 過劇變動破壞 Gate 1)
  4. `mypy --strict` clean on chunker module
- **Effort estimate**:~10-12h(ADR draft 2h + code 4h + unit tests 4h + iteration buffer 2h)
- **Owner**:AI

### F2 — F1 verify gate:Gate 1 R@5 re-verify + dev-KB re-ingest

- **Spec ref**:`architecture.md §3.6` Hybrid retrieval Gate 1 baseline + `§6` Sprint timeline W2 Gate 1 PASS R@5=0.9722
- **H1 trigger**:否(verify gate,run existing eval harness)
- **OQ deps**:Q13 ground truth allocation(Resolved)+ Q14 specific labeler(Resolved)
- **Acceptance criteria**:
  1. Re-ingest **dev-only KBs**(per user default Q2):`sample-doc-with-image-1` + `sample-kb-test-1` + `sample-doc-for-rag-knowledge-1`;Beta-track KB(若有 prod data 落咗)留 W16 Track A IT cred 通咗先 batch re-ingest(out of W25 scope)
  2. Eval set:**`eval-set-v0.yaml` original 6 samples**(per user default Q1)+ **新加 5-8 條 image-bearing queries**(self-written non-SME-labelled,只測 image association — eg「How does the high-level architecture look like?」「Show me the integration components diagram」「Where is the deployment topology described?」)寫入 `eval-set-v0-image-queries.yaml` 並 wire 入 eval harness 作 supplementary
  3. **Gate 1 R@5 re-verify**:
     - Baseline:W2 D5 R@5=0.9722
     - Pass condition:**R@5 ≥ 0.92**(within 5pp degradation tolerance per Gate 2 5pp envelope convention);若 R@5 < 0.92 → STOP + ADR-0033 amendment + re-tune
     - 同時記錄 chunk count change(`sample-doc-with-image-1` 121 chunks → expected ~80-100 chunks post-merge)
  4. RAGAs 4-metric on eval-set-v0:Faithfulness / Correctness / Context-relevancy / Answer-relevancy **all within 5pp** of W6 baseline(Gate 2 verdict envelope)— soft gate for F2,hard gate for F4
- **Effort estimate**:~8-10h(re-ingest 2h + eval run 4h + analysis 2h + buffer)
- **Owner**:AI(eval harness run);Chris(若 Gate 1 fail,sign-off ADR amendment)

### F3 — D4 query expansion / RAG-fusion(ADR-0034)

- **Spec ref**:`architecture.md §3.7` query orchestration
- **H1 trigger**:**是** —— query orchestration 屬 §3.7 architectural component,加 reformulator + fusion step 觸 H1,必寫 ADR
- **OQ deps**:無
- **Acceptance criteria**:
  1. ADR-0034 drafted + approved — `docs/adr/0034-query-expansion-rag-fusion.md`
  2. `backend/pipeline/query_reformulator.py` NEW module:
     - `async def reformulate(query: str, max_variants: int) -> list[str]`
     - 用 GPT-5.5-mini(或同款 cheap LLM,per H2 vendor lock)生 `max_variants - 1` 個 reformulation(eg. original「what is the high level architecture」→「show me the system architecture diagram」+「explain the component overview」)
     - **Hard latency cap**(per user default Q4):wall-clock **P95 < 5s** for full reformulation cycle;若 superseded,fall back **2-query 變體**(original + 1 reformulation only)
  3. `backend/retrieval/result_fusion.py` NEW module:
     - `async def fused_retrieve(queries: list[str], k: int) -> list[ChunkRecord]`
     - Reciprocal Rank Fusion (RRF)(per existing hybrid retrieval pattern §3.6)— 各 query 跑 hybrid retrieve top-k,RRF score = `sum(1/(60+rank))` across queries
     - Configurable `enable_query_expansion` flag(`KbConfig` extension OR `Settings` global default — pre-decide F3 D1)
  4. `backend/pipeline/query_pipeline.py` integration:
     - 若 `enable_query_expansion=true` → `reformulator → fused_retrieve`(取代 plain `hybrid_searcher.search`)
     - 若 false → 原 path unchanged(BC)
  5. Unit tests:
     - `test_query_reformulator.py`:cheap-LLM mock return predetermined variants;assert variants > 1
     - `test_result_fusion.py`:RRF formula correctness(known rank inputs → known fused order);latency cap fallback path
     - Integration:end-to-end `/query` with `enable_query_expansion=true` → top-K chunks set superset relative to plain hybrid baseline
- **Effort estimate**:~16-20h(ADR 2h + reformulator 5h + fusion 5h + tests 6h + integration buffer)
- **Owner**:AI

### F4 — F3 verify gate:RAGAs 4-metric regression + latency budget check

- **Spec ref**:`architecture.md §3.6` Gate 2 + §3.7 query orchestration
- **H1 trigger**:否
- **OQ deps**:Q14 SME labels(Resolved, eval set v0 sufficient for regression gate)
- **Acceptance criteria**:
  1. RAGAs 4-metric run on `eval-set-v0`(W2 baseline 6 samples)+ `eval-set-v0-image-queries`(F2 supplementary 5-8 queries)
     - **Hard pass condition**:all 4 metrics **within 5pp** of W6 baseline(Gate 2 envelope):
       - Faithfulness ≥ baseline - 5pp
       - Correctness ≥ baseline - 5pp
       - Context-relevancy ≥ baseline - 5pp
       - Answer-relevancy ≥ baseline - 5pp
     - 任何 metric 超 5pp degradation → STOP + ADR-0034 amendment 或 disable `enable_query_expansion` by default
  2. **Latency budget check**(per user default Q4):
     - P50 / P95 / P99 measurement across 50 queries
     - **Hard cap**:P95 < 5s(per user default)
     - 若 P95 > 5s → fall back to 2-query 變體 default;若 2-query 仍 > 5s → disable `enable_query_expansion` by default
  3. Image association improvement measurement(soft gate):
     - 用 F2 5-8 image-bearing queries 統計 citation-with-image hit rate
     - Pre-F3 baseline:0/8(per session-start observation,3 queries all 0-image cited)
     - F3 expected lift:≥ 3/8(empirical lift target,non-blocking — 即 chunker fix 後 retrieval 已有 surface,query expansion 仲 additive)
- **Effort estimate**:~6-8h(eval run 3h + analysis 2h + write-up + buffer)
- **Owner**:AI

### F5 — D2 + D1 combined CH-003(retrieval low_value soft-relax + citation post-process)

- **Spec ref**:`architecture.md §3.6` hybrid retrieval + §5.5 chat citation
- **H1 trigger**:**TBD — R6 surfaced at Day 0**(see §7 changelog item iii)。現有 low_value filter 屬 **Azure Search server-side OData filter**(`hybrid.py:4 + :41`,`enabled eq true and low_value_flag eq false`);D2 由 server-side filter → client-side post-filter Python override = 改 §3.6 retrieval policy 嘅 mechanism interface,可能 H1 trigger。F5.1.2 CH-003 spec drafting 必先 surface H1 trigger 風險畀 Chris 決定:**(a)** CH-003 sufficient(若 H1 not triggered:即 "filter mechanism unchanged spec-level,只係 implementation detail"); OR **(b)** CH-003 + co-ADR-0035 mandatory(若 H1 triggered:filter mechanism = §3.6 spec interface)
- **OQ deps**:無
- **Acceptance criteria**:
  1. CH-003 spec.md drafted + approved — `docs/03-implementation/changes/CH-003-image-association-retrieval-and-citation/spec.md`
  2. **D2 — retrieval low_value soft-relax**:
     - `backend/retrieval/hybrid_searcher.py`:filter 階段加 condition「`low_value=true` AND `embedded_images_json` non-empty」→ **保留** chunk(score × **0.7** per user default Q5)而非 hard drop
     - Configurable threshold via `Settings.retrieval_image_low_value_weight = 0.7`(empirical adjust per F4-style verify if needed)
  3. **D1 — citation post-process**:
     - `backend/generation/citation_enrichment.py`(或新建 `citation_image_neighbors.py`):
       - 收到 LLM cited chunks → look up neighbors by `section_path` match OR `doc_order` ±N range(N=3 default)
       - 攞 neighbors 嘅 `embedded_images_json`(若有)→ attach 入 citation `aux_embedded_images: list[ImageRef]` 新 field(Pydantic schema extend)
       - **Cap `max_aux_images_per_citation = 2`**(avoid 圖洪水)
     - 整合入 `query.py` `_proxy_citation_images`:`aux_embedded_images` 同 `embedded_images` 一齊走 proxy URL rewrite
  4. Frontend:`<ImageGallery>`(chat citation viewer)如何顯示 `aux_embedded_images` —— **scope-out**(現有 component 應該自動接住 array;若 backend 同 schema 兼容 fold-in,frontend 零改動)
  5. Tests:
     - `test_hybrid_searcher_image_low_value.py`:image+low_value chunk retained with × 0.7 weight;non-image low_value chunk still dropped
     - `test_citation_image_neighbors.py`:section_path match + doc_order range + cap-at-2 behaviour
     - Integration:end-to-end `/query` with image KB → citation `aux_embedded_images` populated
  6. CH-003 checklist + progress per PROCESS.md §3 lifecycle
- **Effort estimate**:~12-16h(spec 2h + D2 4h + D1 5h + tests 5h + integration buffer)
- **Owner**:AI

### F6 — F5 verify gate:end-to-end manual test + image association measurement

- **Spec ref**:N/A(verification only)
- **H1 trigger**:否
- **OQ deps**:無
- **Acceptance criteria**:
  1. **Manual user-test**:3-5 條 image-bearing queries on `sample-doc-with-image-1` via `/chat` UI:
     - 「How does the high-level architecture look like?」
     - 「Show me the integration components」
     - 「What does the deployment topology diagram show?」
     - 「Where are the API contracts defined?」(non-image query — 對照組,citation 應該 0 圖)
     - 任意第 5 條由 Chris pick
  2. Pass condition:**≥ 4/5 image-bearing query 嘅 citation 帶有至少一張對應 section 嘅圖**(其中 non-image query 對照組 citation 應該 0 圖 — control for false-positive image surfacing)
  3. Image association rate measurement:final image hit rate ≥ **5/8** on F2 supplementary 5-8 query eval set(pre-W25 baseline:0/8)
  4. RAGAs 4-metric final run(post-F5):4 metric 仍 within 5pp baseline envelope(non-regression after D2+D1 add-on)
  5. Latency final measurement post-F5:P95 hard cap < 5s preserved
- **Effort estimate**:~4-6h(manual test 2h + measurement 2h + analysis + buffer)
- **Owner**:AI(measurement);Chris(manual user-test pick 1 query)

### F7 — Phase closeout

- **Spec ref**:CLAUDE.md §10 R5(architectural-adjacent decisions → ADR)+ PROCESS.md §2.3 closeout
- **H1 trigger**:否(closeout meta)
- **OQ deps**:無
- **Acceptance criteria**:
  1. All F1-F6 deliverables `[x]` OR explicit `🚧 deferred + reason` in progress.md
  2. ADR-0033 + ADR-0034 status `Proposed → Accepted` flip
  3. `progress.md` Retro section written:What worked / What didn't / Surprises / Carry-overs to W26+ / ADR triggers / Phase Gate result / Phase status
  4. `RISK_REGISTER.md` update:image-association-deep-fix risk(if any new pattern surfaced)
  5. `decision-form.md` OQ status sync(F2 eval set v0+image queries: confirm Q15 weekly signal report dependency unchanged)
  6. `architecture.md v6` inline-tagged amendments(per ADR-0033/0034)— `§3.3` chunker tuning note + `§3.7` query expansion note(doc-version not bumped — ADR is record per W17 precedent)
  7. `COMPONENT_CATALOG.md` C01 Ingestion Pipeline + C04 Retrieval Engine status update(ADR-0033 / 0034 reference)
  8. Closeout commit:`docs(planning): close W25 retro` + status frontmatter flip `active → closed`
- **Effort estimate**:~4-6h(retro 2h + cross-doc sync 2h + commit + buffer)
- **Owner**:AI(draft);Chris(review + sign-off)

## 3. Success Criteria(Phase Gate)

| # | Criterion | Target | Measure | Block phase closeout? |
|---|---|---|---|---|
| G1 | **Image association rate** | ≥ 5/8 image-bearing queries 嘅 citation 帶圖(pre-W25 = 0/8) | F2 5-8 query eval set + F6 manual measurement | **Yes** |
| G2 | **Gate 1 R@5 non-regression** | R@5 ≥ 0.92(W2 baseline 0.9722,-5pp envelope) | F2 + F6 RAGAs eval | **Yes** |
| G3 | **Gate 2 4-metric non-regression** | all 4 metric within 5pp of W6 baseline | F4 + F6 RAGAs eval | **Yes** |
| G4 | **Latency budget** | P95 < 5s on full query pipeline | F4 + F6 measurement | **Yes** |
| G5 | **ADR-0033 + ADR-0034 status Accepted** | both Accepted by Chris | F7 review | **Yes** |
| G6 | **Manual user-test** | ≥ 4/5 image-bearing queries 帶 section 嘅圖 | F6 manual | **Yes** |

## 4. Risks(Phase-Specific)

| # | Risk | Likelihood | Impact | Mitigation |
|---|---|---|---|---|
| R1 | **Gate 1 R@5 regression** post D3 chunker change(chunk count / boundary 變化破壞 W2 baseline)| Med | **High**(Block W25 closeout per G2 hard gate) | F1 unit test 加 chunk count change envelope ±20%;F2 早期 catch R@5 < 0.92 → ADR-0033 amendment;back-out option = revert `low_value_floor` 60 → 100 |
| R2 | **RAGAs 4-metric regression** post D4 query expansion(reformulation 引入 off-topic chunks → Faithfulness drop)| Med | **High**(Block W25 closeout per G3) | F3 unit tests catch RRF correctness 早;F4 verify 早 catch metric drift;back-out option = disable `enable_query_expansion` by default,留 plumbing on `KbConfig` opt-in |
| R3 | **Latency budget overshoot** post D4(P95 > 5s)| Med | Med(degrade UX but not block) | F4 measurement 早 catch;fall back 2-query 變體;若仍超 cap,disable by default(同 R2 back-out)|
| R4 | **D3 chunker change require re-ingest of production KBs**(Beta-track) | Low(per user default Q2 dev-only)| Med | W25 scope explicit dev-only re-ingest;production KB re-ingest 留 W16 Track A cred 通咗先 batch process(carry over W26+) |
| R5 | **F4 eval set inadequacy**(v0 6 samples 唔夠 cover image-association scenario,supplementary 5-8 queries 非 SME-labelled,signal noisy)| Med | Low-Med | F4 image hit rate 屬 soft gate(non-blocking);G1 measure 仍要 Gate;若 signal too noisy → CH-003 amendment expand eval set OR carry to eval-set-v1 W19+ |
| R6 | **R8 corp-proxy block** on new dependency(若 D4 需要新 LLM SDK e.g. Anthropic-style streaming reformulation 而 Azure OpenAI SDK 已有 cover 唔到)| Low(預想 reformulation 用現有 GPT-5.5-mini chat completion API)| Med | F3 design 用現有 Azure OpenAI SDK + chat completion endpoint;若需新 SDK → ADR-0017 occurrence #9 + Plan B (a/b/c) cascade |
| R7 | **CH-003 D2 weight × 0.7 太進取 / 太保守**(image+low_value chunks 競唔過 normal chunks OR 反而排太前 push 走 relevant non-image)| Low-Med | Low | F5 verify 早期 sample query 觀察 ranking;empirical adjust to 0.5 / 0.8 per F6 verify if needed |

## 5. Day-by-Day Breakdown(rough,~20 working days ≈ 3 calendar weeks per AI compression precedent ~3-7×)

| Day | Date(planned)| Focus | Deliverables targeted |
|---|---|---|---|
| D0 | 2026-05-23 | Kickoff — plan + checklist + progress | F0 meta |
| D1-D3 | 2026-05-24 ~ 2026-05-26 | F1 — ADR-0033 draft + chunker code change + unit tests | F1 |
| D4-D5 | 2026-05-27 ~ 2026-05-28 | F2 — re-ingest dev KBs + Gate 1 + RAGAs run + analysis | F2 |
| D6-D9 | 2026-05-29 ~ 2026-06-01 | F3 — ADR-0034 draft + query reformulator + result fusion + tests | F3 |
| D10-D11 | 2026-06-02 ~ 2026-06-03 | F4 — RAGAs regression + latency budget check | F4 |
| D12-D15 | 2026-06-04 ~ 2026-06-09 | F5 — CH-003 spec + D2 + D1 implementation + tests | F5 |
| D16-D17 | 2026-06-10 ~ 2026-06-11 | F6 — manual user-test + image association measurement | F6 |
| D18-D19 | 2026-06-12 ~ 2026-06-13 | F7 — retro + cross-doc sync + closeout commit | F7 |

**Real-calendar collapse note**:per W12-W18 / W20-W24 AI compression pattern,actual elapsed time **likely** ~3-7× faster than calendar-day estimate(eg. W20 ~12× / W22 ~5-10× / W23 ~1.5×);呢個 plan 嘅 calendar 估算保守 envelope,實際可能 1-2 weeks。

## 6. Dependencies on Prior Phase

Carry-over from **W24c-users-rbac retro**(per session-start.md §11 "CLOSED by W24c-users-rbac" block + plan §6 reference)— **none directly** ;但 phase-level inheritance:

- **R8 corp-proxy mitigation pattern**(ADR-0017,9 occurrences cumulative)— 若 F3 需要新 dependency 立即觸 Plan B cascade(R6 risk)
- **Pre-active-flip 5-step grep verification recursive scope**(per CLAUDE.md §10 R6 W23 F3 amendment + W22 D1+D6+D7+D8+D9 5-pattern catalog)— **applies recursively to W25 plan-text itself**(本 plan 引用 W2 / W6 baseline / `eval-set-v0.yaml` / `layout_aware.py:271-279` 等 reference,F1 active flip 之前必 grep verify upfront — see Day 0 progress entry)
- **Smoke-user-deferred allowance**(W12-W18 / W20-W24 pattern)— 任何 final interactive browser smoke / multi-viewport / dark-mode visual verify 屬 user pre-Beta scope;W25 唔 attempt online browser verify(無 frontend / UI 改動)
- **L3 routing NOT triggered**(per W5 D2 Gate 2 PARTIAL PASS verdict)— D4 query expansion 屬 retrieval-side 改善,不同 L3 routing concept(L3 routing 仍 defer post-Gate 2 STRONG PASS upgrade attempt 未觸發)

呢個 phase **唔依賴** Track A IT cred populate event(W16 F1)—— 所有 F1-F7 work 屬 AI-controllable backlog,類似 W17 beta-hardening parallel-track pattern。

## 7. Plan Changelog

| Date | Change | Reason | Approver |
|---|---|---|---|
| 2026-05-23 | Initial plan — D3 + D4 + D2 + D1 phase-level scope per Path III user pick;F1→F2→F3→F4→F5→F6→F7 sequence;5 design defaults locked(eval-v0+image / dev-only re-ingest / floor 100→60+merge / P95<5s / D2 weight 0.7) | Chris chat 2026-05-23 確認(a)(b)(c)全部 default OK | Chris |
| 2026-05-23 | **R6 pre-active-flip recursive grep verification** at Day 0 kickoff — catch 4 plan-text contaminations upfront(per CLAUDE.md §10 R6 + W23 F3 amendment + memory `feedback_design_fidelity.md` D9 plan-text-contamination pattern):**(i)** `low_value_floor` 喺 `layout_aware.py:35` 係 module-level constant `_TOKEN_LOW_VALUE_FLOOR = 100`(per `architecture.md §3.3` soft floor cite)+ class param `low_value_floor` default(`:69`)→ F1.2.1 change 落 module constant level + ADR-0033 cite `§3.3` amendment;**(ii)** `hybrid_searcher.py` 實際係 `backend/retrieval/hybrid.py` ——plan-text inaccurate naming;**(iii)** Retrieval 現有 low_value filter 係 **Azure Search server-side OData filter** `enabled eq true and low_value_flag eq false`(`hybrid.py:4 + :41`),**唔係** Python `if` filter —— **D2 implementation 唔可以單純 add condition**,要由 server-side filter pattern 改為:filter clause 改 `enabled eq true`(去掉 low_value_flag clause)+ post-filter Python override(`if low_value_flag and embedded_images_json: keep weight × 0.7;else if low_value_flag and not images: drop;else: keep full`)→ **D2 由 retrieval policy 改動觸 H1 boundary,**ADR scope re-examine 喺 F5 spec drafting 時 confirm:CH-003 alone vs CH-003 + co-ADR;若 retrieve filter pattern change 屬 §3.6 spec interface boundary → **可能要 ADR-0035** co-shipped;F5.1.2 spec draft 必先 surface 呢個 H1 trigger 風險畀 Chris 決定;**(iv)** `eval-set-v0.yaml` 位置 = `docs/eval-set-v0.yaml`(not `backend/eval/`)—— F2.2.1 path reference 已 plan-correct,無 amendment 需要 | R6 recursive scope catch upfront before F1 active flip;applied to plan-text 自己 per CLAUDE.md §10 R6 + W23 F3 W22 D9 cumulative empirical pattern | AI(R6 self-audit at Day 0)|

---

## 8. Locked Design Decisions(from user chat 2026-05-23,Path III default pick)

| # | Question | Default(locked)| Rationale |
|---|---|---|---|
| **Q1** | F2 / F4 / F6 eval set version | `eval-set-v0.yaml` 6 samples + 自家寫 5-8 image-bearing queries `eval-set-v0-image-queries.yaml`(non-SME-labelled supplementary) | v1 SME labels not done(Q14 SME labels Resolved but eval-set-v1 file final not exist per session-start.md CO_W15_F1_eval_set_v1);image queries只測 association,non-blocking via supplementary(per memo §6 D1-D4 recommendation chain) |
| **Q2** | F2 re-ingest scope | **dev KBs only**(`sample-doc-with-image-1` + `sample-kb-test-1` + `sample-doc-for-rag-knowledge-1`) | Beta-track production KBs(若有 prod data)留 W16 Track A IT cred populate 通咗先 batch re-ingest(out of W25 scope) |
| **Q3** | F1 D3 chunker tuning approach | **兩樣都做** ——(a)`low_value_floor: 100 → 60`(治標)+(b)adjacent-short-merge(治本)combined 一個 ADR-0033 | 60% low_value flagged ratio = 100 太 aggressive empirical signal;single ADR avoids splitting decision |
| **Q4** | F3 D4 latency budget cap | **P95 < 5s hard cap**;若 implementation 超 cap → fall back 2-query 變體(original + 1 reformulation only) | UX latency budget;back-out option preserved |
| **Q5** | F5 D2 image+low_value soft-relax weight | **× 0.7**(輕微 demotion,still competitive) | Start point;empirical adjust to 0.5 / 0.8 per F6 verify if needed(captured under R7 mitigation)|

---

## 9. Component Impact Map

| Component | Pre-W25 status | W25 impact | Post-W25 expected |
|---|---|---|---|
| **C01 Ingestion Pipeline**(`layout_aware.py`) | ✅ Implemented(W20 F4.2 + W2 baseline) | **F1 D3 chunker re-tune**(low_value_floor 60 + adjacent-short-merge) | ✅ Implemented(updated;ADR-0033 reference) |
| **C04 Retrieval Engine**(`hybrid_searcher.py`)| ✅ Implemented(W3 Cohere + W6 v4.0-pro) | **F5 D2 retrieval low_value soft-relax**(image-bearing chunks weight × 0.7) | ✅ Implemented(extended;CH-003 reference) |
| **C04 / C05 Pipeline**(`query_pipeline.py` + `query_reformulator.py` NEW + `result_fusion.py` NEW)| ✅ Implemented | **F3 D4 query expansion / RAG-fusion** NEW modules | ✅ Implemented(expanded;ADR-0034 reference) |
| **C05 Generation**(`citation_enrichment.py` + `citation_image_neighbors.py` NEW)| ✅ Implemented(W3 + W20 F3) | **F5 D1 citation post-process** for adjacent images | ✅ Implemented(extended;CH-003 reference) |
| **C06 Eval Framework** | ✅ Implemented(W17 F3 RAGAs 4-metric integrated)| F2 + F4 + F6 regression run(no module change,exercise existing harness)| ✅ Implemented(verified)|

無 H7 design fidelity trigger —— 全屬 backend pipeline改動,frontend `<ImageGallery>` 同 chat citation viewer 預期通過 schema field extension(`aux_embedded_images`)自動受惠,無 visual surface change required。

---

**Lifecycle reminder**:呢份 plan locked after Day 0 kickoff commit landed。重大 deviation(eg. ADR-0033 amendment / D4 disabled by default / scope add)入 §7 Plan Changelog;小 detail 變動(eg. effort estimate update)可直接 inline edit。
