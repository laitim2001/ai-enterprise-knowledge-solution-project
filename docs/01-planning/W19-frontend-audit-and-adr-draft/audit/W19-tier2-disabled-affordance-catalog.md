---
phase: W19-frontend-audit-and-adr-draft
deliverable: F5
plan_ref: ../plan.md
audit_refs:
  - ./W19-mockup-jsx-audit.md
  - ./W19-backend-gap-map.md
date: 2026-05-16
status: complete
---

# W19 F5 — Tier 2 Disabled-Affordance Catalog

> Per W19 F1 §2.3 leak audit + W19 F4 §6 per-Wave H4 boundary policing。Standardize the disabled-affordance pattern across `frontend/` Wave A–C ships so operators see consistent "coming Tier 2" signaling without confusion or H4 leak。
>
> **Source-of-truth for `frontend/` Wave A-C implementations**:every Tier 2 feature visible in UI MUST use one of the 4 patterns defined in §2 below + carry the right tooltip + respect coral semantics per `DESIGN_README.md` Color semantics。

---

## §1 Enumeration(per F1 §2.3 + per-Wave scope)

### 1.1 Shell-level affordances(Wave A scope)

| # | Affordance | Location | Tier 2 trigger | Wave |
|---|---|---|---|---|
| S1 | Topbar **Language toggle** | `<AppShell>` topbar(per ADR-0024 W18 F1) | i18n machinery — Tier 2 per architecture.md v6 §11 multi-language JP/ZH | Wave A |
| S2 | Topbar **Workspace switcher**(Ricoh · RAPO + ekp-beta.ricoh.com) | `<AppShell>` sidebar brand block | Multi-tenancy — Tier 2 per §11(currently looks enabled in prototype — **F1 audit §2.3 leak** flag) | Wave A — must fix |
| S3 | Sidebar **Audit Log** entry | `<AppShell>` sidebar Tools sub-section | Tier 2 multi-tenancy operations Q12 | Wave A |
| S4 | Sidebar **Labs · Tier 2 section**(8 entries) | `<AppShell>` sidebar bottom | All Tier 2 features per §11 trigger matrix | Wave A — F5.4 routing decision |

### 1.2 Auth flow affordances(Wave A scope)

| # | Affordance | Location | Tier 2 trigger | Wave |
|---|---|---|---|---|
| A1 | Login **"Forgot password?"** link | `/login` form area(per ADR-0014) | Reset password — Tier 2 per §11(prevents email infrastructure complexity Tier 1) | Wave A |

### 1.3 KB cluster affordances(Wave A scope per ADR-0028)

| # | Affordance | Location | Tier 2 trigger | Wave |
|---|---|---|---|---|
| K1 | `/kb/new` Step 3 **Vision captioning** options(GPT-5.5 Vision + Azure Doc Intel) | StepMultimodal captioning_model options | Vision model integration — Tier 2 per §11(needs C? component or large C01 extension) | Wave A |
| K2 | `/kb/new` Step 3 **Render PDF pages** as screenshots | StepMultimodal `render_pdf_pages` OptionRow | Triples ingestion time + Blob cost(currently extract_embedded_images is Tier 1 active) | Wave A |
| K3 | `/kb/new` Step 3 **low_value image filter threshold** | StepMultimodal low_value_threshold slider | Image-level vision classifier — Tier 2(distinct from chunk-level low_value_flag already in code) | Wave A |
| K4 | `/kb/new` Step 3 **Perceptual hash dedup** option | StepMultimodal dedup_strategy select | Perceptual hashing — Tier 2(SHA256 cross-doc dedup is Tier 1 active) | Wave A |
| K5 | `/kb/new` Step 2 **embed-3-small** embedding model option | StepConfig embedding_model card | Tier 2 — faster + cheaper alternative;Tier 1 locked on embed-3-large per Q19 | Wave A |
| K6 | `/kb/new` Step 2 **heading_aware** chunk strategy | StepConfig chunk_strategy card | Tier 2 — NotImplementedError per `ingestion/chunker/strategies.py`(W3+ deferred per ADR-0004) | Wave A |
| K7 | `/kb/[id]` Access tab(per ADR-0025) | KB Detail Access tab | RBAC infrastructure — depends on ADR-0027 Option B+ acceptance | **Wave A disabled affordance until Wave C activates** |

### 1.4 KB Access affordances(Wave C scope per ADR-0027)

| # | Affordance | Location | Tier 2 trigger | Wave |
|---|---|---|---|---|
| KA1 | `/kb/[id]` Access tab **Public visibility** radio | TabKbAccess visibility section | Public KB catalog + anonymous API key — Tier 2 multi-tenancy | Wave C |
| KA2 | `/kb/[id]` Access tab **Anonymous API key** | TabKbAccess(via Public visibility) | Tier 2(per ADR-0026 API Keys Incoming) | Wave C |

### 1.5 /users RBAC affordances(Wave C scope per ADR-0027 Option B recommended)

| # | Affordance | Location | Tier 2 trigger | Wave |
|---|---|---|---|---|
| U1 | `/users` **Power User role**(4th column in matrix + role card) | RolesTab + PERMISSIONS_MATRIX | Advanced retrieval tuning + per-query model picker — Tier 2 per ADR-0024 future evolution | Wave C |
| U2 | `/users` Roles tab **Custom role creation** | RolesTab(absence of "Create role" button per Option B) | Custom roles — Tier 2 governance | Wave C |
| U3 | `/users` **Groups tab** entire | GroupsTab(per Option B minimal RBAC) | Entra Graph SDK + groups sync — Tier 2 | Wave C |
| U4 | `/users` **Audit log tab** entire | AuditTab(per Option B minimal RBAC) | `audit_log` Postgres table + write-on-every-change middleware — Tier 2 | Wave C |
| U5 | `/users` Members tab **role-change action** | UsersTab actions(per Option B read-only listing) | Role edit Tier 2;Tier 1 manages via Entra group membership + invite/suspend only | Wave C |

### 1.6 /settings affordances(Wave C scope per ADR-0026 Option C hybrid recommended)

| # | Affordance | Location | Tier 2 trigger | Wave |
|---|---|---|---|---|
| ST1 | `/settings → Profile` **Edit profile** button | SettingsProfile | Self-edit profile + display name change — Tier 2(avoids Entra ID sync race) | Wave C |
| ST2 | `/settings → Connections` **Edit endpoint/keys/conn-string** fields | SettingsConnections ApiKeyInput per provider | Per Option C hybrid — read-only Tier 1,edit Tier 2;Beta operators rotate via `.env` + Azure Portal | Wave C |
| ST3 | `/settings → Connections` **Rotate secret** button | SettingsConnections per ApiKeyInput | Per Option C hybrid — Tier 2(Key Vault SDK new dep deferred) | Wave C |
| ST4 | `/settings → Connections` **Add provider** button | SettingsConnections(custom integration) | Tier 2 — custom integrations | Wave C |
| ST5 | `/settings → Identity & Auth` **Power User mapping** row | SettingsIdentity role mapping table | Tier 2 — per U1 above | Wave C |
| ST6 | `/settings → Identity & Auth` **Distributed token cache(Redis)** option | SettingsIdentity MSAL token_cache select | Tier 2 — multi-replica MSAL(currently in-memory per-replica is Tier 1) | Wave C |
| ST7 | `/settings → Identity & Auth` **Multi-tenant** sign-in audience option | SettingsIdentity App registration | Tier 2 — multi-tenancy per S2 above | Wave C |
| ST8 | `/settings → Identity & Auth` **MFA all roles** toggle | SettingsIdentity sign-in policy | Tier 2 — MFA for non-admin roles | Wave C |
| ST9 | `/settings → API Keys & Quotas` **Incoming API keys** table entire | SettingsApiKeys | Tier 2 — external integrations(Tier 1 web UI only per ADR-0026) | Wave C |
| ST10 | `/settings → Account` **Delete account** button | SettingsAccount Danger zone | Tier 2 — account deletion(Tier 1 disable via admin) | Wave C |

### 1.7 Chat affordances(Wave A scope per ADR-0031 Option A recommended)

| # | Affordance | Location | Tier 2 trigger | Wave |
|---|---|---|---|---|
| C1 | Chat **Conversation History server-side persistence** | ConversationHistoryPanel privacy notice "localStorage" | Per C10 §7 — server-side persistence Tier 2(localStorage Tier 1 OK per Option A) | Wave A polish — explicit "Beta+ localStorage,Tier 2 server-side persistence" tooltip on history sidebar |
| C2 | Chat **Conversation share via URL** | ConversationHistoryPanel(absence of share action) | Multi-user share + URL share with `conversation_id` — Tier 2 | Wave A |
| C3 | Chat **Voice input + TTS output** | ChatComposer + ChatThread(absence of voice icon) | Web Speech API + Azure CogServ Speech — Tier 2 per Labs /labs-voice | Wave A |

### 1.8 Dashboard affordances(Wave A scope per ADR-0030 absorbed)

| # | Affordance | Location | Tier 2 trigger | Wave |
|---|---|---|---|---|
| D1 | `/dashboard` Quick Actions **API access** button | QuickActionsCard | Tier 2 — per ST9 Incoming API keys | Wave A |

---

## §2 Per-affordance handling pattern spec

4 patterns + selection criteria:

### 2.1 Pattern P1 — Native `disabled` + tooltip(strongest signal)

**When to use**:feature is genuinely unavailable;no Tier 1 substitute;operator MUST defer to Tier 2 or external workflow

**Implementation**:
```tsx
<button disabled aria-label="..." title="Multi-language (JP / ZH) — coming in a later tier">
  <Icon className="muted" />
</button>
```

**Examples**:S1 Language toggle / A1 Forgot password / K1-K4 Multimodal Tier 2 options / KA1 Public visibility radio / KA2 Anonymous API key / U2 Custom role creation / U5 role-change action / ST1 Edit profile / ST3-ST4 Rotate/Add provider / ST5-ST8 Identity Power User+Redis+Multi-tenant+MFA / ST10 Delete account

**a11y**:native `disabled` is the strongest "unavailable" signal — AT removes from tab order;`aria-label` + `title` carry the explanation

### 2.2 Pattern P2 — `aria-disabled` + click-intercept toast(softer signal)

**When to use**:feature is currently disabled but operator might want to know "what would happen if enabled" — toast can offer "Learn more" or "Tier 2 governance"

**Implementation**:
```tsx
<button aria-disabled="true" onClick={() => toast.info("Tier 2 — TBD post-Beta governance")} className="opacity-60">
  ...
</button>
```

**Examples**:rarely used — most Tier 2 disables are "P1 strongest" per consistency with prototype。Could apply to D1 API access if "Learn more" link to Labs `/labs-personalization` desired。

### 2.3 Pattern P3 — Coral "TIER 2" badge + present-but-noninteractive(preview signal)

**When to use**:feature is **previewed**(shown in UI for awareness)but not yet implemented;coral accent signals "this is coming"

**Implementation**:
```tsx
<div className="opacity-60 cursor-default">
  <span>Feature label</span>
  <span className="badge badge-accent">TIER 2</span>
  <div className="text-xs muted">{description}</div>
</div>
```

**Examples**:U1 Power User role row / K3 low_value threshold slider with "TIER 2" badge / U3 Groups tab content / U4 Audit log tab content / ST9 Incoming API keys table

**Coral semantics guard**:**Coral is reserved for Tier 2 preview + brand emphasis ONLY** per `DESIGN_README.md` Color semantics — do NOT use coral for "selected/active" states of normal radio cards(too alarm-like)。Always check coral usage against:(a) preview elements + (b) brand accent + (c) destructive(red — distinct from coral)

### 2.4 Pattern P4 — Route hidden from sidebar(Labs-style)

**When to use**:entire route is Tier 2;visible navigation entry would mislead — better to not list

**Implementation**:`<AppShell>` sidebar nav array filtered by `NEXT_PUBLIC_TIER2_PREVIEW_ENABLED` env flag,or hardcoded `false` for `frontend/` Wave A ship。Labs routes accessible only via direct URL(prototype demo)or feature flag flip(future)

**Examples**:S4 Sidebar Labs section(if F5.4 picks Option C — recommend)

**Note**:不同 P1-P3,P4 prevents access entirely — no badge,no tooltip,no awareness。Reserved for cases where Tier 2 surface might confuse Tier 1 operators(e.g. GraphRAG / Multi-Agent / Fine-Tune are distracting if Tier 1 doesn't even support them yet)

---

## §3 Coral semantics enforcement(per `DESIGN_README.md`)

**Coral accent `oklch(0.65 0.18 25)` reserved for**:
- ✅ Brand emphasis(CTAs in auth flow brand panel + selected nav-item `::before` strip per ADR-0015 W12 D2)
- ✅ Tier 2 preview elements(P3 pattern above + Labs gradient banner)
- ✅ Citation pill badge in chat(per `ekp-page-chat.jsx CitationPill`)
- ❌ **NOT for "selected/active" state of normal radio cards / segment buttons**(use neutral muted bg + foreground border + check icon — per K5 K6 K7 active state pattern)
- ❌ **NOT for destructive actions**(use red `oklch(0.57 0.22 25)` — different hue)
- ❌ **NOT for warning states**(use yellow `oklch(0.78 0.16 80)`)
- ❌ **NOT for informational banners**(use blue `oklch(0.62 0.13 240)`)

**Wave A audit checklist**(per F5 catalog):
- Grep `frontend/` for `var(--accent)` usage on interactive elements;flag any `cursor: pointer` + `var(--accent)` combo for review(might be misusing coral as active state instead of selected check icon)
- Native `disabled` + `aria-label` + `title` consistency check on Tier 2 patterns(P1)
- "TIER 2" badge text consistency:always use `<span class="badge badge-accent">TIER 2</span>` not "T2" abbreviation(except sidebar Labs nav-tail which uses "T2" per prototype line 321 — small space)

---

## §4 `<DisabledAffordance>` shared component sketch(implementation spec)

To enforce consistency,Wave A implements a shared component encapsulating the 3 main patterns(P1 + P2 + P3 — P4 is route-level not component-level):

```tsx
// frontend/components/ui/disabled-affordance.tsx
import { Badge } from "@/components/ui/badge";
import { cn } from "@/lib/utils";
import type { ReactNode } from "react";

export type DisabledAffordanceProps = {
  /** P1 (default) | P3 (preview with TIER 2 badge) */
  variant?: "p1-strict" | "p3-preview";
  /** Tooltip text */
  reason: string;
  /** Tier 2 trigger note(shown via title attribute)*/
  tier2Trigger?: string;
  /** P3 only — explicit "TIER 2" badge placement */
  showBadge?: boolean;
  className?: string;
  children: ReactNode;
};

export function DisabledAffordance({
  variant = "p1-strict",
  reason,
  tier2Trigger,
  showBadge = false,
  className,
  children,
}: DisabledAffordanceProps) {
  const title = tier2Trigger ? `${reason} · ${tier2Trigger}` : reason;
  return (
    <span
      role={variant === "p3-preview" ? "img" : undefined}
      aria-disabled="true"
      aria-label={title}
      title={title}
      className={cn(
        variant === "p1-strict" ? "opacity-60 pointer-events-none" : "opacity-75",
        "inline-flex items-center gap-2",
        className,
      )}
    >
      {children}
      {showBadge && (
        <Badge variant="outline" className="bg-accent/12 text-accent border-accent/30">
          TIER 2
        </Badge>
      )}
    </span>
  );
}
```

**Usage**:

```tsx
// S1 Language toggle (P1 strict)
<DisabledAffordance reason="Multi-language (JP / ZH) — coming in a later tier">
  <button disabled aria-label="Language" className="...">
    <Languages className="h-4 w-4 muted" />
  </button>
</DisabledAffordance>

// U1 Power User role row (P3 preview)
<DisabledAffordance variant="p3-preview" reason="Advanced retrieval tuning + per-query model picker" tier2Trigger="Tier 2 — post-W12 governance" showBadge>
  <span className="badge badge-muted">Power User</span>
</DisabledAffordance>
```

**Tier 2 catalog enforcement**:every disabled affordance in `frontend/` Wave A-C ships consume `<DisabledAffordance>` instead of inline `disabled`+`title` to:
- Ensure consistent tooltip + ARIA pattern
- Centralize "TIER 2" badge styling
- Make per-affordance auditing easier(grep `<DisabledAffordance` to find all Tier 2 surfaces)

---

## §5 F5.4 — `/labs/*` routing decision

3 options:

### Option A — Labs visible in `<AppShell>` sidebar "Tier 2 Preview" section

- Labs section visible in sidebar(per prototype `ekp-shell.jsx` lines 302-324)— 8 entries with `T2` tail badge
- All roles can see + navigate;each Lab page shows "NOT IMPLEMENTED" banner
- Pros:operators aware of Tier 2 roadmap + can preview before governance
- Cons:adds nav clutter;may confuse less-technical operators

### Option B — Labs feature-flag-gated

- `NEXT_PUBLIC_TIER2_PREVIEW_ENABLED` env flag controls Labs section visibility
- Default `false` for production;dev / staging set `true`
- Pros:operators see Labs only on environments where useful
- Cons:flag management overhead

### Option C — Labs prototype-only,never ship `frontend/`(**RECOMMENDED**)

- `frontend/` Wave A sidebar **does NOT include Labs section**;Labs pages exist only in `references/design-mockups/`(prototype reference for governance)
- Pros:cleanest Tier 1 ship + zero clutter + zero implementation cost;Tier 2 promotion path = governance Q12 picks specific Lab → new W-phase implements that Lab as active feature(not "promotion of preview")
- Cons:operators don't see Tier 2 roadmap in UI(but `architecture.md v6 §11 + COMPONENT_CATALOG.md §6` are the Tier 2 roadmap documentation;UI不負責 roadmap surface)

**Recommended pick**:**Option C** for Tier 1 ship。Tier 2 governance Q12 trigger creates new W-phase for specific Lab promotion(not "Labs section gets activated")。

### F5.4 Wave A action

- Update `<AppShell>` sidebar nav to NOT include Labs section per Option C
- Document in `frontend/components/nav/app-shell.tsx` why Labs section is omitted("Labs is `references/design-mockups/` reference;Tier 2 governance Q12 — specific Lab → new W-phase")
- F1 audit §2.3 leak(Sidebar Workspace switcher)separately fixed in Wave A polish per F4 §1.1 Topbar polish line item

---

## §6 Implementation enforcement(Wave A-C audit hook)

**Wave A acceptance criterion**(per F4 §1.4):
- Grep `frontend/` for `disabled` attribute on interactive elements → confirm all have `aria-label` or `title` per P1 pattern
- Grep `frontend/` for `<DisabledAffordance` count(per `tests/unit/`)→ should match catalog count(after Wave A polish — ~10 affordances visible Wave A scope)

**Wave C acceptance criterion**:
- Wave C ship 7-tab(`-Access`)→ 8-tab(`+Access`)transition per ADR-0025 hard dep on ADR-0027 Option B
- `/users` Members tab read-only listing + invite + suspend only(per ADR-0027 Option B)— no role-change action UI shipped Tier 1

---

**Next deliverable**:F6 Closeout — phase Gate verdict + retro + ADR Status flips + session-start.md hygiene + W20+ kickoff trigger(awaits Chris approval at F6 review session)
