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

## What's here now (W17 F6)

- `button.test.tsx` — sample: `@/components/ui/button` renders children + the
  default `bg-primary text-primary-foreground` token-class variant, the
  `destructive` variant swaps to `bg-destructive`, and `onClick` fires on a
  `user-event` click. This is a render/interaction **smoke** — it proves the
  harness works (jsdom + RTL + jest-dom + cva token resolution + user-event),
  not exhaustive component coverage.

## Tier 2 — expand coverage

Broad component coverage (every shadcn primitive, every page-level component,
form-validation edge cases, hook tests, MSW-mocked data-fetching components) is
**Tier 2**. Tier 1 ships the harness + a smoke; Tier 2 fills it in. Interactive
multi-page flows stay in the Playwright E2E layer (`CO_W15_F4_interactive_flow_E2E`),
not here.
