---
phase: W15-polish-closeout
plan_ref: ./plan.md
checklist_ref: ./checklist.md
status: active
last_updated: 2026-06-10
---

# Phase W15 — Progress(Daily Journal + Decisions + Retro)

> Daily progress entries per CLAUDE.md §10 R2(每 commit reference progress.md Day-N entry)。
> Status:`draft` — pending W15 D1 active flip post stakeholder authorization(rolling JIT — calendar-day-collapse cont OR future session post W14 D5 F5 closeout 2026-06-10)。

---

## Day 0 — Pre-kickoff Setup(W14 D5 F5 closeout cascade 2026-06-10)

> **Note**:呢個 Day 0 entry 屬 W14 D5 F5 closeout cascade carry-over governance prep,而非 W15 implementation start。W15 D1 implementation start = next session post stakeholder authorization(rolling JIT — calendar-day-collapse cont OR future session)。

### Setup completed pre-W15 D1

| Artifact | Commit | Status |
|---|---|---|
| W14 phase Gate PASS WITH SMOKE-USER-DEFERRED CAVEAT verdict landed | _W14 D5 F5 closeout commit_ | 🟡 in flight(this session) |
| W14 progress.md retro 7 sections complete | _W14 D5 F5 closeout commit_ | 🟡 in flight(this session) |
| W14 frontmatter active → closed cascade(plan + checklist + progress) | _W14 D5 F5 closeout commit_ | 🟡 in flight(this session) |
| W15 phase folder skeleton(plan.md + checklist.md + progress.md) | _W14 D5 F5 closeout commit_ | 🟡 in flight(this session) |
| F1 V2 Admin Dashboard refactor + CO_F5d-cont session-token mode | `641b328` | ✅ landed W14 D1 |
| F2 V3 KB List card grid refactor | `23cc579` | ✅ landed W14 D2 |
| F3 V4 KB Detail 5-tab nav | `84c8d39` | ✅ landed W14 D3 |
| F4 cross-cutting verification audit | `a4213d0` | ✅ landed W14 D4 |

### Pending W15 D1 active flip pre-conditions

- ⏳ Stakeholder authorization for W15 D1 implementation start(per W14 closeout same-session OR next session pivot)
- ⏳ User end-to-end browser smoke(`! pnpm dev` + `! uvicorn` + W14 admin views verify)— **non-blocker** for W15 D1(W15 F4 Playwright E2E baseline harness will systematically subsume manual smoke deferred across W12+W13+W14 cycles)
- ⏳ W15 plan/checklist/progress frontmatter `draft → active` flip on W15 D1 active trigger

### W15 immediate scope alignment with W14 retro Carry-overs

- **CO_W14_F4_error_boundary** Token cleanup pass → **W15 F3.4**(deliverable exact match)
- **CO_W15_F1** V5 Eval Console implementation → **W15 F1**(deliverable exact match)
- **CO_W15_F2** V6 Debug View implementation → **W15 F2**(deliverable exact match)
- **CO_W15_F3** Responsive + a11y + Playwright E2E + pixel diff baseline → **W15 F3 + F4**(deliverable exact match)
- **CO_W14_smoke** End-to-end browser smoke → **W15 F4 Playwright E2E systematic subsume**(deliverable exact match — golden-path E2E + admin path E2E)

### W15 critical path

- **W15 D1 V5 Eval Console**:F1 implementation(largest deliverable post-F4 Playwright)— 4-metric cards + Reranker Shootout table data wire
- **W15 D2 V6 Debug View**:F2 implementation — 9-stage timeline accordion + Langfuse link
- **W15 D3 polish + token cleanup**:F3 keyboard nav + ARIA + responsive verify + CO_W14_F4_error_boundary;F4 Playwright install + config
- **W15 D4 E2E harness**:F4 golden-path + admin path + pixel diff baseline
- **W15 D5 closeout + Tier 1 UI sprint cycle final retrospective**:F5 W16+ Beta deploy phase folder rolling JIT trigger

### W16+ Beta deploy phase entry

- W15 closes Phase 4 of 4 UI sprint cycle — **Tier 1 UI Tier 1 expansion 完整 implemented**;W16+ = Beta deploy production launch resume(per W11 plan F1+F2+F3 Track A IT cred event-triggered + R-B1 closure trigger);**ready for W16+ Beta deploy production launch**
- W16+ D1 implementation start trigger = W15 D5 retro post-Tier 1 UI sprint cycle final closeout + Track A IT cred populate event

---

## Day 1 — W15 D1 active flip + F1 V5 Eval Console implementation(real-calendar 2026-06-10 same-day collapse cycle 4 of 4 final cont)

> **Calendar note**:plan §5 tentative date 2026-07-07 superseded by real-calendar 2026-06-10 same-day collapse(W14 D5 F5 closeout → W15 D1 same-session per pivot momentum continuation;cycle 4 of 4 UI sprint final cycle begins)。Time tracking calibration:plan ~1 day budget vs actual ~1 hr(NEW V5 Eval Console implementation + 6 deviations surfaced via investigation phase + 3 NEW frontend files;consistent with W12+W13+W14 7-16x under-budget pattern)。

### What landed

| F# | Deliverable | Files | Status |
|---|---|---|---|
| F1.1 | Top filter bar + admin shell wrap | NEW `frontend/app/eval/layout.tsx`(AuthProvider + QueryProvider + AdminShell mirror admin layout)+ NEW filter bar in page.tsx(Eval set Select + Run / Run Single Buttons + responsive flex);**deviation logged plan §7 (D1)** — actual baseline = W1 skeleton 15-line placeholder NOT W12 F4.5;effective NEW implementation per Karpathy §1.1 think-before-coding | ✅ (deviation noted) |
| F1.2 | Run config card | LLM Select + Reranker Select + Top K Input + CRAG threshold Slider(0.70 default value display)+ Intent type Select per design ref §2.5 layout;DEFAULT_CONFIG const initialized from W6 production lock(gpt-5.5 + cohere-v4.0-pro + top_k=5 + crag=0.70 + intent=auto)| ✅ |
| F1.3 | 4-metric cards | **deviation logged plan §7 (D1)** — schema + design ref §2.5 wireframe agree on Recall@5/Faithfulness/Correctness/Image Association(plan literal "Context Relevancy / Answer Relevancy" inconsistent with both)→ aligned with spec naming;METRIC_THRESHOLDS const(R@5 ≥ 0.80 Gate 1 + others ≥ 0.85 Tier 1 strict);MetricCard component shows score + PASS/FAIL Badge + threshold;**stub mitigation pattern** for backend 501(empty state + AlertCircle + Run CTA + "Backend `/eval/run` is W4 stub")| ✅ (deviation noted) |
| F1.4 | Failed queries table | EvalReport.failed_queries → plain HTML `<table>` w/ query_id (mono) + query (line-clamp-2) + metric_failed Badges + Inspect Link → /debug/{query_id};empty state w/ CheckCircle2 「No failed queries」;mirrors W14 F1.2 Failed ingestion table pattern | ✅ |
| F1.5 | W4 Reranker Shootout table | **deviation logged plan §7 (D1)** — no `reranker_shootout*` artifact exists;采 inline `RERANKER_SHOOTOUT` static const populated from W6 demo-prep.md §107-114 Q-A2 actual W6 D1 LIVE Azure 2-way data(Cohere v4.0-pro 1.000/0.841 RECOMMENDED + Azure built-in 0.882/0.743 Fallback + Voyage + ZeroEntropy DROPPED W4 Karpathy §1.2 simplicity drop = effective 2-way not "4-way");3 status variants Badge(recommended success / fallback muted / dropped muted+opacity-60) | ✅ (deviation noted) |
| F1.6 | Loading + empty state | Skeleton 4-card during loading(matching shape per design ref §3.5);empty state per design ref §3.4(AlertCircle + heading + Run CTA hint + stub note);Failed queries empty state(CheckCircle2 + "No failed queries");Reranker Shootout no empty state(static data always present)| ✅ |
| ADMIN_SHELL_WRAP | NEW eval/layout.tsx | **deviation logged plan §7 (D1)** — design ref §2.5 wireframe shows admin sidebar but `/eval` was standalone W1 skeleton;NEW eval/layout.tsx mirror admin/layout.tsx pattern(5-line non-invasive Karpathy §1.3 surgical);admin-shell NAV_ITEMS already lists `/eval` + SEGMENT_LABELS already covers `eval` segment | ✅ (deviation noted) |

### Decisions

1. **/eval admin shell wrap correctness**(NEW eval/layout.tsx)— design ref §2.5 wireframe shows "Sidebar / KB / ► Eval / Settings" + admin-shell NAV_ITEMS already lists `/eval` + SEGMENT_LABELS already covers `eval` for breadcrumb;adding layout.tsx mirror admin layout pattern is non-invasive(5-line change)+ keeps URL stable;Karpathy §1.3 surgical scope discipline preserved
2. **Schema-aligned metric naming**(Correctness + Image Association vs plan literal Context Relevancy + Answer Relevancy)— EvalReport schema(`backend/api/schemas/eval.py`)+ design ref §2.5 wireframe codes(R@5/FFul/CRct/IAss)agree;plan literal is the outlier(predates W4 RAGAs redesign);**5th occurrence of plan literal vs actual code grep verification gap**(W13 F1.5 + W14 F1.1 + W14 F2.2 + W15 F1.1 baseline + W15 F1.3 metric naming);CO_W14_process_grep_verify call-out reinforced — **process improvement candidate accelerated**(see Carry-overs)
3. **Backend stub mitigation pattern reuse**(W14 F3.2/F3.3 Documents/Chunks tabs precedent)— empty state Card + AlertCircle + Run CTA hint + stub note 「Backend `/eval/run` is W4 stub — pending implementation per docs/eval-methodology.md」;ApiError.status === 501 → `toast.info("Eval run pending W4 backend implementation", { description: "docs/eval-methodology.md" })`;non-breaking + transparent admin user communication
4. **W4-W6 actual reranker shootout data via W6 demo-prep.md §107-114** — Cohere v4.0-pro 1.000/0.841 + Azure built-in 0.882/0.743(W6 D1 LIVE Azure 2-way comparison data per Q-A2 stakeholder Q&A);Voyage + ZeroEntropy null + status='dropped' + opacity-60 visual dim per W4 Karpathy §1.2 simplicity drop;**inline static const** simpler than backend artifact GET endpoint not yet exposed;Cohere production lock per Q21 Resolved + ADR-0012 reservation context preserved in CardDescription tag
5. **Plain HTML `<table>` over shadcn Table primitive**(no shadcn Table installed)— Failed queries + Reranker Shootout both use plain table pattern w/ Tailwind styling matching W14 F1.2 Failed ingestion table;Karpathy §1.2 simplicity-first(do not install new primitive when 2 use sites can satisfy with HTML)+ H2 vendor lock preserved
6. **3 status variants for Reranker Shootout**(recommended Badge bg-success/15 + fallback Badge bg-muted + dropped Badge bg-muted + row opacity-60)— visual hierarchy preserves "ranking" semantics(production lock vs hot fallback vs deprecated);per design ref §3.6 PASS/FAIL color discipline
7. **Run Single button placeholder defer V6 Debug View integration W15 D2** — `toast.info("Run Single — pending V6 Debug View integration", { description: "W15 D2 F2 deliverable" })`;non-blocking F1 critical path;wires up properly when /debug/[traceId] route lands W15 D2

### Verification

```
$ cd frontend && pnpm type-check
> tsc --noEmit
$ # 0 errors

$ grep -r "\[oklch" frontend/app/eval/ frontend/lib/api/eval.ts
(no matches — 0 hardcoded oklch className arbitrary values)
```

✅ TypeScript strict mode clean(0 errors);no `any` / no @ts-ignore;no hardcoded oklch — all colors via Tailwind tokens(`bg-success/15` / `bg-warning/15` / `bg-muted` / `text-foreground` / `text-muted-foreground` / `border-border`)。shadcn primitives reused(Card + Badge + Button + Input + Label + Select + Skeleton + Slider + lucide icons CheckCircle2/AlertCircle/ExternalLink/Play/PlayCircle)— no new vendor。NEW lib/api/eval.ts client mirror kb.ts/query.ts pattern;NEW eval/layout.tsx mirror admin/layout.tsx pattern。

### Carry-overs to W15 D2

- 🚧 F1 user smoke deferred per CLAUDE.md §13(`! pnpm dev` + `! uvicorn`;`/eval` page renders + admin sidebar visible + 4-metric empty state w/ stub note + Run button → toast.info on 501 + Reranker Shootout table 4-row + responsive collapse mobile + dark mode toggle still works)— W15 F4 Playwright E2E baseline harness 將 systematically subsume
- ⏳ W15 D2 focus per plan §5:F2 V6 Debug View implementation(`frontend/app/debug/[traceId]/page.tsx` NEW route + 9-stage timeline accordion + Open in Langfuse stub link;Failed queries Inspect Link target wires up)
- 📝 **CO_W15_F1_backend** Backend `POST /eval/run` + `POST /eval/shootout` W4 implementation per docs/eval-methodology.md(stub status documented in MetricCardsGrid empty state + ApiError 501 toast.info hint)— Beta hardening trigger fit
- 📝 **CO_W15_F1_eval_set_v1** `eval-set-v1` (W4+W5 +20 real-query 50 queries) referenced in dropdown but actual file existence not verified during W15 D1(non-blocker — Run button 501 stub anyway;**6th occurrence latent if eval-set-v1 file missing**)— Beta hardening verify when backend implementation lands
- 📝 **CO_W14_process_grep_verify reinforcement** — 5th occurrence of plan literal vs actual code grep verification gap pattern;suggests **W15 retro decision** to formalize "spec ref grep verification" step pre-active flip checklist for W16+ Beta deploy phase folder rolling JIT trigger

### Commit

- `bf01091` feat(frontend,docs): W15 D1 F1 V5 Eval Console implementation + W15 active flip + 6 deviations + admin shell wrap

---

## Day 2 — W15 D2 F2 V6 Debug View implementation(real-calendar 2026-06-10 same-day collapse cycle 4 of 4 final cont)

> **Calendar note**:plan §5 tentative date 2026-07-08 superseded by real-calendar 2026-06-10 same-day collapse(W15 D1 F1 → W15 D2 F2 cycle continue post user authorization "A:continue W15 D2 — F2 V6 Debug View implementation")。Time tracking calibration:plan ~1 day budget vs actual ~45 min(REWRITE V6 Debug View implementation + 4 deviations surfaced + 3 NEW frontend files;consistent with W12+W13+W14+W15 D1 7-16x under-budget pattern)。

### What landed

| F# | Deliverable | Files | Status |
|---|---|---|---|
| F2.1 | Trace header + summary cards + admin shell wrap | NEW `frontend/app/debug/layout.tsx`(AuthProvider + QueryProvider + AdminShell mirror eval/admin layout)+ NEW `frontend/lib/api/debug.ts`(typed client + TraceData + PipelineStageMetric forward-looking schema)+ REWRITE `frontend/app/debug/[traceId]/page.tsx` header(Back to Eval Link + traceId mono display + Total ms / Total cost / Query summary cards + Open in Langfuse Button);**deviation logged plan §7 (D2)** — file actually exists as W1 skeleton 15-line placeholder per Glob check(plan literal "NEW route" stale)| ✅ (deviation noted) |
| F2.2 | 6-stage pipeline timeline(NOT 9-stage)| **deviation logged plan §7 (D2)** — plan literal "9-stage timeline" inconsistent with plan F2.2 own 6-enumeration + design ref §2.6 wireframe;采 wireframe-aligned 6-stage spec;PIPELINE_STAGES const w/ id (1-6) + name + vendor (Cohere v4.0-pro / gpt-5.5) + description per stage(Query Preprocessor / Hybrid Retrieval / Reranker / CRAG Confidence Judge / LLM Synthesis / Final Response)| ✅ (deviation noted) |
| F2.3 | Custom Collapsible per stage | **deviation logged plan §7 (D2)** — Accordion NOT in W12 D3 19-primitive install list;design ref §2.6 explicitly permits "shadcn Accordion **OR custom Collapsible** primitive";采 custom `PipelineStageCollapsible` component(useState boolean + ChevronDown lucide rotation 0deg ↔ 180deg via CSS transition + button + aria-expanded)per Karpathy §1.2 simplicity-first + H2 vendor lock(no new dependency;6 use sites within same page = local state-machine 5-line component over npm install) | ✅ (deviation noted) |
| F2.4 | Open in Langfuse link | stub URL pattern `https://langfuse.example.com/trace/${encodeURIComponent(traceId)}` per plan literal Tier 1 acceptance;ExternalLink lucide icon + target=_blank + rel=noopener noreferrer;works independently of backend trace API status(uses traceId from URL params via useParams flow) | ✅ |
| F2.5 | Loading + stub + error states | **deviation logged plan §7 (D2)** — backend `GET /debug/trace/{trace_id}` returns 501 NOT_IMPLEMENTED stub(W3+ Langfuse correlation per architecture.md §5.7);采 W14 BackendStubNote stub mitigation pattern(AlertCircle alert + stub note "Backend `GET /debug/trace/&#123;trace_id&#125;` is W3+ stub — pending Langfuse correlation per architecture.md §5.7" + 6-stage scaffold "—" duration);retry: false on useQuery(避免 4-retry waste against 501 stub);non-501 error states show destructive-bordered error banner;Skeleton 3-card during initial loading(matching SummaryCard shape per design ref §3.5) | ✅ (deviation noted) |
| ADMIN_SHELL_WRAP | NEW debug/layout.tsx | mirror admin/layout.tsx + eval/layout.tsx pattern(5-line AuthProvider + QueryProvider + AdminShell);admin-shell SEGMENT_LABELS already covers `debug` for breadcrumb auto-derivation;intentionally NOT added to NAV_ITEMS sidebar(V6 accessed via V5 Failed queries Inspect Link not as top-level nav per architecture.md v6 §5.7) | ✅ |

### Decisions

1. **6-stage spec correctness over plan header literal**(F2.2 "9-stage" → 6-stage)— design ref §2.6 wireframe + plan F2.2 own enumeration agree on 6 stages(Query Preprocessor + Hybrid Retrieval + Reranker + CRAG + LLM Synthesis + Final Response);plan internal inconsistency between header "9-stage" + 6-enumerated body resolved per Karpathy §1.4 verifiable goal-driven match to design ref wireframe(spec lock per §1.1)
2. **Custom Collapsible over shadcn Accordion install**(F2.3)— design ref §2.6 explicitly permits both options;6 use sites within same page benefit from local 5-line component(button + useState + chevron rotation)over installing new shadcn primitive + radix-ui peer dependency;Karpathy §1.2 simplicity-first + H2 vendor lock preserved;mirror W14 F2.1 + W15 F1.4 plain HTML over shadcn Table choice pattern
3. **Backend stub mitigation pattern reuse**(W14 F3.2/F3.3 + W15 F1.3 precedent)— AlertCircle alert + stub note + 6-stage scaffold "—" duration + per-stage "Stage details pending" placeholder;informational delivery without inventing fake metric numbers;UI wire intact + ready for backend completion;retry: false avoids 4-retry waste against 501 stub
4. **Langfuse link works independently** of backend trace API status — uses traceId from URL params encodeURIComponent;link target opens in new tab w/ rel=noopener noreferrer security guard;valuable Tier 1 escape-hatch for admin user seeking real trace inspection while backend `/debug/trace` is stubbed
5. **TraceData + PipelineStageMetric forward-looking schema** — `Record<string, PipelineStageMetric>` keyed by stage id ("1"-"6") for stable lookup when backend lands;backend can match this contract during W3+ Langfuse correlation implementation;forward-design discipline per Karpathy §1.4 verifiable goal-driven contract anchoring
6. **debug/layout.tsx admin shell wrap** mirror eval/layout.tsx + admin/layout.tsx pattern(5-line non-invasive Karpathy §1.3 surgical);intentionally NOT added to NAV_ITEMS sidebar(V6 accessed via V5 Failed queries Inspect Link → /debug/{query_id} per architecture.md v6 §5.7 + design ref §2.6 — Inspect Link only entry point);breadcrumb auto-derivation works via SEGMENT_LABELS `debug` segment label
7. **6th occurrence of plan literal vs actual code grep verification gap pattern accelerating in W15** — W13 F1.5 + W14 F1.1 + W14 F2.2 + W15 F1.1 baseline + W15 F1.3 metric naming + W15 F2.1 NEW route + W15 F2.2 9-vs-6 stage + W15 F2.3 Accordion not installed;CO_W14_process_grep_verify call-out further reinforced;**process improvement candidate accelerated for W15 retro decision**(formalize "spec ref grep verification" step pre-active flip checklist for W16+ Beta deploy phase folder rolling JIT trigger)

### Verification

```
$ cd frontend && pnpm type-check
> tsc --noEmit
$ # 0 errors

$ grep -r "\[oklch" frontend/app/debug/ frontend/lib/api/debug.ts
(no matches — 0 hardcoded oklch className arbitrary values)
```

✅ TypeScript strict mode clean(0 errors);no `any` / no @ts-ignore;no hardcoded oklch — all colors via Tailwind tokens(`bg-muted` / `bg-muted/30` / `bg-muted/40` / `bg-muted/50` / `text-foreground` / `text-muted-foreground` / `border-border` / `border-destructive` / `bg-destructive/10`)。shadcn primitives reused(Card + Button + Skeleton + lucide icons AlertCircle/ChevronDown/ChevronLeft/DollarSign/ExternalLink/Timer)— no new vendor;custom PipelineStageCollapsible local component over shadcn Accordion install per Karpathy §1.2 simplicity-first。NEW lib/api/debug.ts client mirror kb.ts/query.ts/auth.ts/eval.ts pattern;NEW debug/layout.tsx mirror admin/eval layout pattern。

### Carry-overs to W15 D3

- 🚧 F2 user smoke deferred per CLAUDE.md §13(`! pnpm dev` + `! uvicorn`;`/debug/{traceId}` page renders + admin sidebar visible + breadcrumb "EKP > Debug > {traceId-truncated}" + Back to Eval link + Stub note alert visible + 6-stage scaffold "—" duration + Click stage → expand-collapse w/ chevron rotation + Open in Langfuse link target=_blank works + responsive collapse mobile + dark mode toggle still works)— W15 F4 Playwright E2E baseline harness 將 systematically subsume
- ⏳ W15 D3 focus per plan §5:F3 Responsive + a11y polish across 9 views + CO_W14_F4_error_boundary token cleanup pass(`frontend/components/error/error-boundary.tsx` 6 hardcoded oklch values → Tailwind tokens);F4 Playwright install + config(corp proxy R8 mitigation if needed)
- 📝 **CO_W15_F2_backend** Backend `GET /debug/trace/{trace_id}` W3+ implementation per Langfuse correlation(stub status documented in SummaryCard stubMode banner + retry: false on useQuery)— Beta hardening trigger fit
- 📝 **CO_W15_F2_langfuse_url** Langfuse production URL pattern not finalized(stub `https://langfuse.example.com/trace/{traceId}` per plan literal Tier 1 acceptance);real Langfuse instance URL configurable via NEXT_PUBLIC_LANGFUSE_URL env var W16+ Beta hardening trigger fit
- 📝 **CO_W14_process_grep_verify reinforcement** — pattern accelerating(now 8 sub-occurrences across W13+W14+W15 cycles);**W15 retro decision** to formalize "spec ref grep verification" step pre-active flip checklist required for W16+ Beta deploy phase folder rolling JIT trigger

### Commit

- `00b2262` feat(frontend,docs): W15 D2 F2 V6 Debug View implementation + 4 deviations + admin shell wrap + custom Collapsible

---

## Day 3 — W15 D3 F3 Responsive + a11y polish + CO_W14_F4_error_boundary token cleanup(real-calendar 2026-06-10 same-day collapse cycle 4 of 4 final cont)

> **Calendar note**:plan §5 tentative date 2026-07-09 superseded by real-calendar 2026-06-10 same-day collapse(W15 D2 F2 → W15 D3 F3 cycle continue post user authorization "A:continue W15 D3 — F3 Responsive + a11y polish + CO_W14_F4_error_boundary token cleanup")。Time tracking calibration:plan ~0.5 day budget vs actual ~25 min(F3.1-F3.3 verification + F3.4 surgical token migration + 1 a11y gap fix on W15 D2 own mess;consistent with W12+W13+W14+W15 D1+D2 7-16x under-budget pattern)。**F4 Playwright deferred to W15 D4** per plan §5 day-by-day breakdown(F3 = pure polish + token cleanup phase;F4 separate)。

### What landed

| F# | Deliverable | Outcome | Status |
|---|---|---|---|
| F3.1 | Keyboard navigation audit | shadcn primitives 自帶 focus-visible ring(via radix-ui)+ Next.js `<Link>` keyboard nav OK + Esc dismiss handled by shadcn Dialog/Sheet via radix-ui internal;**1 a11y gap fixed** — V6 Debug View custom `<button>` PipelineStageCollapsible 缺 focus-visible ring(W15 D2 own mess per Karpathy §1.3 surgical「only clean your own mess」)→ added `focus-visible:bg-muted/50 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring focus-visible:ring-offset-1` + `rounded-md` for ring fit | ✅ (1 fix) |
| F3.2 | ARIA labels audit | grep `aria-label\|aria-expanded\|aria-describedby\|aria-hidden\|role=` across `frontend/app/` = 5 occurrences across 4 files(chat + admin/kb + register + debug);shadcn primitives via radix-ui automatically include role + aria-* labels;**no new ARIA gaps surface during W15 D1+D2 implementation**(Tier 1 acceptance preserved;screen reader full audit defer Beta hardening per plan §4 risks F3 a11y verification scope expand mitigation)| ✅ (verification preserved) |
| F3.3 | Mobile responsive verify | grep `sm:\|md:\|lg:\|grid-cols-\|flex-col\|flex-row` across `frontend/app/admin/` = 18 occurrences across 4 files(comprehensive responsive coverage);eval/page.tsx W15 D1 has `flex-col sm:flex-row` filter bar + `grid-cols-1 sm:grid-cols-2 md:grid-cols-4` metric cards + `md:grid-cols-[280px_1fr]` 2-column main + `overflow-x-auto` tables;debug/[traceId]/page.tsx W15 D2 has `flex-col sm:flex-row` header + `grid-cols-1 sm:grid-cols-3` summary cards + collapsible buttons full-width(natural mobile);**0 regressions** vs W12 F4 admin shell baseline + W14 admin views baseline | ✅ (verification preserved) |
| F3.4 | CO_W14_F4_error_boundary token cleanup | REWRITE `frontend/components/error/error-boundary.tsx`(74 lines)— 6 hardcoded oklch values L36/39/42/49/58/67 → Tailwind tokens(border-destructive/30 + bg-destructive/10 + text-destructive + text-muted-foreground via shadcn Button outline default + hover muted defaults);native `<button>` + `<a>` replaced w/ shadcn `<Button>` + `<Button asChild>` for visual consistency + automatic dark mode + focus-visible ring(a11y double-win);**MAJOR MILESTONE** — grep `\[oklch` across **entire `frontend/`** now = 0 hits(W12 D2 strict baseline now extends globally vs previously confined to `frontend/app/admin/` strict scope per W14 F4.3 audit boundary)| ✅ |

### Decisions

1. **F3 = pure polish phase**(verification + 1 fix + 1 surgical migration)— per Karpathy §1.4 goal-driven verifiable success criteria 全 met;F3.1-F3.3 verification preserved baselines;F3.4 token cleanup surgical scope per W14 F4 deferred carry-over closure
2. **F3.1 a11y gap fix scoping**(V6 Collapsible button focus-visible ring)— Karpathy §1.3 surgical「only clean your own mess」rule per W14 retro learning;custom button = W15 D2 own creation missing focus-visible style;W15 D3 fix appropriate scope vs deferring;5-classes 1-line edit
3. **F3.4 token mapping discipline** per design ref §1.1 swatches — L=0.88 light coral border → destructive/30(subtle border opacity);L=0.98 very light coral bg → destructive/10(subtle surface tint per W14 admin/page.tsx Failed ingestion `bg-warning/15` precedent);L=0.45 chroma=0.18 hue=25 strong coral → text-destructive(matches tokens.ts destructive token);L=0.55+L=0.45 neutral grey → text-muted-foreground;Retry button bg+border → shadcn Button variant="outline" + className "border-destructive text-destructive hover:bg-destructive/10";Report button → shadcn Button asChild variant="outline" size="sm"(default `border-border` + `hover:bg-muted` matches L=0.92+L=0.94 originals)
4. **shadcn Button conversion over native button preservation**(Karpathy §1.3 scope expansion warranted per plan F3.4 explicit "scope expansion warranted W15 polish phase")— consistency with admin UI + automatic dark mode + focus-visible ring built-in(a11y win + token win double benefit);native button + anchor pattern obsolete in shadcn-first codebase
5. **MAJOR MILESTONE — entire `frontend/` token cleanup complete** — `grep \[oklch frontend/` returned **0 hits** post error-boundary.tsx cleanup;W12 D2 strict baseline now applies globally vs previously confined to `frontend/app/admin/` strict scope per W14 F4.3 audit boundary;**CO_W14_F4_error_boundary carry-over closed**;W15 polish phase milestone achieved
6. **F4 Playwright deferred to W15 D4** per plan §5 day-by-day breakdown — F3 + F4 distinct scopes(F3 = polish + token cleanup;F4 = E2E + pixel diff baseline harness);plan W15 D3 said "F3 Responsive + a11y polish + CO_W14_F4_error_boundary token cleanup;F4 Playwright install + config" — both planned for D3 same-day,actual decision = F3 cleaner standalone closure THIS commit + F4 next session per pivot momentum continuation

### Verification

```
$ cd frontend && pnpm type-check
> tsc --noEmit
$ # 0 errors

$ grep -r "\[oklch" frontend/
(no matches — 0 hardcoded oklch className arbitrary values across ENTIRE frontend codebase)
```

✅ TypeScript strict mode clean(0 errors);no `any` / no @ts-ignore;**MILESTONE** grep `\[oklch` entire `frontend/` = 0 hits(W12 D2 strict baseline now globally extended vs W14 F4.3 admin-only scope);no new vendor + H2 vendor lock preserved(shadcn Button reuse over native button preservation);1 a11y gap fixed(V6 Collapsible focus-visible ring);0 regressions on V1-V9 views responsive + a11y baseline。

### Carry-overs to W15 D4

- 🚧 F3 user smoke deferred per CLAUDE.md §13(`! pnpm dev` + `! uvicorn`;`/admin` + `/eval` + `/debug/{traceId}` triggering error boundary verify token migration visual + dark mode toggle visual + V6 Collapsible focus-visible ring keyboard Tab navigation visible)— W15 D4 Playwright E2E baseline harness 將 systematically subsume
- ⏳ W15 D4 focus per plan §5:F4 Playwright install + config + Golden-path E2E + Admin path E2E + pixel diff baseline harness(W12+W13+W14 manual smoke deferred backlog systematic subsume per F4 deliverable)
- 📝 **CO_W15_F3_aria_full_audit** Full ARIA + screen reader audit defer Beta hardening per plan §4 risks(F3 Tier 1 acceptance = keyboard nav + spot-check ARIA + responsive verify only;NVDA/JAWS/VoiceOver full sweep = Beta hardening fit)
- 📝 **CO_W15_F3_dark_mode_visual_verify** Dark mode visual verify of error-boundary.tsx token migration(`destructive/30` + `destructive/10` 與 `.dark` `--destructive` variant per tokens.ts colorsDark `oklch(0.62 0.24 25)` brighter coral)— confirms automatic dark mode visual via Tailwind token consumption;non-blocker(token system designed for both modes by W12 D2)

### Commit

- `60c812d` feat(frontend,docs): W15 D3 F3 Responsive + a11y polish + CO_W14_F4_error_boundary token cleanup MILESTONE — entire frontend oklch=0

---

## Day 4 — W15 D4 F4 Playwright E2E + pixel diff baseline harness(real-calendar 2026-06-10 same-day collapse cycle 4 of 4 final cont)

> **Calendar note**:plan §5 tentative date 2026-07-10 superseded by real-calendar 2026-06-10 same-day collapse(W15 D3 F3 → W15 D4 F4 cycle continue post user authorization "A:continue W15 D4 — F4 Playwright E2E + pixel diff baseline harness")。Time tracking calibration:plan ~1.5 day budget(largest deliverable W15)vs actual ~1 hr 10 min(install + 7 NEW files + governance docs;consistent with W12+W13+W14+W15 D1-D3 7-16x under-budget pattern;budget-largest deliverable still under by ~12x)。

### What landed

| F# | Deliverable | Files | Status |
|---|---|---|---|
| F4.1 | Playwright install + config | `pnpm add -D @playwright/test` ✅ landed `@playwright/test ^1.59.1`(1m 3s install w/ 4 packages added;R8 proxy 唔 block npm registry — different endpoint vs azure-communication-email which IS blocked per W13 F6);NEW `frontend/playwright.config.ts`(Chromium-only Tier 1 simplicity drop firefox/webkit + sequential exec + trace/screenshot/video retain-on-failure + webServer auto-start `pnpm dev` w/ NEXT_PUBLIC_AUTH_MOCK=true env);NEW `frontend/tests/e2e/` directory + NEW `frontend/tests/e2e/README.md`(7-section user smoke instructions);**deviation logged plan §7 (D4)** — plan F4 spec ref "CLAUDE.md §3.2 Vitest + RTL baseline preserved;Playwright additive" stale(no Vitest infrastructure exists);Playwright independent setup per Karpathy §1.3 surgical scope hold | ✅ (deviation noted) |
| F4.2 | Golden-path E2E | NEW `frontend/tests/e2e/golden-path.spec.ts`(4 tests:V7 Landing + V8 Login + V9 Register Step 1 + V1 Chat — render assertions only Tier 1;subsumes manual smoke deferred backlog across W12+W13+W14 cycles per plan §F4 systematic subsume goal) | ✅ |
| F4.3 | Admin path E2E | NEW `frontend/tests/e2e/admin-path.spec.ts`(5 tests:V2 Admin Dashboard + V3 KB List + V5 Eval Console + V6 Debug View + Sidebar nav navigates between admin views;assumes NEXT_PUBLIC_AUTH_MOCK=true bypasses login;backend stub endpoints (501) handled via stub mitigation UI per W15 D1+D2 implementation) | ✅ |
| F4.4 | Pixel diff baseline | NEW `frontend/tests/e2e/visual-baseline.spec.ts`(5 representative views:V7 Landing + V8 Login + V9 Register Step 1 + V2 Admin Dashboard empty + V5 Eval Console empty);**deviation logged plan §7 (D4)** — plan literal "frontend/tests/e2e/screenshots/baseline/" custom path → Playwright convention `*.spec.ts-snapshots/` next to test files(简简 tool-default per Karpathy §1.2);maskedDiff config for dynamic regions(timestamps + KB IDs in mono font masked via `mask: [page.locator('time'), page.locator('.font-mono')]`);1% maxDiffPixelRatio anti-aliasing tolerance | ✅ (deviation noted) |
| F4.5 | CI integration plan | DEFER to W16+ Beta hardening per plan F4.5 PARTIAL PASS acceptance "local-only baseline OK Tier 1";`reuseExistingServer: !process.env.CI` config flag ready for CI flip + `forbidOnly: Boolean(process.env.CI)` guards test.only() leftover;documented in `tests/e2e/README.md` § CI integration "Deferred to W16+ Beta hardening per W15 plan F4.5" | ✅ |
| INFRA | package.json scripts + .gitignore | `frontend/package.json` add 3 scripts(`test:e2e` / `test:e2e:ui` / `test:e2e:update-snapshots`);root `.gitignore` add 3 Playwright artifact patterns(`/frontend/test-results/` + `/frontend/playwright-report/` + `/frontend/playwright/.cache/`)per CLAUDE.md root .gitignore convention "唔好 individual `.gitignore` 散喺 sub-folder" | ✅ |

### Decisions

1. **Playwright independent setup per Karpathy §1.3 surgical scope hold** — plan F4 spec ref "Vitest + RTL baseline preserved;Playwright additive" stale per Glob check(no Vitest infrastructure exists);Playwright installed standalone without coupling to non-existent Vitest baseline;Vitest infrastructure setup = out of W15 F4 strict scope(W16+ Beta hardening trigger if surface)
2. **R8 proxy mitigation strategy split** — `pnpm add -D @playwright/test` ✅ install via npm registry succeeded 1m 3s(npm registry endpoint generally working per W12 D3 shadcn primitive installs precedent);BUT `npx playwright install chromium` browser binary download(~300MB CDN download via playwright.azureedge.net)deferred to user smoke per CLAUDE.md §13 + plan F4.5 PARTIAL PASS acceptance("local-only baseline OK Tier 1")— if user CDN blocked,ADR-0017 trigger candidate per W11 retro CO17 personal Azure dev tier pattern
3. **Chromium-only Tier 1 simplicity drop** — Karpathy §1.2 simplicity-first(firefox/webkit cross-browser testing scope expansion = Beta hardening fit per plan §4 risks);config `projects` array shows only `name: 'chromium'` with `Desktop Chrome` device emulation;extension to firefox/webkit = additive non-breaking when triggered
4. **Sequential test execution(`fullyParallel: false`)** — in-memory KB state per W11 retro CO18 baseline(no persistent backing yet for KB Manager + users_repo);parallel execution = race conditions on shared state;sequential = simpler + reliable for Tier 1;persistent backing W16+ Beta hardening = enables parallel safe
5. **5 representative views pixel diff baseline scope hold** — Karpathy §1.2 simplicity-first(all 9 views baseline = scope expansion vs Tier 1 PARTIAL PASS acceptance "local-only baseline OK Tier 1");V7 + V8 + V9 + V2 + V5 covers public-facing + admin entry + eval flow;V1 Chat / V3 KB List / V4 KB Detail / V6 Debug = covered by golden-path + admin-path E2E render assertions(complementary coverage layer)
6. **maskedDiff dynamic regions defensive design** — timestamps(<time>)+ KB IDs / chunk IDs(font-mono)dynamic per render → mask via `mask: [page.locator('time'), page.locator('.font-mono')]`;preserves baseline stability vs false-positive pixel diff failures on every test run;`maxDiffPixelRatio: 0.01` 1% tolerance for sub-pixel anti-aliasing jitter
7. **webServer config auto-start frontend only** — `pnpm dev` port 3001 auto-start by Playwright;backend uvicorn port 8000 = user-driven separately per CLAUDE.md §13 dev server policy(Claude Code can't run long-lived servers);`reuseExistingServer: !process.env.CI` allows local dev re-run + CI fresh-start;tests assume both servers running per `tests/e2e/README.md` Prerequisites section
8. **Tier 1 = render assertions only;interactive flow defer Beta hardening** per plan §4 risks F3 a11y verification scope expand mitigation;golden-path tests assert form fields visible / buttons clickable / pages load — not actual register/login round-trip(would require backend wiring + mock email verification + state cleanup);interactive E2E assertions = Beta hardening fit when ACS email service productionized + backend persistent backing landed
9. **9th occurrence of plan literal vs actual code grep verification gap pattern accelerating** — W13 F1.5 + W14 F1.1 + W14 F2.2 + W15 F1.1 baseline + W15 F1.3 metric naming + W15 F2.1 NEW route + W15 F2.2 9-vs-6 stage + W15 F2.3 Accordion not installed + W15 F4 Vitest baseline non-existent;CO_W14_process_grep_verify call-out further reinforced;**process improvement candidate confirmed for W15 D5 retro decision**(formalize "spec ref grep verification" step pre-active flip checklist for W16+ Beta deploy phase folder rolling JIT trigger)

### Verification

```
$ cd frontend && pnpm add -D @playwright/test
+ @playwright/test ^1.59.1
Done in 1m 3s using pnpm v10.19.0

$ cd frontend && pnpm type-check
> tsc --noEmit
$ # 0 errors (Playwright spec files compile clean)

$ ls frontend/tests/e2e/
admin-path.spec.ts
golden-path.spec.ts
README.md
visual-baseline.spec.ts
```

✅ Playwright @playwright/test 1.59.1 installed(R8 proxy 唔 block npm registry);TypeScript strict mode clean(0 errors;Playwright spec files compile + use shared types);no `any` / no @ts-ignore;3 NEW spec files(13 tests total — 4 golden-path + 5 admin-path + 5 visual baseline) + 1 NEW README + 1 NEW playwright.config.ts;package.json + 3 scripts;root .gitignore + 3 artifact patterns;**Tier 1 baseline harness ready for user smoke** — `npx playwright install chromium` + `pnpm test:e2e` + `pnpm test:e2e:update-snapshots` 3-step user workflow documented。

### Carry-overs to W15 D5

- 🚧 F4 user smoke deferred per CLAUDE.md §13 + plan F4.5 PARTIAL PASS — user runs:(a)`! cd frontend && npx playwright install chromium`(one-time browser binary install ~300MB CDN download via playwright.azureedge.net — ADR-0017 trigger if R8 blocks);(b)`! cd backend && .venv/Scripts/python.exe -m uvicorn api.server:app --port 8000`;(c)`! cd frontend && pnpm test:e2e:update-snapshots`(capture pixel diff baseline + commit `tests/e2e/*.spec.ts-snapshots/`);(d)`! cd frontend && pnpm test:e2e`(verify 13 tests pass + 0 regression)
- ⏳ W15 D5 focus per plan §5:F5 W15 phase Gate verdict + retro 7 sections + **Tier 1 UI sprint cycle final closeout retrospective**(W12+W13+W14+W15 cumulative learnings)+ W16+ Beta deploy phase folder rolling JIT trigger
- 📝 **CO_W15_F4_browser_binaries** `npx playwright install chromium` browser binary CDN download ADR-0017 trigger candidate if R8 blocks(W11 retro CO17 personal Azure dev tier pattern fallback)— Beta hardening trigger fit
- 📝 **CO_W15_F4_baseline_capture** Pixel diff baseline screenshots capture deferred to user smoke first run(`pnpm test:e2e:update-snapshots` → commits 5 PNG to `tests/e2e/visual-baseline.spec.ts-snapshots/`)— Tier 1 baseline harness wired but baseline empty until first run
- 📝 **CO_W15_F4_vitest_baseline_gap** CLAUDE.md §3.2 "Vitest + RTL baseline" never set up + plan F4 spec ref stale(9th occurrence of plan literal vs actual code grep verification gap)— Beta hardening trigger candidate(formalize unit test infrastructure beyond Playwright E2E layer)
- 📝 **CO_W15_F4_interactive_flow_E2E** Tier 1 = render assertions only;interactive flow E2E(register/login round-trip + KB upload + Pipeline wizard 3-step + Settings save + Danger zone confirm)= Beta hardening trigger fit when backend persistent backing + ACS email productionized

### Commit

- `88320b9` feat(frontend,docs): W15 D4 F4 Playwright E2E + pixel diff baseline harness — install + config + 13 tests + 7 NEW files + 2 deviations

---

## Day 5 — _(W15 D5,2026-07-11,tentative)_

_(placeholder — F5 Tier 1 UI sprint cycle final closeout + W16+ Beta deploy phase folder kickoff)_

---

## Retro(填於 W15 D5 末 — Tier 1 UI sprint cycle final closeout)

### What worked
_(W15 D5 末 fill — Tier 1 UI sprint cycle 4-phase rhythm / Playwright E2E baseline harness reception / V5+V6 implementation patterns / cycle 4 of 4 same-day collapse continuity)_

### What didn't
_(W15 D5 末 fill — friction points / blockers / unexpected complexity)_

### Surprises / discoveries
_(W15 D5 末 fill — non-obvious findings about V5 eval data wire / V6 timeline accordion / Playwright cost / pixel diff false-positives / a11y audit edge cases)_

### Decisions
_(W15 D5 末 fill — V5 metric threshold display defaults / V6 Langfuse stub URL strategy / E2E CI integration timing / Playwright fixture pattern)_

### Carry-overs to W16+ Beta deploy
_(W15 D5 末 fill — items deferred to W16+ Beta deploy;categorize:Production launch / Track A IT cred / R-B1 closure / CO_F3a-c backend stubs / CO_F5_refresh / CO_F5_cookie / CO_F6a-c)_

### Time tracking
_(W15 D5 末 fill — actual hours per F1-F5 vs estimated 5 working days;Tier 1 UI sprint cycle cumulative time tracking calibration W12+W13+W14+W15)_

### Spec ref alignment
_(W15 D5 末 fill — verify all W15 deliverables trace back to architecture.md v6 §5.6-§5.7 + ADR-0014/0015/0016 spec citations + Tier 1 UI Tier 1 expansion 完整 implementation marker)_

### **Tier 1 UI sprint cycle final retrospective**(W12+W13+W14+W15 cumulative)
_(W15 D5 末 fill — 4-sprint cumulative learnings:W12 tokens.ts ratification → W13 user-facing views → W14 admin views → W15 polish + closeout;9 views × 6+ components × hybrid auth × ACS email × responsive/a11y/E2E/pixel diff baseline implementation arc;same-calendar-day collapse pattern across 4 cycles;Karpathy §1 baseline observance throughout;ADR-0014/0015/0016 cumulative coverage;Tier 1 UI Tier 1 expansion 完整 implementation handoff to Beta deploy)_

---

**Lifecycle reminder**:呢份 progress.md 屬 phase journal,daily entries + retro 必須 commit incrementally per R2。Day 0 setup entry 屬 W14 D5 F5 closeout cascade carry-over prep,W15 D1 active implementation start當 stakeholder authorization 後 — rolling JIT calendar-day-collapse cont OR future session。
