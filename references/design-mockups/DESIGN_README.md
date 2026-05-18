# EKP UI Design Reference

> **What this folder contains**
> A high-fidelity, click-through HTML prototype of the entire EKP (Enterprise Knowledge Platform) frontend, plus this reference document explaining every screen's purpose. Use it as the **design spec** when implementing or evolving the real Next.js frontend at `frontend/`.
>
> **📐 Implementing or modifying `frontend/`?** Read [`DESIGN_SYSTEM.md`](./DESIGN_SYSTEM.md) — the dev API reference (tokens / primitives / layout patterns / composite patterns like PopMenu + Stepper + OptionRow + DisabledAffordance / sync protocol). This README explains *what's in the folder*; DESIGN_SYSTEM.md explains *how to consume the design system in code*.

This is **NOT runnable code for the Next.js app**. It is a visual + interaction spec implemented in plain HTML + React (in-browser Babel) so you can open `EKP Platform.html` directly in a browser without installing anything.

---

## How to view

1. Open **`EKP Platform.html`** in a browser. The whole platform loads — sidebar, top bar, all routes, Tweaks panel.
2. Navigate via the sidebar, or use the URL hash:
   - `#dashboard` `#chat` `#kb` `#kb-detail/drive-manuals` `#kb-detail/drive-manuals/retrieval-test` `#kb-new` `#doc-detail/drive-manuals/d365_fno_gl_v2.4` `#kb-upload/drive-manuals` `#eval` `#traces` `#trace-detail/trace_2026_05_15_a7f4b2c1` `#settings` `#users` `#login` `#register`
   - Labs (Tier 2 preview): `#labs-graph-rag` `#labs-agents` `#labs-languages` `#labs-voice` `#labs-finetune` `#labs-workflows` `#labs-personalization` `#labs-tenancy`
3. Press <kbd>⌘</kbd>+<kbd>K</kbd> for the Cmd-K palette (GlobalSearch per ADR-0024).
4. Click the tools-icon button on the toolbar to open the **Tweaks panel** — switch theme, density, retrieval/trace visualization, citation placement, and jump to any route.

---

## For AI assistants reading this folder

When you (a future AI assistant) are asked to build, modify, or extend the real Next.js frontend in `frontend/`, **read this folder first**:

- `EKP Platform.html` + the `ekp-page-*.jsx` files **show the intended UX** at high fidelity. Open the HTML and click through before suggesting changes.
- The prototype is **locked to the project's real design tokens** (`frontend/lib/theming/tokens.ts` — Warm Charcoal + Coral Accent, Inter + JetBrains Mono, oklch). Do not propose new colors.
- Mock data lives in `ekp-data.jsx` — it mirrors the real backend Pydantic schemas (`backend/api/schemas/*.py`), so structure your real components against the same shapes.
- Every route maps to a Cn component in `docs/02-architecture/COMPONENT_CATALOG.md`. The mapping is in `PAGE_INVENTORY.md` (next to this file). Honor those plug-in points.

**Hard constraints honored** (see `docs/CLAUDE.md` §5.2):
- **H1 — IA locked** per ADR-0024 (AppShell top-bar + collapsible sidebar + main; 5 sidebar modules; flat URLs). Do not redesign.
- **H2 — Vendor lock** (shadcn/ui exclusive, Lucide icons, TanStack Query, Zustand, MSAL). The prototype uses its own stripped-down components for portability; **in the real app, use shadcn**.
- **H3 — Visual identity** is 100% custom oklch, not Dify. Layout patterns may borrow from Dify but not colors / logo / typography.
- **H4 — Tier boundary** — every Tier 2 feature in the prototype is explicitly badged "TIER 2" or lives under `/labs/*`.

---

## File map

| File | Purpose |
|------|---------|
| `EKP Platform.html` | Single entrypoint — loads React + Babel + all `*.jsx` files |
| `styles.css` | Design tokens (oklch) + all class names — mirrors `frontend/lib/theming/tokens.ts` |
| `icons.jsx` | Lucide-style stroke icons (16×16, currentColor) |
| `ekp-data.jsx` | All mock data — KBs, documents, chunks, traces, eval reports, conversations, images |
| `ekp-shell.jsx` | AppShell — sidebar, top bar, Cmd+K palette, dropdown menus |
| `ekp-page-dashboard.jsx` | `/dashboard` — KB summary, recent queries, latest eval, system health, quick actions |
| `ekp-page-kb.jsx` | `/kb` list, `/kb/[id]` 8-tab detail (Documents, Chunks, Images, Chunking Lab, Pipeline, Retrieval Testing, Access, Settings) |
| `ekp-page-kb-new.jsx` | `/kb/new` 5-step wizard (Identity → Format & chunking → Multimodal → Retrieval defaults → Review) |
| `ekp-page-kb-extras.jsx` | Images tab + Chunking Lab tab |
| `ekp-page-doc-detail.jsx` | `/doc-detail/[kbId]/[docId]` 3-pane (outline / chunks / inspector) |
| `ekp-page-chat.jsx` | `/chat` with Conversation History (Beta+), inline image cards, Sources strip, Feedback widget |
| `ekp-page-trace.jsx` | `/traces` list + `/traces/[traceId]` 9-stage Langfuse trace (3 viz modes) |
| `ekp-page-eval.jsx` | `/eval` RAGAs 4-metric + Reranker Shootout + Failed queries + CRAG insights |
| `ekp-page-misc.jsx` | `/kb-upload/[id]` 3-step Pipeline Wizard + original (now-superseded) thin Settings page |
| `ekp-page-settings-tabs.jsx` | `/settings` 6-tab hub (Profile / Appearance / Connections / Identity & Auth / API Keys & Quotas / Account) |
| `ekp-page-users.jsx` | `/users` 4-tab user management (Members / Roles & permissions matrix / Groups / Audit log) + KB Access tab |
| `ekp-page-auth.jsx` | `/login` + `/register` with MSAL SSO primary + email fallback + verify-email flow |
| `ekp-page-labs-1.jsx` | Labs Tier 2: GraphRAG / Multi-Agent / Multi-Language / Voice |
| `ekp-page-labs-2.jsx` | Labs Tier 2: Fine-Tune / Workflow Builder / Personalization / Multi-Tenancy |
| `tweaks-panel.jsx` | Floating Tweaks panel (state persistence + jump shortcuts) |

---

## Design system reference

All visual decisions match `frontend/lib/theming/tokens.ts`:

**Light mode** (Warm Charcoal + Coral Accent — W12 D2 ratification per ADR-0015):
- `--primary`: `oklch(0.20 0.01 285)` — warm charcoal for primary CTAs
- `--accent`: `oklch(0.65 0.18 25)` — warm coral; used **only** for emphasis + Tier 2 preview elements (see "Color semantics" below)
- `--background`: `oklch(1 0 0)` — pure white
- `--foreground`: `oklch(0.15 0 0)` — near-black
- `--muted`: `oklch(0.96 0 0)` — neutral surface for selected/active states
- `--success` `--warning` `--destructive` `--info` — semantic colors

**Dark mode** — inverted-button pattern; warm-neutral dark bg (`oklch(0.18 0.005 285)`) matching primary hue 285.

**Type**: Inter (sans) + JetBrains Mono (mono).

**Radius**: 0.25rem / 0.5rem / 0.75rem (sharper than Dify default).

### Color semantics (important — see implementation notes)

| Color | Reserved for |
|------|--------------|
| **Coral accent** (oklch 0.65 0.18 25) | Brand emphasis + **Tier 2 / preview elements**. Do **not** use as the "selected/active" state of normal radio cards — coral is in the red-orange hue range and reads as alarm to many users. |
| **Neutral / muted bg + foreground border + check icon** | "Selected / active" state of supported options |
| **Yellow / warning** | "Locked after creation" + "config change needs re-index" |
| **Red / destructive** | Only on real delete actions + actual errors |
| **Blue / info** | Informational banners + "UI behavior" markers |

This rule was applied across the prototype after the user explicitly flagged red over-use on the New KB wizard.

---

## Page inventory & rationale

See `PAGE_INVENTORY.md` for:
- Every route with its **purpose** + **Cn component mapping** + **Tier 1 / Tier 2 status**
- What's **active today** (backed by real Pydantic schemas + endpoints)
- What's **aspirational** (Tier 2 preview, marked with coral accent + "TIER 2" badge)

---

## Why this prototype exists

The Next.js frontend at `frontend/` had a thin v0 implementation (per W18 closeout: 9 routes scaffolded, plain Tailwind, deferred design polish). This prototype exists to:

1. **Visualize the full intended platform** before committing engineering effort — Dashboard / Chat / KB Detail (8 tabs) / Document Detail / Eval / Traces / Users / Settings (6 tabs) / Labs Tier 2 (8 pages) — so the team can see and feel the destination.
2. **Bind UX decisions to real backend schemas** — every screen is wired against actual `backend/api/schemas/*.py` shapes (KbStatus, RetrievalTestResult, TraceDetail, EvalReport, FeedbackRequest, etc.).
3. **Surface design questions early** — re-index flow, multimodal text+image binding, locked vs editable KB fields, per-KB ACL, role permissions matrix, RBAC view-gating — all visualized rather than left abstract.
4. **Mark Tier boundary** — explicit "TIER 2 PREVIEW" badges on every aspirational feature, so when implementation starts, the Tier 1 surface is unambiguous.

When you (AI assistant) implement a real component from `frontend/components/`, **open the corresponding HTML page first**, then build it in shadcn + Tailwind matching the layout and information density shown.
