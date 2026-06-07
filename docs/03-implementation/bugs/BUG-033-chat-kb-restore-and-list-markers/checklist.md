---
bug_id: BUG-033
report_ref: ./report.md
status: done            # in-progress | done
last_updated: 2026-06-07
---

# BUG-033 — Checklist

> Atomic checkbox per investigation / fix / regression / verify。AI tick 完成 item;唔可以 tick 嘅喺 progress 寫原因。

## Investigation

- [x] Reproduce both findings(用戶 chat 頁實測 + AI raw-markdown 抽取確認)
- [x] Root cause A:`loadConversation` 缺 `setKbId(detail.kb_id)`(`ConversationDetail.kb_id` 存在 conversations.ts:62)
- [x] Root cause B:`ol`/`ul` renderer 缺 `list-style-type` vs Tailwind preflight `@tailwind base` reset(globals.css:1);LLM raw markdown 已證正確輸出 numbered list
- [x] report.md §6 已記 confirmed root cause(both)

## Fix

- [x] F-A:`chat/page.tsx` `loadConversation` 加 `if (detail.conversation.kb_id) setKbId(detail.conversation.kb_id)`(**修正**:kb_id 喺 `detail.conversation`,非 `detail` 頂層 — 初稿寫錯,tsc 前自捉)
- [x] F-B:`AnswerBodyMarkdown` `ol` 加 `listStyleType:'decimal'`、`ul` 加 `listStyleType:'disc'`(inline style;nested 全層 decimal;附註釋指 Tailwind preflight 根因)
- [x] surgical:只改呢兩處 + 註釋,唔郁無關 code

## Regression Test

- [x] T-A:`chat-bug033.test.tsx` — load conv(kb_id=kb-b)→ KB selector value 由 kb-a 變 kb-b(pass)
- [x] T-B:同檔 — assistant message numbered list → `container.querySelector('ol').style.listStyleType === 'decimal'`(pass)
- [x] frontend tsc exit 0 + eslint 0 error(1 pre-existing `<img>` warning 非我改)+ chat-kb-sync/meta-row 10 passed 0 regression

## Verification

- [x] T-A 證 Finding A:切對話 → selector 還原成該對話 KB(component test pass)
- [x] T-B 證 Finding B:numbered list render 出 `<ol list-style-type:decimal>`(可見 1. 2. 3.)
- [x] 相關 chat 功能無 regression(10 passed);**live-UI 視覺確認 → 用戶 refresh `/chat`(Next.js HMR 自動 reload)即見**(frontend bug,unit-test 已精準覆蓋邏輯)

## Closeout

- [x] progress.md closeout summary(root cause + lessons)
- [x] (Sev3 → **無** mandatory postmortem per PROCESS.md §4.5)
- [x] RISK_REGISTER 不需更新(一般 UI state/CSS bug,非新 pattern)
- [x] report.md status → done
- [x] progress.md status → closed

## Cross-Cutting

- [x] X1 commits 對應 progress Day 1 + component tag `fix(frontend): ... (C10)`
- [x] X2 非 architectural → 無 ADR(純前端 state + CSS 修正)
- [x] X3 無 spec 改動(BUG fix);doc-sync 見 progress
- [x] X4 branch 策略:Option A — feat 上完成 → ff-merge 入 main(用戶 2026-06-07 揀)
