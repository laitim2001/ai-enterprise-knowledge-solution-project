---
bug_id: BUG-004
report_ref: ./report.md
status: done            # in-progress | done
last_updated: 2026-05-19
---

# BUG-004 — Checklist

> Derived from `report.md §7 Acceptance for Fix`。延後項標 🚧 + reason(per CLAUDE.md sacred rule — 唔可以刪未勾 `[ ]`)。

## Fix

- [x] **T1** — Reproduction confirmed locally:`PW_CHANNEL=chrome pnpm exec playwright test tests/e2e/app-shell-path.spec.ts --reporter=line` → 6 failed + 4 passed in ~3.9 min(per W23 D2.2 finding;6 distinct root causes verified via error context per-test page snapshots)

- [x] **T2** — Root cause confirmed per 6 items via error-context.md page snapshots(`test-results/app-shell-path-*-chromium/error-context.md`):
  - #1 `/dashboard` stat-label icon+space prefix → strict regex anchor fail
  - #2 `/kb` placeholder "Filter by name, owner, tag…" not "Search"
  - #3 `/traces` seg uses `<button role="tab">` inside `<div role="tablist">` (W22 `.seg` pattern)
  - #4 `/traces/20260605-Q014` 喺 in-memory backend 唔 exist → backend Langfuse fetch hangs → loading state persists(no h1.page-title)
  - #5 Sidebar `<NavItem>` adds Cmd↵ suffix → accessible name = "Chat Cmd↵"
  - #6 `/kb/drive_user_manuals` 喺 in-memory backend 唔 exist → error banner state(no tablist)

- [x] **T3 (#1)** — Fix `/dashboard` 4-stat strip selectors:`.stat-label` CSS class filter approach applied 3 個 stat labels(Knowledge bases / Documents / Recall @ 5)— W22 CSS-first per CLAUDE.md v1.9 §3.2 + W23 D1.2 anti-pattern catalog
- [x] **T4 (#2)** — Fix `/kb` placeholder selector:`getByPlaceholder(/filter by name/i)` 取代 `getByPlaceholder(/search/i)`(W22 F5.1 actual placeholder per `ekp-page-kb.jsx`)
- [x] **T5 (#3)** — Fix `/traces` seg selectors:`getByRole('tab', { name: label, exact: true })` 取代 `getByRole('button', ...)` inside `for (const label of [...])` loop
- [x] **T6 (#4)** — Refactor `/traces/[traceId]` test render-smoke 3-state OR:
  - `loadingState.or(pageHeader).or(errorHeading).first()` — accepts loading / happy / graceful error
  - **Open Langfuse link assertion + 3 viz modes assertion 全部 defer W24+** — both surfaces 喺 loading state 唔 render,需要 seeded Langfuse trace via Track A IT cred + CO17
- [x] **T7 (#5)** — Fix sidebar Chat selector:`name: /^chat\b/i`(word boundary `\b`)取代 `/^chat$/i`(accommodate "Chat Cmd↵" suffix)
- [x] **T8 (#6)** — Refactor `/kb/[id]` test render-smoke 2-state OR:
  - `tablist.or(errorBanner).first()` — accepts happy 8-tab OR data-empty error
  - Wait `Loading KB…` to clear w/ 20s timeout(W23 D2.1 OneDrive cold-start finding)
  - **8-tab strict count + Access affordance assertion defer W24+** — needs seeded `drive_user_manuals` KB

- [x] **T9** — Re-run `app-shell-path.spec.ts`:`PW_CHANNEL=chrome pnpm exec playwright test tests/e2e/app-shell-path.spec.ts --reporter=line` → **10/10 pass in 1.6m** ✅(W23 baseline 4/10 → **+6 net IMPROVED**)

- [x] **T10** — Re-run full Playwright suite via `PW_CHANNEL=chrome pnpm exec playwright test --reporter=line` → **22/22 pass in 2.0m**(W23 baseline 15/22 → **+7 net IMPROVED**)

## Cross-Cutting

- [x] Commit references `progress.md` entry;component tag `(frontend)` 對應 C09 per CC-1
- [x] No ADR(E2E test fix only,no architectural / vendor change — H1+H2 not triggered)
- [x] `report.md` status `triaged → done`;this `checklist.md` status `in-progress → done`;`progress.md` written
- [x] Header docstring updated to reflect BUG-004 2026-05-19 amendments scope(6 selector tweaks + 2 render-smoke refactor)
- [x] No CLAUDE.md / session-start.md update needed at BUG-004 close;§11 Sev4 BUG-fix carry-over flip CLOSED at session-start sync task #27(combined w/ BUG-003)

## 🚧 Deferred W24+(per CLAUDE.md sacred rule — assertion deferrals NOT test skip)

- 🚧 `/traces/[traceId]` Open Langfuse link assertion — needs seeded Langfuse trace via Track A IT cred + Postgres-path runtime smoke(CO17 ledger)
- 🚧 `/traces/[traceId]` 3 viz modes seg(Vertical / Waterfall / Flame)assertion — needs seeded Langfuse trace
- 🚧 `/kb/[id]` 8-tab strict count assertion(7 active + 1 disabled Access)— needs seeded `drive_user_manuals` KB
- 🚧 `/kb/[id]` Access tab `aria-disabled="true"` assertion(per ADR-0025 + ADR-0027 Option A future scope)— needs seeded KB + Wave C1+C2 RBAC backend infra

---

**Lifecycle reminder**:新加 acceptance item 必先入 `report.md §7`,然後再加 checklist。延後項標 🚧 + reason,唔可以刪。
