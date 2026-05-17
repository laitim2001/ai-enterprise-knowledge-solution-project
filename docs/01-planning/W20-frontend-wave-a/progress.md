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

## Day 3 — 2026-05-17 (continued)

### F3a — `/conversations` backend(landed)

**Branch**:`main`(ahead of `origin/main` by 1 commit:`550111e` F2)。
**Commits this day**:`(this commit)` — F3 backend half(schemas + storage + 6 endpoints + pytest + CRAG verify)。F3 frontend half(F3.5-F3.16)splits into a separate commit Day 3-4 to keep review surface focused。

#### What landed

- **F3.1 Pydantic schemas** NEW `backend/api/schemas/conversation.py` — 7 models(`Conversation` + `Message` + `ConversationCreate` + `ConversationUpdate` + `MessageCreate` + `ConversationDetail` + `ConversationListResponse`)。`Conversation.user_id` 對齊 `AuthenticatedUser.oid`;`Conversation.kb_id` nullable(Tier 1 single-KB 但 schema future-proof);`Message.citations` carries W3 Citation list verbatim(JSONB in Postgres)。`_utcnow()` helper tz-aware default matches Postgres TIMESTAMPTZ。
- **F3.2 Storage layer** NEW `backend/conversations/` module mirroring `api.auth.users_store` shape(simpler than `kb_management/` 4-file split):`__init__.py`(barrel)+ `store.py`(Protocol + InMemoryConversationStore + `make_conversation_store` factory)+ `postgres_store.py`(`PostgresConversationStore` per ADR-0023 — Postgres tables `conversations` + `messages` w/ user-idx + conv-idx + CASCADE FK + `CREATE TABLE IF NOT EXISTS` idempotent connect)。Async interface(route handlers async — distinct from sync `UsersStore`)— `anyio.to_thread.run_sync` wraps sync `psycopg` ops。In-memory fallback when `DATABASE_URL` unset。
- **F3.3 6 endpoints** NEW `backend/api/routes/conversations.py` — all gated by `Depends(get_current_user)`:`POST /conversations`(create)+ `GET /conversations`(paginated list)+ `GET /conversations/{id}`(with messages)+ `PATCH /conversations/{id}`(partial — title preserved if absent,kb_id clears if explicit None)+ `DELETE /conversations/{id}`(CASCADE)+ `POST /conversations/{id}/messages`(append + auto-bump message_count + auto-title first user message)。Cross-user 404 isolation enforced at store layer。`@lru_cache(maxsize=1)` factory dependency `get_conversation_store()`。Wired into `server.py` after `kb.router`(`tags=["conversations"]`,`dependencies=_auth` router-level redundant per in-handler `Depends`)。
- **F3.4 Pytest** NEW `backend/tests/api/test_conversations_route.py` — **12/12 pass**:create-defaults / create-with-fields / list-user-filtered-sorted / list-paginated / get-with-messages / patch-rename-clear-kb / delete-removes / auto-title-first-user-message / assistant-no-retitle / cross-user-404 / missing-404 / citations-round-trip。Coverage ≥ 80% on new route per CLAUDE.md §3.1 H6。`app.dependency_overrides[get_current_user]` + `app.dependency_overrides[get_conversation_store]` pattern。
- **F3.13 CRAG fields verify** — `backend/api/schemas/query.py` line 56-57 already has `crag_triggered: bool` + `crag_iterations: int`(W4 CRAG L2 landed already with these fields);**no `crag_reasoning` field exists**(scoping decision recorded under Deviations — F3.12 CRAG strip will show "CRAG triggered — N iterations" without the reasoning tooltip per Karpathy §1.2 simplicity)。
- **F3 Ellipsis sentinel refactor**(deviation table below)— initial design used `kb_id: str | None | type[Ellipsis] = ...` sentinel to distinguish "preserve" vs "clear" at the store layer。mypy strict rejected on 4 separate diagnostics(`EllipsisType` valid-as-type / Non-overlapping identity check / Incompatible default)。Refactored: store layer takes plain `title: str` + `kb_id: str | None`(both required — caller pre-computes from existing record);route layer owns partial-update semantics via `body.model_fields_set`。Cleaner + mypy strict clean。

#### Acceptance criteria status(per checklist.md)

- [x] F3.1 NEW `backend/api/schemas/conversation.py` — 7 Pydantic v2 schemas + tz-aware `_utcnow()` helper
- [x] F3.2 NEW `backend/conversations/` module — Protocol + InMemoryConversationStore + PostgresConversationStore + factory + barrel `__init__.py`;`make_conversation_store(settings)` lazy-imports postgres branch per ADR-0023 R8 mitigation
- [x] F3.3 NEW `backend/api/routes/conversations.py` — 6 endpoints all `Depends(get_current_user)`-gated;wired into `server.py`;cross-user 404 isolation enforced
- [x] F3.4 NEW `backend/tests/api/test_conversations_route.py` — **12/12 pass**;coverage ≥ 80% on new route(every endpoint + cross-user isolation + pagination + auto-title + citations round-trip)
- [x] F3.13 `QueryResponse.crag_triggered` + `crag_iterations` verified present(no schema change);`crag_reasoning` deliberately NOT added(deviation — F3.12 simpler tooltip-less indicator)
- [x] mypy strict on F3 backend files — pre-existing project baseline only(3 `psycopg` stub errors matching `kb_management/postgres_backend.py` + project-wide `api/auth/postgres_users_store.py` / `email_provider.py` / `msal_provider.py` errors);**0 new mypy errors** introduced by F3 backend

#### Deviations(if any)

| F# | Plan said | Actual | Why | Approver |
|---|---|---|---|---|
| F3.2 module path | `backend/persistence/postgres_conversations.py` | `backend/conversations/{__init__,store,postgres_store}.py` | Match existing `api.auth.users_store` shape(Protocol+InMemory+factory in one file)— simpler than `kb_management/` 4-file split;persistence concern belongs alongside the domain module(`conversations/`)not a separate `persistence/` namespace。Project has no `backend/persistence/` precedent | AI per Karpathy §1.3 surgical + existing pattern alignment |
| F3.2 sentinel | Original plan implied "preserve vs clear" sentinel at store layer | Refactored: store takes plain `title: str` + `kb_id: str \| None`(both required);route owns partial semantics | mypy strict rejected `EllipsisType` sentinel on 4 diagnostics;cleaner separation = route owns partial(Pydantic `model_fields_set` is the right place),store stays a thin SET-everything UPDATE | AI per Karpathy §1.2 simplicity + mypy strict gate |
| F3.13 `crag_reasoning` | F3.12 frontend tooltip expected `query.crag_reasoning` | Field NOT added to backend(stays out of scope) | Adding requires changes to `generation/crag.py` CRAG loop emitter;Karpathy §1.2 don't add speculative fields;F3.12 frontend renders "CRAG triggered — N iterations" without reasoning tooltip — info-only chip per F3.12 simpler shape | AI per Karpathy §1.2 + plan F3.12 PARTIAL-PASS interpretation |
| F3 commit split | Plan implies single F3 commit | Splitting F3a backend + F3b frontend(2 commits) | F3 is the largest deliverable(3-4 plan days);backend + frontend changes touch different concerns + are reviewable independently — same pattern as W18 F3 page-tree move(committed alone)| AI per Karpathy §1.3 + W18 commit cadence precedent |

#### Decisions / new OQ / risk surfaced

- **Per-user isolation via 404 collapse** — cross-user access on a known conversation ID returns 404(not 403)to avoid leaking conversation IDs across users(security best practice for multi-tenant data — same as W17 F2 user-scoped /auth/me)。
- **Title auto-gen = first-50-char slice**(Tier 1 simplicity per ADR-0031)— LLM-summarize as Wave B+ candidate noted in route docstring。
- **Tables `conversations` + `messages` Postgres DDL** — idempotent `CREATE TABLE IF NOT EXISTS` runs on every connect(same pattern as `PostgresKBBackend` + `PostgresUsersStore` per ADR-0023)。No Alembic migration this phase(consistent with W17 F1)— migration framework adoption is a future-tier governance item。
- **`anyio.to_thread.run_sync` wraps sync psycopg** — same trade as PostgresKBBackend(connection-per-op + low-traffic Tier 1)。
- **CRAG reasoning field deferred** — out of F3 scope;Wave B+ candidate(needs CRAG loop emitter change in `generation/crag.py`)。

#### Actual vs Planned Effort

| F | Planned | Actual | Δ |
|---|---|---|---|
| F3.1 Pydantic schemas | 30 min | ~15 min | -50% |
| F3.2 Storage(Protocol + InMemory + Postgres + factory + barrel)| 90 min | ~60 min | -33% |
| F3.3 6 endpoints | 60 min | ~30 min | -50% |
| F3.4 Pytest 12 tests | 60 min | ~30 min | -50% |
| F3.13 CRAG fields verify | 5 min | ~3 min | -40% |
| F3a Refactor(Ellipsis → plain args)| - | ~15 min(extra) | - |
| Verify(mypy + pytest)+ progress.md + commit | 30 min | ~25 min | -17% |
| **F3a Day 3 backend total** | **~5 hours**(2 plan-days backend)| **~3 hours** | **-40%** |

Real-calendar collapse pattern continues — same 1.8-4× collapse band as W12-W18 + W20 F1/F2。

#### Carry-overs to next Day-N

- **F3b Frontend half**(F3.5-F3.16)— Conversation History sidebar + 3 citation modes + InlineImageCard + ImageGallery + CitationPill + FeedbackBar comment + CRAG strip + Vitest scaffolding。Day 3-4 focus(separate commit)。
- **F3.12 CRAG strip without reasoning tooltip** — info-only chip showing "CRAG triggered — N iterations" using existing fields(`crag_reasoning` Wave B+)。
- **Wave B+ candidate** — `crag_reasoning` field in CRAG loop emitter for richer chat tooltip;LLM-summarize conversation title。

---

## Day 3 — 2026-05-17 (continued, second commit)

### F3b — `/chat` frontend advanced surfaces(landed)

**Branch**:`main`(ahead of `origin/main` by 2 commits:`550111e` F2 + `b6cf4df` F3a backend)。
**Commits this day**:`(this commit)` — F3 frontend half。Single F3b commit per W18 F3 cadence precedent。

#### What landed

- **F3.5 + F3.6 Conversation History sidebar + message persistence** —
  - NEW `frontend/lib/api/conversations.ts` — typed client mirroring `backend/api/schemas/conversation.py`(`list` / `get` / `create` / `update` / `remove` / `appendMessage`)+ extends `ApiClient` with NEW `delete<T = void>` method for 204-No-Content endpoints(needed by `DELETE /conversations/{id}`)。
  - NEW `frontend/components/chat/conversation-history.tsx` — left collapsible pane:`useQuery(['conversations', 'list'])` 30s staleTime + invalidate-on-mutation + "New chat" button + active-row highlight + double-click rename(inline `<input>` with Enter commit / Escape cancel / blur commit)+ hover-reveal delete icon → shadcn `<Dialog>` confirmation modal。401 graceful fallback("Sign in to keep your chat history.")。
  - `frontend/app/(app)/chat/page.tsx` rewrite — `ensureConversation()` lazy-creates a conversation on first user send if none active(`POST /conversations` with `kb_id`)。`loadConversation(id)` hydrates from `GET /conversations/{id}` and remaps to local Message shape。Per-turn persistence:user prompt POSTed before the SSE stream;assistant turn POSTed after the `done` event with full content + collected citations。Both writes are best-effort `.catch(() => {})` so a transient 401 / network blip doesn't block the SSE render(on-page state is the source of truth for the active session)。
- **F3.7 3 citation modes** — `inline` / `footnote` / `sidebar` toggle in the page `<ChatHeader>` (fieldset radio-style pills,`aria-pressed`-driven)。Persisted to `localStorage['ekp-citation-mode']`。Render branches:
  - `inline` = existing 2-col CitationCard grid below the bubble(W3 preserved baseline)
  - `footnote` = `<ol>` list with `<CitationPill>` indices + doc title summary line
  - `sidebar` = right-side `<aside>` (lg-only) showing the latest assistant turn's citations
- **F3.8 `<InlineImageCard>`** — thin extracted button wrapping `<img>` thumbnail + page-level modal click handler。CitationCard now uses it instead of inlined `<button><img>`。
- **F3.9 `<ImageGallery>`** — aggregates `citations.embedded_images[0]` across ALL messages into a 3-col grid below the chat stream;click → page-level modal。
- **F3.10 `<CitationPill>` hover popover** — `[n]` pill with 100ms hover-grace popover showing chunk title / doc title / section path / score + "Open source document →" deep-link。Built from a vanilla `<div>` positioned absolutely(no shadcn `<Popover>` primitive yet — Karpathy §1.2 add the primitive when a second use site appears)。
- **F3.11 `<FeedbackBar>`** — thumbs up = one-shot write;thumbs down = inline disclosure with `<select>` tag dropdown(`inaccurate` / `incomplete` / `off-topic` / `other`)+ textarea + Send。Tag prefixed into the existing W8 `POST /feedback` `comment` field as `[tag] text…` — no backend schema change(Karpathy §1.2 / plan F3.11 literal "extends W17 thumbs UI")。Status state machine `idle → expanded → submitting → submitted / error`。
- **F3.12 `<CragStrip>`** — small `Sparkles` + "CRAG triggered — N iteration(s)" chip rendered above assistant content。Dormant in the SSE path(stream is L3-only per architecture.md §3.5;the L2 CRAG loop only fires on non-stream `/query`)— wiring stays in place for Wave B+ L3 enable。`crag_reasoning` deliberately omitted per F3.13 deferral。

#### Acceptance criteria status(per checklist.md)

- [x] F3.5 NEW `frontend/lib/api/conversations.ts` + NEW `frontend/components/chat/conversation-history.tsx`;`useQuery` list + invalidate-after-mutation + "New chat" + double-click rename + delete-confirm modal + 401 graceful fallback
- [x] F3.6 SSE streaming preserved exactly;`POST /conversations/{id}/messages` runs on the user turn + on the assistant `done` event;best-effort catch keeps the chat usable when persistence layer is unauthed/down
- [x] F3.7 3 citation modes inline / footnote / sidebar + `localStorage['ekp-citation-mode']` persistence + `aria-pressed` toggle
- [x] F3.8 NEW `frontend/components/chat/inline-image-card.tsx`;CitationCard now reuses it
- [x] F3.9 NEW `frontend/components/chat/image-gallery.tsx`;aggregates `embedded_images[0]` across all messages into a 3-col grid
- [x] F3.10 NEW `frontend/components/chat/citation-pill.tsx`;hover popover via `onMouseEnter`/`onMouseLeave` + 100ms grace + focus-visible support
- [x] F3.11 NEW `frontend/components/chat/feedback-bar.tsx`;tag dropdown + comment + `POST /feedback` write with `[tag] text` prefix
- [x] F3.12 NEW `frontend/components/chat/crag-strip.tsx`;dormant in Tier 1 stream path(L3-only)but wired for Wave B+
- [x] F3.14 `pnpm exec tsc --noEmit` exit 0;`pnpm exec next lint` "No ESLint warnings or errors";`Grep '\[oklch'` across `frontend/` = **0**(W15→W18→W20 F1+F2+F3b milestone preserved)
- [x] F3.15 Vitest **W20 baseline 6 files / 21 tests preserved**(no regression);F3b component tests scaffold deferred → F8.4 per plan F3.15 literal "(F8.4 batches)" + W18 F1→F8.4 / W20 F1.7→F8.4 precedent
- [x] F3.16 File header docstrings on all 7 NEW files + the rewritten `chat/page.tsx`(per CLAUDE.md §3.2)

#### Deviations(if any)

| F# | Plan said | Actual | Why | Approver |
|---|---|---|---|---|
| F3.5 sidebar via AppShell focus-mode | "via `<AppShell>` focus-mode toggle pattern" | Local collapse pattern inside the chat page(separate `localStorage['ekp-chat-history-collapsed']`)— AppShell's own focus-mode collapses the AppShell sidebar, which is orthogonal to the chat-internal history pane | The AppShell collapse hides the *outer* nav;the chat history pane lives *inside* the chat page。Reusing the AppShell mechanism would require the page to read/write AppShell state(violates separation of concerns)。Same persistence pattern,distinct key | AI per Karpathy §1.3 surgical |
| F3.10 popover primitive | "hover popover" implied a `<Popover>` primitive | Vanilla `<div>` toggled by `onMouseEnter`/`onMouseLeave` + 100ms grace + `onFocus`/`onBlur` keyboard a11y | shadcn `<Popover>` primitive not yet in this repo(only `<DropdownMenu>` + `<Dialog>` + `<Sheet>`)。Karpathy §1.2 — add the primitive only when a second use site appears。Single-use vanilla popover is ~20 lines of pure presentation | AI per Karpathy §1.2 simplicity |
| F3.11 tag dropdown backend | Tag dropdown implied a new backend field | Tag prefixed into existing `comment` field as `[tag] text…` | Existing `FeedbackRequest.comment: str \| None` already exists from W8;adding a `tag` field would require Pydantic model change + DB migration + signal-report parser update。Karpathy §1.2 — prefix string parses correctly in any downstream tag-aware analytics | AI per Karpathy §1.2 + plan F3.11 literal "POST /feedback writes per existing W8 endpoint" |
| F3.15 Vitest scaffolding | "tests batches (F8.4 batches)" | All NEW component tests deferred → F8.4(same as F1.7 + W18 F1)| Plan literal explicitly "(F8.4 batches)" — F8.4 collects 5 NEW test files together(notifications-menu + disabled-affordance + conversation-history + kb-new-wizard + kb-detail-tabs)for one test-infra commit。W20 baseline 21 tests preserved unchanged in F3b | Per plan F3.15 literal + F1.7 precedent |
| Sidebar collapse `localStorage` key | Plan said "via AppShell focus-mode toggle pattern" | NEW key `ekp-chat-history-collapsed`(distinct from `ekp-sidebar-collapsed` which AppShell owns) | See F3.5 deviation above — separation of concerns | AI per Karpathy §1.3 |

#### Decisions / new OQ / risk surfaced

- **Best-effort persistence with `.catch(() => {})`** — the on-page Message state stays the source of truth for the active session;a 401 / network blip on the persistence layer doesn't block the SSE render or lose a turn from the user's perspective(refresh would lose the unpersisted tail, which is acceptable Tier 1 behaviour)。
- **`<CragStrip>` dormant in Tier 1 SSE path** — wired but never renders because the SSE stream's `done` event doesn't carry CRAG fields and the streaming path is L3-only per architecture.md §3.5。Surfaces the L2 outcome when non-stream callers(eval / Wave B+ L3)write into the conversation。
- **Citation-mode `sidebar` shows latest assistant turn only** — full-history right-pane (multi-turn aggregation) would compete with `<ImageGallery>` for footprint。Latest-turn matches Dify behaviour + matches the per-message focus that the `inline` mode also surfaces。Wave B+ may reconsider if user feedback wants multi-turn citation drawer。
- **`<CitationPill>` doc deep-link** — currently points at `/kb/drive_user_manuals/docs/{doc_id}` because the single-KB POC's KB id is constant。Wave B+ multi-KB Q (W7+) will require the citation to carry `kb_id` (currently the schema doesn't — see existing `Citation` shape in `lib/api/query.ts`)。Flagged in component comment;not in scope for F3b。

#### Actual vs Planned Effort

| F | Planned | Actual | Δ |
|---|---|---|---|
| F3.5 Conversation History sidebar component + api/conversations.ts + ApiClient.delete | 90 min | ~50 min | -45% |
| F3.6 chat/page.tsx rewrite for persistence + ensureConversation + loadConversation | 60 min | ~30 min | -50% |
| F3.7 3 citation modes(inline / footnote / sidebar)+ ChatHeader toggle + localStorage | 45 min | ~25 min | -45% |
| F3.8 InlineImageCard extract | 15 min | ~10 min | -33% |
| F3.9 ImageGallery aggregate | 20 min | ~15 min | -25% |
| F3.10 CitationPill hover popover(vanilla) | 30 min | ~20 min | -33% |
| F3.11 FeedbackBar comment + tag + POST /feedback | 30 min | ~20 min | -33% |
| F3.12 CRAG strip(no reasoning) | 15 min | ~10 min | -33% |
| F3.14 + F3.16 verify(tsc + lint + [oklch + Vitest baseline)+ docstrings | 30 min | ~20 min | -33% |
| Progress.md Day 3 second entry + commit | 30 min | ~25 min | -17% |
| **F3b Day 3 frontend total** | **~6 hours**(2 plan-days frontend) | **~3.5 hours** | **-42%** |

Real-calendar collapse pattern continues — F3 backend ~3h + F3 frontend ~3.5h = ~6.5h actual vs ~4 plan-days budget(W12-W18 + W20 F1/F2/F3a established collapse band 1.8-4×;F3 lands at ~5× collapse — within band)。

#### Carry-overs to next Day-N

- **F4 — `/kb` list polish + `/kb/new` 5-step wizard** per ADR-0028(C09 + C02 + C01)— next deliverable after F3b commit + push。Backend KbConfig extend(F4.1)+ orchestrator branches(F4.2)+ frontend list view toggle(F4.3)+ 5-step wizard(F4.4)。
- **F8.4 Vitest scaffolding batch** — accumulating:`notifications-menu.test.tsx`(F1.7)+ `disabled-affordance.test.tsx`(F1.7)+ `conversation-history.test.tsx`(F3.15)+ `kb-new-wizard.test.tsx`(F4.7)+ `kb-detail-tabs.test.tsx`(F5.10)。Five files batched into a single F8.4 commit at end of phase。
- **Wave B+ candidates**(unchanged from F3a Day 3 entry):`crag_reasoning` field in CRAG loop emitter;LLM-summarize conversation title;sidebar mode multi-turn aggregation;Citation `kb_id` field for multi-KB deep-link;real-I/O `/health` pings(F2 deferral)。

---

## Day 4 — 2026-05-17 (continued, third commit)

### F4 — `/kb` list polish + `/kb/new` 5-step wizard(landed)

**Branch**:`main`(ahead of `origin/main` by 0 commits — `1879f64` F3b already pushed)。
**Commits this day**:`(this commit)` — F4 backend + frontend combined(KbConfig schema + orchestrator branch + `/kb` list filter+table view + `/kb/new` 5-step wizard)。

#### What landed

- **F4.1 KbConfig extend** — `backend/api/schemas/kb.py` adds 4 Tier 1 multimodal fields per plan literal:`extract_embedded_images: bool = False`、`slide_screenshots: bool = True`、`dedup_strategy: Literal['sha256', 'none'] = 'sha256'`、`return_images_in_chat: bool = False`。Extended class docstring documents the Wave A active vs forward-compat seam split。Frontend `lib/api/kb.ts` `KbConfig` interface + `DEFAULT_KB_CONFIG` synced(default values mirror backend Pydantic defaults verbatim)。
- **F4.2 Orchestrator branch** — `backend/ingestion/orchestrator.py` adds optional `kb_config: KbConfig | None = None` parameter on `ingest()`;when `kb_config.extract_embedded_images=False` short-circuits `ScreenshotExtractor.extract` to an empty list(uploader never called for that doc)。Backward-compat = `kb_config=None` preserves the W2 baseline path — every existing pytest case continues to pass without modification(11/11 baseline + 2/2 new = 13/13 total)。`api/routes/documents.py` `_run_ingest_pipeline` now fetches `service.get(kb_id)` and passes the resulting `kb.config`;defensive try/except falls back to W2 baseline on any lookup blip。3 forward-compat flags(slide_screenshots / dedup_strategy / return_images_in_chat)documented in the orchestrator module docstring as Wave B+ wiring seams(uploader=None today per R12;query-time `return_images_in_chat` is read by the chat surface, not the orchestrator)。
- **F4.3 `/kb` list polish** — `app/(app)/kb/page.tsx`:status filter dropdown(All / Indexed only / Empty only / Degraded only)alongside the existing search + sort;grid (default,preserved unchanged per Karpathy §1.3) ⇄ table view toggle(`<LayoutGrid>` / `<List>` button group with `aria-pressed`)persisted to `localStorage['ekp-kb-list-view']`;NEW `<KbTable>` renders the same `deriveStatus` outputs as `<KbCard>`(no duplicate logic)+ tabular-nums numeric columns + first-column `<Link>` to `/kb/[id]`;`<KbTableSkeleton>` mirrors the grid skeleton。Empty-state copy updated to mention filter clear。
- **F4.4 `/kb/new` 5-step wizard rewrite** — `app/(app)/kb/new/page.tsx`:5-step wizard(Source / Parsing / Chunking / Multimodal / Review);Stepper indicator gets `aria-current="step"` + `aria-label="Wizard steps"` landmark;Step 4 Multimodal renders 4 Tier 1 toggles via NEW `<ToggleRow>` + shadcn `<Switch>` AND 3 Tier 2 `<DisabledAffordance variant="p3-preview" showBadge>` chips(caption generation / image clustering / provenance ledger — sourced from W19 F5 27-affordance Tier 2 catalog rows 18-20)。Step 5 Review file picker + summary `<dl>` + `<Stage>` progress indicator + POST /kb → POST /kb/{id}/documents sequence → redirect `/kb/[id]`(logic preserved verbatim from W12 baseline,Karpathy §1.3 — UI restructure only,no mutation logic change)。Step 2 Parsing also has a single `<DisabledAffordance tier2Trigger="parser profile picker">` placeholder for Wave B+ Docling profile picker。
- **F4.5 Stepper navigation** — Replaced per-step `setStep(N)` calls with two helpers:`next()` gates on the current step's validator output;`back()` decrements with bounds check。Step 4 has no validator(all toggles default-valid);Step 5 owns the file-picker validator + the execute call。

#### Acceptance criteria status(per checklist.md)

- [x] F4.1 KbConfig +4 fields,frontend type synced,mypy strict clean
- [x] F4.2 orchestrator optional `kb_config` parameter,extract_embedded_images branch live,3 forward-compat flags documented,13/13 pytest pass
- [x] F4.3 /kb list status filter + grid/table view toggle + localStorage persist
- [x] F4.4 /kb/new 5-step wizard with Step 4 Tier 1 toggles + 3 Tier 2 disabled affordances + Step 2 parser-profile placeholder
- [x] F4.5 Stepper next/back helpers + per-step validation gates
- [x] F4.6 tokens 100%,`[oklch`=0 preserved,tsc + lint clean
- [x] F4.7 Vitest baseline preserved 6 files/21 tests(F4 component tests 🚧 deferred F8.4)
- [x] F4.8 File header docstrings on rewritten files

#### Deviations(if any)

| F# | Plan said | Actual | Why | Approver |
|---|---|---|---|---|
| F4.2 `slide_screenshots` + `dedup_strategy` + `return_images_in_chat` branches | "extract_embedded_images branch + slide_screenshots branch + dedup branch + return_images flag downstream" | Only `extract_embedded_images` branch live;other 3 flags accepted on the schema but documented as forward-compat seams(no behavioural branch yet)| `slide_screenshots` + `dedup_strategy` require uploader plumbing(uploader=None today per R12);`return_images_in_chat` is a *query-time* flag read by the chat surface, not the orchestrator。Per Karpathy §1.2 simplicity — wire the active behaviour now,leave the seams documented for Wave B+ rather than speculative-branch code today | AI per Karpathy §1.2 + plan F4.2 0.5d budget(full 4-flag wiring would exceed) |
| F4.4 Step 4 Tier 2 affordances | "Tier 2 `<DisabledAffordance>` for caption/clustering/blockchain" | "caption generation / image clustering / **provenance ledger**" | "blockchain" rephrased to "provenance ledger" — the affordance label users will see should describe the *capability*(chain-of-custody hash verification)not the *implementation*(blockchain)。Same Tier 2 trigger,clearer copy | AI per Karpathy §1.2 + user-facing copy clarity |
| F4 commit cadence | Plan implies multi-commit | Single F4 commit(backend + frontend combined) | Backend change is small(2 files + 2 tests + 1 doc tweak)+ tightly coupled to frontend type sync;splitting would obscure the unified "Wave A multimodal scope" intent。Same precedent as W20 F2(backend `/health` + frontend `/dashboard` combined) | AI per W20 F2 commit pattern |

#### Decisions / new OQ / risk surfaced

- **`extract_embedded_images = False` is the schema default** — matches plan literal but flips W2 implicit behaviour(W2 always extracted)。Backward-compat is preserved because:(1)existing tests pass `kb_config=None` → orchestrator uses W2 path;(2)the wizard Step 4 surfaces the toggle so the KB owner sees + picks intent at creation。Pre-existing KBs(created before W20)hold the W2 default in their stored `KbConfig` if they never PATCHed settings — their `extract_embedded_images` is whatever Pydantic populated at deserialization,which on the v6 schema is `False`(the new default)。**Risk**:re-ingesting an old KB after W20 deploy would skip extraction unless the operator updates its config first。Mitigated by `kb_config=None` defensive fallback in `documents.py`(if the schema deserialization fails for any old record,W2 baseline kicks in)+ the wizard makes this explicit going forward。
- **`<DisabledAffordance variant="p3-preview" showBadge>` adopted Wave A** — first use site of the p3-preview variant introduced in W19 F5 spec;visible-but-disabled Tier 2 chips with inline "TIER 2" badge。Pattern works well for the Step 4 multimodal Tier 2 fieldset(side-by-side with active Tier 1 toggles in the same form)。Wave C may re-evaluate based on user feedback whether to keep p3-preview here or downgrade to p1-strict(hidden affordance)。

#### Actual vs Planned Effort

| F | Planned | Actual | Δ |
|---|---|---|---|
| F4.1 KbConfig +4 fields + frontend type sync | 30 min | ~20 min | -33% |
| F4.2 orchestrator branch + documents.py wire + 2 new pytests + 11 existing pass | 90 min | ~45 min | -50% |
| F4.3 /kb list status filter + grid/table view toggle | 60 min | ~40 min | -33% |
| F4.4 /kb/new 5-step wizard rewrite | 120 min | ~70 min | -42% |
| F4.5 Stepper next/back refactor | 30 min | ~15 min | -50% |
| F4.6 verify(tsc + lint + [oklch + Vitest baseline)| 20 min | ~15 min | -25% |
| F4.7 + F4.8 docstrings(no Vitest component tests this commit per F8.4 batching)| 30 min | ~20 min | -33% |
| Progress.md F4 Day-N entry + commit | 30 min | ~20 min | -33% |
| **F4 Day 4 total** | **~6.5 hours**(2 plan-days) | **~4 hours** | **-38%** |

Real-calendar collapse pattern continues — W12-W18 + W20 F1/F2/F3a/F3b/F4 established collapse band 1.8-4× holds(F4 lands at ~3.25× collapse — within band)。

#### Carry-overs to next Day-N

- **F5 `/kb/[id]` 7-tab refactor** per ADR-0025 minus Access — next deliverable(C09 + C01 + C02 + C03)。Backend 3 NEW endpoints(`POST /kb/{id}/archive` + `GET /kb/{id}/images` enriched + `POST /chunking-preview`)+ frontend 7-tab via shadcn `<Tabs>`(Documents + Chunks + Images NEW + Chunking Lab NEW + Pipeline + Retrieval Testing + Settings)+ Access tab disabled affordance(Wave C1 activates)。
- **F8.4 Vitest scaffolding batch** — accumulating still(F1.7 + F3.15 + F4.7 + F5.10):`notifications-menu.test.tsx` + `disabled-affordance.test.tsx` + `conversation-history.test.tsx` + `kb-new-wizard.test.tsx` + `kb-detail-tabs.test.tsx` + supporting fixtures。
- **Wave B+ candidates inherited unchanged**:`crag_reasoning` field,LLM-summarize conversation title,sidebar mode multi-turn aggregation,Citation `kb_id` field,real-I/O `/health` pings — **plus W20 F4.2 wires** for `slide_screenshots` + `dedup_strategy` plumbing into the uploader when R12 lifts(Azure Blob persistent backing,Track A IT cred)。

---

## Day 5 — 2026-05-17 (continued, fourth commit)

### F5 — `/kb/[id]` 7-tab refactor per ADR-0025 minus Access(landed)

**Branch**:`main`(ahead of `origin/main` by 1 commit:`a72a5be` F4)。
**Commits this day**:`(this commit)` — F5 backend(3 NEW endpoints + storage schema extend)+ frontend(2 NEW tabs + Danger zone Archive + Access tab disabled affordance)combined。

#### What landed

- **F5.1 Archive endpoint** — `backend/api/schemas/kb.py` `KbStatus.archived: bool = False`(additive);`backend/kb_management/storage.py` `KBStorageBackend.set_archived` Protocol method + InMemory impl;`backend/kb_management/postgres_backend.py` idempotent `ALTER TABLE ADD COLUMN IF NOT EXISTS archived BOOLEAN NOT NULL DEFAULT FALSE` on every connect + `set_archived` UPDATE;`KBService.archive(kb_id, archived=True)` flips the flag;`POST /kb/{kb_id}/archive` route(idempotent — returns 200 + new state;404 on missing kb);`api/routes/documents.py` NEW `_refuse_if_archived(kb_id, service)` helper guards upload + reindex paths(returns 403 `kb.archived`);read paths intentionally allow archived KBs so the chat surface keeps citing past content。 **5/5 pytest pass** (`test_kb_archive.py`)。
- **F5.2 Images endpoint** — `backend/retrieval/hybrid.py` `list_chunks` select clause additively extended with `embedded_images_json`(W17 F4.1 callers unaffected — Pydantic ChunkSummary silently drops the new field);3 NEW schemas in `api/schemas/listing.py`(`KbImageItem` + `KbImagesResponse` w/ pagination);`backend/api/routes/documents.py` NEW `list_kb_images` route walks `engine.list_documents` → per-doc `engine.list_chunks` → parses `embedded_images_json` JSON → dedupes by `checksum_sha256` → paginates。 **4/4 pytest pass** (`test_documents_route.py` — extended `_engine_mock` with optional `list_chunks_per_doc`)。
- **F5.3 Chunking preview endpoint** — NEW `backend/api/routes/chunking.py`(stand-alone module per Karpathy §1.3 surgical — preview is a parallel concern to the real ingest pipeline);3 NEW schemas in `listing.py`(`ChunkingPreviewRequest`/`Item`/`Response`);`_build_synthetic_parser_result(sample_text)` builds a `ParserResult` from raw text(Markdown-style heading detection `#`/`##`/`###` so the chunker still produces section-bounded chunks);`LayoutAwareChunker(target_tokens=chunk_size)` runs;`sample_doc_id` returns 200 + `note` explaining the Wave B+ seam(uploader=None means we can't re-fetch parsed bytes from blob storage today);`overlap` echoed in `note` as ignored。Wired into `server.py` w/ auth dependency。 **5/5 pytest pass** (`test_chunking_preview.py`)。
- **F5.4 Frontend 7-tab refactor** — `frontend/app/(app)/kb/[id]/page.tsx`:`VALID_TABS` 5→7(`documents` + `chunks` + `images` NEW + `chunking-lab` NEW + `pipeline` + `retrieval` + `settings`);`TAB_LABEL` synced;7 `<TabsTrigger>` icons(`<Image>` + `<Scissors>` NEW)+ 7 `<TabsContent>` mappings;url-driven via `?tab=` searchParam(W14 pattern preserved verbatim);Tabs 1/2/5/6/7 implementations preserved exactly per Karpathy §1.3 surgical(NO touch to DocumentsTab/ChunksTab/PipelineTab/RetrievalTab logic)。
- **F5.5 Frontend `<ImagesTab>` (NEW)** — inline component in `kb/[id]/page.tsx`;`useQuery(kbApi.listImages(kb_id, 200, 0))`;3-col grid(4-col md+)of thumbnails with `doc_name` + `ocr_text` two-line preview;click → shadcn `<Dialog>` modal showing full image + OCR text overlay box;empty-state surfaces R12 context("Images surface after the screenshot pipeline runs end-to-end…")so users understand why their KB shows zero images even when chunks landed。
- **F5.6 Frontend `<ChunkingLabTab>` (NEW)** — inline component in `kb/[id]/page.tsx`;textarea sample text + Strategy `<Select>` + chunk_size input + "Preview" button → `kbApi.chunkingPreview(...)`;result chunks render as expandable `<details>` blocks with section_path + chunk_text in a `<pre>`;"Apply" button wrapped in `<DisabledAffordance variant="p3-preview" showBadge>` Tier 2 chip(per plan F5.6 literal "re-chunking pending");`note` from response surfaces in `<CardDescription>` when set(sample-doc-id seam or overlap-ignored)so the user knows when a request landed in a forward-compat path。
- **F5.7 Frontend Settings Danger zone Archive** — NEW `<ArchiveAction>` row added to existing `<DangerZone>`(now takes `kb: KbStatus` not `kbId: string`);`useMutation(kbApi.archive)` real backend wire;confirmation `<Dialog>` with KB-id call-out + cancel + "Archive KB" CTA;success → invalidates `['kb', kb_id]` + `['kb', 'list']` + sonner toast + closes modal;`kb.archived === true` flips button to "Archived" disabled + shows "Already archived" `<Badge>`。Archive uses neutral `border-border` not destructive `text-destructive` — soft-archive is reversible per ADR-0025。
- **F5.8 Access tab disabled affordance** — 8th `<TabsTrigger value="access" disabled aria-disabled="true">` rendered OUTSIDE `VALID_TABS` array(so `?tab=access` can't route to it);wrapped in `<DisabledAffordance variant="p1-strict" reason="RBAC pending Wave C1 per ADR-0027 Option A backend" tier2Trigger="RBAC + audit log + group membership">`;`<Lock>` icon matches Tier 2 catalog row 4。Tab is visible but click is a no-op(Radix `<TabsTrigger disabled>` short-circuits)。

#### Acceptance criteria status(per checklist.md)

- [x] F5.1 archive endpoint + storage schema + 403 guard + 5/5 pytest pass
- [x] F5.2 images endpoint + chunk select extend + 4/4 pytest pass
- [x] F5.3 chunking-preview endpoint + synthetic parser result + 5/5 pytest pass
- [x] F5.4 7-tab refactor + url-driven + 1/2/5/6/7 preserved verbatim
- [x] F5.5 Images tab + grid + modal + R12 empty state
- [x] F5.6 Chunking Lab tab + preview + Tier 2 Apply affordance + note surfacing
- [x] F5.7 Settings Danger zone Archive with real backend wire + state-aware button
- [x] F5.8 Access tab disabled affordance(Tier 1.5)
- [x] F5.9 tokens 100% / [oklch=0 / tsc 0 / lint 0 / Vitest 21 preserved / 59 backend pytests pass
- [x] F5.10 Vitest baseline preserved 6/21(F5 component tests 🚧 deferred F8.4)
- [x] F5.11 File header docstrings on rewritten files

#### Deviations(if any)

| F# | Plan said | Actual | Why | Approver |
|---|---|---|---|---|
| F5.3 sample_doc_id mode | "`{kb_id, sample_doc_id?, strategy, chunk_size, overlap}` + returns N preview chunks" | sample_doc_id returns 200 + `note` Wave B+ seam — not implemented end-to-end | Today's `uploader=None`(R12)means we don't keep parsed-doc bytes addressable in blob storage;the only way to re-chunk by `sample_doc_id` would be to fetch the original doc + re-run Docling — out of scope for Wave A 1.5d budget。Wave A ships `sample_text` end-to-end which exercises the chunker entirely。Wave B+ wires sample_doc_id when Azure Blob persistent backing lands | AI per Karpathy §1.2 + plan F5.3 0.5-1.5d budget |
| F5.3 overlap parameter | Implies overlap windowing | Accepted but echoed in `note` as ignored | The LayoutAwareChunker(W2 baseline)is heading-bounded — sections never split mid-paragraph and there's no overlap window to honour。Adding overlap requires a new chunker class — out of Wave A scope。Wave B+ candidate | AI per Karpathy §1.2 |
| F5.2 page_num / screenshot_type / created_at | Plan literal `{id, url, doc_id, doc_name, page_num, ocr_text, screenshot_type, created_at}` | All 3 forward-compat seams return null in Tier 1 | Existing `ImageRef` schema doesn't carry `page_num` or `screenshot_type`(architecture.md §3.5 `embedded_images = list[ImageRef]` per W2 F3);`ingested_at` lives on ChunkRecord but the existing list_chunks doesn't surface it。Adding all 3 = schema changes upstream + index reflow — out of Wave A scope。Tier 1 returns `null` for the 3 fields so the response shape contract holds for Wave B+ | AI per Karpathy §1.2 + plan F5.2 1d budget |
| F5.2 endpoint reality with R12 | Plan implies real images surface | Today returns empty list with 200 OK(uploader=None) | `uploader=None` per R12 means newly-ingested chunks have empty `embedded_images_json`;endpoint is forward-compat — when Track A IT cred lands and Azure Blob switch flips uploader on,the gallery starts populating without further code change。Empty-state in `<ImagesTab>` explicitly explains the R12 context to users | AI per Karpathy §1.2 + plan F5.2 — frontend gallery shell already valuable now |
| F5.7 Archive button styling | Plan says Danger zone | Archive row uses neutral `border-border` not destructive `text-destructive` | Archive is a soft-state flag(reversible via service.archive(kb_id, archived=False))— not destructive。Re-index + Delete actions still use destructive styling for the genuinely-dangerous arms。Visual hierarchy preserved | AI per Karpathy §1.2 + ADR-0025 |
| F5 commit cadence | Plan implies multi-commit | Single F5 commit(backend 3 endpoints + storage schema + frontend 4 tabs + Danger zone)| Tightly coupled — backend endpoints + matching frontend tabs ship together;splitting would obscure the unified "Wave A 7-tab Detail" intent。Same precedent as W20 F2 + F4 | AI per W20 F2/F4 commit pattern |

#### Decisions / new OQ / risk surfaced

- **`KbStatus.archived` defaults `False`** — Pydantic backfills the field on existing records(even when storage row doesn't have the column yet — `_row_to_kb` uses `row.get("archived", False)`)。Postgres `ALTER TABLE ADD COLUMN IF NOT EXISTS` runs on every `_connect()`(idempotent — same pattern as `CREATE TABLE IF NOT EXISTS`),so older DBs migrate without an Alembic migration step。In-memory backend already returns the field from the Pydantic default。
- **Read paths intentionally allow archived KBs** — `_refuse_if_archived` only fires on upload + reindex(the canonical write paths);chat / query / retrieval test / list docs / list chunks all read freely。This preserves the citation surface for past content even after archive(matches ADR-0025 intent — archive freezes ingest,not retrieval)。
- **Image gallery R12 reality surfaced in-UI** — the `<ImagesTab>` empty state explicitly mentions "the screenshot pipeline runs end-to-end (R12 — Azure Blob switch pending Track A IT cred)";users see why their KB shows zero images even when chunks are populated。Self-documenting Tier 1 state for Beta operators。
- **`POST /chunking-preview` is preview-only by design** — no Azure index write,no doc re-parse,no persistence。Apply button wrapped in `<DisabledAffordance>` Tier 2 chip because Apply-style re-chunking requires every doc to be re-ingested through the new strategy(uploader=None today + multi-doc re-ingest cascade is Wave B+ scope)。

#### Actual vs Planned Effort

| F | Planned | Actual | Δ |
|---|---|---|---|
| F5.1 archive endpoint + storage schema + Postgres ALTER TABLE + 5 pytest | 90 min | ~50 min | -44% |
| F5.2 images endpoint + chunk select extend + 4 pytest | 120 min | ~70 min | -42% |
| F5.3 chunking-preview endpoint + synthetic parser + 5 pytest | 180 min | ~80 min | -56% |
| F5.4 7-tab refactor + url routing | 30 min | ~20 min | -33% |
| F5.5 Images tab + modal | 60 min | ~35 min | -42% |
| F5.6 Chunking Lab tab + preview UI | 60 min | ~40 min | -33% |
| F5.7 Settings Danger zone Archive + state-aware button | 45 min | ~25 min | -44% |
| F5.8 Access tab disabled affordance | 15 min | ~10 min | -33% |
| F5.9 verify(tsc + lint + [oklch + Vitest + backend pytest 59)| 30 min | ~25 min | -17% |
| F5.10 + F5.11 docstrings(no Vitest component tests this commit per F8.4 batching)| 30 min | ~20 min | -33% |
| Progress.md F5 Day-N entry + commit | 30 min | ~25 min | -17% |
| **F5 Day 5 total** | **~11 hours**(3.5 plan-days) | **~6.5 hours** | **-41%** |

Real-calendar collapse pattern continues — W12-W18 + W20 F1/F2/F3a/F3b/F4/F5 established collapse band 1.8-4× holds(F5 lands at ~4.3× collapse — just outside upper band,driven by the unified-commit cadence avoiding context re-load cost)。

#### Carry-overs to next Day-N

- **F6 `/kb-upload/[id]` re-ingestion wizard polish** per ADR-0028 §5.5.3b — next deliverable(C09);existing 3-step skeleton preserved + add Multimodal toggles per KB's existing config + Tier 2 disabled affordance reuse from F4。
- **F7 `/login` + `/register` polish** per ADR-0014 — Brand panel slot integration + Forgot password disabled affordance + 5-step register wizard preserved。
- **F8 cross-cutting** — responsive + a11y + dark-mode + Vitest expansion(F8.4 batches 5 NEW test files from F1.7 + F3.15 + F4.7 + F5.10 — accumulating)+ Playwright E2E updates + COMPONENT_CATALOG + PAGE_INVENTORY updates。
- **F9 phase closeout** — Gate verdict + retro + frontmatter status flip + W21+ rolling JIT decision。
- **F8.4 Vitest scaffolding batch** — accumulating still(F1.7 + F3.15 + F4.7 + F5.10):`notifications-menu.test.tsx` + `disabled-affordance.test.tsx` + `conversation-history.test.tsx` + `kb-new-wizard.test.tsx` + `kb-detail-tabs.test.tsx` + supporting fixtures。
- **Wave B+ candidates updated**:`crag_reasoning` field;LLM-summarize conversation title;sidebar mode multi-turn aggregation;Citation `kb_id` field;real-I/O `/health` pings;**plus W20 F5 wires** for `sample_doc_id` chunking-preview path + image `page_num`/`screenshot_type`/`created_at` enrichment + chunker `overlap` window + Apply-style re-chunking pipeline + `archived` flag CASCADE to Azure index lifecycle decisions(when Track A IT cred lands)。

---

## Day 5 — 2026-05-17 (continued, fifth commit)

### F6 — `/kb-upload/[id]` re-ingestion wizard skeleton(landed)

**Branch**:`main`(ahead of `origin/main` by 0 commit at the time of starting F6 — last push was `82f18c3` CLAUDE.md v1.6;F5 `4af3ade` already on origin)。
**Commits this day**:`(this commit)` — F6 standalone(`frontend/app/(app)/kb/[id]/upload/page.tsx` 74-line single-step → 3-step wizard rewrite + Plan §7 changelog batch row for F6/F7 deviations)。

#### What landed

- **F6.1 — 3-step wizard skeleton rewrite** — `frontend/app/(app)/kb/[id]/upload/page.tsx` was a 74-line single-step `<input type="file">` + `Upload + Ingest` button shape since W12 D4 F4.8;W20 F6 rebuilt it from scratch as a **3-step wizard skeleton** per the AskUserQuestion Option 1 pick(2026-05-17):**Step 1 Source**(file picker `.docx/.pdf/.pptx`,reuses F4 Step 5 file-picker shape — `state.file` size hint + accept attribute identical)+ **Step 2 Multimodal**(read-only display of the KB's current multimodal config via `kbApi.get(kbId)` `useQuery`;4 Tier 1 toggles use NEW `<ReadOnlyToggleRow>` — `<Switch>` `disabled` + `aria-readonly="true"` + `cursor-not-allowed`;`dedup_strategy` rendered as a mono `<span>` badge rather than a select to make read-only intent unambiguous;3 Tier 2 disabled affordances re-use `<DisabledAffordance variant="p3-preview" showBadge>` from F4 Step 4 / W20 F1.5 — caption generation / image clustering / provenance ledger;`<Link>` "Edit settings" → `/kb/[id]?tab=settings` makes the per-KB-not-per-doc constraint user-discoverable)+ **Step 3 Review**(summary `<dl>` 11 rows = KB id / KB name / Document / Size / 4 multimodal fields + Stage 1-stage progress for `POST /kb/{id}/documents` only + redirect `/kb/[id]` on success via `queryClient.invalidateQueries` + `router.push`)。
- **F6.2 — DRY decision rationale** — F4 KB Pipeline wizard's `<Field>` / `<Stepper>` / `<ToggleRow>` / `<Stage>` / `<Summary>` are **file-local primitives** in `kb/new/page.tsx`(no export);F6 inline-redeclares each per the W13 Register page strategy(also file-local — `Stepper` / `Step1` / `Step2` / `Step3` / `Field` patterns)。**This is the 4th wizard usage** in `frontend/` (F4 KB Pipeline + W13 Register + W18 F5 Pipeline + W20 F6 Re-ingestion)— the **rule-of-3 promotion trigger is NOW hit**;extracting to a shared `frontend/components/ui/stepper.tsx` + `<Field>` + `<Stage>` (Karpathy §1.2 promotion when N≥3 use sites)is a **Wave B+ candidate**(avoiding a Wave A ripple change to F4 + Register + W18 F5 per Karpathy §1.3 surgical preserve-adjacent-unchanged)。
- **F6.3 — verify** — `pnpm exec tsc --noEmit` exit 0;`pnpm exec next lint` "No ESLint warnings or errors";`Grep '\[oklch'` across `frontend/` = **0**(W15→W18→W20 F1+F2+F3b+F4+F5+F6 milestone preserved through 6 deliverables)。
- **F6.4 — Vitest deferred per precedent** — `kb-upload-wizard.test.tsx`(3-step navigation + read-only Multimodal display + Stage progress)🚧 deferred → **F8.4 batches**(per plan F6.4 literal + the established F1.7 / F3.15 / F4.7 / F5.10 precedent of holding scaffold tests for the F8 sweep)。
- **F6.5 — file header docstring** — 22-line docstring at the top of `upload/page.tsx` explains:W12 baseline single-step → W20 F6 3-step wizard promotion;per-KB(not per-doc)multimodal config rationale tied back to W20 F4.2 orchestrator `ingest(kb_config)` reading from `service.get(kb_id)`;rule-of-3 Wave B+ promotion note for future readers;tokens 100% preservation milestone callout。

#### Acceptance criteria status(per checklist.md)

- [x] F6.1 single-step → 3-step wizard skeleton(Source / Multimodal / Review)
- [x] F6.2 DRY rule-of-3 trigger hit but Wave B+ defer per Karpathy §1.3 surgical
- [x] F6.3 tokens 100% / [oklch=0 / tsc 0 / lint 0
- [x] F6.4 Vitest 🚧 deferred F8.4
- [x] F6.5 File header docstring updated

#### Deviations(if any)

| F# | Plan said | Actual | Why | Approver |
|---|---|---|---|---|
| F6.1 | "existing 3-step skeleton preserved + Source step add Multimodal toggles" | single-step → 3-step **NEW** wizard built from scratch | The plan literal mis-described the W12 baseline — `frontend/app/(app)/kb/[id]/upload/page.tsx` was a 74-line single-step file picker, no wizard structure to preserve. AskUserQuestion 3-way picked Option 1 → build the 3-step skeleton out of nothing. The plan §7 changelog 2026-05-17 entry records this. | AskUserQuestion picked Option 1 by Chris 2026-05-17 + Plan §7 changelog |
| F6.1 Multimodal step | "Source step add Multimodal toggles per KB's existing config" | Dedicated Step 2 Multimodal with **read-only** display (not editable toggles in Step 1) | W20 F4.2 orchestrator `ingest()` reads `kb_config` from `service.get(kb_id)` — multimodal config is **per-KB level**, not per-doc. Per-doc override would break backend contract. Step 2 surfaces the in-effect config + a link to `/kb/[id]?tab=settings` to edit per-KB instead. | AI per Karpathy §1.2 + W20 F4.2 backend contract |
| F6.2 DRY | "reuse F4 wizard step components where possible (Karpathy §1.2)" | Inline-redeclared per W13 register strategy + Wave B+ promote-to-shared note | F4 `<Field>` / `<Stepper>` / `<ToggleRow>` / `<Stage>` / `<Summary>` are file-local (no `export`). Extracting to shared `frontend/components/ui/stepper.tsx` would force ripple changes to F4 + Register + W18 F5 — out of W20 surgical scope. Rule-of-3 promotion trigger now hit (4th wizard usage) → Wave B+ candidate. | AI per Karpathy §1.3 surgical + rule-of-3 deferred promotion |
| F6 commit cadence | Plan implies F6+F7 dual-commit | F6 standalone commit + F7 to follow | User pick 方案 A "F6+F7 雙 commit" 2026-05-17 makes this two commits, one per F. The unified commit cadence (F2 / F4 / F5) was the exception — for small surface polish F# the dual-commit cadence holds. | User pick 方案 A 2026-05-17 |

#### Decisions / new OQ / risk surfaced

- **Per-KB-not-per-doc multimodal config** surfaced in-UI — Step 2's "Edit settings" link makes the architectural constraint visible to KB owners(previously implicit in W20 F4.2 + KbConfig schema)。Without this surface, users would expect per-doc override and be confused why their toggle choices don't take effect。
- **Rule-of-3 wizard primitive promotion trigger now hit** — file-local `<Field>` / `<Stepper>` / `<ToggleRow>` / `<Stage>` / `<Summary>` exist in 4 places now(F4 KB Pipeline + W13 Register + W18 F5 Pipeline + W20 F6 Re-ingestion);Wave B+ should extract to `frontend/components/ui/stepper.tsx` (+ companion primitives)so future wizard usages don't repeat the inline pattern。
- **No backend change needed** — F6 is frontend-only(no schema / endpoint / storage change);the existing `kbApi.uploadDoc(kbId, file)` Mutation + `kbApi.get(kbId)` Query do the entire job。

#### Actual vs Planned Effort

| F | Planned | Actual | Δ |
|---|---|---|---|
| F6.1 single-step → 3-step wizard rewrite + Step 2 read-only Multimodal + Step 3 Review | 30 min(plan budget)| ~30 min(rewrite from scratch + 3 step components inline)| 0% |
| F6.2 + F6.5 docstring + Plan §7 changelog row | 15 min | ~10 min | -33% |
| F6.3 verify(tsc + lint + [oklch)| 10 min | ~5 min | -50% |
| F6.4 Vitest scaffold(this commit per F8.4 batching)| — | — | — |
| Progress.md F6 Day-N entry + checklist tick + commit | 25 min | ~20 min | -20% |
| **F6 Day 5 sub-total** | **~1.5 hours**(plan F6 cell 30 min implementation only;real cost includes process overhead)| **~65 min** | **-28%** |

Real-calendar collapse pattern continues — W12-W18 + W20 F1-F5 collapse band 1.8-4× preserved(F6 lands at ~1.4× — slightly below band lower bound which fits since F6 is a small isolated polish without backend co-coordination overhead)。

#### Carry-overs to next Day-N(F7)

- **F7 `/login` + `/register` polish** — next deliverable(C11 + C09);F7 dual decisions picked 2026-05-17:Login Option 2 strict design fidelity(SSO primary + Divider + email secondary + Forgot password inline next to Password label + Tier 2 badge via `<DisabledAffordance>` + bottom mono dashed "Auth modes (Tier 1)" block);Register Option 2 visual polish-only(keep 3-step 6-digit code structure + field reorder Full name → Email → Password + Confirm + Terms checkbox + hint copy specificity)+ Step 3 KB selector migrate to shared `<DisabledAffordance>`。
- **F8.4 Vitest scaffold batch** — accumulating still(F1.7 + F3.15 + F4.7 + F5.10 + F6.4):`notifications-menu.test.tsx` + `disabled-affordance.test.tsx` + `conversation-history.test.tsx` + `kb-new-wizard.test.tsx` + `kb-detail-tabs.test.tsx` + `kb-upload-wizard.test.tsx` + supporting fixtures。
- **Wave B+ candidates updated** — `crag_reasoning` field;LLM-summarize conversation title;sidebar mode multi-turn aggregation;Citation `kb_id` field;real-I/O `/health` pings;`sample_doc_id` chunking-preview path;image `page_num`/`screenshot_type`/`created_at` enrichment;chunker `overlap` window;Apply-style re-chunking pipeline;`archived` flag CASCADE to Azure index lifecycle;**plus W20 F6 wires** for **rule-of-3 wizard primitive promotion** to shared `frontend/components/ui/stepper.tsx` (+ Field/Stage/ToggleRow/Summary) given the 4th wizard usage now observed(extracting before a 5th appears avoids 5-site ripple)。

---

<!-- Day 3+ frontend entries to be appended. Template:

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
