---
phase: W23-frontend-test-cleanup
plan_ref: ./plan.md
status: active
last_updated: 2026-05-19
---

# Phase W23 — Checklist

> Atomic checkbox(每 item ≤ 0.5–2 hour effort)。Status:`active` from kickoff 2026-05-19(user directive「先處理 carry-overs 唔好累積債務」+ AI recommendation accepted「先清 W22 fresh debt 再 ship Wave C」 = the authorization)。
> 每 item done 後 `[ ]→[x]` + commit ref;延後項標 🚧 + reason(per CLAUDE.md §10 sacred rule — 唔可以刪未勾選 item)。
> Deliverable ↔ scope mapping:F0 = W23 kickoff governance / F1 = Vitest re-align 4 files / F2 = Playwright re-align + visual baseline / F3 = CLAUDE.md amendment cluster 3 candidates + v1.8→v1.9 / F4 = setup.md `--reload` discipline / F5 = closeout governance。

## F0 — Kickoff cascade

- [x] F0.1 W23 `plan.md`(this directory)+ `checklist.md`(this file)+ `progress.md` created `status: active` 2026-05-19 `(this commit)`
- [x] F0.2 NO `frontend/` code change at kickoff(per W19-W22 F0 precedent — F0 governance only)`(this commit)`
- [x] F0.3 Pre-active-flip 5-step grep audit landed — W22 retro carry-over text vs `frontend/tests/` actual files cross-checked(F1 4 個 file names + F2 3 個 spec files + `visual-baseline.spec.ts-snapshots/` directory 全部 verified exist;no mismatch surfaced)`(this commit)`
- [x] F0.4 W23 kickoff cascade committed `(this commit)`

## F1 — Vitest re-align(4 個 `describe.skip` 重寫)

- [ ] F1.1 `frontend/tests/unit/eval-page.test.tsx` `describe.skip` 解除 + 重寫對齊 W22 F7.1 /eval DOM — top stat-grid 4-metric(R@5/FFul/CRct/IAss labels per backend-wins per W22 D9.d)+ 2-col 1.6fr/1fr below(RerankerShootoutCard + FailedQueriesCard + RecommendationCard + OpsMetricsCard + CragInsightCard)+ page-header 3 actions(Run eval suite / Export / Reranker shootout — **冇** eval-set picker per W22 D7 H7 correction)
- [ ] F1.2 `frontend/tests/unit/kb-detail.test.tsx` `describe.skip` 解除 + 重寫對齊 W22 F6.1 /kb/[id] DOM — 7-tab(Documents / Chunks / Images / Chunking Lab / Pipeline / Retrieval Testing / Settings)+ Access tab DisabledAffordance per CC10 H4 Tier 2 boundary
- [ ] F1.3 `frontend/tests/unit/kb-new-wizard.test.tsx` `describe.skip` 解除 + 重寫對齊 W22 F5.2 /kb/new DOM — 5-step canonical sequence(Identity → Format & chunking → Multimodal → Retrieval defaults → Review;**冇** file picker per W22 D2 H7 mockup-wins;file upload stays at /kb/[id]/upload F6.2 scope)
- [ ] F1.4 `frontend/tests/unit/kb-upload-wizard.test.tsx` `describe.skip` 解除 + 重寫對齊 W22 F6.2 /kb/[id]/upload DOM — 3-step(Data source / Document processing / Execute);drag-drop + file picker dual entry;Step 2 chunking config READ-ONLY per §13 backend-wins
- [ ] F1.5 Vitest stats verify:`pnpm test:unit` post-W23 stats ≥ 30 pass + 0/few skipped(W22 baseline 26 pass + 6 skipped → W23 target IMPROVED)
- [ ] F1.6 `tsc --noEmit` exit 0 + `next lint` clean(test file lints too;W23 不 introduce `any` / non-justified `@ts-ignore`)
- [ ] F1.7 `Grep '\[oklch'` across `frontend/` = 0 preserved(test files 都唔 hardcode oklch)
- [ ] F1.8 Backend 99/99 pytest regression preserved(W23 不 touch backend code;regression check)

## F2 — Playwright re-align + visual baseline re-capture

- [ ] F2.1 `frontend/tests/e2e/app-shell-path.spec.ts` selectors re-align W22 F1 AppShell DOM — WORKSPACE / NAVIGATE / TOOLS / Labs section markers + DesktopSidebar + MobileSidebar selectors per W22 F1.3 + F1.5;breadcrumb selectors per W22 F1.2 `computeBreadcrumbs(pathname)` derive
- [ ] F2.2 `frontend/tests/e2e/golden-path.spec.ts` selectors re-align W22 6 cluster routes DOM — /chat F4 + /kb F5.1 + /kb/new F5.2 + /kb/[id] F6.1 + /kb/[id]/upload F6.2 + /kb/[id]/docs/[docId] F6.3 + /eval F7.1 + /traces F7.2 + /traces/[traceId] F7.3
- [ ] F2.3 `frontend/tests/e2e/visual-baseline.spec.ts` pixel snapshots re-capture for 15 W22 rebuilt routes via `PW_CHANNEL=chrome pnpm test:e2e:update-snapshots`;baseline files committed under `frontend/tests/e2e/visual-baseline.spec.ts-snapshots/`(per W15 CO_W15_F4_baseline_capture pattern;`*-chromium-win32.png` filename suffix)
- [ ] F2.4 `PW_CHANNEL=chrome pnpm test:e2e` end-to-end green run — target ≥ 22/22 pass(W22 baseline 4 pass + 18 fail-now-fixed = 22)
- [ ] F2.5 If pixel diff threshold trigger false positive,`maxDiffPixels` 容差 per route 調整 per R-W23-3 mitigation(threshold 100 → 200-500 acceptable;若 systemic drift → log `🚧` defer W23b+)
- [ ] F2.6 `tsc --noEmit` exit 0 + `next lint` clean(spec files lints too)

## F3 — CLAUDE.md amendment cluster(3 amendments + v1.8 → v1.9)

- [ ] F3.1 **§3.2 CSS-first pivot baseline** amendment landed — add bullet:mockup `styles-mockup.css` 1073→1048 lines verbatim adoption 係 W22 F1 mid-session pivot 嘅 baseline;mockup CSS classes drive visual layer;shadcn primitives 限 Radix a11y benefits(Dialog / DropdownMenu / Sheet / Toast / Tabs);Tailwind utility 限 one-off layout;cite W22 D1 process meta as evidence
- [ ] F3.2 **§10 R5 amendment** — pre-active-flip 5-step formalized 為 **recursive**:applies 唔單只 to code-at-active-flip-time,也 applies to **plan-text itself** at plan kickoff;cite W22 D1(F4 ChatHeader)/ D8(F6 KB cluster)/ D9(F7 observability cluster)3 次 cumulative recursive catch evidence;update R5 wording 加 recursive scope note
- [ ] F3.3 **§13 When-in-Doubt scoping amendment** — backend-wins authority scope 限 **data contract conflicts only**(field shape conflict → backend wins),**NOT** visual element removal(mockup has visual button N backend filter mode 唔 cover → drop button = H7 violation per W22 D6 over-extending precedent);add row 喺 §13 table 區分兩個 sub-scope + cite W22 D6 evidence
- [ ] F3.4 CLAUDE.md version bump v1.8 → **v1.9** + footer entry 描述 W23 F3 3 amendments + W22 anti-pattern catalog 來源(`feedback_design_fidelity.md` D1/D6/D7/D8/D9 cumulative)
- [ ] F3.5 Cross-ref memory `feedback_design_fidelity.md` 入 §10 R5 amendment + §13 amendment text(linkability per memory hygiene + cross-ref convention)
- [ ] F3.6 Grep `CLAUDE.md` 揾相關 cross-ref(no internal contradiction with §1-§13);若 conflict surface → STOP+ask user(per §14 重大 update 需 user explicit approve)
- [ ] F3.7 Amendment landed `(this commit)` w/ commit message `docs(claude-md): v1.9 — W22 anti-pattern catalog → §3.2 CSS-first + §10 R5 recursive + §13 backend-wins scoping (W23 F3)`

## F4 — setup.md `--reload` discipline amendment

- [ ] F4.1 `docs/setup.md` §8(or relevant section per existing structure)加 / 改:standardize `uvicorn backend.api.server:app --reload --reload-dir backend/`(or equivalent invocation per existing setup.md pattern)作為 dev default;production invocation preserve 唔加 `--reload`
- [ ] F4.2 加 troubleshooting subsection「Stale uvicorn PID」:Windows `tasklist /fi "imagename eq python.exe"` / Unix `ps aux | grep uvicorn` detect;Windows `Stop-Process -Id <PID>` / Unix `kill <PID>` safe kill;warn against `--no-verify` git skip(cite CLAUDE.md §4.4 hard rule)
- [ ] F4.3 Cross-ref W22 D8 progress.md retro entry(authority + Langfuse SDK clamp 500→100 evidence + W21 F2 `55f876b` original commit reference)
- [ ] F4.4 Grep `docs/setup.md` 揾 existing backend dev workflow / Azurite / Postgres section — preserve existing structure;amendment 限定 NEW troubleshooting subsection 或者 existing section augment

## F5 — Closeout cascade

- [ ] F5.1 W23 phase Gate verdict landed(PASS / PARTIAL PASS / FAIL with explicit rationale per W18-W22 pattern)
- [ ] F5.2 W23 `progress.md` Retro — 7 sections(What worked / What didn't & friction / Surprises / Decisions / Carry-overs to W23b+ / Time tracking / Spec-ref alignment)
- [ ] F5.3 W23 `plan.md` + `checklist.md` + `progress.md` frontmatter `status: active` → `closed`
- [ ] F5.4 W23b+ phase folder **NOT pre-created** per CLAUDE.md §10 R1 rolling JIT — Wave C SPLIT kickoff candidates noted in retro(C1 ADR-0027 RBAC + C2 ADR-0026 Settings;mock-auth default continues per user 岔口 2)
- [ ] F5.5 `session-start.md` hygiene catch-up — §9 OQ status preserved;§10 W23 closed row + W23b+ candidates row;§11 W23 CLOSED block(F1-F4 cleanup + governance + 3 CLAUDE.md amendments);§12 milestones row 累計 22 closed + Last Updated + Update history
- [ ] F5.6 `references/design-mockups/PAGE_INVENTORY.md` no change(test cleanup doesn't touch page status — 已 W22 F8.9 updated)
- [ ] F5.7 `docs/02-architecture/COMPONENT_CATALOG.md` no change(W23 不 ship feature)

---

## Cross-Cutting(must verify each commit + at closeout)

- [ ] CC1 Each commit references `progress.md` Day-N entry(R2)
- [ ] CC2 Component tag in commit message — F0 = governance / F1 = C09(test layer)/ F2 = C09(E2E layer)/ F3 = governance(CLAUDE.md)/ F4 = C12(docs)/ F5 = governance(closeout)
- [ ] CC3 OQ status sync — **no-op expected**(W23 不 resolve any new OQ;Q1-Q22 status preserved per W22 closeout)
- [ ] CC4 Risk register — R-W23-1 through R-W23-6 logged in plan §4;per-occurrence add to `RISK_REGISTER.md` if hit
- [ ] CC5 CLAUDE.md §5.1 H1 check — W23 是 test cleanup + governance,**NOT** H1 architectural change(component spine / 8-view layout philosophy / vendor lock 全部 preserved)
- [ ] CC6 CLAUDE.md §5.2 H2 check — **no new dependency**(Vitest + Playwright existing stack;`PW_CHANNEL=chrome` 用 system Chrome 非 dep add)
- [ ] CC7 CLAUDE.md §3.2 frontend conventions — `tsc --noEmit` exit 0 + `next lint` clean across `frontend/`(including test files);no `any`;no `@ts-ignore` unless justified comment
- [ ] CC8 CLAUDE.md §3.1 backend conventions — N/A(W23 不 touch backend);backend 99/99 pytest regression preserved at each W23 commit(若有 regression → STOP and investigate as separate W22 bug-fix)
- [ ] CC9 CLAUDE.md §5.5 H5 — no secret committed;no hardcoded tenant/subscription/resource
- [ ] CC10 CLAUDE.md §5.4 H4 — Tier 2 boundary preserved(W23 test re-align consume existing W22 DisabledAffordance for Tier 2 surfaces;不 加 Tier 2 feature)
- [ ] CC11 Karpathy §1.3 surgical — **preserve list** explicit:Vitest + Playwright frameworks + `frontend/tests/setup.ts` + `frontend/tests/__mocks__/` mock pattern + existing API client + W22 rebuilt components;**rebuild list**:4 個 Vitest `describe.skip` files + 3 個 Playwright spec files + visual baselines;**no 順手 refactor** of preserved layers
- [ ] CC12 CLAUDE.md §3.2.1 H7 check — N/A(W23 不 rebuild presentation layer;W22 rebuilt DOM 係 test target 不變);CLAUDE.md §14 §3.2 / §10 R5 / §13 amendment 屬 standing instruction update,不屬 H7

---

**Lifecycle reminder**:呢份 checklist 衍生自 `plan.md` deliverables。新加 deliverable 必須先入 plan + §7 changelog,然後再加 checklist item。延後 item 標 🚧 + reason,**唔可以刪**未勾選 `[ ]`。
