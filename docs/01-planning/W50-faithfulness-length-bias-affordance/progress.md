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

### F1 frontend(同日,H7 design-first)
- 落點定案:**(a) 忠實度 label `title=` tooltip**(on-the-spot,兩卡自動)+ **(b) A/B grid 下方單一 length-bias caveat note**(`IcAlert`/lucide `AlertTriangle` warning 色 + `<b>length bias</b>`,單一位置兩卡共用)。
- mockup `ekp-page-kb.jsx` 先改:`KbTestResultCard` 忠實度 label 加 `title`(faithfulness 性質 + length bias 警示 + 對照完整性訊號判讀)+ A/B 結果 grid 後加 caveat note(IcAlert + 「忠實度對長/全面答案有 **length bias** —— 低分若配合高引用數/長答案,多為 bias 而非 config 差,宜對照引用數/字數(+ 將來 recall)判讀,勿與完整性混為一談」)。
- `page.tsx` match:`ConfigResultCard` 忠實度 label 加同文 `title`;A/B grid(`result.saved ? 1fr 1fr : 1fr`)後加同款 caveat(`AlertTriangle` + 同文案),placement 對齊 mockup(grid 後、per-citation breakdown 前)。
- 驗:tsc --noEmit clean + next lint clean(唯一 pre-existing chat `<img>`)+ `[oklch`=0(用 `oklch(var(--warning))` token)。

### F2 test(同日)
- frontend `kb-settings-tuning.test.tsx`:主 A/B test 加 `expect(screen.getByText('length bias')).toBeInTheDocument()`(`<b>length bias</b>` leaf,唯一,避 nested-text 坑)。
- 驗:**kb-settings-tuning 4 passed**(含新斷言)+ kb-detail + kb-settings-reindex **5 passed**(page.tsx 純加性改動 0 regression)。

### F3 doc-sync(同日)
- architecture.md §5.5.5 加 **W50 amendment**(length-bias affordance:label tooltip + caveat note;static / frontend-only;completeness 對沖留 W51+)
- roadmap:逐期重點 W49 bullet (d) → ✅ W50 shipped(平 part);修訂史加 2026-06-05 W50 entry
- session-start §10 W50 closed row + plan.md status→closed + changelog

### Phase Gate G1-G4 — **PASS**

| # | Criterion | Verdict | Evidence |
|---|---|---|---|
| G1 | config-test panel 有 length-bias explainer affordance | ✅ PASS | 忠實度 label `title` tooltip + A/B grid 下 caveat note(`AlertTriangle` + `<b>length bias</b>`)|
| G2 | 100% match mockup(H7 fidelity)| ✅ PASS | design-first mockup `ekp-page-kb.jsx` 先改 → page.tsx 同文案 + 同 placement(grid 後 / per-citation 前)|
| G3 | tsc/lint/build clean + vitest 0 regression | ✅ PASS | tsc clean + lint(唯一 pre-existing chat `<img>`)+ `[oklch`=0;vitest kb-settings-tuning 4 + kb-detail/reindex 5 passed |
| G4 | frontend-only + 無新 ADR/vendor/backend | ✅ PASS | 純前端;用 result card 現有資料;無新 metric/endpoint/dep;extend ADR-0040 |

**判決:Phase Gate 通過(PASS)**。決策 7 Option (d) 平 part done;用戶試跑時有 length-bias 教育 affordance,避免把 faithfulness 跌誤判為 config 差。

### Retro
- **Karpathy simplicity 守得住**:抵住 scope creep —— 用戶 option 已 scope「先做平 part」,本期 static explainer only(無 arbitrary threshold conditional hint / 無 completeness proxy metric),frontend-only。completeness/recall 對沖明文留 W51+ 評估。
- **落點 design judgment**:tooltip(on-the-spot,per-card 自動)+ 單一 caveat note(A/B 兩卡共用,唔 per-card 重複增噪)組合 — 兩種 discoverability(hover label vs 常駐 caveat)。
- **R6 grep 慳 trial-and-error**:kickoff grep mockup hint 模式(`.hint` / `title=` / IcAlert)→ 直接沿用,無造新 component;page.tsx `AlertTriangle` 已 import 無需加 import。
- **nested-text test 坑(W49 教訓延續)**:caveat span 含 `<b>length bias</b>` → 斷言用 `<b>` leaf `getByText('length bias')`(唯一),避 span/ancestor multiple-match。
- **Watch(carry W51+)**:completeness/recall 對沖指標(Option d ideal 半邊;per_citation distinct-sections band 或 synthetic-QA)= 未做;length-bias static note 係教育非自動偵測,conditional flag 屬後續 refinement。

### Carry-overs → W51+(rolling JIT)
- faithfulness **completeness/recall 對沖指標**(決策 7 Option d ideal 半邊:distinct-sections band / synthetic-QA recall proxy + UI 對沖顯示)
- (前期 carry 不變)per-document scope(決策 1 + AUDIT-E)/ ingestion 質素(reindex→eval)/ AUDIT-D (ii) correctness+context_recall / production v1→v2(Track A 決策 4)/ presets+config 版本史(決策 5)/ Layer C 視覺內容揀圖(Tier 2 決策 3)/ heading_aware footgun

### Commits
- `8830f4a` F0 kickoff + `ad2c93e` F1-F2 code+test + F3 closeout commit(pending)

### Blockers / carry-over
- 無 blocker。infra 已起(azurite 23252 / backend 8000 W49 code / frontend 46364 clean .next)。**注**:本期 frontend-only,frontend dev hot-reload 即時反映,**唔使** restart backend。caveat 只喺有試跑結果時顯示(per-card title tooltip 隨時 hover 可見);未做 live UI screenshot(static note,vitest 已覆蓋 — 如要可手動再跑 config-test)。
