---
bug_id: BUG-033
title: "Chat: KB selector not restored on conversation switch + ordered/bulleted list markers missing"
severity: Sev3          # Sev1 | Sev2 | Sev3 | Sev4 (per PROCESS.md §4.5)
status: done            # triaged | investigating | fixing | verifying | done | wont-fix
reported: 2026-06-07
reporter: "Chris (end-user testing on chat page)"
affects_components: [C10]      # Frontend Chat UI (chat/page.tsx)
spec_refs:
  - architecture.md §5 (frontend chat surface)
  - frontend/app/(app)/chat/page.tsx
---

# BUG-033 — Chat KB-not-restored on conversation switch + list markers missing

> **Report version**:1.0(initial)
> **Triage approver**:Chris(2026-06-07 — chat「開 BUG report 一齊修呢兩個」）

兩個獨立、同喺 chat 頁(C10)、同 session 測試發現嘅前端 bug,合併一個 BUG instance 修。

## 1. Symptom

- **Finding A(KB restore)**:喺左側 Conversations 揀返一個舊對話時,頂部 KB selector **永遠顯示第一個 KB**(`DCE Integration (images)`),而唔係嗰個對話原本綁定嘅 KB。
- **Finding B(list markers)**:detailed 答案嘅 numbered/nested 步驟**冇顯示數字標示**(`1. 2. 3.`)—— 只見到粗體標題 + 縮排嘅純文字行,用戶難以逐步跟。

## 2. Reproduction Steps

**Finding A**:
1. 開 `/chat`,左側有多個對話(各綁不同 KB:dce-integration-images-1 / w56-drive-ab-1 / test-kb-* …)。
2. 揀一個 KB ≠ 第一個 嘅對話(例 `w56-drive-ab-1` 嗰個)。
3. **Observed**:頂部 KB selector 仍係第一個 KB,唔係 `w56-drive-ab-1`。

**Finding B**:
1. `w56-drive-ab-1` 設 `answer_detail=detailed`(CH-006),`/chat` 問「How do I post a journal entry in General Ledger?」。
2. **Observed**:答案有階層縮排但**leaf 步驟前無 `1. 2. 3.`**。

**Reproduction reliability**:Always(兩者皆穩定重現）

**Environment**:local dev,frontend `localhost:3001`(Next.js dev),Chromium

## 3. Expected vs Actual

**Finding A**
- **Expected**:揀對話後,KB selector 還原成該對話 `conversation.kb_id`(對話 list item 本身有顯示 kb_id,理應一致)。
- **Actual**:KB selector 永遠停喺 `kbs[0]`。

**Finding B**
- **Expected**:numbered list 顯示 `1. 2. 3.`(LLM 已輸出正確 markdown ordered list)。
- **Actual**:無數字。**已抽 raw markdown 證實 LLM 輸出正確**(`1. ... \n   1. ... \n      1. Click... \n         2. Click New`)→ 純前端 render 吞咗。

## 4. Impact

- **Affected**:所有 chat 用戶。Finding A:切對話後若無為意 selector,新訊息會發去**錯誤 KB**(correctness risk,但可手動 re-select)。Finding B:detailed 答案可讀性下降(cosmetic)。
- **Workaround**:Finding A = 手動再揀 KB;Finding B = 無(要睇 raw 先知有號)。
- **Data loss / corruption?**:No
- **Security implication?**:No

## 5. Severity Justification

**Sev3** per PROCESS.md §4.5:影響 usability + 一個 recoverable correctness risk(發錯 KB),但有 workaround、無資料損失、核心檢索/生成功能正常。非 Sev2(無 broad 數據完整性破壞)、非 Sev4(多過純 cosmetic — Finding A 有錯發 KB 風險)。

## 6. Initial Diagnosis(root cause confirmed 2026-06-07)

**Finding A — confirmed root cause**:`chat/page.tsx` `loadConversation()`(line 292-316)load `detail.messages` 但**從不 `setKbId(detail.kb_id)`**;`ConversationDetail.kb_id` 欄位存在(`lib/api/conversations.ts:62`)。selector 受 line 221 useEffect 鎖喺 `kbs[0]`(當 `kbId` 為 '' 或 invalid 時)。

**Finding B — confirmed root cause**:`AnswerBodyMarkdown` 嘅 `ol`(line 1405-1407)/ `ul`(1408-1410)custom renderer 只設 `paddingLeft`,**冇 `list-style-type`**;`globals.css` 第 1 行 `@tailwind base` → Tailwind preflight reset `ol,ul { list-style: none }` → markers 被吞。**非 synthesis prompt 問題**(prompt 已正確輸出 numbered markdown)。

## 7. Acceptance for Fix(checklist preview)

- [ ] Finding A 重現確認(切對話 KB 不變)
- [ ] Finding A root cause 確認(loadConversation 缺 setKbId)
- [ ] Finding A fix:`loadConversation` 加 `if (detail.kb_id) setKbId(detail.kb_id)`
- [ ] Finding B 重現確認(numbered list 無號)
- [ ] Finding B root cause 確認(ol/ul 缺 list-style-type vs Tailwind preflight)
- [ ] Finding B fix:`ol` 加 `listStyleType:'decimal'`、`ul` 加 `listStyleType:'disc'`
- [ ] Regression test 加(Finding A:loadConversation setKbId;Finding B:ol/ul style 含 list-style-type)
- [ ] frontend tsc + lint + vitest 0 regression
- [ ] Live 驗:切對話 KB 還原 + detailed 答案顯示 `1. 2. 3.`

## 8. Report Changelog

| Date | Change | Reason | Approver |
|---|---|---|---|
| 2026-06-07 | Initial triage + root cause confirmed(both findings)| chat 頁測試發現;診斷已完成(loadConversation 缺 setKbId / ol-ul 缺 list-style-type)| Chris |

---

**Out-of-scope（明確)**:「Step N:」字面前綴(需 prompt 改,用戶選 `1. 2. 3.` CSS 方案);per-KB 自訂 prompt UI(未規劃);nested list 逐層不同 marker（decimal/alpha/roman polish,本 BUG 用 decimal 全層）。
