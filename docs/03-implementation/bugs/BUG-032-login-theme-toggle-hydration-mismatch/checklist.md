---
bug_id: BUG-032
report_ref: ./report.md
status: done
last_updated: 2026-06-03
---

# BUG-032 — Checklist

> Atomic checkbox per investigation / fix / regression / verify stages。

## Investigation

- [x] Reproduce locally per `report.md §2`(Playwright full-load `/login` → 11 console errors)
- [x] Identify root cause(`next-themes` resolvedTheme undefined @ SSR → server `<Layers>` vs client `<Sparkles>`)
- [x] Confirm hypothesis with concrete evidence(console `Prop d did not match` server/client SVG path diff → 精確指向 `auth-frame.tsx:221`)
- [x] Update `report.md §3` with confirmed root cause

## Fix

- [x] Implement minimal fix(`auth-frame.tsx` mounted guard — per CLAUDE.md §1.3 surgical)
- [x] 一併修同 pattern `nav/theme-toggle.tsx`(用戶 explicit 要求)
- [x] Cross-reference comment(兩檔互引 + BUG-032)
- [ ] Update affected `components/Cn-*.md`(N/A — 無 design note 改動,純 hydration correctness)

## Regression Test

- [x] Manual repro re-run:`/login` full-load console hydration error **11 → 0**(Playwright)
- [ ] Add automated test(see progress closeout §「Regression Test」— 既有 `visual-baseline.spec.ts` v8-login 覆蓋 visual;hydration-error assertion 未自動化,記為 follow-up)
- [x] Manual smoke test:SSO 登錄修復後仍跳 `/dashboard`(zero regression)

## Verification

- [x] Re-run `report.md §2` repro → console error 0
- [x] Confirm related features still work(SSO 登錄成功 + 視覺零 regression)
- [x] Manual UI verify(截圖 login-after-fix:theme icon mounted 後正確顯示 Sparkles@dark)

## Closeout

- [x] `progress.md` closeout summary(timeline + root cause + lessons)
- [ ] (if Sev1/Sev2)Write `postmortem.md` — N/A(Sev3,skip per §4.5)
- [ ] Update `RISK_REGISTER.md` — pattern 已記入 `report.md §7 Pattern watch`;非新 risk class(hydration 已見於 BUG-023),不另開 register entry
- [x] `report.md` status flipped to `done`
- [x] `progress.md` status flipped to `closed`

---

## Cross-Cutting

- [x] Commit references `progress.md` Day 1 entry(R2)
- [x] Component tag in commit message per CC-1(`fix(frontend): ... (C11, C09)`)
- [ ] ADR — N/A(非 architectural fix,純 hydration correctness,無 H1 trigger)(R5)
- [ ] OQ status sync — N/A(R4)
