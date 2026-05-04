---
phase: W05-optimization
plan_ref: ./plan.md
checklist_ref: ./checklist.md
status: in-progress     # flipped 2026-05-04 W5 D1 kickoff per user "現在可以啟動 W5 D1" signal
---

# Phase W05 — Progress

> Daily progress + 結尾 retro。
> 每 commit 必須對應一個 Day-N entry mention(R2 binding rule per PROCESS.md §5)。
> Status:`draft` 直到 W4 D5 closeout sign-off + W5 kickoff approval + procurement landing trigger。

---

## Day 0 — 2026-05-04: Kickoff prep(W4 D5 末 closeout 同 session)

**Action**:Phase W05 kickoff prep(per PROCESS.md §2.3 rolling-JIT lifecycle + W4 D5 closeout 同 session per CLAUDE.md §10 R5)

- Folder `docs/01-planning/W05-optimization/` created
- `plan.md` filled with status=`draft`(6 deliverables F1-F6:Gate 2 LIVE close + CRAG threshold fine-tune + L3 routing conditional + reranker per-KB field reconsideration + W4 carry-overs LIVE smoke remainder + closeout retro)
- `checklist.md` derived from plan deliverables(~32 atomic items)
- `progress.md` Day 0 entry initialized(this file)
- **Carry-over candidates from W04-crag-eval-shootout**(per W4 retro § Carry-overs C1-C11):
  - C1 Gate 2 LIVE verdict close → **F1**(blocking gate)
  - C2 Cohere Marketplace endpoint+key populate → **F1.1**
  - C3 ~~Voyage + ZeroEntropy procurement~~ **DROPPED W5 D1 per Karpathy §1.2** — Cohere + Azure semantic 2-way satisfies Gate 2 verdict policy;Tier 2 alternative candidates 留 future
  - C4 Azure semantic config verify → **F1.3**
  - C5 Chris SME chunk_id labeling → **F1.4**
  - C6 Eval-set v1 promote → post F1.4 cascade(non-deliverable;SME-bound)
  - C7 F9 PPT orchestrator E2E smoke → **F5.1**
  - C8 F5/F6/F7 LIVE smoke remainder → **F5.2-F5.4**
  - C9 Reranker per-KB field reconsideration → **F4**
  - C10 CRAG threshold empirical fine-tune → **F2**
  - C11 plan estimates calibration 0.3x heuristic → applied W5 plan §2 effort estimates(每 deliverable 0.5-1h baseline)
- **Gate 2 critical context inherited from W4**:per architecture.md §6.3 + W4 plan §F10 fallback path "Cohere baseline pending — partial verdict on available rerankers" — Gate 2 LIVE verdict 是 W5 D1 critical path;PASS = continue Tier 1 W5+ optimization(F2 + F3 + F4)/ FAIL = ADR-0012 + drop L2 CRAG → baseline-only + W5 D2-D5 fork to W6 demo prep early-start
- **Procurement timeline transparency**:
  - Cohere Marketplace endpoint(7-14d turnaround from 2026-05-04 trigger;ETA 2026-05-11 to 2026-05-18)
  - Voyage rerank-2.5 API key(direct,non-Azure path;Chris async)
  - ZeroEntropy zerank-1 API key(direct,non-Azure path;Chris async)
  - Azure semantic ranker(built-in S1 SKU;non-procurement;F1.3 verify-only)
  - Chris SME chunk_id labeling(per Q14 SME cascade;unbounded but target W5 D1)

**Status update will follow at W4 D5 closeout commit**(W4 frontmatter `active → closed` + Chris approve W5 kickoff trigger → W5 status `draft → in-progress`)。If W4 G1+G3+G4+G5 hard gates FAIL(structural)→ W5 plan **does not flip in-progress**;HALT POC per architecture.md §6.3,foundation iteration loop replaces W5。當前 W4 closeout = G1+G3(structural)+G4+G5 PASS / G2+G3(LIVE)+G6 explicit DEFER → W5 promotion pending Chris kickoff sign-off + procurement landing trigger。

---

## Day 1 — 2026-05-04 (Mon — same-session continuation per "現在可以啟動 W5 D1" signal)

> Per plan §5 D1 = F1 Gate 2 LIVE close。Same-day W3+W4+W5 momentum continues。Initial scope discovery + Voyage/ZeroEntropy drop decision + procurement state verification。

### Done

#### F1.0 — Procurement state discovery + scope simplification

- **`.env` load verification**(F1.0 boolean-only check via `Settings`):
  - ✅ `azure_openai_api_key`(Q3 Resolved + W3 D1 后段 populated)
  - ✅ `azure_search_admin_key`(Q4 Resolved + W2 D5 populated)
  - ✅ `cohere_api_key`(Q5 Path A procurement landed W3 D1 後段)
  - ⚠️ `cohere_endpoint`(False — F1.1 仍需 Chris populate Path A Marketplace endpoint OR Path B `https://api.cohere.com` fallback)
  - ❌ `voyage_api_key`(DROPPED W5 D1 per user decision)
  - ❌ `zeroentropy_api_key`(DROPPED W5 D1 per user decision)
  - ❌ `langfuse_public_key`(W3 deferred — non-critical for Gate 2)
- **Path resolution learning**:Pydantic Settings `env_file=".env"` 路徑相對 cwd → 必須由 project root 跑(W4 driver scripts 全部已 from project root)。F1.0 initial run 由 backend/ 跑導致 false negative,corrected by re-run from project root

#### Voyage + ZeroEntropy DROP decision(close W4 C3 NOT NEEDED — per Karpathy §1.2)

- **User signal**:「如果唔係必須, 咁把它們先drop吧」per W5 D1 conversation 2026-05-04
- **Rationale documented**:Cohere v3.5(H2 LOCKED W3 baseline)+ Azure built-in semantic ranker(S1 SKU bundled,no procurement)2-way comparison **already satisfies** Gate 2 4-metric within-5pp verdict policy per architecture.md §6.3。Voyage / ZeroEntropy 屬 alternative Tier 2 candidates;procurement burden(non-Azure path + monthly billing)+ low marginal value(Cohere 業界 +10-20% R@5 lift over hybrid baseline,satisfies Tier 1 quality)= drop pragmatically
- **Code preservation**:W4 D3 落地嘅 `VoyageReranker` + `ZeroEntropyReranker` class + 21 unit tests **preserved as future-proof scaffold**(Tier 2 / Beta+ 將來 evaluate);`run_reranker_shootout.py` skip-row fallback automatically handles SKIPPED rows,driver-side無需改動;`Settings` 8 NEW fields kept for同樣 reason
- **Q21 narrowed**:reranker final pick 由 4-way → **Cohere vs Azure semantic 2-way**;若 F1.6 LIVE shootout Cohere PASS → Q21 Resolved as `cohere-v3.5`;若 FAIL → escalate per ADR-0012(drop L2 CRAG)

#### W5 plan + checklist + W4 retro carry-overs C3 + W5 progress Day 0 update

- W5 plan §1 scope:Voyage + ZeroEntropy DROPPED note + Cohere endpoint Path A/B clarification + R2 marked N/A + carry-over C3 strikethrough
- W5 plan §2 F1.2 simplified;F1.6 reduced 5-way → 3-way(hybrid-only / cohere / azure;Voyage + ZeroEntropy auto-SKIP)
- W5 plan §4 Risk R2 marked N/A
- W5 plan §6 Dependencies C3 strikethrough
- W5 plan §7 changelog entry per R3
- W5 checklist F1.2 Voyage + ZeroEntropy 兩個 row 標 [x] DROPPED + rationale;F1.1 Cohere endpoint clarification(Path A/B);F1.6 reduced 3-way
- W4 retro carry-over C3 strikethrough + DROPPED rationale + future-proof scaffold preservation note
- W5 progress Day 0 carry-over C3 strikethrough sync

### Surprises / Notes

- **Cohere endpoint missing但 api_key populated**:推測 Chris populated key 早於 endpoint(Path A Marketplace deploy 仍 7-14d turnaround)OR 用 Path B 但 endpoint URL 仍未 set 為 `https://api.cohere.com`。F1.1 acceptance criteria 已 clarify 兩個 path 嘅 endpoint format
- **W4 D3 4-way scaffold-first decision pays off**:Voyage + ZeroEntropy 雖然 W5 drop,但 21 unit tests + Settings fields + factory branches 全部留 — driver skip-row fallback 自動處理 SKIPPED rows = zero refactor cost。Karpathy §1.2 surgical principle 反例:「scaffold first then drop」反而比「drop fully + delete code」更 surgical(因為刪除 = touch多處;skip-row fallback = touch zero 處)
- **Voyage + ZeroEntropy 屬 Tier 2 candidates 唔等於垃圾**:Tier 1 Cohere + Azure semantic 2-way 滿足現有 quality target;Tier 2 multi-tenancy / scale phase 若 R@5 quality regression OR cost spike,W4 D3 scaffold ready-to-evaluate(只需 procure key + 跑 shootout)。Future-proof preserved without near-term burden

### Next steps(等 Chris)

- **F1.1**:populate `.env` `COHERE_ENDPOINT` — Path A `https://<cohere-deployment>.<region>.models.ai.azure.com` OR Path B `https://api.cohere.com` + `COHERE_PROCUREMENT_PATH=B`
- **F1.3**:verify Azure semantic config `ekp-semantic-default` exists on `ekp-kb-drive-v1` index;create if missing
- **F1.4**:start chunk_id labeling cascade per Q14 SME(blocking strict-mode RAGAs;keyword-mode acceptable for 1st-pass Gate 2)
- F1.5-F1.8 LIVE drivers:once F1.1 + F1.3 land,AI runs `run_cohere_lift_smoke.py` + `run_reranker_shootout.py --subset 10`(cost containment)+ `run_ragas_eval.py --subset 20`,emit Gate 2 procedural verdict

### Actual vs Planned Effort

| Item | Planned (h) | Actual (h) | Variance | Note |
|---|---|---|---|---|
| F1.0 procurement state discovery + path resolution learning | 0.2 | 0.1 | -0.1h | Boolean-only Settings dump |
| Voyage + ZeroEntropy drop docs propagation(W5 plan §1+§2+§4+§6+§7;W5 checklist F1.2;W4 retro C3;W5 progress Day 0+Day 1)| 0.5 | 0.4 | -0.1h | Surgical edit pattern;multi-file but each edit narrow |
| Cohere v3.5 → v4.0-pro spec drift document + accept(per architecture.md §3.2 same-vendor model upgrade,non H1+H2 violation per same-vendor doctrine)| 0.2 | 0.2 | 0 | Path 1 user decision documented inline in conversation |
| F1.5 LIVE Cohere v4.0-pro lift smoke(initial $2.85 cost overshoot due to Bug B + retry $0.10 post-fix)| 0.5 | 0.6 | +0.1h | Bug B subset cost overshoot caused first call;retry clean |
| F1.6 LIVE 3-way shootout(initial errored=15 azure;Bug C+D fix retry;final clean run)| 0.5 | 0.7 | +0.2h | 2 retry cycles for Azure config name + queryLanguage deprecation |
| F1.7 LIVE RAGAs subset=5(Bug F+G+H surfaced;Path A monkey-patch wrapper)| 1.5 | 2.5 | +1.0h | Largest variance — systematic GPT-5 ↔ ragas 0.4.3 incompatibility required wrapper architecture decision + 3 retry cycles |
| Bug A+B encoding+subset cost containment fix(EvalRunner.run max_main_queries + ASCII labels)| 0.5 | 0.4 | -0.1h | Surgical EvalRunner change |
| Bug C+D+E Azure semantic config name + queryLanguage + mojibake | 0.4 | 0.4 | 0 | Direct REST probe revealed root cause cleanly |
| Bug F+G temperature drop + AsyncAzureOpenAI switch + ragas 0.4.3 collections API refactor | 0.7 | 1.0 | +0.3h | API rewrite per ragas 0.4.3 collections module structure(LangchainLLMWrapper deprecated;per-metric ascore signature divergence)|
| Bug H Path A monkey-patch(initial proxy class fail isinstance → monkey-patch preserves type)| 0.5 | 0.6 | +0.1h | instructor.from_openai isinstance check forced architecture refinement |
| W5 D1 progress entry + commits + checklist tick + closeout doc(this entry)| 0.5 | 0.7 | +0.2h | This entry — 8-bug timeline + Path A wrapper rationale 較長 |
| **Total D1(AI-side)**| **5.5** | **7.6** | **+2.1h** | W4 0.3x heuristic 仲低估;系統性 vendor compat surprise(GPT-5 reasoning model ≠ legacy GPT-4 chat completions API)係 dominant cause;wrapper 架構決定 + 8-bug 連鎖 makes D1 嘅 LIVE work calendar-bound 而非 effort-bound |

### Commits

| Hash | Subject |
|---|---|
| `c394ee5` | `docs(planning): W5 D1 — drop Voyage + ZeroEntropy per Karpathy §1.2; F1 simplified to Cohere + Azure semantic 2-way` |
| `e15a2d6` | `docs(planning): backfill W5 D1 commit hash (c394ee5)` |
| `5a00bcd` | `fix(eval): subset cost containment + ASCII output (W5 D1 Bug A+B)` |
| `4c43e96` | `fix(c04): Azure semantic reranker — config name + queryLanguage + mojibake (W5 D1 Bug C+D+E)` |
| `38ea9b1` | `fix(generation): GPT-5 reasoning model compat — drop temperature; switch ragas async client (W5 D1 Bug F+G partial)` |
| `8b1c3da` | `fix(eval): Path A — monkey-patch GPT-5 param translation on ragas judge client (W5 D1 Bug F+H closure)` |
| _pending_ | `docs(planning): W5 D1 closeout — Path A success + Bug A-H timeline + F1.5/F1.6/F1.7 LIVE results + defer subset=20 to D2` |

### F1.7 RAGAs LIVE 5-query results(reports/ragas-results.json)

> **Cohere v4.0-pro pipeline 4-metric evaluation, subset=5, evaluated=5 errored=0**

| Metric | mean | p95 | n | Interpretation |
|---|---|---|---|---|
| **Faithfulness** | 0.989 | 1.000 | 5 | Answer 高度 grounded in retrieved chunks(min 0.944 — Q005)|
| **Answer Relevancy** | 0.815 | 0.854 | 5 | Answer 直接回應 question(0.815 屬正常範圍 — answer 可能有 explanation 冗餘但仍 on-topic)|
| **Context Precision** | 0.978 | 1.000 | 5 | Retrieved chunks 對 question 高度 relevant(min 0.887 — Q001)|
| **Context Recall** | 1.000 | 1.000 | 5 | Retrieval cover 全部 reference info(perfect across 5/5 queries)|

**Per-query breakdown**:
```
Q001: faith=1.000 rel=0.755 prec=0.887 recall=1.000
Q002: faith=1.000 rel=0.832 prec=1.000 recall=1.000
Q003: faith=1.000 rel=0.804 prec=1.000 recall=1.000
Q004: faith=1.000 rel=0.827 prec=1.000 recall=1.000
Q005: faith=0.944 rel=0.854 prec=1.000 recall=1.000
```

**統計 caveat**:n=5 sample size 對 Gate 2 verdict 4-metric within-5pp 互換 評估 underpowered — variance estimate 不穩。建議 W5 D2 scale to subset=20 提供 robust baseline + 加 Azure semantic 2-way comparison(若 architecture.md §6.3 verdict policy 嚴格要求 ≥2 reranker 比較)。

### Bug A-H timeline + W5 D1 Karpathy lessons

| Bug | Symptom | Root cause | Fix layer | Commit |
|---|---|---|---|---|
| **A** | UnicodeEncodeError 喺 driver stdout `📊 / 📁 / ✅ / ⚠️ / ❌` print | Windows console charmap codec 唔 encode emoji | Driver-level ASCII labels | `5a00bcd` |
| **B** | `--subset N` 只 cap 最終 lift table aggregation,API calls 跑齊 55 queries × 2 passes | EvalRunner.run() 全 query 跑;driver 後 slice;cost docstring 同 behavior 不一致 | EvalRunner.run accepts max_main_queries param;driver pass cap | `5a00bcd` |
| **C** | Shootout azure row evaluated=0 errored=15 | Settings default `azure_semantic_config_name` = `ekp-semantic-default` ≠ index schema reality `ekp-semantic-config`(W4 D3 typo,從未 cross-check W2 D5 schema)| Settings default + AzureSemanticReranker default + tests aligned | `4c43e96` |
| **D** | 400 "queryLanguage parameter is not valid" | api-version=2024-07-01 deprecated `queryLanguage` field;AzureSemanticReranker payload hardcoded `"queryLanguage": "en-us"` | Drop param;Tier 2 ZH/JP fallback note | `4c43e96` |
| **E** | SKIPPED reason 顯示 `per W4 plan �F3` | `§` Windows charmap codec replace 為 `�` | Drop `§` for cross-shell ASCII | `4c43e96` |
| **F** | 400 "temperature does not support 0.1 with this model" | GPT-5 reasoning model 只支援 default `1`;Synthesizer + CragGrader + RAGAs judge 全部 hardcoded 0.0 / 0.1 | temperature param default None → omit from chat.completions.create call | `38ea9b1` |
| **G** | "Cannot use agenerate() with synchronous client" | RAGAs metric.ascore() internally call `llm.agenerate()` which requires AsyncAzureOpenAI;driver originally use sync `AzureOpenAI` | Switch to `AsyncAzureOpenAI` for both judge + embed clients | `38ea9b1` |
| **H** | 400 "max_tokens not supported,use max_completion_tokens" | ragas 0.4.3 internal LLM call hardcoded `max_tokens` legacy GPT-4 param;GPT-5 rename to `max_completion_tokens`。Latest ragas == 0.4.3,no upstream fix | **Path A**:`_patch_for_gpt5(client)` monkey-patch chat.completions.create kwargs translate `max_tokens → max_completion_tokens` + drop `temperature` + drop `logprobs`/`top_logprobs` defensively | `8b1c3da` |

**Karpathy §1.1 think-before-coding lessons learned W5 D1**:
- **Surface不 hide confusion**:用戶 screenshot Azure portal 觸發我去 distinguish service-level vs index-level configuration → revealed Bug C(name typo)+ Bug D(API param deprecation)— 直接 REST probe 比 monkey-test driver 高效 root-cause root cause
- **Surgical Path A vs proxy fail**:initial implementation 用 proxy class wrapping AsyncAzureOpenAI → instructor.from_openai isinstance check fail → fallback to sync path → "Cannot agenerate" — 需 refine to monkey-patch live instance preserving type identity。lesson:third-party library type-check 邊界 surprise(需 `isinstance(client, openai.AsyncOpenAI)` pass)— "transparent proxy" abstract pattern 唔 always work 喺 isinstance-strict ecosystem
- **System incompatibility ≠ isolated bug**:Bug F + H 唔係兩條 bug 而係 systemic ragas 0.4.3 ↔ GPT-5 reasoning model API mismatch(同類 deprecation chain — temperature / max_tokens / 預期 logprobs 等)。pre-emptive defensive drop `_DROP_PARAMS = ("temperature", "logprobs", "top_logprobs")` 留將來 surface bug 嘅 expansion point
- **Path A monkey-patch vs Path B vendor swap**:keep Tier 1 stack lock(GPT-5.4-mini judge per §3.2 H2)+ surgical wrapper 比 procure GPT-4o-mini deployment 更貼 simplicity-first;wrapper code ~25 lines,不 affect synthesizer / crag / 任何其他 modules

### Surprises / Notes

- **GPT-5 reasoning model API 同 ragas 0.4.3 系統性 incompatibility**:單純 model 升級(GPT-4 → GPT-5)觸發 chat completions API spec 變化;ragas 0.4.3(2025 中發布,主要支援 GPT-4 / Claude legacy chat API)未 upgrade 對應 GPT-5 params(`max_completion_tokens` rename)。Tier 1 vendor lock list(architecture.md §3.2 H2)需要 acknowledge:當 vendor model deprecate 舊 API,tooling library 可能 lag behind。Path A monkey-patch 屬 mitigation;long-term 留 ragas upstream upgrade 或 swap to RagasOpenAI native judge
- **Azure AI Search api-version 2024-07-01 比 我地 W4 D3 reranker scaffold 更 strict**:`queryLanguage` 喺 newer api-versions 移除 → scaffold 必須 align deployment-time api-version。lesson:vendor REST API version 升級 = silent breakage,需 integration-test on first LIVE call 確認
- **Path A monkey-patch 對其他 W5 deliverables 無 spillover**:wrapper 只 touch RAGAs judge client edge,Synthesizer + CragGrader + reranker + EvalRunner 都唔受影響(Synthesizer 已 Bug F fix temperature drop;同樣 GPT-5.5 兼容)。Surgical scope contained
- **5-query RAGAs 4-metric 全 ≥ 0.815 mean** — Cohere v4.0-pro pipeline 信號強勁,Faithfulness + Context Precision + Context Recall 都 ≥ 0.978(near-perfect)。Answer Relevancy 0.815 is the binding constraint;若 W5 D2 subset=20 sustain 呢個 baseline → Gate 2 verdict 大概率 PASS

### Deferred to W5 D2

- **F1.7-extended** RAGAs `--subset 20` for robust statistical baseline(~12 min runtime + cost ~$15-25 USD judge LLM)
- **F1.6-extended** Azure semantic 2-way comparison via `run_ragas_eval --reranker azure`(若 driver supports;否則 swap `Settings.reranker_kind=azure` + re-run)— Gate 2 嚴格要求 Cohere baseline + winning reranker 4-metric within-5pp 互換,所以 Azure semantic 也需 LIVE RAGAs(cost 同樣 ~$15-25 USD)
- **F1.8** Gate 2 LIVE verdict landed:**PASS** = continue F2-F4 / **FAIL** = ADR-0012(drop L2 CRAG)
- **F1.9** Q5 + Q21 + relevant OQ follow-up note in `decision-form.md`
- **W5 D1 Path A wrapper unit tests** — 寫 4 tests covering`_patch_for_gpt5`(max_tokens rename / temperature drop / logprobs drop / no-op pass-through);non-blocking F1.7 LIVE但屬 H6 test coverage 應 backfill W5 D2

### Why pause W5 D1 here(Option 4 user decision per Path 1 confirm)

- **8 bugs A-H 連鎖** + **2 cumulative architectural decisions(Path 1 v3.5→v4.0-pro accept + Path A wrapper)**= W5 D1 cumulative effort 7.6h(plan 估 5.5h),variance +2.1h 反映系統性 incompatibility surprise
- **Cohere baseline RAGAs n=5 已通**(faith 0.989 / rel 0.815 / prec 0.978 / recall 1.000)— sufficient for Chris review state 而 不需要 trigger ~$30-50 全 subset=20 + Azure 2-way LIVE 之前 confirm path
- **Gate 2 verdict 仍 W5 critical path** — defer 到 W5 D2 不影響 Tier 1 timeline(W4 closeout已 mark Gate 2 verdict deferred);W5 D2 spend $30-50 補 robust verdict 屬 acceptable budget per W4 plan §4 R4
- **Chris review 後可能 redirect**:e.g. 揀 Option 1(直接 emit Gate 2 verdict on n=5 with caveat);揀 Option 3(Cohere subset=20 only,defer Azure to W6);揀 explicitly procure GPT-4o-mini deployment after seeing W5 D1 wrapper complexity;揀 swap Q21 reranker pick 直接 Cohere(skip Azure comparison since Cohere n=5 already strong)— 各條 path 對應不同 W5 D2 scope

---

## Day 3 — _(pending)_

---

## Day 4 — _(pending)_

---

## Day 5 — _(pending)_

---

## Retro(填於 W5 D5 末)

### What worked
_(W5 D5 末 fill)_

### What didn't work / unexpected friction
_(W5 D5 末)_

### Surprises / discoveries
_(W5 D5 末)_

### Carry-overs to W06-final-eval-demo
_(W5 D5 末)_

### ADR triggers
_(W5 D5 末 — ADR-0012 reserved for(a)Gate 2 LIVE FAIL → drop L2 CRAG OR(b)reranker per-KB field STICKY decision per W3 C5 + W4 C9)_

### Phase Gate result(per plan.md §3 + architecture.md §6.3)
- G1-G6:_(W5 D5 末)_
- **Gate 2 LIVE verdict**:_(W5 D5 末)_ → PASS continues Tier 1 W5+ optimization landed;FAIL drops L2 CRAG → baseline-only + W6 demo prep early-start

### Phase status
- Closeout commit:_(W5 D5 末)_
- Frontmatter status flipped to `closed`:_(W5 D5 末)_
- Phase W06 kickoff trigger:_(W5 D5 末 — W6 plan scope contingent on Gate 2 LIVE verdict + Tier 1 path PASS/FAIL)_

---
