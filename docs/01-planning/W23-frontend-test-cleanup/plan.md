---
phase: W23-frontend-test-cleanup
name: "Frontend Test Cleanup + CLAUDE.md Amendment Cluster + setup.md --reload Discipline — clear W22 PASS WITH CARRY-OVER debt before Wave C kickoff"
sprint_week: W23
start_date: 2026-05-19              # real-calendar — user directive 2026-05-19 「不希望累積債務」 + AI recommendation accepted「先清 W22 fresh debt 再 ship Wave C」
end_date: 2026-05-22                # ~2-3 day window per test cleanup + governance cadence;real-calendar collapse 5-10× pattern applies — actual likely ~1-2 days per W12-W22 trajectory;frontmatter is a window, not a commitment
status: active                      # active from kickoff 2026-05-19;flips to closed at F5 closeout cascade
spec_refs:
  - CLAUDE.md §10 R1-R5             # rolling JIT + plan-before-code (test cleanup is multi-day Phase work needing plan)
  - CLAUDE.md §5.6                  # H6 test coverage constraint (Vitest target re-align)
  - CLAUDE.md §3.2                  # frontend TypeScript / Next.js conventions (Vitest + Playwright belong here)
  - CLAUDE.md §14                   # Update This File (CLAUDE.md amendment cluster authority)
  - architecture.md v6 §5           # UI Tier 1 expansion (W22 rebuilt presentation = test target unchanged)
prior_phase: W22-frontend-presentation-rebuild  # closed 2026-05-18 PASS WITH F8.7+F8.8 TEST-CLEANUP CARRY-OVER
related_artifacts:
  - docs/01-planning/W22-frontend-presentation-rebuild/progress.md  # retro carry-over enumeration + 5 anti-pattern catalogue authoritative
  - docs/01-planning/W22-frontend-presentation-rebuild/checklist.md # F8.7 + F8.8 deferred items source
  - frontend/tests/unit/                                            # Vitest target — 4 complex describe.skip files
  - frontend/tests/e2e/                                             # Playwright target — 3 spec files + visual-baseline snapshots dir
  - CLAUDE.md                                                       # §3.2 / §10 R5 / §13 amendment target
  - docs/setup.md                                                   # --reload discipline amendment target
  - .claude/projects/.../memory/feedback_design_fidelity.md         # 5 anti-pattern catalog (referenced by §10 R5 amendment as evidence)
---

# Phase W23 — Frontend Test Cleanup + Governance Plan

> **Authorization**:User explicit directive 2026-05-19(W22 closeout 後一日):
>
> 「**是否應該先處理 carry-overs 的 items? 我不希望一直在累積債務**」
>
> 「**是的, 可以開始執行 draft W23-frontend-test-cleanup plan**」
>
> AI sequencing recommendation accepted:**先清 W22 fresh debt 再 ship Wave C**。Rationale = W22 closeout PASS WITH CARRY-OVER caveat 連續喺 W21 / W22 兩個 phase 出現,係「正常化 caveat」嘅徵兆;test infrastructure 同 W22 rebuilt DOM 同步 + W22 揭露嘅 3 個 anti-pattern 入 CLAUDE.md standing instructions 之前 ship Wave C,大機會再蹈覆轍。
>
> 呢個係 **fresh debt cleanup + governance pass**,**唔係** H1 / H7 enforcement。Architecture(C01-C13 spine + 28 backend endpoints + W22 rebuilt presentation)全部 preserved unchanged;test files + CLAUDE.md amendments + setup.md amendment 為主。

---

## §0 Phase identity

**Trigger**:W22-frontend-presentation-rebuild closeout(2026-05-18)Gate verdict PASS **WITH** F8.7 + F8.8 TEST-CLEANUP CARRY-OVER:
- F8.7:Vitest 4 個 complex files `describe.skip` deferred(`eval-page.test.tsx` / `kb-detail.test.tsx` / `kb-new-wizard.test.tsx` / `kb-upload-wizard.test.tsx` — W22 DOM rebuild 嗰陣 pre-W22 selectors break)
- F8.8:Playwright 18 fail + 4 pass(same W22 DOM rebuild breakage pattern;pixel snapshot subset updated where renderable)
- 3 個 CLAUDE.md amendment candidates surfaced by W22 retro:§3.2 CSS-first pivot baseline / §10 R5 pre-active-flip recursive / §13 backend-wins authority scoping
- W22 D8 surfaced:backend uvicorn `--reload` discipline 唔 standardized 喺 `docs/setup.md`(stale PID survived through phase,backend regression Langfuse SDK cap clamp 500→100 透過咗 mid-phase 至 D8 先 catch)

**Decision**:用戶 2026-05-19 explicit「不希望累積債務」signal → clear 呢一批 fresh debt 先,然後再 kickoff Wave C SPLIT(W23b / W24+)。

**Scope**:
- F1 Vitest re-align(4 個 complex `describe.skip` 重寫對齊 W22 DOM)
- F2 Playwright re-align(18 fail 重寫對齊 W22 DOM + visual baseline re-capture)
- F3 CLAUDE.md amendment cluster(3 個 candidates landed + version bump v1.8 → v1.9)
- F4 `docs/setup.md` `--reload` discipline amendment(+ stale PID troubleshooting subsection)
- F5 Closeout governance(Gate verdict + retro + session-start sync + W23b+ rolling JIT discipline)

**Out of scope**:
- Wave C feature work(W23b / W23c kickoff post-W23 close;Wave C SPLIT 嘅 C1 ADR-0027 RBAC + C2 ADR-0026 Settings 仍 W19 F4 §3.6 trigger 決定)
- New page rebuilds(W22 closed;preserve list unchanged)
- Backend code changes(test layer adjust 去 consume existing endpoints,無 endpoint signature change)
- New ADR(W23 不 trigger H1/H2/H7;CLAUDE.md amendments 屬 §14 standing instruction update,不寫 ADR)
- W16 F1-F4 Track A IT cred(仍係 parallel external-blocked track)
- CO17 R8 umbrella(F1.5b psycopg / F3.5b RAGAs live-verify — external-blocked,not W23 scope)
- CO_W15_F1 eval-set-v1(需 Chris Q14 SME labels,not W23 scope)

**Authorities**:
- **CLAUDE.md §10 R1-R5** — rolling JIT + plan-before-code(Phase-class work)
- **CLAUDE.md §5.6 H6** — test coverage constraint(Vitest target re-align 屬 H6 scope)
- **CLAUDE.md §3.2** — frontend conventions(Vitest + Playwright 屬 frontend toolchain)
- **CLAUDE.md §14** — Update This File(CLAUDE.md amendment cluster authority;v1.9 bump 需 user explicit approve since `§3.2 / §10 R5 / §13` 屬 H/R 級 hard rule 嘅 wording 改動)

---

## §1 Authorization + spec refs

| F-deliverable | Authorization | Spec ref |
|---|---|---|
| F0 Kickoff | this plan | CLAUDE.md §10 R1 |
| F1 Vitest re-align | W22 retro F8.7 carry-over | CLAUDE.md §5.6 H6 + W22 progress.md Day 8 + W22 checklist F8.7 |
| F2 Playwright re-align | W22 retro F8.8 carry-over | CLAUDE.md §5.6 H6 + W22 progress.md Day 8 + W17 F0b ADR-0017(Plan B `PW_CHANNEL=chrome`)+ W15 CO_W15_F4_baseline_capture pattern |
| F3 CLAUDE.md amendment cluster | W22 D1+D6+D7+D8+D9 5 anti-pattern catalog + W22 retro 3 surfaced candidates | CLAUDE.md §14 standing instruction update + memory `feedback_design_fidelity.md` 5-pattern summary table |
| F4 setup.md `--reload` discipline | W22 D8 backend regression discovery rationale | `docs/setup.md` §8 troubleshooting / backend dev workflow section |
| F5 Closeout | CLAUDE.md §10 R3(changelog)+ R5(no ADR — W23 不 trigger H1/H2)+ W22 F8 closeout pattern | this plan §3 Gate criteria |

---

## §2 F0-F5 deliverables

**Rolling JIT discipline**:F0 + F1 detailed kickoff time;F2-F5 sketched;detail refines per-deliverable at kickoff time per W12-W22 pattern。

### F0 — Kickoff cascade(landed at phase open — `(this commit)`)

- **Component(s)**:governance(no Cn touched)
- **Spec ref**:CLAUDE.md §10 R1 + this plan §0
- **OQ deps**:none
- **Acceptance criteria**:
  - F0.1 W23 `plan.md`(this file)+ `checklist.md` + `progress.md` created `status: active` 2026-05-19
  - F0.2 NO `frontend/` code change at kickoff(per W19-W22 F0 precedent — F0 governance only)
  - F0.3 Pre-active-flip 5-step grep audit landed:W22 retro carry-over text vs `frontend/tests/` actual files cross-checked(F1 4 file names + F2 3 spec files + visual-baseline snapshots dir 全部 verified exist;no mismatch surfaced)
  - F0.4 W23 kickoff cascade committed `(this commit)`
- **Effort estimate**:0.25 day(this commit)

### F1 — Vitest re-align(4 個 `describe.skip` 重寫對齊 W22 DOM)

- **Component(s)**:**C09** Admin Console UI(test layer)
- **Spec ref**:
  - W22 F8.7 4 個 deferred files(per W22 checklist.md F8.7 + W22 progress.md Day 8):
    - `frontend/tests/unit/eval-page.test.tsx`(W22 F7.1 /eval rebuild 後 selectors break)
    - `frontend/tests/unit/kb-detail.test.tsx`(W22 F6.1 7-tab rebuild 後 selectors break)
    - `frontend/tests/unit/kb-new-wizard.test.tsx`(W22 F5.2 5-step rebuild 後 selectors break)
    - `frontend/tests/unit/kb-upload-wizard.test.tsx`(W22 F6.2 3-step rebuild 後 selectors break)
- **OQ deps**:none
- **Acceptance criteria**:
  - F1.1 `eval-page.test.tsx` `describe.skip` 解除 + 重寫對齊 W22 F7.1 /eval DOM — top stat-grid 4-metric(R@5/FFul/CRct/IAss labels per backend-wins per W22 D9.d)+ 2-col 1.6fr/1fr below(RerankerShootoutCard + FailedQueriesCard + RecommendationCard + OpsMetricsCard + CragInsightCard)+ page-header 3 actions(Run eval suite / Export / Reranker shootout — **冇** eval-set picker per W22 D7 H7 correction)
  - F1.2 `kb-detail.test.tsx` `describe.skip` 解除 + 重寫對齊 W22 F6.1 /kb/[id] DOM — 7-tab(Documents / Chunks / Images / Chunking Lab / Pipeline / Retrieval Testing / Settings)+ Access tab DisabledAffordance per CC10 H4 Tier 2 boundary
  - F1.3 `kb-new-wizard.test.tsx` `describe.skip` 解除 + 重寫對齊 W22 F5.2 /kb/new DOM — 5-step canonical sequence(Identity → Format & chunking → Multimodal → Retrieval defaults → Review;**冇** file picker per W22 D2 H7 mockup-wins;file upload stays at /kb/[id]/upload F6.2 scope)
  - F1.4 `kb-upload-wizard.test.tsx` `describe.skip` 解除 + 重寫對齊 W22 F6.2 /kb/[id]/upload DOM — 3-step(Data source / Document processing / Execute);drag-drop + file picker dual entry point;Step 2 chunking config READ-ONLY per §13 backend-wins
  - F1.5 Vitest stats verify:`pnpm test:unit` post-W23 stats ≥ 30 pass + 0/few skipped(W22 baseline 26 pass + 6 skipped → W23 target IMPROVED;若 1-2 files 真係 unrecoverable 入 PARTIAL PASS rationale)
  - F1.6 `tsc --noEmit` exit 0 + `next lint` clean(test files lints too;W23 不 introduce `any` / non-justified `@ts-ignore`)
  - F1.7 `Grep '\[oklch'` across `frontend/` = 0 preserved(test files 都唔 hardcode oklch — render-smoke 只 check structure 唔 check pixel)
  - F1.8 Backend 99/99 pytest regression preserved(W23 不 touch backend code;regression check only,若 fail 即係 揭露 W22 silent integration drift → STOP)
- **Effort estimate**:1 day(~4-6 hours)

### F2 — Playwright re-align(18 fail + visual baseline re-capture)

- **Component(s)**:**C09** Admin Console UI(E2E test layer)
- **Spec ref**:
  - W22 F8.8 18 fail breakdown(per W22 progress.md Day 8):
    - `app-shell-path.spec.ts` — TopBar / Sidebar / breadcrumb selectors changed(W22 F1.2 + F1.3 rebuild;WORKSPACE / NAVIGATE / TOOLS / Labs section)
    - `golden-path.spec.ts` — /chat + /kb + /kb/[id] + /kb/[id]/upload + /eval + /traces workflow selectors changed(W22 F4 + F5 + F6 + F7 rebuild)
    - `visual-baseline.spec.ts` — 15 page pixel snapshots 全部 stale(W22 rebuilt 15 routes;snapshots dir `visual-baseline.spec.ts-snapshots/` 需要 re-capture)
  - W17 F0b ADR-0017 Plan B(`PW_CHANNEL=chrome` system Chrome — corp-managed,避開 `npx playwright install chromium` R8 block)
  - W15 D5 CO_W15_F4_baseline_capture(W15 4 baselines first-capture pattern,2026-05-13 via Plan B)
- **OQ deps**:none
- **Acceptance criteria**:
  - F2.1 `app-shell-path.spec.ts` selectors re-align W22 AppShell DOM — WORKSPACE / NAVIGATE / TOOLS / Labs section markers + DesktopSidebar + MobileSidebar selectors per W22 F1.3 + F1.5;breadcrumb selectors re-aligned per W22 F1.2 `computeBreadcrumbs(pathname)` derive pattern
  - F2.2 `golden-path.spec.ts` selectors re-align W22 W22 6 cluster routes DOM — /chat(F4 inline single-file decomposition)+ /kb(F5.1 grid+table+filter)+ /kb/new(F5.2 5-step)+ /kb/[id](F6.1 7-tab)+ /kb/[id]/upload(F6.2 3-step)+ /kb/[id]/docs/[docId](F6.3 3-pane NEW)+ /eval(F7.1)+ /traces(F7.2 9-col table 4-button seg)+ /traces/[traceId](F7.3 5-stat + 3 viz modes)
  - F2.3 `visual-baseline.spec.ts` pixel snapshots re-capture for 15 W22 rebuilt routes via `PW_CHANNEL=chrome pnpm test:e2e:update-snapshots`;baseline files committed under `frontend/tests/e2e/visual-baseline.spec.ts-snapshots/`(per W15 CO_W15_F4_baseline_capture pattern;`*-chromium-win32.png` filename suffix)
  - F2.4 `PW_CHANNEL=chrome pnpm test:e2e` end-to-end green run — target ≥ 22/22 pass(W22 baseline 4 pass + 18 fail-now-fixed = 22;若有 PARTIAL PASS 入 retro rationale)
  - F2.5 If pixel diff threshold trigger false positive(rebuild typography 對 oklch token resolve 出微小 color drift),`maxDiffPixels` 容差 per route 調整 per R-W23-3 mitigation(threshold 100 → 200-500 acceptable;若 systemic drift → log `🚧` defer W23b+ with explicit reason)
  - F2.6 `tsc --noEmit` exit 0 + `next lint` clean(spec files lints too)
- **Effort estimate**:1 day(~4-6 hours)

### F3 — CLAUDE.md amendment cluster(3 amendments + version bump v1.8 → v1.9)

- **Component(s)**:governance(CLAUDE.md standing instructions)
- **Spec ref**:W22 retro 3 surfaced amendment candidates + W22 D1/D6/D7/D8/D9 5 anti-pattern catalog memory + CLAUDE.md §14 Update This File
- **OQ deps**:none
- **Acceptance criteria**:
  - F3.1 **§3.2 CSS-first pivot baseline amendment** — add bullet:mockup `styles-mockup.css` 1073→1048 lines verbatim adoption 係 W22 F1 mid-session pivot 嘅 baseline;mockup CSS classes drive visual layer;shadcn primitives 限 Radix a11y benefits(Dialog / DropdownMenu / Sheet / Toast / Tabs);Tailwind utility 限 one-off layout;原本「shadcn primitives + Tailwind tokens only」表述 under-represent 實際做法;cite W22 D1 process meta as evidence
  - F3.2 **§10 R5 amendment** — pre-active-flip grep verification 5-step formalized 為 **recursive**:applies 唔單只 to code-at-active-flip-time,也 applies to **plan-text itself** at plan kickoff;cite W22 D1(F4 ChatHeader 7 signals)/ D8(F6 KB cluster 5 signals)/ D9(F7 observability cluster 9 signals)3 次 cumulative recursive catch evidence;update R5 wording 加 recursive scope note + cross-ref memory `feedback_design_fidelity.md`
  - F3.3 **§13 When-in-Doubt scoping amendment** — backend-wins authority scope 限 **data contract conflicts only**(mockup expects field X that backend schema doesn't return → backend wins on field shape),**NOT** visual element removal(mockup has visual button N that backend filter mode 唔 cover → drop button = H7 violation per W22 D6 over-extending precedent);add row 喺 §13 table 區分兩個 sub-scope + cite W22 D6 evidence
  - F3.4 CLAUDE.md version bump v1.8 → **v1.9** + footer entry 描述 W23 F3 3 amendments + W22 anti-pattern catalog 來源(`feedback_design_fidelity.md` D1/D6/D7/D8/D9 cumulative)
  - F3.5 Cross-ref memory `feedback_design_fidelity.md` 入 §10 R5 amendment + §13 amendment text(linkability per memory hygiene convention)
  - F3.6 Grep `CLAUDE.md` 揾相關 cross-ref(no internal contradiction with §1-§13;e.g. §13 amendment 唔 conflict §4 authority ordering / §5.1 H1);若 conflict surface STOP+ask user(per §14「重大 update 需 user explicit approve」)
  - F3.7 Amendment landed `(this commit)` w/ commit message `docs(claude-md): v1.9 — W22 anti-pattern catalog → §3.2 CSS-first + §10 R5 recursive + §13 backend-wins scoping (W23 F3)`
- **Effort estimate**:0.5 day(~2-3 hours)

### F4 — setup.md `--reload` discipline amendment

- **Component(s)**:**C12** DevOps & Infra(documentation)
- **Spec ref**:W22 D8 progress.md retro entry — backend regression(Langfuse SDK cap clamp 500→100)透過 stale uvicorn PID 37036(2026-05-16 started,無 `--reload`)survived through W22 phase;new PID 2092 via `.venv/Scripts/python.exe -m uvicorn` 都冇 `--reload`;`docs/setup.md` 唔有 standardized backend dev workflow troubleshooting
- **OQ deps**:none
- **Acceptance criteria**:
  - F4.1 `docs/setup.md` §8(or relevant section per existing structure)加 / 改 backend dev workflow note:standardize `uvicorn backend.api.server:app --reload --reload-dir backend/`(or equivalent invocation per existing setup.md pattern)作為 dev default;production invocation(ACA / gunicorn / whatever)preserve 唔加 `--reload`
  - F4.2 加 troubleshooting subsection「Stale uvicorn PID」:Windows `tasklist /fi "imagename eq python.exe"` / Unix `ps aux | grep uvicorn` detect;Windows `Stop-Process -Id <PID>` / Unix `kill <PID>` safe kill;warn against `--no-verify` git skip(cite CLAUDE.md §4.4 hard rule)
  - F4.3 Cross-ref W22 D8 progress.md retro entry(authority + Langfuse SDK clamp 500→100 evidence + W21 F2 `55f876b` commit reference where clamp originally introduced)
  - F4.4 Grep `docs/setup.md` 揾 existing backend dev workflow / Azurite / Postgres section — preserve existing structure;amendment 限定 NEW troubleshooting subsection 或者 existing section augment(不 rewrite 既有 section)
- **Effort estimate**:0.25 day(~1 hour)

### F5 — Closeout cascade

- **Component(s)**:governance
- **Spec ref**:CLAUDE.md §10 R3(changelog)+ R5(no ADR — W23 不 trigger H1/H2)+ W22 F8 closeout pattern
- **OQ deps**:none
- **Acceptance criteria**:
  - F5.1 W23 phase Gate verdict landed(PASS / PARTIAL PASS / FAIL with explicit rationale per W18-W22 pattern)
  - F5.2 W23 `progress.md` Retro — 7 sections(What worked / What didn't & friction / Surprises / Decisions / Carry-overs to W23b+ / Time tracking / Spec-ref alignment)
  - F5.3 W23 `plan.md` + `checklist.md` + `progress.md` frontmatter `status: active` → `closed`
  - F5.4 W23b+ phase folder **NOT pre-created** per CLAUDE.md §10 R1 rolling JIT — Wave C SPLIT kickoff candidates noted in retro(C1 ADR-0027 RBAC + C2 ADR-0026 Settings;mock-auth default continues per user 岔口 2)
  - F5.5 `session-start.md` hygiene catch-up — §9 OQ status preserved(no new OQ resolved by W23);§10 W23 closed row + W23b+ candidates row;§11 W23 CLOSED block(F1-F4 cleanup + governance + 3 CLAUDE.md amendments);§12 milestones row 累計 22 closed + Last Updated + Update history
  - F5.6 `references/design-mockups/PAGE_INVENTORY.md` no change(test cleanup doesn't touch page status — 已 W22 F8.9 updated)
  - F5.7 `docs/02-architecture/COMPONENT_CATALOG.md` no change(W23 不 ship feature)
- **Effort estimate**:0.5 day(~2-3 hours)

---

## §3 Success Criteria + Gate verdict

**Phase Gate = PASS** requires:
1. F0-F5 all `[ ]` items in checklist.md flipped `[x]`(或 `🚧` with explicit deferral reason per CLAUDE.md §10 sacred rule)
2. `pnpm test:unit` Vitest green end-to-end(F1.5 stats target ≥ 30 pass + 0/few skipped;all 4 W22-deferred files re-aligned)
3. `PW_CHANNEL=chrome pnpm test:e2e` Playwright green end-to-end(F2.4 target ≥ 22/22 pass)
4. `tsc --noEmit` exit 0 across `frontend/`(including test files)
5. `next lint` clean(No ESLint warnings or errors)including test files
6. `Grep '\[oklch'` across `frontend/` = 0(milestone preserved through W23 test re-align)
7. **CLAUDE.md v1.9 landed** with 3 amendments(§3.2 / §10 R5 / §13)+ version bump + footer entry
8. **`docs/setup.md` `--reload` discipline** standardized + stale PID troubleshooting subsection
9. **Backend 99/99 pytest regression** preserved(W23 不 touch backend code;regression check only)
10. **Pixel baselines** for 15 W22 rebuilt routes captured + committed under `visual-baseline.spec.ts-snapshots/`

**PARTIAL PASS** allowance:
- 1-2 個 test files 重 align 過程 hit unexpected mock conflict / fixture path drift → STOP+ask + defer 該 file with explicit `🚧` reason 入 checklist + retro
- Pixel baseline 系統性 drift(`maxDiffPixels` threshold 提高 > 500 仍 false positive)→ log `🚧` per-route 入 retro,defer dark-mode token resolve 到 W23b+
- CLAUDE.md amendment 嘅 3 條 中 1 條 wording 觸發 user-explicit-approve 異議 → 該條 defer 重 propose,另外 2 條照 land

**FAIL** triggers:
- Test re-align introduces backend regression(99/99 pytest 退 — W23 不 touch backend,如果 regression 即係 test layer 揭露 W22 silent integration drift,STOP and investigate root cause as separate bug-fix workflow per PROCESS.md §4)
- CLAUDE.md amendment introduces internal contradiction with existing §1-§13 standing instructions(per §14 grep check)
- 整個 Playwright suite 仍 < 50% pass rate post-F2(systemic re-align failure,非單 file issue)

---

## §4 Risks

| R# | Risk | Likelihood | Impact | Mitigation |
|---|---|---|---|---|
| **R-W23-1** | 4 個 Vitest files `describe.skip` 重寫 出 mock setup conflict / fixture path drift | Medium | Low | Per file kickoff:grep `frontend/tests/setup.ts` + `frontend/tests/__mocks__/`(若有)確認 mock pattern;若 drift `STOP+log + ask`;先 fix 1 file 揭露 pattern 再 batch apply |
| **R-W23-2** | Playwright `PW_CHANNEL=chrome` system Chrome version drift(corp-managed update 可能 break selector 或者 rendering) | Low | Medium | Per W17 ADR-0017 Plan B (a) precedent:若 break,fallback 試 `pnpm test:e2e` 唔加 channel 用 bundled Chromium(`npx playwright install chromium` 仍 R8-blocked,但 local cache 或 prior install 可能仍 viable);若 all blocked,STOP+ask user smoke + defer F2.4 |
| **R-W23-3** | Pixel baseline first-capture diff threshold 過嚴(W22 rebuild typography 對 oklch token resolve 出微小 color drift) | Medium | Low | Playwright `expect(page).toHaveScreenshot({ maxDiffPixels: 100 })` 容差 per existing baseline;若 false positive 多 → 提高 threshold 至 200-500;若 systemic drift → log per-route `🚧` defer 到 W23b+ dark-mode token resolve session |
| **R-W23-4** | CLAUDE.md amendment 嘅 §3.2 / §10 R5 / §13 wording 同 existing standing instructions 衝突 / overlap | Low | Medium | F3.6 acceptance criteria 要求 amendment landing 之前 grep `CLAUDE.md` 揾相關 cross-ref;若 conflict surface STOP+ask user decision(per §14 重大 update 需 user explicit approve) |
| **R-W23-5** | setup.md `--reload` discipline 反過來 break 既有用戶 workflow(e.g. 用戶 prefer no-reload 為咗 reproduce timing-sensitive bug 或 production-shape backend) | Low | Low | F4 amendment 以「dev default」框定,**唔係** mandatory(`docs/setup.md` 唔係 hard constraint level;production / debug / advanced use case 仍可 opt-out);若用戶反饋 → revert + add advanced opt-out section |
| **R-W23-6** | Test re-align 揭露 W22 rebuild 嗰陣 silent backend integration drift(e.g. API client method signature 同 component consume 唔對齊) | Medium | High | F1 + F2 acceptance criteria 包含 `tsc` + backend pytest regression gate;若 揭露 → STOP and investigate;treat as W22 regression(separate W22 bug-fix workflow per PROCESS.md §4)not W23 scope creep |

---

## §5 Dependencies / OQ deps

- **No new OQ**(Q1-Q22 status preserved per W22 closeout)
- **No new ADR**(W23 不 trigger H1/H2/H7;CLAUDE.md amendments 屬 §14 standing instruction update,不寫 ADR per CLAUDE.md §14 wording「重大 update(改 H1–H6 或 §1 Behavioral Baseline)需要 user explicit approve」— §3.2 / §10 R5 / §13 amendments 屬 wording 細化 / scope clarification 而非新增 H 級 hard rule)
- **No new dependency**(per CC6 H2 — Vitest + Playwright existing stack;`PW_CHANNEL=chrome` 用 system Chrome 非 dependency add)
- **No new R8 occurrence expected**(no new package install — `pnpm test:unit` + `pnpm test:e2e` 用 existing `node_modules/`)
- **Existing W23 dev workflow**:
  - Vitest:`pnpm test:unit`(local + CI same invocation)
  - Playwright:`PW_CHANNEL=chrome pnpm test:e2e`(per W17 ADR-0017 Plan B (a))
  - Visual baseline re-capture:`PW_CHANNEL=chrome pnpm test:e2e:update-snapshots`(per W15 CO_W15_F4_baseline_capture pattern)
  - Backend regression gate:`cd backend && pytest`(local;CI 用同樣 invocation)
  - Frontend dev server:`pnpm dev`(`localhost:3001`)— F1 + F2 需要 running 以便 Vitest jsdom render + Playwright fetch route

---

## §6 Carry-overs from W22 closeout

W22 progress.md retro Day 8 §5 Carry-overs to W23+(per W22 retro authoritative):
- F8.7 Vitest 4 個 files `describe.skip` defer → **W23 F1**
- F8.8 Playwright 18 fail + visual baseline re-capture → **W23 F2**
- 3 個 CLAUDE.md amendment candidates surfaced(§3.2 CSS-first / §10 R5 recursive / §13 backend-wins scoping)→ **W23 F3**
- Backend uvicorn `--reload` discipline 唔 standardized → **W23 F4**

W22 + earlier carry-overs that remain parallel(NOT W23 scope):
- **CO16 / Track A IT cred consumption** → W16 F1-F4 仍 Track-A-blocked;parallel track,W23 唔 touch
- **CO17 R8 umbrella** → F1.5b psycopg / F3.5b RAGAs live-verify(external-blocked,not W23 scope)
- **CO_W15_F1_eval_set_v1** → still OPEN(需 Q14 SME labels;not W23 scope)
- **CO_W15_F3_dark_mode_visual_verify** → W22 pixel baselines re-capture by W23 F2.3 部分 cover dark-mode token verification per page;remaining interactive multi-viewport walkthrough 仍 user pre-Beta smoke
- **CO_W15_F4_interactive_flow_E2E** → user pre-Beta smoke;not W23 blocker
- **W22 D1+D6+D7+D8+D9 5 個 anti-pattern catalog**(memory `feedback_design_fidelity.md`)→ W23 F3 amendments cite 為 evidence + cross-ref;memory file 本身 preserved unchanged
- **Wave C SPLIT kickoff(C1 ADR-0027 + C2 ADR-0026)**→ W23b+ post-W23 close decision
- **R12** Azurite SDK signature mismatch → permanent fix 等 W16+ cloud Azure Blob;not W23 scope
- **R-B1** Beta deploy launch readiness blocker → W16 F1 deliverable;not W23 scope

---

## §7 Changelog

| Date | Author | Change |
|---|---|---|
| **2026-05-19 D0** | AI per Chris directive | **W23 phase kickoff cascade landed** — `plan.md`(this file)+ `checklist.md` + `progress.md` created `status: active`;authorization = user explicit directive 2026-05-19「**是否應該先處理 carry-overs 的 items? 我不希望一直在累積債務**」+「**是的, 可以開始執行 draft W23-frontend-test-cleanup plan**」;AI sequencing recommendation accepted「先清 W22 fresh debt 再 ship Wave C」;per CLAUDE.md §10 R1 rolling JIT(W23 folder 喺 kickoff 時建,W23b+ Wave C SPLIT post-W23-close 先 kickoff);no `frontend/` code change at kickoff(F0 governance only per W19-W22 F0 precedent);F1-F5 detailed per §2 with rolling-JIT detail-refine cadence。**Pre-active-flip 5-step recursive 11th cumulative application**(CO_W14_process_grep_verify formalized W17 D0 + W22 D1/D8/D9 recursive 3 applications + W23 D0 plan-vs-W22-retro-text grep verify — no major mismatch surfaced;W22 retro carry-over enumeration matches W23 F1-F4 scope 1:1;`frontend/tests/unit/` 4 files + `frontend/tests/e2e/` 3 spec files 全部 verified exist before plan landing)。 |

---

**Plan ready for F1 kickoff.** F0 cascade landed at this commit;F1 Vitest re-align starts next session(或 continuation per user direction)。每 F-deliverable kickoff time refine acceptance criteria + grep existing mock pattern / fixture path / W22 DOM selector before re-align。

**Per-deliverable workflow standard**:
1. Read F-deliverable acceptance criteria + W22 retro 對應 carry-over text + W22 plan/checklist 對應 section
2. Grep target file existing state(test file's previous `describe.skip` block / CLAUDE.md target section / setup.md target section)
3. Identify mock / fixture / selector / wording mismatches upfront(per CLAUDE.md §10 R5 recursive 5-step)
4. Surface ambiguities via Karpathy §1.1 think-before-coding 之前 implement
5. Implement re-align / amendment
6. Verify gate per F-deliverable:`tsc` + `lint` + `pnpm test:unit`(F1)/ `PW_CHANNEL=chrome pnpm test:e2e`(F2)/ grep verify(F3 / F4)
7. Commit with Day-N entry
8. Day-N entry 入 progress.md(per CLAUDE.md §10 R2)
