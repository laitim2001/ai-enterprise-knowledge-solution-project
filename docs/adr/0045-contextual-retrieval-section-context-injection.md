# ADR-0045: Contextual Retrieval — section-context injection for rerank + embedding

**Date**: 2026-06-08
**Status**: Proposed
**Approver**: Chris

## Context

問題1(chat 圖片 + 內容 recall 相關性)實地診斷揭發一個底層 retrieval 質素問題,而**唔係** config 或 presentation 問題:

- Cohere reranker(`retrieval/reranker/cohere.py:94`)**只用 `chunk_text` 做 rerank document**,完全唔餵 `section_path` / 章節標題(architecture.md §3.6 明文「Document text uses `chunk_text` field」)。
- DRIVE 手冊每個程序(GL02 / GL03 / GL05…)嘅 section leaf **全部叫同一個 generic 名**「System Instruction for each step」,而且 chunk_text 都係結構相似嘅步驟表(`# | Process Step | Case | System…`)。
- 結果:query「How do I post a journal entry in General Ledger?」,reranker 分唔清章節,純 rerank top-8:
  - #1 = **§5.1.3 GL05 Journal Reversal**(off-topic)
  - #3/#4 = **§2.1.x GL02**(off-topic)
  - 真正 GL03「Create General Journal」(§3.1.3)沉到 #5-8。

**驗證實驗**(2026-06-07,throwaway,同一批 74 chunk Cohere rerank 兩次):

| 名次 | (A) Baseline `chunk_text` | (B) Contextual `section_path + chunk_text` |
|---|---|---|
| #1 | §5.1.3 GL05 ❌ | §3.1.5 GL03 ✅ |
| #2 | §3.1.5 GL03 | §3.1.3 GL03 Create ✅ |
| #3 | §2.1.10 GL02 ❌ | §3.1.5 GL03 ✅ |
| #4 | §2.1.7 GL02 ❌ | §3.1.3 GL03 Create ✅ |
| #5-8 | §3.1.3×3 + §3.1.5 | §3.1.3×3 + §3.1.1 + §5.1.3 |

Contextual 之後:GL02 兩個 off-topic chunk 完全清走、GL05 由 #1 跌到 #8、GL03 由佔 5 個升到 7 個。**根因 + 修法雙確認。**

呢個改動觸發 **H1**(改 §3.2/§3.6 reranker documented behavior + §3.3/§3.5 ingestion embedding input),所以開 ADR。Cohere 同 Azure OpenAI embedding 維持原 vendor(無 H2 觸發)。

## Decision

採用 **Contextual Retrieval**(業界 / Anthropic「contextual retrieval」技術):喺 chunk 嘅檢索表示之前 prepend 該 chunk 嘅 **section 階層 context**(`section_path` join),令 reranker + embedding model 都「睇到」chunk 屬邊個章節 / 程序。

具體兩處:

1. **Rerank-time(query 時,零 re-index)**
   - `cohere.py` + `azure_semantic.py` 構造 rerank document 由 `chunk_text` 改為:
     ```
     "<section_path join ' > '>\n<chunk_text>"
     ```
   - 抽一個共用 helper(`retrieval/contextual.py` 或同類)建呢個字串,兩個 reranker 共用。
   - **Fallback**:`section_path` 空(legacy chunk)→ 退回純 `chunk_text`(零行為改變)。

2. **Embed-time(ingest 時,要 re-index)**
   - Ingestion pipeline 計 chunk embedding 時,embed `"<section_path join>\n<chunk_text>"`(同一 helper),令 vector 候選池本身更能區分章節。
   - **儲存嘅 `chunk_text` 維持原文不變**(citation 顯示 / rerank document base 都用原文 + query-time context;只有 embedding 向量 bake 咗 context)。
   - 需要 re-index 受影響 KB 先生效(embedding 喺 ingest 時計)。

**Context 格式**:`" > ".join(section_path)`(實驗用呢個,work);唔加 `chunk_title`(避免冗餘 — section leaf 已喺 path)。

## Alternatives Considered

- **只改 rerank、唔改 embedding(零 re-index)**:實驗證實已足夠解 reranker 章節混淆。但 vector 候選池本身仍可能漏(若正確 chunk 連入唔到候選池,rerank 救唔到)。用戶選全套(rerank + embedding)求徹底,接受 re-index 成本。
- **per-KB config toggle**:contextual retrieval 係全域 retrieval 質素提升,唔係 per-KB 取捨;做成 per-KB toggle 等於無謂複雜化(Karpathy §1.2)。Reject。
- **改 chunker 令 section leaf 更 specific**(把「System Instruction for each step」換成「GL03-1 Create General Journal」):依賴 doc 標題結構、唔通用、且唔解 embedding/rerank context 缺失嘅根。Reject。
- **換 reranker vendor**:H2 鎖 Cohere v4.0-pro;且問題唔喺 vendor 質素,係餵佢嘅 text 缺 context。Reject。

## Consequences

- **Positive**:reranker + vector 候選池都能區分章節 → off-topic 章節(GL05 Reversal / GL02)清走、正確程序(GL03)升頂;全域改善所有 KB;query-time fallback 保證 legacy chunk 零 regression。
- **Negative**:embedding context 要 re-index 受影響 KB(Free-tier 3-index 槽,需逐個 in-place;本期只 re-index `drive-images-1`,其餘 KB 待有真實 source + 需要時再 re-index);rerank document 變長少少(section_path 通常 < 100 char,對 Cohere token 成本影響可忽略)。
- **Neutral**:stored `chunk_text` 不變 → citation 顯示 / `/chunks` listing / Finding D 圖片排序全部唔受影響;architecture.md §3.6 文字需更新(「rerank document = section context + chunk_text」)。

## References

- architecture.md §3.2(reranker)/ §3.3 §3.5(ingestion / chunking)/ §3.6(index schema + rerank document)
- `retrieval/reranker/cohere.py` / `azure_semantic.py`
- BUG-034 progress.md(問題1 診斷 + Finding D 圖片排序,presentation 層;本 ADR 解底層 rerank/embedding 層)
- CH-008 spec(本 ADR 嘅實作 change)
- 驗證實驗(2026-06-07,74-chunk Cohere rerank A/B 對照)
- ADR-0012(Cohere v4.0-pro lock)/ ADR-0040(per-KB tunable config — 區分:本 ADR 係全域,非 per-KB)
