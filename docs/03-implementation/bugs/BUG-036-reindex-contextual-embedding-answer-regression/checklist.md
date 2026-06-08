---
bug_id: BUG-036
report_ref: ./report.md
status: investigating     # investigating | fixing | verifying | done
last_updated: 2026-06-08
---

# BUG-036 — Checklist

> 逐項 atomic;done → `→[x]`,未做標 🚧 + 理由。Sev2 → postmortem mandatory。

## Investigation
- [x] I1 — repro 確認（API 2 run：13 cites = 4 reranked + 9 expansion；CAR×2 穩定）
- [x] I2 — config 確認（answer_detail=detailed / expansion depth=1 max_aux=10 / parent_doc=false / rerank_k=5）
- [x] I3 — 鎖定唯一變數 = re-index 引入 CH-008 contextual embedding（always-on，無 toggle）
- [x] I4 — **重複行 = source-inherent**（2026-06-08）：§3.1.4 chunk 原文真有重複 heading（process-step-list 摘要表「1 Confirm Approval Request / 2 Approve General Journal / 3 Reject…」+ 逐步 section「Confirm Approval Request」heading + 「Confirm approval request」step + caption）。`detailed` synthesizer 忠實逐行列 → 可見重複。**非 synthesis 幻覺**；contextual embedding 令摘要表 chunk + 逐步 chunk 同時 surface 放大之
- [x] I5 — **lever = synthesis prompt（用戶揀 A）**：`_RULE_3_DETAILED` 明文「do NOT summarize, compress, **merge**, or omit」正係令 LLM 忠實列冗餘 heading 嘅原因 → 改為「enumerate every DISTINCT step + list each distinct step ONLY ONCE + 唔把 process-step-list 摘要表當獨立步驟」。保完整性 + recall + 圖片,唔需 reduce expansion / contextual toggle

## Fix（A — synthesis dedup prompt）
- [x] F1 — 改 `_RULE_3_DETAILED`（`backend/generation/prompt_builder.py`）：移除 "merge" 過度忠實字眼 + 加 distinct-step dedup + summary-table fold 指示（BUG-036）；concise 變體不變
- [x] F2 — regression test（`test_detailed_variant_dedups_repeated_source_headings_bug036`）+ 既有 40 prompt test 全綠

## Verify
- [x] V1 — 重跑 repro（backend /query，新 prompt）：§GL03-2 由「Confirm Approval Request ×3 / Approve General Journal ×2」→ **每 step 一次**；完整性保留（create→validate→submit→approve/reject→post→voucher 全在）；答案 ~10300→~2098 字(去 cite) leaner
- [x] V2 — **CH-011 圖片 doc_order 不受影響**：prompt 改動只掂 synthesis 文字,圖片 attach/pin/sort 路徑無關;13 citations + lead doc_order-sorted 圖不變
- [ ] V3 — 用戶 live 驗（chat UI hard refresh + 問 GL03）

## Closeout
- [ ] C1 — postmortem.md（Sev2 mandatory）— 重點：re-index 副作用未預警
- [ ] C2 — report status → done;ff-merge（用戶確認）
