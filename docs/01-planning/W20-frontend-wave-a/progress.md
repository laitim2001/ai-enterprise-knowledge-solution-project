---
phase: W20-frontend-wave-a
plan_ref: ./plan.md
checklist_ref: ./checklist.md
status: active
last_updated: 2026-05-16
---

# Phase W20 — Progress

> Daily progress + decisions + commits;結尾 retro。Status:`active` from kickoff 2026-05-16(per Chris directive + 6 ADRs Accepted + AskUserQuestion A1 pick — same pattern as W17 D0 + W18 D0)。

---

## Day 0 — 2026-05-16(Kickoff)

### F0 — Kickoff cascade(landed)

**Branch**:`main` post-W19 closeout(`6a34a41` → `origin/main`)。Working tree clean at start;single kickoff commit will land:
- `docs/adr/0025-kb-detail-8-tabs.md` Status Proposed → Accepted + Wave A 7-tab scope note
- `docs/adr/0028-kb-new-5-step-wizard.md` Status Proposed → Accepted
- `docs/adr/0031-chat-advanced-surfaces.md` Status Proposed → Accepted + Option B Wave A +3 backend days note
- `docs/adr/README.md` — 3 ADR rows Status flip(Proposed→Accepted)+ Next NNNN unchanged(0033)+ Update history row
- `docs/architecture.md` — inline-tagged §5.x amendments(§5.2 Chat / §5.3 Dashboard / §5.4-§5.5 KB List+Detail / §5.5.5 NEW /kb/new wizard / §5.10-§5.11 Login+Register)— doc version held per W18 ADR-0024 / §3.4 / §3.7 precedent
- `docs/01-planning/W20-frontend-wave-a/{plan,checklist,progress}.md` — created `status: active`
- `docs/12-ai-assistant/01-prompts/01-session-start.md` — §10 W20 row added(`active`)+ §12 milestones row(`active`)+ Update history + Last-Updated

### Decisions captured at kickoff

| Decision | Rationale | Authority |
|---|---|---|
| Wave A ships **7-tab `-Access`**(not 8-tab) | F4 §3.6 recommend — Wave A backend already +3 days from ADR-0031 Option B;Access tab needs ADR-0027 Option A RBAC infra(~20 backend days)which is Wave C1 scope;7-tab Wave A + Access tab Wave C1 is the realistic split | Chris AskUserQuestion 2026-05-16 A1 pick |
| **Mock-auth default through Wave C** | User 岔口 2 W19 — real-MSAL feature-flagged concurrent ship Wave C;Wave A doesn't touch real-MSAL path | Chris W19 F0 kickoff AskUserQuestion |
| ADR-0031 Option B **server-side** Conversation History | Promotes C10 §7 Tier 2 → Tier 1;Postgres `conversations` + `messages` tables per ADR-0023 backing pattern + in-memory fallback;+3 backend days extends Wave A backend from ~5-7d to ~8-10d | Chris W19 F6 AskUserQuestion(rejected Option A localStorage Tier 1 + Option C Tier 2 defer)|
| ADR-0030 + ADR-0032 **SKIPPED**(absorbed) | Dashboard polish + Trace 3 viz + /traces list + Topbar/Sidebar additive scope = small enough to absorb into Wave A F1+F2 (Dashboard/Topbar parts) + Wave B (Trace/Traces parts) without separate ADR record | W19 F6 closeout decision |
| Wave C **MUST split into C1+C2** per F4 §3.6 trigger | Chris Option A+B picks (ADR-0027 full RBAC ~20 backend days + ADR-0026 Settings fully editable ~22 NEW endpoints) combined ~42 backend days exceeds single Wave C phase budget;C1 + C2 scope concrete split decision at W22 kickoff | W19 F6 closeout |
| **2 NEW dependencies** Plan B sequencing at Wave C kickoff | Key Vault SDK + Entra Graph SDK — triggered by ADR-0026 Option B + ADR-0027 Option A picks;H2 stop-and-ask implicit via Chris pick;R8 corp-proxy mitigation per ADR-0017 applies to both — Plan B sequencing decision deferred to Wave C kickoff per ADR-0017 Decision-rule #5 | W19 F6 |

### Tier 2 boundary enforcement(Wave A)

Per W19 F5 27-affordance Tier 2 catalog + `<DisabledAffordance>` shared component spec:

| Tier 2 leak surface | Wave A treatment |
|---|---|
| Workspace switcher(multi-tenancy)| `<DisabledAffordance tier={2}>` chip in topbar — F1.2 |
| Access tab(KB Detail RBAC)| `<TabsTrigger disabled>` + `<DisabledAffordance tier={1.5}>` — F5.8;Wave C1 activates |
| Multimodal caption gen / image clustering / blockchain | `<DisabledAffordance tier={2}>` rows in `/kb/new` Step 4 + `/kb-upload/[id]` Source step — F4.4 + F6.1 |
| Labs section in sidebar | Hidden by default(F1.4)— prototype-only `/labs/*` routes don't ship per W19 F5.4 Option C |
| Forgot password on `/login` | `<DisabledAffordance tier={2}>` chip — F7.1 |
| Chunking Lab "Apply" button | `<DisabledAffordance tier={2}>` "re-chunking pending" — F5.6;Tier 1 = preview-only |

### Actual vs Planned Effort(Day 0)

| F | Planned | Actual | Δ |
|---|---|---|---|
| F0.1 ADR-0025 Status flip | 5 min | TBD | TBD |
| F0.2 ADR-0028 Status flip | 5 min | TBD | TBD |
| F0.3 ADR-0031 Status flip | 5 min | TBD | TBD |
| F0.4 ADR README sync | 5 min | TBD | TBD |
| F0.5 architecture.md §5.x inline amendments | 30 min | TBD | TBD |
| F0.6 plan/checklist/progress create | 60 min | ~45 min | -25% |
| F0.7 session-start.md §10+§12 sync | 15 min | TBD | TBD |
| **Day 0 total** | **~2 hours** | TBD | TBD |

### Notes / open items at Day 0

- W19 F4 §1.2 backend gap items 3 + 4(Q6 recent queries + Eval-cache decisions)defer = empty-state CTA per W18 F4 acceptance — preserved as Wave A scope-minimum path(can flip to data-wired if user enables at any Day-N — see F2.2(c)/(d))
- ADR-0031 Option B Postgres tables + endpoints decision = reuse W17 F1 / ADR-0023 backing pattern(`make_conversation_store()` factory + in-memory fallback when `DATABASE_URL` unset)— same shape as `make_kb_backend` + `make_users_store`,no new architectural pattern
- W18 milestone `[oklch(`=0 across `frontend/` MUST be preserved through Wave A — F1.6 + F2.5 + F3.14 + F4.6 + F5.9 + F6.3 + F7.3 + F8.3 all gate on it
- F8.4 Vitest target 20+/20+ tests = additive on top of W18 F8.4 baseline(4 files / 13 tests) — no regression on existing tests
- F8.5 Playwright run via `PW_CHANNEL=chrome pnpm test:e2e`(system Chrome — ADR-0017 Plan B (a) realised 2026-05-13)— no longer R8-blocked for the *run*;the `npx playwright install chromium` block remains for fresh bundled Chromium, but unchanged

---

## Day 1 — 2026-05-16

### F1 — `<AppShell>` topbar + sidebar polish per ADR-0032 absorbed scope(landed)

**Branch**:`main`(post-W20 kickoff `40964b6`,now ahead of `origin/main` 1 commit)。
**Commits this day**:`(this commit)` — single F1 commit covering F1.1+F1.2+F1.3+F1.4+F1.5。

#### What landed

- **F1.5** NEW `frontend/components/ui/disabled-affordance.tsx`(shared `<DisabledAffordance>` per W19 F5 §4 spec)— props `variant` ∈ {`p1-strict` default,`p3-preview`} + `reason` + `tier2Trigger?` + `showBadge?`(p3 only)+ `className?`;`aria-disabled="true"` + `title` + `aria-label`;p1-strict 用 `opacity-60 pointer-events-none`,p3-preview 用 `opacity-75` + 可選 inline `TIER 2` badge(`bg-accent/10 text-accent border-accent/30`)。Catalog §4 用 `bg-accent/12` → rounded 至 `bg-accent/10`(Tailwind default opacity step;視覺差異忽略;避免 one-off tailwind.config 擴展)。
- **F1.1** NEW `frontend/components/nav/notifications-menu.tsx`(per ADR-0032 absorb)— `<DropdownMenu>` triggered by `<Bell>` + counter badge(absolute-positioned,`bg-destructive` semantic token);`useQuery(['notifications'])` off `GET /notifications` with `retry: false`(W19 F2 item 21 endpoint optional)+ refetchInterval 60s;404 → static `MOCK_NOTIFICATIONS` fallback(3 deterministic items);Mark all read button(disabled if no unread or backend absent → wrapped in `<DisabledAffordance>`);See all → `<DisabledAffordance>`(no `/notifications` route in Wave A scope);per-item relative time formatter(just now / Nm / Nh / Nd ago);unread-dot indicator + locally-marked-read state(`useState<Set<string>>`)。
- **F1.2** AppShell topbar — **Workspace switcher disabled chip**(`<DisabledAffordance reason="Multi-workspace support — Tier 2 per architecture.md §11" tier2Trigger="multi-tenancy">` 包住 disabled `<button>` 顯示 `Briefcase` icon + `Ricoh · RAPO` label + `ChevronDown` icon;`hidden sm:inline-flex`)— fixes W19 F1 §2.3 leak。**Language toggle migrated** from inline `disabled`+`title` to `<DisabledAffordance reason="Multi-language (JP / ZH) — coming in a later tier" tier2Trigger="i18n machinery">`(W19 S1 catalog item consume shared component instead of ad-hoc disabled+title)。
- **F1.3** AppShell sidebar — `NAV_ITEMS` 重組為 `NAV_SECTIONS`(`{ title, items }[]`)— Main(Dashboard / Chat / Knowledge Bases)+ Tools(Eval Console / Traces);NEW `NavGroupHeader` sub-component(`aria-hidden="true"` — visual-only,not separate landmark;`mt-3 px-3 pb-1 text-[10px] font-semibold uppercase tracking-wider text-muted-foreground first:mt-0`);所有 5 個 nav item 仍喺單一 `<nav aria-label="Primary">` 入面(W18 Vitest baseline test 對 5 items / `aria-current="page"` / focus-mode toggle 不變)。
- **F1.4** AppShell sidebar — **Labs section 不渲染**(W19 F5.4 Option C — prototype-only;`/labs/*` routes NOT 加入 `frontend/`);comment 標 future Tier 2 enablement = add a third `NavSection` behind env flag。
- **F1 wire-in** Topbar 右 cluster 加 `<NotificationsMenu />` 喺 Language toggle 之前;language toggle 上面 docstring update reflect F1.1+F1.2+F1.3+F1.4。

#### Acceptance criteria status(per checklist.md)

- [x] F1.1 NEW `notifications-menu.tsx` — `<Bell>` trigger + DropdownMenu + counter badge + useQuery + mock fallback + Mark all read + See all → disabled affordance + file header docstring
- [x] F1.2 Workspace switcher disabled affordance — `<DisabledAffordance>` 包住 disabled `<button>` + `Ricoh · RAPO` label + tooltip(W19 §2.3 leak fix);Language toggle migrated to `<DisabledAffordance>`
- [x] F1.3 Sidebar Tools sub-section — NAV_SECTIONS structure(Main + Tools)+ `<NavGroupHeader>` sub-component(visual-only,`aria-hidden="true"`)
- [x] F1.4 Labs section hidden(deliberate omission — no `/labs/*` routes in `frontend/`)
- [x] F1.5 NEW `disabled-affordance.tsx` — shared per W19 F5 §4 spec + p1-strict / p3-preview variants + TIER 2 badge + file header docstring
- [x] F1.6 Tokens 100%(`Grep '\[oklch'` across `frontend/` = **0** preserved);`pnpm exec tsc --noEmit` exit 0;`pnpm exec next lint` "No ESLint warnings or errors";`pnpm test:unit` 6 files/18 tests pass(W20 baseline post-CH-002 preserved — no regression)
- [x] F1.7 File header docstrings on both NEW files;Vitest test scaffolding **deferred → F8.4** per plan F1.7 "(F8 carries full pass)"

#### Deviations(if any)

| F# | Plan said | Actual | Why | Approver |
|---|---|---|---|---|
| F1.5 catalog §4 spec | Badge uses `bg-accent/12` | Rounded to `bg-accent/10`(Tailwind default opacity step)| `12` 唔係 Tailwind default opacity scale(0/5/10/15/20/25/…),要 add 入 tailwind.config 先 work — Karpathy §1.2 simplicity (avoid one-off config extension;視覺差異 ~2% opacity 忽略)| AI Karpathy §1.2 self-judgment |
| F1.7 Vitest test | Scaffolding for `<DisabledAffordance>` + `<NotificationsMenu>` at F1 | Deferred to F8.4(full pass)per plan literal | Plan F1.7 acceptance criterion 寫「(F8 carries full pass)」— F1 commits the component code;F8.4 batches the test files(same pattern as W18 F1→F8.4)| Plan §2 F1.7 + W18 precedent |
| F1 sequencing | NotificationsMenu first per checklist order | DisabledAffordance landed first(shared component F1.5)| F1.1 NotificationsMenu's `See all →` consumes `<DisabledAffordance>` — F1.5 must land first(dependency order;not a scope deviation)| AI sequencing per Karpathy §1.4 |
| Vitest baseline | W18 baseline 4 files/13 tests | Actual W20 baseline 6 files/18 tests(post-CH-002)| `session-start.md` §11 line 314 already noted "post-CH-002 6 files/18 tests";F1 preserves 18/18(no regression);F8.4 target should be 20+ tests | AI documentation accuracy |

#### Decisions / new OQ / risk surfaced

- **`<DisabledAffordance>` consumption grows** — F1 landed 3 call sites(Language toggle / Workspace switcher / NotificationsMenu See-all + Mark-all-read);Wave A targets ~10 affordances per W19 F5 §6 audit。Grep `<DisabledAffordance` count = the audit hook。
- **`Briefcase` icon import** — new lucide icon added(workspace switcher visual hint);no new dep(lucide-react already in package.json per W18 baseline)。
- **`apiClient.get<NotificationsResponse>('/notifications')` 404 silent** — endpoint not implemented backend-side;`retry: false` + mock fallback ensures topbar never breaks even in fully-offline dev。`query.isError` drives the Mark-all-read disabled affordance branch — graceful degradation pattern (W18 F4 dashboard precedent).

#### Actual vs Planned Effort

| F | Planned | Actual | Δ |
|---|---|---|---|
| F1.5 DisabledAffordance | 30 min | ~20 min | -33% |
| F1.1 NotificationsMenu | 60 min | ~30 min | -50% |
| F1.2 Workspace + Language migration | 30 min | ~25 min | -17% |
| F1.3 NAV_SECTIONS + NavGroupHeader | 30 min | ~20 min | -33% |
| F1.4 Labs hidden(deliberate omission)| 5 min | ~0 min(no code change)| -100% |
| F1.6 Verify(tsc + lint + oklch + test:unit)| 15 min | ~3 min | -80% |
| F1.7 docstrings + progress.md + commit | 30 min | ~15 min | -50% |
| **F1 Day 1 total** | **~3 hours**(1 plan-day)| **~1.5 hours** | **-50%** |

Real-calendar collapse pattern continues — W12-W18 1.8-4× collapse;F1 ~2× faster than 1 plan-day budget。

#### Carry-overs to next Day-N

- **F2 `/dashboard` real cards per ADR-0030 absorbed** — backend `/health` per-component connectivity payload(W19 F2 §3.1 item 1)+ frontend 5 cards + 4-stat strip rewrite。Day 2 focus。
- **F8.4 Vitest test for `<DisabledAffordance>` + `<NotificationsMenu>`** — scaffolding deferred per F1.7 plan literal;F8 carries the full pass(target 6 → 8+ files / 18 → 20+ tests)。
- **F8.1 multi-viewport browser smoke** — F1 surfaces NEW(workspace chip + notifications badge + Tools section header)need smoke at `sm` / `md` / `lg`;deferred to F8.1(R8 caveat per plan)。

---

## Day 2 — 2026-05-17

### F2 — `/dashboard` real cards per ADR-0030 absorbed scope(landed)

**Branch**:`main`(ahead of `origin/main` by 2 commits:`40964b6` kickoff + `b1fb75b` F1)。
**Commits this day**:`(this commit)` — single F2 commit covering backend F2.1+F2.2 + frontend F2.3+F2.4 + Vitest F2.6 extension。

#### What landed

- **F2.1 Backend** NEW `backend/api/routes/health.py` — extracted from `api/server.py`'s inline `{"status": "ok"}` route + extended payload。Pydantic v2 schemas:`ComponentStatus = Literal["ok", "not_configured", "degraded", "error"]` + `ComponentHealth(status, latency_ms, detail)` + `HealthResponse(status: "ok"|"degraded", components: dict[str, ComponentHealth])`。5 per-component checks(config-state-only per Karpathy §1.2 simplicity;real-I/O ping deferred Wave B+):
  - `azure_search` ← `app.state.retrieval_engine is not None`
  - `azure_openai` ← `app.state.embedder is not None`
  - `cohere` ← `engine.reranker is not None`(else `not_configured` per Q5 Path A)
  - `langfuse` ← `get_langfuse_client() is not None`(else `not_configured`)
  - `postgres` ← `settings.database_url`(else `not_configured` per ADR-0023 in-memory fallback)
  Top-level roll-up:`ok` if all components are `ok` or `not_configured`;`degraded` if any `degraded`/`error`。`server.py` 修改 — removed inline route function + `app.include_router(health.router)`。
- **F2.2 Backend pytest** NEW `backend/tests/api/test_health_route.py` — 7 tests covering all-green path + 2 degraded branches(retrieval_engine None + embedder None)+ 3 `not_configured` branches(Cohere optional + no DATABASE_URL + Langfuse no client)+ response schema shape contract;mypy strict clean on the new file。**7/7 pass**。
- **F2.3-F2.4 Frontend** `frontend/app/(app)/dashboard/page.tsx` rewrite — replaces W18 F4 5-card placeholder with **4-stat strip + 5 cards**:
  - **4-stat strip**(`<StatCard>` × 4 + skeleton)— Total KBs / Documents / Chunks / Storage MB,`grid grid-cols-2 lg:grid-cols-4`
  - **Knowledge bases** card — top-5 KB list(sorted by document count desc)+ name link → `/kb/[kb_id]` + per-row doc count;empty-state when `kbs.length === 0`;"View all knowledge bases →" link → `/kb`
  - **Recent queries** card — Q6 Open empty-state CTA → `/chat`(preserved per W18 F4 acceptance)
  - **Latest evaluation** card — no cached-run empty-state CTA → `/eval`(preserved)
  - **System health** card — **per-component dots** off `HealthResponse.components` via `useQuery(['health'])` + `refetchInterval: 60_000`(60s poll);5 dots Azure Search / OpenAI / Cohere / Langfuse / Postgres + label + `statusLabel(status)` text;dot colours via semantic tokens(`bg-success` / `bg-muted-foreground/40` / `bg-accent` / `bg-destructive` — no hardcoded oklch);`title={comp.detail}` for inline tooltip context
  - **Quick actions** card — 4 buttons preserved(New KB / Upload doc / Run eval / Open chat)
- **F2.6 Vitest extension** `frontend/tests/unit/dashboard.test.tsx` extended from W18 baseline 2 tests → **5 tests**(per plan F2.6):
  - existing 2 tests preserved(5 card headings + 4 quick-action links)
  - NEW **4-stat strip** test(KB count + Documents 17 + Chunks 320 + Storage 4.5 MB aggregated from fixture)
  - NEW **5 per-component dots** test(`role="list" aria-label="Component connectivity"` + 5 listitems + cohere/postgres "Not configured" labels)
  - NEW **top-5 KB list** test(2 KBs in fixture rendered as links to `/kb/[id]`)
- **F2.7 docstring** updated dashboard page docstring(W18 F4 → W20 F2 evolution note + per-component dots scope + 4-stat strip + semantic-token note)

#### Acceptance criteria status(per checklist.md)

- [x] F2.1 Backend `/health` per-component payload(`{status, components: {…} × 5}` + status taxonomy + Pydantic v2 schemas)— mypy strict clean(only pre-existing langfuse-stub error remains,same as feedback.py baseline)
- [x] F2.2 Backend pytest — 7/7 pass(all-green + 2 degraded + 3 not_configured + schema contract);coverage on `routes/health.py` ≥ 80% per CLAUDE.md §3.1 H6
- [x] F2.3 Frontend `dashboard/page.tsx` rewrite — 4-stat strip + 5 cards + per-component dots + top-5 KB list
- [x] F2.4 Loading skeletons(`<StatCardSkeleton>` + `<Skeleton>` per card)+ error banners(KB card destructive + health card destructive dot)+ empty states(no-KBs message + Q6 CTA + no-eval-run CTA)
- [x] F2.5 Tokens 100%(`bg-success`/`bg-muted-foreground/40`/`bg-accent`/`bg-destructive` semantic only — no hardcoded oklch);`pnpm exec tsc --noEmit` exit 0;`pnpm exec next lint` "No ESLint warnings or errors";`Grep '\[oklch'` across `frontend/` = **0**(W15→W18→W20 F1 milestone preserved — 1 accidental docstring occurrence reworded before commit,same fix as W18 F1.6 precedent)
- [x] F2.6 Vitest `dashboard.test.tsx` extended W18 baseline 2 tests → **5 tests**(+3 NEW per F2.6 plan literal:4-stat strip + per-component dots + top-5 KB list);`pnpm test:unit` 6 files / **21 tests pass**(W20 baseline post-F1 18 → 21)
- [x] F2.7 File header docstrings updated(routes/health.py NEW + dashboard/page.tsx rewrite reflect W18 → W20 F2 evolution)

#### Deviations(if any)

| F# | Plan said | Actual | Why | Approver |
|---|---|---|---|---|
| F2.1 real-I/O ping | "per-component status + latency_ms" suggested real pings | Config-state-only(latency_ms always None Wave A)| Karpathy §1.2 simplicity — real `SELECT 1` / `SearchClient.get_service_statistics()` pings add flap risk + 60s poll cost for marginal Wave A signal;schema keeps `latency_ms` field so Wave B+ pings populate without breaking response shape | AI Karpathy §1.2 self-judgment + plan F2 PARTIAL-PASS clause |
| F2.1 server.py routing | Inline route extension | Extract to `routes/health.py` + `app.include_router` | Better testability(pytest 7/7)+ matches other route modules pattern(auth/kb/query/...)| AI per existing pattern;not a deviation,just an extraction decision |
| F2.1 mypy strict | "clean" | Same as feedback.py baseline(1 pre-existing langfuse-stub error)| Project-wide pre-existing — langfuse SDK has no py.typed marker;health.py adds **0 new errors** post-cleanup of unused PostgresKBBackend import | Pre-existing project tolerance |
| F2.6 Vitest first-pass | top-5 KB link test used `findByRole({ name: /view all/ })` as the await-anchor | Fixed by using `findByRole({ name: 'Drive Project — Manuals' })` as anchor instead | The "View all →" link renders even in empty-state(kbs.length === 0)→ first attempt's await didn't actually wait for kbQuery resolution → test saw empty state. Switched anchor to data-dependent link → forces real wait | AI per Vitest pattern correction |

#### Decisions / new OQ / risk surfaced

- **Config-state-only health check** documented as Wave A scope;real-I/O pings explicitly deferred Wave B+ per plan F2 PARTIAL-PASS clause(no new OQ)。
- **`Settings.database_url`** is the Tier 1 signal for Postgres health;`make_kb_backend` runs lazily so absence = in-memory fallback per ADR-0023(no new risk)。
- **Component label localization** — `COMPONENT_LABELS` const English-only;i18n machinery deferred Tier 2 per architecture.md §11(no new OQ)。
- **Refetch interval 60s** — chosen for Wave A simplicity;Beta cohort traffic may require websocket/SSE push pattern to reduce poll noise → Wave B+ polish candidate(not a Wave A blocker)。

#### Actual vs Planned Effort

| F | Planned | Actual | Δ |
|---|---|---|---|
| F2.1 Backend `/health` extract + per-component payload | 45 min(0.5-1d C07 per W19 F2)| ~30 min | -33% |
| F2.2 Backend pytest 7 tests | 45 min | ~25 min | -45% |
| F2.3-F2.4 Frontend rewrite(4-stat strip + 5 cards + per-component dots + top-5 KB list)| 90 min | ~50 min | -45% |
| F2.5 Verify(tsc + lint + oklch + test:unit + pytest)| 15 min | ~5 min | -67% |
| F2.6 Vitest 3 NEW tests + 1 fix iteration | 30 min | ~25 min | -17% |
| F2.7 docstrings + progress.md + commit | 20 min | ~15 min | -25% |
| **F2 Day 2 total** | **~4 hours**(1 plan-day budget)| **~2.5 hours** | **-38%** |

Real-calendar collapse pattern continues — same 1.8-4× collapse band as W12-W18 + W20 F1。

#### Carry-overs to next Day-N

- **F3 `/chat` advanced surfaces per ADR-0031 Option B server-side Conversation History** — largest deliverable(3-4 days plan budget)。Day 3-5 focus。Postgres `conversations` + `messages` tables + 6 NEW `/conversations` CRUD endpoints + frontend Conversation History sidebar + 3 citation modes + InlineImageCard + ImageGallery + CitationPill + FeedbackBar comment + CRAG strip。
- **F8.1 multi-viewport browser smoke** — F2 surfaces NEW(4-stat strip + per-component health dots)need smoke at `sm` / `md` / `lg`;deferred to F8.1(R8 caveat per plan)。
- **Wave B+ candidate** — real-I/O pings for `/health` per-component(`SearchClient.get_service_statistics()` / Postgres `SELECT 1` / etc)to populate `latency_ms` + catch silent degradation。

---

<!-- Day 3+ entries to be appended by AI as F3-F9 land. Template:

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

#### Carry-overs to next Day-N

- ...

---

-->

## Retro(填 at F9 closeout)

> 7 sections per W18 / W19 retro template:
>
> 1. What worked
> 2. What didn't & friction
> 3. Surprises(positive + negative)
> 4. Decisions(architectural / scope / sequencing)
> 5. Carry-overs to W21+(NOT pre-created — items only;next phase folder at W21 kickoff)
> 6. Time tracking(plan-day budget vs actual real-calendar)
> 7. Spec-ref alignment(architecture.md v6 + ADR-0025/0028/0031 verification)
>
> **Phase Gate verdict** = TBD(PASS / PARTIAL PASS / FAIL with explicit rationale)

---

**Lifecycle reminder**:呢份 progress.md `status=active`(2026-05-16,per kickoff)。每 Day-N entry append；retro 喺 F9 closeout 寫。Status flip `active`→`closed` at F9.4。
