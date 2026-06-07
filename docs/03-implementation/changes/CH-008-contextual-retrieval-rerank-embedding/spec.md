---
change_id: CH-008
title: "Contextual Retrieval — section-context injection for rerank + embedding"
status: approved          # draft | approved | done
adr_ref: ../../../adr/0045-contextual-retrieval-section-context-injection.md
affects_components: [C04, C03]   # C04 Retrieval (reranker) · C03 Ingestion (embedding input)
spec_refs:
  - architecture.md §3.2 (reranker)
  - architecture.md §3.3 / §3.5 (ingestion / chunking)
  - architecture.md §3.6 (index schema + rerank document)
---

# CH-008 — Contextual Retrieval(section-context injection for rerank + embedding)

> **H1 change** — implements ADR-0045(Proposed)。Code GATED on ADR Accept(本 spec approved 即代表 Chris 已批准方向 2026-06-08)。

## 1. Problem

BUG-034 問題1 底層診斷:Cohere reranker(`cohere.py:94`)+ vector embedding 都**只用 `chunk_text`、唔帶 section/章節 context**。DRIVE 手冊每個程序(GL02/GL03/GL05…)section leaf 都係 generic「System Instruction for each step」+ 相似步驟表 → reranker 分唔清章節,query「post a journal entry」竟然 #1 揀 §5.1.3 GL05 Journal Reversal、#3/#4 揀 §2.1.x GL02,真正 GL03-Create 沉到 #5-8。74-chunk A/B 實驗證:加 section context 後 off-topic GL05/GL02 清走、GL03 升頂(7/8)。

## 2. Scope

### In scope
- **I1 共用 helper**:`build_contextual_document(section_path, chunk_text)` → `"<section_path join ' > '>\n<chunk_text>"`;section_path 空 → 純 `chunk_text`(fallback)。放 `retrieval/contextual.py`(或同類單一 module)。
- **I2 rerank-time**:`cohere.py` + `azure_semantic.py` 構造 rerank document 改用 I1 helper(由 `chunk_text` → contextual)。
- **I3 embed-time**:ingestion pipeline 計 chunk embedding 時 embed I1 helper 輸出(`context + chunk_text`);**stored `chunk_text` 維持原文不變**。
- **I4 tests**(H6):helper(含 fallback)+ rerank document 構造 + embedding-input 構造。
- **I5 re-index**:`drive-images-1`(有真實 6 source、live index、in-place,唔佔新槽)→ 令 I3 embedding context 生效。
- **I6 eval 驗證**:re-index 後 retrieval-test(GL)before/after 確認 GL03 升頂 + off-topic 清走;跑現有 eval set 確認無 regression。
- **I7 docs**:architecture.md §3.6 文字更新(rerank document = section context + chunk_text);C04 + C03 design note bump。

### Out of scope
- per-KB toggle(contextual retrieval 係全域提升,非 per-KB 取捨)。
- 其他 KB re-index(多數 stub source;待有真實 source + 需要時再 re-index)。
- chunk_title 加入 context(避免冗餘 — section leaf 已喺 path)。
- v1→v2 index 原子切換 / embedding_model 變更(無關)。

## 3. Acceptance Criteria

- AC1 — `build_contextual_document` 對有 section_path 嘅 chunk 回 `"<path>\n<text>"`;空 path 回純 text(fallback)。
- AC2 — `cohere.py` + `azure_semantic.py` rerank document 用 contextual;query-time,無 re-index 依賴。
- AC3 — ingest embedding 用 contextual input;stored chunk_text 原文不變(citation/listing/Finding D 圖排序 bit-identical)。
- AC4 — `drive-images-1` re-index 後 retrieval-test(GL)top-8 由「§5.1.3 GL05 #1 + §2.1.x GL02」→「GL03 為主、off-topic 清走」。
- AC5 — 現有 eval set 無 regression(recall / faithfulness / correctness 不降)。
- AC6 — backend pytest(retrieval + ingestion 相關)pass + ruff + mypy(改檔)0 新 error。
- AC7 — ADR-0045 status Proposed → Accepted;architecture.md §3.6 + C04/C03 note 更新。

## 4. Design Notes

- **Stored vs embedded 分離**:`chunk_text` 喺 index 維持原文(citation 顯示 / rerank document base / `/chunks` listing 全部用原文);embedding 向量喺 ingest 時 bake context;rerank document 喺 query 時 prepend context。三者用同一 helper 串,確保一致。
- **Fallback 保 production-preserve**:section_path 空(legacy / 無 section chunk)→ 退純 chunk_text → bit-identical 現行,零 regression。
- **Re-index 必要性**:I2(rerank)即時生效(query-time);I3(embedding)要 re-index 先有新向量。`drive-images-1` in-place re-index(已有 source)。
- **成本**:rerank document 加 section_path(通常 < 100 char),Cohere token 成本影響可忽略;embedding 同理。

## 5. Risks

- **R1**:section_path 格式跨 doc 不一致 → helper 對任何 list[str] 都 robust(join + fallback)。
- **R2**:re-index `drive-images-1` 期間該 KB 暫不可查(in-place drop+rebuild)→ 預期短暫,完成後驗證。
- **R3**:embedding context 改變向量 → 候選池分佈變;靠 I6 eval 確認無 regression。

## 6. Changelog

| Date | Change | Reason |
|---|---|---|
| 2026-06-08 | spec draft → approved | Chris 批准 H1 + 全套 rerank+embedding scope;74-chunk 實驗 PASS |
