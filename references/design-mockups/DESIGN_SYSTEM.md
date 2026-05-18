# EKP Design System — Developer Reference

> **Audience**: frontend developers + AI assistants implementing or modifying `frontend/`.
>
> **Scope**: this doc is the **dev API reference** for the design system. For folder overview + "how to view the prototype" see [`DESIGN_README.md`](./DESIGN_README.md). For per-route component mapping see [`PAGE_INVENTORY.md`](./PAGE_INVENTORY.md).
>
> **Source of truth ordering**:
> 1. `styles.css` (canonical CSS in this folder) — all tokens + all class definitions
> 2. `frontend/app/styles-mockup.css` — verbatim copy of `styles.css` adopted into Next.js
> 3. `frontend/app/globals.css` — Tailwind bridge layer (declares CSS custom properties for utility consumption)
> 4. `frontend/lib/theming/tokens.ts` — TypeScript mirror of color tokens only (consumed by `tailwind.config.ts`)
>
> When the chain drifts (e.g. mockup designer updates `styles.css` but frontend hasn't re-synced), follow §7 **Sync protocol** to repair.
>
> **Reading order**: §1 tokens → §2 primitives → §3 layouts → §4 composites are layered; later sections build on earlier ones. §5-§8 are cross-cutting reference / hygiene.

---

## §0 Quick reference card

| Need | Answer |
|---|---|
| **Make a button** | `<button className="btn btn-primary btn-sm">` — see §2.1 |
| **Make a card** | `<div className="card">` + `.card-header` + `.card-body` + `.card-footer` — see §2.2 |
| **Make a form field** | `<div className="field">` + `.label` + `.input` + `.hint` — see §2.3 |
| **Make a badge** | `<span className="badge badge-success">` — see §2.4 |
| **Make a toggle switch** | `<span className="switch" data-on={value} onClick={...} />` — see §2.5 |
| **Make a seg control** | `<div className="seg">` + `<button className="seg-btn" data-active={...}>` — see §2.6 |
| **Page shell** | `<div className="content">` + `.content-wide`/`.content-narrow` + `.page-header` — see §3.1-3.2 |
| **4-stat strip** | `<div className="stat-grid">` + 4 `<div className="stat">` — see §3.3 |
| **KB cards grid** | `<div className="kb-grid">` + N `<div className="kb-card">` — see §3.4 |
| **Topbar dropdown** | Portal-to-body + `position: fixed; right: 66 (or 138 / 20)` — see §4.1 |
| **Multi-step wizard** | Stepper card 28px circles + per-step `<div className="card">` — see §4.2 |
| **Tier 2 disabled affordance** | `<button disabled style={{ opacity: 0.5, cursor: 'default' }}>` with `<span className="badge badge-accent">T2</span>` — see §4.4 |
| **Use accent coral** | **NOT** for "selected" state — reserved for brand emphasis + Tier 2 — see §5 |

---

## §1 Token reference

All tokens declared in `styles.css` `:root` and mirrored in `frontend/app/globals.css`. Consumers should **never hardcode color values** — reference via `oklch(var(--token))` wrapper (CSS) or `oklch(var(--token))` template in TS.

### 1.1 Color tokens — light mode (Warm Charcoal + Coral Accent)

Per ADR-0015 + W12 D2 ratification. Values are bare `L C H` triplets; consumers wrap with `oklch(...)` at use site.

| CSS var | Value `L C H` | Purpose |
|---|---|---|
| `--primary` | `0.20 0.01 285` | Warm charcoal — primary CTA bg, nav active rail, brand mark |
| `--primary-foreground` | `0.98 0 0` | Text on primary bg |
| `--secondary` | `0.94 0.005 285` | Subtle warm-tinted surface |
| `--secondary-foreground` | `0.20 0.01 285` | Text on secondary bg |
| `--accent` | `0.65 0.18 25` | **Warm coral** — brand emphasis + Tier 2 markers (see §5) |
| `--accent-foreground` | `0.98 0 0` | Text on accent bg |
| `--background` | `1 0 0` | Pure white page background |
| `--foreground` | `0.15 0 0` | Near-black primary text |
| `--card` | `1 0 0` | Card surface (same as background light mode) |
| `--card-foreground` | `0.15 0 0` | Text on card |
| `--popover` | `1 0 0` | Popover surface |
| `--popover-foreground` | `0.15 0 0` | Text on popover |
| `--muted` | `0.96 0 0` | Neutral selected/hover surface |
| `--muted-foreground` | `0.45 0 0` | Secondary text |
| `--border` | `0.92 0 0` | Standard border |
| `--border-strong` | `0.85 0 0` | Emphasized border (dashed callouts) |
| `--input` | `0.92 0 0` | Input field border |
| `--ring` | `0.65 0.18 25` | Focus ring (matches accent) |
| `--success` | `0.65 0.16 145` | Green — READY status, completed step, eval pass |
| `--warning` | `0.78 0.16 80` | Amber — LOCKED, "re-index needed", config-change-affects-schema |
| `--destructive` | `0.57 0.22 25` | Red — delete actions, real errors only |
| `--info` | `0.62 0.13 240` | Blue — info banners, "UI behavior" markers |

### 1.2 Color tokens — dark mode (inverted-button pattern)

Activated via `.dark` class on root or `[data-theme="dark"]`. Background = `oklch(0.18 0.005 285)` warm-neutral dark (subtle hue 285 alignment with primary). Primary inverts to light warm-neutral so buttons read as "lifted" surfaces.

| CSS var | Dark value | Shift from light |
|---|---|---|
| `--primary` | `0.95 0.005 285` | L 0.20 → 0.95 (inverted) |
| `--accent` | `0.68 0.16 25` | L 0.65 → 0.68 + chroma 0.18 → 0.16 (better contrast on dark) |
| `--background` | `0.18 0.005 285` | Warm-neutral dark |
| `--foreground` | `0.95 0 0` | Light text |
| `--card` | `0.20 0.005 285` | One step lighter than bg |
| `--popover` | `0.22 0.005 285` | Two steps lighter than bg ⚠️ |
| `--muted` | `0.25 0.005 285` | Three steps lighter |
| `--border` | `0.30 0.005 285` | Subtle separator |

> ⚠️ **`--popover` dark drift incident (W22 F1)**: the popover L value was `0.20` in `globals.css` while `styles.css` had it at `0.22`. Caught via user-eye verify, fixed `a385180`. **Lesson**: any time mockup `styles.css` dark mode tokens update, `globals.css` must re-sync. See §7.

### 1.3 Radius

| CSS var | Value | Use case |
|---|---|---|
| `--radius-sm` | `0.25rem` | Inputs, badges, small cards |
| `--radius-md` | `0.5rem` | Standard cards, modals |
| `--radius-lg` | `0.75rem` | Large feature cards |

Sharper than Dify's default radii — intentional editorial-direction choice per ADR-0015.

### 1.4 Shadow

| CSS var | Use case |
|---|---|
| `--shadow-xs` | Subtle lift (active button, small chip) |
| `--shadow-sm` | Standard card |
| `--shadow-md` | Modal, dropdown elevation |
| `--shadow-lg` | Popover, dialog elevation |

Dark mode shadows use stronger alpha (0.3-0.6 vs 0.04-0.10 in light) to remain visible on dark background.

### 1.5 Font

| CSS var | Family | Use |
|---|---|---|
| `--font-sans` | `Inter, ui-sans-serif, system-ui, ...` | All body text, UI labels, headings |
| `--font-mono` | `JetBrains Mono, ui-monospace, "SF Mono", Menlo, ...` | KB ids, hashes, timestamps, code, technical IDs |

Body inherits `font-sans` 14px line-height 1.5. Mono used via `<span className="mono">` or `.mono` utility class.

### 1.6 Density

| CSS var | Default | Compact | Comfy |
|---|---|---|---|
| `--density-row` | `44px` | `36px` | `52px` |
| `--density-pad` | `16px` | `12px` | `20px` |

Activated via `data-density="compact|comfy"` on root. Default (no attribute) = normal density.

### 1.7 Layout vars

| CSS var | Value | Override notes |
|---|---|---|
| `--sidebar-w` | `248px` | Collapse to `60px` via `[data-sidebar="collapsed"]` on `.app` |
| `--topbar-h` | `52px` | Spec-locked; brand strip in sidebar aligns to this height |

These drive both AppShell grid and `<PopMenu>` vertical anchor (`top: calc(var(--topbar-h) - 4px)`).

### 1.8 Animation

| CSS var | Value | Use |
|---|---|---|
| `--duration-fast` | `150ms` | Hover transitions, badge fades |
| `--duration-base` | `200ms` | Modal/popover open, stepper transitions |
| `--ease` | `cubic-bezier(0.4, 0, 0.2, 1)` | All transitions — material-style standard |

Predefined animations: `pop-in 0.14s var(--ease)` for popover entry, `pulse 1.4s ease-in-out infinite` for `.status-dot.processing`.

---

## §2 Primitive index

Each primitive: **class catalog** + **minimal example** + **rationale notes**. Cross-reference with `styles.css` line numbers for source.

### 2.1 Button — `.btn` family

**Variants** (color/style):

| Class | Use |
|---|---|
| `.btn-primary` | Primary CTA (charcoal bg, light text) |
| `.btn-accent` | Brand emphasis CTA (coral bg, light text) — sparingly, reserved for "primary brand action of the page" e.g. KB Create |
| `.btn-secondary` | Standard action (muted bg, foreground text, border) |
| `.btn-ghost` | Borderless action (transparent bg, foreground text, hover muted) |
| `.btn-ghost-muted` | Borderless tertiary (muted-foreground text initially, foreground on hover) |
| `.btn-destructive` | Destructive action (destructive bg, light text) |

**Sizes** (height + padding + font):

| Class | Height | Use |
|---|---|---|
| `.btn-lg` | 38px | Auth submit, primary modal CTA |
| `.btn-sm` | 28px | Standard page-action button, table row action |
| `.btn-xs` | 24px | Inline ghost action, popover footer link |
| _(default)_ | 36px | General use |

**Icon-only**: add `.btn-icon` to make button square (width = height); typically combined with `.btn-sm` → 28×28 or `.btn-xs` → 24×24.

**Disabled**: `disabled` attribute applies `opacity: 0.5; pointer-events: none` via `.btn[disabled]` rule.

**Example**:
```tsx
<button type="button" className="btn btn-primary btn-sm">
  <Plus size={13} /> New KB
</button>

<button type="button" className="btn btn-ghost btn-icon btn-sm" aria-label="Settings">
  <Settings size={15} />
</button>
```

### 2.2 Card — `.card` family

**Structure** (4 zones):

```
.card
├── .card-header   — title + actions row
│   ├── .card-title       (h3, 14px / 600)
│   └── .card-desc        (12.5px / muted-foreground)
├── .card-body              (18px padding)
│   OR .card-body-tight    (0 padding — for tables, lists)
└── .card-footer           (18px padding, top-border, flex space-between)
```

**Variant**:
- `.card-flat` — removes border-radius + side borders (for cards inside cards / full-bleed sections)

**Example**:
```tsx
<div className="card">
  <div className="card-header">
    <h3 className="card-title">Knowledge bases</h3>
    <Link href="/kb" className="btn btn-secondary btn-sm">View all →</Link>
  </div>
  <div className="card-body card-body-tight">
    <table className="table">...</table>
  </div>
  <div className="card-footer">
    <div className="text-xs muted mono">Reranker locked · cohere-v4.0-pro</div>
    <Link href="/eval" className="btn btn-ghost btn-xs">Shootout →</Link>
  </div>
</div>
```

### 2.3 Form field — `.field` + `.label` + `.input` + `.hint`

**Standard form group** (vertical stack):

```tsx
<div className="field">
  <label className="label" htmlFor="example">Field name</label>
  <input
    id="example"
    className="input"
    placeholder="..."
    value={value}
    onChange={(e) => setValue(e.target.value)}
  />
  <div className="hint">Helper text or constraint explanation</div>
</div>
```

**Variants**:
- `<textarea className="input" rows={3}>` — same `.input` class works for textarea
- `<select className="select">` — separate `.select` class for dropdowns
- `.input.mono` — add `.mono` for kb_id, hash, code-like inputs (uses font-mono)

**Search input with leading icon**:
```tsx
<div className="input-search-wrap" style={{ flex: 1, maxWidth: 320 }}>
  <span className="icon-leading"><Search size={14} /></span>
  <input className="input" placeholder="Filter by name…" />
</div>
```
The wrapper adds left-padding `32px` to the inner input via `.input-search-wrap .input` rule.

**Error state**:
```tsx
{errors.field && (
  <div className="hint" style={{ color: 'oklch(var(--destructive))' }} role="alert">
    {errors.field}
  </div>
)}
```

### 2.4 Badge — `.badge` family

**Semantic variants**:

| Class | Color | Typical use |
|---|---|---|
| `.badge-success` | Green tint | READY, ACTIVE, completed, BETA DEFAULT |
| `.badge-warning` | Amber tint | LOCKED, "Re-index needed" |
| `.badge-error` | Red tint | FAILED, ERROR |
| `.badge-info` | Blue tint | INDEXING, UI BEHAVIOR marker |
| `.badge-accent` | Coral tint | TIER 2 PREVIEW marker, brand emphasis |
| `.badge-muted` | Neutral muted | ARCHIVED, EMPTY, tag chip |

**With dot indicator**:
```tsx
<span className="badge badge-success">
  <span className="badge-dot" /> READY
</span>
```
`.badge-dot` is a 6×6 circle in `currentColor`. Use for status-style badges (READY / FAILED / INDEXING). Omit for plain category chips (TIER 2 / Locked).

**With icon**:
```tsx
<span className="badge badge-warning">
  <Shield size={10} /> Locked
</span>
```

### 2.5 Switch — `.switch`

Visual-only toggle (no native checkbox). State driven by `data-on` attribute. Animation handled by CSS via `.switch[data-on="true"]::after { transform: translateX(14px); }`.

**Controlled (with handler)**:
```tsx
<span
  className="switch"
  data-on={value}
  onClick={() => setValue(!value)}
  role="switch"
  aria-checked={value}
  tabIndex={0}
/>
```

**Visual-only (no handler)** — for mockup-style display switches (e.g. ChatHeader CRAG + Show images):
```tsx
<span className="switch" data-on="true" />
```

### 2.6 Seg control — `.seg` + `.seg-btn`

Mutually-exclusive choice (like radio group but pill-shaped).

```tsx
<div className="seg">
  {options.map((opt) => (
    <button
      key={opt}
      type="button"
      className="seg-btn"
      data-active={value === opt}
      onClick={() => setValue(opt)}
    >
      {opt}
    </button>
  ))}
</div>
```

Active state via `data-active="true"`; inactive seg-btns are muted-foreground with hover lift.

### 2.7 Tabs — `.tabs` + `.tab`

Horizontal tab bar; same `data-active="true"` convention as seg.

```tsx
<div className="tabs">
  {tabs.map((t) => (
    <button
      key={t.id}
      type="button"
      className="tab"
      data-active={activeTab === t.id}
      onClick={() => setActiveTab(t.id)}
    >
      {t.label}
      {t.count !== undefined && <span className="count">{t.count}</span>}
    </button>
  ))}
</div>
```

`.tab .count` renders a small parenthetical count chip (e.g. "Documents (12)").

### 2.8 Table — `.table` + `.table-wrap`

```tsx
<div className="table-wrap">
  <table className="table">
    <thead>
      <tr>
        <th>Name</th>
        <th>Status</th>
        <th className="col-num">Docs</th>
        <th className="col-num">R@5</th>
        <th className="col-shrink" aria-label="Row actions" />
      </tr>
    </thead>
    <tbody>
      {rows.map((r) => (
        <tr key={r.id}>
          <td>...</td>
          <td><span className="badge badge-success">...READY</span></td>
          <td className="col-num">{r.docs}</td>
          <td className="col-num">{r.recall.toFixed(1)}%</td>
          <td className="col-shrink">
            <button className="btn btn-ghost btn-icon btn-xs">
              <MoreHorizontal size={14} />
            </button>
          </td>
        </tr>
      ))}
    </tbody>
  </table>
</div>
```

**Column class modifiers**:
- `.col-num` — `font-variant-numeric: tabular-nums; text-align: right; font-family: var(--font-mono); font-size: 12.5px` — for numeric columns
- `.col-mono` — mono only, no alignment
- `.col-shrink` — `width: 1px; white-space: nowrap` — for actions column

**Row hover**: built-in via `.table tbody tr:hover { background: oklch(var(--muted) / 0.4) }`. No additional class needed.

**Row link**: wrap first `<td>` content in `<Link>` with `.table-row-link` on the inner text for proper hover treatment.

### 2.9 Banner — `.banner` family

Inline alert/info block inside cards or page bodies.

```tsx
<div className="banner banner-warning" style={{ marginBottom: 16 }}>
  <TriangleAlert size={14} style={{ color: 'oklch(var(--warning))' }} />
  <div style={{ flex: 1, fontSize: 12.5, lineHeight: 1.55 }}>
    Changing these settings later requires a <b>full re-index</b>.
  </div>
</div>
```

Variants:
- `.banner-info` — blue tint, info icon
- `.banner-warning` — amber tint, warning icon
- `.banner-success` — green tint, check icon

Banners are flex-row by default; icon left, message body flex-grow.

### 2.10 Progress bar — `.progress`

```tsx
<div className="progress accent">
  <i style={{ width: `${percentage * 100}%` }} />
</div>
```

Variants: `.progress` (foreground), `.progress.accent` (coral), `.progress.success` (green). The `<i>` element is the filled portion; width controls progress.

### 2.11 Status dot — `.status-dot`

Tiny colored circle for inline state indicators (e.g. "System healthy", KB status).

```tsx
<span className={`status-dot ${stateClass}`} />
```

State classes:
| Class | Color | Animation |
|---|---|---|
| `.ready` | success | static |
| `.indexing` | info | static |
| `.failed` | destructive | static |
| `.queued` | muted-foreground | static |
| `.processing` | info | `pulse 1.4s` infinite |

### 2.12 Avatar — `.avatar`

Circle initial badge.

```tsx
<div className="avatar avatar-sm">CL</div>
```

Sizes: `.avatar` (default ~32px) / `.avatar-sm` (22px / 10px text) / `.avatar-lg` (36px / 13px text). Background is `var(--muted)` by default; can override via inline style for per-user color.

### 2.13 Utility — `.mono` / `.muted` / `.row` / `.col` / `.spacer` / `.hr` / `.text-xs` / `.text-sm`

| Class | Effect |
|---|---|
| `.mono` | `font-family: var(--font-mono); font-size: 12.5px` |
| `.muted` | `color: oklch(var(--muted-foreground))` |
| `.row` | `display: flex; align-items: center; gap: 8px` |
| `.col` | `display: flex; flex-direction: column; gap: 8px` |
| `.spacer` | `flex: 1` (for flex-row push-right) |
| `.hr` | 1px horizontal divider with 12px vertical margin |
| `.text-xs` | `font-size: 11.5px` |
| `.text-sm` | `font-size: 12.5px` |

Combine freely: `<span className="text-xs muted mono">trace_2026_05_15_a7f4b2c1</span>`.

---

## §3 Layout patterns

### 3.1 Page shell — `.content` + `.content-wide` / `.content-narrow`

Every page renders inside `<AppShell>` (provided by `frontend/components/nav/app-shell.tsx`). The page's own root self-wraps in `.content` to inherit padding + scroll behavior:

```tsx
// Page-level self-wrap pattern (F1 H7 pivot 2026-05-18 — AppShell is layout-agnostic).
return (
  <div className="content">
    <div className="content-wide">   {/* OR .content-narrow for forms/wizards */}
      {/* page content */}
    </div>
  </div>
);
```

**Width variants**:
- `.content-wide` — `max-width: 1600px; margin: 0 auto` — for dashboards, lists, multi-column views
- `.content-narrow` — `max-width: 1280px; margin: 0 auto` — for forms, wizards, single-column reading

**Exception**: `/chat` uses full-bleed grid layout without `.content` wrap (3-pane: 260px history + 1fr main + 400px citations).

### 3.2 Page header — `.page-header`

```tsx
<div className="page-header">
  <div>
    <h1 className="page-title">Knowledge bases</h1>
    <p className="page-subtitle">
      Each KB is provisioned with its own Azure AI Search index per ADR-0018.
    </p>
  </div>
  <div className="page-actions">
    <button className="btn btn-secondary btn-sm">Export</button>
    <Link href="/kb/new" className="btn btn-primary btn-sm">
      <Plus size={13} /> New KB
    </Link>
  </div>
</div>
```

`.page-header` is `display: flex; justify-content: space-between; align-items: flex-start` with 28px bottom-margin. `.page-actions` is flex-row 8px gap.

**Back link** in subtitle area (e.g. /kb/new):
```tsx
<div style={{ display: 'flex', alignItems: 'center', gap: 8, marginBottom: 4 }}>
  <Link href="/kb" className="btn btn-ghost btn-xs btn-ghost-muted">
    <ChevronLeft size={12} /> Knowledge
  </Link>
</div>
```

### 3.3 Stat strip — `.stat-grid` + `.stat`

4-column responsive stat grid for dashboard / metric overview.

```tsx
<div className="stat-grid">
  <div className="stat">
    <div className="stat-label">
      <Database size={13} /> Knowledge bases
    </div>
    <div className="stat-value">
      {count}<span className="stat-unit"> active</span>
    </div>
    <div className="stat-meta">
      <span className="status-dot ready" /> All ready
    </div>
  </div>
  {/* 3 more .stat */}
</div>
```

`.stat-grid` is `display: grid; grid-template-columns: repeat(4, 1fr); gap: 12px`.

### 3.4 KB cards grid — `.kb-grid` + `.kb-card`

Adaptive card grid (auto-fill 280px+).

```tsx
<div className="kb-grid">
  {kbs.map((kb) => (
    <Link
      key={kb.kb_id}
      href={`/kb/${kb.kb_id}`}
      className="kb-card"
      style={{ textDecoration: 'none', color: 'inherit', display: 'flex', flexDirection: 'column' }}
    >
      <div className="kb-card-head">
        <div className="kb-icon"><Database size={18} /></div>
        <span className="badge badge-success"><span className="badge-dot" /> READY</span>
      </div>
      <div>
        <div className="kb-title">{kb.name}</div>
        <div className="kb-desc">{kb.description}</div>
      </div>
      <div className="kb-meta">
        <span><FileText size={11} /> {kb.total_documents}</span>
        <span><Layers size={11} /> {kb.total_chunks}</span>
        <span><Zap size={11} /> R@5 —%</span>
        <span style={{ marginLeft: 'auto' }}>{relativeTime}</span>
      </div>
    </Link>
  ))}
</div>
```

### 3.5 Activity list — `.activity` + `.activity-icon` + `.activity-body` + `.activity-time`

For chronological feeds (recent queries, audit log):

```tsx
<div className="activity-list">
  {events.map((e) => (
    <div key={e.id} className="activity">
      <div className="activity-icon"><MessageCircle size={14} /></div>
      <div className="activity-body">
        <div>{e.title}</div>
        <div className="text-xs muted mono">{e.metadata}</div>
      </div>
      <div className="activity-time">{e.relativeTime}</div>
    </div>
  ))}
</div>
```

Each `.activity` has 12px vertical padding + 1px bottom border (auto-strips last).

### 3.6 AppShell — `.app` + `.sidebar` + `.main` + `.topbar`

Provided by `frontend/components/nav/app-shell.tsx`. Page components **don't render these directly** — they render their `.content` wrap inside `<AppShell>`'s `<main>` slot.

Grid structure:
```
.app  (grid-template-columns: var(--sidebar-w) 1fr; height: 100vh)
├── .sidebar  (border-right, padding, brand+nav+footer)
└── .main  (flex-col, overflow-hidden)
    ├── .topbar  (var(--topbar-h), border-bottom)
    └── (content slot — receives page's <div className="content">)
```

Sidebar collapse: `[data-sidebar="collapsed"]` on `.app` flips `--sidebar-w` to 60px.

---

## §4 Composite patterns

These are **multi-class compositions** for specific UX patterns. Recipes here prevent re-deriving the pattern each time and prevent silent drift.

### 4.1 PopMenu — viewport-anchored topbar popover

**Pattern**: topbar dropdowns (NotificationsMenu / UserMenu / LanguageMenu / GlobalSearch) use **viewport-anchored fixed positioning**, NOT trigger-anchored Radix-style alignment. This creates a consistent right-gutter chain across all topbar popovers.

**Right-edge offsets** (mockup canonical):
| Popover | `right:` value | Why |
|---|---|---|
| `UserMenu` | `20px` | Rightmost (matches topbar right padding) |
| `NotificationsMenu` | `66px` | Bell-icon area |
| `LanguageMenu` | `138px` | Language toggle area |

**Implementation** (use plain portal, NOT Radix DropdownMenu):

```tsx
'use client';
import { useEffect, useState } from 'react';
import { createPortal } from 'react-dom';

export function TopbarPopover() {
  const [open, setOpen] = useState(false);
  const [mounted, setMounted] = useState(false);

  useEffect(() => { setMounted(true); }, []);

  // Click-outside + Escape close.
  useEffect(() => {
    if (!open) return;
    function handleClick(e: MouseEvent) {
      const t = e.target as Element | null;
      if (!t) return;
      if (!t.closest('.topbar-popmenu') && !t.closest('[data-popmenu-trigger="X"]')) {
        setOpen(false);
      }
    }
    function handleKey(e: KeyboardEvent) {
      if (e.key === 'Escape') setOpen(false);
    }
    document.addEventListener('click', handleClick);
    document.addEventListener('keydown', handleKey);
    return () => {
      document.removeEventListener('click', handleClick);
      document.removeEventListener('keydown', handleKey);
    };
  }, [open]);

  const popover = (
    <div
      className="topbar-popmenu"
      role="menu"
      style={{
        position: 'fixed',
        top: 'calc(var(--topbar-h) - 4px)',
        right: 66,           // adjust per popover identity (20/66/138)
        width: 380,
        background: 'oklch(var(--popover))',
        border: '1px solid oklch(var(--border))',
        borderRadius: 'var(--radius-md)',
        boxShadow: 'var(--shadow-lg)',
        zIndex: 50,
        overflow: 'hidden',
        animation: 'pop-in 0.14s var(--ease)',
      }}
    >
      {/* header / body / footer */}
    </div>
  );

  return (
    <>
      <button
        type="button"
        className="btn btn-ghost btn-icon btn-sm"
        data-popmenu-trigger="X"
        aria-haspopup="menu"
        aria-expanded={open}
        onClick={() => setOpen((o) => !o)}
      >
        <Bell size={15} />
      </button>
      {mounted && open && createPortal(popover, document.body)}
    </>
  );
}
```

**⚠️ Critical anti-pattern — DO NOT use Radix DropdownMenu for topbar popovers**:

Radix wraps content in a Floating UI positioning ancestor with `transform: translate3d(...)`. Per CSS spec, `position: fixed` inside a transformed ancestor anchors to that ancestor's coordinate system, NOT the viewport. Setting `position: fixed; right: 66` on `<DropdownMenuContent>` does NOT produce viewport-anchored layout — it produces transformed-ancestor-anchored layout, which shifts the popover unpredictably (W22 F1 incident `ac75671` → corrected `c3ca1a3`).

**Why viewport-anchored matters**: trigger-anchored alignment (Radix default with `align="end"`) breaks the gutter chain when topbar contents shift — e.g. UserMenu's display-name width varies per user, which pulls every other Radix-aligned popover with it. Viewport-anchored guarantees the right-gutter rail stays consistent.

**Internal popover structure** (header + body + footer):
```tsx
{/* Header: title + subtitle + right action */}
<div style={{ padding: '10px 14px', borderBottom: '1px solid oklch(var(--border))', display: 'flex', alignItems: 'center' }}>
  <div>
    <div style={{ fontSize: 13, fontWeight: 600 }}>Title</div>
    <div className="text-xs muted">Subtitle</div>
  </div>
  <div className="spacer" />
  <button className="btn btn-ghost btn-xs">Action</button>
</div>

{/* Body */}
<div style={{ maxHeight: 420, overflowY: 'auto' }}>...</div>

{/* Footer */}
<div style={{ padding: '8px 14px', borderTop: '1px solid oklch(var(--border))', background: 'oklch(var(--muted) / 0.3)', display: 'flex', alignItems: 'center' }}>
  <span className="text-xs muted">Left text</span>
  <div className="spacer" />
  <Link href="..." className="btn btn-ghost btn-xs">Right action →</Link>
</div>
```

### 4.2 Stepper — 28px circle wizard

Used in `/kb/new` 5-step + `/kb/[id]/upload` 3-step wizards. **Not extracted as a shared primitive** (per W22 F5.3 Rule-of-3 defer — only 2 instances + minor styling drift between them suggests mockup author hand-tuned each).

**Structure**:

```tsx
import { Fragment } from 'react';

const STEPS = [
  { id: 0, label: 'Step name', hint: 'Short description' },
  /* ... */
];

<div className="card" style={{ marginBottom: 16, overflow: 'visible' }}>
  <div style={{ display: 'flex', padding: '18px 24px', alignItems: 'center', gap: 12 }}>
    {STEPS.map((s, i) => (
      <Fragment key={s.id}>
        <div style={{ display: 'flex', alignItems: 'center', gap: 12 }}>
          <div style={{
            width: 28, height: 28, borderRadius: '50%',
            background: step >= s.id ? 'oklch(var(--primary))' : 'oklch(var(--muted))',
            color: step >= s.id ? 'oklch(var(--primary-foreground))' : 'oklch(var(--muted-foreground))',
            display: 'grid', placeItems: 'center',
            fontFamily: 'var(--font-mono)', fontWeight: 600, fontSize: 12,
            border: step === s.id ? '2px solid oklch(var(--accent))' : '0',
          }}>
            {step > s.id ? <Check size={14} /> : i + 1}
          </div>
          <div>
            <div style={{ fontSize: 13.5, fontWeight: step === s.id ? 600 : 500 }}>
              {s.label}
            </div>
            <div className="text-xs muted">{s.hint}</div>
          </div>
        </div>
        {i < STEPS.length - 1 && (
          <div style={{
            flex: 1, height: 1,
            background: step > i ? 'oklch(var(--foreground))' : 'oklch(var(--border))',
          }} />
        )}
      </Fragment>
    ))}
  </div>
</div>
```

**State logic** (mockup canonical):
- `step >= s.id` → completed/active circle (primary bg + light text)
- `step > s.id` → render `<Check>` icon instead of number
- `step === s.id` → add `2px solid accent` border for "current step" emphasis
- Divider line between steps: `foreground` color when completed, `border` color when pending

**Per-step content** uses `<div className="card">` + `.card-header` + `.card-body` + `.card-footer`. Footer typically has:
- Left: "← Back" `<button className="btn btn-ghost btn-sm">` (except step 0)
- Right: "Continue →" `<button className="btn btn-primary btn-sm">` (or "Create" `<button className="btn btn-accent">` on final step)
- Step 0 alternative right: `<div className="text-xs muted mono">Step N of M</div>` + continue button

### 4.3 OptionRow — toggle-row with title/desc/badge/warn

Used in `/kb/new` Step 2 Multimodal for image extraction source toggles.

```tsx
function OptionRow({
  checked, onToggle, title, desc, badge, warn, tier2,
}: {
  checked: boolean;
  onToggle: (v: boolean) => void;
  title: string;
  desc: string;
  badge?: string;
  warn?: string | null;
  tier2?: boolean;
}) {
  const border = tier2 && checked
    ? '1px solid oklch(var(--accent) / 0.4)'
    : checked
      ? '1px solid oklch(var(--foreground) / 0.4)'
      : '1px solid oklch(var(--border))';
  const bg = tier2 && checked
    ? 'oklch(var(--accent) / 0.05)'
    : checked
      ? 'oklch(var(--muted) / 0.5)'
      : 'transparent';
  return (
    <div onClick={() => onToggle(!checked)} style={{
      display: 'flex', gap: 12, padding: '12px 14px',
      border, background, borderRadius: 'var(--radius-sm)', cursor: 'pointer',
    }}>
      <span className="switch" data-on={checked} style={{ flexShrink: 0, marginTop: 1 }} />
      <div style={{ flex: 1 }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: 6, flexWrap: 'wrap' }}>
          <span style={{ fontSize: 13, fontWeight: 500 }}>{title}</span>
          {badge && <span className="badge badge-success" style={{ fontSize: 9.5 }}>{badge}</span>}
          {tier2 && <span className="badge badge-accent" style={{ fontSize: 9.5 }}>TIER 2</span>}
        </div>
        <div className="text-xs muted" style={{ marginTop: 3, lineHeight: 1.5 }}>{desc}</div>
        {warn && checked && (
          <div className="text-xs" style={{
            marginTop: 4, color: 'oklch(var(--warning))',
            display: 'flex', gap: 4, alignItems: 'center',
          }}>
            <TriangleAlert size={11} /> {warn}
          </div>
        )}
      </div>
    </div>
  );
}
```

**Visual states**:
- Unchecked: neutral border, transparent bg
- Checked (Tier 1): foreground/0.4 border, muted/0.5 bg
- Checked (Tier 2 preview): accent/0.4 border, accent/0.05 bg
- Warn (only when checked): amber inline alert below desc

### 4.4 DisabledAffordance — Tier 2 boundary

When a UI surface exists in mockup but the underlying feature is Tier 2 (post-Beta), show it **present-but-disabled** rather than hidden (per ADR-0024 + W19 F5 catalog). This communicates "feature is planned" without functionally enabling it.

**Inline disabled button**:
```tsx
<button
  type="button"
  disabled
  aria-disabled="true"
  className="btn btn-secondary btn-sm"
  title="Tag filtering — pending backend `tags[]` field"
  style={{ opacity: 0.5, cursor: 'default' }}
>
  <Tag size={13} /> Tag: Any
</button>
```

**Per-feature shared component** — use `<DisabledAffordance>` from `frontend/components/ui/disabled-affordance.tsx` for consistent Tier 2 chip + tooltip + accessibility. See W19 F5 27-affordance catalog for full surface inventory.

**Tier 2 chip alone**:
```tsx
<span className="badge badge-accent" style={{ fontSize: 9.5 }}>TIER 2</span>
{/* or in mockup pipeline diagrams: */}
<span className="badge badge-accent" style={{ fontSize: 9, padding: '0 4px', height: 14 }}>T2</span>
```

### 4.5 Modal — `.modal-overlay` + `.modal`

```tsx
<div className="modal-overlay" onClick={(e) => e.target === e.currentTarget && onClose()}>
  <div className="modal modal-lg">
    <div className="modal-header">
      <h2 className="modal-title">Title</h2>
      <p className="modal-desc">Description</p>
    </div>
    <div className="modal-body">
      {/* content */}
    </div>
    <div className="modal-footer">
      <button className="btn btn-ghost btn-sm" onClick={onClose}>Cancel</button>
      <button className="btn btn-primary btn-sm" onClick={onConfirm}>Confirm</button>
    </div>
  </div>
</div>
```

Sizes: `.modal` (default ~560px wide) / `.modal-lg` (720px). Overlay dims background; close-on-overlay-click via target check.

### 4.6 Chunk inspector — `.chunk` + `.chunk-head` + `.chunk-body` + `.chunk-foot`

For retrieval result display (Retrieval Testing tab, Doc Detail inspector pane).

```tsx
<div className="chunk">
  <div className="chunk-head">
    <span className="chunk-rank chunk-rank-top">#1</span>
    <div className="chunk-source">
      <div className="doc-title">D365 F&O GL Configuration v2.4</div>
      <div className="section-path">
        <span>General Ledger</span>
        <span>Setup</span>
        <span>Posting Definitions</span>
      </div>
    </div>
    <div className="chunk-score-wrap">
      <div className="chunk-score">0.94</div>
      <div className="score-bar"><i style={{ width: '94%' }} /></div>
    </div>
  </div>
  <div className="chunk-body">
    {/* text with <mark> highlights */}
  </div>
  <div className="chunk-foot">
    <span className="text-xs muted mono">chunk_84 · page 48</span>
  </div>
</div>
```

`.chunk-rank-top` adds accent tint for top-1 rank. `.score-bar > i` width = score as percentage.

---

## §5 Color semantics

**Critical rule** (per ADR-0015 + W12 D2 user audit): **coral accent is NOT the "selected/active" color**. Coral reads as alarm to many users due to red-orange hue range. Active states use **neutral muted bg + foreground border + check icon** instead.

| Color | Reserved for | DON'T use for |
|---|---|---|
| **Accent (coral 0.65 0.18 25)** | Brand emphasis (primary CTA on auth pages) · Tier 2 preview markers (badges, dashed callouts) · "View latest eval" cite link in answers · focus ring · primary-action emphasis where charcoal feels too dull | "Selected radio card" — use muted/foreground border instead. "INDEXING" status — that's info-blue. Anything "destructive" — that's destructive-red. |
| **Primary (charcoal 0.20 0.01 285)** | Primary CTA bg · nav active rail · brand mark | Selected card border. |
| **Muted + foreground border** | "Selected/active" state of normal radio cards · hover bg · keyboard focus indicator | "Indicates progress" — use accent for that. |
| **Success green** | READY status · completed step · eval pass · BETA DEFAULT chip | "Active step" — use accent border. |
| **Warning amber** | LOCKED · "Re-index needed" · "config affects schema" | Validation errors — that's destructive. |
| **Destructive red** | Real delete actions (button + modal) · actual errors (alert role) · failed status | Locked / disabled — that's warning or muted. |
| **Info blue** | Informational banner · "UI behavior" markers · INDEXING status | Selected state. |

**This rule was applied retroactively** across the prototype after the user flagged red over-use on the New KB wizard. Implementations that copy mockup must preserve this convention.

---

## §6 Interaction state convention

Mockup uses **data-attributes** for visual state (not class toggles), so the same component can statelessly express different states.

| Attribute | Values | Semantics |
|---|---|---|
| `data-active="true"` | `true` / absent | Current selection (seg-btn, tab, nav-item) |
| `data-on="true"` | `true` / absent | Toggle ON (switch component) |
| `data-density="compact"\|"comfy"` | `compact` / `comfy` / absent | Density variant (root-level) |
| `data-sidebar="collapsed"` | `collapsed` / absent | Sidebar collapsed (root-level on `.app`) |
| `data-theme="dark"` | OR use `.dark` class | Dark mode |
| `data-popmenu-trigger="<name>"` | string | Marks topbar dropdown trigger for click-outside exclusion |

**ARIA companion attrs** (always pair with data-attrs for accessibility):
| Pattern | ARIA |
|---|---|
| Switch | `role="switch"` + `aria-checked={value}` + `tabIndex={0}` |
| Seg button | `aria-pressed={isActive}` (or built-in via button + data-active) |
| Tab | `role="tab"` + `aria-selected={isActive}` |
| Popover trigger | `aria-haspopup="menu"` + `aria-expanded={open}` |
| Popover content | `role="menu"` + `aria-label="..."` |
| Disabled affordance | `aria-disabled="true"` + `title` tooltip |

---

## §7 Sync protocol

The design system has 4 source layers that must stay synchronized. When `styles.css` (mockup canonical) updates, the other 3 must follow.

```
┌─────────────────────────────────────────────────────────┐
│  Layer 1 (canonical):                                    │
│    references/design-mockups/styles.css                  │
│    — designer edits here first                           │
└──────────┬──────────────────────────────────────────────┘
           │ verbatim copy (preserve order + comments)
           ▼
┌─────────────────────────────────────────────────────────┐
│  Layer 2 (frontend adoption):                            │
│    frontend/app/styles-mockup.css                        │
│    — copied as-is, no edits except @tailwind directive   │
└──────────┬──────────────────────────────────────────────┘
           │ extract :root CSS vars only
           ▼
┌─────────────────────────────────────────────────────────┐
│  Layer 3 (Tailwind bridge):                              │
│    frontend/app/globals.css                              │
│    — :root declarations with bare L C H, consumed by     │
│      tailwind.config.ts as oklch(var(--token))           │
└──────────┬──────────────────────────────────────────────┘
           │ mirror color tokens (NOT radius/font/etc.)
           ▼
┌─────────────────────────────────────────────────────────┐
│  Layer 4 (TS mirror):                                    │
│    frontend/lib/theming/tokens.ts                        │
│    — colorsLight + colorsDark objects with full          │
│      oklch(...) strings for tailwind config consumption  │
└─────────────────────────────────────────────────────────┘
```

### 7.1 When tokens change (color / radius / font / layout var)

1. **Edit `references/design-mockups/styles.css`** in the `:root` block (or `.dark` block for dark-mode-only changes)
2. **Re-copy** the entire `styles.css` to `frontend/app/styles-mockup.css` (preserve `@tailwind` directives at top of frontend file if any — usually mockup has none, frontend has 3)
3. **If color token changed**: update the bare `L C H` value in `frontend/app/globals.css` `:root` (or `.dark`) block
4. **If color token changed**: update the matching `oklch(...)` string in `frontend/lib/theming/tokens.ts` `colorsLight` (or `colorsDark`) object
5. **Run `pnpm exec tsc --noEmit`** + **`pnpm exec next lint`** + **`Grep '\[oklch' frontend/**/*.{ts,tsx}`** (expect 0 hits — no hardcoded `[oklch(...)]` arbitrary values)
6. **Test dark mode toggle** via theme switcher — verify changed token applies to both modes correctly
7. **If this was a drift repair** (not a planned token change): append a row to §7.3 drift incident log table **in the same commit** — preserves institutional memory
8. **Commit** with message format: `style(tokens): <what changed> — sync styles.css → styles-mockup.css + globals.css + tokens.ts`

### 7.2 When class definitions change (new primitive, modified hover, etc.)

1. **Edit `references/design-mockups/styles.css`** at the class definition
2. **Re-copy** to `frontend/app/styles-mockup.css`
3. **No `globals.css` or `tokens.ts` changes needed** (those layers only carry tokens, not class defs)
4. **If a NEW class is added**, add a row to this doc's §2 primitive index
5. **If this was a drift repair**: append a row to §7.3 drift incident log table **in the same commit**
6. **Commit** with message format: `style(<class>): <what changed> — sync styles.css → styles-mockup.css`

### 7.3 Drift detection (quarterly manual)

Run this diff command quarterly (suggested: end of each quarter or before any major release):

```bash
diff references/design-mockups/styles.css frontend/app/styles-mockup.css
```

**Expected differences** (these are OK):
- `@tailwind base; @tailwind components; @tailwind utilities;` at top of `styles-mockup.css` only (Next.js Tailwind setup, not present in standalone mockup)
- File-end whitespace / line ending differences (CRLF vs LF — Windows checkout)

**Unexpected differences** indicate drift — investigate which side is right (usually mockup, but check git history of both files):
- Different color values → resync per §7.1 step 3-5
- Different class definitions → resync per §7.2
- New class in one side only → propagate to the other + update §2 index

**Drift incident log** (extend with each repair):

| Date | Drift | Direction | Fix commit |
|---|---|---|---|
| 2026-05-18 | `--popover` dark mode `0.20` (globals.css) vs `0.22` (styles.css) | mockup was right | W22 F1 cascade `a385180` |

### 7.4 What NOT to do

- **Never edit `frontend/app/styles-mockup.css` directly** as if it were the source of truth — your change will be lost the next time someone resyncs from `styles.css`
- **Never hardcode color values in components** — always reference via `oklch(var(--token))` (CSS) or token from `tokens.ts` (Tailwind config). The `[oklch(...)]` arbitrary-value pattern in Tailwind is forbidden; `Grep '\[oklch' frontend/**/*.{ts,tsx}` must return 0
- **Never add new tokens to `globals.css` or `tokens.ts` without adding to `styles.css` first** — that breaks the canonical-source chain
- **Never modify mockup canonical for impl convenience** (e.g. "this token would be easier to consume if we renamed it") — mockup is design intent, impl follows

---

## §8 Maintenance checklist

End-of-quarter health check (cadence: every 3 months;**Next due**: `2026-08-18` — set at v1.0 land 2026-05-18 + 3 months). Skip if there's a Beta-cohort expansion or major release within the same quarter — bring the check forward instead.

**Trigger owner**: **Chris** (technical lead). To delegate: assign the run to an AI session by including the §8 checklist in the prompt + the most recent `git log -10 references/design-mockups/` snapshot;the AI returns a pass-fail report and proposes any repair commits;Chris reviews + approves before merge.

**Calendar mechanism**: Chris's choice — `/schedule` skill reminder at `Next due` date, calendar event, or rely on phase F8 closeout self-check (whichever phase first crosses the due date appends "Run §8 health check" to its F8.x acceptance criteria).

**Checklist**:

- [ ] Run §7.3 diff — `diff references/design-mockups/styles.css frontend/app/styles-mockup.css`; investigate any unexpected diff
- [ ] Run `Grep '\[oklch' frontend/**/*.{ts,tsx}` — expect 0 hits; if any, refactor to `oklch(var(--token))` reference
- [ ] Run `pnpm exec tsc --noEmit` — exit 0
- [ ] Run `pnpm exec next lint` — clean
- [ ] Open `references/design-mockups/EKP Platform.html` in browser; click through 5 random routes; verify visual matches `localhost:3001` for same routes
- [ ] Toggle dark mode in browser; verify no color drift between light/dark on same component
- [ ] Review §7.3 drift incident log — append any new repair commits since last check
- [ ] Update this doc's "Last reviewed" line below AND advance the **Next due** date 3 months forward

---

## Cross-references

- [`DESIGN_README.md`](./DESIGN_README.md) — folder overview + how-to-view the prototype + Cn mapping + color semantics origin (ADR-0015 lineage)
- [`PAGE_INVENTORY.md`](./PAGE_INVENTORY.md) — per-route component mapping + Tier 1/2 status
- `frontend/app/styles-mockup.css` — verbatim copy of `styles.css`
- `frontend/app/globals.css` — Tailwind bridge layer
- `frontend/lib/theming/tokens.ts` — TS token mirror
- `frontend/tailwind.config.ts` — Tailwind utility consumption of `tokens.ts`
- `docs/02-architecture/COMPONENT_CATALOG.md` — C01-C13 component spine (this design system serves C09 Admin Console + C10 Chat UI)
- `docs/01-planning/W19-frontend-audit-and-adr-draft/audit/W19-tier2-disabled-affordance-catalog.md` — 27-affordance Tier 2 inventory
- `CLAUDE.md` §5.7 — H7 Design Fidelity Constraint (binding rule that this design system enforces)
- `CLAUDE.md` §3.2.1 — Design Fidelity Rule 7-item checklist (used at every page rebuild)

---

**Last reviewed**: 2026-05-18 (W22 F5b session — initial draft + Wave 3 maintenance executable layer landed `(this commit)`)
**Next quarterly review due**: 2026-08-18 — see §8 for trigger owner + calendar mechanism + delegation handoff
**Owner**: Chris (technical lead — trigger owner) + AI assistants (review runners on user request per CLAUDE.md §5.7 H7);ownership transfer must update this line + §8 trigger owner line
