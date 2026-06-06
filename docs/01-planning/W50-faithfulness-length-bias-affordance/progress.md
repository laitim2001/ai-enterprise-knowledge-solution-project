# W50 — Faithfulness Length-Bias Affordance · Progress

> Daily progress + decisions + commits + 結尾 retro。每 daily commit 對應 Day-N entry(R2)。

---

## Day 1 — 2026-06-05

### Context / kickoff
W49 closed + pushed(`ac172b0`,API + UI live-verify band 重現)。用戶問「W43 vision 仲有幾多未做」→ 我給全圖;用戶 pick W50+ 候選 = **A. length-bias 對沖**(決策 7 Option d)。

### 決策
- **AskUserQuestion(W50 起點)**:Chris 揀 **A. length-bias 對沖**(否決 B per-document 需先解 AUDIT-E 語意 + C ingestion eval 新 harness)。揀嘅 option description 已 scope:「**先做平 part:UI 明標 length-bias;再評估係咪加 completeness/recall 對沖指標**」。
- **Key design lock**(plan §2):static explainer(無 arbitrary threshold)+ frontend-only(用現有 card 資料,無 backend/新 metric)+ H7 design-first + 無新 ADR。completeness/recall 對沖指標 + conditional data-driven hint **明文 out-of-scope**(留 W51+ 評估)。

### R6 grep 驗證(plan kickoff)— mockup hint 模式
- mockup `ekp-page-kb.jsx` 現成 hint 模式齊:`.hint` class(小 muted 文字)/ `title=` native tooltip(line 573/598)/ 「What is this?」expandable(line 956 reindex card)→ length-bias affordance 沿用,**無需新 component**。
- result card faithfulness headline(W49)+ 試跑 panel footer(`:942`)係落點候選 → 落點 design-first 時定案。
- **無 plan-text contamination**:plan 引用嘅 mockup 模式 grep 對齊現實(R6 recursive scope 過)。

### Done
- F0 R1 phase 三件套建立(plan/checklist/progress);Phase Gate G1-G4 定義

### Commits
- (F0 kickoff commit pending)

### Blockers / carry-over
- 無 blocker。infra 已起(azurite 23252 / backend 8000 W49 code / frontend 46364 clean .next)。**注**:本期 frontend-only,frontend dev hot-reload 即時反映,**唔使** restart backend。
