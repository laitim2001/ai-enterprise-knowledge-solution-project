---
bug_id: BUG-036
report_ref: ./report.md
checklist_ref: ./checklist.md
status: closed     # investigating | closed
---

# BUG-036 — Progress

> Day-N entries + closeout。Sev2 → postmortem mandatory。

---

## Day 1 — 2026-06-08

### Done
- 用戶 chat 測試揭文字答案 regression（CH-011 re-index 後）→ triage Sev2 → 開 BUG-036
- 診斷捕捉（report §6）：唯一變數 = re-index 首次套 CH-008 contextual embedding；13 cites = 4 reranked + 9 expansion；detailed synthesizer 列整段 → synthetic 重編號 + 重複行
- repro 確認（API 2 run 穩定 CAR×2）

### Decisions
- 用戶揀「開 Bug-fix 正式診斷+修」（over 即時 config 緩解 / contextual toggle+re-index）
- Sev2（核心 chat surface 品質 regression + 明確 defect + 用戶 flag 嚴重）→ postmortem mandatory
- branch `fix/chat-reindex-text-answer-regression`（off main）

- I4 **root cause = source-inherent 冗餘 heading**（讀 §3.1.4 chunk 原文確認）+ `_RULE_3_DETAILED` 「do NOT merge」令 LLM 忠實列
- I5 用戶揀 **A（synthesis dedup prompt）**
- **Fix**：改 `_RULE_3_DETAILED`（distinct-step dedup + summary-table fold，移除 "merge"）+ regression test；40 prompt test + 新 test 綠;ruff/format clean
- **Verify（backend，新 prompt）**：§GL03-2「Confirm Approval Request ×3 / Approve General Journal ×2」→ **每 step 一次**；完整性保留；CH-011 圖片不受影響;答案 leaner
- Postmortem 寫好（Sev2 mandatory）

### Blockers
- 無（fix backend-verified；待 V3 用戶 live 驗 + postmortem sign-off）

### Commits
| Hash | Subject |
|---|---|
| `f...`（triage）| docs(bug): BUG-036 triage Sev2 |
| _(this commit)_ | fix(generation): BUG-036 detailed-synth dedup repeated source headings |

---

## Day 2 — 2026-06-09 — 格式 regression 連環修(去重 → 壓平 → 標題化 → few-shot 釘死)

### Context
Day 1 去重後,用戶連續 2 輪 live 驗反映**文字格式**仍未還原到 re-index 前滿意嗰版。逐張截圖比對鎖定真正差別(非內容、係**結構渲染**)。

### Done
- **F1 第二輪(hierarchy)** `276eb5e`：第一版 dedup 順手把程序壓平做單層 `1.1..1.19`,失去源層級。加「PRESERVE source grouping + NEST 子組 + 唔 flatten」+ 把 "fold into single step" 改 "summary table = outline"
- **F1 第三輪(few-shot)** _(this commit)_：用戶截圖比對確認 — 第二輪「**group headings**」字眼令 gpt-5.5 把組渲染成 **markdown 標題**(`##`/`###`,每組重設編號、得 2 層),而非用戶要嘅**單一連續 3 層嵌套編號清單**(`1` → `1.1` → `1.1.1`,組標題=粗體編號 item)。修法:
  - 換走「group headings」→ 明文「render the ENTIRE procedure as ONE single CONTINUOUS nested ordered (numbered) list」+ 三層定義(top-level / sub-procedure / step)+ 組標題粗體 + **禁 Markdown headings** + 禁 flatten / 禁 reset 編號
  - **嵌入 few-shot worked example**(具體 3 層嵌套編號清單範本)— few-shot 對「格式重現」遠比抽象規則可靠
  - 去重指令(distinct step ONLY ONCE + summary-table=outline)保留不變
- **F2** regression test 加 `test_detailed_variant_nested_numbered_list_not_headings_bug036`(assert ordered / markdown heading ban / bold / worked example / level-1 numbered item)；`test_answer_detail_ch006.py` 17 passed；ruff/format clean

### Decisions
- 再郁 prompt 前同用戶 sync 目標格式(AskUserQuestion 確認 = 截圖2 嵌套編號清單)→ 避免第 4 次盲改(per CLAUDE.md §1.1 think-before-coding + §13 when-in-doubt)
- 根因定性:**唔係 recall / 唔係內容**,係 synthesis **markdown 結構渲染**;「group headings」wording 係我自己上一輪引入嘅 regression

### Blockers
- 無(few-shot fix backend-restart 載入中,待 /query 驗證 + V3 用戶 live 驗)

### Commits
| Hash | Subject |
|---|---|
| `276eb5e` | fix(generation): BUG-036 follow-up — preserve source hierarchy, not flat list |
| _(this commit)_ | fix(generation): BUG-036 follow-up #2 — nested numbered list + few-shot, not headings |

---

## Closeout — 2026-06-09

**判決**:✅ RESOLVED（用戶 live UI 確認「文字格式終於變回預期效果」）

- Fix 共 3 輪 prompt 演進(dedup → preserve grouping → nested numbered list + few-shot),根因 = re-index 引入 contextual embedding 令 source-inherent 重複 heading 同時 surface + `detailed` synthesis 過度忠實。
- 教訓(postmortem §5）:**re-index = 全 pipeline 重跑**(chunker + contextual embedding 現行版)→ 副作用未預警;格式精確重現靠 **few-shot worked example**(抽象規則 whack-a-mole 唔可靠,連錯 2 輪先 sync 用戶確認目標格式)。
- Action item 1（re-index pre-flight checklist)+ 新風險候選(全 pipeline 重跑 drift)入 postmortem §7/§8,建議入 RISK_REGISTER。
- ff-merge fix branch → main;V3/postmortem signed。

**Sev2 postmortem**:`./postmortem.md`(signed 2026-06-09）。

---

**End of BUG-036 progress**
