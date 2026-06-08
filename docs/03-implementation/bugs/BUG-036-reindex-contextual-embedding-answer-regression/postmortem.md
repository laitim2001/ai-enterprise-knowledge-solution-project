---
bug_id: BUG-036
report_ref: ./report.md
progress_ref: ./progress.md
written: 2026-06-09
author: "Claude (AI)"
sign_off: pending     # pending | signed
---

# BUG-036 — Postmortem

> Mandatory for Sev2（per PROCESS.md §4.5）。

## 1. Incident Timeline

| Time | Event |
|---|---|
| (CH-011 verify) | 為 CH-011 doc_order re-index drive-images-1 — 首次套 CH-008 contextual embedding 落此 KB |
| 2026-06-08 ~23:27 | 用戶 chat 測試,發現文字答案格式由清晰變亂（重複行 + synthetic 重編號）|
| +5 min | triage：確認 CH-011 圖片修復 intact，文字側 regression；開 BUG-036 Sev2 |
| +15 min | 診斷：唯一變數 = re-index 引入 contextual embedding；13 cites = 4 reranked + 9 expansion |
| +25 min | **I4 root cause**：讀 §3.1.4 chunk 原文 → 重複 heading 係 **source-inherent**（process-step-list 摘要表 + 逐步 heading + caption）；`_RULE_3_DETAILED` 明令「do NOT merge」→ LLM 忠實列冗餘 |
| +35 min | Fix：改 `_RULE_3_DETAILED`（distinct-step dedup + summary-table fold）+ regression test |
| +50 min | Verify：backend /query 新 prompt → §GL03-2 重複消失，完整性保留，CH-011 圖片不受影響 |
| **Total**:~50 min（report → backend-verified fix）| |

## 2. Root Cause（detailed）

兩層：

**(a) 觸發 — re-index 副作用**：CH-011 為加 `doc_order` 對 drive-images-1 做 re-index。Re-index 唔單止加 doc_order metadata —— 佢**重跑成個現行 ingest pipeline**，包括 **CH-008 contextual embedding（ADR-0045，同日 merge，`build_contextual_document` always-on 無 toggle）**。drive-images-1 原 index 係非-contextual；re-index 後變 contextual → 檢索 ranking shift → **process-step-list 摘要表 chunk 同逐步 detail chunk 同時 surface**。

**(b) 根本 — detailed synthesis 過度忠實**：源手冊結構性重複每個 step（摘要表項 + section heading + caption）。`_RULE_3_DETAILED` 原文明令「enumerate EVERY step... do NOT summarize, compress, **merge**, or omit」→ LLM 把所有重複 heading 逐行列 → synthetic 重編號 + 重複行（「Confirm Approval Request」×3 等）。(a) 令兩個重複 chunk 同時入 context，放大 (b)。

**Fix**：改 `_RULE_3_DETAILED` —— 保「every DISTINCT step」（完整性），但加「list each distinct step ONLY ONCE + 唔把 summary/process-step-list 表當獨立步驟，fold 入 detailed step」。移除過度忠實嘅 "merge" 禁令。

**Why didn't this surface earlier?**
- contextual embedding（CH-008）同日先 merge，drive-images-1 從未喺 contextual 下被 query 過 —— re-index 係第一次。
- `detailed` 模式 + 完整性 expansion + 圖密程序手冊（摘要表+逐步重複結構）嘅組合係 drive-images-1 獨有；其他 eval KB 無此 source 冗餘結構。
- **最關鍵**：re-index 操作被當成「純加 doc_order」，無人預期佢會 re-embed 改檢索 → 改文字答案。**re-index = 全 pipeline 重跑**呢點未被 surface。

## 3. Impact Assessment

- **Users affected**：drive-images-1（demo KB）程序型 query；僅本地 dev，未到 Beta/Prod。
- **Duration**：~50 min（從用戶發現到 backend-verified fix）。
- **Data loss / corruption**：No（index 完整，純答案 formatting）。
- **Workarounds**：內容仍齊全可用，只係格式亂。
- **Cost impact**：minimal（幾次 re-query 嘅 LLM 成本）。

## 4. What Worked

- 用戶即時 chat 測試 catch 到（CH-011 V2 UI verify 嘅副產品）。
- 讀 source chunk 原文（I4）快速分清「source-inherent vs synthesis 幻覺」→ 鎖定正確 fix 層（synthesis prompt，非 retrieval / 非 config）。
- 改動隔離喺 `detailed` 變體 + 既有 40 prompt test + 新 regression test 守住 concise/cross-KB 不受影響。

## 5. What Didn't Work / Was Slow

- **落 re-index 前無 warn 用戶會 re-embed（contextual）影響文字答案** —— 應喺 CH-011「Commit+重啟+re-index」決策前明列副作用。
- CH-011 spec 嘅 re-index 風險（R4「re-index 令 chunk_index 變」）只諗咗 chunk_index，**漏咗 embedding 演進（CH-008）令檢索/答案改變**。

## 6. Surprises

- 重複行原來係 **source 文件本身結構性冗餘**（摘要表+逐步+caption），唔係 synthesis 亂生 —— `detailed` 模式「忠實」反而放大咗源缺陷。
- contextual embedding（CH-008，本意改善檢索）喺呢個 case 透過「提升 recall 令兩個重複 chunk 同時 surface」間接令答案變差 —— 改善 recall 同改善可讀性唔一定同向。

## 7. Action Items

| # | Action | Owner | Due | Component(s) | Status |
|---|---|---|---|---|---|
| 1 | Re-index 操作前 checklist：明列「re-index = 全 pipeline 重跑（chunker + contextual embedding 現行版）→ 可能改檢索/答案」,提醒比對 KB 原 ingest 版本 | Chris | — | C02/C03 | Open |
| 2 | 考慮 `detailed` synthesis 對「source 冗餘 heading」嘅穩健性（本 fix 係 prompt-soft;若 variance 大可加 post-process 去連續重複行） | AI | W next | C05 | Open |
| 3 | 評估 contextual embedding 是否需 per-KB toggle（部分 KB 可能唔受惠 + 有副作用） | Chris | — | C04 | Open（呼應 ADR-0045 後續）|

## 8. Risk Register Update

- 新風險候選：**「re-index 副作用 — 全 pipeline 重跑令既有 KB 檢索/答案 drift」**（pipeline 演進 vs 既有 index 版本落差）。建議入 RISK_REGISTER（🟡 partial — 本 bug 已 surface + action item 1 緩解）。

## 9. Component Design Note Updates

- `components/C05-generation.md`：可補 detailed-mode「source 冗餘 heading dedup」edge case（per CC-5）— deferred 非阻塞。

---

**Sign-off**:Claude (AI) | Date:2026-06-09
**Reviewed by**:_(待 Chris)_ | Date:—
