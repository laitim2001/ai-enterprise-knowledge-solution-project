# W50 — Faithfulness Length-Bias Affordance · Checklist

> Atomic items per deliverable。不可刪未勾項(只 `[x]` 或標 🚧 + reason)。
> **F1 frontend = H7 design-first**(mockup 先改再 match);**frontend-only**(無 backend / 無新 metric / 無新 dep)。

## F0 — Phase kickoff
- [ ] F0.1 plan/checklist/progress 三件套 committed(R1);scope(平 part / static / frontend-only)+ key design 鎖定;R6 grep 記 progress

## F1 — Frontend:length-bias explainer affordance(H7 design-first)
- [x] F1.1 mockup `ekp-page-kb.jsx` 先改:faithfulness「忠實度」label 加 length-bias `title=` tooltip + A/B grid 下方單一 caveat note(`IcAlert` + `<b>length bias</b>`);文案 = faithfulness 反幻覺但對長/全面答案 length bias → 低分配高引用/長答案多為 bias 非 config 差 → 對照引用數/字數判讀,勿混 completeness
- [x] F1.2 `page.tsx` `ConfigResultCard` 忠實度 label `title` + A/B grid 後 caveat(`AlertTriangle`)100% match 更新後 mockup(placement grid 後 / per-citation 前)
- [x] F1.3 tsc --noEmit clean + next lint clean(唯一 pre-existing chat `<img>` warning)+ `[oklch`=0 preserved

## F2 — Test + verify
- [x] F2.1 frontend vitest:`kb-settings-tuning` 主 A/B test assert `getByText('length bias')`(`<b>` leaf 唯一,避 nested-text)
- [x] F2.2 既有 kb-settings-tuning 4 passed + kb-detail/kb-settings-reindex 5 passed(0 regression);tsc + lint clean

## F3 — Doc-sync + closeout
- [ ] F3.1 architecture.md §5.5.5 加 W50 amendment(length-bias affordance;static explainer;completeness 對沖留未來)
- [ ] F3.2 roadmap 決策 7 Option (d)「平 part」→ ✅ done(completeness 對沖指標仍 ideal 留 W51+)+ 修訂史 entry
- [ ] F3.3 session-start §10 W50 closed row + W51+ rolling JIT(local-only,gitignored)+ plan.md status→closed + changelog
- [ ] F3.4 Phase Gate G1-G4 = **PASS** + retro + carry-overs(見 progress)+ checklist 全 tick(無 🚧)+ W51+ candidates
