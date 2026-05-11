# Frontend unit tests (Vitest + React Testing Library)

Established W17 F6 — closes `CO_W15_F4_vitest_baseline_gap` (CLAUDE.md §3.2 named
"Vitest + React Testing Library" as the frontend test framework; this is the
first time the harness exists).

## Run

```bash
pnpm test:unit          # vitest run (one-shot, CI)
pnpm test:unit:watch    # vitest (watch mode, local dev)
```

Config: `frontend/vitest.config.ts` — jsdom environment, `@vitejs/plugin-react`,
path alias `@/* → ./*` (mirrors `tsconfig.json`), `setupFiles: tests/unit/setup.ts`
(jest-dom matchers + per-test `cleanup()`). Discovers `tests/unit/**/*.test.{ts,tsx}`;
explicitly excludes `tests/e2e/**` so it never picks up Playwright specs.

## The three test layers (don't blur them)

| Layer | Tool | Scope | Where |
|---|---|---|---|
| **Unit / component** | Vitest + RTL + jsdom | A component renders the right token classes / a small interaction (click, type) fires the right handler; pure-function utils | `frontend/tests/unit/` (this dir) |
| **E2E / golden-path** | Playwright (real Chromium) | Full user flows across pages — register→login, KB upload, Pipeline wizard; pixel-diff baselines | `frontend/tests/e2e/`, `playwright.config.ts`, `pnpm test:e2e` |
| **Backend** | pytest + pytest-asyncio | API routes, pipeline, retrieval, eval, auth | `backend/tests/`, `pytest` |

## What's here now

- `button.test.tsx` (W17 F6) — sample: `@/components/ui/button` renders children +
  the default `bg-primary text-primary-foreground` token-class variant, the
  `destructive` variant swaps to `bg-destructive`, and `onClick` fires on a
  `user-event` click. Proves the harness works (jsdom + RTL + jest-dom + cva token
  resolution + user-event).
- `app-shell.test.tsx` (W18 F8.4) — `<AppShell>`: the 5 sidebar nav modules render
  under `<nav aria-label="Primary">`, the active route gets `aria-current="page"`,
  the focus-mode toggle hides the desktop sidebar (+ flips its label), the top-bar
  global-search trigger is present. (`next/navigation` + `next/link` + `@/lib/api/kb`
  mocked; `<UserMenu>` shows "Signing in…" with no AuthProvider — that path is fine.)
- `global-search.test.tsx` (W18 F8.4) — `<GlobalSearch>`: opening renders the static
  Page results, typing filters them + appends an "Ask in chat: …" action, selecting
  that result `router.push('/chat?q=…')` + closes the palette, ArrowDown+Enter selects
  the next result. (KB results come off `useQuery` — mocked to `[]`.)
- `dashboard.test.tsx` (W18 F8.4) — `/dashboard` page render smoke: the `<h1>` + the
  5 overview card headings (`role="heading" aria-level={2}`) + the 4 quick-action links
  with the right hrefs. (Both `useQuery` calls mocked; this is a structure smoke.)

These are render/interaction **smokes** — not exhaustive component coverage (see below).

## Tier 2 — expand coverage

Broad component coverage (every shadcn primitive, every page-level component,
form-validation edge cases, hook tests, MSW-mocked data-fetching components) is
**Tier 2**. Tier 1 ships the harness + a smoke; Tier 2 fills it in. Interactive
multi-page flows stay in the Playwright E2E layer (`CO_W15_F4_interactive_flow_E2E`),
not here.
