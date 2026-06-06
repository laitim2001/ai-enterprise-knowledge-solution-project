# EKP Tier 1 — Eval Methodology

> **目的**:本文件定義 EKP Tier 1 嘅 measurement framework。包括 4 個 success metric 嘅 formal definition、eval set 嘅 schema + annotation guideline、RAGAs + LLM-as-judge pipeline 嘅 integration、Reranker Mini-Shootout 方法、同 measurement bias 嘅 honest disclosure。
>
> **目標讀者**:Claude Code(implementation reference)、Chris(audit measurement validity)、Domain Expert(annotation guideline)、Stakeholder(verify metric methodology)
>
> **適用版本**:EKP spec v5 / decision-form v1
> **最後更新**:2026-04-27

---

## 1. Measurement Philosophy

### 1.1 為何 4 個 metric 而唔係單一「accuracy」

「90% 準確率」呢類 single metric 對 RAG 系統**結構上 unmeasurable**。原因:

- 「準確率」係邊個層面?Retrieval 揾啱 chunk?LLM 答案 truthful?Citation 對唔對?圖片正確?**呢 4 件事可以 individually 失敗**,單一 metric 隱藏 root cause。
- Stakeholder 喺 W6 demo 質疑「點解唔係 90%」嘅時候,team 必須拎得出**呢個 metric measure 緊邊一層、其他層 status 係咩**。

EKP 用嘅 4 metric 對應 RAG 系統嘅 4 個獨立 failure mode:

| Metric | 對應 failure mode | 失敗症狀 |
|---|---|---|
| **Retrieval Recall@5** | Retrieval 撈唔到 relevant chunk | 答案根本冇用啱 source |
| **Answer Faithfulness** | LLM hallucinate(retrieval 撈啱但 LLM 亂講) | 答案脫離 retrieved chunk 內容 |
| **Answer Correctness** | 整體答案正不正確(retrieval + LLM 共同決定) | 用戶覺得答案唔啱用 |
| **Image Association** | 答案 cite 嘅 screenshot 對唔對 | 文字 cite step 7 但顯示 step 5 嘅圖 |

呢套 metric 已經喺 spec §1.6 同 decision-form Q8 lock,本文件係 measurement 嘅 operational doc。

### 1.2 Technical Metric vs Business Impact Metric 嘅分別

EKP 有兩組 metric,本文件**只 cover Technical(W6 POC gate)**:

| 組別 | Metric | Measure 階段 | 本文件 cover? |
|---|---|---|---|
| Technical | Recall@5、Faithfulness、Correctness、Image Association | W4 + W6 Gate | ✅ Yes |
| Business Impact | Time-to-answer reduction、Shadow AI displacement、User satisfaction | Beta phase(W7+) | 略,僅參考 spec §1.7 |

Business metric 嘅 measurement methodology(stopwatch sessions、user survey schema)由 Beta plan 另立文件處理(W6 末 prepare)。

### 1.3 設計原則

| 原則 | 描述 |
|---|---|
| **Reproducible** | Same eval set + same config → same metric numbers(within ±2pp variance) |
| **Auditable** | 每個 score 都可以 trace 返 query / retrieved chunks / LLM output / judge reasoning |
| **Bias-disclosed** | LLM-as-judge bias、synthetic eval bias 必須 explicit 列(see §10) |
| **Cost-bounded** | 跑一次 full eval(50 queries × 4 metrics)< USD 10 |
| **Decision-driven** | Metric 數字直接 feed Gate 1 / Gate 2 / W6 Final(see §8) |

---

## 2. Metric Definitions(formal)

### 2.1 Retrieval Recall@5

**定義**:對於 eval set 入面每條 query,**ground truth 標明嘅 primary chunk**(或 acceptable chunks 之一)有冇出現喺 reranker 之後嘅 top 5?

**Formula**:

```
Recall@5 = (count of queries where any ground_truth.acceptable_chunk_ids ∈ top_5_chunk_ids) / total_queries
```

**Pipeline 點 measure**:
1. 對 eval set 每條 query,run full retrieval pipeline 直到 reranker 出 top 5
2. 攞 top 5 chunk_ids
3. 對比 ground truth 嘅 `acceptable_chunk_ids` list
4. 任何 intersection → hit;empty intersection → miss
5. Aggregate hit rate

**唔係 measure**:
- ❌ Top-1 accuracy(EKP 用 top-5,因為 LLM 用 5 chunks 做 synthesis,top-1 太嚴)
- ❌ Mean Reciprocal Rank(MRR,過於 retrieval-engineer-flavor,stakeholder 唔易理解)
- ❌ NDCG@10(用喺 §7 reranker shootout,但 main metric 用 Recall@5 simpler)

**Target**:≥ 90%(spec §1.6)
**Stretch**:≥ 95%

---

### 2.2 Answer Faithfulness

**定義**:LLM 嘅答案有冇基於 retrieved chunks 講嘢?即係答案嘅每個 claim 係咪可以 trace 返 retrieved 上下文?

**Formula**(沿用 RAGAs 標準):

```
Faithfulness = (count of claims supported by retrieved chunks) / (total claims in answer)
```

**Pipeline 點 measure**:
1. 對 eval set 每條 query,run full pipeline 出 final answer + retrieved chunks
2. Pass(query, answer, retrieved_chunks) 入 RAGAs `faithfulness` metric
3. RAGAs 內部用 GPT-5.5 Pro:
   - **Step A**:從 answer 抽出所有 atomic claim(e.g.「按 lever」「等 30 秒」)
   - **Step B**:對每個 claim,問 judge:呢個 claim 嘅 information 喺 retrieved_chunks 入面搵到 supporting evidence 嗎?(Yes / No)
   - **Step C**:Faithfulness = Yes count / Total claims
4. Aggregate across queries

**Why GPT-5.5 Pro 做 judge**:Spec §3.2 已 lock。Pro 嘅 parallel test-time compute 提升 judge consistency(同一 query 重跑 variance 較細)。

**Target**:≥ 95%
**Stretch**:≥ 98%

**Note**:Faithfulness ≠ Correctness。Faithfulness 只 check 答案有冇 stick to retrieved content;retrieved content 本身啱唔啱(chunk 係咪 ground truth 嘅 step)係 Recall@5 + Correctness 嘅 job。

---

### 2.3 Answer Correctness(human)

**定義**:領域專家盲審答案嘅整體質素,綜合判斷答案係咪解到用戶嘅問題。

**Formula**:

```
Correctness = (count of queries with answer rated "Acceptable" or above) / total_queries
```

**Rating scale**(SME 用):

| Rating | 描述 |
|---|---|
| **Excellent**(2 分) | 答案準確、完整、cite 啱 source |
| **Acceptable**(1 分) | 答案大致準確,minor incompleteness 或 phrasing issue,但用戶可解到問題 |
| **Wrong**(0 分) | 答案 factually wrong、misleading、或 critical missing info |

**Pipeline 點 measure**:
1. 對 eval set 每條 query,run pipeline 出 final answer + citations
2. 將 (query, answer, citations) anonymize(SME 唔知道 answer source 係 EKP 邊個版本 / 邊個 config)
3. SME 標 rating(Excellent / Acceptable / Wrong)
4. Correctness = (Excellent + Acceptable) / total

**Target**:≥ 80%(Excellent + Acceptable 合計)
**Stretch**:≥ 90%

**Why 人工 + 為何 binary-ish 而非 5-point Likert**:
- LLM-as-judge for correctness 嘅 inter-rater reliability 對 EKP 場景未驗證,POC 階段 SME 信號 strongest
- 5-point Likert 增加 SME workload + 增加 inter-rater variance(SME 之間「3 vs 4」分歧大過「Acceptable vs Wrong」)
- 3-tier scale 平衡 simplicity + signal richness

**SME workload estimate**:
- POC W4 + W6 各跑一次 full eval(50 queries)
- 每條 query rating 估 2 分鐘(read query + answer + check citations)
- 50 queries × 2 min = ~100 min per round
- 2 rounds = ~3.5 工作小時

---

### 2.4 Image Association Accuracy

**定義**:LLM 答案 cite 嘅 screenshot 屬於正確嘅 chunk?

**Formula**:

```
Image Assoc = (count of queries where cited screenshots ⊆ ground_truth.expected_screenshot_chunks) / total_queries
```

**Pipeline 點 measure**:
1. 對 eval set 每條 query,run pipeline 出 answer + citations,citation 包括 `chunk_id` 同對應 `screenshot_blob_url`
2. Ground truth 提供 `expected_screenshot_chunks`(list of chunk_id)
3. 對每條 query,對比 cited chunk_ids vs expected_screenshot_chunks
4. **Hit 條件**:每個 cited chunk 都喺 expected list 內(strict)
5. **Partial hit policy**:partial 算 miss,因為錯配 image 對用戶 confusing

**Target**:≥ 85%
**Stretch**:≥ 95%

**Edge cases**:
- Ground truth chunk 無 screenshot → expected_screenshot_chunks empty → cited 0 個 image OK
- LLM cite chunk_id 但 chunk metadata 無 image → 答案展示「無圖」placeholder,自動 hit(spec §7.3 E3)

---

## 3. Eval Set Schema

Eval set 用 **YAML format**(human-readable + git-diff-friendly,優於 JSON)。

### 3.1 Schema Definition

```yaml
# eval_set_v1.yaml(會喺 docs/eval-set-v0.yaml 用呢個 schema)
metadata:
  version: "1.0"
  created_at: "2026-04-27"
  total_queries: 30
  composition:
    synthetic: 30        # by architect
    user_collected: 0    # to be added W4
  difficulty_distribution:
    easy: 15
    medium: 11
    hard: 4
  query_type_distribution:
    single_step_lookup: 18
    multi_step_synthesis: 9
    troubleshooting: 3

queries:
  - query_id: Q001
    query_text: "How do I clear a paper jam?"
    query_phrasing_source: synthetic    # synthetic | user_collected | expert
    difficulty: easy                    # easy | medium | hard
    query_type: single_step_lookup      # single_step_lookup | multi_step_synthesis | troubleshooting | oos
    
    ground_truth:
      primary_chunk_ids:                # 必須喺 top-5(highest priority chunk)
        - "kb-drive_doc-M042_chunk-0007"
      acceptable_chunk_ids:              # 任一喺 top-5 即 Recall@5 hit
        - "kb-drive_doc-M042_chunk-0007"
        - "kb-drive_doc-M042_chunk-0008"
      expected_screenshot_chunks:        # Image Association 對照
        - "kb-drive_doc-M042_chunk-0007"
      expected_answer_keywords:          # 答案應包含嘅 key phrase(soft check)
        - "lever"
        - "rear cover"
        - "30 seconds"
      expected_refusal: false            # OOS query 設 true,系統應拒答
    
    annotation:
      annotator: "<SME-name>"
      annotated_at: "2026-04-28"
      validated: true                    # SME 標完設 true
      notes: "Step 7 + step 8 都 acceptable,因為 step 7 講 lever、step 8 講開門"
```

### 3.2 Field 嘅 normative rule

| Field | Required? | Notes |
|---|---|---|
| `query_id` | Yes | Q001 起,zero-padded |
| `query_text` | Yes | < 500 char,無中英混合(現階段英文為主) |
| `query_phrasing_source` | Yes | `synthetic` 由 architect / dev 寫;`user_collected` 由真實用戶問;`expert` 由 SME 設計 |
| `difficulty` | Yes | 主觀但有 §3.3 嘅 guideline |
| `query_type` | Yes | 4 個 enum value |
| `ground_truth.primary_chunk_ids` | Yes | 至少 1 個,標明 highest-priority 答案 |
| `ground_truth.acceptable_chunk_ids` | Yes | superset of `primary`,可包含 acceptable alternative |
| `ground_truth.expected_screenshot_chunks` | Yes(可 empty list) | Empty list 代表呢條 query 無關 image |
| `ground_truth.expected_answer_keywords` | Optional | 用做 sanity check,唔係 metric 主信號 |
| `ground_truth.expected_refusal` | Yes | OOS query 設 true |
| `annotation.validated` | Yes | SME 必須 explicit set true 先算 ground truth ready |

### 3.3 Difficulty Guideline

| Difficulty | 條件 | 例子 |
|---|---|---|
| **Easy** | Single chunk 答案、明確 keyword overlap、用戶用 manual 嘅原話 | "How to reset device?" → step 直接寫 "Reset device" |
| **Medium** | 1–2 chunks、用戶用 paraphrase 而唔係原話、需要少量 reasoning | "What if my printer doesn't respond?" → ground truth 喺 troubleshooting section,但用戶冇用 "troubleshooting" 字眼 |
| **Hard** | Multi-chunks synthesis、ambiguous query、需要 cross-section reasoning | "How to setup the device for first-time user including network and security?" |

### 3.4 Query Type Guideline

| Type | 描述 | Eval set 比例 target |
|---|---|---|
| `single_step_lookup` | 答案喺單一 chunk 即可 | ~60% |
| `multi_step_synthesis` | 需 retrieve + synthesis 跨 2–3 chunks | ~30% |
| `troubleshooting` | 用戶描述 symptom,需 reverse-lookup procedure | ~10% |
| `oos`(out-of-scope) | 故意問 manual 冇答案嘅嘢,test refusal | 5 條 baseline + extras |

**OOS query 例子**:"What's the weather today?" / "List all employees" / "How to do open-heart surgery?"

---

## 4. SME Annotation Guideline

呢部分專為**領域專家(Q14 owner)**寫,做 ground truth 標註時跟住做。

### 4.1 Workflow Overview

```
Step 1:Architect / dev 出 candidate query(synthetic)+ initial ground truth proposal
   ↓
Step 2:SME review query 係咪合理(用戶真係會咁問?)
   ↓
Step 3:SME 用 EKP Admin Console 嘅 chunk inspector(spec §5.5.2)瀏覽相關 chunks
   ↓
Step 4:SME 標 primary_chunk_ids + acceptable_chunk_ids + expected_screenshot_chunks
   ↓
Step 5:SME set validated=true,sign annotator name + date
   ↓
Step 6:Commit annotated yaml 入 repo
```

### 4.2 標註原則

**Rule 1 — Primary 同 Acceptable 嘅分別**

- `primary_chunk_ids`:**最佳答案**嘅 chunk(通常 1 個)。若 retrieval 連 primary 都唔係 top-5,即係 retrieval 嚴重 fail
- `acceptable_chunk_ids`:**可接受答案**嘅 superset(包括 primary)。Adjacent step、similar procedure 都可以加入

**例**:Query "How to clear paper jam?",manual 有兩處講(simplified procedure step 7 + detailed troubleshooting section step 12)。
- Primary:step 7(simpler,first-time user 友好)
- Acceptable:[step 7, step 12](都答得到問題)

**Rule 2 — Expected Screenshot 唔等於 Primary chunk 嘅 screenshot**

某啲情況答案係 step 7,但用戶想睇嘅 image 屬於 step 8(因為 step 8 嘅圖 visualize 咗 step 7 嘅 outcome)。要 explicit 標 `expected_screenshot_chunks: [step_7, step_8]`。

**Rule 3 — Edge Case 嘅標註**

| Case | 點標 |
|---|---|
| Manual 完全無相關 step(query OOS)| `acceptable_chunk_ids: []`,`expected_refusal: true` |
| 答案散落多 manual | `acceptable_chunk_ids` 包含跨 doc 嘅 chunk_ids |
| Step 有圖但 image quality 差 | 仍標 expected_screenshot,UI 顯示 quality 同 ground truth measurement 無關 |
| Manual 寫法 ambiguous(SME 自己都 confused) | `notes` 記錄 ambiguity,query 移去 `hard` difficulty bucket |

**Rule 4 — Annotator Bias 自我 audit**

SME 標完 30 條後,**spot check 自己**:
- 有冇傾向 mark 自己熟嘅 manual 為 primary?
- 有冇傾向避用某啲 chunk?
- Difficulty 分佈係咪太 skew(全部 easy = eval 過寬)?

W4 加入 20 條 real user query 時,**SME 應該由唔同人 label**(避免 single-annotator bias)。

### 4.3 Annotation Tooling

POC 階段用 **YAML editor + EKP Admin Console**(chunk inspector):
1. SME 喺 EKP Admin Console search chunk(spec §5.5.2)
2. 確認 chunk_id 後 copy
3. 喺 yaml 填入

W2 後 dev 可考慮起一個簡單 CLI tool `python -m scripts.annotate_eval_set --interactive` 提升 SME 體驗,**但唔係 W1 deliverable**。

### 4.4 Quality Control

每完成一批 annotation,**dev run sanity check**:

```bash
uv run python -m scripts.validate_eval_set docs/eval-set-v0.yaml
```

Check:
- 所有 `chunk_id` reference 都存在於 indexed corpus
- `validated` 必須 true
- Difficulty 分佈合理(easy 唔超過 70%、hard 至少 10%)
- Query type 分佈合理
- 5 條 OOS 入面 expected_refusal 全部 true

---

## 5. RAGAs Pipeline Integration

### 5.1 Why RAGAs

- Open source,Apache 2.0,~10K GitHub stars(2026 mature)
- Native 支援 4 metric 入面嘅 Faithfulness + Answer Relevancy + Context Precision + Context Recall(我哋只用 Faithfulness)
- 同 LangChain / LlamaIndex / 自寫 pipeline 都易接
- LLM judge 可以 swap(我哋用 Azure OpenAI GPT-5.5 Pro)

### 5.2 Configuration

```python
# backend/eval/ragas_runner.py 嘅 reference config
from ragas import evaluate
from ragas.metrics import faithfulness
from ragas.llms import LangchainLLMWrapper
from langchain_openai import AzureChatOpenAI

judge_llm = LangchainLLMWrapper(
    AzureChatOpenAI(
        azure_endpoint=os.getenv("AZURE_OPENAI_ENDPOINT"),
        api_key=os.getenv("AZURE_OPENAI_API_KEY"),
        api_version=os.getenv("AZURE_OPENAI_API_VERSION"),
        deployment_name=os.getenv("AZURE_OPENAI_DEPLOYMENT_LLM_EVAL_JUDGE"),  # gpt-5-5-pro
        temperature=0.0,                           # judge 必須 deterministic
    )
)

result = evaluate(
    dataset=ragas_dataset,                         # 由 eval_set_loader 轉換
    metrics=[faithfulness],
    llm=judge_llm,
    raise_exceptions=False,                        # 個別 query fail 唔 abort 整個 run
)
```

**Critical**:`temperature=0.0`。Judge 隨機性會 inflate variance,W4 / W6 數字會無法重複。

### 5.3 Recall@5 + Image Association 唔用 RAGAs

呢兩個 metric 自寫(RAGAs 嘅 context_precision / context_recall 唔同我哋定義):

```python
# backend/eval/recall_at_5.py(self-implemented)
def measure_recall_at_5(eval_set, pipeline_fn):
    hits = 0
    for query in eval_set.queries:
        result = pipeline_fn(query.text)
        top_5_chunk_ids = {c.chunk_id for c in result.citations[:5]}
        acceptable = set(query.ground_truth.acceptable_chunk_ids)
        if top_5_chunk_ids & acceptable:           # any intersection
            hits += 1
    return hits / len(eval_set.queries)


# backend/eval/image_association.py(self-implemented)
def measure_image_association(eval_set, pipeline_fn):
    hits = 0
    for query in eval_set.queries:
        result = pipeline_fn(query.text)
        cited_chunk_ids = {c.chunk_id for c in result.citations if c.embedded_images}
        expected = set(query.ground_truth.expected_screenshot_chunks)
        if not expected:                           # query 無關 image
            hits += 1                              # auto-hit
        elif cited_chunk_ids and cited_chunk_ids.issubset(expected):
            hits += 1
    return hits / len(eval_set.queries)
```

### 5.4 LLM-as-Judge for Correctness(automated 補充)

**Correctness primary measurement 由 SME 人工**(§2.3),但**LLM judge 做 auto-screening 加速**:

```python
# backend/eval/llm_judge.py(self-implemented)
CORRECTNESS_JUDGE_PROMPT = """
You are evaluating an answer to a question about a Ricoh user manual.

Question: {query}
Answer: {answer}
Citations: {citations}

Reference: the ground truth chunks contain this content:
{ground_truth_chunks_content}

Rate the answer on this scale:
- "excellent": fully correct, complete, well-cited
- "acceptable": mostly correct with minor issues, user can solve their problem
- "wrong": factually wrong, misleading, or critically missing info

Respond ONLY with JSON: {{"rating": "<level>", "reason": "<one sentence>"}}.
"""
```

**Use**:
- W2 + W3 階段用 LLM judge 做 correctness 嘅 fast iteration signal(SME 唔需要每次 re-rate)
- W4 + W6 Gate 必須 SME 重 rate(LLM judge 唔可以 dominate Gate decision)
- Disagreement(LLM judge "excellent" but SME "wrong")要記錄 + 用作改 prompt 嘅 input

---

## 6. Eval Run Workflow

### 6.1 跑 Full Eval

```bash
# Backend
cd backend
uv run python -m eval.run_full_eval \
    --eval-set docs/eval-set-v0.yaml \
    --kb-id drive_user_manuals \
    --llm-model gpt-5-5 \
    --reranker cohere-v4.0-pro \
    --enable-crag \
    --output reports/eval_run_$(date +%Y%m%d_%H%M).json
```

預期 output:`reports/eval_run_*.json`,內含 4 metric + per-query detail + cost summary。

### 6.2 跑 Single Query(debug)

```bash
uv run python -m eval.run_single_query \
    --kb-id drive_user_manuals \
    --query "How do I clear a paper jam?" \
    --inspect                              # 顯示 retrieval stages + LLM input/output
```

### 6.3 Frontend Eval Console

Spec §5.6 嘅 Eval Console 直接 trigger 上面兩個 backend command,result 顯示喺 UI:
- 4 metric card(pass / fail vs target)
- Failed queries table + 跳轉 Debug View

### 6.4 Cost Estimate Per Run

| Component | Per query cost | 50 query run total |
|---|---|---|
| Embedding | ~$0.0001 | ~$0.005 |
| Hybrid retrieval(Azure AI Search) | ~$0(included in tier) | ~$0 |
| Cohere Rerank | ~$0.002 | ~$0.10 |
| GPT-5.5 synthesis | ~$0.05 | ~$2.50 |
| RAGAs(GPT-5.5 Pro judge,faithfulness) | ~$0.05 | ~$2.50 |
| LLM Correctness judge(GPT-5.5 Pro) | ~$0.05 | ~$2.50 |
| **Total** | **~$0.15** | **~$7.50** |

POC 6 週估 4–6 次 full eval run = USD 30–45。

---

## 7. Reranker Mini-Shootout(W4)

### 7.1 Methodology

W4 嘅 4-way reranker shootout(spec §4.5)用 **same eval set + same retrieval candidates**,只變 reranker:

```
Eval Set(50 queries)
    ↓
Hybrid Retrieval(BM25 + Vector + RRF) → top 50 candidates per query
    ↓
4 個 reranker 並行 rerank → top 5 each
    ↓
4 個 metric 計算(per reranker)
    ↓
4-way comparison report
```

### 7.2 Comparison Metrics

| Metric | 重要性 | Notes |
|---|---|---|
| Recall@5 | **Primary** | 主要決勝指標 |
| NDCG@10 | Secondary | Reranker quality 嘅 textbook indicator |
| p95 Latency | Important | 對 30s SLA 嘅 budget impact |
| Cost per 1K queries | Important | Production cost projection |
| Stability(stdev across 3 runs) | Tie-breaker | Variance 大嘅 reranker 唔可信 |

### 7.3 Decision Rule(spec §4.5 lock)

```
若 Cohere 同 winner 差距 < 3% Recall@5 + < 5% NDCG@10:
  → lock Cohere(vendor reliability win)

若有 alternative > 5% Recall@5 顯著勝:
  → switch,但要 verify cost、stability、SLA

若 Azure built-in 同 Cohere 差距 < 2%:
  → switch to Azure built-in(慳一個 vendor)
```

### 7.4 Output Artifact

```yaml
# reports/reranker_shootout_W4.yaml
metadata:
  ran_at: "2026-..."
  eval_set: "docs/eval-set-v0.yaml"
  query_count: 50
  rounds: 3                    # 跑 3 次取 mean,reduce variance

results:
  cohere_v3_5:
    recall_at_5_mean: 0.92
    recall_at_5_stdev: 0.008
    ndcg_at_10: 0.87
    p95_latency_ms: 1200
    cost_per_1k_queries_usd: 2.0
  voyage_rerank_2_5:
    ...
  zeroentropy_zerank_1:
    ...
  azure_semantic:
    ...

recommendation:
  winner: "cohere_v3_5"
  rationale: "..."
  decision_rule_triggered: "Cohere 同 winner 差距 < 3% → lock Cohere"
```

---

## 8. Decision Gates ↔ Metric Mapping

呢個 section 將 spec §6.3 嘅 Gate 同本文件嘅 metric 串連。

### 8.1 Gate 1(W2 末)— Foundation Gate

| 條件 | Metric source |
|---|---|
| Hybrid Recall@5 ≥ 80% on 30 條 synthetic eval set | §2.1 + §6.1 |
| 100 manuals ingested w/o unrecoverable error | Ingestion log + admin status |
| End-to-end query latency p95 ≤ 30s(無 reranker)| Langfuse trace p95 |

**Note**:Gate 1 用 **80%** 而非 90%,因為 W2 仲未上 reranker。Reranker 進場之後 W3 末預期 Recall@5 提升 ~5–10pp。

### 8.2 Gate 2(W4 末)— Capability Gate

| 結果 | 對應 metric |
|---|---|
| 4 metric 全部 within 5pp of W6 target | Recall@5 ≥ 85%、Faithfulness ≥ 90%、Correctness ≥ 75%、Image Assoc ≥ 80% |
| 任意 1 miss > 5pp | CONTINUE w/ Watch |
| 任意 2 miss > 5pp | RESCOPE |
| 任意 3+ miss > 5pp | ESCALATE |

### 8.3 W6 Final Gate(POC → Beta)

| 條件 | Metric |
|---|---|
| 4 metric 全達 spec §1.6 target | Recall@5 ≥ 90%、Faithfulness ≥ 95%、Correctness ≥ 80%、Image Assoc ≥ 85% |
| p95 Latency ≤ 30s | Langfuse |
| F1–F14 functional acceptance pass | Spec §7.1 |

**Gating policy**:任一 miss 即 W6 後 1 週 hardening 或 escalate(spec §6.3 / §7.2)。

---

## 9. Statistical Considerations

### 9.1 Sample Size 嘅警告

50 條 eval set 嘅 statistical power **有限**:
- 90% accuracy 嘅 95% confidence interval ≈ ±8pp
- 即係 measured Recall@5 = 88% 同 92% 喺 statistical sense **可能無顯著差別**
- W6 demo 講「我哋達到 90%」係 point estimate,**confidence interval 必須一齊 surface**

### 9.2 Per-run Variance

LLM judge 嘅 randomness(即使 temperature=0)+ reranker 嘅 numerical precision 會令同一 config 重跑出唔同數字。**所以**:
- Gate 1 / Gate 2 / W6 Final 嘅 metric 都用**3-run mean** 而非 single-run
- Per-run stdev > 3pp 視為 unstable,需 investigate

### 9.3 Eval Set Drift

W4 加入 20 條 real user query 之後,eval set distribution **改變**。所以:
- W4 之前 vs W4 之後嘅 metric **不可直接比較**
- W4 metric drop 5pp 可能係 distribution shift 而唔係 regression
- W5–W6 用 **post-W4 augmented eval set**(50 條 final)做 official benchmark

### 9.4 Multiple Comparisons

跑 reranker shootout 4-way + LLM A/B 2-way,加埋 multiple metric,**cherry-picking risk** 高。**對策**:
- Pre-register hypothesis before shootout(e.g.「Cohere baseline,任何 alternative > 5pp 才 switch」)
- 唔做 post-hoc redefining「最重要」嘅 metric
- W4 shootout 結果 commit 入 repo 後唔再 re-run cherry-pick

---

## 10. Limitations & Bias Disclosure

呢個 section 係 **policy-level honesty**,W6 demo deck 必須包含。

### 10.1 Eval Set 由 Architect 出 Synthetic ⇒ 偏離真實 user behavior

**Risk**:
- Synthetic query 用 manual 內嘅 vocabulary,真實 user 可能用日常用語
- Synthetic difficulty distribution 由我估,可能過於均衡(real production 70% easy)

**Mitigation**:
- W4 加入 20 條 user_collected query(Q6),改變 distribution
- W6 demo 明確 disclose:30 synthetic + 20 real

**Lingering bias**:
- Even W4 augmented eval set 仍係小樣本(50 條),production 真實 query distribution 唔可能 exact 反映
- **Beta phase user query log 先係 ground truth**

### 10.2 LLM-as-Judge Bias

GPT-5.5 Pro 做 judge 嘅 known bias:
- **Length bias**:傾向 rate longer answer 為 "more correct"
- **Self-preference**:同一 family LLM 嘅 output 有時會 bias upward
- **Hallucination on judge call**:judge 自己有時 mis-classify,~3–5% rate(基於 2025 RAGAs benchmark)

**Mitigation**:
- Correctness 主信號用 SME 人工(LLM judge 只做 auto-screening)
- Faithfulness 因有 chunked content 對照,bias 影響細(~±2pp variance)
- W4 + W6 record SME-LLM disagreement rate,> 15% 視為 judge unreliable

### 10.3 Image Association 嘅 Strict Match Limitation

我哋用 strict subset match(cited ⊆ expected)。Trade-off:
- **Pro**:false positive 低(LLM 唔可能 cite 一啲 random screenshot 攞分)
- **Con**:true negative 嚴(LLM cite 1 個正確 + 1 個 adjacent → miss)

**未來改善**(Tier 2):partial match scoring(Jaccard overlap)。

### 10.4 Faithfulness 嘅 Atomic Claim 抽取依賴 Judge

RAGAs faithfulness 第一步係 LLM 抽 claim。如果 judge 漏抽 claim,denominator 細,score 偏高。

**Mitigation**:
- Spot check 5–10 query 嘅 claim 抽取準確度
- W4 / W6 報告 attach claim count distribution,exception 觸發 manual audit

### 10.5 Cost Bias of Cheap Judge

W2–W3 iteration 用 GPT-5.4-mini 做 fast judge,**唔代表 W6 final 嘅信號**。Final eval **必須**用 GPT-5.5 Pro,W2–W3 嘅 mini-judge metric 唔 promote 入 official report。

### 10.6 Synthetic-QA Self-Supervised Recall 非人手 Ground Truth(W52)

**背景**:`backend/eval/synthetic_qa.py`(W52 offline 工程閘,決策 7 Option d「更深半邊」)量度一個 **self-supervised recall**:由 KB 自己嘅 indexed chunk 用 LLM(gpt-5.4-mini)生成問題(每條問題嘅答案只應喺嗰個 source chunk),source chunk_id 當作 ground truth,跑 retrieval 量「source chunk 有無喺 top-K 返」。formatted 成 `acceptable_chunk_ids=[source]` + `validated=True` 餵 §2.1 嘅 `EvalRunner` strict-mode(零新 recall 數學)。

**比 W51 coverage proxy 進一步**:W51「涵蓋章節數」(distinct-sections-cited)係**廣度 proxy**(答案橫跨幾多章節),W52 synthetic recall 實際量 **retrieval 命中 source chunk 嘅比率** —— 更接近真 recall。

**但仍非人手 ground-truth recall — 已知 bias**:
- **生成偏差**:LLM 生成嘅問題傾向用 source chunk 嘅 vocabulary → 對 lexical/embedding retrieval **偏樂觀**(真實 user 用日常用語會更難);問題若太泛(任何 chunk 都答到)→ source chunk 唔係唯一答案 → recall 失真(故 prompt 明確要求 self-contained + answer-only-here)。
- **單 chunk grounding**:只測「答案喺單一 chunk」嘅 lookup,**唔覆蓋** multi-chunk synthesis / cross-section reasoning(§3.4 `multi_step_synthesis`)。
- **無人手驗證**:無 SME 確認生成問題真係 well-formed + source chunk 真係唯一正解。

**Disclosure rule**:label 必須係 **synthetic / self-supervised recall**,**唔可以** present 做人手 ground-truth recall(對齊 §1.3 Bias-disclosed)。真 ground-truth recall 仍靠 §2.1 + §4 SME 標註集(eval-set-v1)。W52 synthetic recall 嘅用途 = **相對比較**(同一 KB 跨 config / 跨 chunk strategy 嘅 retrieval 變化,W53 reindex eval 基建),非絕對 production 質素 verdict。

**W53 chunk-strategy 比較 — per-config 重生 QA 嘅額外 confounding**:`backend/eval/strategy_comparison.py`(W53 / ADR-0044)跨 `chunk_strategy`(heading_aware vs layout_aware)比較時,**每 strategy reindex 後由它自己 chunks 重生 synthetic QA** → 問題集**逐 strategy 唔同** → recall delta **含問題難度 confounding**。所以量度嘅係 **self-retrievability(自檢索性 — 「呢個 chunking 之下答案 chunk 幾易被檢索返」)**,**非 controlled A/B**(同問題跨 strategy)。`best_strategy` 讀作**相對信號**,非絕對 verdict。Controlled shared-question A/B(strategy-independent text-anchored ground truth + keyword-mode recall)留更未來。

---

## 11. Reporting Format

### 11.1 W4 Report(internal)

```markdown
# EKP W4 Capability Gate Report

**Run Date**: 2026-...
**Eval Set**: docs/eval-set-v0.yaml(synthetic 30 + user 20 = 50 queries)
**Pipeline Config**: spec v6 default + Cohere Rerank v4.0-pro + GPT-5.5 + CRAG

## Metrics(3-run mean ± stdev)
| Metric | Value | W6 Target | W4 Threshold(within 5pp) | Pass? |
|---|---|---|---|---|
| Recall@5 | 87.3% ± 1.2pp | ≥ 90% | ≥ 85% | ✅ |
| Faithfulness | 93.2% ± 0.8pp | ≥ 95% | ≥ 90% | ✅ |
| Correctness | 78.0% ± 2.1pp(SME)| ≥ 80% | ≥ 75% | ✅ |
| Image Assoc | 82.4% ± 1.5pp | ≥ 85% | ≥ 80% | ✅ |

## Gate 2 Decision: PROCEED to W5(L3 routing optional)

## Failed Queries
- Q012: ...
- Q027: ...

## Reranker Shootout(see reports/reranker_shootout_W4.yaml)
Winner: Cohere v4.0-pro(W4 shootout narrowed 4-way → 2-way per Karpathy §1.2;W5 D1 v3.5 → v4.0-pro same-vendor upgrade;W6 D1 LIVE Azure 2-way reaffirmed via faith Δ -11.76pp + rel Δ -9.81pp WORSE per ADR-0012)

## Cost
Total run cost: $X.XX
```

### 11.2 W6 Stakeholder Demo Deck

W6 demo 必須有 1 張 slide cover:
- 4 metric 達標 status(W6 Final Gate,green / red badge)
- Confidence interval(±X pp)
- Sample size + composition disclosure
- Known limitations(at least mention §10.1 + §10.2)

**唔可以**只 surface point estimate 而 hide variance。

---

## 12. Reference

- Spec metrics:[`architecture.md` §1.6 + §1.7](./architecture.md)
- Decision Gates:[`architecture.md` §6.3](./architecture.md)
- Reranker Shootout:[`architecture.md` §4.5](./architecture.md)
- Eval set placeholder:[`eval-set-v0.yaml`](./eval-set-v0.yaml)(下一份 deliverable)
- RAGAs official docs:https://docs.ragas.io/
- Risk register R2(ground truth slip):[`architecture.md` §8.1](./architecture.md)

---

**Eval methodology version**:1.0
**Created**:2026-04-27
**Owner**:Chris(Tech Lead)+ Domain Expert(annotation)
**Effective**:from W1 Day 1
