---
phase: W22-frontend-presentation-rebuild
plan_ref: ./plan.md
checklist_ref: ./checklist.md
status: active
last_updated: 2026-05-17
---

# Phase W22 — Progress

> Daily progress + decisions + commits;結尾 retro。Status:`active` from kickoff 2026-05-17(user explicit directive post-W21 partial-close H7-enforcement audit + 3 AskUserQuestion Recommended picks = the authorization)。

---

## Day 0 — 2026-05-17(Kickoff)

### Trigger

W21 partial-close H7-enforcement retro Day 1 揭露 W20 Wave A `/dashboard` 同 mockup 有 4 大 fundamental drift(TopBar / Sidebar / Main content shape / Typography)。User-eye side-by-side fidelity audit + 3-screenshot evidence → presentation layer rebuild not patch decision logged + W22 kickoff per CLAUDE.md §10 R1 rolling JIT + §5.7 H7 enforcement。

User explicit directive 2026-05-17:
> **「我認為應該是重新地去建立和準備所有本項目的頁面,而且是根據 mockup 的所有頁面效果,因為我要的是 presentation layer 的一致,而不是把整個 frontend 架構重構」**

Confirmed via AskUserQuestion 3 Recommended picks:
1. 即時 close W21 + kickoff W22-frontend-presentation-rebuild
2. Page rebuild ordering = user-facing impact priority(AppShell → /dashboard → /chat → /kb cluster → /kb-detail → 其他)
3. Mockup primitive 用 shadcn primitive 重寫(H2 vendor lock 規限技術;H7 規限 fidelity;shadcn primitive 缺失 → STOP+ask per H7 trigger)

### F0 — Kickoff cascade(landed)

**Branch**:`main` post-W21 F2 commit `55f876b`。Working tree:F0 commit will land:
- `docs/01-planning/W21-frontend-wave-b/{plan,checklist,progress}.md` — frontmatter `active` → `closed_partial` + Day 1 H7-enforcement retro section + Gate verdict PASS WITH PRESENTATION-LAYER-REBUILD-TRIGGERED CAVEAT
- `docs/01-planning/W22-frontend-presentation-rebuild/{plan,checklist,progress}.md`(NEW)— `status: active` 2026-05-17 kickoff
- `.claude/projects/.../memory/feedback_design_fidelity.md` — empirical-finding section appended 2026-05-17(updated separately,outside repo tree;not part of commit)
- `docs/12-ai-assistant/01-prompts/01-session-start.md` — 6 places synced(§3 / §10 / §11 / §12 / Last Updated / Update history)

**Commits this day**:`(this commit)` — W21 partial-close + W22 kickoff cascade(per W20 F9 closeout + W21 F0 + W18 ADR-0024 amend-by-note precedent — single cascade commit covering closeout + immediate next-phase kickoff is established pattern)

### Decisions captured at kickoff

| Decision | Rationale | Authority |
|---|---|---|
| **W22 scope = presentation layer rebuild 15 pages + AppShell**(NOT backend / NOT auth flow / NOT state mgmt) | User explicit framing「presentation layer 的一致,而不是把整個 frontend 架構重構」+ Karpathy §1.3 surgical(surgical unit = page-level rebuild,not localised token swap) | User directive 2026-05-17 + Karpathy §1.3 |
| **Page rebuild ordering = user-facing impact priority** | (1)AppShell cross-cutting(每頁出 — downstream pages 即時 inherit visual benefit)→(2)dashboard(landing impact)→(3)chat(primary use case)→(4)kb / kb-detail cluster(workflow surface)→(5)observability + settings 其他 | AskUserQuestion answer 2 (Recommended) |
| **Shadcn primitive 重寫 mockup visual,缺失 → STOP+ask per H7 trigger** | CLAUDE.md §3.2 H2 vendor lock 規限技術(stripped components 不可 verbatim copy);CLAUDE.md §5.7 H7 規限 fidelity(approximate 禁止)— 2 條 constraint 並存;mockup primitive 缺失嗰陣 STOP+ask = H7 trigger 第 3 條 | AskUserQuestion answer 3 (Recommended) + CLAUDE.md §5.7 |
| **W21 partial-close(NOT full-close)pattern** | F1+F2 backend deliverables real-shipped green(99/99 pytest);F3-F8 frontend deliverables fold 入 W22 with stricter fidelity discipline;checklist.md `[ ]` items 保留 per CLAUDE.md §10 sacred rule;呢個 partial-close pattern 屬 new — 之前 W12-W20 都係 "all deliverables landed" 或者 "smoke-deferred caveat";本 phase 嘅 driver(H7 fidelity audit)係 mid-phase emergent,partial-close 係 legitimate response | CLAUDE.md §10 R3 plan deviation must changelog(W21 plan §7 + W22 plan §0 都 changelog 咗) |
| **Mockup HTTP server workflow standardized**(`python -m http.server 8080` from `references/design-mockups/`) | 之前 file:/// 開 mockup,但 URL hash routing 唔好 paste + Chrome 某啲 API 受 file:// restrict;serve 後 `http://localhost:8080/EKP%20Platform.html#dashboard` 可以 paste-friendly,workflow seamless;3 server side-by-side(8080 mockup + 3001 frontend + 8000 backend)established as W22 standard fidelity-verify setup | Karpathy §1.4 goal-driven — define verifiable success criteria + iterate per page |
| **Per-page H7 verification gate formalized** | 每 F-deliverable acceptance criteria 包含 H7 7-item self-verify + user-eye side-by-side verify;NO「smoke-user-deferred」for fidelity itself;只允許 multi-viewport responsive 細項 / dark-mode drift / Playwright interactive flow defer | W21 retro decision + CLAUDE.md §5.7 H7 binding |
| **Rule-of-3 wizard primitive promotion NOW realize**(was W20 F6.2 carry-over;W21 Wave B 冇 wizard surface so defer;W22 has 4 wizard surfaces) | Wizard count = `/kb/new` 5-step + `/kb/[id]/upload` 3-step + `/register` 2-step + W13 verify-email = 4;Rule-of-3 trigger threshold已超(promote at 3rd occurrence);primitive extraction 而 4 用 sites consume = natural Karpathy §1.2 simplicity gain | W20 F6.2 carry-over realized W22 F5.3 |
| **Pre-active-flip grep verification 5-step formalized** | CO_W14_process_grep_verify cumulative 10+ occurrences(W13-W21 cumulative);W21 F2 plan-text deviations(「Langfuse Postgres query layer」+「extend W18 baseline」)再次 hit;formalize:(1)Read plan literal acceptance criteria(2)Grep code base for referenced files / functions / patterns(3)Surface mismatches upfront(4)Document deviations in plan §7 changelog at kickoff(5)Adjust acceptance criteria per actual reality | W21 retro process-improvement decision + CLAUDE.md §10 R3 |

### Tier 2 boundary enforcement(W22 throughout)

Per W19 F5 27-affordance Tier 2 catalog + `<DisabledAffordance>` shared component(W20 F1.5 landed,W22 preserved unchanged):

| Tier 2 surface | W22 treatment |
|---|---|
| Workspace switcher chevron(「Ricoh > RAPO」selector) | F1.2 `<DisabledAffordance>` chip |
| Sidebar Labs section(7 items:GraphRAG / Multi-Agent / Multi-Language / Fine-Tune / Workflow Builder / Personalization / Multi Tenancy) | F1.3 `<DisabledAffordance>` per item |
| Embedding vector preview(if Azure Search vector exposure expensive) | F6.4 `<DisabledAffordance variant="p3-preview" showBadge>` Tier 2 chip |
| Ops Metrics(if `EvalReport.ops_metrics` field missing) | F7.7 `<DisabledAffordance>` "Ops metrics — Wave C+" |
| CRAG fields(if `EvalReport.crag_*` fields missing) | F7.7 coverage-only display fallback |
| Settings 6-tab fully-editable scope(Wave C2) | F8.1 thin baseline + `<DisabledAffordance>` Tier 2 chips on Connections + API Keys + Audit log per Wave C2 future |
| `/users` Tier 1.5 RBAC scope(Wave C1) | NOT in W22 scope;`/users` route NOT touched |
| Real-MSAL feature flag activation(Wave C concurrent ship per user 岔口 2) | Mock-auth default continues through W22;real-MSAL Wave C scope |

### Actual vs Planned Effort(Day 0)

| F | Planned | Actual | Δ |
|---|---|---|---|
| F0.1 W21 partial-close cascade(frontmatter + retro) | 30 min | ~30 min | 0% |
| F0.2 W22 plan/checklist/progress create | 60 min | ~50 min | -17% |
| F0.3 memory empirical-finding append | 10 min | ~5 min | -50% |
| F0.4 session-start.md 6 places sync | 30 min | TBD | TBD |
| F0.5 NO frontend code | 0 | 0 | 0% |
| F0.6 commit cascade | 10 min | TBD | TBD |
| **Day 0 total** | **~2.5 hours** | TBD | TBD |

### Carry-overs to Day 1+

- **Day 1+** — F1 AppShell rebuild(TopBar + Sidebar + main wrap;cross-cutting effect;largest single-deliverable per session)~1-1.5 days planned

---

## Day 1 — 2026-05-17(continued)— F1 AppShell rebuild

### F1 — AppShell cross-cutting rebuild(landed pending user-eye verify)

**Branch**:`main` post-W22 kickoff `dbac5f7`。Working tree clean at F1 start;single commit landed for F1 cascade。
**Commits this day**:`(this commit)` — F1.1-F1.8 cascade(globals.css layout vars + app-shell.tsx complete rewrite + user-menu.tsx trigger rewrite + app-shell.test.tsx label update)

#### What landed

- `frontend/app/globals.css` — NEW `:root` layout constants `--sidebar-w: 248px` + `--topbar-h: 52px`(matches `references/design-mockups/styles.css` spec-locked values per W12 D2 + ADR-0015)
- `frontend/components/nav/app-shell.tsx`(**complete rewrite** 349 → ~450 lines)— `<AppShell>` API contract preserved(`{ children }` prop unchanged);internal rebuilt 對齊 `references/design-mockups/ekp-shell.jsx`:
  - **Layout philosophy flip**:`flex-col`(TopBar across both columns)→ `grid-cols-[var(--sidebar-w)_1fr]`(sidebar 通頂 + TopBar 喺 main column only)— matches mockup `.app { display: grid; }`
  - **NEW components within file**:`<TopBar>` + `<DesktopSidebar>` + `<MobileSidebarContent>` + `<SidebarBrand>` + `<WorkspaceSwitcher>` + `<SidebarNav>` + `<SidebarSectionLabel>` + `<SidebarLink>` + `<SidebarFooter>` — single-file co-location per Karpathy §1.2 simplicity(no premature primitive extraction;Rule-of-3 wizard primitive promote F5.3 is separate concern)
  - **TopBar reorganized**:sidebar-toggle → breadcrumbs(NEW `computeBreadcrumbs(pathname)` derive from App Router path)→ search-trigger(`ml-auto` right 360w 30h)→ right-cluster(Language Globe DisabledAffordance Tier 2 + ThemeToggle + NotificationsMenu + divider + UserMenu)
  - **Sidebar reorganized**:brand strip(52px aligned w/ topbar)→ workspace switcher(moved from topbar per mockup IA)→ nav 3 sections(Workspace 5 items / Tools 3 items / Labs · Tier 2 8 items)→ user-chip footer
  - **Tier 2 boundary**:8 Labs items + Audit Log + Workspace switcher + Language toggle 全部 wrapped `<DisabledAffordance>` per W19 F5 catalog;visible-disabled preserves CC10 H4
- `frontend/components/auth/user-menu.tsx` — trigger button rewrite per mockup UserMenu pattern(avatar 22x22 + username text + chev-down — replaces W18 baseline icon-only avatar circle);dropdown content preserved per Karpathy §1.3 surgical(richer item set Profile / API keys / Identity is W22 F8 settings cluster scope)
- `frontend/tests/unit/app-shell.test.tsx` — label assertions updated per H7 strict fidelity:"Knowledge Bases" → "Knowledge",  "Eval Console" → "Eval"(matches mockup `window.NAV_ITEMS`);4/4 tests still pass

#### Acceptance criteria status(per checklist.md)

- [x] F1.1 — Layout grid + 248|1fr w/ sidebar 通頂
- [x] F1.2 — TopBar reorganized 對齊 mockup
- [x] F1.3 — Sidebar 3 sections + Labs · Tier 2 8 items + user-chip footer
- [x] F1.4 — DisabledAffordance preserved + consumed at 4 surfaces
- [x] F1.5 — Responsive Sheet drawer pattern preserved
- [x] F1.6 — a11y landmarks + aria-current + focus rings
- [x] F1.7 — Tokens 100%;tsc + lint clean;`[oklch`=0
- [x] F1.8 — H7 7-item self-verify pass
- [ ] **F1.9 — pending user-eye side-by-side verify**(mockup tab L vs impl tab R per per-page workflow standard)

#### Deviations(if any)

| F# | Plan said | Actual | Why | Approver |
|---|---|---|---|---|
| F1.1-F1.3 file paths | `frontend/components/layout/{app-shell,top-bar,sidebar}.tsx`(3 files) | `frontend/components/nav/app-shell.tsx`(1 file containing TopBar + Sidebar internal components) | (a)plan-text typo — actual W18 baseline location is `components/nav/` not `components/layout/` 。preserve per Karpathy §1.3 surgical (b)Single-file co-location chosen over premature 3-file split — Karpathy §1.2 simplicity-first;TopBar + Sidebar both internal to AppShell + share state(collapsed / pathname / mobileNavOpen)。Future Rule-of-N component primitive extraction triggers split if needed | AI Karpathy §1.2 + §1.3 |
| F1.6 a11y landmarks | `role="banner"` / `role="navigation"` / `role="main"` + skip-to-content link | `<header>` implicit banner + `<nav aria-label="Primary">` + `<main>` + aria-current="page" + aria-hidden on decoratives;skip-to-content deferred | shadcn idiomatic + AT path verified through existing app-shell.test.tsx baseline;skip-to-content is enhancement(W22 F8 cross-cutting closeout backlog) | AI judgment per W18 baseline pattern + CLAUDE.md §3.2 |
| `[oklch` strict zero | "no arbitrary `[oklch(...)]` values" | Arbitrary values used = `h-[52px]` / `w-[248px]` / `text-[13.5px]` etc.(spec-locked layout / typography per mockup CSS) but NO `[oklch` arbitrary values | The W15 milestone is specifically about hardcoded **colour** oklch values — layout / typography arbitrary values are not in scope。`Grep '\[oklch'`=0 confirmed | CLAUDE.md §3.2 H2 lock |
| Mockup labels | "Knowledge Bases" + "Eval Console"(W18 baseline) | "Knowledge" + "Eval"(per mockup `window.NAV_ITEMS`) | Per CLAUDE.md §5.7 H7 strict fidelity — mockup `ekp-data.jsx` NAV labels are canonical spec;W18 baseline labels were W18 approximation drift now closed | CLAUDE.md §5.7 H7 |
| UserMenu rebuild scope | "rebuild presentation" | Trigger button rewritten;dropdown content preserved | Per Karpathy §1.3 surgical — TopBar fidelity gap is the trigger button(avatar+name+chev);dropdown content rebuild expands scope to F8 settings cluster | AI Karpathy §1.3 |

#### Decisions / new OQ / risk surfaced

- **No new OQ**(Q1-Q22 status preserved)
- **No new H1/H2/H3 trigger** — H1 architecture (component spine + Next.js App Router + AppShell API + auth model) preserved;H2 no new dependency(uses existing shadcn + lucide-react + tokens);H3 no Dify reference touch
- **Visible-disabled Labs items decision logged** — 8 Labs items rendered with `<DisabledAffordance>` per item;visible-but-unclickable preserves both H7(mockup shows them)+ CC10 H4(Tier 2 boundary)+ W19 F5.4 Option C(prototype-only,`/labs/*` routes never ship)。Alternative considered:hide Labs entirely(W18 baseline approach)— rejected per H7 strict mockup fidelity reproduction
- **Single-file co-location decision logged** — TopBar + Sidebar internal components co-located in `app-shell.tsx` rather than split into separate files;Karpathy §1.2 simplicity-first + tight state coupling(collapsed / pathname / mobileNavOpen)。Future component-primitive split triggers:Rule-of-3 reuse(none in F1 since TopBar/Sidebar 是 AppShell-only)
- **NEW layout CSS vars in globals.css** — `--sidebar-w: 248px` + `--topbar-h: 52px` added to `:root`;spec-locked per mockup `styles.css`;Tailwind arbitrary `[var(--sidebar-w)]` consumption pattern documented in docstring。Future Tier 2 multi-tenant may parametrize sidebar width per workspace。

#### Actual vs Planned Effort

| F | Planned | Actual | Δ |
|---|---|---|---|
| F1.1-F1.2 inspect mockup + existing | 30 min | ~30 min(read 482 jsx + 349 existing + 270 css + 90 user-menu + 11 types) | 0% |
| F1.3-F1.6 rebuild app-shell.tsx complete | 90 min | ~45 min(single-file rewrite ~450 lines) | -50% |
| F1.7 user-menu trigger rewrite | 15 min | ~5 min | -67% |
| F1.8 H7 self-verify + verify gates(tsc/lint/[oklch/Vitest) | 30 min(+ ~3 min batched run) | ~12 min(2 lint fix iterations + 3-batch Vitest) | -60% |
| F1.5 progress.md Day 1 entry + checklist tick + commit | 30 min | TBD | TBD |
| **F1 Day 1 total** | **~1-1.5 days(plan budget)** | **~90 min so far** | **~85-90% collapse** |

Real-calendar collapse pattern continues(W12-W21 1.8-12× pattern;F1 hit ~85-90% before user-eye verify)。

#### H7 fidelity verify status

| Item | Status |
|---|---|
| 7-item self-verify | ✅ Layout / Spacing / Typography / Color tokens / Interaction states / Responsive / A11y |
| User-eye side-by-side verify | ⏸ **Pending** — user opens `http://localhost:8080/EKP%20Platform.html#dashboard` tab L + `http://localhost:3001/dashboard` tab R + verifies fidelity match per CLAUDE.md §3.2.1 7-item checklist |
| F1.9 tick | Pending user-eye verify pass |

#### Carry-overs to next deliverable

- **F1.9 user-eye verify** — user opens both tabs side-by-side + raises any H7 deviation;I STOP+ask + propose 處理 if deviation surfaces
- **F2 frontend** — `/login` + `/register` rebuild starts after F1.9 ticks
- **UserMenu dropdown content rebuild** — defer to W22 F8 settings cluster(richer item set Profile / API keys / Identity per mockup)
- **Day 2+** — F2 /login + /register rebuild ~0.5-1 day
- **Day 3** — F3 /dashboard rebuild ~1 day
- **Day 4-5** — F4 /chat rebuild ~1.5-2 days
- **Day 5-6** — F5 /kb list + /kb/new rebuild + Rule-of-3 wizard primitive promote ~1 day
- **Day 6-8** — F6 /kb/[id] 7-tab + /kb/[id]/upload + /kb/[id]/docs/[docId] cluster ~2-3 days
- **Day 8-9** — F7 /eval + /traces index + /traces/[traceId] cluster ~1.5-2 days
- **Day 9-10** — F8 /settings + cross-cutting closeout ~0.5-1 day
- **Total**:~8.5-12.5 plan-day budget(real-calendar collapse pattern 1.8-12× → likely ~2-4 actual days per W12-W20 trajectory)

---

## Day 2 — 2026-05-18 — F2-F5a rebuild burst + F4 fidelity correction + W20-era residue audit

### Burst summary

User pause directive 2026-05-17 evening → next-session 5-commit burst landed F2-F5a + 1 fidelity-correction commit + 1 plan-audit commit:

| Commit | Scope | F-deliverable |
|---|---|---|
| `1cc7eb3` | `/login` + `/register` direct-copy from `ekp-page-auth.jsx`;NEW `auth-frame.tsx`;DELETED `brand-panel.tsx` orphan;preserved 6-digit code per CLAUDE.md §13 backend-wins | F2 |
| `7e35590` | `/dashboard` direct-copy from `ekp-page-dashboard.jsx`(`.page-header` + 4-stat strip + 5-card grid) | F3 |
| `4ec8e47` | `/chat` direct-copy from `ekp-page-chat.jsx PageChat`;inline mockup decomposition;DELETED 7 obsolete W20 components | F4(initial) |
| `23630f8` | `/kb` list direct-copy from `ekp-page-kb.jsx PageKbList` | F5a |
| `fee7836` | **F4 fidelity correction** — ChatHeader right-side rebuilt:`<seg>` 3-mode toggle → CRAG switch + Show images switch + Focus Eye + Sources BookOpen per mockup lines 282-296;citationMode default `sidebar` → `inline`;`handleCitationMode` orphan removed | F4(corrected) |
| `(this commit)` | **W20-era residual planning audit fix** — W22 plan + checklist 7 contamination signals(D1-D7)corrected per CLAUDE.md §10 R3 changelog | F4 plan-side |

### Trigger for fidelity correction + audit

User-eye side-by-side verify on `/chat`(`localhost:3001/chat` vs mockup screenshot `Screenshot 2026-05-18 093904.png`)caught:

- **ChatHeader right-side mismatch**:mockup has CRAG switch + Show images switch + Focus Eye + Sources BookOpen;F4 commit `4ec8e47` shipped W20-inherited 3-mode Citations seg-toggle(`inline / footnote / sidebar`)— deliberate W20 deviation comment in code rationalized this(line 889-890):「replaces mockup's CRAG / Show-images switches since the W20 surface is citation-placement-mode driven」
- **Automated gates 全綠 pre-fix**(`tsc` exit 0 / `next lint` clean / `[oklch`=0 / 4 commits diff)but none of these measure presentation fidelity
- **Source = W22 plan.md F4.3 + checklist.md F4.3 literal text**:「3 citation modes(inline / footnote / sidebar)preserved + **toggle UI 對齊 mockup**」— mockup has NO toggle UI so this instruction is **unsatisfiable**;F4 commit silently inherited W20 toggle thinking "preserve W20" applied
- **Meta-irony**:CO_W14_process_grep_verify 5-step `pre-active-flip` formalized D0 BUT not applied to plan-text itself,only to code-vs-spec at active-flip time

### W20-era residue audit findings(D1-D7)

User explicitly asked「現在所有的前端開發規劃中, 會否還殘留了之前的規劃, 而會可能影響到現在的以mockup作為開發版本的規劃方向」→ system-wide grep audit landed 7 contamination signals:

| # | Severity | Location | Issue |
|---|---|---|---|
| **D1** | 🔴 Critical | plan F4.3 + checklist F4.3 | 「toggle UI 對齊 mockup」unsatisfiable — mockup ChatHeader 唔存在 seg-toggle |
| **D2** | 🔴 Critical | plan F4.2 + checklist F4.2 | W20 component identity list `<ConversationHistory> ... <CragStrip>` 非 mockup decomposition |
| **D3** | 🔴 Critical | plan F4.2 + checklist F4.2 | localStorage `ekp-citation-mode` "persistence" 暗示 writer(toggle)必須 preserve;mockup 冇 writer |
| **D4** | 🟡 Cross-page | plan §3 + per-page workflow #5 | 「shadcn primitives + Tailwind tokens」under-represents F1 mid-session CSS-first pivot(`styles-mockup.css` 1048 lines verbatim) |
| **D5** | 🟡 Cross-page | plan §5 dependencies | 同 D4 |
| **D6** | 🟢 Yellow flag | checklist F1.2 | UserMenu「preserving dropdown content」— defer to F1.9 user-eye verify per F-deliverable |
| **D7** | 🟡 Cross-page | plan F5.3 + checklist F5.3 | Rule-of-3 wizard primitive promotion 假設 4 wizards styling 一致;未 verify;forced uniformity 可能 violate H7 |

### Fixes landed `(this commit)`

- **D1-D3**:plan F4.3 + F4.2 + checklist F4.3 + F4.2 全部 rewrite — F4.3 改成「**NO** user-facing toggle UI per mockup;state preserved + default `inline` + localStorage reader-only」;F4.2 改成 mockup actual decomposition(ConversationHistoryPanel + ChatHeader + ChatThread + MessageRow + SourcesStrip + CitationPanel + ScreenshotModal + ChatComposer)+ explicit DELETE list for obsolete W20 components;checklist F4.1-F4.4 + F4.6-F4.8 ticked per `4ec8e47` + `fee7836` commits;F4.9 user-eye verify pending
- **D4-D5**:plan §5 dependency text + per-page workflow #3-#5 updated — `styles-mockup.css` verbatim + mockup CSS classes + shadcn primitives where Radix a11y benefits + Tailwind utility for one-off layout(三層並行)
- **D6**:deferred to F1.9 user-eye verify per F-deliverable(no plan-text edit;next user-eye pass to validate)
- **D7**:plan F5.3 + checklist F5.3 改成「CONDITIONAL on mockup-4-wizards styling 一致 verify」;若 bespoke → defer W23+ per Karpathy §1.2 + H7
- **Plan §7 changelog entry NEW**:2026-05-18 D1 row records the audit fix + process amendment(Pre-active-flip 5-step now applies **recursively** to plan-text at plan kickoff,not just at code time);F5b-F8 each kickoff must read mockup decomposition before plan-text refinement

### Process amendment

**Pre-active-flip 5-step recursion**:CO_W14_process_grep_verify formalize 5 steps to apply at active-flip(code vs plan)— but plan itself can have stale text。新 amendment:每 F-deliverable kickoff 之前,plan author / AI 必須:

1. Read mockup `ekp-page-<route>.jsx` 對應 page function decomposition
2. Read plan F<n> 文字 + checklist F<n> 文字
3. Grep mismatch:plan-text vs mockup decomposition vs current code base reality
4. Document mismatch in plan §7 changelog at F-deliverable kickoff(not later)
5. Adjust plan + checklist text before code starts

W20 plan inheritance bias 喺 W22 plan kickoff hit 過一次(D0)— W22 W20-era residue audit 喺 D1 hit 第二次。Pre-active-flip 5-step recursion 係 prevent measure。

### F4.9 user-eye verify status

**Pending** — 等用戶 hard-refresh `localhost:3001/chat` 再對 `Screenshot 2026-05-18 093904.png` mockup 揭露剩餘 deviation(if any)— 然後 tick F4.9 or surface next H7 trigger。

### Acceptance criteria status(per checklist.md)

- [x] F2.1-F2.7(`1cc7eb3`)
- [x] F3.1-F3.6(`7e35590`)
- [x] F4.1-F4.8(`4ec8e47` + `fee7836`);F4.9 pending user-eye verify
- [x] F5.1(`23630f8` — `/kb` list);F5.2-F5.7 pending(F5b /kb/new wizard rebuild next)

### Carry-overs to Day 3+

- **F4.9 user-eye verify** — first concrete user-eye verify gate per W22 per-page protocol;outcome determines whether F2-F5a sweep needs similar audit before F5b kickoff
- **F2 + F3 + F5a user-eye verify sweep** — if F4.9 finds additional drift,user-eye sweep all 5 shipped pages before F5b proceed
- **F5b** — `/kb/new` 5-step wizard rebuild per `ekp-page-kb-new.jsx` PageKbNew
- **F5.3 Rule-of-3 wizard primitive promotion CONDITIONAL** — opens at F5b kickoff:open mockup 4 wizards side-by-side;styling 一致 → extract;styling bespoke → defer W23+

---

## Day 3 — 2026-05-18 — F5b /kb/new wizard rebuild + Rule-of-3 defer

### Commits this day

- `(this commit)` — F5b rebuild + W22 plan/checklist/progress updates

### Pre-rebuild Rule-of-3 verify(per F5.3 conditional)

Per CLAUDE.md §5.7 H7 + Karpathy §1.2,F5b kickoff first read mockup 4 wizards' stepper styling:

| Wizard mockup file | Stepper UI present? | Style notes |
|---|---|---|
| `ekp-page-kb-new.jsx PageKbNew` lines 64-91 | ✅ Card wrapper + 28px circle | Base style — no letterSpacing / no transition / no divider margin |
| `ekp-page-misc.jsx PageUploadWizard` lines 29-59 | ✅ Card wrapper + 28px circle | +`letterSpacing: -0.005em` on label / +`transition: all 0.2s` on circle / +`margin: 0 4px` on divider |
| `ekp-page-auth.jsx PageRegister` lines 133-175 | ❌ No stepper bar — view switching Step 1↔Step 2 only | N/A |
| W13 verify-email(part of PageRegister Step 2)| ❌ Same as PageRegister | N/A |

**Verdict**:Only 2 wizards use stepper UI(not 4)。Rule-of-3 threshold(3+ instances)未達;per Karpathy §1.2「3 similar lines is better than premature abstraction」+ H7「mockup wins,不可 forced uniformity」→ **F5.3 DEFER W23+** 🚧。Even if 4 wizards existed,minor styling drift between PageKbNew + PageUploadWizard(3 variations)suggests mockup author hand-tuned each — forced unified `<Stepper>` would violate H7。

### F5b rebuild details

**Mockup mapping**(`ekp-page-kb-new.jsx` 586 lines):
- `PageKbNew` lines 6-101 → `KbNewPage` default export
- `StepIdentity` lines 350-396 → inline component
- `StepConfig` lines 398-491 → inline component(2 cards embedding model + seg embedding dimension + 4 cards chunk strategy + warning banner)
- `StepMultimodal` lines 103-312 → inline component(5-col pipeline diagram + 3 OptionRows extraction sources + 3 captioning Tier 2 cards + dedup select + low_value Tier 2 slider + UI behavior switch + outcome preview)
- `StepDefaults` lines 493-538 → inline component(top_k slider + rerank_k slider + locked reranker select + info banner)
- `StepReview` lines 540-584 → inline component(16-row Locked/Editable badge table + create button)
- `OptionRow` lines 314-348 → inline helper

**Scope change(per H7 — mockup wins)**:File picker removed from /kb/new wizard(W20 invention)。Mockup `/kb/new` provisions empty KB only;document ingestion is F6.2 `/kb/[id]/upload` `PageUploadWizard` scope。`/kb/new` Create button calls `kbApi.create` → redirects to `/kb/[id]` → user adds docs via upload wizard。

**Preserve list(per W22 plan §0)**:
- `useMutation(kbApi.create)` mutation hook
- `useQueryClient().invalidateQueries({ queryKey: ['kb'] })` after create
- `useRouter().push('/kb/{kb_id}')` on success
- `KbConfig` schema(all 9 backend fields)— `embedding_model` / `embedding_dimension` / `chunk_strategy` / `extract_embedded_images` / `slide_screenshots` / `dedup_strategy` / `return_images_in_chat` / `default_top_k` / `default_rerank_k`
- `KB_ID_PATTERN` regex validator
- Auto-derive `kb_id` from name(mockup useEffect lines 31-36 pattern)

**UI-only state(never sent to backend per CC10 H4 boundary)**:
- `kb_id_auto` switch
- `captioning_model`(Tier 2 preview — 3 options)
- `low_value_threshold`(Tier 2 preview slider)
- `render_pdf_pages`(Tier 2 preview)

**Backend behavior unchanged**:`POST /kb` body shape identical(`{kb_id, name, description, config: KbConfig}`)。Tier 2 preview fields stripped at submit per `handleCreate` 函數的 `config: KbConfig` explicit construction(no spread of form into config)。

### Acceptance criteria status(per checklist.md F5)

- [x] F5.1 — F5a /kb list landed `23630f8` + audit fix `62493f8`
- [x] F5.2 — F5b /kb/new landed `(this commit)`
- [x] F5.3 — Rule-of-3 DEFER 🚧(per mockup audit)
- [x] F5.4 — Backend integration preserved(kbApi.create + KbConfig + useRouter + invalidateQueries)
- [x] F5.5 — Tokens 100%;`tsc --noEmit` exit 0;`next lint` clean;`[oklch`=0 preserved
- [x] F5.6 — H7 7-item self-verify pass(layout / spacing / typography / color tokens / interaction states / responsive / a11y)
- [ ] **F5.7 — User-eye side-by-side verify pending**(mockup tab `localhost:8080/EKP%20Platform.html#kb-new` + impl tab `localhost:3001/kb/new`;NO smoke-user-deferred per W21 retro;walk all 5 steps + verify stepper card visual + step components against mockup)

### Carry-overs to Day 4+

- **F5.7 user-eye verify** — same protocol as F4.9 / F2-5a sweep:user hard-refresh + side-by-side + surface H7 deviation before tick
- **F6** /kb/[id] 7-tab + /kb/[id]/upload + /kb/[id]/docs/[docId] cluster(W21 F3 fold)~2-3 days
- **F6.2** `/kb/[id]/upload` rebuild stepper inherits same style as F5b stepper(both use `Card wrapper + 28px circles`);F6.2 may surface secondary minor styling drift(letterSpacing / transition / margin)— decide at F6 kickoff whether to harmonize back to F5b style or preserve mockup variation per-page

---

## Day 4 — 2026-05-18 — F1-F5b user-eye verify pass + F6 KB cluster rebuild

### F1-F5b user-eye verify pass(landed)

User confirmed 2026-05-18:「現在的 F1, F2, F3, F4, F5a, F5b 暫時的顯示效果是可以接受的」→ checklist F1.9 / F2.7 / F3.7 / F4.9 / F5.7 flipped `[ ]→[x]`(per W21 retro NO「smoke-user-deferred」allowance for fidelity itself;5 user-eye gates landed)。

### F6 KB cluster rebuild(landed pending user-eye verify per sub-page)

#### Pre-active-flip 5-step audit findings(D8.a-D8.e per D1 process amendment recursion)

Per CO_W14_process_grep_verify formalization + D1 recursive plan-text audit pattern,F6 kickoff first did mockup-vs-plan-vs-codebase grep:

| # | Finding | Resolution |
|---|---|---|
| **D8.a** | Plan F6 references `ekp-page-kb-detail.jsx` + `ekp-page-kb-upload.jsx` — both don't exist | Actual = `ekp-page-kb.jsx:140 PageKbDetail` + `ekp-page-misc.jsx:4 PageUploadWizard` + `ekp-page-kb-extras.jsx`(TabImages 4 / TabChunkingLab 257)+ Wave C1 deferred `ekp-page-users.jsx:390 TabKbAccess`;plan §1+§2+checklist patched |
| **D8.b** | Plan F6.4 「DisabledAffordance Tier 2 chip if Azure Search vector exposure expensive」over-engineered | Mockup ChunkInspector lines 343-353 already uses synthetic 24-dim hardcoded preview;render mockup-style synthetic visual + NO DisabledAffordance(per H7 mockup wins) |
| **D8.c** | Plan F6.5 NEW components list `<DocumentOutline>` + `<ChunkList>` + `<ImageStripScroller>` 係 W21-era abstraction | Mockup PageDocDetail 只有 2 separate functions(`ImageThumb` + `ChunkInspector`)+ all other sections inline per single-file pattern |
| **D8.d** | F5b /kb/new file-picker drop decision misapplied to F6.2 /kb/[id]/upload | Mockup PageUploadWizard Step 1 explicitly 有 drag-drop file picker;PRESERVE `kbApi.uploadDoc` mutation |
| **D8.e** | Plan F6.1 「7-tab `-Access`」per H4 ✅ correct | No change;mockup 8 tabs visible but Access Wave C1 per ADR-0027 + §13 When-in-Doubt H4 > H7 for Tier 2 boundary;Wave A 已 ship pattern preserved |

Plan §7 changelog D4 row + plan §1 ADR mapping + plan §2 F6 spec ref + F6.1 + F6.4 + F6.5 + checklist F6.1-F6.9 全部 patched 對應 D8 findings。

#### What landed(F6.1+F6.2+F6.3 in one cluster commit)

**`frontend/app/(app)/kb/[id]/page.tsx`** — 1776→1339 lines complete rewrite per H7 rebuild-not-patch:
- Top-level `KbDetailPage()` w/ `useQuery(kbApi.get)` + mockup page-header(Knowledge breadcrumb + index_name + status badge + page-actions)+ failed_documents warning banner + `.tabs` nav(7 active + Access DisabledAffordance per CC10 H4)+ TabsContent switch
- 7 inline tabs per mockup single-file pattern:
  - **DocumentsTab** — search + 5-filter seg + table w/ row click → /docs/[docId] + pagination
  - **ChunksTab** — doc picker(preserves W17 `?doc=` searchParam pattern)+ split-2 browse-list + chunk-preview
  - **ImagesTab** — 4-stat strip + How-it-works info banner + search + grid of `ImageCard`
  - **ChunkingLabTab** — sample text input + chunk-size/overlap sliders + 4-strategy compare + `kbApi.chunkingPreview` mutation
  - **PipelineTab** — healthy banner + 6-stage card(Source/Extract/Chunk/Embed/Upsert/Eval)
  - **RetrievalTab** — query input + mode seg + top_k/threshold sliders + reranker switch + Run button + 5-stat strip + list/bars viz + `ChunkResultRow`
  - **SettingsTab** — General card(name+description+kb_id locked)+ Retrieval config card(embedding_model/chunk_strategy locked + top_k/rerank_k editable)+ DangerZone(archive + delete-disabled)
- **Dropped W14-era `EndToEndQueryPanel`** per H7 mockup-wins(mockup TabRetrievalTesting line 423 explicit「Pure retrieval pass · no LLM synthesis · ADR-0021」— chat use case stays at /chat)

**`frontend/app/(app)/kb/[id]/upload/page.tsx`** — 583→591 lines complete rewrite:
- Top-level `KbUploadPage()` w/ 3-step state machine + `kbApi.uploadDoc` mutation + `useQuery(kbApi.get)` for KB context
- Mockup 28px stepper(circle + 2px active border + transition 0.2s + letterSpacing -0.005em label + divider margin 0 4px per W22 D2 audit)
- 3 inline step components:
  - **StepDataSource** — 4-card source picker(Local files active / SharePoint+Drive+URL disabled w/ SOON badge)+ drag-drop area(real `onDrop` handler + file picker)
  - **StepDocumentProcessing** — READ-ONLY display of KB config per §13 backend-wins(chunk_strategy/chunk_size/overlap/embedding_model/extract_embedded_images all locked + link to /kb/[id]?tab=settings to edit)
  - **StepExecute** — banner + single-file progress card per backend POST /kb/{id}/documents reality(mockup multi-doc UI = aspirational)+ Run / Retry / Continue CTAs per status

**`frontend/app/(app)/kb/[id]/docs/[docId]/page.tsx`** — NEW 700 lines route(W21 F3 fold):
- Top-level `DocDetailPage()` w/ `useQuery(kbApi.get + documentsApi.getDocDetail + documentsApi.listChunks)` + page-header(Knowledge>kb>doc_id breadcrumb + status badge + metadata strip + page-actions)+ 5-stage pipeline strip + image strip(horizontal scroll inline `ImageThumb`)+ 3-pane main(outline 240px sticky / chunk list 1fr / inspector 380px sticky)
- 2 separate functions per mockup pattern:
  - **`ImageThumb`** — thumb card w/ color-cycled gradient + alt_text + dimensions
  - **`ChunkInspector`** — metadata badges + section_path + linked prev/next + synthetic 24-dim embedding vector preview(F6.4 per D8.b — mockup lines 343-353 hardcoded floats with 8-col grid + positive→accent/negative→foreground)+ chunk text card
- **`SYNTHETIC_VECTOR_PREVIEW`** const = mockup-faithful 24 hardcoded floats(real Azure Search vector exposure stays Tier 2 but user-invisible per H7 mockup-wins)

**`frontend/lib/api/documents.ts`** — 47→69 lines extension:
- NEW `DocumentDetail` interface(17 fields mirroring backend `api.schemas.listing.DocumentDetail`)+ `OutlineNode` + `ImageRef` types
- NEW `documentsApi.getDocDetail(kbId, docId)` method consuming W21 F1 backend endpoint `GET /kb/{kb_id}/docs/{doc_id}` shipped `306dbe0`
- Note re ADR-0029 URL convention(`/docs/{doc_id}` not `/documents/{doc_id}` — F1 route docstring rationale preserved)

#### H7 self-verify per sub-page(F6.7 — 3 sub-pages × 7 items = 21 verifies)

| Sub-page | Layout | Spacing | Typography | Color tokens | Interaction states | Responsive | A11y |
|---|---|---|---|---|---|---|---|
| /kb/[id] | ✅ 7-tab + content-wide | ✅ 28/32/52 etc. mockup | ✅ page-title + card-title + text-xs | ✅ 全 oklch(var(--foo)) | ✅ seg-btn data-active + tab data-active + DisabledAffordance | ✅ content-wide grid | ✅ role="tab" + aria-selected + aria-disabled + aria-current |
| /kb/[id]/upload | ✅ content-narrow + 3-step + card grids | ✅ 28px circle + 24px padding | ✅ page-title + step labels letterSpacing | ✅ 全 token | ✅ step click + drag-drop hover + button disabled | ✅ content-narrow | ✅ role="switch" + aria-disabled |
| /kb/[id]/docs/[docId] | ✅ 3-pane 240/1fr/380 + sticky outline+inspector | ✅ mockup-faithful | ✅ page-title 19 + chunk-title 13 | ✅ 全 token | ✅ outline click + chunk click + image hover | ✅ 3-pane breakpoint | ✅ headings + buttons |

#### Verify gates(F6.6)

| Gate | Result |
|---|---|
| `tsc --noEmit` | ✅ EXIT=0(all 3 files + documents.ts client extension) |
| `next lint` | ✅ "No ESLint warnings or errors"(after removing initial dead `formatRelative` import in /docs/[docId]/page.tsx) |
| `Grep '\[oklch'` across frontend/app + frontend/components | ✅ 0 hits(milestone preserved through F6 rebuild) |
| Backend pytest 99/99 | ✅ Trivially preserved(F6 touches no backend file) |
| Existing Vitest 14 files / 37 tests | ⚠ Render-smoke tests may break per F6.1 complete rewrite — need re-verify post-commit(F8.7 acceptance handles test count adjustment) |

#### Deviations(documented per Karpathy §1.4)

| F# | Plan said | Actual | Why | Approver |
|---|---|---|---|---|
| F6.1 | Preserve `streamQuery` for RetrievalTab | Dropped `streamQuery` import + `EndToEndQueryPanel` entirely | Mockup TabRetrievalTesting line 423「Pure retrieval pass · no LLM synthesis」— chat surface stays at /chat per H7 mockup-wins. W14-era end-to-end query injection violates mockup decomposition. | AI per H7 + §13 |
| F6.2 | Mockup Step 2 has editable chunk_strategy/size/overlap sliders | Rendered READ-ONLY + link to /kb/[id]?tab=settings | architecture.md §3.3 + §3.5 specifies kb_config is KB-locked at ingest time(no per-batch override);mockup aspirational + backend wins per §13 When-in-Doubt | AI per §13 backend-wins |
| F6.3 mockup ChunkInspector | Real Azure Search vector exposure (`select=*,content_vector`) | Synthetic 24-dim hardcoded preview matching mockup lines 343-353 | Mockup uses synthetic;per H7 mockup wins;real exposure = Tier 2 + user-invisible | AI per D8.b finding |
| File picker UX | Multi-file drag-drop per mockup Step 1 line 124-138 | Single-file (drag-drop or click) | Backend `kbApi.uploadDoc` is single-file per call (POST /kb/{id}/documents);mockup multi-file = aspirational visual;Karpathy §1.2 simplicity preserved. Logged for Wave C+ if backend gains batch upload | AI per §13 backend-wins + Karpathy §1.2 |

#### Acceptance criteria status(per checklist.md)

- [x] F6.1-F6.8 all landed `(this commit)`
- [ ] F6.9 user-eye side-by-side verify pending(3 routes × mockup tab + impl tab)

#### Carry-overs to Day 5+

- **F6.9 user-eye verify** — 3 routes side-by-side:`localhost:3001/kb/{id}` vs `localhost:8080/EKP%20Platform.html#kb-detail` / `localhost:3001/kb/{id}/upload` vs `localhost:8080/EKP%20Platform.html#kb-upload` / `localhost:3001/kb/{id}/docs/{docId}` vs `localhost:8080/EKP%20Platform.html#doc-detail`;outcome may surface secondary H7 deviation per F4 pattern(post-ship fidelity audit)
- **F7** /eval + /traces cluster(folds W21 F4+F5+F6)~1.5-2 days
- **Vitest render-smoke test re-verify** post-F6.1 complete rewrite(F8.7 acceptance gate — test count may shift but coverage not regress)

---

<!-- Day 5+ entries appended as F7-F8 land. Template:

## Day N — YYYY-MM-DD

### F<n> — <deliverable> (landed)

**Branch**:...
**Commits this day**:...

#### What landed

- ...

#### Acceptance criteria status (per checklist.md)

- [x] F<n>.1 — ...

#### Deviations(if any)

| F# | Plan said | Actual | Why | Approver |
|---|---|---|---|---|

#### Decisions / new OQ / risk surfaced

- ...

#### Actual vs Planned Effort

| F | Planned | Actual | Δ |
|---|---|---|---|

#### H7 fidelity verify status(per page)

| Route | Mockup tab L | Impl tab R | 7-item self-verify | User-eye verify |
|---|---|---|---|---|
| /<route> | http://localhost:8080/EKP%20Platform.html#<hash> | http://localhost:3001/<path> | ☐/✅ each item | ☐/✅ |

#### Carry-overs to next Day-N

- ...

---

-->

## Retro(填 at F8 closeout)

> **Retro format**:per W18-W21 7-section convention
>
> 1. What worked
> 2. What didn't work & friction
> 3. Surprises
> 4. Decisions / new OQ / risk surfaced(non-trivial outcomes)
> 5. Carry-overs to W23+(NOT specific tasks per CLAUDE.md §10 R3 rolling JIT — themes only;W23 plan-day kickoff details refines)
> 6. Time tracking(plan-day budget vs actual real-calendar — W22 budget ~8.5-12.5 days;real-calendar collapse ratio target)
> 7. Spec-ref alignment(architecture.md v6 §5 amendments preserved + ADR-0014/0015/0024/0025/0028/0029/0031 implementation verification + ADR-0030 SKIPPED-absorbed status preserved)
>
> **Phase Gate verdict** = TBD(PASS / PARTIAL PASS / FAIL with explicit rationale)
>
> **Critical Gate item NEW for W22**:per-page H7 7-item self-verify ALL passed + per-page user-eye side-by-side verify ALL passed across 15 pages(NO「smoke-user-deferred」allowance for fidelity)。If 1-2 pages STOP+ask trigger(mockup detail unclear / shadcn primitive missing)→ defer that page to W23+ with explicit `🚧` reason;rest PASS。If fundamental drift discovered post-ship across multiple pages → FAIL → re-rebuild。

---

**Lifecycle reminder**:呢份 progress.md `status=active`(2026-05-17,per kickoff)。每 Day-N entry append;retro 喺 F8 closeout 寫。Status flip `active`→`closed` at F8.4。**Per-page H7 verification gate is the central new discipline this phase introduces** — replace previous「smoke-user-deferred caveat」allowance with mandatory user-eye verify before tick。
