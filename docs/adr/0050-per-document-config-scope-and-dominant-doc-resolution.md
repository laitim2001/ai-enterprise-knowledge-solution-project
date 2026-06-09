# ADR-0050: Per-Document 配置範圍 + 主導 doc 解析策略

**Date**: 2026-06-09
**Status**: Accepted
**Approver**: Chris

## Context

ADR-0040(W43)formalize 咗 per-KB 可調配置:`EffectiveConfig` 喺 request 入口按
`per-query > per-KB(KbConfig)> global(Settings)` resolve 13 個 retrieval / citation 旋鈕。
用戶 2026-06-01 foundational vision(memory `project_per_kb_tunable_config_vision`)要求配置粒度落到
**per-document** —— 同一 KB 內不同文件用度身訂做配置(圖密程序手冊 vs prose 文件需不同 expansion /
image cap / answer detail)。平台藍圖 `docs/02-architecture/per-document-config-platform-design.md`
§3.1 Layer A 提出此擴展;Gap C(圖片位置 + 完整性)已喺 CH-011/CH-012 完成,本 ADR 起 Gap A。

**核心張力**(平台藍圖 OQ-1):一個答案可引**多個 doc**(跨文件 query),而**部分旋鈕喺引文未知前已
被消耗** —— `default_top_k` / `default_rerank_k` 驅動 retrieval 本身,`parent_doc_*` 驅動 retrieval 擴展,
兩者都喺「邊個 doc 被引」確定之前執行(雞同蛋)。因此「全 13 旋鈕 per-doc」需要 retrieval 後二次
retrieve = 重構檢索路徑,代價過大。

用戶 2026-06-09 拍板兩個決策(AskUserQuestion):
- **Q1 解析語意 = 主導 doc + 後處理旋鈕**(reject「逐引文 owning-doc」+「全旋鈕 per-doc」)。
- **Q2 UI 拆 P2b**(本 phase W57 = P2a 後端層;per-doc 配置 UI 喺 mockup 無對應 surface = H7,UI 待
  mockup 決定)。

## Decision

**1. Per-doc 配置只覆蓋「合成 + 引文後處理」旋鈕**,用**主導 doc(dominant doc)**解析:

| 旋鈕類別 | 旋鈕 | 消耗點 | per-doc? |
|---|---|---|---|
| 檢索入口 | `default_top_k` / `default_rerank_k` / `parent_doc_*` | retrieve / parent-doc(synth 前)| ❌ 維持 per-KB |
| 合成 | `answer_detail` | synth | ✅ dominant doc |
| 引文後處理 | `citation_expansion_*` / `citation_neighbour_*` / `max_images_per_answer` / `enable_chapter_overview_pin` | citations / images(retrieval 後)| ✅ dominant doc |

**2. 解析鏈擴一層**:`per-query override > per-DOC profile > per-KB KbConfig > global Settings`。
`resolve_effective_config` 加 `doc_config: DocConfig | None` 參數;`DocConfig`(新 schema)**只含上表
post-retrieval Optional 旋鈕**,所以檢索入口旋鈕結構上不受 doc layer 影響(無嗰啲 field)。

**3. Dominant doc** = reranked chunk set 入面**出現 chunk 數最多**嘅 `doc_id`(tie → 最高 rank chunk 嘅
doc)。單文件 query(Drive 手冊主用例)→ dominant doc = 唯一 doc → 效果 = 100% per-doc;multi-doc query
→ 用主導 doc profile(簡單合理 default)。

**4. Pipeline 注入點**:`/query`(`execute_query_pipeline`)+ `/query/stream`(`query_stream`)喺 retrieve
**之後**、synth **之前**,若 dominant doc 有 per-doc 配置 → 重 resolve `effective`(只後處理旋鈕變),
downstream wire point 讀 `effective.*` 不變。無 per-doc 配置 → 跳過,維持 per-KB(bit-identical)。

**5. 儲存**:獨立 `DocConfigStore`(新 Postgres 表 `document_configs(kb_id, doc_id, config JSONB,
PK(kb_id,doc_id))`),平行 `make_kb_backend` factory pattern;`DATABASE_URL` unset → in-memory fallback。
**唔污染** KB CRUD,亦唔加 documents 持久表(MVP doc_id = free-form key,不強制 FK)。

**6. Config-test doc-scope**:`ConfigTestRequest` 加 `doc_id`(optional)→ 試跑解析鏈插 doc layer
(`draft > per-DOC > per-KB > global`),令 KB owner 可針對單一文件 profile 試跑。

**production-preserve(G7)**:`doc_config=None` / store 空 → resolve 結果 bit-identical 現有行為
(沿 ADR-0028/0040 migration-default precedent)。

## Alternatives Considered

- **B — 逐引文 owning-doc 解析**:每條 citation 嘅圖片/擴展用該 citation owning doc 嘅 profile。最貼
  vision,但 pipeline 要逐 citation 多次 resolve + image-cap 跨 doc budget 分配變複雜。reject —— 主用例
  (Drive 手冊)係單文件 query,dominant doc 已等同 owning doc;multi-doc 收益不抵複雜度(Karpathy §1.2)。
  用戶 2026-06-09 reject。
- **C — 全旋鈕 per-doc(含檢索)**:`top_k`/`rerank`/`parent_doc` 都 per-doc → 需 retrieval 後二次
  retrieve。reject —— 重構檢索路徑,代價過大;檢索入口旋鈕對「文件內容格式」敏感度低過後處理旋鈕。
  用戶 2026-06-09 reject。
- **儲存沿用 `documents` metadata JSONB**:reject —— 無 documents 持久表(文件只活在 search index),
  且會污染未來 doc metadata;獨立表更乾淨(平台藍圖 §3.1 傾向 (a))。
- **per-doc 配置 UI 今個 phase 一齊做**:defer —— mockup 無 per-doc config surface(H7),UI 拆 P2b 待
  mockup 決定(用戶 Q2)。

## Consequences

- **Positive**:vision 核心(per-doc 度身訂做配置)後端地基齊;單文件 query 即享全 per-doc;解析鏈
  cleanly 擴一層;無 re-index、無 vendor、無 frontend 改動;production-preserve(`doc_config=None`
  bit-identical)。
- **Negative**:pipeline 多一次 conditional resolve(retrieve 後);dominant-doc 對 multi-doc query 係
  近似(非逐引文精準,但符合 Q1 決策);doc_id free-form 可能指向已刪文件(P2b UI / list-by-kb surface
  孤兒;記 OQ)。
- **Neutral**:檢索入口旋鈕維持 per-KB(future 若需 per-doc 檢索 = 另一 ADR + 檢索重構);per-doc 配置
  UI = P2b 後續工作。

## References

- ADR-0040(per-KB tunable retrieval config scope;本 ADR 延伸至 per-DOC)
- ADR-0023(Postgres persist;`DocConfigStore` 沿其 backend factory pattern)
- ADR-0028(multimodal migration-default;production-preserve precedent)
- 平台藍圖:`docs/02-architecture/per-document-config-platform-design.md` §3.1 Layer A + §7 P2
- Phase plan:`docs/01-planning/W57-per-doc-config-backend/plan.md`
- 用戶決策:2026-06-09 AskUserQuestion(Q1 主導 doc + 後處理旋鈕 / Q2 UI 拆 P2b)
- Vision:memory `project_per_kb_tunable_config_vision`
