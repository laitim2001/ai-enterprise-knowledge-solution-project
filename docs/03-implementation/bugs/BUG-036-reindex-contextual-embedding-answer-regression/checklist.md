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
- [x] F1 — 改 `_RULE_3_DETAILED`（`backend/generation/prompt_builder.py`）：(1) 移除 "merge" 過度忠實字眼 + distinct-step dedup（去重複 heading）；(2) **follow-up** — 用戶反映第一版 dedup **順手 flatten 咗**(失去 nested 分組),加「PRESERVE source grouping + NEST 子組步驟 + 唔 flatten」；(3) **follow-up #2** — 用戶截圖比對確認「group **headings**」字眼令 gpt-5.5 渲染成 **markdown 標題**(每組重設編號、得 2 層),非要嘅**單一連續 3 層嵌套編號清單**。換走「group headings」→ 明文「single continuous nested ordered (numbered) list」+ 三層定義 + 組標題粗體 + **禁 Markdown headings** + 禁 flatten/reset + **嵌入 few-shot worked example**；concise 變體不變
- [x] F2 — regression test（dedup + grouping/nest/flatten + nested-numbered-list/no-headings/few-shot assertions）+ 既有 prompt test 全綠（**17** answer_detail）

## Verify
- [x] V1 — 重跑 repro（backend /query，新 prompt）：(a) §GL03-2「Confirm Approval Request ×3 / Approve General Journal ×2」→ **每 step 一次**；(b) **結構還原 nested 分組**（`## 3.1.1 Overview` / `## 3.1.3` + `### Create General Journal header` / `### Prepare excel file` / `### Upload excel file` … 每組 numbered 步驟,唔再 flat 1.1–1.19）；完整性保留；deduped。**注意**:測試期機器重度 load,query ~220s（event-loop starvation,非 backend 壞,per memory loaded-machine）
- [x] V2 — **CH-011 圖片 doc_order 不受影響**：prompt 改動只掂 synthesis 文字,圖片 attach/pin/sort 路徑無關;13 citations + lead doc_order-sorted 圖不變
- [ ] V3 — 用戶 live 驗（chat UI hard refresh + 問 GL03）

## Closeout
- [ ] C1 — postmortem.md（Sev2 mandatory）— 重點：re-index 副作用未預警
- [ ] C2 — report status → done;ff-merge（用戶確認）
