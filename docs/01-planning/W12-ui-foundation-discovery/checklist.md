---
phase: W12-ui-foundation-discovery
plan_ref: ./plan.md
status: active
last_updated: 2026-06-10
---

# Phase W12 — Checklist

> Atomic checkbox(每 item ≤ 0.5–2 hour effort per W6 C10 calibration)。
> Status:`active` 自 2026-06-10 evening W12 D1(W11 early closeout cascade same-session;Q22 email vendor F1 implementation start)。

## F1 — Q22 email vendor decision + W12 phase plan validate

- [x] F1.1 Q22 added to `decision-form.md` Section 1(Stakeholder Decisions)— Question / Why it matters / Default if unanswered / Decision pending fields populated per existing Q1-Q21 pattern ✅ W12 D1(2026-06-10 evening)
- [x] F1.2 Q22 trade-off table populated:Azure Communication Services vs SendGrid(billing / SDK maturity / verification token flow / email deliverability / monthly volume cap / cost per 1k email)✅ W12 D1 — 8-row trade-off table embedded in decision-form.md Q22 entry
- [x] F1.3 Q22 default-if-unanswered = Azure Comm Service rationale documented(per ADR-0014 + spec §13 Azure-native preference per CLAUDE.md §5.2 H2)✅ W12 D1 — 3 anchors per Q22 entry decision rationale(Azure-native billing integration + Python SDK asyncio + ADR-0014 default consistency + CLAUDE.md §5.2 H2)
- [x] F1.4 Q22 Resolved by W12 D2(stakeholder approve OR default activate per timing)✅ W12 D1 — early default activation per User-as-Stakeholder same-session pattern Q7+Q9+Q10+Q11+Q12 W6 D5 cycle 重複(2026-06-10 evening)
- [x] F1.5 architecture.md v6 §3 amendment — add C13 Email Verification Service component card per Q22 outcome ✅ W12 D1 — `docs/architecture.md §3.7 C13 Email Verification Service`(vendor + SDK + cost model + integration pattern + tier boundary + RISK_REGISTER cross-ref)+ §13.12 Cross-references row added
- [x] F1.6 W12 plan.md `status: draft → active` flip — based on(a) W11 D5 closeout PASS sign-off(b) Q22 Resolved(c) Stakeholder ack 2026-06-10 final sign-off ✅ W12 D1 — 三條件全 cleared(W11 PARTIAL PASS commit `4ec56d5` + Q22 default activated + Stakeholder authorization 2026-06-10 evening session);plan + checklist + progress.md frontmatter `draft → active`

## F2 — Visual identity tokens.ts finalize + design reference doc

- [ ] F2.1 `frontend/lib/theming/tokens.ts` populate:colors object(primary / accent / background / foreground / muted / border / success / warning / destructive — all oklch values per spec)
- [ ] F2.2 `frontend/lib/theming/tokens.ts` populate:radius object(sm 0.25 / md 0.5 / lg 0.75rem per spec "更銳利感 vs Dify default")
- [ ] F2.3 `frontend/lib/theming/tokens.ts` populate:fontFamily object(Inter sans + JetBrains Mono per spec — distinct from Dify SF Pro)
- [ ] F2.4 `frontend/lib/theming/tokens.ts` populate:spacing(Tailwind default reference)+ shadow + motion tokens(extend per shadcn/ui v0)
- [ ] F2.5 AI propose visual decisions doc — primary color OkLab proposal + accent + typography hierarchy + initial dark mode strategy(default deferred to W15 polish)
- [ ] F2.6 User approve cycle 1 — primary + accent + typography sign-off(progress.md Day-N entry record approval)
- [ ] F2.7 Design reference doc `docs/02-architecture/ui-design-reference-v6.md` create:9 views layout sketches(low-fi ASCII diagrams + key component inventory per view)
- [ ] F2.8 Design reference doc — cross-view consistency rules section(sidebar / breadcrumb / toast / empty state pattern unification)
- [ ] F2.9 Design reference doc — component-to-view mapping table(which shadcn primitives used where)
- [ ] F2.10 Design reference doc — Dify reference path index(layout patterns to mirror per architecture.md v6 §5.5.1-§5.5.5 + §5.8 + §5.9-§5.11)

## F3 — shadcn/ui foundation setup + 12-15 base components

- [ ] F3.1 `pnpm dlx shadcn@latest init` run in `frontend/` w/ New York style + Tailwind CSS variables + tokens.ts integration verify
- [ ] F3.2 `frontend/components.json` 配置 → tracked in git(committed at W12 commit cycle)
- [ ] F3.3 Form primitives install:Button、Input、Textarea、Label、Select、Switch、Slider、Checkbox(8 components)
- [ ] F3.4 Layout primitives install:Card、Separator、Sheet、Dialog、Tabs(5 components)
- [ ] F3.5 Feedback primitives install:Badge、Toast(via sonner per shadcn default)、Skeleton(3 components)
- [ ] F3.6 Nav primitives install:Dropdown、Breadcrumb (custom if shadcn 唔支援)(2 components)
- [ ] F3.7 全部 shadcn components 在 `frontend/components/ui/` 目錄;tokens.ts 整合 via Tailwind CSS variable layer
- [ ] F3.8 Smoke verify:Render `<Button variant="default">Test</Button>` 喺 `app/admin/page.tsx` → visual match tokens primary
- [ ] F3.9 Type-check pass(`pnpm type-check` clean — 0 shadcn-introduced TS error per Karpathy §1.4 verification)

## F4 — Admin shell foundation + existing pages tokens migration

- [ ] F4.1 `frontend/components/nav/admin-shell.tsx` rebuild w/ shadcn primitives:sidebar nav using `Sheet`(mobile)+ flat sidebar(desktop)
- [ ] F4.2 admin-shell header w/ breadcrumb + user-menu(reuse `auth/user-menu.tsx`,wrap in shadcn `Dropdown`)
- [ ] F4.3 admin-shell main content area outlet
- [ ] F4.4 `frontend/app/page.tsx` (Chat) tokens migration — replace hardcoded `oklch(...)` with tokens-referenced classes;keep functional logic intact
- [ ] F4.5 `frontend/app/admin/page.tsx` tokens migration
- [ ] F4.6 `frontend/app/admin/kb/page.tsx` tokens migration
- [ ] F4.7 `frontend/app/admin/kb/[id]/page.tsx` tokens migration
- [ ] F4.8 `frontend/app/admin/kb/[id]/upload/page.tsx` tokens migration
- [ ] F4.9 `frontend/app/admin/kb/new/page.tsx` tokens migration
- [ ] F4.10 `frontend/app/eval/page.tsx` tokens migration
- [ ] F4.11 `frontend/app/debug/[traceId]/page.tsx` tokens migration
- [ ] F4.12 Visual sanity check post-refactor:all 8 pages tokens-driven + no hardcoded oklch leakage(grep `oklch\(` in `frontend/app/**` should return 0 matches)
- [ ] F4.13 Functional regression smoke browser test:KB list / chat stream / admin nav / KB detail render still work via `localhost:3001`

## F5 — Phase Gate closeout + W13 phase folder kickoff

- [ ] F5.1 W12 phase Gate verdict landed(PASS / PARTIAL PASS / FAIL with explicit rationale per W11 F6.1 pattern)
- [ ] F5.2 W12 progress.md retro 7 sections complete:What worked / What didn't / Surprises / Decisions / Carry-overs / Time tracking / Spec ref alignment
- [ ] F5.3 `docs/01-planning/W13-user-facing-views/{plan,checklist,progress}.md` draft per architecture.md v6 §5.9-§5.11 + §5.2 Chat path move + ADR-0014 hybrid auth backend cascade
- [ ] F5.4 W12 progress.md frontmatter status flipped to `closed`
- [ ] F5.5 OQ Q22 sync to decision-form.md per outcome
- [ ] F5.6 W12 retro carry-overs consolidated(future W13/W14/W15 / Tier 2 / external dependency items)

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
