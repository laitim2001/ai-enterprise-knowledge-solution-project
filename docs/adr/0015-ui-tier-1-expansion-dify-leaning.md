# ADR-0015: UI Tier 1 Expansion — 6 views → 9 views, Dify-leaning aesthetic, shadcn/ui foundation commit

**Date**: 2026-06-10
**Status**: Accepted
**Approver**: Chris(acting as Stakeholder per past sessions authorization pattern;explicit ack 2026-06-10 evening session W11 D2 cont)

## Context

architecture.md v5(2026-04-27 frozen)§5 spec **6 views Dify pattern**:
- §5.2 View 1 Chat(`/`)
- §5.3 View 2 Admin Dashboard(`/admin`)
- §5.4 View 3 KB List(`/admin/kb`)
- §5.5 View 4 KB Detail(`/admin/kb/[id]`,5 tabs:Documents / Pipeline / Retrieval Testing / Settings)
- §5.6 View 5 Eval Console(`/eval`)
- §5.7 View 6 Debug View(`/debug/[traceId]`)

Spec §5.1 Visual Identity Strategy + ADR-0006(Next.js + shadcn/ui from Day 1)+ CLAUDE.md §3.2(shadcn/ui only)established UI quality bar:Dify layout / interaction pattern + EKP-native tokens.ts visual identity。

**Trigger**:W11 D2 cont(2026-06-10)evening session — User opened browser at `localhost:3001` 後 surface UI quality gap:

### Current state(W11 D2 cont local dev unblock confirmed):

```
frontend/app/page.tsx              322 lines — barebones <main> + textarea + Send button
frontend/app/admin/page.tsx         78 lines — minimal placeholder
frontend/app/admin/kb/page.tsx      88 lines
frontend/app/admin/kb/[id]/page.tsx 207 lines — NO 5-tab structure visible
frontend/components/                3 files only(user-menu / error-boundary / admin-shell)
frontend/components/ui/             ❌ DOES NOT EXIST(shadcn/ui never installed)
frontend/components.json            ❌ DOES NOT EXIST(shadcn config missing)

Total frontend code:                ~695 lines for entire 6-view implementation
Spec §5 completion estimate:        ~15-20%
```

### Causation chain(why we got here):

1. **W3 D4 shadcn/ui upgrade deferral** — `frontend/app/page.tsx:6-8` self-acknowledged comment:「W3 D4 baseline plain HTML/Tailwind (shadcn upgrade deferred to W3 D5 F8 polish window per Karpathy §1.2 simplicity-first; matches W2 D5 admin-views pattern)」
2. **W3 D5 → W4 → W5 → W6**:backend-heavy work(reranker shootout / CRAG eval / demo prep)dominate sprint capacity
3. **W7-W8**:per architecture.md §6.1 sprint plan「React polish」delivery 不足,被 Track A IT cred 後勤 + rate limiting + Beta deploy infra 拖住
4. **W9-W10**:Beta internal testing focus on functional bugs 而非 UI polish
5. **W11 D2 cont**:Mode B local dev unblock allows User 第一次直接 evaluate UI quality → gap surface
6. **W11 D2 cont evening session**:User explicit ack scope expansion + production launch defer

### Violations cumulative(已 ~5 個月):

| Violation | Source | Status |
|---|---|---|
| shadcn/ui 從未 install | architecture.md §13.5 + CLAUDE.md §3.2 | 🔴 ongoing since W3 D4 |
| Design tokens 未 consume(hardcode `oklch(...)` 喺 page.tsx)| architecture.md §5.1 + CLAUDE.md §3.2 | 🔴 ongoing |
| §5.5 KB Detail 5-tab structure 未實 | architecture.md §5.5 | 🔴 ongoing |
| §5.6 Eval Console split layout + metric cards 未實 | architecture.md §5.6 | 🟡 functional but undershoot polish |
| §5.7 Debug View vertical timeline 未實 | architecture.md §5.7 | 🟡 functional but undershoot polish |

## Decision

Tier 1 v6 amendment **expands UI Tier 1 deliverable from 6 views → 9 views**,**lock shadcn/ui foundation commit**,**lock Dify-leaning aesthetic**(layout 1:1 mirror Dify Image 1-6 patterns,visual identity 100% EKP-native via tokens.ts):

### 新 views(per architecture.md v6 §5.9-§5.11):

- **§5.9 View 7 Landing Page(`/`)**:public landing,modern SaaS aesthetic,hero + features + how-it-works
- **§5.10 View 8 Login(`/login`)**:split layout,Microsoft SSO + email login form(per ADR-0014 hybrid auth)
- **§5.11 View 9 Register(`/register`)**:3-step wizard(account info → email verify → welcome,per ADR-0014)

Path change:原 §5.2 Chat View(`/`)→ 移至 `/chat`(per v6 amendment;path detail W12 D1-D2 detail)。

### Dify-leaning aesthetic commit:

Per User decision 2026-06-10 evening session — **Inspired-by Dify, EKP-native cleaner**:
- Layout 1:1 mirror Dify Image 1-6 patterns(per existing §5.5.1-§5.5.5 spec sections)
- Sidebar nav / step indicator / card-based selection / document table / chunk inspector / retrieval setting cards 全部按 Dify pattern
- Visual identity 100% EKP-native via `frontend/lib/theming/tokens.ts`(已存在但 unused;W12 phase 1 deliverable: consume 全部 page.tsx hardcode oklch values → tokens.ts reference)
- Dify branding(blue primary / SF Pro typography / illustration style)**唔抄**

### shadcn/ui foundation commit:

Per ADR-0006(原 Day 1 commitment 但 implementation defer)+ ADR-0015(now)— **W12 phase 1 必須 install shadcn/ui** + setup `components.json` + populate `frontend/components/ui/` 12-15 base components(initial set):
- Button、Input、Textarea、Label、Card、Badge、Separator、Tabs、Sheet、Dialog、Dropdown、Select、Switch、Slider、Toast

Default New York style + custom tokens.ts integration。

### Multi-sprint roadmap(W12-W15)

| Sprint | Scope | 估時 |
|---|---|---|
| **W12 — Discovery + Foundation** | Spec amendment land + tokens.ts finalize + shadcn/ui setup + 12-15 base components + admin shell | ~1.5 weeks |
| **W13 — User-facing views** | Landing(§5.9)+ Login(§5.10)+ Register(§5.11)+ Chat V1 expanded(§5.2 path move 同 polish)| ~1.5 weeks |
| **W14 — Admin views** | Admin Dashboard(§5.3)+ KB List(§5.4)+ KB Detail 5-tab(§5.5)| ~1.5 weeks |
| **W15 — Eval / Debug + Polish** | Eval Console(§5.6)+ Debug View(§5.7)+ responsive + a11y + Playwright E2E + pixel diff baseline | ~1.5 weeks |
| **W16+ — Production launch resume** | Track A IT cred event + F1.x SSO LIVE switch + 25%-50%-100% staged rollout(per W11 plan resumed) | ~2-3 weeks |

**Production launch implication**:從原 W12 → W16+(estimated 5-7 weeks delay)。

## Alternatives Considered

### Alt A:Ship current barebones at W12 + post-launch polish(rejected)

**Tradeoff**:
- ✅ Pro:no production launch delay
- ❌ Con:250-500 user 量級 UX impact 不可接受;poor first impression hard to recover
- ❌ Con:violations cumulative(shadcn never installed,tokens not consumed)signal poor engineering discipline to stakeholder
- ❌ Con:post-launch UI sprint requires user re-onboarding to changed UI(higher friction than initial onboarding)

**Reject reason**:User explicit decision to comprehensive UI sprint。

### Alt B:Phased UI(MVP 4 views W12-W13,polish W14+)(rejected)

**Tradeoff**:
- ✅ Pro:earlier soft launch to small Beta cohort(<50 user)mid-cycle
- ❌ Con:UI inconsistency between phased views(MVP shadcn vs polished shadcn)
- ❌ Con:soft launch UI gap may damage internal credibility before hard launch
- ❌ Con:User explicit ask「全面 phase / sprint 規劃」rules out phased

**Reject reason**:User decision tree 2026-06-10。

### Alt C:Hire / loan designer + design phase(deferred consideration)

**Tradeoff**:
- ✅ Pro:proper design output(wireframes / hi-fi mockups / a11y review)
- ❌ Con:adds 2-4 weeks design phase before any implementation;production launch defer extends
- ❌ Con:no designer in current OQ list — sourcing + onboarding additional overhead
- 🟡 Mid:Tier 2 / future quarterly polish cycle 補 designer involvement 可考慮

**Reject reason**:User decision「I (claude) propose visual decisions, you approve」。Designer involvement deferred Tier 2 / post-launch polish cycle。

### Alt D:Hybrid Tier 1(this ADR + ADR-0014)— ACCEPTED

UI sprint W12-W15 + hybrid auth(ADR-0014)combined under single v6 amendment cycle。Production launch defer 5-7 weeks。Substantial scope but coherent。

## Consequences

### Positive

- **Spec §5 actually delivered**:6 views Dify pattern + 3 new views(Landing/Login/Register)quality match spec intent
- **ADR-0006 commitments resolved**:shadcn/ui foundation finally installed(原 Day 1 promise)
- **Design tokens consumed**:tokens.ts 終於使用,visual identity layer working as spec'd
- **Production-ready UX**:250-500 user launch with quality match enterprise expectation
- **Long-term maintainability**:future view addition(Tier 2)benefits from established shadcn/ui pattern + design system

### Negative

- **5-7 weeks production launch delay**:W12 → W16+;Stakeholder explicit ack但 Beta cohort 等 SSO LIVE 仍需 IT cred event(W11 plan F1 unchanged)
- **Substantial frontend code rewrite**:`frontend/app/page.tsx`(322 lines)+ admin views 全部 refactor → reuse logic,replace UI primitives
- **Existing snapshot tests / Playwright tests**(if any from W6 demo prep)需 update — pixel diff baselines 全部 regenerate
- **Q22 OQ NEW**(email vendor)+ R-A1 risk NEW(user data PII)triggered alongside ADR-0014

### Neutral

- **Track A IT cred event**:UI sprint W12-W15 不依賴 Track A,但 W16 production launch 仍需 IT cred event-triggered SSO LIVE switch
- **Eval baseline**:UI rewrite 不影響 backend pipeline → eval-set-v0 baseline preserved(retrieval / answer relevancy / faithfulness / latency 全 unaffected)
- **Existing W11 D2 cont local dev unblock**:`.npmrc` hoisted layout + `/api/backend` proxy route 都 reuse(W12 sprint benefit from W11 D2 cont 投入)

## References

- architecture.md v6 §5.9-§5.11(Landing / Login / Register view specs)
- architecture.md v6 §13.12(v5.1→v6 amendment trigger)
- architecture.md v5.1 §5.1-§5.8(existing 6 views spec — preserved)
- ADR-0006 — Next.js + shadcn/ui from Day 1(promise being fulfilled by this ADR)
- ADR-0010 — Dify read-only reference(visual identity rule preserved)
- ADR-0014(sister ADR same amendment cycle — hybrid auth)
- W11 plan changelog 2026-06-10(production launch defer record)
- W11 D2 progress.md cont entry(2026-06-10 stakeholder ack)
- W12 phase folder — `docs/01-planning/W12-ui-foundation-discovery/`(kickoff per CLAUDE.md §10 R1)
- CLAUDE.md §5.1 H1 architectural change constraint(this ADR satisfies)
- CLAUDE.md §3.2 frontend conventions(shadcn/ui only + tokens via lib/theming)
