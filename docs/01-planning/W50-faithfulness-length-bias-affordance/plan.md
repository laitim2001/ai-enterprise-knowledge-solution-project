---
phase: W50-faithfulness-length-bias-affordance
name: "Config-Test Faithfulness Length-Bias Affordance (決策 7 Option d, 平 part)"
sprint_week: W50
start_date: 2026-06-05
end_date: 2026-06-05          # actual close (D1; F0-F3 all same-day)
status: closed
spec_refs:
  - ROADMAP-per-kb-tunable-config.md 決策 7 Option (d)(length-bias UI 標示;completeness/recall 對沖指標屬 ideal)+ 逐期重點 bullet 證據②
  - ADR-0040 (per-KB config-scope + config-test 雙軸)
  - architecture.md §5.5.5 (KB Detail Settings config-test 試跑 panel)
  - W49 phase(faithfulness N-run band — 本期接住補 known limitation)
  - references/design-mockups/ekp-page-kb.jsx(KbTestResultCard faithfulness headline + 試跑 panel footer)
prior_phase: W49-faithfulness-quality-band
---

# Phase W50 — Config-Test Faithfulness Length-Bias Affordance

> **Plan version**:1.0(initial)
> **Owner**:Chris(Tech Lead)
> **Approved by**:Chris(2026-06-05 AskUserQuestion:W50 起點 = **A. length-bias 對沖**;揀嘅 option 已 scope「先做平 part:UI 明標 length-bias;再評估係咪加 completeness/recall 對沖指標」)

## 1. Scope

收 **決策 7 Option (d) 嘅「平 part」**:W49 令 faithfulness 由 single-shot → N-run band(用戶見到噪音)。但 W49 live-verify 同時印證 roadmap 證據② 嘅更深問題 —— **RAGAs faithfulness 系統性懲罰長/全面答案**(列舉 query:完整 SAVED 答案 0.019 vs 退化短答 DRAFT 1.0),即**質素軸可能同 completeness 反相關**。用戶撥 config 令答案更完整時,faithfulness 反而跌,可能誤判「更完整嘅 config 更差」。

本期加一個 **length-bias UI explainer affordance** 到 config-test 試跑面板,**明確教育**用戶:faithfulness 對長/全面答案有 length bias;低分配合高引用/長答案(presentation 完整性訊號高)時,**多為 bias 而非 config 差**;應對照 presentation 軸(引用數 / 字數)+ 將來 recall 一齊判讀,**勿與 completeness 混為一談**。

**Scope kickoff R6 grep 已驗**(read mockup ekp-page-kb.jsx):mockup 現成 hint 模式齊 —— `.hint` class(小 muted 文字)/ `title=` native tooltip / 「What is this?」expandable;length-bias affordance 沿用呢啲,**無需新 component**。result card faithfulness headline(W49)+ 試跑 panel footer 係落點候選。

**Out-of-scope(按用戶「再評估」+ Karpathy simplicity)**:
- **completeness/recall 對沖指標**(加新 metric / synthetic-QA / per-run distinct-sections band)→ 屬 ideal,留 **W51+ 候選評估**(per_citation 現 last-run only,真 recall 無 ground truth — 需另設計)。
- **conditional data-driven hint**(faith 低 + completeness 高 → 自動 flag)→ 需 arbitrary threshold,本期用 **static explainer**(無 threshold,更 honest);conditional 屬後續 refinement。
- backend 改動(length-bias 純資訊性,用現有 card 資料 — **frontend-only**)。
- judge LLM / faithfulness 計算本身(不動)。

**Sprint week origin**:roadmap 決策 7 Option (d);Chris 2026-06-05 pick(W49 closeout 後)。

## 2. Key Design Decisions(kickoff lock)

- **Static explainer,無 arbitrary threshold**:always-on 教育性 affordance,唔靠「faith < X」啟發式判 length-bias(會 arbitrary)。直接講清 faithfulness 嘅 bias 性質 + 點對照 completeness 判讀。
- **Frontend-only**:length-bias 係資訊性,用 result card 現有資料(faithfulness band + 引用數 + 字數);**無 backend / 無新 endpoint / 無新 dep**。
- **Design-first per H7(ADR-0024)**:先改 mockup `ekp-page-kb.jsx` → 令 `page.tsx` 100% match。
- **落點(design-first 時定案)**:候選 = (a) faithfulness「忠實度」label 加 `title=` tooltip(on-the-spot)+ (b) 試跑面板一處 length-bias caveat note(單一位置,A/B 兩卡共用,唔 per-card 重複)。實作時揀最 H7-consistent + 最低視覺噪音組合。
- **無新 ADR**:純前端資訊性 affordance,extend 既有 config-test panel(非新架構/vendor/storage)。

## 3. Deliverables

### F0 — Phase kickoff
- **Acceptance criteria**:plan/checklist/progress 三件套 committed(R1);scope(平 part / static / frontend-only)+ key design 鎖定;R6 grep 記 progress
- **Owner**:AI

### F1 — Frontend:length-bias explainer affordance(H7 design-first)
- **Spec ref**:§5.5.5;mockup `ekp-page-kb.jsx` KbTestResultCard faithfulness headline + 試跑 panel
- **Acceptance criteria**:
  - mockup `ekp-page-kb.jsx` 先改:faithfulness affordance 加 length-bias explainer(label `title=` tooltip + 單一位置 caveat note;design-first 定案落點)。文案要點:faithfulness 反幻覺但對長/全面答案有 **length bias** → 低分配高引用/長答案多為 bias 非 config 差 → 對照引用數/字數(+ 將來 recall)判讀,勿與 completeness 混為一談
  - `page.tsx` `ConfigResultCard` + 試跑 panel 100% match 更新後 mockup(H7 fidelity)
  - tsc --noEmit clean + next lint clean + `[oklch`=0 preserved
- **Owner**:AI

### F2 — Test + verify
- **Spec ref**:§5.6 H6(frontend nice-to-have;config-test panel)
- **Acceptance criteria**:
  - frontend vitest:`kb-settings-tuning` 試跑 test assert length-bias explainer 渲染(caveat note text 或 tooltip attr present)
  - 既有 kb-settings-tuning + 相關 test 0 regression
  - tsc + lint clean
- **Owner**:AI

### F3 — Doc-sync + closeout
- **Acceptance criteria**:
  - architecture.md §5.5.5 加 W50 amendment(length-bias affordance;static explainer;completeness 對沖留未來)
  - roadmap 決策 7 Option (d)「平 part」→ ✅ done(completeness 對沖指標仍 ideal 留 W51+)+ 修訂史 entry
  - session-start §10 W50 row + plan.md status→closed + changelog
  - Phase Gate G1-G4 + retro + carry-overs + checklist tick / 🚧
- **Owner**:AI

## 4. Success Criteria(Phase Gate)

| # | Criterion | Target | Measure | Block closeout? |
|---|---|---|---|---|
| G1 | config-test panel 有 length-bias explainer affordance | static note + label tooltip 渲染 | mockup 對齊 + vitest | Yes |
| G2 | 100% match mockup(H7 fidelity)| design-first mockup → page.tsx 對齊 | mockup 對齊 | Yes |
| G3 | frontend tsc/lint/build clean + vitest 0 regression | all green | CI commands | Yes |
| G4 | frontend-only + 無新 ADR/vendor/backend | review | review | Yes |

## 5. Risks(Phase-Specific)

| # | Risk | Likelihood | Impact | Mitigation |
|---|---|---|---|---|
| R1 | explainer 文案誤導(過度貶低 faithfulness)| Low | Med | 文案平衡:faithfulness 仍係反幻覺有效軸,只係對長答案有 bias,需對照判讀 — 唔係「faithfulness 冇用」 |
| R2 | H7 mockup drift(affordance 視覺 / 落點)| Low | Med | design-first 先改 mockup;不清晰 → STOP+ask(§5.7)|
| R3 | scope creep 去做 completeness 指標 | Med | Low | 本期 static explainer only;completeness/recall 對沖明文 out-of-scope(W51+)|

## 6. Day-by-Day Breakdown(rough)

| Day | Date | Focus | Deliverables |
|---|---|---|---|
| D1 | 2026-06-05 | F0 kickoff + F1 frontend affordance + F2 test + F3 closeout(小 phase,同日)| F0-F3 |

## 7. Plan Changelog

| Date | Change | Reason | Approver |
|---|---|---|---|
| 2026-06-05 | Initial plan | W50 kickoff;Chris AskUserQuestion 揀 W50 起點 = **A. length-bias 對沖**(平 part:static UI explainer;completeness/recall 對沖指標留 W51+ 評估)| Chris |
| 2026-06-05 | 落點定案:忠實度 label `title` tooltip + A/B grid 下單一 caveat note(`AlertTriangle`)| design-first F1;單一位置避 per-card 重複 + tooltip on-the-spot | AI |
| 2026-06-05 | status active → closed;end_date set(D1 全 F0-F3 同日)| Phase Gate G1-G4 PASS;決策 7 Option (d) 平 part done | AI |

---

**Lifecycle reminder**:plan locked after status=active。重大 deviation 入第 7 節 changelog。**F1 frontend = H7 design-first**(mockup 係 canonical spec,先改 mockup 再 match)。**Frontend-only**(無 backend / 無新 metric)。
