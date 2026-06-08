---
change_id: CH-008
spec_ref: ./spec.md
---

# CH-008 — Checklist

> 逐項 atomic;done → `→[x]`,未做標 🚧 + 理由(per CLAUDE.md sacred rule)。

## Implementation
- [x] I1 — `build_contextual_document(section_path, chunk_text)` helper(`retrieval/contextual.py`);section_path 空 → fallback 純 chunk_text
- [x] I2 — `cohere.py` rerank document 用 helper(+ docstring 更新)
- 🚧→**DROPPED** I2b — `azure_semantic.py` rerank document 用 helper(一致性)— **Chris 確認 drop 2026-06-08**。Rationale:azure_semantic **唔砌 document list**(re-issue `queryType=semantic` search,排序由 index `ekp-semantic-config` 決定)→ 無 document 可注入;Azure semantic 非 production reranker(Cohere H2 lock)+ chat 行 semantic OFF;該 fallback 路徑經 I3 embedding re-index 間接受惠候選池;真正注入需改 index schema(額外 H1,Karpathy §1.2 reject)。spec §6 changelog 記。
- [x] I3 — ingestion embedding input 用 helper(`orchestrator.py:153` embed_inputs,stored chunk_text 原文不變)
- [x] I7a — architecture.md §3.6 文字更新(rerank document + embedding input = section context + chunk_text;CH-008 amendment block)
- [x] I7b — C04(rerank)+ C01(embedding input)design note bump(C03 §3.6 doc 已 amend;component 名 C03→C01 修正)

## Tests (H6)
- [x] T1 — `build_contextual_document`:有 path → `"<path>\n<text>"`;空/None path → 純 text;多層 path join;whitespace-only entries drop(4 tests)
- [x] T2 — `cohere.py` rerank document 構造用 contextual(mock；assert payload documents[0] 含 section、documents[1] fallback)
- [x] T3 — embedding-input 構造用 contextual(capturing embedder → assert embed 收到 context-prefixed 串;stored chunk_text 不變)

## Re-index + Verification
- [x] V1 — backend pytest(`test_contextual_retrieval_ch008` + `test_reranker` + `test_orchestrator` 27 passed)+ ruff(all pass)+ mypy(改檔 0 新 error;17 個 pre-existing 全喺未 touch 檔)
- [x] V2 — `drive-images-1` in-place re-index DONE(6/6 reindexed,0 skipped,0 failed,369 chunks;I3 contextual embedding 生效)
- [x] V3 — retrieval-test(GL「post a journal entry」)before/after **AC4 PASS**:rerank=true top-8 = GL03 ×7 + GL05 #8(對照 ADR 實驗 baseline 純 chunk_text rerank #1 GL05 / #3-4 GL02);rerank=false 候選池 re-index 後跨文件 AR03 洩漏清走、GL03 佔比 4→5/8
- [x] V4 — **AC5 = 接設計+live 證據**(Chris 2026-06-08):full RAGAs eval 環境性 blocked(所有 eval-baseline KB index 在 Free-tier 3-slot 下已 drop;eval-set-v0 = W1 MFP placeholder 非 DRIVE corpus)→ regression 證據改以 ① fallback bit-identical unit test ② strictly-more-context 設計 ③ live DRIVE retrieval-test 改善(非 regression)三項
- [x] V5 — chat live 驗(用戶 2026-06-08)**文字維度 PASS**:GL「post a journal entry」答案 13/13 citation 全部錨 GL03 §3.1.x(Overview/System Instruction 順序),零 off-topic;`/query` 重現確認。**圖片維度**(裝飾燈泡 icon surface + `INLINE_IMAGE_CAP=8` 截斷 + 圖片相關性排序)= deferred problem 1,**split 到新工作**(非 CH-008 文字 scope;所有圖 source_section 正確喺 GL03,非 recall 錯)

## Closeout
- [x] C1 — spec status → done;progress closeout retro
- [x] C2 — ADR-0045 Proposed → Accepted(Chris 2026-06-08;README index 同步)
- [x] C3 — commits 對應 Day-N(R2);ff-merge 入 main(Chris 2026-06-08 go)
