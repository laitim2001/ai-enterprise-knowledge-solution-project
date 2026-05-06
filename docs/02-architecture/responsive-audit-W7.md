---
component: C09-admin-console + C10-chat-interface
status: active
created: 2026-05-15
updated: 2026-05-15
spec_refs:
  - architecture.md §6.1 W7 row — Mobile responsive baseline
  - components/C09-admin-console.md
  - components/C10-chat-interface.md
  - W07-beta-deploy/plan.md §2 F5
---

# W7 Mobile Responsive Audit(F5.1)

> **Lifecycle**:living document — W7 D4 baseline → W7 D5 F5.4 viewport smoke verification → W8 polish

## 1. Tailwind breakpoints used(EKP convention)

| Breakpoint | Min width | Notes |
|---|---|---|
| `sm` | 640 px | Smallest target — phone landscape / small tablet portrait |
| `md` | 768 px | Tablet portrait / small laptop |
| `lg` | 1024 px | Default desktop |
| `xl` | 1280 px | Wide desktop |

## 2. Per-view audit(W7 D4 baseline,4 main views per plan §2 F5.1)

| View | Path | Status | Mobile gaps W7 D4 → fix scope |
|---|---|---|---|
| **KB list** | `/admin/kb` | 🟡 Partial | Sidebar fix-width 224px = 70% of 320px viewport → **F5.2 done**(off-canvas drawer + hamburger);table layout wraps OK |
| **KB detail** | `/admin/kb/[id]` | 🟡 Partial | Inherits admin shell ✅;upload form input touch target OK |
| **Eval Console** | `/eval` | ⏳ Skeleton only | W4 deliverable per architecture.md §5.6;mobile-first design from C04 implementation onward |
| **Chat UI** | `/chat`(not yet built)| ⏳ C10 not started | F5.3 citation card mobile UX deferred until C10 lands(rolling-JIT scope per session-start §3 status)|

## 3. F5.2 hamburger nav implementation(W7 D4 done)

**Component**:`frontend/components/nav/admin-shell.tsx` NEW(client component)

**Behaviour**:
- `< md`(< 768 px):sidebar `fixed inset-y-0 left-0 -translate-x-full`(off-canvas);hamburger button on top header bar toggles `translate-x-0`;dimmed overlay closes drawer on tap
- `>= md`(≥ 768 px):sidebar `static md:w-56 md:translate-x-0` — W2 D5 desktop layout preserved verbatim
- Touch targets:nav links `min-h-[40px]`(per architecture.md §5.10 accessibility recommendation);hamburger button `h-10 w-10`
- Auto-close on nav link tap → user lands on selected route without an extra tap to close drawer
- `aria-expanded` / `aria-label` for screen readers

## 4. F5.3 citation card mobile UX — DEFERRED

**Reason**:C10 Chat Interface UI status `⏳ Not started` per session-start §3;no `<CitationCard>` component exists yet。

**Trigger**:F5.3 acceptance(full-width vs sidebar adjust;screenshot modal mobile-friendly)cascades when C10 Chat lands。Until then no mobile UX surface to polish。

**Action**:once C10 Chat is built, citation card MUST default to:
- `< md`:full-width card list,citation expand/collapse toggle,screenshot modal `max-h-[80vh] w-full`
- `>= md`:sidebar 320 px right rail per architecture.md §5.4 Chat layout

## 5. F5.4 viewport smoke result(W7 D5 — 2026-05-16 PASS)

| Viewport | Width × height | Result | Screenshot |
|---|---|---|---|
| iPhone SE 1st | 320 × 568 | ✅ PASS — sidebar off-canvas + hamburger left + EKP Admin centered + UserMenu right + content full-width + no horizontal scroll;backend 503 surfaces inline error message correctly | [viewport-320-iphone-se.png](./responsive-audit-W7/viewport-320-iphone-se.png)|
| iPhone 13 mini | 375 × 812 | ✅ PASS — identical mobile shell as 320,wider title fits inline | [viewport-375-iphone-13-mini.png](./responsive-audit-W7/viewport-375-iphone-13-mini.png)|
| iPhone 13 | 414 × 896 | ✅ PASS — identical mobile shell pattern | [viewport-414-iphone-13.png](./responsive-audit-W7/viewport-414-iphone-13.png)|
| iPad mini | 768 × 1024 | ✅ PASS — md+ kicks in:persistent sidebar(EKP Admin / Overview / Knowledge Bases / Eval Console)+ desktop top header(UserMenu only)+ no hamburger;hamburger correctly hidden via `md:hidden` | [viewport-768-ipad-mini.png](./responsive-audit-W7/viewport-768-ipad-mini.png)|
| Small laptop | 1024 × 768 | ✅ PASS — W2 D5 baseline desktop layout 完整保留;more horizontal space for content; everything 同 768 一致 | [viewport-1024-desktop.png](./responsive-audit-W7/viewport-1024-desktop.png)|

**Tool**:Playwright MCP automated capture(per session-start §1)。`npm run dev` localhost:3001 + browser_navigate `/admin/kb` + browser_resize 5 widths + browser_take_screenshot。**Backend not running during capture**(no /kb response)— inline "Failed to load KBs" error surfaces F4.2 boundary working as intended;layout-only smoke verifies F5.2 hamburger / sidebar / header behaviour at all 5 widths。

## 6. F5.5 Pixel diff snapshots — DEFERRED W8

**Reason**:no Vitest / Playwright snapshot harness installed yet(per W7 D2 frontend audit — `package.json` has only `lint` + `type-check` + `dev` + `build` + `start` scripts)。Adding snapshot harness = scope creep for W7;defer to W8 polish per W6 C10 plan estimate calibration(static work 0.5x not in budget)。

## 7. Cross-component dependencies

| Component | Mobile-touched W7 D4 |
|---|---|
| C09 Admin Console | `app/admin/layout.tsx` server component thinned;`components/nav/admin-shell.tsx` NEW client shell with hamburger |
| C10 Chat UI | F5.3 deferred — cascades when component lands |
| C11 Identity & Access | `<UserMenu>` already used inside admin shell — works on mobile header ✅ |

## 8. Update history

| Date | Change | Reason |
|---|---|---|
| 2026-05-15 | Initial audit(W7 D4 F5.1)| F5.2 hamburger landed;baseline before W7 D5 F5.4 smoke |
