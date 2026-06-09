---
phase: W57
plan_ref: ./plan.md
checklist_ref: ./checklist.md
status: active     # active | closed
---

# W57 — Progress

> Day-N entries + closeout retro。

---

## Day 1 — 2026-06-09

### Done
- Gap C(CH-011/CH-012)收尾後,用戶 trigger Gap A / P2(per-doc 配置平台 + UI,vision 核心)。
- 讀平台藍圖 §3.1 Layer A + ground 現有 config 解析鏈(`EffectiveConfig` `per-query > per-KB > global`,
  request 入口 resolve 一次)+ 儲存層(`KBStorageBackend` Protocol + Postgres/InMemory + factory)+
  pipeline(`/query` `execute_query_pipeline` + `/query/stream` `query_stream`,retrieve 後拎到 reranked chunks)。
- **H7 發現**:per-doc 配置 UI 喺 mockup **無對應 surface**(`ekp-page-doc-detail.jsx` 純唯讀 chunk
  inspector;config UI 只喺 KB 層 `ekp-page-kb.jsx` SettingsTab)→ 唔可以自行 approximate。
- **2 個架構決策(AskUserQuestion)**:
  - **Q1 解析語意 = 主導 doc + 後處理旋鈕**:per-doc 只蓋 post-retrieval 旋鈕(answer_detail /
    citation_expansion / neighbour_images / max_images / overview_pin),用 dominant doc resolve;
    retrieval-entry(top_k/rerank/parent_doc)維持 per-KB。單文件 query → 等同全 per-doc。
  - **Q2 UI 拆 P2b**:今個 phase = P2a 後端層;UI 待 mockup 決定。

### Decisions
- Phase W57 = P2a 後端 per-doc 配置層(不掂 frontend = 守 H7)。
- ADR-0050 延伸 ADR-0040 config-scope(per-KB → per-DOC + dominant-doc 解析)。
- 儲存用獨立 `DocConfigStore`(新表 `document_configs`)平行 `make_kb_backend` pattern,唔污染 KB CRUD。
- doc_id free-form key(無 documents 持久表;MVP 不強制 FK,記 OQ)。

### Blockers
- 無(待實作)。

### Commits
| Hash | Subject |
|---|---|
| _(pending)_ | docs(planning): W57 kickoff — plan + ADR-0050 |

---

**End of W57 progress(Day 1 cont 將續寫實作)**
