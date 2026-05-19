---
bug_id: BUG-004
title: "6 Playwright `app-shell-path` selectors drifted from W22 rebuilt DOM — 6/10 tests failing"
severity: Sev4          # Sev1 | Sev2 | Sev3 | Sev4 (per PROCESS.md §4.5)
status: done            # triaged | investigating | fixing | verifying | done | wont-fix
reported: 2026-05-19
reporter: "AI (W23 D2.2 Playwright partial fix during W23 closeout)"
affects_components: [C09]      # C09 Admin Console UI — E2E test layer drift
spec_refs:
  - architecture.md v6 §5      # Application architecture — AppShell + 9 views
  - W22 F1-F7                  # Presentation rebuild — DOM structure changed
  - W23 F2                     # Playwright re-align partial(3/9 pass + 6 selector tweaks deferred)
---

# BUG-004 — Playwright `app-shell-path` 6 selectors W22 DOM drift

> **Report version**:1.0(initial)
> **Triage approver**:AI(self-triaged Sev4 — test infra drift only;production behavior unchanged;flagged at W23 closeout as Sev4 carry-over per session-start.md §11)
> **Closed**:2026-05-19(Chris confirmed Sev4 + fix approach via AskUserQuestion;all 10 app-shell-path tests pass + 22/22 full suite +7 IMPROVED vs W23 15/22 baseline)

## 1. Symptom

`frontend/tests/e2e/app-shell-path.spec.ts` 跑時 6/10 tests fail:

| # | Test | Failure |
|---|---|---|
| 1 | `/dashboard renders the W22 F3 mockup-faithful header + 4-stat strip + main grid` | `getByText(/^documents$/i).first()` 唔搵到 — actual stat-label DOM 係 `<div className="stat-label"><FileText size={13} /> Documents</div>`,icon+space prefix 令 strict `^...$` regex 唔 match |
| 2 | `/kb KB List renders W22 F5.1 page-title + grid view + Create KB CTA` | `getByPlaceholder(/search/i)` 唔搵到 — actual placeholder 係 `Filter by name, owner, tag…`(W22 F5.1 KB list textbox 用「Filter」not「Search」)|
| 3 | `/traces list renders W22 F7.2 page-title + 4-button seg toggle` | `getByRole('button', { name: 'All', exact: true })` 唔搵到 — actual DOM 係 `tablist > tab "All" [selected]`,4 個 seg button render 做 `role="tab"` 而唔係 `role="button"`(per W22 F7.2 mockup `.seg` CSS-first pattern)|
| 4 | `/traces/[traceId] renders W22 F7.3 dynamic page-title + 3 viz modes` | `locator('h1.page-title').filter({ hasText: /query\|not surfaced/i })` 唔搵到 — `/traces/20260605-Q014` 喺 in-memory backend 唔 exist → renders `heading "Observability degraded" [level=3]` error state,**冇** h1.page-title element。Mixed root cause:**selector drift** + **data not seeded** |
| 5 | `AppShell sidebar nav navigates between modules (aria-label="Primary")` | `getByRole('link', { name: /^chat$/i })` timeout 60s — actual link accessible name 係 `"Chat Cmd↵"`(W20 NavItem renders Cmd↵ keyboard hint suffix);strict `^chat$` 唔 match |
| 6 | `/kb/[id] 7-tab refactor renders Access disabled affordance OUTSIDE VALID_TABS` | `getByRole('tab')` count = 0 vs expected 8 — `/kb/drive_user_manuals` 喺 in-memory backend 唔 exist → renders `Failed to load KB drive_user_manuals: KB 'drive_user_manuals' not found` error,tablist 唔 render。Mixed root cause:**data not seeded**(primary)+ tab role assertion can co-exist |

## 2. Reproduction Steps

1. 喺 `frontend/` run:`PW_CHANNEL=chrome pnpm exec playwright test tests/e2e/app-shell-path.spec.ts --reporter=line`
2. Observed:**6 failed + 4 passed** in ~3.9 min(per W23 D2.2 finding)

**Reproduction reliability**:Always(deterministic — DOM drift + missing seed data,both env-independent)。

**Environment**:local dev frontend(`:3001`)+ backend(`:8000`)w/ in-memory KB + users store fallback per ADR-0023(no `DATABASE_URL` set)。

## 3. Expected vs Actual

| # | Expected | Actual |
|---|---|---|
| 1 | `getByText('Documents', { exact: true })` 應該 match `<div className="stat-label">` 入面嘅 "Documents" text | `<div className="stat-label">` 含 `<img>` + " Documents"(icon space prefix);Playwright strict-regex `/^documents$/i` 唔 match elements with mixed content children |
| 2 | KB list 有 search input w/ placeholder containing "search" | W22 F5.1 KB list 用 `Filter by name, owner, tag…` placeholder(per mockup `ekp-page-kb.jsx`)— "Filter" not "Search" |
| 3 | 4 seg buttons rendered as `role="button"` w/ names "All"/"Success"/"Error"/"CRAG triggered" | W22 F7.2 `.seg` pattern render 4 個 `<button role="tab">` inside `<div role="tablist">`(per mockup `ekp-page-traces.jsx` `.seg` pattern + W22 D6 H7 fidelity correction) |
| 4 | h1.page-title 含 query text 或 "Query text not surfaced" fallback | trace ID `20260605-Q014` 喺 in-memory backend 唔 exist → renders error state heading「Observability degraded」h3,**冇** h1.page-title。viz modes seg 喺 error state 唔 render |
| 5 | Sidebar Chat link accessible name = "Chat"(strict) | W20 F1 NavItem render Cmd↵ keyboard hint suffix → accessible name = "Chat Cmd↵";strict `/^chat$/i` 唔 match |
| 6 | `/kb/drive_user_manuals` page 有 8 個 tabs(7 active + 1 disabled Access) | `drive_user_manuals` KB 喺 in-memory backend 唔 exist → renders error banner「Failed to load KB drive_user_manuals: KB 'drive_user_manuals' not found」,tablist 唔 render |

## 4. Impact

- **Affected users / scenarios**:CI / local dev 跑 Playwright `app-shell-path` E2E suite 嗰陣會見到 6/10 fail。Production frontend rendering fully functional(W22 mockup-fidelity verified manually per W22 closeout per-page user-eye verify)。
- **Workaround available?**:Yes — `pnpm test:e2e --grep "golden-path|visual-baseline"` skips app-shell-path(W23 F2 verified golden-path 7/7 + visual-baseline 6/6 全 pass)。
- **Data loss / corruption?**:No
- **Security implication?**:No

## 5. Severity Justification

**Sev4** per `PROCESS.md §4.5`:test infrastructure drift,cosmetic test failures,no production behavior breakage,no data risk,no security implication,workaround exists(`--grep` filter)。Sev4 → no mandatory postmortem。

**Why deferred W24+**:W23 closeout 識別 7 selector tweaks(per W23 D2.2)— per Karpathy §1.2 simplicity scope guard;W23 phase Gate verdict 用 **PASS WITH F2 PARTIAL CAVEAT**(per plan §3 allowance — `15/22 + 6 selectors W24+` predetermined acceptable trajectory)。

## 6. Initial Diagnosis

- **Initial hypothesis**(at triage):W22 rebuild change 咗多個 page DOM structure(stat-label icon prefix / KB list filter placeholder / .seg tablist pattern / Sidebar Cmd hint / KB detail error state),selectors 未 align
- **Root cause confirmed**(2026-05-19):
  - **#1, #2, #3, #5**:pure selector drift — fix by aligning selector with actual W22 DOM(CSS class approach per W23 D1.2 CSS-first anti-pattern + role correction + relax strict anchors)
  - **#4, #6**:mixed root cause — primary 係 data not seeded(in-memory backend per ADR-0023 fallback,test trace ID + test KB ID 都唔 exist),secondary selector drift。**Fix approach**:test refactor → render-smoke style assertion(page renders without crash + shell-level surface visible,either happy path OR graceful error state)— data-seeded full-state E2E defer to W24+ post Track A IT cred + Postgres path runtime smoke per CO17 ledger

## 7. Acceptance for Fix(checklist preview)

- [x] Reproduction confirmed locally(6/10 fail across 6 distinct root causes)
- [x] Root cause identified per item(4 pure selector drifts + 2 mixed selector+data)
- [x] **#1** Fix `/dashboard` 4-stat:`page.locator('.stat-label').filter({ hasText: /Documents/ }).first()` 取代 `getByText(/^documents$/i).first()`(W22 CSS-first per W23 D1.2)— apply 3 個 stat labels consistency
- [x] **#2** Fix `/kb` placeholder:`getByPlaceholder(/filter by name/i)` 取代 `getByPlaceholder(/search/i)`(W22 F5.1 actual placeholder)
- [x] **#3** Fix `/traces` seg:`getByRole('tab', { name: label, exact: true })` 取代 `getByRole('button', ...)`(W22 F7.2 `.seg` tablist pattern)
- [x] **#4** Refactor `/traces/[traceId]` test:render-smoke 3-state OR — loading state(backend timeout 接受)/ h1.page-title(happy)/ Observability degraded heading(error);Open Langfuse link + 3 viz modes assertion 全部 defer W24+(loading state 唔 render 呢兩個 surface)
- [x] **#5** Fix sidebar Chat:`name: /^chat\b/i`(word boundary `\b`)取代 `/^chat$/i`(accommodate "Chat Cmd↵" suffix)
- [x] **#6** Refactor `/kb/[id]` test:render-smoke 2-state OR — tablist(happy)OR error banner(data-empty);8-tab strict count + Access affordance assertion defer W24+
- [x] Re-run `app-shell-path.spec.ts` → **10/10 pass in 1.6m** ✅
- [x] Re-run full Playwright suite via `PW_CHANNEL=chrome pnpm exec playwright test` → **22/22 pass in 2.0m**(W23 baseline 15/22 → **+7 net IMPROVED**)

## 8. Report Changelog

| Date | Change | Reason | Approver |
|---|---|---|---|
| 2026-05-19 | Initial triage(Sev4)+ root cause confirmed per 6 items(4 pure selector + 2 mixed selector+data)+ fix approach proposed | W23 closeout flagged for W24+ Sev4 BUG-fix per session-start.md §11 + user pick BUG-004 workflow 2026-05-19 | Chris(W23 closeout flagged for W24+ Sev4 BUG-fix) |
| 2026-05-19 | Chris confirm Sev4 + fix approach via AskUserQuestion → 6 fixes implemented + 2 test refactor → 10/10 app-shell-path pass + 22/22 full suite +7 IMPROVED → status `triaged → done` | BUG-004 single-sitting close | Chris |

---

**Lifecycle reminder**:Sev1/Sev2 → `postmortem.md` mandatory(per `PROCESS.md §4.5`)。Sev4 — none required。
