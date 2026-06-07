---
change_id: CH-008
spec_ref: ./spec.md
checklist_ref: ./checklist.md
status: in-progress     # in-progress | closed
---

# CH-008 — Progress

> Day-N entries + closeout。每 commit 對應 Day-N mention(R2)。

---

## Day 1 — 2026-06-08

### Context
接 BUG-034 問題1 底層診斷。Finding D(圖按文件次序,presentation)已 merge;但純 rerank top-8 證 reranker 揀錯章節(§5.1.3 GL05 #1、§2.1.x GL02 #3/#4,GL03-Create 沉 #5-8),因為 reranker 只餵 `chunk_text`、section heading 又 generic 重複。74-chunk Cohere rerank A/B 實驗(2026-06-07)PASS:加 section context 後 off-topic 清走、GL03 升頂 7/8。用戶選全套(rerank + embedding,要 re-index)。

### Done
- (kickoff)ADR-0045 寫(Proposed)+ 入 ADR index;CH-008 spec(approved)+ checklist + progress committed(R1.change + R5 滿足)。
- (pending I1-I7 + re-index + eval + closeout)

### Decisions
- 全域 contextual retrieval(非 per-KB);format = `" > ".join(section_path) + "\n" + chunk_text`;section_path 空 → fallback 純 chunk_text(零 regression)。
- Stored `chunk_text` 維持原文(citation/listing/Finding D 不受影響);只 embedding 向量 + rerank document 加 context。
- 本期只 re-index `drive-images-1`(有真實 source、in-place、唔佔 Free-tier 新槽);其他 KB 多 stub source,另議。

### Blockers
- 無。

### Effort
- Planned ~0.5-1 day;Actual:_(填)_

### Commits
| Hash | Subject |
|---|---|
| _(待)_ | docs(adr+change): ADR-0045 + CH-008 kickoff |

---

**End of CH-008 progress (Day 1 in-progress)**
