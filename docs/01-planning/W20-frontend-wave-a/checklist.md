---
phase: W20-frontend-wave-a
plan_ref: ./plan.md
status: active
last_updated: 2026-05-16
---

# Phase W20 — Checklist

> Atomic checkbox(每 item ≤ 0.5–2 hour effort)。Status:`active` from kickoff 2026-05-16(Chris directive + 6 ADRs Accepted + AskUserQuestion A1 pick = the authorization)。
> 每 item done 後 `[ ]→[x]` + commit ref;延後項標 🚧 + reason(per CLAUDE.md §10 sacred rule — 唔可以刪未勾選 item)。
> Deliverable ↔ ADR mapping:F0=ADR Status flip + spec amend / F1=ADR-0032 absorb / F2=ADR-0030 absorb / F3=ADR-0031 Option B / F4=ADR-0028 / F5=ADR-0025 minus Access / F6=ADR-0028 §5.5.3b / F7=ADR-0014 polish / F8=cross-cutting / F9=closeout。

## F0 — Kickoff cascade(ADR-0025/0028/0031 Status flip + spec amendment — landed at kickoff)

- [ ] F0.1 `docs/adr/0025-kb-detail-8-tabs.md` Status **Proposed → Accepted**(consensus pick — 7-tab `-Access` Wave A scope note added;Implementation Deliverables row — Wave A ships 7-tab,Wave C1 activates Access tab)
- [ ] F0.2 `docs/adr/0028-kb-new-5-step-wizard.md` Status **Proposed → Accepted**(consensus pick — Multimodal Tier 1 active fields + Tier 2 disabled affordance scope confirmed)
- [ ] F0.3 `docs/adr/0031-chat-advanced-surfaces.md` Status **Proposed → Accepted**(Option B server-side pick — Wave A +3 backend days impact noted;6 NEW `/conversations` CRUD endpoints + Postgres `conversations` + `messages` tables per ADR-0023 backing pattern)
- [ ] F0.4 `docs/adr/README.md` — rows for 0025/0028/0031 Status「Proposed」→「Accepted」+ context cells updated(W19 F6 Chris approval cascade outcome)+ footnote「Proposed 2026-05-16」→「Accepted 2026-05-16」
- [ ] F0.5 `docs/architecture.md` — inline-tagged §5.x amendments(doc version held per W18 + §3.4/§3.7 precedent):**§5.2 Chat** ADR-0031 server-side Conversation History paragraph + C10 §7 Tier 2→Tier 1 note;**§5.3 Dashboard** ADR-0030 absorbed polish paragraph;**§5.4 KB List** grid+table+filter paragraph;**§5.5 KB Detail** 7-tab refactor per ADR-0025 (-Access) paragraph + Access tab Tier 1.5 deferral note;**§5.5.5 NEW** `/kb/new` 5-step wizard per ADR-0028 paragraph;**§5.10+§5.11 Login+Register** Brand panel + Forgot password disabled affordance paragraph
- [ ] F0.6 `docs/01-planning/W20-frontend-wave-a/{plan,checklist,progress}.md` created `status: active`(this commit)
- [ ] F0.7 `docs/12-ai-assistant/01-prompts/01-session-start.md` §10 W20 row added(`active`)+ §12 milestones row added(`active`)+ Update history row + Last-Updated

## F1 — `<AppShell>` topbar + sidebar polish per ADR-0032 absorbed scope(C09)

- [ ] F1.1 NEW `frontend/components/nav/notifications-menu.tsx` — `<DropdownMenu>` triggered by `<Bell>` icon;`useQuery(['notifications'])` off `GET /notifications` if backend lands(W19 F2 item 21)else static mock list;counter badge;"Mark all read" + "See all →" CTA → `/notifications`(disabled affordance if backend absent);file header docstring
- [ ] F1.2 Workspace switcher **disabled affordance** — `<DisabledAffordance>` chip in top bar showing current workspace name + `<DropdownMenuTrigger disabled>` + tooltip "Multi-workspace support — Tier 2(architecture.md §11)";fixes W19 F1 §2.3 Tier 2 leak
- [ ] F1.3 Sidebar Tools sub-section — 5 modules grouped into 2 sections:**Main**(Dashboard / Chat / Knowledge Bases)+ **Tools**(Eval Console / Traces);labelled section headers via `<NavGroupHeader>` sub-component
- [ ] F1.4 Sidebar Labs section **hidden by default** per W19 F5.4 Option C;prototype-only `/labs/*` routes don't ship(none created in `frontend/`);if future Tier 2 sprint enables Labs,section header + items reactivate via env flag
- [ ] F1.5 NEW `frontend/components/ui/disabled-affordance.tsx` — shared `<DisabledAffordance>` component per W19 F5 spec:wraps children with `aria-disabled` + `title` + `(Tier 2)` badge;props for `tier` + `reason` + `tooltipText`;reused across F1.2 + F4 + F5 + F7;file header docstring
- [ ] F1.6 100% `tokens.ts`;`Grep '\[oklch'` across `frontend/` = **0**(W18 milestone preserved);`pnpm exec tsc --noEmit` exit 0;`pnpm exec next lint` "No ESLint warnings or errors"
- [ ] F1.7 File header docstrings(NEW files)+ Vitest test scaffolding for `<DisabledAffordance>` + `<NotificationsMenu>`(F8 carries full pass)

## F2 — `/dashboard` real cards per ADR-0030 absorbed scope(C09 + C07 + C02 + C06)

- [ ] F2.1 Backend `backend/api/routes/health.py` — extend `GET /health` payload from `{status: "ok"}` to `{status, components: {azure_search, azure_openai, cohere, langfuse, postgres}}` with per-component status + latency_ms;per W19 F2 §3.1 item 1;~0.5-1d C07;mypy strict
- [ ] F2.2 Backend — pytest test for `/health` per-component payload(skeleton fail / partial fail / all green)
- [ ] F2.3 Frontend `frontend/app/(app)/dashboard/page.tsx` rewrite — replaces W18 F4 placeholder with 5 cards + 4-stat strip:(a) Top stat strip 4 cards / (b) Knowledge bases / (c) Recent queries CTA / (d) Latest evaluation CTA / (e) System health per-component dots / (f) Quick actions 4 buttons
- [ ] F2.4 Loading skeletons + error banners per card(reuse W17 F4.1 + W18 F4 pattern);empty states first-class
- [ ] F2.5 Tokens 100% `tokens.ts`;`tsc` + `lint` clean;`[oklch`=0 preserved
- [ ] F2.6 Vitest test extension — `dashboard.test.tsx` cover 4-stat strip + per-component health dot count(W18 baseline 2 tests → ~5 tests)
- [ ] F2.7 File header docstring updated

## F3 — `/chat` advanced surfaces per ADR-0031 Option B server-side Conversation History(C10 + C08)

- [ ] F3.1 NEW backend `backend/api/schemas/conversation.py` — `Conversation` + `Message` + `ConversationCreate` + `ConversationUpdate` + `MessageCreate` Pydantic v2 schemas;mypy strict
- [ ] F3.2 NEW backend `backend/persistence/postgres_conversations.py` — `PostgresConversationStore` per ADR-0023 backing pattern:`conversations` table(id PK / user_id FK / title / kb_id FK nullable / created_at / updated_at)+ `messages` table(id PK / conversation_id FK CASCADE / role / content / citations JSONB / created_at)+ `make_conversation_store()` factory(Postgres if `DATABASE_URL` set,else `InMemoryConversationStore` fallback per W17 F1);Alembic migration or raw SQL DDL alongside per W17 F1 precedent
- [ ] F3.3 NEW backend `backend/api/routes/conversations.py` — 6 endpoints:`POST /conversations` + `GET /conversations` (paginated) + `GET /conversations/{id}` + `PATCH /conversations/{id}` + `DELETE /conversations/{id}` + `POST /conversations/{id}/messages`;all gated by `Depends(get_current_user)` per W17 F2 cookie/Bearer transport
- [ ] F3.4 Backend pytest `tests/api/test_conversations_route.py` — coverage ≥ 80% per CLAUDE.md §3.1 H6;happy path + auth-required + not-found + cross-user isolation tests
- [ ] F3.5 Frontend `frontend/app/(app)/chat/page.tsx` — Conversation History sidebar(left collapsible pane via `<AppShell>` focus-mode toggle pattern);`useQuery(['conversations'])`;"New chat" button → `POST /conversations`;list-item click loads via `GET /conversations/{id}`;title auto-gen first-50-char slice;rename(double-click)+ delete confirmation modal
- [ ] F3.6 Frontend — existing SSE `/query` streaming logic preserved;message persistence layer added(`POST /conversations/{id}/messages` after assistant turn completes)
- [ ] F3.7 Frontend 3 citation placement modes — `inline` / `footnote` / `sidebar` toggle in `<ChatHeader>` + persisted to `localStorage['ekp-citation-mode']`(W18 sidebar focus-mode pattern);3 separate render branches in the message component
- [ ] F3.8 Frontend `<InlineImageCard>` — renders inline within assistant message when `citation.image_url` exists(consume W17 image schema)
- [ ] F3.9 Frontend `<ImageGallery>` — aggregates all message images at end as grid;click → modal preview with OCR text overlay
- [ ] F3.10 Frontend `<CitationPill>` hover popover — citation pill `[1]` hover shows popover with chunk preview + KB doc link
- [ ] F3.11 Frontend `<FeedbackBar>` comment field — extend W17 thumbs-up/down with optional text comment + tag dropdown(`['inaccurate', 'incomplete', 'off-topic', 'other']`)+ `POST /feedback` writes per existing W8 endpoint
- [ ] F3.12 Frontend CRAG strip indicator — horizontal strip above assistant message when `query.crag_triggered === true` showing "CRAG triggered — N iterations" + tooltip with `query.crag_reasoning`
- [ ] F3.13 Backend — verify `QueryResponse` schema includes `crag_triggered: bool` + `crag_iterations: int`(W19 F2 item 5);add if missing;~0.2d C05
- [ ] F3.14 Tokens 100% `tokens.ts`;`[oklch`=0 preserved;`tsc` + `lint` clean
- [ ] F3.15 Vitest tests — `conversation-history.test.tsx`(sidebar render + new-chat click + list-item click)+ citation mode toggle render + InlineImageCard / FeedbackBar comment / CRAG strip(F8.4 batches)
- [ ] F3.16 File header docstrings(NEW + rewritten files)

## F4 — `/kb` list polish + `/kb/new` 5-step wizard per ADR-0028(C09 + C02 + C01)

- [ ] F4.1 Backend `backend/api/schemas/kb.py` extend `KbConfig` — Tier 1 active fields:`extract_embedded_images: bool = False` + `slide_screenshots: bool = True` + `dedup_strategy: Literal['sha256', 'none'] = 'sha256'` + `return_images_in_chat: bool = False`;mypy strict
- [ ] F4.2 Backend `backend/ingestion/orchestrator.py` — consume new KbConfig fields(per W19 F2 §3.1 item 2;~0.5d C01 + C02);extract_embedded_images branch + slide_screenshots branch + dedup branch + return_images flag downstream;pytest fixture updates
- [ ] F4.3 Frontend `frontend/app/(app)/kb/page.tsx` — grid view(default,preserved)+ table view toggle + filter bar(search by name + status dropdown + sort dropdown)+ view persisted to `localStorage['ekp-kb-list-view']`
- [ ] F4.4 Frontend `frontend/app/(app)/kb/new/page.tsx` rewrite — 5-step wizard:Step 1 Source(Name + Description + Tags)/ Step 2 Parsing(Docling profile picker — disabled affordances if not impl)/ Step 3 Chunking(strategy + size + overlap)/ Step 4 Multimodal(Tier 1 active toggles + Tier 2 `<DisabledAffordance>` for caption/clustering/blockchain)/ Step 5 Review(summary table + POST /kb submit + redirect `/kb/[id]`)
- [ ] F4.5 Frontend — Stepper navigation(back / next / cancel)reuse W3 Pipeline wizard pattern;each step `<Validate>` before "Next"
- [ ] F4.6 Tokens 100% `tokens.ts`;`[oklch`=0 preserved;`tsc` + `lint` clean
- [ ] F4.7 Vitest tests — `kb-new-wizard.test.tsx`(5-step navigation + Tier 2 disabled affordance render)+ list view toggle test
- [ ] F4.8 File header docstrings(rewritten files)

## F5 — `/kb/[id]` 7-tab Detail refactor per ADR-0025 minus Access(C09 + C01 + C02 + C03)

- [ ] F5.1 Backend `POST /kb/{kb_id}/archive` endpoint per W19 F2 §3.1 item 6;~0.3d C02;sets `kb.status = 'archived'`;guards user re-ingestion;pytest happy + auth + already-archived tests
- [ ] F5.2 Backend `GET /kb/{kb_id}/images` enriched per W19 F2 §3.1 item 7;~1d C01 + C02 + C03;paginated image list with `{id, url, doc_id, doc_name, page_num, ocr_text, screenshot_type, created_at}`;reuse W2 F3 screenshot pipeline metadata;pytest coverage
- [ ] F5.3 Backend `POST /chunking-preview` endpoint per W19 F2 §3.1 item 8;~1.5d C01 + C03;takes `{kb_id, sample_doc_id?, strategy, chunk_size, overlap}` + returns N preview chunks(no persist);reuse `layout_aware_chunker.py` from W2 F2;pytest coverage
- [ ] F5.4 Frontend `frontend/app/(app)/kb/[id]/page.tsx` rewrite to 7-tab via shadcn `<Tabs>` — Tab 1 Documents(preserved W17 F4.1 + CH-001)+ Tab 2 Chunks(preserved)+ Tab 3 Images NEW + Tab 4 Chunking Lab NEW + Tab 5 Pipeline(preserved W3)+ Tab 6 Retrieval Testing(preserved W18 ADR-0021)+ Tab 7 Settings(preserved + Danger zone archive)
- [ ] F5.5 Frontend Tab 3 Images — NEW component `kb-images-tab.tsx` — consume `GET /kb/{kb_id}/images`;ImageGallery filter(by doc_id / screenshot_type)+ click-to-preview modal + OCR text overlay
- [ ] F5.6 Frontend Tab 4 Chunking Lab — NEW component `kb-chunking-lab-tab.tsx` — consume `POST /chunking-preview`;controls(strategy + size + overlap)+ "Preview" button + live chunk preview list + "Apply" disabled affordance(Tier 2 "re-chunking pending")
- [ ] F5.7 Frontend Tab 7 Settings — extend existing with Danger zone:`POST /kb/{kb_id}/archive` confirmation modal + warning text;reuses pattern from CH-001 delete
- [ ] F5.8 Frontend **Access tab disabled affordance** — 8th tab visible but `<TabsTrigger disabled>` + `<DisabledAffordance tier={1.5} reason="RBAC pending Wave C1 per ADR-0027 Option A backend">` wrapper;clicking shows tooltip
- [ ] F5.9 Tokens 100% `tokens.ts`;`[oklch`=0 preserved;`tsc` + `lint` clean
- [ ] F5.10 Vitest test `kb-detail-tabs.test.tsx` — 7-tab nav + Access disabled assertion + Images grid render + Chunking Lab preview render
- [ ] F5.11 File header docstrings(rewritten + NEW files)

## F6 — `/kb-upload/[id]` re-ingestion wizard polish per ADR-0028 §5.5.3b(C09)

- [ ] F6.1 Frontend `frontend/app/(app)/kb/[id]/upload/page.tsx` polish — existing 3-step skeleton preserved + Source step add Multimodal toggles per KB's existing config + Tier 2 `<DisabledAffordance>` reuse from F4
- [ ] F6.2 DRY — reuse F4 wizard step components where possible(Karpathy §1.2)
- [ ] F6.3 Tokens 100% `tokens.ts`;`[oklch`=0 preserved;`tsc` + `lint` clean
- [ ] F6.4 Vitest test — 3-step navigation + Multimodal toggle render
- [ ] F6.5 File header docstring updated

## F7 — `/login` + `/register` polish per ADR-0014(C11 + C09)

- [ ] F7.1 `frontend/app/login/page.tsx` polish — Brand panel slot integration(reuse `brand-panel.tsx` from W13)+ Forgot password link **disabled affordance**(`<DisabledAffordance tier={2}>` chip + tooltip "Coming in a later tier");redirect target unchanged(`/dashboard` per W18 F7)
- [ ] F7.2 `frontend/app/register/page.tsx` polish — same Brand panel slot pattern + 5-step wizard preserved(W13);Step 3 "Welcome" CTA preserved → `/dashboard`(W18 F7);no other functional change
- [ ] F7.3 Tokens 100% `tokens.ts`;`[oklch`=0 preserved;`tsc` + `lint` clean
- [ ] F7.4 Vitest test — Forgot password disabled affordance render + Brand panel slot present
- [ ] F7.5 File header docstrings updated

## F8 — Cross-cutting:responsive + a11y + dark-mode + tests + COMPONENT_CATALOG + PAGE_INVENTORY

- [ ] F8.1 Responsive pass on new surfaces — `<NotificationsMenu>` + `<DisabledAffordance>` chips + `/dashboard` 4-stat strip + `/chat` Conversation History sidebar + `/kb/new` 5-step wizard + `/kb/[id]` 7-tab nav at `sm` / `md` / `lg` / `xl`;multi-viewport browser smoke = user pre-Beta walkthrough(R8 caveat shape per W18)
- [ ] F8.2 a11y pass on new surfaces only(full screen-reader audit Tier 2 / CO_W15_F3_aria_full_audit):`<NotificationsMenu>` Radix `<DropdownMenu>` role/aria-haspopup verified + `<DisabledAffordance>` aria-disabled+title+badge + `/chat` Conversation History `<nav aria-label>` + each item `role="link"` + `/kb/new` step `role="form"` + step indicator `aria-current="step"` + `/kb/[id]` Radix `<TabsList>`/`<TabsTrigger>` role + Access disabled `aria-disabled`
- [ ] F8.3 Dark-mode re-check — `Grep '\[oklch'` across `frontend/` = **0**(W15/W18 milestone preserved through F1-F7);next-themes mechanism unchanged
- [ ] F8.4 Vitest expansion — W18 baseline 4 files/13 tests → W20 target 6-8 files/20+ tests:NEW `notifications-menu.test.tsx` + NEW `disabled-affordance.test.tsx` + NEW `conversation-history.test.tsx` + NEW `kb-new-wizard.test.tsx` + NEW `kb-detail-tabs.test.tsx` + existing `dashboard.test.tsx` extended;`pnpm test:unit` → 20+/20+ pass
- [ ] F8.5 Playwright E2E updates — `app-shell-path.spec.ts`(NotificationsMenu + workspace switcher disabled chip present)+ `golden-path.spec.ts`(extend chat flow:create conv → send msg → reload page → conv still shown — server-side persistence test)+ `visual-baseline.spec.ts`(re-baseline `/dashboard` + `/chat` + NEW snapshots `/kb/new` step 1 + `/kb/[id]` Images tab + Chunking Lab tab);`tsc --noEmit` compile-check;run via `PW_CHANNEL=chrome pnpm test:e2e`(ADR-0017 Plan B)
- [ ] F8.6 `docs/02-architecture/COMPONENT_CATALOG.md` — C01/C02/C03/C05/C07/C08/C09/C10 status notes appended with W20 Wave A amendment(per ADR-0025/0028/0031 + ADR-0030/0032 absorbed scope)
- [ ] F8.7 `references/design-mockups/PAGE_INVENTORY.md` — Cn mapping rows for 7 W20-implemented routes update from "prototype" to "implemented W20"

## F9 — Phase closeout + W21+ rolling-JIT trigger

- [ ] F9.1 W20 phase Gate verdict landed(PASS / PARTIAL PASS / FAIL with explicit rationale per W18 pattern)
- [ ] F9.2 W20 `progress.md` Retro — 7 sections written(What worked / What didn't & friction / Surprises / Decisions / Carry-overs to W21+ / Time tracking / Spec-ref alignment)
- [ ] F9.3 ADR-0025 + ADR-0028 + ADR-0031 status verified `Accepted`(F0 flip;verify-no-op at closeout)+ Implementation Deliverables checkboxes ticked(7-tab `-Access` shipped Wave A per ADR-0025;5-step wizard per ADR-0028;Option B server-side Conversation History per ADR-0031)
- [ ] F9.4 W20 `plan.md` + `checklist.md` + `progress.md` frontmatter `status: active` → `closed`
- [ ] F9.5 W21+ phase folder **NOT pre-created**(rolling-JIT per CLAUDE.md §10 R1)— kickoff candidates noted in `progress.md` Day-N retro section("W21+ — NOT pre-created":W21-frontend-wave-b per W19 F4 §2;OR W22-frontend-wave-c1 per F4 §3.6 split decision;OR W16 F1-F4 if Track A IT cred lands)
- [ ] F9.6 `session-start.md` hygiene catch-up — §3 C01/C02/C03/C05/C07/C08/C09/C10 status(W20 Wave A amendments)+ §10 W20 row(closed, Gate verdict)+ W21+ not-pre-created note + §11 carry-overs(W20-closed items + any new 🚧 deferrals)+ §12 milestones row + Last-Updated + Update-history;`COMPONENT_CATALOG.md` + `PAGE_INVENTORY.md` already touched in F8.6 + F8.7
- [ ] F9.7 New OQ surfaced(if any) → sync `decision-form.md` per R4;ADR-0030 + ADR-0032 SKIPPED footnote preserved per W19 F6 closeout

---

## Cross-Cutting(must verify each commit + at closeout)

- [ ] CC1 Each commit references `progress.md` Day-N entry(R2)
- [ ] CC2 Component tag in commit message — F1 = C09 / F2 = C09+C07+C02+C06 / F3 = C10+C08+C02 / F4 = C09+C02+C01 / F5 = C09+C01+C02+C03 / F6 = C09 / F7 = C11+C09 / F8 = cross-cutting / F9 = governance
- [ ] CC3 OQ status sync to `decision-form.md`(R4)— **no-op expected**:Q6 / Q15 / Q11 all stay Open(W20 doesn't resolve any);ADR-0017 occurrences if any new R8 hit → log
- [ ] CC4 Risk register — no new W20 risk expected;the `npx playwright install chromium` block stays under ADR-0017 Plan B realised(use `PW_CHANNEL=chrome`)
- [ ] CC5 CLAUDE.md §5.1 H1 check — Wave A authorized by ADR-0025/0028/0031 Accepted(W19 F6);no other architectural change;F1-F8 implement the amended §5.2 + §5.3 + §5.4-§5.5 + §5.5.5 + §5.10-§5.11 — additive content + 7-tab refactor + 5-step wizard + server-side Conversation History;NO Tier 2 leak(Access tab disabled affordance / Workspace switcher disabled affordance / Multimodal Tier 2 disabled affordances / Labs hidden / Forgot password disabled affordance)
- [ ] CC6 CLAUDE.md §5.2 H2 check — **no new dependency**(per ADR-0031 Option B uses existing `psycopg>=3.2` per ADR-0023;no Key Vault SDK / no Entra Graph SDK — those are Wave C);shadcn/ui + `tokens.ts` unchanged
- [ ] CC7 CLAUDE.md §3.2 conventions — `tsc --noEmit` exit 0 + `next lint` "No ESLint warnings or errors" on all F1-F8 changes;no `any`;shadcn/ui only;design tokens via `tokens.ts`(`[oklch`=0);App Router only;Server Components default;Client Components have `"use client"` + docstring
- [ ] CC8 CLAUDE.md §3.1 conventions — Python 3.12+ + mypy --strict clean + async by default + Pydantic v2 + structlog JSON + absolute imports;function length soft cap 50 lines;pytest + pytest-asyncio;coverage ≥ 80% on F3 `/conversations` + F5.1/F5.2/F5.3 new endpoints
- [ ] CC9 CLAUDE.md §5.5 H5 — no secret committed;no hardcoded tenant/subscription/resource;`/conversations` user_id from `get_current_user` (no PII;no plaintext-prompt logging changed)
- [ ] CC10 CLAUDE.md §5.4 H4 — Tier 2 boundary held:Workspace switcher disabled / Labs hidden / Access tab disabled affordance / Multimodal Tier 2 affordances disabled / Forgot password disabled / no GraphRAG / multi-agent / multi-tenancy / multi-modal-search / auto-sync / fine-tune leak
- [ ] CC11 Karpathy §1.3 surgical — preserve Tab 1/2/5/6/7 unchanged in F5(`git mv` if needed);additive content only(NEW Tab 3 Images + NEW Tab 4 Chunking Lab);no "順手" refactor of adjacent code

---

**Lifecycle reminder**:呢份 checklist 衍生自 `plan.md` deliverables。新加 deliverable 必須先入 plan + §7 changelog,然後再加 checklist item。延後 item 標 🚧 + reason,**唔可以刪**未勾選 `[ ]`。
