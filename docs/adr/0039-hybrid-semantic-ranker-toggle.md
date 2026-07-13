# ADR-0039: Hybrid Mode Semantic Ranker as Configurable Layer

**Date**: 2026-05-29
**Status**: Accepted
**Approver**: Chris(技術 Lead)— confirmed 2026-05-29(W42 F0.9 H1 boundary AskUserQuestion「Approved — ADR-0039 Accept + 開始 F1」pick)

## Context

EKP `/query` + `/chat` 嘅 hybrid retrieval mode(per `architecture.md §3.1`)目前喺 Azure AI Search search call 內 hard-code `queryType="semantic"` + `semanticConfiguration="ekp-semantic-config"`(`backend/retrieval/hybrid.py:371-372`),即每次 hybrid query 都觸發 Azure 嘅 **semantic ranker**(L2 semantic reranking)。

**問題**:Azure AI Search **Free tier** 對 semantic ranker 有 monthly quota hard cap(1000/月),用盡即 `402 Payment Required`。EKP 當前用 Free tier,chat UI 固定行 hybrid mode(`useChat` SSE 唔 expose mode param)→ chat UI 全 pipeline 測試被 402 block(W41 smoke test 2026-05-29 confirmed)。

**架構觀察**:
- Q21 Resolved(2026-05-05,ADR-0012)— W6 D1 LIVE 2-way verify 已證 **Azure semantic ranker 比 Cohere v4.0-pro WORSE**(faith Δ -11.76pp / answer-relevancy Δ -9.81pp),Cohere 定為 production reranker。
- EKP pipeline 喺 hybrid search 之後**已經行 Cohere rerank** 做主 L2 reranker,作用於同一個 top-50 候選集。
- 即係話 hybrid mode 入面 Azure semantic ranker 只係一個「會被 Cohere override 嘅次等中間 reorder 層」— 候選集(由 BM25+vector+RRF 決定)不受 semantic ranker 影響,Cohere 收到嘅 input 不變。

**Trade-off 分析(2026-05-29)** 比較三個 unblock chat UI full-pipeline 嘅 path:
- Option ①(本 ADR)— drop semantic ranker config flag:$0 / 唔換 vendor / 可逆
- Option ② pgvector swap — H2 vendor swap + 重寫 hybrid + 推翻 W25-W41 tuning
- Option ④ Azure Basic tier($75/月)+ Semantic Standard pricing — IT cost + stakeholder approval

## Decision

加一個 **default-preserve config flag** `Settings.hybrid_use_semantic_ranker: bool = True`:
- **default True** → 保留 W2 baseline production 行為(hybrid 用 semantic ranker)— production 不變
- **False** → hybrid mode drop `queryType="semantic"` + `semanticConfiguration`,變成 **BM25 + vector + RRF**(Azure 喺有 search text + vectorQueries 時自動 RRF fusion)→ Cohere rerank → W40 deboost → synthesize。無 semantic ranker = 無 quota = Free tier work。

`HybridSearcher.__init__` 加 `use_semantic_ranker: bool = True` + `semantic_config_name` params(後者順手 parametrize,取代 L372 hard-coded literal);`api/server.py` 從 settings wire。

**Production default 維持 True**(semantic ranker on)— flag OFF 透過 `.env` `HYBRID_USE_SEMANTIC_RANKER=false` 啟用,initial 用途為 **Free-tier 全 pipeline + chat UI dev/test**。是否將 default flip 為 False(永久 drop semantic ranker)屬 W43+ separate decision,gated on F2 Gate 1 R@5 re-verify 確認 no regression。

## Alternatives Considered

- **Option ② pgvector / Qdrant vector DB swap** — REJECTED for this goal:(a) 解錯問題 — 其他 vector DB 都冇 Azure semantic ranker,402 同 vector DB 無關;(b) 觸發 H2 vendor lock swap,需獨立 ADR + stakeholder approval;(c) 重寫 `HybridSearcher` 全 5 method + populator + index schema + 手寫 RRF + Postgres FTS,推翻 W25-W41 累積 Azure-tuned eval baseline。屬重大 governance,非測試便利。
- **Option ④ Azure Basic tier + Semantic Standard pricing** — DEFERRED:$75/月 IT cost,zero code,retrieval identical,係 GA stepping stone,但 user stated goal 係「平」($0 vs $75)。保留作 GA tier candidate。
- **改 chat UI 加 mode toggle 畀用戶揀 vector mode** — REJECTED:改 chat UX 行為(default retrieval mode),user-facing surface change;flag-at-backend 更 surgical 且 production-default-preserve。
- **等 Free tier monthly quota 6-1 reset** — REJECTED:passive,唔解 long-term cap,quota 反覆耗盡。

## Consequences

- **Positive**:
  - Chat UI 全 pipeline 可喺 Free tier $0 測試(unblock W41 smoke test 嘅唯一 gate)
  - 唔換 vendor(H2 safe)— Azure AI Search + Cohere 不變
  - 完全可逆(`.env` flag,default preserve production)
  - 移走一個 Q21 已證 inferior + 被 Cohere override 嘅 redundant 層
  - 對齊 W37-W41 surgical knob pattern(additive + default preserve)
- **Negative**:
  - 改 §3.1 retrieval search behavior = H1-adjacent → 需本 ADR + Gate 1 re-verify safety gate(F2)
  - flag OFF 時失去 Azure semantic ranker 嘅 captions / answers extraction(EKP 唔用,無影響)
  - 若 F2 eval 顯示 semantic ranker 實際有貢獻 R@5(理論上不應,因 Cohere rerank 同一候選集)→ flag 留 default True,只做 dev test workaround
- **Neutral**:
  - Production default 維持 semantic on — production 行為零變化直到 W43+ explicit flip decision
  - 長期 GA 若升 paid tier(Basic / S1),semantic ranker quota 解除,flag 可保持 True 或視 eval flip

## References

- `architecture.md §3.1`(RAG core retrieval)+ §3.2(vendor lock,Azure AI Search S1 H2 — 不變)
- ADR-0012(Cohere v4.0-pro production reranker lock)+ Q21 Resolved(Azure semantic ranker WORSE than Cohere)
- ADR-0021(retrieval mode param hybrid/vector/fulltext)
- W2 Gate 1 R@5=0.9722 baseline(measured WITH semantic ranker → F2 re-verify predicate)
- `backend/retrieval/hybrid.py:362-372`(search() mode branches)
- W42 plan §5 H1 boundary 評估
- memory `project_azure_search_tier_semantic_billing`(402 root cause analysis + W42 flag workaround + eval index 發現)
- **W42 F2/F3 closeout 2026-05-29**:G3 chat UI Free-tier LIVE **PASS ⭐**(flag-OFF 3 query 全 200 無 402);G2 Gate 1 R@5 re-verify **INCONCLUSIVE**(`/eval/run` hard-code `kb_id="drive_user_manuals"` → index `ekp-kb-drive-v1` 唔喺 Azure Search service;service 只有 per-KB index `ekp-kb-{kb_id}-v1` ×2)→ Chris 環境受限結案,safety 由本 ADR 理論(Q21 + Cohere override redundant)+ F3 質性證據滿足;production default True 維持不變

---

## Amendment — B-18 default flip to False(2026-07-13)

**Trigger**:pipeline review(`docs/09-analysis/pipeline_review_20260706.md` Q-R4)重新標示「預設雙重 rerank 冗餘」,用戶 approve 走「完整 flip + eval 背書」。本 amendment 記錄 W42 F2 明訂的 default-flip gate(Gate 1 R@5 no-regression)如何滿足,以及 flip 執行。

**Gate 方法調整**:原定 Gate 1 R@5 re-verify 無法執行 —— `eval-set-v0` 是 W1 synthetic placeholder(chunk_id 非真實 index、`validated: false`),無 validated text R@5 ground truth(= B-07 卡用戶的結構性 blocker,非單純 W42 的 `kb_id` hardcode)。改用**不依賴 GT 的 retrieval-overlap A/B**,直接驗證本 ADR 核心論點(「Cohere rerank 作用於同一候選集 → semantic ranker 被 override」)。

**方法**:對 `drive-images-1`(6 真實 drive 財務 manual / 369 chunks)以 9 條真實 query(`docs/eval-set-image-recall-ar.yaml` query_text)打 `POST /kb/{kb_id}/retrieval-test`(retrieve-only,hybrid + Cohere rerank),比較 semantic ON vs OFF 兩臂的最終 top-10 chunk_id。ON 臂用進程環境變數 `HYBRID_USE_SEMANTIC_RANKER=true` 覆蓋 `.env`(pydantic os.environ 優先於 `.env` file,不改檔案),兩臂各 restart backend;ON 生效以「帶/不帶 env var 載入 `Settings` 對比」確認(True vs False)。

**結果**:

| 條件 | ON vs OFF top-10 overlap | 順序一致 | 結論 |
|---|---|---|---|
| rerank=true(production 路徑) | **1.00** | **9/9 byte-identical** | Cohere override 令最終結果完全相同 |
| rerank=false(純 hybrid 對照) | 0.50 | 0/9 | semantic 確實生效(改 hybrid 排序)→ 排除「假 ON」 |

rerank-OFF 兩臂顯著發散(overlap 0.50)證明 semantic ranker 真的在作用;rerank-ON 兩臂完全相同(1.00)證明 Cohere 把它完全 override。→ **移除 semantic ranker 對 production 最終檢索零影響,no-regression 決定性成立**(比原定 R@5 命中率更直接證「flip 前後 byte-identical」)。

**Decision**:`Settings.hybrid_use_semantic_ranker` 預設 `True → False`(`backend/storage/settings.py`)。production hybrid 檢索改行 BM25 + vector + RRF → Cohere rerank,移除冗餘 + Free-tier semantic 配額消耗的中間層。`HybridSearcher` 建構子參數 default(`use_semantic_ranker: bool = True`)與兩個 W42 單元測試不變(測參數行為,非 `Settings` default)。`.env` 既有 `HYBRID_USE_SEMANTIC_RANKER=false` override 與新 default 同值,變冗餘(可移除,未動)。

**Scope note**:overlap A/B 限 `drive-images-1`(唯一有真實多文件內容 + 真實 query 的 not-archived KB)。若未來出現候選集構造(BM25+vector+RRF top-50 邊界)對某 KB 敏感的情況,可用同一 harness 重驗。GA 若升 paid tier,semantic quota 解除,此 flip 仍成立(移除的是已證冗餘的層,非單純配額 workaround)。
