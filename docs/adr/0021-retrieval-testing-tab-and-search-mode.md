# ADR-0021: V4 Retrieval Testing tab §5.5.4 deliver + HybridSearcher search-mode parameter

**Date**: 2026-05-10
**Status**: Accepted
**Approver**: Chris（技術 Lead）

## Context

W15 D5 closeout audit（`docs/02-architecture/audit-W15-d5-vs-spec.md` 偏差 #5 / §7 P2.1）發現 V4 KB 詳情頁嘅「Retrieval Testing」分頁同規格 `architecture.md §5.5.4` 結構不符：

**規格 §5.5.4 要求**（抄 Dify Image 2 + EKP-specific 額外項）：
- Vector Search / Full-Text / Hybrid Search 模式選擇器
- Top K slider + Score Threshold input
- Rerank Model toggle
- 右側：test query input + ranked result preview
- EKP 額外：Reranker dropdown（Cohere / Voyage / ZeroEntropy / Azure → for W4 shootout）+ CRAG enable toggle + LLM model selector

**現實**（`frontend/app/admin/kb/[id]/page.tsx:406` `RetrievalTab`）：一個 free-form textarea + Run query → `/query/stream`（完整 RAG）→ 合成答案 Card + 引用 Card（按分數排）+ reranker badge + refusal banner。**零控制項** —— 0 mode selector / 0 slider / 0 threshold input / 0 rerank toggle。功能上係一個「test query」面板，但規格要求嘅係一個「retrieval-mode test harness」。

審計文件結論：「**spec wins;don't amend**」—— 補齊控制項，唔改規格。審計 §7 把佢列做 P2 修補（非 P0；non-blocking Beta）。

**為何呢個觸 H1（需要 ADR）**：「Vector / Full-Text / Hybrid」模式選擇器要真正生效，後端 `HybridSearcher.search()` 必須加一個 `mode` 參數（而家只做 hybrid = BM25 + vector RRF）。`HybridSearcher` 喺 `architecture.md §3` RAG Core 範圍 → 加參數 = 改 §3 組件嘅 interface → 嚴格讀屬 CLAUDE.md §5.1 H1 架構改動。同 ADR-0020（Context Expander）一樣係「規格列咗、現實冇、補返（reaffirm spec, not amend）」嘅情況。用戶 2026-05-10 明確選「寫 ADR-0021（strict mode）」。

**規格嘅過時項**：`architecture.md §5.5.4` 嘅 Reranker dropdown 列「Cohere / Voyage / ZeroEntropy / Azure → for W4 shootout」—— 但 Voyage + ZeroEntropy 已喺 Tier 1 被 DROPPED（ADR-0012 + Q21 Resolved，W4 shootout 收 2-way，Cohere v4.0-pro production lock）。所以呢個規格項已被後續決策淘汰；本 ADR 確認 dropdown 只列 Tier 1 鎖定嘅選項。

## Decision

**Option A — Deliver code，reaffirm `architecture.md §5.5.4`（NOT amend spec）**

### 1. `HybridSearcher.search()` 加 `mode` 參數

```python
async def search(
    self, query_text, query_vector, kb_id,
    top_k=50, filter_clause=_DEFAULT_FILTER,
    mode: Literal["hybrid", "vector", "fulltext"] = "hybrid",
) -> list[HybridSearchHit]:
```
- `mode="hybrid"`（default，現有行為不變）：`search=query_text` + `vectorQueries` + `queryType=semantic` + `semanticConfiguration`（BM25 + vector RRF + semantic rerank）
- `mode="vector"`：`search="*"` + `vectorQueries` only（純向量相似度檢索；無 semantic config）
- `mode="fulltext"`：`search=query_text` + `queryType="simple"`（純 BM25；無 `vectorQueries`、無 semantic config）

**唔改**：vendor（仍 Azure AI Search Standard S1）、storage layout、index schema、kb_id 多租戶 invariant（ADR-0018）、`/query` 主流程 default（仍 hybrid）。`mode` 只 expose Azure AI Search 原生已支援嘅查詢類型，純為 admin 嘅檢索測試工具服務。

### 2. `RetrievalEngine.retrieve()` 加 `mode` + `rerank` 參數

```python
async def retrieve(
    self, query, kb_id, top_k=50, filter_clause=None,
    mode: Literal["hybrid", "vector", "fulltext"] = "hybrid",
    rerank: bool = True,
) -> RetrievalResult:
```
- `mode` 傳落 `searcher.search()`；`mode="fulltext"` 時跳過 query embedding（嘥資源 guard）
- `rerank=False` 時跳過 reranker（即使 engine 注入咗 reranker）→ 直接攞 hybrid/vector/fulltext top-K

### 3. 新後端端點 `POST /kb/{kb_id}/retrieval-test`（純檢索，唔跑合成）

- 新檔 `backend/api/routes/retrieval_test.py` + schema `backend/api/schemas/retrieval_test.py`
- Request：`query` + `mode` + `top_k`（1–50）+ `rerank: bool` + `score_threshold: float`（0–1）
- 流程：verify KB exists（404）→ `_engine_or_503`（無 engine 時 503，本地 dev / 測試）→ `engine.retrieve(query, kb_id, top_k, mode, rerank)` → 按 `score_threshold` 過濾（**只對 vector/hybrid mode；fulltext 嘅 BM25 分無 0–1 上界，threshold 忽略**）→ 返回 ranked chunks（rank / chunk_id / doc / section_path / score / chunk_text preview）+ 各階段耗時 + `reranked` + `reranker`（`"cohere-v4.0-pro"` 或 `"none"`）+ `total_hits`（threshold 前）
- 加 `app.include_router(retrieval_test.router, tags=["retrieval-test"], dependencies=_auth)`
- **唔跑 CRAG、唔跑 LLM 合成** —— 呢個係純檢索台

### 4. 前端 `RetrievalTab` 重寫（`frontend/app/admin/kb/[id]/page.tsx`）

- **「Retrieval test」子區（主）**：mode radio（Hybrid default；Vector / Full-Text 真正可用）+ Top K slider（滑桿 + 數字輸入組合，per §5.8 Dify UX win）+ Score Threshold slider（fulltext mode 時 disabled + tooltip 解釋 BM25 分無 0–1 範圍）+ Rerank Model toggle（Switch）+ Reranker Select（**只列 Cohere v4.0-pro（Tier 1 locked，disabled）+ "None"**；唔列 Voyage / ZeroEntropy — 已 drop per ADR-0012）→ ranked chunks + scores（按分數排，section_path、reranker badge、score badge）
- **「End-to-end query」子區（次，摺疊）**：保留現有 `/query/stream` 流程 + 加 CRAG enable toggle + LLM model Select（gpt-5.5 / gpt-5.4-mini）→ 合成答案 + 引用（滿足規格嘅 EKP 額外項：CRAG toggle + LLM selector，呢啲係完整 RAG 嘅嘢，唔屬於純檢索台）
- 新 typed client `frontend/lib/api/retrieval-test.ts`；前端 `QueryRequest` interface 補 optional `llm_model?` / `enable_crag?`（已喺後端 schema）

## Alternatives Considered

### Option B — Amend `architecture.md §5.5.4`（規格 catch up to code）

移除 §5.5.4 嘅模式選擇器（只保留現有「test query → answer」面板），把 V4 Retrieval Testing 重定義為「end-to-end 查詢面板」；移除過時嘅 Voyage/ZeroEntropy dropdown 項。

- **Pros**：零後端代碼、零 H1 觸碰、最少工時（純 spec 編輯）；現有面板功能上夠用（admin 想試查詢睇結果）；W4 shootout 已收 2-way，模式選擇器嘅 W4 用途已過去
- **Cons**：放棄一個有實際價值嘅檢索調試工具（Vector vs Full-Text vs Hybrid 對比、Top-K / threshold 調參、rerank on/off 對比 —— 對 W16+ Beta cohort 嘅 D365 corpus 調優有用）；§5.5.4 amendment = governance debt；審計文件明確講「don't amend — these are real-value retrieval-mode test harness controls」
- **Rejected because**：審計判斷呢啲控制項有實值；`HybridSearcher.search()` 加 `mode` 只係 expose Azure AI Search 原生能力（低風險、低工時）；spec amendment 嘅 governance debt > 加參數嘅工時

### Option C — 純前端 baseline-only（用戶最初提議嘅「純前端版」嘅變體）

加齊規格控制項嘅 UI，但 Vector/Full-Text radio 永久 disabled（標「Tier 1: Hybrid baseline」），沿用現有 `/query/stream`，唔加新後端端點、唔觸 `HybridSearcher`。

- **Pros**：零後端、零 H1、約半日；UI 結構符合規格
- **Cons**：模式選擇器係「假」嘅（只有 Hybrid 真生效）—— 規格嘅核心對比功能（Vector vs Full-Text vs Hybrid）唔 work；仍係跑完整 RAG（有合成），唔係規格講嘅「ranked result preview」純檢索台
- **Rejected because**：用戶 2026-05-10 明確選「完整版（含後端）」+「寫 ADR-0021（strict mode）」

## Consequences

### Positive
- `architecture.md §5.5.4` honored（reaffirm not amend；零 governance debt）
- 真正可用嘅檢索調試工具：Vector / Full-Text / Hybrid 三模式對比 + Top-K / threshold 調參 + rerank on/off —— 對 W16+ Beta cohort D365 corpus 調優有實值
- `HybridSearcher` 而家 expose 咗 Azure AI Search 嘅三種查詢模式，Tier 2 如要做 mode-aware retrieval routing 可直接用
- 審計偏差 #5 → FULLY CLOSED（5/5 major drifts 全閉合）
- 純檢索端點（無合成）—— admin 想睇「邊啲 chunk 被檢索到、分數係幾多」唔使等 LLM 合成（更快、更平、更聚焦）

### Negative
- `HybridSearcher.search()` + `RetrievalEngine.retrieve()` interface 各加 1–2 個參數（default 不變，向後相容）—— C04 組件 surface 微擴
- 新端點 = 新 surface（測試覆蓋 + 維護）—— 用既有嘅 `_engine_or_503` / `Depends(get_kb_service)` / 404 / 503 pattern（同 W16 F5.1 `documents.py` / `chunks.py` 一致）降低風險
- Score Threshold 對 fulltext mode 唔適用（BM25 分無 0–1 範圍）—— 前端 disabled + tooltip 處理，唔係 silent

### Neutral
- Reranker dropdown 只列 Cohere v4.0-pro + "None"（唔列 Voyage/ZeroEntropy）—— 規格 §5.5.4 嘅「Cohere / Voyage / ZeroEntropy / Azure」項已被 ADR-0012 + Q21 Resolved 淘汰；本 ADR 確認 Tier 1 範圍，唔再 amend §5.5.4（歷史敘述保留）
- CRAG toggle + LLM selector 放喺「end-to-end query」子區（完整 RAG），唔放喺純檢索台 —— 規格 §5.5.4 把佢哋同「ranked result preview」並列有少少矛盾；本 ADR 嘅讀法係：純檢索台（規格標準項）+ end-to-end 子區（規格 EKP 額外項）兩者並存
- Feature flag for `mode` default：不需要 —— `/query` 主流程 default 永遠 hybrid，`mode` 只係 retrieval-test 端點 expose

## References

- **Reaffirmed（NOT amended）**：`architecture.md §5.5.4` Retrieval Testing Tab（Vector/Full-Text/Hybrid selector + Top K slider + Score Threshold + Rerank Model toggle + Reranker dropdown + CRAG toggle + LLM selector）+ §5.8（Slider + numeric input combo UX）
- **Audit trigger**：`docs/02-architecture/audit-W15-d5-vs-spec.md` 偏差 #5（V4 Retrieval Testing tab structural mismatch）+ §7 P2.1
- **Cross-ref（過時規格項）**：[ADR-0012 Cohere v4.0-pro upgrade + Gate 2 PARTIAL PASS](./0012-cohere-v4-pro-upgrade-and-gate2-partial-pass.md) —— Voyage / ZeroEntropy DROPPED Tier 1；Q21 Resolved Cohere v4.0-pro production lock
- **Sibling pattern**：[ADR-0020 Context Expander Tier 1 deliver](./0020-context-expander-tier-1-deliver.md) —— 同樣係「規格列咗、現實冇、補返（Option A deliver, reaffirm not amend）」
- **Multi-KB invariant preserved**：[ADR-0018 Multi-KB kb_id propagation](./0018-multi-kb-kb-id-propagation.md) —— `retrieval-test` 端點同 `HybridSearcher.search(mode=...)` 仍走 kb_id-scoped dynamic index name + filter
- **Code citations**：
  - `backend/retrieval/hybrid.py` `HybridSearcher.search()`（mode 參數加入點）
  - `backend/retrieval/retrieval_engine.py` `RetrievalEngine.retrieve()`（mode + rerank 參數）
  - `frontend/app/admin/kb/[id]/page.tsx:406` `RetrievalTab`（重寫目標）
  - `backend/api/schemas/query.py` `QueryRequest`（已有 top_k_retrieval / top_k_rerank / llm_model / reranker / enable_crag）
- **Behavioral baseline**：Karpathy §1.2 simplicity-first（mode = expose 原生能力，唔加 fusion 層；單一 Top K slider 唔開兩個；feature flag 不需要）+ §1.3 surgical（default 不變、向後相容、reuse `_engine_or_503` pattern）+ §1.4 goal-driven（unit tests for mode payload shape + endpoint 404/503/happy path）

## Implementation Deliverables

> **Status（2026-05-10 closeout）**：ADR 文件 + README = `1ea08b0`；implementation = `9582fa4`；audit §10 帳本 #25-26 + 偏差 #5 FULLY CLOSED + 本 checkbox tick + W16 progress = closeout commit。**593 passed + 7 skipped**（was 583+7；0 regressions）；ruff clean；`tsc --noEmit` EXIT_CODE=0；eslint clean on changed files。

### Backend
- [x] `backend/retrieval/hybrid.py`（`9582fa4`）— `HybridSearcher.search()` 加 `mode: Literal["hybrid","vector","fulltext"]="hybrid"`；payload 按 mode 組裝（hybrid 不變 = search + vectorQueries + semantic config / vector = `search="*"` + vectorQueries / fulltext = `search=query_text` + `queryType="simple"`）
- [x] `backend/retrieval/retrieval_engine.py`（`9582fa4`）— `RetrievalEngine.retrieve()` 加 `mode` + `rerank: bool=True`；fulltext mode 跳過 embed；rerank=False 跳過 reranker；default 不變 → `/query` 主流程未動
- [x] `backend/api/schemas/retrieval_test.py` — NEW（`9582fa4`）：`RetrievalTestRequest` / `RetrievalTestChunk` / `RetrievalTestResult`
- [x] `backend/api/routes/retrieval_test.py` — NEW（`9582fa4`）：`POST /kb/{kb_id}/retrieval-test`（404 / 503 / 502 / happy path；score_threshold 過濾 vector/hybrid only；reuse W16 F5.1 `_engine_or_503` / `Depends(get_kb_service)` pattern）
- [x] `backend/api/server.py`（`9582fa4`）— register `retrieval_test.router`

### Frontend
- [x] `frontend/lib/api/retrieval-test.ts` — NEW typed client（`9582fa4`）：`RetrievalMode` / `RetrievalTestRequest` / `RetrievalTestChunk` / `RetrievalTestResult`
- [x] `frontend/app/admin/kb/[id]/page.tsx`（`9582fa4`）— `RetrievalTab` 重寫成兩個 panel：「Retrieval test」（mode Select + Top K Slider + Score Threshold Slider（fulltext 時 disabled）+ Rerank Switch（Cohere v4.0-pro locked label）→ ranked chunks + scores + timings；用 `useMutation`）+「End-to-end query」（query textarea + CRAG Switch + LLM Select（gpt-5.5 / gpt-5.4-mini）→ synthesis + citations；reuse `/query/stream`）。Reranker dropdown 只列 Cohere v4.0-pro + "None"（Voyage/ZeroEntropy dropped per ADR-0012；§5.5.4 not amended）
- [x] ~~`frontend/lib/api/query.ts` — `QueryRequest` interface 補 optional `llm_model?` / `enable_crag?`~~ — **already present**（W3+ 已加；無需改動）

### Tests
- [x] `backend/tests/test_retrieval.py`（非 `test_hybrid_search.py` — 實際檔名）+2 cases（`9582fa4`）— mode='vector' payload shape（`search="*"` + vectorQueries，無 semantic config）/ mode='fulltext' payload shape（`queryType="simple"`，無 vectorQueries）；hybrid default 不變由現有 `test_hybrid_search_payload_shape_matches_spec` 覆蓋
- [x] `backend/tests/test_retrieval_test_endpoint.py` — NEW 8 cases（`9582fa4`）：happy path（mode+rerank forwarded）/ mode+rerank-off forwarded / score_threshold filters vector（ranks re-numbered）/ threshold ignored for fulltext / 404（engine not called）/ 503（engine absent）/ 502（engine raises）/ 422（empty query）
- [x] full backend regression（593 passed + 7 skipped，0 regressions）+ ruff clean（`server.py` 18 pre-existing E402 from truststore-inject pattern NOT touched）+ frontend `tsc --noEmit` EXIT_CODE=0 + eslint clean on changed files；RetrievalTab interactive browser smoke 受限（local dev server's Azure backend 無 seeded KB → KB-detail page 渲染唔到個 tab；`/admin/kb` list 渲染正常，page.tsx module loads）

### Docs / governance
- [x] `docs/adr/README.md` — index 加 ADR-0021 row + next-NNNN 註腳更新（0021 landed → next available 0022；cookie migration / KB persistent backing 候選順延 0022/0023）
- [x] `docs/02-architecture/audit-W15-d5-vs-spec.md` — §10 帳本 #25-26 append + 偏差 #5 → FULLY CLOSED（5/5 major drifts closed）+ closure verdict 更新 + ADR-0017 cumulative count 確認（本改動無 install 新 dependency，R8 count 仍 4）+ handoff section update
