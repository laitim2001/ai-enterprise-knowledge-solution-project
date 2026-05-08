---
phase: W12-ui-foundation-discovery
plan_ref: ./plan.md
status: closed
last_updated: 2026-06-10
---

# Phase W12 — Checklist

> Atomic checkbox(每 item ≤ 0.5–2 hour effort per W6 C10 calibration)。
> Status:`closed` 自 2026-06-10 night cont 3 W12 D5 closeout(Phase Gate PASS WITH F4.13 USER-DEFERRED CAVEAT verdict per progress.md retro § F5.1)。

## F1 — Q22 email vendor decision + W12 phase plan validate

- [x] F1.1 Q22 added to `decision-form.md` Section 1(Stakeholder Decisions)— Question / Why it matters / Default if unanswered / Decision pending fields populated per existing Q1-Q21 pattern ✅ W12 D1(2026-06-10 evening)
- [x] F1.2 Q22 trade-off table populated:Azure Communication Services vs SendGrid(billing / SDK maturity / verification token flow / email deliverability / monthly volume cap / cost per 1k email)✅ W12 D1 — 8-row trade-off table embedded in decision-form.md Q22 entry
- [x] F1.3 Q22 default-if-unanswered = Azure Comm Service rationale documented(per ADR-0014 + spec §13 Azure-native preference per CLAUDE.md §5.2 H2)✅ W12 D1 — 3 anchors per Q22 entry decision rationale(Azure-native billing integration + Python SDK asyncio + ADR-0014 default consistency + CLAUDE.md §5.2 H2)
- [x] F1.4 Q22 Resolved by W12 D2(stakeholder approve OR default activate per timing)✅ W12 D1 — early default activation per User-as-Stakeholder same-session pattern Q7+Q9+Q10+Q11+Q12 W6 D5 cycle 重複(2026-06-10 evening)
- [x] F1.5 architecture.md v6 §3 amendment — add C13 Email Verification Service component card per Q22 outcome ✅ W12 D1 — `docs/architecture.md §3.7 C13 Email Verification Service`(vendor + SDK + cost model + integration pattern + tier boundary + RISK_REGISTER cross-ref)+ §13.12 Cross-references row added
- [x] F1.6 W12 plan.md `status: draft → active` flip — based on(a) W11 D5 closeout PASS sign-off(b) Q22 Resolved(c) Stakeholder ack 2026-06-10 final sign-off ✅ W12 D1 — 三條件全 cleared(W11 PARTIAL PASS commit `4ec56d5` + Q22 default activated + Stakeholder authorization 2026-06-10 evening session);plan + checklist + progress.md frontmatter `draft → active`

## F2 — Visual identity tokens.ts finalize + design reference doc

- [x] F2.1 `frontend/lib/theming/tokens.ts` populate:colors object — light + **dark** variants(11 entries each;Option C "Warm Charcoal + Coral Accent" + dark mode parallel implement override)✅ W12 D2(2026-06-10)
- [x] F2.2 `frontend/lib/theming/tokens.ts` populate:radius object(sm 0.25 / md 0.5 / lg 0.75rem)✅ W12 D2 — preserved per spec lock
- [x] F2.3 `frontend/lib/theming/tokens.ts` populate:fontFamily object(Inter sans + JetBrains Mono with system fallback chain)✅ W12 D2 — preserved per spec lock
- [x] F2.4 `frontend/lib/theming/tokens.ts` populate:spacing(Tailwind default reference comment)+ shadow(sm / DEFAULT / md / lg per shadcn v0)+ motion tokens(duration fast/base/slow + ease cubic-bezier)✅ W12 D2
- [x] F2.5 AI propose visual decisions doc — 3-option proposal via AskUserQuestion(monospace previews):Forest Teal / Indigo-Plum / **Warm Charcoal+Coral**;dark mode strategy binary(defer W15 / start W12 D4)✅ W12 D2
- [x] F2.6 User approve cycle 1 — Option C ratified + dark mode parallel implement override(progress.md Day 2 entry record approval)✅ W12 D2(2026-06-10 evening cont)
- [x] F2.7 Design reference doc `docs/02-architecture/ui-design-reference-v6.md` create:9 views layout sketches(low-fi ASCII per architecture.md v6 §5.2-§5.11)✅ W12 D2 — V1 Chat / V2 Admin / V3 KB List / V4 KB Detail 5-tab(2.4.1-2.4.5)/ V5 Eval / V6 Debug / V7 Landing / V8 Login / V9 Register
- [x] F2.8 Design reference doc — §3 cross-view consistency rules(sidebar / breadcrumb / toast / empty state / loading skeleton / focus + interaction states / spacing rhythm)✅ W12 D2
- [x] F2.9 Design reference doc — §4 component-to-view mapping table(19 shadcn primitives × 9 views matrix + 4 custom EKP-built components)✅ W12 D2
- [x] F2.10 Design reference doc — §5 Dify reference path index(per architecture.md v6 §5.5.1-§5.5.5 + §5.8 + §5.9-§5.11;layout source + NEVER copy visual identity per ADR-0010)+ §6 W12-W15 implementation sequencing + §7 maintenance protocol ✅ W12 D2

## F3 — shadcn/ui foundation setup + 12-15 base components(actual 19 per design ref §4 — scope adjusted)

- [x] F3.1 ~~`pnpm dlx shadcn@latest init`~~ → **manually written `frontend/components.json`**(sidesteps interactive Q&A;matches existing tokens.ts + globals.css + tailwind.config.ts integration setup landed F2)✅ W12 D3
- [x] F3.2 `frontend/components.json` 配置(New York + Tailwind CSS variables + cssVariables true + lucide icon library)→ tracked in git ✅ W12 D3
- [x] F3.3 Form primitives install(8):Button、Input、Textarea、Label、Select、Switch、Slider、Checkbox ✅ W12 D3 — 全部 in `frontend/components/ui/`
- [x] F3.4 Layout primitives install(5):Card、Separator、Sheet、Dialog、Tabs ✅ W12 D3
- [x] F3.5 Feedback primitives install(3):Badge、Sonner(toast)、Skeleton ✅ W12 D3
- [x] F3.6 Nav primitives install(2):Dropdown-menu、Breadcrumb ✅ W12 D3 — 兩個 shadcn 支援都有
- [x] F3.6.1 **🆕 Identity primitive install(1)**:Avatar — 補加 per design ref §4 mapping table(V1/V2/V3/V4/V5/V7 user-menu cross-view essential)✅ W12 D3 — scope adjustment 由 plan F3 12-15 target → actual 19 per design ref doc authoritative count
- [x] F3.7 全部 shadcn components 在 `frontend/components/ui/`(19 files)+ tokens.ts 整合 via Tailwind CSS variable layer 驗證:**6 missing tokens 補齊** post-install audit(secondary / card / popover token pairs;shadcn components reference 但 F2 baseline 未 wire)→ globals.css :root + .dark + tailwind.config.ts colors mapping + tokens.ts colorsLight/Dark documentation 三 files 同步 update ✅ W12 D3
- [x] F3.8 Smoke verify:`app/admin/page.tsx` 用 `<Button asChild>` wrap 「Manage KBs →」link(替換 hardcoded `bg-[oklch(0.42_0.04_260)]` Link)— 順便 F4 page tokens migration head-start;import resolves clean ✅ W12 D3
- [x] F3.9 Type-check pass(`pnpm type-check` clean — 0 shadcn-introduced TS error)✅ W12 D3 — first run 撞 `as const` readonly array vs Tailwind mutable expectation conflict in tokens.ts fontFamily;remove `as const` 一行 fix → 0 errors final;initial 19 component install 100% TS-clean

## F4 — Admin shell foundation + existing pages tokens migration

- [x] F4.1 `frontend/components/nav/admin-shell.tsx` rebuild w/ shadcn primitives:sidebar nav using `Sheet`(mobile)+ flat sidebar(desktop)✅ W12 D4 — Sheet trigger + SheetContent(left side)+ flat sidebar md+ + responsive layout
- [x] F4.2 admin-shell header w/ breadcrumb + user-menu(reuse `auth/user-menu.tsx`,wrap in shadcn `Dropdown`)✅ W12 D4 — Breadcrumb auto-derive from `usePathname()` + 6 segment label mapping(admin/kb/eval/debug/new/upload)+ dynamic segment truncation;UserMenu rebuilt with `DropdownMenu` + Avatar(initials fallback)+ DropdownMenuLabel/Separator/Item LogOut icon
- [x] F4.3 admin-shell main content area outlet ✅ W12 D4 — `<main>` with desktop header(breadcrumb + UserMenu)+ p-4 md:p-8 content padding
- [x] F4.4 `frontend/app/page.tsx` (Chat) tokens migration ✅ W12 D4 — Send/Stop buttons → shadcn Button(default + destructive variants);MessageBubble + CitationCard + ScreenshotModal use token classes(`bg-primary text-primary-foreground` / `bg-muted/50 border-border` / `bg-warning/20 text-warning-foreground` / `bg-destructive/10` / `text-muted-foreground` / `bg-card`);streamQuery / patchAssistant / handleSubmit / handleStop functional logic intact
- [x] F4.5 `frontend/app/admin/page.tsx` tokens migration ✅ W12 D4 — F3.8 head-start completed via Button asChild + StatCard `border-border bg-card` + error toast `border-destructive bg-destructive/10` + StatCard `text-muted-foreground` caption
- [x] F4.6 `frontend/app/admin/kb/page.tsx` tokens migration ✅ W12 D4 — `+ Create KB` Button asChild + table headers `border-border` + row dividers `border-muted` + Upload link `text-accent hover:underline`
- [x] F4.7 `frontend/app/admin/kb/[id]/page.tsx` tokens migration ✅ W12 D4 — Upload Button asChild + Save Settings Button + Stat card `border-border bg-card` + error toast `border-destructive bg-destructive/10` + Save success/failed `text-success`/`text-destructive` + form inputs `border-input bg-background ring-ring` + failed docs list `border-border`
- [x] F4.8 `frontend/app/admin/kb/[id]/upload/page.tsx` tokens migration ✅ W12 D4 — Back link `text-accent hover:underline` + Upload Button + error toast `border-destructive bg-destructive/10`
- [x] F4.9 `frontend/app/admin/kb/new/page.tsx` tokens migration ✅ W12 D4 — Step1+Step2+Step3 Next/Back/Execute Buttons(default + outline) + Stepper bullet `bg-primary text-primary-foreground` active / `bg-success text-success-foreground` done / `border-border text-muted-foreground` pending + Summary `border-border bg-muted/40` + Stage icon colors `text-success`/`text-destructive`/`text-accent`/`text-muted-foreground` + form inputs token-clean
- [x] F4.10 `frontend/app/eval/page.tsx` tokens migration ✅ W12 D4 — already token-clean(`text-muted-foreground`)no-op
- [x] F4.11 `frontend/app/debug/[traceId]/page.tsx` tokens migration ✅ W12 D4 — already token-clean(`text-muted-foreground`)no-op
- [x] F4.12 Visual sanity check post-refactor:all 8 pages tokens-driven + no hardcoded oklch leakage(grep `oklch\(` in `frontend/app/**` returns 0 matches)✅ W12 D4 — final grep clean(包括 docstring + globals.css comment refinement remove `oklch(` literal references)
- [ ] F4.13 Functional regression smoke browser test:KB list / chat stream / admin nav / KB detail render still work via `localhost:3001` 🚧 **AI 唔可以驗證**(per CLAUDE.md §13 唔啟動長期運行 server process — `pnpm dev` 屬 long-running)→ user 需自行 `! pnpm dev` 然後 browser smoke;**alternative AI verification done**:type-check ✅ 0 errors + grep oklch ✅ 0 matches;all imports resolve clean(`@/components/ui/*` + `@/lib/utils` + `@/components/auth/user-menu` + lucide-react Menu/LogOut icons)

## F5 — Phase Gate closeout + W13 phase folder kickoff

- [x] F5.1 W12 phase Gate verdict landed:**🟢 PASS WITH F4.13 USER-DEFERRED CAVEAT** per plan §3 5 conditions evaluation(F1 ✅ Q22 + decision-form sync / F2 ✅ tokens.ts + design ref doc / F3 ✅ 19 shadcn primitives + 6 token补齊 + type-check / F4 ⚠ admin shell + 8 pages migration met except F4.13 user-deferred per CLAUDE.md §13 / F5 🟢 in progress this entry)✅ W12 D5(2026-06-10 night cont 3)
- [x] F5.2 W12 progress.md retro 7 sections complete:What worked(7)/ What didn't(4)/ Surprises(5)/ Decisions(7)/ Carry-overs(19 categorized W13/W14/W15/W16+ Beta/external)/ Time tracking(7x under-budget calibration table)/ Spec ref alignment(7-row trace table)✅ W12 D5
- [x] F5.3 `docs/01-planning/W13-user-facing-views/{plan,checklist,progress}.md` draft per architecture.md v6 §5.2 Chat path move + §5.9-§5.11 Landing/Login/Register + ADR-0014 hybrid auth backend cascade ✅ W12 D5 — 7 deliverables F1-F7(F1 routing restructure + theme provider / F2 V7 Landing / F3 V8 Login / F4 V9 Register 3-step wizard / F5 backend hybrid auth `/auth/register` + `/auth/verify-email` + `/auth/login` + users table + Argon2id / F6 C13 ACS integration / F7 closeout + W14 kickoff);plan + checklist + Day 0 progress entry initialized
- [x] F5.4 W12 progress.md frontmatter status flipped to `closed`(plan + checklist + progress 三 files cascade)✅ W12 D5
- [x] F5.5 OQ Q22 sync to decision-form.md per outcome ✅ already done W12 D1 commit `00a1dba`(Section 1 Q22 entry + Section 4 Dashboard row + Section 0 volume count update 13→14 stakeholder + 21→22 total)— no additional sync needed at F5
- [x] F5.6 W12 retro carry-overs consolidated:19 items categorized(CO1-CO3 W13 immediate priority / CO4-CO9 W13 user-facing views scope / CO10-CO12 W14 admin views deferred / CO13-CO15 W15 polish + closeout / CO16-CO19 W16+ Beta deploy unchanged from W11)✅ W12 D5

---

## Cross-Cutting

- [ ] Each commit references `progress.md` Day-N entry(R2)
- [ ] Component tag in commit message per CC-1(C09 admin shell / C10 chat UI)
- [ ] OQ status sync to `decision-form.md`(R4)— Q22 W12 critical
- [ ] Risk register update if any new risk surface(e.g. shadcn install Windows env regression)
- [ ] CLAUDE.md §5.1 H1 boundary check:no architectural change without ADR(W12 scope already covered by ADR-0014 + ADR-0015)
- [ ] CLAUDE.md §5.2 H2 boundary check:no new vendor / dependency without ADR(shadcn already locked per ADR-0006 + ADR-0015;no new deps expected)
- [ ] CLAUDE.md §3.2 frontend conventions check:no `any` / no @ts-ignore / shadcn/ui only / tokens consumption verified

---

**Lifecycle reminder**:呢份 checklist 衍生自 `plan.md` deliverables。新加 deliverable 必須先入 plan + changelog,然後再加 checklist item。
