# Playwright E2E + pixel diff baseline harness

Tier 1 baseline test infrastructure landed W15 D4 F4 (per architecture.md v6
§5.8 + design ref §6 W15 scope + ADR-0015 UI Tier 1 expansion 9 views).

## Coverage scope

| Test file | Deliverable | Views covered |
|---|---|---|
| `golden-path.spec.ts` | F4.2 — public + chat E2E (W18 F7 updated) | `/` → `/login` redirect (Landing removed), V8 Login (`/login`), V9 Register (`/register`), V1 Chat (`/chat`) |
| `app-shell-path.spec.ts` | F4.3 + W18 F3/F4/F8 — app-shell modules | `/dashboard` (real F4 overview cards + quick actions), `/kb` KB List, `/eval` Eval Console, `/traces/[traceId]` Traces detail, AppShell sidebar nav + chrome-present-on-app-routes / absent-on-auth-pages (F8.5) |
| `visual-baseline.spec.ts` | F4.4 — pixel diff harness (W18 F7 updated) | `/login` + `/register` + `/dashboard` + `/eval` (empty-state baselines) |

> **W18 F3–F7 (per ADR-0024)**: the IA was restructured — all authenticated views moved into the `app/(app)/` route group under a single `<AppShell>`; `/admin/kb/*` → `/kb/*`, `/debug/[traceId]` → `/traces/[traceId]`, `/admin` → `/dashboard` (real overview cards landed W18 F4). The V7 marketing Landing was REMOVED (W18 F7) — `/` now redirects to `/login`; login/register success routes to `/dashboard`. `<GlobalSearch>` Cmd/Ctrl+K quick-jump palette landed W18 F6. `admin-path.spec.ts` was renamed `app-shell-path.spec.ts` + its route refs updated. Browser binaries still can't be installed under the R8 corp proxy (CO_W15_F4_browser_binaries / ADR-0017) — these spec updates are the deliverable; the run stays the pre-Beta smoke.

V4 KB Detail 5-tab interactive flow + KB seeding tests = Beta hardening trigger
(non-blocker per W15 plan F4.5 PARTIAL PASS acceptance "local-only baseline OK
Tier 1").

## Prerequisites

Run once:

```bash
# 1. Install Playwright browser binaries (~300MB Chromium download)
cd frontend
npx playwright install chromium
```

If R8 corp proxy blocks the binary CDN download, see ADR-0017 trigger candidate
or use personal Azure dev tier per W11 retro CO17 pattern.

## Running tests

E2E tests need both servers running. Per CLAUDE.md §13 dev server policy,
backend uvicorn is user-driven separately; Playwright auto-starts the frontend
dev server via `webServer` config.

```bash
# Terminal 1 — backend (one-time per session)
cd backend
.venv/Scripts/python.exe -m uvicorn api.server:app --port 8000

# Terminal 2 — Playwright (auto-starts pnpm dev on port 3001)
cd frontend
pnpm test:e2e               # Run all tests
pnpm test:e2e:ui            # Interactive UI mode (Playwright Inspector)
pnpm test:e2e:update-snapshots  # Capture / update pixel diff baseline
```

## First-time pixel diff baseline capture

Before pixel diff tests can pass on diff comparison, baseline screenshots must
be captured:

```bash
pnpm test:e2e:update-snapshots
```

This runs `visual-baseline.spec.ts` + writes baseline PNGs to:

```
frontend/tests/e2e/visual-baseline.spec.ts-snapshots/
├── v8-login-chromium-win32.png
├── v9-register-step1-chromium-win32.png
├── dashboard-chromium-win32.png
└── v5-eval-console-chromium-win32.png
```

Commit these baselines to git (they form the visual regression contract).
Subsequent `pnpm test:e2e` runs diff against them with 1% pixel tolerance.

When intentional UI changes happen (e.g., the W18 F3 app-shell IA restructure +
the W18 F4 dashboard overview cards; the V7 Landing baseline was dropped in W18
F7 when the Landing page was removed), re-run `--update-snapshots` after visual
approval and re-commit.

## Authentication

Tests assume `NEXT_PUBLIC_AUTH_MOCK=true` (set automatically via
`playwright.config.ts` webServer env) so Entra ID SSO is bypassed via mock
MSAL. No real Azure AD round-trip needed in test mode.

If backend is run with `feature_auth_mock=true` (default Tier 1), the mock
bearer is accepted directly.

## Backend stub endpoints

V5 Eval Console and V6 Debug View test against backend stub endpoints (501
NOT_IMPLEMENTED) per W15 plan §3 PARTIAL PASS acceptance:

- `POST /eval/run` — W4 stub (eval-methodology.md cascade)
- `POST /eval/shootout` — W4 stub
- `GET /debug/trace/{trace_id}` — W3+ stub (Langfuse correlation)

Tests assert UI handles 501 gracefully via stub mitigation pattern (empty
state + AlertCircle + stub note + retry: false on TanStack Query).

## CI integration

Deferred to W16+ Beta hardening per W15 plan F4.5. Local-only baseline OK
for Tier 1 acceptance.

## Troubleshooting

| Symptom | Mitigation |
|---|---|
| `npx playwright install` blocked by R8 corp proxy | ADR-0017 trigger; use personal Azure dev tier per W11 retro CO17 |
| Tests fail on first run with "Backend unreachable" | Start backend uvicorn on port 8000 |
| Pixel diff fails after intentional UI change | Re-run `pnpm test:e2e:update-snapshots` + commit new baseline |
| Webserver auto-start hangs | Set `reuseExistingServer: true` in `playwright.config.ts` + start `pnpm dev` manually |
