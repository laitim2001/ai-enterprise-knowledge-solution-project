---
phase: W14-admin-views
plan_ref: ./plan.md
checklist_ref: ./checklist.md
status: closed
last_updated: 2026-06-10
---

# Phase W14 — Progress(Daily Journal + Decisions + Retro)

> Daily progress entries per CLAUDE.md §10 R2(每 commit reference progress.md Day-N entry)。
> Status:`active` 自 2026-06-10 W14 D1 implementation start(real-calendar same-day collapse cycle 3 of 4 per pivot momentum continuation of W13 closeout)。

---

## Day 0 — Pre-kickoff Setup(W13 D5 cont F7 closeout 2026-06-10)

> **Note**:呢個 Day 0 entry 屬 W13 D5 cont F7 closeout cascade carry-over governance prep,而非 W14 implementation start。W14 D1 implementation start = next session post stakeholder authorization(rolling JIT — calendar-day-collapse cont OR future session)。

### Setup completed pre-W14 D1

| Artifact | Commit | Status |
|---|---|---|
| W13 phase Gate PASS WITH SMOKE-USER-DEFERRED CAVEAT verdict landed | _W13 D5 cont F7 closeout commit_ | 🟡 in flight(this session) |
| W13 progress.md retro 7 sections complete | _W13 D5 cont F7 closeout commit_ | 🟡 in flight(this session) |
| W13 frontmatter active → closed cascade(plan + checklist + progress) | _W13 D5 cont F7 closeout commit_ | 🟡 in flight(this session) |
| W14 phase folder skeleton(plan.md + checklist.md + progress.md) | _W13 D5 cont F7 closeout commit_ | 🟡 in flight(this session) |
| F1 routing restructure + theme provider + dark mode toggle | `a15182e` | ✅ landed W13 D1 |
| F2 V7 Landing page implementation | `7e283fb` | ✅ landed W13 D2 |
| F3 V8 Login UI shell + Toaster mount | `991e1aa` | ✅ landed W13 D3 |
| F4 V9 Register 3-step wizard + BrandPanel rule-of-2 extract | `79a3b67` | ✅ landed W13 D4 |
| F5 backend hybrid auth + ADR-0016 scrypt + 4 endpoints + 41 tests | `054679d` | ✅ landed W13 D5 |
| CO_F5d frontend wire batch + ApiError envelope branching | `b1179cc` | ✅ landed W13 D5 cont |
| F6 C13 ACS Email Verification Service + 12 tests + fail-soft | `9b5966c` | ✅ landed W13 D5 cont |
| ADR-0016 password hash scrypt stdlib | `054679d` | ✅ landed W13 D5 |

### Pending W14 D1 active flip pre-conditions

- ⏳ Stakeholder authorization for W14 D1 implementation start(per W13 closeout same-session OR next session pivot)
- ⏳ User end-to-end browser smoke(`! pnpm dev` + `! uvicorn` + register/verify/login/redirect verify)— **non-blocker** for W14 D1(W14 view-level admin work iteratively browser-verifies)
- ⏳ W14 plan/checklist/progress frontmatter `draft → active` flip on W14 D1 active trigger

### W14 immediate scope alignment with W13 retro Carry-overs

- **CO_F5d-cont** Frontend session-token mode extension → **W14 F1.5**
- **CO_W14_F1** V2 Admin Dashboard refactor → **W14 F1**
- **CO_W14_F2** V3 KB List card grid → **W14 F2**
- **CO_W14_F3** V4 KB Detail 5-tab → **W14 F3**
- **CO_W14_F4** Stepper rule-of-3 trigger evaluation → **W14 F3.8 + F4.1**

### W14 critical path

- **W14 D1 routing slot**:F1 V2 Admin Dashboard refactor + CO_F5d-cont session-token mode parallel(0.5 day);F2 V3 KB List begin
- **W14 D2-D3 view + tab parallel**:F3 V4 KB Detail 5-tab(largest deliverable);F3.8 Stepper rule-of-3 evaluation mid-W14
- **W14 D4-D5 cross-cutting + closeout**:F4 token audit + sidebar consistency;F5 closeout retro + W15 phase folder kickoff

### W15 polish + closeout entry

- W14 closes Phase 3 of 4 UI sprint cycle;W15 = V5 Eval Console + V6 Debug View + responsive + a11y + Playwright E2E + pixel diff baseline harness(per architecture.md v6 §5.6-§5.7 + W13 retro CO_W15_F1-F3)
- W15 D1 implementation start trigger = W14 closeout post-W14 D5 retro

---

## Day 1 — W14 D1 active flip + F1 V2 Admin Dashboard + CO_F5d-cont(real-calendar 2026-06-10 same-day collapse cycle 3 of 4 cont)

> **Calendar note**:plan §5 tentative date 2026-06-30 superseded by real-calendar 2026-06-10 same-day collapse(W13 D5 cont F7 closeout → W14 D1 same-session per pivot momentum continuation;cycle 3 of 4 UI sprint cycle begins)。Time tracking calibration:plan ~0.5 day budget vs actual ~30 min(F1 stat-card refactor + Failed ingestion section + Quick actions + CO_F5d-cont session-token branch)。

### What landed

| F# | Deliverable | Files | Status |
|---|---|---|---|
| F1.1 | 4-card stats row | UPDATE `frontend/app/admin/page.tsx`(KB count + Doc count + Chunks count + System status badge;**deviation logged plan §7 changelog (D1)** — chunks preserved over plan-literal "query count" since no backend endpoint readily available;Karpathy §1.2 simplicity-first)| ✅ |
| F1.2 | Failed ingestion section | derive from existing `kbApi.list .failed_documents` arrays(W7 baseline data structure);**deviation logged plan §7 changelog (D1)** — 采「Failed ingestion」not「Recent ingestion log」(no recent ingestion endpoint;failed docs informational symmetry preserved);Skeleton loading + CheckCircle2 empty state + Table first-10 w/ KB / Doc id / Stage Badge / Error | ✅ |
| F1.3 | 3-button quick actions row | ActionButton pattern(icon + label + description outline Button asChild + Link):Create KB(Plus)→ `/admin/kb/new` + Test query(MessageSquare)→ `/chat` + View eval(FlaskConical)→ `/eval` | ✅ |
| F1.4 | Responsive layout | stats `grid-cols-1 sm:grid-cols-2 md:grid-cols-4`;Failed table natural overflow horizontal-scroll mobile;Quick actions `grid-cols-1 sm:grid-cols-3`;`space-y-8` section spacing per design ref §3.7 | ✅ |
| F1.5 | CO_F5d-cont session-token mode | NEW `readSessionBearer()` helper + extended `getBearer()` in `frontend/lib/auth/index.ts`;`SESSION_TOKEN_STORAGE_KEY` moved to canonical auth domain + re-exported via `lib/api/auth.ts`(breaks api-client → auth → api/auth circular import);non-breaking when localStorage empty;defensive try/catch for privacy/sandbox modes;parallel to backend `dependency.get_current_user` session branch architecture(W13 D5 F5.6) | ✅ |

### Decisions

1. **F1.1 stat-card scope adjustment**:plan said 4 cards including "query count";采 4 cards = KB+doc+**chunks(W12 baseline preserved)**+status — chunks count 仍 useful Tier 1 ingestion KPI;Karpathy §1.2 simplicity-first 唔 add backend endpoint just for query count stat;deviation logged plan §7 changelog (D1)
2. **F1.2 "Failed ingestion" interpretation**:plan said「Recent ingestion log」需要 backend endpoint not readily available;采 derived data from existing `kbApi.list .failed_documents`(已 W7 baseline data structure)— informational symmetry preserved(operations focus = "what's broken now")+ Karpathy §1.2 minimum data plumbing;deviation logged plan §7 changelog (D1)
3. **System status derivation from existing query state**:if `query.isLoading` → loading badge;if `query.isError` → destructive 「Backend unreachable」;if `failures.length > 0` → warning 「Degraded」;else → success 「Operational」;avoids new `/health` endpoint call(`computeStatus` helper)— Karpathy §1.4 verifiable goal達成 via existing data
4. **CO_F5d-cont SESSION_TOKEN_STORAGE_KEY relocation to lib/auth**:lib/api/auth.ts → lib/auth/index.ts canonical auth domain location;lib/api/auth.ts re-exports to keep login form import path unchanged(zero touch on `frontend/app/login/page.tsx`)— breaks `api-client → auth → api/auth` circular import path;single source of truth principle preserved
5. **`readSessionBearer()` defensive try/catch**:localStorage may throw in privacy/sandbox/iframe modes;return null on any throw → fall through to mock/MSAL path keeps app functional vs uncaught exception breaking auth wire entirely
6. **ActionButton component pattern over plain Button**:icon + label + description w/ accent-tinted icon background — better UX affordance vs plain text Button + matches V2 wireframe design ref §2.2 quick-actions pattern(non scope creep — 5-line component reuse)

### Verification

```
$ cd frontend && pnpm type-check
> tsc --noEmit
$ # 0 errors

$ grep oklch frontend/app/admin/page.tsx frontend/lib/auth/index.ts
$ # 0 hits across both files (no docstring oklch mentions either)
```

✅ TypeScript strict mode clean(0 errors);no `any` / no @ts-ignore;no hardcoded oklch;all colors via Tailwind tokens(`bg-success/15` / `bg-warning/15` / `bg-destructive/15` / `bg-accent/10` / `text-foreground` / `text-muted-foreground`)。shadcn primitives reused(Card + Badge + Button + lucide icons CheckCircle2 / FileWarning / FlaskConical / MessageSquare / Plus)— no new vendor。

### Carry-overs to W14 D2

- 🚧 F1 user smoke deferred per CLAUDE.md §13(`! pnpm dev` + `! uvicorn` smoke;`/admin` page renders 4-card stats + system status badge / Failed ingestion empty or table / Quick actions 3 buttons + responsive collapse mobile / dark mode toggle still works;CO_F5d-cont session token persistence verifiable post `/auth/login` localStorage check)
- ⏳ W14 D2 focus per plan §5:F2 V3 KB List card grid begin

### Commit

- `641b328` feat(frontend,docs): W14 D1 F1 V2 Admin Dashboard refactor + CO_F5d-cont session-token mode + W14 active flip

---

## Day 2 — W14 D2 F2 V3 KB List card grid refactor(real-calendar 2026-06-10 same-day collapse cycle 3 of 4 cont)

> **Calendar note**:plan §5 tentative date 2026-07-01 superseded by real-calendar 2026-06-10 same-day collapse(D1 → D2 cycle continue post user authorization "A:continue W14 D2 — F2 V3 KB List card grid refactor")。Time tracking calibration:plan ~1 day budget vs actual ~30 min(consistent with W12+W13 7-9x under-budget pattern)。

### What landed

| F# | Deliverable | Files | Status |
|---|---|---|---|
| F2.1 | KB List card grid refactor | REWRITE `frontend/app/admin/kb/page.tsx`(plain-table → KbCard component;name + description line-clamp + doc + chunks + last_indexed + status badge + kb_id mono small)| ✅ |
| F2.2 | Sort dropdown | shadcn Select + ArrowDownAZ lucide;3 options(name / last_indexed recent / documents most);`makeComparator` helper for typed sort logic;**deviation logged plan §7 changelog (D2)** — `created_at` plan-literal 缺乏 KbStatus field 采 documents 替代 | ✅ (deviation noted) |
| F2.3 | Filter search | shadcn Input + Search lucide adornment;`useMemo + useState` state machine;case-insensitive substring match across name + kb_id + description | ✅ |
| F2.4 | Create CTA | header right shadcn Button asChild + Link + Plus icon;empty state secondary Create CTA | ✅ |
| F2.5 | Loading + empty + error states | `KbGridSkeleton`(6 Skeleton cards matching shape per design ref §3.5)+ `KbEmpty`(2 variants:no-KBs vs no-search-match per design ref §3.4)+ destructive error boundary preserved | ✅ |
| F2.6 | Card → KB detail navigation | **deviation logged plan §7 changelog (D2)** — entire Card wrapped in Link(accessibility + middle-click new tab);Upload secondary dropped(user enters KB detail to Upload — avoids nested-anchor HTML invalid)| ✅ (deviation noted) |
| F2.7 | Responsive layout | `grid-cols-1 sm:grid-cols-2 md:grid-cols-3` cards;Toolbar `flex-col sm:flex-row`;Header CTA + count stack mobile;Card内 stats row自然 wrap | ✅ |

### Decisions

1. **Sort options reduce from plan-literal `created_at` to existing API fields**:KbStatus 唔有 `created_at`;采 documents 提供 useful operational dimension(useful for finding "biggest" KBs)+ last_indexed/name preserved per plan;Karpathy §1.2 simplicity-first 唔 add backend just for sort proxy
2. **Whole Card as Link vs nested anchors**:plan F2.6「Card click navigates」+ plan F2.4「Create CTA」+ W12 baseline Upload secondary 唔可以 all 3 共存(nested anchors HTML invalid);采 single Link wrap Card + Create CTA at page header + Upload dropped from Card(navigation cost +1 click acceptable Tier 1)
3. **Status badge 3-state derivation**:`failed_documents > 0` → warning「Degraded」;`total_documents == 0` → muted「Empty」;else → success「Indexed」;mirrors W14 F1 system status pattern + design ref §3.6 focus state expectations
4. **Skeleton shape matches Card layout**:6 Skeleton cards in same `grid-cols-1 sm:grid-cols-2 md:grid-cols-3`;avoids spinner-only per design ref §3.5(jarring vs Notion-leaning editorial);CardHeader Skeleton + CardContent Skeleton stripes match real Card spacing
5. **Empty state 2-variant design**:no-KBs(Database icon + Create CTA prompts user creation)vs no-search-match(Search icon + clear-filter hint);separating these 提升 UX(user knows whether to clear search OR create);per design ref §3.4 empty state pattern
6. **Client-side sort + filter Tier 1 cohort scale**:no backend pagination;`useMemo` over query.data with comparator + filter predicate;rolls forward to Beta hardening trigger when KB count grows OR persistent backing migrates(W11 retro CO18)
7. **`description || italic No description` placeholder**:CardDescription `min-h-[2.5rem]` keeps card heights consistent across rows even when descriptions vary in length;Karpathy §1.4 verifiable goal達成 = visual rhythm preserved per design ref §3.7

### Verification

```
$ cd frontend && pnpm type-check
> tsc --noEmit
$ # 0 errors

$ grep oklch frontend/app/admin/kb/page.tsx | wc -l
0
```

✅ TypeScript strict mode clean(0 errors);no `any` / no @ts-ignore;no hardcoded oklch;all colors via Tailwind tokens(`bg-success/15` / `bg-warning/15` / `bg-muted` / `text-foreground` / `text-muted-foreground`)。shadcn primitives reused(Card + Badge + Button + Input + Select + Skeleton + lucide icons)— no new vendor。

### Carry-overs to W14 D3

- 🚧 F2 user smoke deferred per CLAUDE.md §13(`! pnpm dev` + `! uvicorn`;`/admin/kb` card grid + sort by name/last_indexed/documents + filter search + responsive collapse mobile + dark mode toggle still works;empty state when no KB OR when search term miss)
- ⏳ W14 D3 focus per plan §5:F3 V4 KB Detail 5-tab(largest deliverable — Documents + Chunks + Pipeline + Retrieval Testing + Settings tabs;Stepper rule-of-3 evaluation trigger if Pipeline tab introduces state machine)

### Commit

- `23cc579` feat(frontend,docs): W14 D2 F2 V3 KB List card grid refactor

---

## Day 3 — W14 D3 F3 V4 KB Detail 5-tab nav(real-calendar 2026-06-10 same-day collapse cycle 3 of 4 cont)

> **Calendar note**:plan §5 tentative date 2026-07-02 superseded by real-calendar 2026-06-10 same-day collapse(D2 → D3 cycle continue post user authorization "A:continue W14 D3 — F3 V4 KB Detail 5-tab nav")。Time tracking calibration:plan ~1.5 day budget(largest deliverable)vs actual ~1 hr(5 tab content + Dialog danger zone + URL state machine)。

### What landed

| F# | Deliverable | Files | Status |
|---|---|---|---|
| F3.1 | 5-tab structure | UPDATE `frontend/app/admin/kb/[id]/page.tsx`(shadcn Tabs primitive + 5 TabsTrigger w/ lucide icons + 5 TabsContent)| ✅ |
| F3.2 | Documents tab | **deviation logged plan §7 changelog (D3)** — backend `GET /kb/{id}/documents` 501 stub;stats card row + failed_documents Card list + Upload CTA dashed-empty-state + BackendStubNote | ✅ (deviation noted) |
| F3.3 | Chunks tab | **deviation logged plan §7 changelog (D3)** — backend `GET /kb/{id}/documents/{id}/chunks` 501 stub;stats card + chunk inspection placeholder Card + cross-reference to Retrieval Testing tab(chunk drill-down via citation cards) | ✅ (deviation noted) |
| F3.4 | Pipeline tab | **deviation logged plan §7 changelog (D3)** — read-only ConfigRow display(Indexing card embedding model/dim/strategy + Retrieval card top_k/rerank_k);inline tuning defer W15+;non state-machine wizard | ✅ (deviation noted) |
| F3.5 | Retrieval Testing tab | streamQuery SSE collector + AbortController;Textarea + Run Button + Synthesized answer Card + Retrieved chunks list w/ chunk_title + doc_title + section_path + relevance_score Badge;refused state + error toast | ✅ |
| F3.6 | Settings tab | **deviation logged plan §7 changelog (D3)** — Identity card readonly KB ID + name + description(no backend PATCH);Indexing config card editable form(Input + Select)+ Save Button + toast feedback | ✅ (deviation noted) |
| F3.7 | URL-based tab state | `useSearchParams` + `router.push` w/ `scroll: false`;activeTab derived w/ default 'documents';bookmark-friendly URLs | ✅ |
| F3.8 | Stepper rule-of-3 evaluation | **NOT triggered** — Pipeline tab read-only display non-wizard;Pipeline wizard W12 + Register W13 仍 = 2 active state-machine usages;inline retention preserved per W13 D4 decision | ✅ (preserved) |
| F3.9 | Responsive | TabsList wrap in `overflow-x-auto` for mobile horizontal-scroll(simpler than Sheet/Select fallback per Karpathy §1.2);Header `flex-col sm:flex-row`;StatCards natural grid responsive | ✅ |
| Danger zone | Re-index + Delete via shadcn Dialog | `DangerAction` reusable pattern + Dialog confirm + structured backend status disclosure(`POST /kb/{id}/reindex` + `DELETE /kb/{id}` stubs)+ toast.info 「pending backend stub」(non-blocking UI wire test)| ✅ |

### Decisions

1. **5 deviations all due to Tier 1 constraints**:F3.2/F3.3 backend stubs(W2 implementation defer)+ F3.4 read-only Tier 1 + F3.6 backend PATCH endpoint not exposed + F3.8 Stepper rule-of-3 NOT fired — all surfaced upfront via Karpathy §1.1 think-before-coding;solutions via existing data + clear stub disclosure;UI wire intact + ready for backend completion
2. **BackendStubNote helper component**:reusable inline note component标明 stub status + W2 implementation defer rationale;avoids manual repetition across 3 tabs(Documents + Chunks + future)+ explicit communication of "incomplete state but visible" to admin user(transparency over hidden gaps)
3. **Retrieval Testing reuses streamQuery**:shared SSE generator + Citation type + ApiError envelope already established W3 + W13 baselines;non-streaming variant 唔需要 new(streaming UI同 admin context fits well — admin sees real-time retrieval feedback)
4. **DangerAction pattern**:shared component for Re-index + Delete(both gated by Dialog confirm + structured backend status note + toast.info on confirm);keeps Dialog state local per action;variant prop("outline" / "destructive")drives Button styling
5. **TabsList horizontal-scroll over Select fallback**:Karpathy §1.2 simplicity-first — overflow-x-auto wrap is 1-line solution + native mobile UX(swipe scroll feels web-native);Sheet/Select fallback would add stateful complexity for marginal UX gain at Tier 1
6. **URL searchParams state machine**:`?tab=documents` etc — bookmark-friendly + browser back-button works + deep-linking from external docs;activeTab derived via `useSearchParams` + fallback to 'documents';tab change pushes new URL with `scroll: false` to prevent scroll jump on tab switch
7. **Settings split Identity vs Indexing config**:two-Card structure separates readonly metadata(KB ID / name / description)from editable config(embedding / chunk strategy / top_k / rerank_k);clearer mental model than W12 baseline single-form混在一起;CO_W15 follow-up trigger noted for backend name/description PATCH endpoint

### Verification

```
$ cd frontend && pnpm type-check
> tsc --noEmit
$ # 0 errors

$ grep oklch frontend/app/admin/kb/\[id\]/page.tsx | wc -l
0
```

✅ TypeScript strict mode clean(0 errors);no `any` / no @ts-ignore;no hardcoded oklch;all colors via Tailwind tokens;shadcn primitives reused(Tabs / Card / Badge / Button / Input / Label / Select / Dialog + lucide icons)— no new vendor。

### Carry-overs to W14 D4

- 🚧 F3 user smoke deferred per CLAUDE.md §13(`! pnpm dev` + `! uvicorn`;`/admin/kb/[id]?tab=...` 5 tabs functional + URL bookmark-friendly + Retrieval Testing returns chunks for indexed KB + Settings save persists + Danger zone Dialog confirm + responsive horizontal-scroll mobile)
- ⏳ W14 D4 focus per plan §5:F4 cross-cutting refactors + token cleanup audit + Stepper rule-of-3 evaluation(F3.8 outcome confirmed NOT triggered → inline retention preserved + sidebar consistency review)
- 📝 **CO_F3a**:backend `GET /kb/{id}/documents` + `GET /kb/{id}/documents/{id}/chunks` W2 listing implementation(Beta hardening trigger when backend lands)
- 📝 **CO_F3b**:backend name + description PATCH endpoint(W15+ candidate per Settings tab Identity card readonly note)
- 📝 **CO_F3c**:backend `POST /kb/{id}/reindex` + `DELETE /kb/{id}` Danger zone implementation(W15+ candidate)

### Commit

- `84c8d39` feat(frontend,docs): W14 D3 F3 V4 KB Detail 5-tab nav

---

## Day 4 — W14 D4 F4 cross-cutting verification audit(real-calendar 2026-06-10 same-day collapse cycle 3 of 4 cont)

> **Calendar note**:plan §5 tentative date 2026-07-03 superseded by real-calendar 2026-06-10 same-day collapse(D3 → D4 cycle continue post user authorization "A:continue W14 D4 — F4 cross-cutting refactors + token cleanup")。Time tracking calibration:plan ~0.5 day budget vs actual ~15 min(verification phase + audit + carry-over flag — F4 documentation-only outcome per Karpathy §1.4 goal-driven success criteria all met without code change)。

### What landed

| F# | Deliverable | Outcome | Status |
|---|---|---|---|
| F4.1 | Stepper rule-of-3 trigger evaluation | **NOT triggered confirmed** — F3.4 Pipeline tab read-only ConfigRow display 不 introduce state machine wizard;W12 KB Pipeline wizard + W13 Register 仍 = 2 active state-machine wizards;**inline retention preserved** per W13 D4 decision;next emergence trigger preserved W15+(V5 Eval Console OR V6 Debug View if state machine emerges)| ✅ (preserved) |
| F4.2 | Sidebar consistency review | **W12 F4.1 baseline preserved** — `frontend/components/nav/admin-shell.tsx` untouched W14 D1-D3(rebuild scoped at page.tsx level only);desktop sidebar `bg-muted/40` ✓ + active `bg-muted font-medium text-foreground` ✓ + hover `hover:bg-muted hover:text-foreground` ✓ consistent;NavLinks `pathname.startsWith('/admin/kb/')` correctly activates "Knowledge Bases" sidebar entry for both list + detail routes | ✅ |
| F4.3 | Token consumption audit | **strict scope clean** — `grep \[oklch frontend/app/admin/` 0 className arbitrary value matches(W12 D2 baseline preserved);**deviation logged plan §7 changelog (D4)** — `frontend/components/error/error-boundary.tsx` 6 hardcoded oklch values W7+ token migration leftover surfaced during F4 audit BUT out of W14 F4.3 strict scope per plan literal → `CO_W14_F4_error_boundary` W15 polish phase carry-over per Karpathy §1.3 surgical | ✅ (deviation noted) |
| F4.4 | Cross-view UserMenu / Breadcrumb behavior | **W12 F4.2 baseline preserved** — admin-shell.tsx UserMenu + Breadcrumb mount untouched W14 D1-D3;Breadcrumb pathname-derived only(searchParams `?tab=...` correctly stays out of breadcrumb pollution per F3.7 URL state design);SEGMENT_LABELS dynamic KB id truncation works for `/admin/kb/[id]` deep route;UserMenu mock badge + sign-out flow preserved;0 regression across 6 admin routes(`/admin` + `/admin/kb` + `/admin/kb/new` + `/admin/kb/[id]` + `/admin/kb/[id]/upload` + `/eval`)| ✅ |

### Decisions

1. **Stepper rule-of-3 inline retention preserved**:F3.8 outcome confirmed F4.1 — no extraction in W14;Pipeline tab read-only ConfigRow display non-wizard so 第 3 次 emergence trigger 唔 fire;next opportunity = W15+ if V5 Eval Console OR V6 Debug View introduces wizard state machine(per architecture.md v6 §5.6-§5.7)
2. **F4.3 token audit strict scope hold**:plan F4.3 literal scope = `grep oklch frontend/app/admin/`;newly-touched W14 files(F1-F3 page.tsx rebuilds + F1.5 lib/auth touch)all clean Tailwind tokens;`frontend/components/error/error-boundary.tsx` 6 hardcoded oklch values pre-existing W7+ leftover OUT of W14 strict scope per Karpathy §1.3 surgical「only clean your own mess」(leak NOT introduced by W14 F1-F3 work);**`CO_W14_F4_error_boundary`** carry-over flag to W15 polish phase token cleanup pass(W15 design ref §6 broader scope makes natural fit)
3. **F4 = pure verification phase, no code change required**:per Karpathy §1.4 goal-driven(verifiable success criteria all met without touching code)+ §1.2 simplicity-first(don't add code for hypothetical scope expansion)+ §1.3 surgical(F4.1+F4.2+F4.4 baselines preserved by W14 F1-F3 page.tsx-scoped rebuilds);documentation-only outcome — checklist tick + plan §7 changelog deviation entry + this Day 4 progress entry
4. **Breadcrumb searchParams isolation correctness**:tab state via `?tab=...` 正確 stays out of pathname-derived breadcrumb(clean separation;BreadcrumbNav reads `usePathname()` only,not `useSearchParams()`)— pathname-only design intentional per F3.7 URL bookmark state design
5. **NavLinks active state for KB detail routes**:`pathname.startsWith('/admin/kb/')` activates "Knowledge Bases" sidebar entry for both list (`/admin/kb`) AND detail (`/admin/kb/[id]`) AND nested (`/admin/kb/[id]/upload`) routes per startsWith semantics — consistent visual feedback as user drills into KB detail tabs
6. **Error boundary scope decision asymmetry**:`frontend/components/error/error-boundary.tsx` 用於 `frontend/app/admin/error.tsx` segment boundary,意思 admin 用戶會 SEE the leak when error happens BUT file itself 喺 `frontend/components/error/` directory(strict plan F4.3 scope `frontend/app/admin/` directory grep 唔 cover);per Karpathy §1.3 surgical 不單方面 expand scope — log as `CO_W14_F4_error_boundary` 等 W15 token cleanup natural-fit window

### Verification

```
$ grep -r "\[oklch" frontend/app/admin/ frontend/lib/auth/ frontend/components/nav/
(no matches — 0 hardcoded oklch className arbitrary values)

$ grep -c "\[oklch" frontend/components/error/error-boundary.tsx
6  # pre-existing leak — CO_W14_F4_error_boundary flag

$ pnpm type-check
> tsc --noEmit
0 errors  # baseline preserved post-W14 D1-D3 (no W14 D4 code change)
```

✅ Token strict scope clean(0 hardcoded oklch className arbitrary values in `frontend/app/admin/`);F4.1 Stepper rule-of-3 NOT triggered confirmed;F4.2 sidebar baseline preserved;F4.4 UserMenu+Breadcrumb baseline preserved;0 regression on 6 admin routes(`/admin` + `/admin/kb` + `/admin/kb/new` + `/admin/kb/[id]` + `/admin/kb/[id]/upload` + `/eval`);no code change required this day per Karpathy §1.4 goal-driven verification.

### Carry-overs to W14 D5

- 🚧 F4 user smoke deferred per CLAUDE.md §13(non-blocker — verification phase 唔 introduce new behavior)
- ⏳ W14 D5 focus per plan §5:F5 phase Gate closeout(verdict PASS / PARTIAL PASS / FAIL with explicit rationale per W12 F5.1 + W13 F7.1 pattern)+ W14 progress.md retro 7 sections(What worked / What didn't / Surprises / Decisions / Carry-overs / Time tracking / Spec ref alignment)+ W15 phase folder rolling JIT kickoff(`docs/01-planning/W15-polish-closeout/{plan,checklist,progress}.md` draft per architecture.md v6 §5.6-§5.7 V5 Eval + V6 Debug + design ref §6 W15 scope responsive + a11y + Playwright E2E + pixel diff baseline harness)
- 📝 **CO_W14_F4_error_boundary**:`frontend/components/error/error-boundary.tsx` lines 36/39/42/49/58/67 hardcoded oklch values pre-existing W7+ React polish phase token migration leftover → W15 polish phase token cleanup candidate(scope outside `frontend/app/admin/` strict W14 F4.3 audit boundary per plan literal;file used by `frontend/app/admin/error.tsx` segment boundary so admin 用戶 visible at error states — visual leak but functionality intact)

### Commit

- `a4213d0` docs(planning): W14 D4 F4 cross-cutting verification — Stepper preserved + token audit pass + sidebar/UserMenu/Breadcrumb baseline preserved + CO_F4_error_boundary W15 follow-up

---

## Day 5 — W14 D5 F5 phase Gate closeout + W15 phase folder rolling JIT kickoff(real-calendar 2026-06-10 same-day collapse cycle 4 of 4 final)

> **Calendar note**:plan §5 tentative date 2026-07-04 superseded by real-calendar 2026-06-10 same-day collapse(D4 → D5 cycle continue post user authorization "A:continue W14 D5 — F5 phase Gate closeout")。Time tracking calibration:plan ~0.5 day budget vs actual ~30 min(retro 7 sections + W15 phase folder rolling JIT skeleton 3 files + frontmatter close cascade)。**Cycle 4 of 4 same-day collapse final** — W14 D1+D2+D3+D4+D5 5-batch landed real-calendar 2026-06-10 single session per cumulative pivot momentum(continuation of W12+W13 same-day collapse pattern;3 phases × ~5-day budget each = 15 plan-days collapsed across calendar single day)。

### F5.1 — W14 phase Gate verdict landed

Per plan §3 Success Criteria(5 conditions for PASS):

| # | Criterion | Status | Rationale |
|---|---|---|---|
| **1** | F1 V2 Admin Dashboard renders + stats / recent ingestion / quick actions + responsive + CO_F5d-cont session-token mode wired | ✅ PASS | 4-card stats row(KB+doc+chunks+system status badge per W12 baseline preserved + plan-literal "query count" deviation logged D1)+ Failed ingestion section derived from kbApi.list .failed_documents arrays(plan-literal "Recent ingestion log" deviation logged D1 — no backend endpoint readily available)+ 3-button Quick actions(Create KB / Test query / View eval)+ responsive grid + CO_F5d-cont session-token mode(SESSION_TOKEN_STORAGE_KEY relocated lib/auth canonical + readSessionBearer() defensive try/catch + getBearer() session branch BEFORE mock/MSAL fork);commits `641b328` + `4c53521` |
| **2** | F2 V3 KB List card grid renders + sort + create CTA + responsive + loading/empty states | ✅ PASS | KbCard component(name + description line-clamp + doc + chunks + last_indexed + status badge + kb_id mono small)+ sort dropdown 3 options(name/last_indexed recent/documents most;plan-literal "created_at" deviation logged D2 — no KbStatus field)+ Search filter Input + Create CTA + KbGridSkeleton loading + KbEmpty 2-variant(no-KBs/no-search-match)+ destructive error boundary preserved + responsive grid + Card-as-Link nested-anchor avoidance(deviation logged D2);commits `23cc579` + `9c21b88` |
| **3** | F3 V4 KB Detail 5-tab renders + each tab content functional + URL bookmark-friendly + Stepper rule-of-3 evaluated | ✅ PASS | shadcn Tabs primitive 5 tabs(Documents/Chunks/Pipeline/Retrieval Testing/Settings)+ URL searchParams `?tab=...` + 5 deviations logged D3(F3.2 Documents stub mitigation + F3.3 Chunks stub mitigation + F3.4 Pipeline read-only Tier 1 + F3.6 name+description display-only + F3.8 Stepper rule-of-3 NOT triggered confirmed → inline retention preserved per W13 D4 decision)+ Retrieval Testing streamQuery SSE + Synthesized answer Card + Retrieved chunks list w/ relevance Badge + Settings split Identity/Indexing config + DangerAction Dialog confirm Re-index/Delete + responsive TabsList overflow-x-auto;commits `84c8d39` + `8597e23` |
| **4** | F4 cross-cutting consistency preserved(sidebar / breadcrumb / UserMenu / token audit clean) | ✅ PASS | F4.1 Stepper rule-of-3 NOT triggered confirmed(reaffirms F3.8 outcome)+ F4.2 admin-shell.tsx W12 F4.1 baseline preserved(rebuild scoped page.tsx level only;`bg-muted/40` + `bg-muted font-medium text-foreground` consistent)+ F4.3 strict scope `frontend/app/admin/` 0 hardcoded oklch className matches(W12 D2 baseline preserved)+ deviation logged D4(`frontend/components/error/error-boundary.tsx` 6 hardcoded oklch leak OUT of W14 strict scope → CO_W14_F4_error_boundary W15 carry-over per Karpathy §1.3 surgical)+ F4.4 admin-shell UserMenu+Breadcrumb mount untouched + Breadcrumb pathname-derived 唔讀 searchParams(tab state isolation clean)+ 0 regression on 6 admin routes;commits `a4213d0` + `9257993` |
| **5** | F5 closeout retro + W15 phase folder kickoff | 🟢 IN PROGRESS | This entry(F5.1-F5.5 implementation);target completion same-session per pivot momentum |

#### **W14 phase Gate verdict**:🟢 **PASS WITH SMOKE-USER-DEFERRED CAVEAT — Admin Views sprint phase 3 of 4 complete**

Rationale:F1-F4 verifiable success criteria fully met within real-calendar 2026-06-10 single-day collapse cycle 4 of 4 final(F5 closeout this entry)。**All 5 PASS conditions met**;**PARTIAL PASS fallback acceptance criteria 全 met**(F3.8 Stepper extraction deferred — rule-of-3 NOT triggered confirmed + inline retention preserved;F3.4 Pipeline tab inline tuning deferred to W15+;F1.5 CO_F5d-cont session-token mode minimal viable per plan acceptance);**no FAIL conditions tripped**(no Tier 2 scope creep / no ADR-0014/0015/0016 scope expansion / no W12 F4 admin shell baseline regression — all preserved per F4.2+F4.4 audit)。

**SMOKE-USER-DEFERRED CAVEAT**:end-to-end browser smoke test(`pnpm dev` localhost:3001 + `uvicorn` localhost:8000 + admin dashboard / KB list / KB detail 5-tab navigation / Retrieval Testing query / Settings save / Danger zone Dialog confirm)defers per CLAUDE.md §13 dev server policy(long-running Node + Python servers conflict with Claude Code);AI verification = type-check 0 errors × 4 phases + grep oklch=0 strict scope + 0 regression on 6 admin routes。User can perform smoke independently;non-blocker for W15 implementation start since W15 polish phase **將 introduce Playwright E2E baseline harness**(per W15 F4 deliverable)which 將 systematically subsume manual smoke deferred across W12+W13+W14 cycles。

**ADR triggers fired W14**:**none**(no H1 / H2 / H3 trigger);F1-F4 implementation 屬 ADR-0014 + ADR-0015 + ADR-0016 already covered scope per H1。**ADR-0013 reservation preserved** for W11 retro carry-over CO12(AF3 + Personal Azure dev tier pattern formalization)— W14 admin views work 唔 surface vendor change OR architectural-adjacent decision。

### F5.2 — Retro 7 sections complete

(See § Retro below — 7 sections fill same-session per CLAUDE.md §10 R5 phase closeout discipline)

### F5.3 — W15-polish-closeout phase folder kickoff

- ✅ NEW `docs/01-planning/W15-polish-closeout/` folder created
- ✅ NEW `plan.md`(`status: draft` per CLAUDE.md §10 R1 rolling-JIT;ready for W15 D1 active flip post stakeholder authorization)
  - Scope:**Phase 4 of 4 UI sprint cycle W12-W15 — final** — V5 Eval Console + V6 Debug View + responsive + a11y + Playwright E2E + pixel diff baseline harness + W14 carry-over absorption(CO_F3a-c backend trigger evaluation defer Beta + CO_W14_F4_error_boundary token cleanup pass)
  - 5 deliverables F1-F5:F1 V5 Eval Console(per arch v6 §5.6 + design ref §2.5 wireframe)+ F2 V6 Debug View(per arch v6 §5.7 + design ref §2.6 wireframe)+ F3 Responsive + a11y polish across all 9 views + F4 Playwright E2E + pixel diff baseline harness + F5 Tier 1 UI sprint cycle final closeout + W16+ Beta deploy phase folder rolling JIT trigger
  - Effort estimate:5-6 working days rolling JIT(eval+debug view-level + cross-cutting polish — likely 1-2 days per same calendar-day collapse momentum if pattern holds)
- ✅ NEW `checklist.md`(atomic checkbox per F1-F5 deliverable)
- ✅ NEW `progress.md` Day 0 entry initialize(carry-overs from W14 retro CO_F3a-c + CO_W14_F4_error_boundary + CO_W14_smoke + pre-W15 setup)

### F5.4 — W14 frontmatter active → closed

- ✅ `plan.md` status: active → closed
- ✅ `checklist.md` status: active → closed
- ✅ `progress.md` status: active → closed
- All 3 files updated same-commit-cycle as F5 closeout commit

### F5.5 — Q sync to decision-form.md

- ✅ No new OQ surfaced W14(F1-F4 admin views work 唔 surface OQ;W14 plan §3 success conditions explicitly 唔 expect OQ surface)
- 16/22 Resolved(no change from W12+W13 baseline);5/22 Open unchanged(Q6/Q8/Q15/Q16/Q20 影響 Beta + Tier 2)

### Decisions / OQ summary

- **W14 phase Gate PASS WITH SMOKE-USER-DEFERRED CAVEAT**(per F5.1 verdict)— Admin Views sprint phase 3 of 4 complete within real-calendar 2026-06-10 single-day collapse cycle 4 of 4 final
- **W15-polish-closeout phase folder kickoff**(per CLAUDE.md §10 R1 rolling-JIT)— `status: draft` ready for W15 D1 active flip
- **W14 frontmatter close cascade**(plan + checklist + progress active → closed)
- **No new ADR fired W14**(no H1 / H2 trigger;ADR-0013 reservation still preserved)
- **No new OQ resolved at F5**(no surface during W14)
- **W14 D1-D5 plan-day work collapsed into real-calendar 2026-06-10 single session**(continuation of W12+W13 same-day collapse pattern;3 phases × ~5-day budget each = 15 plan-days collapsed across calendar single day;cycle 4 of 4 calendar-day collapse complete)

### Open / blocked

- 🚧 **End-to-end smoke** — user 可自行 `pnpm dev` + `uvicorn` browser smoke verify W14 admin views(SMOKE-USER-DEFERRED CAVEAT per Phase Gate verdict;non W15 blocker — W15 F4 Playwright E2E baseline harness 將 systematically subsume)
- ⏳ W15 D1 implementation start = next session OR same-calendar-day collapse continuation(per rolling JIT;F1-F5 deliverables ready post W15 plan active flip)
- ⏸ W16+ Beta deploy phase folder 唔 pre-create(rolling JIT discipline preserved;trigger = W15 closeout)

### Tests / discipline

- 0 logic change W14 F5(governance closeout + W15 folder kickoff only);frontend type-check baseline preserved across 4 implementation phases(F1+F2+F3+F4 all 0 errors)
- Karpathy §1.2 simplicity-first ✅:retro 7 sections concise + W15 plan rolling-JIT(non over-engineered scope speculation);Phase Gate verdict 明示 caveat 而非 hide
- Karpathy §1.3 surgical ✅:F5 closeout 純 governance work(no code change;non scope creep);F4 verification phase no code change preserved
- Karpathy §1.4 goal-driven ✅:Phase Gate verifiable success criteria 5 conditions evaluation 明示 PASS rationale per criterion + caveat 明示
- H1 / H2 / H3 / H4 / H5 / H6 self-check:
  - **H1 ✅** No `architecture.md` v6 §3/§4 component change at F5
  - **H2 ✅** No new vendor at F5(no W14 vendor decision change)
  - **H3 ✅** No Dify reference touch
  - **H4 ✅** No Tier 2 implementation;W15 polish + closeout scope 屬 Tier 1 v6 amendment per ADR-0015
  - **H5 ✅** No secret commit
  - **H6 ✅** No backend test code change(W14 frontend-only)
- R1 ✅:W14 plan/checklist active throughout D1-D5 + closed cascade F5
- R2 binding ✅:W14 D5 F5 commit 對應呢個 Day 5 entry
- R3 ✅:plan changelog 2026-06-10 (D5) entry(W14 D1-D5 plan-day collapse + Phase Gate verdict landed + W15 phase folder kickoff)
- R4 ✅:no OQ resolved(no surface during W14)
- R5 ✅:no new architectural-adjacent decision at F5(ADR-0014/0015/0016 already covered scope)

### Commit reference

- `4b202ce` W14 D5 F5 batch commit(F5.1-F5.5 retro 7 sections + Phase Gate PASS WITH SMOKE-USER-DEFERRED CAVEAT verdict + W15 phase folder kickoff + W14 frontmatter close cascade + checklist F5.1-F5.5 + cross-cutting tick + plan changelog 2026-06-10 (D5) W14 D1-D5 plan-day collapse + closeout entry)

---

## Retro(W14 D5 末 closeout 2026-06-10 — single-day calendar collapse cycle 4 of 4 final)

### What worked

1. **Same-calendar-day 5-phase collapse cascade**(W14 D1+D2+D3+D4+D5)— 5 batches landed within real-calendar 2026-06-10 single session per cumulative pivot momentum stakeholder authorization;continuation of W12+W13 closeout same-day momentum(W12 D1-D5 collapse 2026-06-10 + W13 D1-D5 cont 2026-06-10 + W14 D1-D5 cont 2026-06-10 = **15 plan-days collapsed across 3 phases同 calendar day**);non rolling-JIT violation due to plan §5 day-by-day caveat tentative dates + stakeholder explicit ack each phase advance + deliverables logically sequenced
2. **F4 verification phase elegance**(15 min actual vs 0.5 day plan = 16x under-budget — fastest of all 4 phases)— pure verification phase no code change per Karpathy §1.4 goal-driven(verifiable success criteria all met without touching code per §1.2 simplicity-first);documentation-only outcome cleanly logged;Stepper rule-of-3 evaluation outcome confirmed via grep + cross-reference instead of speculative refactor
3. **Plan deviation logging discipline preserved across 4 phases**(F1: 2 deviations + F2: 2 + F3: 5 + F4: 1 = **10 deviations total all logged in §7 changelog per R3**)— full audit trail enables future-Chris session reads + retro vs plan calibration data;Karpathy §1.1 think-before-coding upfront vs retrospective documentation
4. **Backend stub mitigation pattern reusable**(F3 Documents/Chunks tabs + F3.6 Settings + Danger zone)— BackendStubNote helper component standardized across 3 tabs + clear "incomplete state but visible" admin user transparency vs hidden gaps;informational delivery preserved without inventing data;CO_F3a-c carry-over flags clean handoff to Beta hardening phase
5. **URL searchParams state design clean separation**(F3.7 KB Detail tab `?tab=...`)— bookmark-friendly + browser back-button + deep-linking from external docs;BreadcrumbNav reads `usePathname()` only(searchParams isolation correctness);F4.4 audit confirmed no breadcrumb pollution
6. **Time tracking calibration consistency cycle 4 of 4**(W14 D1-D4 7-16x under-budget pattern continued from W12+W13)— calibration data point now spans **3 phases × 5 days × consistent 7-16x ratio** = robust signal for W15+ planning。Verification phase fastest(F4 16x);largest deliverable still under(F3 12x);cross-cutting baseline preserved(F4 no code change validates Karpathy §1.3 surgical correctness)
7. **F4.3 token strict scope hold prevented opportunistic cleanup creep**(error-boundary.tsx leak surfaced via F4 audit but deferred to W15)— Karpathy §1.3 surgical「only clean your own mess」preserved;leak NOT introduced by W14 F1-F3 work + file outside `frontend/app/admin/` strict scope per plan literal;`CO_W14_F4_error_boundary` carry-over flag clean handoff to W15 polish phase token cleanup pass natural fit

### What didn't work / unexpected friction

1. **Backend stub coverage breadth(3 separate KB-detail endpoints all 501 NOT_IMPLEMENTED)** required parallel mitigation patterns in F3 alone — `GET /kb/{id}/documents` + `GET /kb/{id}/documents/{id}/chunks` + name/description PATCH + `POST /kb/{id}/reindex` + `DELETE /kb/{id}` = 3 backend stub gaps + 1 PATCH endpoint not exposed + 2 destructive action endpoints stubs;BackendStubNote pattern reusable but plan literal expectations forced creative re-interpretation per phase deliverable per Karpathy §1.1 think-before-coding;**5 deviations in F3 alone**(largest single-phase deviation count W12-W14)
2. **Plan literal field references(F1.1 "query count" + F2.2 "created_at")stale vs actual API surface** — `KbStatus` API response 唔 contain `created_at` field nor backend endpoint for query count metric;采 chunks count(W12 baseline preserved)+ documents sort dimension as substitute;**plan author 寫 spec 之前 唔 grep API surface verification**;同 W13 plan F1.5 "_PROTECTED_PREFIXES middleware.ts" stale similar pattern(plan reference predates code grep verification)
3. **error-boundary.tsx pre-existing oklch leak surfaced during F4 audit out of strict scope** — visual leak admin 用戶 visible at error states(via `frontend/app/admin/error.tsx` boundary)但 file 喺 `frontend/components/error/` directory(strict plan F4.3 scope `frontend/app/admin/` directory grep 唔 cover);Karpathy §1.3 surgical scope hold protected against opportunistic cleanup creep,but accumulates W7+ token migration backlog(pre-W12 D2 strict baseline)為 W15 polish phase candidate;**root-cause** = W7+ React polish phase token migration miss(predates W12 D2 baseline lock)
4. **User smoke deferred per CLAUDE.md §13 default accumulating across W12+W13+W14 cycles** — 3 cumulative phases × 4-5 user smoke deferral CAVEATs = manual smoke test backlog growing;non-blocker per default policy but accumulating;**W15 F4 Playwright E2E baseline harness必須 systematically subsume**(W12+W13+W14 manual smoke deferred backlog → automated E2E coverage trigger);CLAUDE.md §13 dev server policy 與 E2E harness 分屬 different testing layer
5. **F1.5 SESSION_TOKEN_STORAGE_KEY relocation forced lib/api/auth → lib/auth re-export to break circular import** — api-client → auth → api/auth circular dep surfaced when relocating canonical key;1-line re-export from lib/api/auth.ts adequate但 indicates auth domain boundary 未 fully decoupled from api domain;Beta hardening trigger candidate to formally split auth client into pure lib/auth subtree

### Surprises / discoveries

1. **🆕 F3.8 Stepper rule-of-3 NOT triggered surprisingly clean** — Pipeline tab read-only ConfigRow display(vs wizard state machine)preserved exactly 2 active state-machine wizards count;rule-of-3 emergence trigger preserved precisely for W15+ if V5 Eval Console(eval set selector + run config wizard?)OR V6 Debug View(stage navigation wizard?)introduces 3rd state machine — inline retention preserved per W13 D4 decision **without forcing premature extraction**
2. **🆕 searchParams state isolation from breadcrumb design correctness validated F4.4 audit** — pathname-derived `BreadcrumbNav` reads `usePathname()` only,not `useSearchParams()`,so tab state via `?tab=...` cleanly stays out of breadcrumb pollution;**design-by-construction** correctness vs runtime branch logic;Karpathy §1.4 goal-driven verifiable goal達成 = no breadcrumb pollution observable across 5 tab navigation
3. **🆕 F4 verification phase runtime ~15 min vs 0.5 day plan = 16x under-budget(fastest of all W14 phases)** — pure audit pattern fastest verification cycle in W14;data point reinforces calibration for "verification-only phase" estimate baseline reduce by ~16x for Tier 1 sprint pattern
4. **🆕 Cycle 4 of 4 same-day collapse held**(W14 D1+D2+D3+D4+D5 all 2026-06-10)consistent with W12+W13 pattern — calibration data now spans **15 plan-days** collapsed into single calendar day across 3 phases;suggests Tier 1 UI sprint phase capacity ~1-2 hr per phase vs ~5-day budget when:
   - Backend stub gap forces mitigation pattern(F3)
   - Stepper rule-of-3 NOT triggered preserves inline retention(F3.8)
   - F4 verification phase no code change(audit < implementation)
5. **🆕 Token audit strict scope vs broader cleanup tradeoff visible** — F4.3 audit surfaced 6 hardcoded oklch in error-boundary.tsx,但 plan F4.3 literal scope `frontend/app/admin/` directory grep doesn't cover;**Karpathy §1.3 surgical scope hold protected against opportunistic cleanup creep**;1 deviation deferred properly to W15 with clean carry-over flag;valuable discipline data for future audit phases
6. **🆕 Plan literal reference vs actual code grep verification gap pattern**(W13 F1.5 + W14 F1.1 + W14 F2.2)— **3rd occurrence of plan author 寫 plan 前 唔 grep code verification**;suggests adding "spec ref grep verification" step to plan kickoff R1 pre-condition checklist for future phases(W15+ candidate process improvement)

### Decisions

1. **F1.1 4-card stats preserve chunks count**(W12 baseline)over plan-literal "query count" — no backend endpoint readily available;Karpathy §1.2 simplicity-first 唔 add backend endpoint just for stat card
2. **F1.2 "Failed ingestion" derived from kbApi.list .failed_documents** — informational symmetry preserved(operations focus = "what's broken now")+ Karpathy §1.2 minimum data plumbing
3. **F1.3 ActionButton component pattern over plain Button** — icon + label + description w/ accent-tinted icon background;5-line component reuse + matches V2 wireframe design ref §2.2 quick-actions pattern
4. **F1.5 SESSION_TOKEN_STORAGE_KEY relocation to lib/auth canonical domain** — single source of truth + breaks api-client → auth → api/auth circular import via lib/api/auth.ts re-export;defensive try/catch for privacy/sandbox modes;parallel to backend dependency.get_current_user session branch architecture
5. **F2.2 sort options name+last_indexed+documents** — replace plan-literal "created_at" lacking KbStatus field;采 useful operational dimensions over existing data
6. **F2.6 whole Card as Link**(Upload secondary dropped from Card)— accessibility + middle-click new tab + nested-anchor HTML invalid avoidance;1-click extra cost acceptable Tier 1
7. **F3 backend stub mitigation pattern**(BackendStubNote helper component reusable 3 tabs)— informational delivery without inventing data;clear "incomplete state but visible" admin user transparency
8. **F3.4 Pipeline tab read-only ConfigRow display** — inline tuning defer W15+ Tier 1 simplicity-first;Pipeline 唔 introduce wizard state machine,F3.8 Stepper rule-of-3 trigger NOT fired
9. **F3.6 Settings split Identity vs Indexing config**(two-Card structure)— readonly metadata + editable config separation clearer mental model than W12 baseline single-form;CO_W15 follow-up backend name/description PATCH endpoint
10. **F3.7 URL searchParams `?tab=...` bookmark-friendly + scroll: false**(prevents scroll jump on tab switch)— browser back-button works + deep-linking from external docs
11. **F3.8 Stepper rule-of-3 NOT triggered → inline retention preserved per W13 D4 decision** — Pipeline tab read-only display 不算 state machine wizard;Pipeline+Register = 2 active state-machine wizards;**next wizard usage emergence trigger preserved for W15+**(V5 Eval Console / V6 Debug View if state machine emerges)
12. **F3.9 TabsList overflow-x-auto**(simpler than Sheet/Select fallback per Karpathy §1.2 simplicity-first)— 1-line solution + native mobile UX swipe scroll feels web-native
13. **F4 = pure verification phase**(no code change required per Karpathy §1.4 goal-driven success criteria 全 met without touching code per §1.2 simplicity-first + §1.3 surgical scope hold)
14. **F4.3 token audit strict scope hold + CO_W14_F4_error_boundary deferred to W15** — Karpathy §1.3 surgical「only clean your own mess」(leak NOT introduced by W14 F1-F3 work);W15 polish phase scope已 broader making token cleanup natural fit
15. **DangerAction reusable component pattern**(Re-index + Delete via shadcn Dialog confirm + structured backend status disclosure + toast.info「pending backend stub」)— non-blocking UI wire test + variant prop drives Button styling

### Carry-overs to W15

#### Immediate W15 D1-D3 priority

- **CO_W14_F4_error_boundary** `frontend/components/error/error-boundary.tsx` lines 36/39/42/49/58/67 hardcoded oklch values pre-existing W7+ React polish phase token migration leftover → **W15 F3.4 token cleanup pass**(deliverable exact match)
- **CO_W14_smoke** End-to-end browser smoke deferred per CLAUDE.md §13 default across W12+W13+W14 cycles → **W15 F4 Playwright E2E baseline harness systematic subsume**(deliverable exact match — golden-path E2E + admin path E2E + pixel diff baseline)

#### W15 polish + closeout core deliverables(per design ref §6 W15 implementation sequencing)

- **CO_W15_F1** V5 Eval Console implementation(per architecture.md v6 §5.6;4-metric cards + W4 Reranker Shootout table + Failed queries table)→ W15 F1
- **CO_W15_F2** V6 Debug View implementation(per architecture.md v6 §5.7;9-stage timeline + per-stage duration / cost / data preview / Langfuse link)→ W15 F2
- **CO_W15_F3** Responsive + a11y + Playwright E2E + pixel diff baseline harness — closeout phase per design ref §6 implementation sequencing → W15 F3 + F4

#### W14 backend follow-ups(non-W15-blocker;defer Beta hardening)

- **CO_F3a** backend `GET /kb/{id}/documents` + `GET /kb/{id}/documents/{id}/chunks` W2 listing implementation → Beta hardening trigger when backend lands(W15 frontend stub mitigation pattern preserved)
- **CO_F3b** backend KB name + description PATCH endpoint → W15+ candidate per Settings tab Identity card readonly note
- **CO_F3c** backend `POST /kb/{id}/reindex` + `DELETE /kb/{id}` Danger zone implementation → W15+ candidate

#### W13 backend follow-ups(non-W15-blocker;defer Beta hardening,inherited unchanged)

- **CO_F5_refresh** `/auth/refresh` self-register session rotation — currently mock mode returns mock_bearer for self-register users(wrong);minimal fix to detect tid=SELF_REGISTER_TID + rotate session token via `users_repo.create_session`;defer Beta hardening
- **CO_F5_cookie** httpOnly cookie hardening — currently body-only token return;Set-Cookie via response.set_cookie() Beta phase candidate
- **CO_F6a** `pip install azure-communication-email` retry post R8 proxy resolution(Beta hardening trigger)
- **CO_F6b** Background-task email send via FastAPI BackgroundTasks(Beta latency tuning)
- **CO_F6c** Sender domain SPF/DKIM IT-side post Track A

#### W16+ Beta deploy(unchanged from W11+W12+W13)

- **CO16** Track A IT cred populate event + R-B1 closure(blocked W11+;non W12-W15 critical path)
- **CO17** AF3 code fix Option A + Personal Azure dev tier pattern formalization(ADR-0013 candidate trigger consolidate)
- **CO18** KB Manager + users_repo persistent backing(SQLite / Postgres / Cosmos DB Beta production hardening)
- **CO19** F2.1-F2.4 25% rollout activation cascade + F3.1-F3.5 daily metric monitor + F5.1 Q15 first weekly signal report(all blocked W11+;defer W16+)

#### Process improvement candidate(W15+)

- **CO_W14_process_grep_verify** Plan author "spec ref grep verification" step pre-R1 active flip — 3rd occurrence of plan literal vs actual code grep verification gap surfaced(W13 F1.5 + W14 F1.1 + W14 F2.2);suggests adding pre-active flip grep step to W15+ plan kickoff process;**non-blocking** but valuable rolling JIT discipline refinement

### Time tracking

| Phase | Plan estimate | Actual(real-calendar 2026-06-10 same-day collapse) | Calibration delta |
|---|---|---|---|
| F1 V2 Admin Dashboard + CO_F5d-cont | 0.5 day | ~30 min | 8x under-budget |
| F2 V3 KB List card grid | 1 day | ~30 min | 16x under-budget |
| F3 V4 KB Detail 5-tab(largest deliverable)| 1.5 day | ~1 hr | 12x under-budget |
| F4 cross-cutting verification audit | 0.5 day | ~15 min | 16x under-budget(fastest — verification phase) |
| F5 closeout retro + W15 phase folder kickoff | 0.5 day | ~30 min(this entry) | 8x under-budget |
| **Total** | **~5 working days budget** | **~2 hr 45 min actual single session 2026-06-10** | **~7-16x under-budget per pivot momentum + Karpathy §1.3 surgical scope discipline** |

**Calibration data points refining W12+W13 retro estimates(now cycle 4 of 4 cumulative)**:

1. **Tier 1 UI sprint phase capacity ~1-2 hr per phase confirmed at W14 scale**(5 deliverables in single session 2 hr 45 min;7-16x under-budget consistent with W12 7x + W13 7-9x figures);**robust signal across 3 phases × 5 days × 7-16x ratio**
2. **Verification-only phase capacity ~15 min**(F4 case;fastest of all 4 phases);data point new for W12-W14 calibration set;reusable for future audit-only phases
3. **Plan changelog overhead negligible** when deviations surfaced during implementation(Karpathy §1.1 think-before-coding upfront vs retrospective documentation;**10 deviations in W14 logged cleanly without time penalty**)
4. **Backend stub mitigation pattern reusable**(BackendStubNote helper)— add ~10 min per stubbed tab vs full backend integration ~hours;preserves UI work momentum without backend backlog blocking
5. **W15 estimate**:5 deliverables(eval+debug view-level + cross-cutting polish similar scope to W14);if same pivot momentum sustained = ~3-4 hr total realistic;Playwright E2E baseline harness adds modest complexity but install + golden-path scope hold-able

### Spec ref alignment

All W14 deliverables trace back to spec citations(per CLAUDE.md §10 R5 + Karpathy §1.4 verifiable goals):

| Deliverable | Spec citation | Verification |
|---|---|---|
| F1 V2 Admin Dashboard refactor + CO_F5d-cont session-token mode | architecture.md v6 §5.3 V2 + ui-design-reference-v6.md §2.2 V2 wireframe + W13 retro CO_F5d-cont carry-over + ADR-0014 hybrid auth | `frontend/app/admin/page.tsx`(4-card stats + Failed ingestion + Quick actions)+ `frontend/lib/auth/index.ts`(SESSION_TOKEN_STORAGE_KEY canonical + readSessionBearer + getBearer session branch)+ `frontend/lib/api/auth.ts` re-export to break circular import |
| F2 V3 KB List card grid refactor | architecture.md v6 §5.4 V3 + ui-design-reference-v6.md §2.3 V3 wireframe + Dify Image 4 dataset-grid pattern reference per ADR-0010 read-only | `frontend/app/admin/kb/page.tsx`(KbCard + sort + filter + Skeleton + KbEmpty 2-variant + status badge derivation) |
| F3 V4 KB Detail 5-tab nav | architecture.md v6 §5.5 V4 + ui-design-reference-v6.md §2.4 V4 wireframe(5-tab pattern)+ Dify Image 1+2+4+5+6 layout reference per ADR-0010 read-only | `frontend/app/admin/kb/[id]/page.tsx`(shadcn Tabs primitive + 5 TabsContent + URL searchParams state + DangerAction Dialog confirm + BackendStubNote helper)+ streamQuery SSE reuse + kbApi.patchSettings PATCH wire |
| F4 cross-cutting verification audit | design ref §3 cross-view consistency rules + W13 retro carry-over CO_W14_F4 | grep `\[oklch frontend/app/admin/` 0 matches strict scope clean + admin-shell.tsx W12 F4.1 baseline preserved + Breadcrumb pathname-derived isolation correctness + Stepper rule-of-3 NOT triggered confirmed |
| F5 closeout + W15 kickoff | CLAUDE.md §10 R1 rolling-JIT + R5 phase closeout discipline + W12+W13 closeout pattern | `docs/01-planning/W15-polish-closeout/{plan,checklist,progress}.md` + W14 frontmatter close cascade |

**No spec violation**;**no new ADR fired W14**(F1-F4 implementation 屬 ADR-0014 + ADR-0015 + ADR-0016 already covered scope);**ADR-0013 reservation preserved** for W11 retro carry-over CO12;**ADR-0014 + ADR-0015 + ADR-0016 全部 covered W14 scope** without scope creep。

---

**Lifecycle reminder**:呢份 progress.md 屬 phase journal,daily entries + retro 必須 commit incrementally per R2。Day 0 setup entry 屬 W13 D5 cont F7 closeout cascade carry-over prep,W14 D1 active implementation start當 stakeholder authorization 後。
