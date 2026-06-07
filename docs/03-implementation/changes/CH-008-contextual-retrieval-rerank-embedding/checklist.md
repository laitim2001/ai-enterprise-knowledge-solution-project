---
change_id: CH-008
spec_ref: ./spec.md
---

# CH-008 — Checklist

> 逐項 atomic;done → `→[x]`,未做標 🚧 + 理由(per CLAUDE.md sacred rule)。

## Implementation
- [ ] I1 — `build_contextual_document(section_path, chunk_text)` helper(`retrieval/contextual.py`);section_path 空 → fallback 純 chunk_text
- [ ] I2 — `cohere.py` rerank document 用 helper
- [ ] I2b — `azure_semantic.py` rerank document 用 helper(一致性)
- [ ] I3 — ingestion embedding input 用 helper(embed `context+text`,stored chunk_text 原文不變)— 找 embed 計算點
- [ ] I7a — architecture.md §3.6 文字更新(rerank document = section context + chunk_text)
- [ ] I7b — C04 + C03 design note bump

## Tests (H6)
- [ ] T1 — `build_contextual_document`:有 path → `"<path>\n<text>"`;空 path → 純 text;多層 path join
- [ ] T2 — `cohere.py` rerank document 構造用 contextual(mock；assert payload documents 含 section)
- [ ] T3 — embedding-input 構造用 contextual(找 embed 點 → assert embed 收到 context-prefixed 串;stored chunk_text 不變)

## Re-index + Verification
- [ ] V1 — backend pytest(retrieval + ingestion 相關)pass + ruff + mypy(改檔)0 新 error
- [ ] V2 — `drive-images-1` in-place re-index(I3 embedding 生效)
- [ ] V3 — retrieval-test(GL)before/after:top-8 由 §5.1.3 GL05 #1 + §2.1.x → GL03 為主、off-topic 清走(AC4)
- [ ] V4 — 現有 eval set 無 regression(AC5)
- [ ] V5 — chat live 驗(用戶):GL 答案錨 GL03 + 圖由 Create 行先(配合已 merge Finding D)

## Closeout
- [ ] C1 — spec status → done;progress closeout
- [ ] C2 — ADR-0045 Proposed → Accepted
- [ ] C3 — commits 對應 Day-N(R2);ff-merge 入 main(用戶確認)
