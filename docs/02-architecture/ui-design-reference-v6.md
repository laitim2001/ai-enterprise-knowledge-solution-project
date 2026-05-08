# EKP UI Design Reference v6 — Visual Identity + 9 Views Layout Atlas

> **Owner**:Chris(Tech Lead)+ AI 助手共同維護
> **Created**:2026-06-10 W12 D2(per W12 plan F2.7-F2.10 deliverable)
> **Spec basis**:`architecture.md` v6 §5(UI Specifications)+ ADR-0014(hybrid auth)+ ADR-0015(UI Tier 1 expansion 9 views)
> **Tokens basis**:`frontend/lib/theming/tokens.ts`(Option C "Warm Charcoal + Coral Accent" ratified W12 D2)
> **Reference policy**:Dify layout patterns reference per ADR-0010 read-only;**NEVER** copy Dify branding / colors / typography(H3 hard constraint)

---

## 1. Visual Identity Decision Summary(W12 D2 ratification)

### 1.1 Color System — Option C "Warm Charcoal + Coral Accent"

**Decision rationale**:
- **Distinct from Dify blue**(achromatic primary 完全不同 category vs Dify hue 240-260)
- **Editorial / content-first vibe**(知識 platform 角色匹配;Notion-leaning aesthetic 適合 D365 F&O ERP user manual context)
- **Warm coral accent**(hue 25)provides personality without overwhelming professionalism

**Light mode swatches**(per `tokens.ts` colorsLight):

| Token | Value | Approx hex | Use case |
|---|---|---|---|
| primary | `oklch(0.20 0.01 285)` | `#2A2730` | Sidebar nav text / primary CTA bg / strong emphasis |
| primary-foreground | `oklch(0.98 0 0)` | `#FAFAFA` | Text on primary CTAs |
| accent | `oklch(0.65 0.18 25)` | `#E97155` | Citation links / action highlights / KB selector hover / active states |
| accent-foreground | `oklch(0.98 0 0)` | `#FAFAFA` | Text on accent surfaces |
| background | `oklch(1 0 0)` | `#FFFFFF` | Page bg |
| foreground | `oklch(0.15 0 0)` | `#181818` | Body text |
| muted | `oklch(0.96 0 0)` | `#F4F4F4` | Card bg / disabled state |
| muted-foreground | `oklch(0.45 0 0)` | `#737373` | Caption / metadata text |
| border | `oklch(0.92 0 0)` | `#E8E8E8` | Subtle borders / dividers |
| ring | `oklch(0.65 0.18 25)` | `#E97155` | Focus ring(matches accent) |
| success | `oklch(0.65 0.16 145)` | `#4FAA4F` | Success toast / index complete |
| warning | `oklch(0.78 0.16 80)` | `#D5A93A` | Warning toast / Beta-only feature |
| destructive | `oklch(0.57 0.22 25)` | `#D04A2C` | Destructive CTA / error toast |

**Dark mode swatches**(inverted-button pattern;warm-neutral dark bg matches primary hue 285 for editorial cohesion):

| Token | Value | Approx hex | Notes |
|---|---|---|---|
| primary | `oklch(0.95 0.005 285)` | `#F1EFF2` | Light warm-neutral(buttons become light bg in dark) |
| primary-foreground | `oklch(0.18 0.005 285)` | `#262328` | Dark text on light buttons |
| accent | `oklch(0.68 0.16 25)` | `#EB7E62` | Slightly brighter coral for dark contrast |
| background | `oklch(0.18 0.005 285)` | `#262328` | Warm-neutral dark(NOT pure black) |
| foreground | `oklch(0.95 0 0)` | `#F0F0F0` | Near-white text |
| muted | `oklch(0.25 0.005 285)` | `#322F35` | Slightly lighter dark surface |
| muted-foreground | `oklch(0.65 0 0)` | `#A3A3A3` | Caption text on dark |
| border | `oklch(0.30 0.005 285)` | `#3D3A40` | Subtle visible border on dark |
| ring | `oklch(0.68 0.16 25)` | `#EB7E62` | Focus ring(matches dark accent) |

**Dark mode toggle mechanism**:CSS class-based(`.dark` on `<html>`)wired through `frontend/app/globals.css` `:root` + `.dark` layers;tokens consume via `oklch(var(--token))` Tailwind config wire。System preference detection + persistence W12 F3 shadcn init phase land(theme provider integration)。

### 1.2 Radius — sharper than Dify default

| Token | Value | Use |
|---|---|---|
| sm | `0.25rem` | Buttons / chips / small badges |
| md | `0.5rem` | Cards / inputs / dropdowns |
| lg | `0.75rem` | Modals / sheets / large containers |

**Spec lock per architecture.md v6 §5.1**(Dify uses 0.5rem default → EKP uses smaller scale for sharper feel)。

### 1.3 Typography — Inter sans + JetBrains Mono

| Family | Stack | Use |
|---|---|---|
| sans | `Inter, system-ui, -apple-system, sans-serif` | Body / heading / UI text |
| mono | `JetBrains Mono, ui-monospace, monospace` | Code / chunk_id / trace IDs / technical params |

**Heading scale**:Tailwind default(`text-xs` 12 / `sm` 14 / `base` 16 / `lg` 18 / `xl` 20 / `2xl` 24 / `3xl` 30 / `4xl` 36)+ shadcn New York convention(headings `font-semibold` for H2-H4,`font-bold` for H1)。

### 1.4 Shadow + Motion — shadcn v0 default

- **Shadow**:`shadow-sm` / `shadow` / `shadow-md` / `shadow-lg`(per `tokens.ts` shadow tokens)
- **Motion durations**:fast 150ms / base 200ms / slow 300ms
- **Ease**:`cubic-bezier(0.4, 0, 0.2, 1)` for all transitions

---

## 2. 9 Views Layout Sketches(low-fi ASCII)

> **Convention**:`█` = primary surface / `▒` = muted bg / `░` = page bg / `─` = border / `[CTA]` = button / `(•)` = icon。Wireframe focus on layout structure NOT visual fidelity(visual fidelity post F3 shadcn install)。

### 2.1 V1 — End User Chat(`/chat`)— per architecture.md v6 §5.2

```
┌─────────────────────────────────────────────────────────────┐
│ EKP  ▼ KB: Drive Manuals                          (•) Chris │ ← Header(border-b)
├─────────────────────────────────────────────────────────────┤
│ ┌─────────┐ ┌────────────────────────────┐ ┌──────────────┐ │
│ │ Sidebar │ │  Chat history(virtualized)  │ │ Citation     │ │
│ │         │ │ ┌──────────────────────┐    │ │ panel        │ │
│ │ + New   │ │ │ User message         │    │ │ (slide-in)   │ │
│ │  chat   │ │ └──────────────────────┘    │ │              │ │
│ │         │ │ ┌──────────────────────┐    │ │ chunk_title  │ │
│ │ History │ │ │ Assistant streaming  │    │ │ doc_title    │ │
│ │  • Q1   │ │ │ ...with [1][2] cite  │    │ │ doc_format   │ │
│ │  • Q2   │ │ └──────────────────────┘    │ │ chunk text   │ │
│ │  • Q3   │ │  └─ Citation card 1         │ │ section_path │ │
│ │         │ │  └─ Citation card 2         │ │              │ │
│ │ Settings│ │       (thumbnail • text)    │ │ [Open Debug] │ │
│ │         │ │                              │ │              │ │
│ └─────────┘ │ ┌──────────────────────────┐│ └──────────────┘ │
│             │ │ Textarea + [Send] (•)Mic ││                  │
│             │ └──────────────────────────┘│                  │
│             │  👍 👎  · Report issue       │                  │
│             └────────────────────────────┘                   │
└─────────────────────────────────────────────────────────────┘
```

**Component inventory**:Sidebar Sheet(mobile) / flat sidebar(desktop) + ChatStream(custom virtualized list) + MessageBubble(custom) + CitationCard(shadcn Card + Dialog modal for thumbnail) + Textarea + Button send + Dropdown KB selector + Avatar user-menu + side Citation Sheet(shadcn Sheet right-aligned)。

**Streaming UX**:Vercel AI SDK `useChat` hook (W11 D2 cont 用 native fetch streaming per Karpathy §1.2 simplicity;Vercel AI SDK NOT wired — preserved per progress.md)。

**Tokens consumed**:`bg-background` / `text-foreground` / `bg-muted`(message bubble alt) / `text-accent`(citation links) / `border-border`(dividers) / `ring-ring`(focus)。

---

### 2.2 V2 — Admin Dashboard(`/admin`)— per architecture.md v6 §5.3 + Dify Image 4 layout reference

```
┌─────────────────────────────────────────────────────────────┐
│ EKP / Admin                       (•) Chris   [Sign out]    │
├─────────┬───────────────────────────────────────────────────┤
│ Sidebar │ Top stats card row                                │
│         │ ┌──────┐┌──────┐┌──────┐┌──────┐                  │
│ ► KB    │ │ Tot  ││ Tot  ││ Tot  ││ Last │                  │
│  Eval   │ │ KBs  ││ Docs ││ Chunks││ Activ│                  │
│  Settings│ └──────┘└──────┘└──────┘└──────┘                  │
│         │                                                    │
│         │ ┌─────────────────────────────────┐                │
│         │ │ Recent ingestion log            │                │
│         │ │ • doc_001 indexed 5m ago        │                │
│         │ │ • doc_002 indexing in progress  │                │
│         │ │ • doc_003 failed parse          │                │
│         │ └─────────────────────────────────┘                │
│         │                                                    │
│         │ Quick actions:                                    │
│         │ [+ Create KB]  [→ Eval Console]                    │
└─────────┴───────────────────────────────────────────────────┘
```

**Component inventory**:AdminShell(custom + shadcn Sheet for mobile) + StatsCardRow(shadcn Card×4) + RecentLog(shadcn Card + ScrollArea) + Button create + Button link。

**Sidebar pattern reference**:Dify `web/app/components/datasets/list.tsx` sidebar layout(LAYOUT ONLY;visual identity 100% EKP per ADR-0010)。

---

### 2.3 V3 — KB List(`/admin/kb`)— per architecture.md v6 §5.4

```
┌─────────────────────────────────────────────────────────────┐
│ EKP / Admin / Knowledge Base                                │
├─────────┬───────────────────────────────────────────────────┤
│ Sidebar │ ┌────────────────────────────┐ [+ Create KB]      │
│         │ │ Search KB...     │ [Sort▼] │                    │
│ ► KB    │ └────────────────────────────┘                    │
│  Eval   │                                                    │
│  Settings│ ┌──────────────┐ ┌──────────────┐ ┌─────────────┐ │
│         │ │ Drive Manuals│ │ (future KB)  │ │ + New KB    │ │
│         │ │              │ │              │ │             │ │
│         │ │ 6 docs       │ │ —            │ │             │ │
│         │ │ 329 chunks   │ │              │ │             │ │
│         │ │ 36 MB        │ │              │ │             │ │
│         │ │ 3 q/day      │ │              │ │             │ │
│         │ │              │ │              │ │             │ │
│         │ │ [Open]       │ │ [Open]       │ │             │ │
│         │ └──────────────┘ └──────────────┘ └─────────────┘ │
└─────────┴───────────────────────────────────────────────────┘
```

**Component inventory**:Card grid(shadcn Card × n + CSS grid)+ Input search + Select sort + Button create。

---

### 2.4 V4 — KB Detail 5-tab(`/admin/kb/[id]`)— per architecture.md v6 §5.5

```
┌─────────────────────────────────────────────────────────────┐
│ EKP / Admin / KB / Drive Manuals                            │
├─────────┬───────────────────────────────────────────────────┤
│ Sidebar │ ┌──────────────────────────────────────────────┐  │
│         │ │ KB header: name + 6 docs · 329 chunks · 36MB│  │
│ ► KB    │ └──────────────────────────────────────────────┘  │
│  Eval   │ ┌─────────────────────────────────────────────┐   │
│  Settings│ │[Documents][Chunks][Pipeline][Retrieve][Set]│   │ ← shadcn Tabs
│         │ └─────────────────────────────────────────────┘   │
│         │ ┌─────────────────────────────────────────────┐   │
│         │ │ Tab content area                            │   │
│         │ │ (per tab content — see §2.4.1-2.4.5)        │   │
│         │ │                                             │   │
│         │ └─────────────────────────────────────────────┘   │
└─────────┴───────────────────────────────────────────────────┘
```

#### 2.4.1 Documents tab — per architecture.md v6 §5.5.1 + Dify Image 4

```
[Search] [Sort▼] [+ Add file] [Metadata]
┌───┬──────────────┬────────┬──────┬────────┬──────────┬─────┬─────┐
│ # │ NAME (•)     │ CHUNK  │ WORDS│ RETR # │ UPLOAD T │STATUS│ ⋯  │
├───┼──────────────┼────────┼──────┼────────┼──────────┼─────┼─────┤
│ 1 │ (•docx) AR   │ Layout │ 12k  │  85    │ 2026-05  │ ✓   │ ⋮  │
│ 2 │ (•docx) AP   │ Layout │ 18k  │  42    │ 2026-05  │ ✓   │ ⋮  │
│ 3 │ (•pdf)  PR   │ Layout │ 8k   │  5     │ 2026-05  │ ⚠   │ ⋮  │
└───┴──────────────┴────────┴──────┴────────┴──────────┴─────┴─────┘
```

**EKP-specific extensions vs Dify Image 4**:format icon column(.docx / .pdf / .pptx)+ embedded images count + failed parse status + error preview。

#### 2.4.2 Chunks tab(Document → Chunks View)— per architecture.md v6 §5.5.2 + Dify Image 5

```
┌──────────────────────────────────────────────────────┐
│ Document: AR_User_Manual.docx                       │
│ 24 CHUNKS · 1018 raw images · 872 unique post-dedup │
└──────────────────────────────────────────────────────┘
┌─────────────────────────┐ ┌──────────────────────────┐
│ Chunk-001 · 412 chars   │ │ Document Information     │
│ Retrieval count: 12     │ │ — Format: docx           │
│ Enabled: [✓] Toggle     │ │ — Pages: 15              │
│ Embedded images: 2      │ │ — Sections: 7            │
│ low_value_flag: false   │ │ — Indexed: 2026-05-04    │
│                         │ │                          │
│ Chunk-002 · 875 chars   │ │ Technical Parameters     │
│ Retrieval count: 5      │ │ — Embedding: 1024d MRL   │
│ ...                     │ │ — Chunker: layout-aware  │
└─────────────────────────┘ └──────────────────────────┘
```

#### 2.4.3 Pipeline tab(Ingestion Wizard)— per architecture.md v6 §5.5.3 + Dify Image 1+6

```
[Step 1: Data Source] → [Step 2: Document Processing] → [Step 3: Execute & Finish]
(•) ─────────────────  ( )                              ( )
ACTIVE                  pending                          pending

┌─────────────────────────────────────────────────────────┐
│ Step 1 — Data Source                                    │
│ ┌─────────────────────────────────────────────────────┐ │
│ │  (•) Drag-drop multi-format upload                  │ │
│ │      .docx / .pdf / .pptx supported                 │ │
│ │  [Browse...]                                         │ │
│ └─────────────────────────────────────────────────────┘ │
│                                            [Continue →] │
└─────────────────────────────────────────────────────────┘
```

**Step indicator**:shadcn Tabs OR custom Step component(borrow Dify Image 1+6 visual pattern;visual identity 100% EKP)。

#### 2.4.4 Retrieval Testing tab — per architecture.md v6 §5.5.4 + Dify Image 2

```
┌─────────────────────────────────────────────────────────┐
│ ( ) Vector Search   (•) Hybrid   ( ) Full-Text          │ ← Radio
│                                                          │
│ Top K: ━━━━●━━━━━━━━ 5     Score Threshold: 0.7         │ ← Slider + Input
│ Reranker: [ Cohere v4.0-pro ▼]                          │ ← Select
│ CRAG enable: [✓ Toggle]                                 │
│ LLM model: [ gpt-5.5 ▼]                                 │
└─────────────────────────────────────────────────────────┘
┌─────────────────┐ ┌──────────────────────────────────────┐
│ Test query:     │ │ Ranked results                       │
│ ┌─────────────┐ │ │ 1. chunk_007 · score 0.92 · doc_001  │
│ │ How do I... │ │ │ 2. chunk_142 · score 0.88 · doc_003  │
│ └─────────────┘ │ │ 3. chunk_055 · score 0.85 · doc_002  │
│ [Search]        │ │ ...                                  │
└─────────────────┘ └──────────────────────────────────────┘
```

#### 2.4.5 Settings tab — per architecture.md v6 §5.5.5

KB-level config:embedding model lock / chunk strategy default / retrieval default / KB description(Form fields per shadcn Form)。

---

### 2.5 V5 — Eval Console(`/eval`)— per architecture.md v6 §5.6

```
┌─────────────────────────────────────────────────────────────┐
│ EKP / Eval Console                                          │
├─────────┬───────────────────────────────────────────────────┤
│ Sidebar │ Top filter bar                                    │
│  KB     │ [ Eval set: v1 (30 queries) ▼] [Run] [Run Single] │
│ ► Eval  │                                                    │
│  Settings│ ┌──────────────┐ ┌──────────────────────────────┐ │
│         │ │ Run config   │ │ 4 metric cards               │ │
│         │ │              │ │ ┌────┐ ┌────┐ ┌────┐ ┌────┐  │ │
│         │ │ LLM:         │ │ │R@5 │ │FFul│ │CRct│ │IAss│  │ │
│         │ │ Reranker:    │ │ │.97│ │.95 │ │.84 │ │.92 │  │ │
│         │ │ Top K:       │ │ │PASS│ │PASS│ │PASS│ │PASS│  │ │
│         │ │ CRAG:        │ │ └────┘ └────┘ └────┘ └────┘  │ │
│         │ │ Intent:      │ │                              │ │
│         │ │              │ │ Failed queries(5)            │ │
│         │ │              │ │ Q14 · OOS refusal · inspect  │ │
│         │ │              │ │ ...                          │ │
│         │ └──────────────┘ │                              │ │
│         │                   │ W4 Reranker Shootout         │ │
│         │                   │ (4-way table + recommendation)│ │
│         │                   └──────────────────────────────┘ │
└─────────┴───────────────────────────────────────────────────┘
```

---

### 2.6 V6 — Debug View(`/debug/[traceId]`)— per architecture.md v6 §5.7

```
┌─────────────────────────────────────────────────────────────┐
│ Trace: 20260605-Q014 · Total 5677ms · $0.0023               │
├─────────────────────────────────────────────────────────────┤
│ ┌────────────────────────────────────────────────────────┐  │
│ │ ▼ Stage 1 — Query Preprocessor              30ms       │  │
│ │   Input: "How do I configure GL account..."            │  │
│ │ ▼ Stage 2 — Hybrid Retrieval                480ms      │  │
│ │   BM25 top 10 + Vector top 10 + RRF fusion             │  │
│ │   Result: 15 unique chunks                             │  │
│ │ ▼ Stage 3 — Reranker (Cohere v4.0-pro)      120ms      │  │
│ │   Top 5 with scores                                    │  │
│ │ ▼ Stage 4 — CRAG Confidence Judge           340ms      │  │
│ │   Score: 0.85 → no re-retrieve                         │  │
│ │ ▼ Stage 5 — LLM Synthesis (gpt-5.5)         4200ms     │  │
│ │   Full prompt: [Expand]                                │  │
│ │   Raw output: [Expand]                                 │  │
│ │ ▼ Stage 6 — Final Response                  10ms       │  │
│ │   1509 chars · 1 citation                              │  │
│ └────────────────────────────────────────────────────────┘  │
│                                                             │
│ [Open in Langfuse →]                                        │
└─────────────────────────────────────────────────────────────┘
```

**Per-stage**:duration / cost / key data preview / expand-collapse / Langfuse link。Implementation uses shadcn Accordion or custom Collapsible primitive。

---

### 2.7 V7 — Landing Page(`/`)— v6 amendment per architecture.md v6 §5.9

```
┌─────────────────────────────────────────────────────────────┐
│ EKP            Features  Pricing  Docs   [Sign in][Get Start]│ ← Header
├─────────────────────────────────────────────────────────────┤
│                                                             │
│       Enterprise Knowledge Platform                         │
│       Get answers from your documents — with citations.    │
│                                                             │
│       [Start asking →]   [Watch demo]                      │ ← Hero CTAs
│                                                             │
├─────────────────────────────────────────────────────────────┤
│ Feature highlights — 3 cards                                │
│ ┌──────────────┐ ┌──────────────┐ ┌──────────────┐          │
│ │ Multi-format │ │ Hybrid       │ │ Citation-    │          │
│ │ ingestion    │ │ retrieval +  │ │ grounded     │          │
│ │ (•docx•pdf•  │ │ CRAG         │ │ answers      │          │
│ │  pptx)       │ │              │ │              │          │
│ └──────────────┘ └──────────────┘ └──────────────┘          │
├─────────────────────────────────────────────────────────────┤
│ How it works(3 step indicator,Dify Image 1 pattern):       │
│  (•) Upload → ( ) Ask → ( ) Verify                          │
├─────────────────────────────────────────────────────────────┤
│ Footer: status / docs / contact / legal                     │
└─────────────────────────────────────────────────────────────┘
```

**Content discipline**:per architecture.md v6 §5.9 — 唔可以 leak Tier 2 / future feature claims(per CLAUDE.md §5.4 H4)。所有 feature claim 必須 ground 在已實 Tier 1 capability。

---

### 2.8 V8 — Login(`/login`)— v6 amendment per architecture.md v6 §5.10

```
┌──────────────────────────────┬──────────────────────────────┐
│ Brand panel(left)            │ Form area(right)             │
│                              │                              │
│  EKP                         │ Sign in                      │
│  Knowledge,                  │                              │
│  on demand.                  │ Email                        │
│                              │ ┌──────────────────────────┐ │
│  (minimal pattern bg)        │ │                          │ │
│                              │ └──────────────────────────┘ │
│                              │                              │
│                              │ Password                     │
│                              │ ┌──────────────────────────┐ │
│                              │ │                          │ │
│                              │ └──────────────────────────┘ │
│                              │                              │
│                              │ [Sign in]                    │
│                              │                              │
│                              │ ── or ──                     │
│                              │                              │
│                              │ [(•) Sign in with Microsoft] │ ← MSAL SSO
│                              │                              │
│                              │ Forgot password? · Register  │
└──────────────────────────────┴──────────────────────────────┘
```

**Auth flow**:per architecture.md v6 §5.10 + ADR-0014 hybrid model — internal staff(Entra ID SSO)+ external partner(self-register email + password)。

**Error states**:invalid cred / unverified email / locked account → backend `error.code` 對應前端 toast(per ApiError envelope §4.5)。

---

### 2.9 V9 — Register(`/register`)— v6 amendment per architecture.md v6 §5.11

```
┌──────────────────────────────┬──────────────────────────────┐
│ Brand panel(left,same V8)    │ Form area(right)             │
│                              │                              │
│                              │ Step indicator:              │
│                              │ (•)─( )─( )                  │
│                              │  1   2   3                   │
│                              │                              │
│                              │ ► Step 1: Account info       │
│                              │                              │
│                              │ Email                        │
│                              │ ┌──────────────────────────┐ │
│                              │ └──────────────────────────┘ │
│                              │                              │
│                              │ Password                     │
│                              │ ┌──────────────────────────┐ │
│                              │ │ ●●●●●●●●                 │ │
│                              │ └──────────────────────────┘ │
│                              │ Strength:━━━━━━━○○○ Strong   │
│                              │                              │
│                              │ Confirm password             │
│                              │ Display name                 │
│                              │                              │
│                              │ [Continue →]                 │
└──────────────────────────────┴──────────────────────────────┘

Step 2: Email verify
  ┌──────────────────────────────────────────────────────┐
  │ Check your inbox at chris@example.com                │
  │ Enter 6-digit code:                                  │
  │ ┌────┬────┬────┬────┬────┬────┐                      │
  │ │    │    │    │    │    │    │                      │
  │ └────┴────┴────┴────┴────┴────┘                      │
  │ [Resend(60s)]                                        │
  └──────────────────────────────────────────────────────┘

Step 3: Welcome
  Account created · [Optional: select first KB] · [Tour CTA] → /chat
```

**Backend dependency**:C13 Email Verification Service(Azure Communication Services per Q22 Resolved 2026-06-10)+ C12 Auth Provider extended(`/auth/register` + `/auth/verify-email` per architecture.md v6 §5.11)。

**Tier boundary**:self-register 屬 Tier 1 v6 amendment scope per ADR-0014;forgot password / 2FA / OAuth provider(Google / GitHub)defer Tier 2(per architecture.md v6 §11)。

---

## 3. Cross-View Consistency Rules

### 3.1 Sidebar pattern

- **Desktop**:flat sidebar persistent on `/admin/*`(width 240px / md / 320px lg via Tailwind responsive)
- **Mobile**:shadcn Sheet from left edge(`<Sheet side="left">`)triggered by hamburger
- **Active state**:`bg-muted text-primary` for selected route(no accent background — accent reserved for action emphasis only)
- **Section dividers**:`border-b border-border` minimal

### 3.2 Breadcrumb pattern

- shadcn Breadcrumb at top of admin views(under header,above content)
- Format:`EKP / Admin / KB / Drive Manuals`(separator `/` 灰色)
- Last segment:`text-foreground font-medium`(non-clickable indicator of current page)
- Earlier segments:`text-muted-foreground hover:text-foreground`(clickable links)

### 3.3 Toast pattern(via shadcn sonner)

- Position:bottom-right desktop / top-center mobile
- Variants:`default` / `success`(success token bg)/ `destructive`(destructive token bg)/ `warning`(warning token bg)
- Auto-dismiss:default 5s / destructive 8s / success 3s
- Action button(optional):"Undo" / "View detail"

### 3.4 Empty state pattern

- 居中 vertical layout:icon(64px muted-foreground)+ heading(text-xl font-semibold)+ subtext(text-muted-foreground)+ optional CTA button
- Examples:"No KB registered yet" / "No queries to show" / "No failed queries" / "No documents uploaded"

### 3.5 Loading skeleton pattern

- shadcn Skeleton primitive(`bg-muted animate-pulse rounded-md`)
- Match shape of incoming content(table rows / card grids / message bubbles)
- Avoid spinner-only patterns(jarring vs Notion-leaning editorial vibe)

### 3.6 Focus + interaction states

- **Focus ring**:`ring-ring ring-offset-2`(coral ring on white bg / coral ring on dark bg per dark mode token)
- **Hover**:opacity 0.9 OR `bg-muted` overlay(non-color shift to preserve brand consistency)
- **Active**(button press):scale 0.98 + brightness 0.95(shadcn default + tokens transition)
- **Disabled**:`opacity-50 cursor-not-allowed`

### 3.7 Spacing rhythm

- Page edge padding:`px-6 md:px-8 lg:px-12`(responsive)
- Section gap:`space-y-8`(major sections)/ `space-y-4`(component groups)
- Card internal padding:`p-4`(sm card)/ `p-6`(default card)/ `p-8`(hero card)

---

## 4. Component-to-View Mapping Table

| shadcn Primitive | V1 Chat | V2 Admin | V3 KB List | V4 KB Detail | V5 Eval | V6 Debug | V7 Landing | V8 Login | V9 Register |
|---|---|---|---|---|---|---|---|---|---|
| **Button** | ✓ Send | ✓ Quick action | ✓ Create | ✓ Tab actions | ✓ Run | — | ✓ Hero CTA | ✓ Sign in | ✓ Continue |
| **Input** | ✓ — | — | ✓ Search | ✓ Search / Form | — | — | — | ✓ Email/Pwd | ✓ All steps |
| **Textarea** | ✓ Chat | — | — | — | ✓ Test query | — | — | — | — |
| **Label** | — | — | — | ✓ Form | ✓ Run config | — | — | ✓ Form | ✓ Form |
| **Select** | ✓ KB | — | ✓ Sort | ✓ Reranker / LLM | ✓ Eval set | — | — | — | — |
| **Switch** | — | — | — | ✓ CRAG / Enable | ✓ CRAG | — | — | — | — |
| **Slider** | — | — | — | ✓ Top K | ✓ Top K | — | — | — | — |
| **Checkbox** | — | — | — | ✓ Filter | — | — | — | — | — |
| **Card** | ✓ Citation | ✓ Stats / Log | ✓ KB card | ✓ Doc info / Tech params | ✓ Metric card | — | ✓ Feature highlight | — | — |
| **Separator** | ✓ Divider | ✓ Section | — | ✓ Tab | ✓ Section | ✓ Stage | ✓ Section | ✓ "or" | ✓ Step |
| **Sheet** | ✓ Citation panel(right) / Sidebar(mobile) | ✓ Sidebar(mobile) | ✓ Sidebar(mobile) | ✓ Sidebar(mobile) | ✓ Sidebar(mobile) | — | ✓ Mobile menu | — | — |
| **Dialog** | ✓ Screenshot modal | — | ✓ Create KB modal(optional) | ✓ Add file / Re-index confirm | — | — | — | — | — |
| **Tabs** | — | — | — | ✓ 5-tab nav | — | — | — | — | — |
| **Badge** | — | ✓ Status | ✓ Doc count | ✓ Status / format | ✓ PASS/FAIL | — | — | — | — |
| **Toast(sonner)** | ✓ Errors | ✓ Operation status | ✓ Operation status | ✓ Re-index complete | ✓ Run done | — | — | ✓ Auth errors | ✓ Verification sent |
| **Skeleton** | ✓ Streaming pre | ✓ Stats loading | ✓ Cards loading | ✓ Tab content loading | ✓ Metric loading | ✓ Stage loading | — | — | — |
| **Dropdown** | ✓ KB selector / User menu | ✓ User menu | ✓ Sort / Filter | ✓ Action menu | — | — | ✓ User menu | — | — |
| **Breadcrumb** | — | ✓ | ✓ | ✓ | ✓ | ✓ | — | — | — |
| **Avatar** | ✓ User menu | ✓ User menu | ✓ User menu | ✓ User menu | ✓ User menu | — | ✓ Header | — | — |
| **Custom Step indicator** | — | — | — | ✓ Pipeline wizard | — | — | ✓ How-it-works | — | ✓ Register wizard |
| **Custom Stage timeline** | — | — | — | — | — | ✓ Trace stages | — | — | — |
| **Custom Code block(JetBrains Mono)** | ✓ Chunk text expansion | — | — | ✓ Chunk preview | ✓ Failed query inspect | ✓ Stage data | — | — | — |

**Total shadcn primitives required**(W12 F3 install scope):**Button / Input / Textarea / Label / Select / Switch / Slider / Checkbox / Card / Separator / Sheet / Dialog / Tabs / Badge / Toast(sonner) / Skeleton / Dropdown / Breadcrumb / Avatar** = **19 primitives**(per W12 plan F3 12-15 base components target — 19 略超出但 Breadcrumb + Avatar + Dropdown 屬 essential cross-view;final list per F3 install phase confirm)。

**Custom components(non-shadcn,EKP-built)**:Step indicator(Register wizard / Pipeline wizard / How-it-works)+ Stage timeline(Debug View)+ Code block(JetBrains Mono mono-font block;wraps `<pre><code>` with theme-aware bg)+ Markdown renderer(for chat assistant rich text + citation footnotes,W13+ scope)。

---

## 5. Dify Reference Path Index

> **Policy reminder per ADR-0010 + CLAUDE.md §5.3 H3**:Dify reference 純 read-only,**NEVER copy-paste / import / replicate Dify branding**。以下 path 標明 layout pattern 借鑒 source 但 EKP visual identity 100% custom。

| EKP View | architecture.md v6 ref | Dify reference path | What to mirror | What NOT to copy |
|---|---|---|---|---|
| V1 Chat | §5.2 | (none — Claude.ai / ChatGPT pattern,not Dify;Dify 唔係 chat tool) | — | — |
| V2 Admin Dashboard | §5.3 | `references/dify/web/app/components/datasets/list.tsx` | Sidebar layout pattern | Dify blue / SF Pro typography / Dify branding |
| V3 KB List | §5.4 | `references/dify/web/app/components/datasets/` (card grid pattern) | Card grid layout | Dify card visual styling |
| V4 KB Detail / Documents tab | §5.5.1 | `references/dify/web/app/components/datasets/documents/list.tsx` (Dify Image 4 base) | Table column layout / row action menu pattern / sort+filter toolbar | All visual identity |
| V4 KB Detail / Chunks tab | §5.5.2 | `references/dify/web/app/components/datasets/documents/detail/` (Dify Image 5 base) | Side panel split layout / chunk list with toggle | All visual identity |
| V4 KB Detail / Pipeline tab | §5.5.3 | `references/dify/web/app/components/datasets/create/` (Dify Image 1+6 wizard) | 3-step indicator + step content frame pattern | Dify card-binary-choice visual styling |
| V4 KB Detail / Retrieval Testing tab | §5.5.4 | `references/dify/web/app/components/datasets/hit-testing/` (Dify Image 2 base) | Slider + numeric input combo / left config + right results split | All visual identity |
| V5 Eval Console | §5.6 | (none direct — Dify lacks dedicated eval console;EKP custom design) | — | — |
| V6 Debug View | §5.7 | (none — vertical timeline pattern is Langfuse-inspired,not Dify) | — | — |
| V7 Landing | §5.9 | (none — Vercel / Linear / Supabase landing aesthetic;Dify 用 marketing site,visual reference 唔同) | — | — |
| V8 Login | §5.10 | (none — Standard SaaS auth split layout pattern;industry-common) | — | — |
| V9 Register | §5.11 | `references/dify/web/app/components/datasets/create/` (Dify Image 1 step indicator pattern) | 3-step wizard step indicator visual rhythm | All visual identity |

**Cross-cutting Dify references**(Dify Image 1+2+4+5+6 source material in architecture.md v6 §5.5.x + §5.8 visual reference quotes):

- Dify Image 1 — Pipeline wizard 3-step → V4.5.3 Pipeline tab + V9 Register wizard
- Dify Image 2 — Retrieval testing slider+input combo → V4.5.4 Retrieval Testing tab + V5 Eval Console run config
- Dify Image 4 — Documents table layout → V4.5.1 Documents tab
- Dify Image 5 — Chunk inspector side-panel split → V4.5.2 Chunks tab
- Dify Image 6 — Step indicator with status badge → V4.5.3 Pipeline tab + V7 Landing how-it-works

---

## 6. Implementation Sequencing(W12-W15 sprint cycle)

| Sprint | View(s) | Status | Notes |
|---|---|---|---|
| **W12** | tokens.ts + admin shell + 8 existing pages tokens migration | 🟢 Active(D2-D5) | F2 ratification 2026-06-10;F3-F4 W12 D3-D5 cycle |
| **W13** | V1 Chat(refactor)+ V7 Landing + V8 Login + V9 Register | ⏳ W13 D1+ | ADR-0014 hybrid auth backend cascade(C13 ACS + C12 extended)前置 |
| **W14** | V2 Admin Dashboard + V3 KB List + V4 KB Detail 5-tab | ⏳ W14 D1+ | Existing barebones implementation 用 5-tab 架構 + tokens migration |
| **W15** | V5 Eval Console + V6 Debug View + responsive + a11y + Playwright E2E + pixel diff baseline | ⏳ W15 D1+ | Polish phase + closeout 4-sprint UI initiative |
| **W16+** | Production launch resume(per W11 plan F1+F2+F3 Track A IT cred event-triggered) | ⏸ Beta deploy | UI sprint cycle 完成 + R-B1 closure trigger |

---

## 7. Maintenance Protocol

| Operation | How |
|---|---|
| **Add new view** | Append to §2 with low-fi ASCII sketch + component inventory + `architecture.md` ref;update §4 mapping table with primitive coverage |
| **Update visual decision**(post-W12 designer pass per Q10 default)| Update §1 swatch table + `tokens.ts` colorsLight/Dark + `globals.css` CSS custom properties;commit message `docs(ui-design): <change>` |
| **Update Dify reference** | Update §5 path index;verify reference still exists at `references/dify/...` (commit pin);add carry-over to W12+ phase plan if changes propagate to wireframes |
| **Update component map** | Update §4 table per shadcn primitive add/remove;sync with `frontend/components/ui/` actual installed list |

**Source-of-truth precedence**(per CLAUDE.md §2 routing + this doc §1.1 lineage):
1. `docs/architecture.md` v6 §5(view spec)
2. ADR-0014 + ADR-0015(scope + amendment trigger)
3. `frontend/lib/theming/tokens.ts`(visual identity values)
4. **This doc**(layout reference + component map)
5. `references/dify/`(layout pattern source — read-only reference)

---

**Doc version**:1.0(2026-06-10 W12 D2 — initial create per W12 plan F2.7-F2.10 deliverable)
**Maintainer**:Chris(Tech Lead)+ AI 助手
