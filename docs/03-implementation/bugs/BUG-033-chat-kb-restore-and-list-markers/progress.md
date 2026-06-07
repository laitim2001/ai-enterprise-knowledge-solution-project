---
bug_id: BUG-033
report_ref: ./report.md
checklist_ref: ./checklist.md
status: closed          # in-progress | closed
---

# BUG-033 — Progress

> Investigation → fix → verify。每 commit 對應 Day-N(R2)。

---

## Day 1 — 2026-06-07

### Done
- (kickoff)report.md(Sev3,both findings root-caused)+ checklist + progress committed。
- Investigation 已完成(triage 時即 root-caused,見下)。
- (pending fix F-A/F-B + regression test + verify)

### Diagnosis update
- **Finding A**:`loadConversation()`(chat/page.tsx:292)只 `setMessages`,**缺 `setKbId(detail.kb_id)`**;`ConversationDetail.kb_id?: string|null` 存在(conversations.ts:62)→ selector 被 line 221 useEffect 鎖 `kbs[0]`。
- **Finding B**:LLM raw markdown **正確輸出** nested numbered list(`1.`/`   1.`/`      1.`…),但 `AnswerBodyMarkdown` `ol`/`ul` renderer(chat/page.tsx:1405-1410)缺 `list-style-type`;`@tailwind base`(globals.css:1)preflight reset `list-style:none` → markers 消失。**非 prompt 問題。**

### Decisions
- 用戶選 **`1. 2. 3.` CSS 方案**(非「Step N:」prompt 改)→ 純前端,唔郁 backend prompt。
- nested 全層用 `decimal`(minimal;逐層不同 marker 屬 polish,out-of-scope)。
- 兩 finding 合一 BUG instance(同 chat 頁 / 同 session / 皆 Sev3 / 皆 surgical)。

### Blockers
- 無。

### Effort
- Planned ~1-2h;Actual:_(填)_

### Commits
| Hash | Subject |
|---|---|
| _(待)_ | docs(bug): BUG-033 kickoff |

---

## Closeout — 2026-06-07

### Root cause(both confirmed)
- **A**:`loadConversation()` 缺 `setKbId` → selector 鎖 kbs[0]。**修正注意**:kb_id 喺 `detail.conversation.kb_id`(ConversationDetail = `{conversation, messages}`),初稿誤寫 `detail.kb_id`,tsc 前自捉改正。
- **B**:`ol`/`ul` renderer 缺 `list-style-type`;`@tailwind base` preflight reset `list-style:none` 吞 marker。LLM markdown 本身正確(已抽 raw 證)。

### Fix
- `chat/page.tsx`:loadConversation 加 `setKbId(detail.conversation.kb_id)`;AnswerBodyMarkdown `ol`→`listStyleType:'decimal'`、`ul`→`'disc'`。純前端,2 處 + 註釋。

### Verification
- `chat-bug033.test.tsx` 2/2 pass(A:selector kb-a→kb-b;B:`ol.style.listStyleType==='decimal'`)。
- tsc exit 0;eslint 0 error(1 pre-existing `<img>` warning 非本 fix);chat-kb-sync+meta-row 10 passed 0 regression。
- live-UI:用戶 refresh `/chat`(Next.js HMR)即見(切對話 KB 跟住變 + detailed 答案顯示 1. 2. 3.)。

### Lessons
- **型別前提要核實**:初稿假設 `detail.kb_id` 頂層存在(grep 誤把 Create/Update payload 嘅 kb_id 當 ConversationDetail)→ 正確係 `detail.conversation.kb_id`。教訓:改 API 消費點,睇實 interface 定義,唔好靠 grep 行號估;tsc 係安全網但應 think-before。
- **CSS 對抗框架 reset**:Tailwind preflight 會 reset list-style,custom markdown renderer 必須明確 re-assert marker。
- **(承 CH-006/CH-007 教訓)** 改 component 用 unit test 精準鎖行為,避免 hand-picked subset 漏 caller。

### Effort
- Planned ~1-2h;Actual ~1h(diagnosis 早於 triage 完成)。

### Commits
| Hash | Subject |
|---|---|
| `d1d8c7a` | BUG-033 kickoff(report + checklist + progress)|
| _(fix)_ | fix(frontend): BUG-033 — KB restore + list markers(C10)|

### Branch
- 按用戶 Option A:喺 `feat/retrieval-per-kb-top-k` 完成 → 收尾 ff-merge 全部(CH-007 + CH-006-recovery + BUG-033)入 main + push。

---

**End of BUG-033 progress**
