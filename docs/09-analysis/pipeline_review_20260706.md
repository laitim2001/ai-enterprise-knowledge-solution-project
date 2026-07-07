# EKP 核心 Pipeline 技術評估 —— RAG 查詢 + 文件 Ingestion

> **文件定位**:對 EKP 兩條核心功能 pipeline —— **RAG 查詢流程(問答)** 與 **文件 Ingestion 流程(入庫)** —— 的合理性 + 潛在風險評估。回答用戶兩個問題:①查詢流程是否合理、有無風險;②入庫流程是否合理、有無風險。
>
> **方法論(關鍵)**:本評估**基於實際代碼核對**(2026-07-06 code snapshot),**非** spec 推斷。由兩個獨立代碼調查各讀 28–33 個檔案、逐行追蹤呼叫鏈,再由主評估者用專案 context(ADR / memory / DD)校準「現階段實際暴露面」。行號基於 2026-07-06 快照,可能隨後續改動漂移。
>
> **權威來源**:`backend/api/routes/query.py`(查詢入口)· `backend/ingestion/orchestrator.py`(入庫核心)· `backend/storage/settings.py`(config default)· `docs/architecture.md §3`(spec 對照)。
>
> **關聯文件**:[`../01-planning/PROJECT_STATUS_REVIEW_2026-07-04.md`](../01-planning/PROJECT_STATUS_REVIEW_2026-07-04.md)(項目進度全面盤點 — 本評估補足其「卡 production 上線」結論的技術深度)· [`ekp_architecture_diagrams_20260704.html`](./ekp_architecture_diagrams_20260704.html)(RAG 十步 + ingestion 十步流程圖)。

---

## 0. 摘要與總判斷

**兩條 pipeline 的「RAG 邏輯本身」成熟、合理** —— 層次分明、符合現代 RAG 最佳實踐、經 W25–W99 大量實證調優。**但風險幾乎全部集中在兩個地方:①「單機同步」的簡化、②「多用戶安全邊界」。兩者都是 Tier 1 刻意的取捨,不是算法設計錯誤。**

**核心結論**:上 production 前要補的是「生產健壯性 + 安全收口」,**不是重做 RAG**。這正好補足盤點文件「功能完備、卡 production 上線」結論的技術深度 —— 產品功能成熟,但單機簡化 + 多用戶邊界是上線前的結構性技術債。

**三個橫跨兩條 pipeline 的系統性主題**:

| 主題 | 查詢層 | 入庫層 | 性質 |
|---|---|---|---|
| **同步阻塞** | 長操作同步 | parse/chunk 阻塞事件迴圈 + 無佇列 | Tier 1「單機 + no background job」簡化;production 並發下頭號風險 |
| **ACL 預設放行(fail-open)** | 圖片路徑漏 trim(Q-R1) | backend 缺失印成 public(I-R4) | 「寧鬆勿死」取捨;每個新呼叫點漏傳 principals 就靜默洩漏 |
| **靜默退化無告警** | 多層 try/except 退化 | best-effort 步驟失敗只 log | 系統不 crash 但品質/完整度浮動,client 收不到信號 |

---

## 1. RAG 查詢流程(問答)

### 1.1 端到端流程(實際實作)

入口 `backend/api/routes/query.py` 的 `execute_query_pipeline`。註:spec 提及的 `backend/pipeline/` 目錄實際不存在,pipeline 邏輯住在 `backend/generation/` + `backend/retrieval/`,由 `query.py` 直接編排。

| # | 步驟 | 負責模組 | 檔案:行 | 關鍵 config(default) | 失敗行為 |
|---|---|---|---|---|---|
| 0 | KB 層授權 | `assert_kb_access` | `query.py:237` | admin 無條件過 | 無 grant → 403;backend 未 wire → 503 |
| 1 | 解析四層 effective config | `resolve_effective_config` | `effective_config.py:156` | per-query>per-doc>per-KB>global | KB 缺失 → 退 global |
| 2–3 | per-doc overlay(延後套用)+ 解析 user principals | `principals_for_user` | `query.py:244/256` | admin→None(不過濾) | backend None → `[oid]` |
| 4 | **檢索**(單 query 或 RAG-Fusion 分支) | `engine.retrieve` | `retrieval_engine.py:121` | `enable_query_expansion=False` | 整段 try/except → 502 |
| 4-ii | hybrid search(BM25+向量+RRF) | `HybridSearcher.search` | `hybrid.py:387` | `mode=hybrid`,`use_semantic_ranker=True` | tenacity 3× 重試 |
| 4-iii | **ACL filter 注入** | `_build_acl_filter` | `hybrid.py:60`,注入 `421` | `allowed_principals/any()` + `classification` | `principals=None` → 無 filter(fail-open) |
| 4-v | Cohere rerank + cross-section deboost | `CohereReranker.rerank` | `cohere.py:89` | `deboost=1.0`(停用) | 無 reranker → hybrid-only;Cohere 失敗 → 502 |
| 7 | Context Expander(±鄰 chunk 文字) | `expand_context_for_chunks` | `context_expander.py` | `enable_inline_image_markers=False` | 例外 → 退原 chunks(graceful) |
| 8 | Parent-doc / section 聚合 | `aggregate_parent_sections_for_chunks` | `parent_doc_retriever.py` | `enable_parent_doc_retrieval=True`,`top_k=2`,`max_tokens=2000` | 例外 → 退 expanded |
| 9 | Synthesizer(GPT-5.5) | `synthesizer.synthesize` | `synthesizer.py:127` | `detail=concise`,逾時 120s | 例外 → 502 |
| 9d | 事後引用擴展(engine-fetch) | `expand_citations` | `citation_expansion.py:167` | `enable=True`,`window=10`,`max_aux=10`,`depth=1` | 逐 doc 失敗跳過 |
| 10 | **CRAG L2 loop(僅非串流)** | `crag_loop.refine` | `crag.py:296` | `enable_crag=True`,`threshold=0.70`,`max_corrections=1` | 任何 stage 失敗 → 退初始 synth |
| 11–16 | build citations → 鄰居圖 attach → 概覽圖釘前 → 圖去重+cap → proxy URL → section-anchor marker | `citation_enrichment` / `citation_image_neighbors` / `section_anchor_markers` | `query.py:475–523` | `neighbour=True`,`overview_pin=False`,`max_images=None`,`section_anchor=False` | 各層 try/except 退化 |

**串流路徑 `/query/stream`**(chat UI 實際主路徑,`query.py:551–767`):步驟 0–8 相同,但 **完全無 CRAG**(步驟 10 缺席,見 Q-R2)。

**ACL 安全過濾確有注入**:`allowed_principals` filter 打入 4 個檢索面 —— `search`(`hybrid.py:421`)、`fetch_by_chunk_ids`(`230`,context expander)、`fetch_chunks_by_section_path`(`339`,parent-doc)、`list_chunks`(`600`,citation expansion)。**但**鄰居圖/概覽圖兩條路徑漏網(Q-R1)。

### 1.2 合理、做得好的地方

- **層次符合最佳實踐**:query 改寫 → hybrid 檢索 → Cohere rerank → CRAG 自我修正 → parent-doc 聚合 → 引文事後擴展 → synthesizer → 引文/圖片還原,順序與業界成熟 RAG 一致。
- **四層 config 解析**靈活,檢索入口旋鈕 vs 答案後處理旋鈕分開解析(per-doc 只疊後處理層,ADR-0050)。
- **ACL filter 真有注入 4 個檢索面**,非僅設計文件。
- **大量 graceful degradation**:單一 Azure 抖動不會 crash 整個查詢。

### 1.3 風險分級(主評估者判斷)

| 級 | 編號 | 風險 | 校準後判斷 |
|---|---|---|---|
| 🔴 高 | Q-R1 | 鄰居圖 + 章節概覽圖路徑漏 ACL 過濾(confused-deputy 圖片洩漏) | 真缺口,與 ADR-0066 G4 矛盾;**但現階段暴露面細**(文件級 ACL P3 未有真實 driver)。**啟用文件級 ACL 前必修** |
| 🟠 中 | Q-R2 | 串流路徑(chat 主路徑)完全無 CRAG | 面向用戶主路徑跑零檢索修正;spec 允許的 defer 但效果是「CRAG 只在 eval 生效」 |
| 🟠 中 | Q-R3 | Cohere 故障無熱切換,直接 502 | spec §7.3 E7/R6 承諾免 redeploy 熱切,實作要改 config 並重啟。spec drift + 可用性風險 |
| 🟠 中 | Q-R4 | 預設雙重 rerank(Azure semantic + Cohere),冗餘 + Free-tier 402 | production Standard S1 不 402,但冗餘成本在;ADR-0039 有 toggle(Proposed)未 flip |
| 🟡 低 | Q-R5~R10 | CRAG 修正臂配置不一致 + `expanded_top_k` 硬編;`except→502` 遮蔽根因;靜默退化無指標;引文擴展脆弱耦合;fusion latency 失真 | observability / 可維護性層面,不影響正確性 |

### 1.4 完整風險清單(附代碼佐證)

- **Q-R1** 鄰居圖/概覽圖漏 ACL trim:`attach_neighbour_images`(`citation_image_neighbors.py:45`)、`pin_chapter_overview_images`(`:318`)簽名無 `user_principals`,內部 `list_chunks` 無帶 filter。其餘檢索面均已 thread principals(`query.py:314/332/383/408/429`),唯此兩條漏。與 `hybrid.py:228` 的 G4 註解意圖矛盾。
- **Q-R2** 串流無 CRAG:`crag_loop.refine` 只在非串流 `/query`(`query.py:445`);`/query/stream` 無 CRAG(`crag.py:23` 註「stream 是 L3-only」,L3 從未實作,`feature_l3_routing_enabled=False`)。
- **Q-R3** Cohere 無熱切:reranker 在 `server.py:225` lifespan 一次選定;5xx 經 tenacity 3×(`cohere.py:83`)`reraise=True` → 502(`query.py:432`)。切 Azure semantic 需改 `reranker_kind` 並重啟。
- **Q-R4** 雙重 rerank:`hybrid_use_semantic_ranker=True`(`settings.py:211`)加 `queryType=semantic`(`hybrid.py:451`)再 Cohere L2;`settings.py:203-205` 自認「redundant intermediate layer」。
- **Q-R5** CRAG re-retrieve 忽略 per-KB overfetch/mode;`expanded_top_k=20` 是建構子 default(`crag.py:277`),`server.py:261-267` 未從 settings 傳 → 永遠 20 不可調。
- **Q-R6** fail-open ACL:`_build_acl_filter`(`hybrid.py:94`)`None` → 無 filter;空 `allowed_principals` 當 public。
- **Q-R7** `except Exception → 502`:`query.py:334`(檢索)、`:431`(合成)把限流/逾時/schema 錯攤平成 502。
- **Q-R8** 靜默退化無指標:context expander / parent-doc / 圖片層 / CRAG 全部 `except → warning + 退化`,HTTP 照回 200。
- **Q-R9** 引文事後擴展脆弱耦合:`citation_expansion.py:336-347` 需手動物化 `RetrievedChunk` 傳回,否則被 hallucination filter(`citation_enrichment.py:83`)丟棄(W32 事故);約束只靠 docstring。
- **Q-R10** fusion latency 失真:`result_fusion.py:61-79` 把 embed/rerank latency 塞 0、per-variant 序列 sum,影響監控可信度。

---

## 2. 文件 Ingestion 流程(入庫)

### 2.1 端到端流程(實際實作)

**核心結論:整條 ingest 同步阻塞(無 background job),且 parse/chunk 在 async handler 內直接 blocking 事件迴圈。** 共享管線 `_run_ingest_pipeline`(`documents.py:820`)。

| # | 步驟 | 模組 | 檔案:行 | 同步/背景 | 失敗行為 |
|---|---|---|---|---|---|
| 0–1 | 副檔名白名單 + stream 落 tempfile | `_run_ingest_pipeline` | `documents.py:838/860` | 同步 | 非法 → 422 |
| 2 | **P4 掃描 PDF guard**(pre-OCR probe) | `is_scan_pdf` | `profiler.py:97` | 同步(秒級) | 未 `force_scan` → 422 `scan_requires_confirm` |
| 3–8 | 讀 KbConfig → 選 parser → 建 uploader/chunker → 解析 ACL principals + classification | `select_parser`/`_select_chunker`/`resolve_doc_principals` | `documents.py:886–932` | — | ACL backend None → `[]`(fail-open) |
| 9a | **parse(同步阻塞)** | `parser.parse` | `orchestrator.py:152` | **阻塞事件迴圈** | 失敗 → abort 整 doc |
| 9b | 文件畫像 profiling(best-effort) | `_PROFILER.profile` | `orchestrator.py:164` | 同步 | 例外 → 不 abort |
| 9c | **chunk(同步阻塞)** | `chunker.chunk` | `layout_aware.py:108` | **阻塞事件迴圈** | 空 → abort |
| 9d | 抽 + 上傳 screenshots(best-effort) | `ScreenshotExtractor` | `orchestrator.py:184` | 同步 | 個別失敗 skip,整批例外不 abort |
| 9e–f | Contextual embedding 組裝 + **embed 一次過整 doc** | `embedder.embed_batch` | `orchestrator.py:234` | 同步 | **任何失敗 → abort 整 doc** |
| 9g–i | 組裝 ChunkRecord(chunk_id 位置 index-based)+ inline marker 改寫 + ACL/classification stamp | — | `orchestrator.py:248–332` | — | 圖未上傳 → 該 ImageRef skip |
| 10 | Index upsert(mergeOrUpload,batch 1000) | `populator.upload` | `populate.py:137` | 同步 | 例外或 partial>0 → 502 |
| 11–14 | 同步 counter → 原檔持久化 → preset routing → profile persist(全 best-effort) | `record_doc_event`/`upload_source_document`/`_route_profile_preset` | `documents.py:1008–1070` | 同步 | 全部失敗只 log,不 fail ingest |

**三個 HTTP 入口**:`POST /kb/{id}/documents`(單檔)· `POST …/{doc_id}/reindex`(單檔,replace-in-place)· `POST /kb/{id}/reindex`(整 KB,逐 doc 串行)· `POST …/profiles/backfill`(只補畫像,跳過 chunk/embed/upsert)。全部同步、守衛 `require_kb_acl("edit")`。

### 2.2 合理、做得好的地方

- **best-effort 分層清晰**:profiling / preset / 原檔持久化 / counter 失敗只 log 不 abort;核心 parse→chunk→embed→upsert 才 hard-fail,分界正確。
- **reindex 先 delete 再重建**,避免 chunk_id 位置漂移產生 orphan。
- **P4 掃描件 pre-OCR guard**(ADR-0065)秒級擋住會 hang 8–9 分鐘的掃描 PDF。
- **安全 stamp 有做**:`allowed_principals` + `classification` 真印落每個 chunk。

### 2.3 風險分級(主評估者判斷)

| 級 | 編號 | 風險 | 校準後判斷 |
|---|---|---|---|
| 🔴 高 | I-R1 | parse/chunk 在 async 事件迴圈內同步阻塞(且 `base.py` docstring 承諾 `asyncio.to_thread` 但實作沒有) | **最嚴重結構性風險**;大檔 parse 期間整個 uvicorn 事件迴圈卡死,所有並發 request 一齊 hang |
| 🔴 高 | I-R2 | 全條 ingest 同步、無佇列;大檔/慢 Azure → client HTTP 逾時 | 「no background job」是 Tier 1 spec 刻意簡化,但 production 前最應補 |
| 🟠 中 | I-R3 | embedding 一次過送整 doc,無 sub-batch → 超大 doc 撞 Azure 限額 abort | populator 有分批但 embedder 無,不對稱 |
| 🟠 中 | I-R4 | ACL fail-open:RBAC backend 缺失時 chunk 印成 public | 安全相關,同查詢 Q-R1 同一主題 |
| 🟠 中 | I-R7 | <1000 chunks/doc 硬假設,超過 delete/restamp 靜默漏尾 | 大 doc 或原子切換前要處理 |
| 🟠 中 | I-R8 | KB reindex 非原子,有不一致窗口 + 半途失敗留爛狀態 | ADR-0043 已知(zero-downtime defer Track A) |
| 🟡 低 | I-R5,R6,R9~R13 | in-memory restart 即失(dev-only);chunk_id 位置(有緩解);screenshot 靜默缺圖 + orphan blob;OData 插值(有 slugify);重複 pre-OCR probe;per-request 重建 client;counter drift | 多數 dev 環境或 perf/邊角 |

### 2.4 完整風險清單(附代碼佐證)

- **I-R1** 同步阻塞事件迴圈:`orchestrator.py:152`(parse)、`:170`(chunk)直接 blocking,無 `asyncio.to_thread`;`parsers/base.py:10-11` docstring 明寫「orchestrator wraps in asyncio.to_thread」→ 實作與承諾不符。
- **I-R2** 全同步無佇列:`documents.py:1433` docstring 自認「no background job」,回 202 但實際做完才返;KB reindex 逐 doc 串行(`documents.py:1169-1216`)。
- **I-R3** embedding 無 sub-batch:`orchestrator.py:234` 所有 chunk(實測可 369)一次餵 `embed_batch` → 單一 `embeddings.create`(`azure_openai_embedder.py:69`);失敗 → abort(`orchestrator.py:235-246`)。
- **I-R4** ACL fail-open:`acl.py:147-148` + `orchestrator.py:149`,`rbac_backend None` → `allowed_principals=[]`,檢索視空為 public。
- **I-R5** in-memory restart 即失:`server.py:127-154` store 在 `DATABASE_URL` 未設時 in-memory;re-ingest 時 classification store 未 wire → `documents.py:928-932` 退 `"internal"`,restricted tag 靜默降級。
- **I-R6** chunk_id 位置 index-based:`schemas.py:54-62`;有 delete-before-reindex 緩解(`documents.py:1610`),但改用純 mergeOrUpload 會殘留舊尾。ADR-0044 已知。
- **I-R7** <1000 chunk 假設:`populate.py:344/422/514` 全 `top=1000` 單頁無分頁;超過只處理頭 1000,其餘靜默殘留。
- **I-R8** reindex 非原子:`run_kb_reindex`(`documents.py:1169`)delete 與 re-ingest 之間 chunk 消失;單檔半途失敗(`documents.py:1648`)→ 舊已刪新未入,502。
- **I-R9** screenshot best-effort:`orchestrator.py:200-221` 個別失敗 skip、整批例外只 warning;刪 doc 不清 screenshot blob(`documents.py:1507`,orphan)。
- **I-R10** 重複檢查 fail-open + OData 插值:`_doc_exists_in_kb`(`documents.py:800`)出錯 return False;`populate.py:341/421/513` 把 `doc_id` 直插 OData(有 slugify 緩解)。
- **I-R11** 重複 pre-OCR probe:`is_scan_pdf`(`documents.py:871`)+ profiler `_extract_signals`(`profiler.py:180`)同一 PDF 掃 2 次(perf)。
- **I-R12** per-request 重建 client:`ScreenshotUploader`(`documents.py:904`)、`source_store.py:55/98` 每次新建;`documents.py:1037` 原檔再讀入 memory 一次。
- **I-R13** counter drift:`record_doc_event` 失敗只 log,無 reconcile。

---

## 3. 建議與優先排序

呢啲風險**不是叫重做 RAG** —— RAG 邏輯本身健康。而是「Tier 1 單機簡化 + 多用戶邊界」在上 production 前要收口的技術債。建議優先排序:

| 優先 | 項目 | 理由 | 對應風險 |
|---|---|---|---|
| **① 最高** | ingest 改 `asyncio.to_thread`(或背景佇列) | 最低成本擋最大並發風險 | I-R1 / I-R2 |
| **② 高** | 補鄰居圖/概覽圖的 ACL trim | 啟用文件級 ACL 前必修 | Q-R1 |
| **③ 中** | embedding 分批 | 大 doc 入庫脆弱 | I-R3 |
| **④ 按需** | 串流 CRAG / Cohere 熱切換 / semantic ranker toggle flip | 按 production 可用性需求排 | Q-R2 / Q-R3 / Q-R4 |

前兩項係最值得即刻立案(走 PROCESS.md `BUG`/`CH` 流程)。

---

## 4. Spec Drift 小結

| 面向 | Spec 講 | 實作真相 | 佐證 |
|---|---|---|---|
| CRAG L3 adaptive routing | W5 stretch → Gate 2 PARTIAL defer Tier 2 | 未做(一致);但串流連 L2 CRAG 都無(Q-R2) | `architecture.md:1231` |
| Cohere outage hot fallback | E7/R6 承諾免 redeploy 熱切 | 啟動時靜態選定 + 需重啟(Q-R3) | `architecture.md:1296/1342` |
| low_value 處理 | §3.5/§3.6 原 hard exclude | 已按 ADR-0035 改 symmetric deboost | `hybrid.py:117`(受控 drift) |
| PPTX「每 slide = 1 chunk」 | §3.3 | 無此處理,退化 LayoutAware(I-R6 相關) | ADR-0044 note `architecture.md:1066` |
| async wrap 承諾 | `base.py` docstring | orchestrator 無 `to_thread`,直接 block(I-R1) | `orchestrator.py:152/170` |

大部分 drift 有對應 ADR 記錄(受控);唯 **async-wrap 承諾**(I-R1)與 **PPTX slide-chunk** 兩項未對齊且無明確 reconcile。

---

## 附錄:方法論註記

- 本評估由兩個獨立代碼調查(查詢 pipeline 28 檔 / ingestion pipeline 33 檔)逐行追蹤 + 主評估者用專案 context 校準。
- **校準原則**:調查給「事實 + 代碼位置」,主評估者疊加「現階段實際暴露面」判斷(例:Q-R1 標高風險但註明文件級 ACL 未有真實 driver → 現暴露面細;Q-R4 Free-tier 402 註明 production Standard S1 不受影響)。
- 未做:實際觸發驗證(未真跑洩漏 PoC / 未壓測並發 hang);行號可能隨後續 commit 漂移。要 confirm 某條風險的實際觸發面,可再指派針對性驗證。

---

**評估人**:Claude Code(雙代碼調查 + 主評估綜合) · **快照日期**:2026-07-06 · **基礎 commit**:見 `git log`(2026-07-04 後)
