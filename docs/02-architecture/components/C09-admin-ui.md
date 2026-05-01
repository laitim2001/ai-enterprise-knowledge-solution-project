---
component: C09
name: Admin Console UI
catalog_ref: ../COMPONENT_CATALOG.md#c09--admin-console-ui
spec_refs: [architecture.md §5.1-§5.7, references/dify (layout reference only per H3)]
status: v0-draft
last_updated: 2026-05-01
---

# C09 — Admin Console UI Design Note

> **Status**:`v0-draft`(W1 D1 F3 6 routes scaffold ✅;views wire-up W2-W5)
>
> **Owner**:AI

---

## 1. Internal Architecture

```
frontend/
├── app/                              ← Next.js 14 App Router
│   ├── layout.tsx                    ← root layout(theme provider + structured nav)
│   ├── page.tsx                      ← landing (View 1) — W3 可能 pivot to Chat root
│   ├── globals.css                   ← Tailwind base + design tokens
│   ├── admin/
│   │   ├── page.tsx                  ← View 2 Admin overview
│   │   ├── kb/
│   │   │   ├── page.tsx              ← View 3 KB list
│   │   │   └── [id]/
│   │   │       ├── page.tsx          ← View 4 KB detail + config
│   │   │       └── (W2: upload + chunks subroutes)
│   │   └── (W7+)settings/page.tsx    ← View 8 (Beta+)
│   ├── eval/page.tsx                 ← View 7 Eval dashboard
│   └── debug/[traceId]/page.tsx      ← View 6 Langfuse trace viewer
├── components/
│   ├── ui/                           ← shadcn base(Button, Card, Dialog, Skeleton, etc)
│   ├── kb/                           ← KB domain(KbCard, KbConfigForm, KbStatsBadge)
│   ├── eval/                         ← Eval domain(MetricChart, GateBadge, EvalRunTable)
│   ├── debug/                        ← TraceViewer, SpanTree
│   └── shared/                       ← AppShell, NavSidebar, ErrorBoundary, ThemeProvider
├── lib/
│   ├── api-client.ts                 ← thin fetch wrapper(reads NEXT_PUBLIC_API_URL)
│   ├── theming/
│   │   └── tokens.ts                 ← custom design tokens(non-Dify per H3)
│   └── utils.ts                      ← shadcn cn() helper
└── styles/
    └── (custom CSS 限 globals.css per CLAUDE.md §3.2)
```

### 8 Views per spec §5.1-§5.7

| # | View | Path | First wire phase | Owner Cn dep |
|---|---|---|---|---|
| 1 | Landing | `/` | W1 D1 placeholder ✅ → W3 chat root | C10 |
| 2 | Admin overview | `/admin` | W2 D1 | C02 |
| 3 | KB list | `/admin/kb` | W2 D1 | C02 |
| 4 | KB detail + config | `/admin/kb/[id]` | W2 D2 | C02 + C03 |
| 5 | Doc upload | `/admin/kb/[id]/upload` | W2 D3 | C01 + C08 |
| 6 | Chunk inspector | `/admin/kb/[id]/chunks/[doc_id]` | W3 D2 | C01 + C03 |
| 7 | Eval dashboard | `/eval` | W4 D2 | C06 |
| 8 | Debug trace viewer | `/debug/[traceId]` | W4 D3 | C07 |

(2 routes `/history` + `/settings` defer to Beta+ per spec §5.7)

---

## 2. Key Interfaces

### Inputs
- Browser navigation → Next.js routing
- User form submit → POST to C08 API via `lib/api-client.ts`
- Optional WebSocket / SSE → C10 chat streaming

### Outputs
- Server-rendered React tree(SSG / SSR mix)
- Client-side hydration + interactivity
- Browser history navigation

### Side effects
- HTTP fetch to C08 (`http://localhost:8000` dev,Azure CA URL prod)
- Browser localStorage(theme preference,no auth tokens — those goes via httpOnly cookie W7+)

---

## 3. Critical Design Decisions

| Decision | Rationale |
|---|---|
| **Next.js 14 App Router**(non Pages Router) | App Router 係 Next.js 14+ default;Server Components, streaming, layout nesting 全部 native。Pages Router legacy |
| **Server Components default,Client only for interactivity** | Per CLAUDE.md §3.2;reduce JS bundle,SEO friendly。`"use client"` directive 必須有 comment 解釋 |
| **shadcn/ui exclusive**(non Material / Ant / Chakra) | Per CLAUDE.md §3.2 H2;owns the components(copy into repo),no runtime dep,Tailwind-native |
| **TanStack Query for non-streaming data fetch**(non SWR / Redux) | Per CLAUDE.md §3.2;mature caching, invalidation, optimistic updates;`useChat`(Vercel AI SDK)handles streaming separately |
| **Zustand for cross-component state**(non Redux) | Per CLAUDE.md §3.2;minimal boilerplate;works with Server Components(client-side only) |
| **Custom design tokens(`lib/theming/tokens.ts`),100% non-Dify** | Per CLAUDE.md §5.3 H3;may reference Dify *layout pattern* but not color/logo/copy |
| **Tailwind utility classes,zero custom CSS except `globals.css`** | Per CLAUDE.md §3.2;consistent design language;easier reasoning about specificity |
| **No `any` type / no `@ts-ignore` without comment** | Per CLAUDE.md §3.2;TypeScript strict mode |

---

## 4. Edge Cases & Error Handling

| Edge case | Handling |
|---|---|
| **API error**(C08 returns 4xx/5xx)| `lib/api-client.ts` throws typed error;TanStack Query `onError` → toast notification(shadcn `Sonner` or `useToast`) |
| **Loading state** | Suspense + Skeleton component(shadcn);per-view loading.tsx file in App Router |
| **Empty state**(no KB / no docs / no eval runs)| Guidance UI:"Create your first KB" with CTA button |
| **404 not found**(invalid kb_id in URL)| Next.js notFound() helper → not-found.tsx page |
| **Network offline** | Browser online/offline event;banner with retry CTA |
| **(W7+) Auth fail / token expired** | Middleware redirect to `/login`(Entra ID flow);silent token refresh via MSAL.js |
| **API contract drift**(server schema diff)| Pydantic generates OpenAPI;frontend optionally generate types via openapi-typescript(W4+ if needed)|
| **Stream connection drop**(C10 chat)| Vercel AI SDK `useChat` 自動 retry + onError handler |

---

## 5. Performance Characteristics

| Metric | Target | Notes |
|---|---|---|
| **Page load(SSR + hydration)** | < 1s P95 | Critical for KB list / overview |
| **Time-to-interactive(TTI)** | < 2s P95 | Admin views relatively heavy(charts, tables) |
| **Largest Contentful Paint(LCP)** | < 2.5s P95 | Web Vitals |
| **JS bundle size** | < 300KB main bundle gzipped | shadcn components are copy-in,tree-shakeable |
| **TanStack Query cache** | stale-while-revalidate 5 min | Acceptable for KB list / config(infrequent change) |
| **Image optimization** | Next.js `<Image>` 自動 | Screenshots from C12 Blob via signed URL(W2+) |

---

## 6. Test Strategy

| Test type | Scope | Status |
|---|---|---|
| **Lint + type-check** | `pnpm lint` + `pnpm type-check` | ✅ W1 D1 clean |
| **Component tests**(per CLAUDE.md §3.2)| Vitest + React Testing Library | W2-W5 per view wire |
| **Integration tests** | TanStack Query mock + MSW(Mock Service Worker) | W3+ |
| **E2E**(future)| Playwright on Beta env | W8+ |
| **Visual regression** | Tier 2 nice-to-have(Chromatic / Percy) | Tier 2 |
| **Accessibility(a11y)** | axe-core + manual screen reader smoke | W5 polish |

---

## 7. Future Evolution / Tier 2 Hooks

| Tier 2 feature | C09 evolution |
|---|---|
| **Workflow / plugin builder UI** | New view(C13 component partner)plug into nav |
| **Multi-tenancy** | Tenant switcher in `AppShell` header;tenant context propagated via React Context;all API calls auto-prefix `/tenants/{tid}` |
| **Role-based view gating** | `useRole()` hook gates view rendering(Admin / End-user / Power-user) |
| **White-label theming** | Tenant-specific tokens loaded at runtime;theme switcher in settings |
| **Real-time updates**(KB indexing progress)| WebSocket or SSE to listen for index events;re-invalidate TanStack Query cache |
| **Dark mode** | shadcn supports out-of-box;toggle in `AppShell` |
| **i18n**(JP / ZH per Tier 2 multi-language)| Next.js native i18n routing;language-aware design tokens |

---

## 8. Open Items / TODO

- [ ] **W2 D1 View 2 Admin overview** wire to C02 GET /kb stats
- [ ] **W2 D1 View 3 KB list** with TanStack Query + shadcn DataTable
- [ ] **W2 D2 View 4 KB detail + config form** PATCH wire
- [ ] **W2 D3 View 5 Doc upload** multipart form to C01 + C08
- [ ] **W3 D2 View 6 Chunk inspector** with chunk PATCH (toggle enabled per §3.5)
- [ ] **W4 D2 View 7 Eval dashboard** with metric chart(recharts)+ Gate badge
- [ ] **W4 D3 View 8 Debug trace viewer** consume C07 Langfuse trace API
- [ ] **W4 designer pass on `tokens.ts`**(per Q10 resolution)
- [ ] **W5 a11y audit** + polish

---

**Cross-refs**:
- Catalog: [`../COMPONENT_CATALOG.md#c09--admin-console-ui`](../COMPONENT_CATALOG.md#c09--admin-console-ui)
- Spec: `architecture.md §5.1-§5.7`(8 views)+ Dify reference per H3 layout-only
- Skeleton commit: `7589110`(W1 D1 6 routes)
- Cross-component: consumes C08 API;shares design tokens with C10
