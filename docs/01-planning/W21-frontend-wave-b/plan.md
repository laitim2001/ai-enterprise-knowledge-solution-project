---
phase: W21-frontend-wave-b
name: "Frontend Wave B — Doc Detail 3-pane + Eval Console refactor + Traces list + Trace 3 viz (per ADR-0029 Option C `/kb/[id]/docs/[docId]` + ADR-0030 absorbed scope)"
sprint_week: W21
start_date: 2026-05-17              # real-calendar — kicked off post-W20 closeout (Chris directive「開 W21-frontend-wave-b kickoff」); independent of W16 F1-F4 (Track-A-blocked, parallel) and W22 Wave C (sequential, post-W21 close)
end_date: 2026-05-24                # ~1 week per W19 F4 §2.3 (backend ~2 days + frontend ~6.5-7.5 days); real-calendar collapse pattern 1.8-12× — actual likely ~1-2 days per W12-W20 trajectory; frontmatter is a window, not a commitment
status: active                      # `active` from kickoff 2026-05-17 (Chris directive at W20 F9 closeout post-push session + ADR-0029 Accepted + ADR-0030 absorbed = the authorization; same pattern as W20 D0 + W19 D0)
spec_refs:
  - architecture.md v6 §5.5.2        # KB Detail Chunks tab (per ADR-0024 — unchanged) + NEW §5.5.2a Document Detail page 3-pane (per ADR-0029 Option C)
  - architecture.md v6 §5.6          # Eval Console (W17 F3 RAGAs 4-metric integration consumed)
  - architecture.md v6 §5.7          # Traces (W18 ADR-0024 — flat `/traces/[traceId]` URL preserved; W21 adds `/traces` index)
  - ADR-0029                         # /doc-detail 3-pane (Accepted Option C `/kb/[id]/docs/[docId]` per W19 F6)
  - ADR-0030                         # SKIPPED per W19 F6 — Dashboard polish shipped Wave A F2; Trace 3 viz + /traces list ship Wave B F5+F6 (this phase)
  - ADR-0024                         # Unified application shell (W18) — Wave B routes render inside the existing <AppShell>
  - ADR-0025                         # KB Detail 8-tab (Wave A shipped 7-tab `-Access`; Wave B doc detail nested under `/kb/[id]/docs/[docId]` consistent with the IA)
prior_phase: W20-frontend-wave-a    # closed 2026-05-17 (Gate PASS WITH SMOKE-USER-DEFERRED CAVEAT); 19 phase closed; 3 ADRs (0025/0028/0031) Implementation Status appended at closeout; rule-of-3 wizard primitive promotion trigger NOW hit (Wave B+ candidate per W20 F6.2 — but Wave B has no wizard surface, defer further)
related_artifacts:
  - docs/01-planning/W19-frontend-audit-and-adr-draft/audit/W19-wave-breakdown.md   # §2 Wave B scope skeleton (signed off W19 F4)
  - docs/01-planning/W19-frontend-audit-and-adr-draft/audit/W19-backend-gap-map.md  # §3.3 Wave B backend deps (items 9-10)
  - docs/01-planning/W19-frontend-audit-and-adr-draft/audit/W19-mockup-jsx-audit.md # §2.1 D5 (Doc Detail 3-pane + route topology) + §2.1 D6 (Eval Console) + §2.1 D7 (Traces)
  - references/design-mockups/PAGE_INVENTORY.md                # rows #6 (/doc-detail) / #8 (/eval) / #9 (/traces) / #10 (/traces/[traceId])
  - references/design-mockups/DESIGN_README.md                 # high-fidelity click-through HTML prototype entry
  - references/design-mockups/ekp-page-doc-detail.jsx          # `PageDocDetail` 3-pane + `ChunkInspector` + `ImageThumb`
  - references/design-mockups/ekp-page-eval.jsx                # `PageEval` 4-metric stat + Shootout + Failed queries + Recommendation + Ops + CRAG insights
  - references/design-mockups/ekp-page-traces.jsx              # `PageTraces` list + `PageTraceDetail` 9-stage 3 viz modes
  - docs/adr/0029-doc-detail-3-pane-layout.md                  # Accepted Option C `/kb/[id]/docs/[docId]` (W19 F6 `6a34a41`)
  - frontend/app/(app)/kb/[id]/page.tsx                        # F3 — Documents tab row click → `/kb/[id]/docs/[docId]` deep-link (existing W17 F4.1 navigation point)
  - frontend/app/(app)/eval/page.tsx                           # F4 — W15 baseline → 6-section refactor
  - frontend/app/(app)/traces/page.tsx                         # F5 — W18 thin index → richer list view
  - frontend/app/(app)/traces/[traceId]/page.tsx               # F6 — W18 stage list → 3 viz modes (vertical default + waterfall + flame)
  - backend/api/routes/documents.py                            # F1 — extend with `GET /kb/{kb_id}/docs/{doc_id}` enriched (outline + parse/embed durations + image refs)
  - backend/api/routes/debug.py                                # F2 — add `GET /traces?filter=...&since=...` list endpoint (existing `GET /debug/trace/{id}` preserved)
  - backend/api/schemas/listing.py                             # F1 — NEW `DocumentDetail` + `OutlineNode` schemas
  - backend/api/schemas/observability.py                       # F2 — NEW `TraceSummary` schema for list endpoint
  - docs/architecture.md                                       # F0 — inline-tagged §5.5.2 + §5.5.2a (NEW) + §5.6 + §5.7 amendments per ADR-0029 + ADR-0030 absorbed
  - docs/02-architecture/COMPONENT_CATALOG.md                  # F7 — C01 + C03 + C06 + C07 + C09 status notes for Wave B amendments
  - docs/12-ai-assistant/01-prompts/01-session-start.md        # F8 — §3 / §10 / §11 / §12 + Update history catch-up
---

# Phase W21 — Frontend Wave B

> **Plan version**:1.0(draft 2026-05-17 — rolling JIT per CLAUDE.md §10 R1;kicked off post-W20 closeout per Chris directive「開 W21-frontend-wave-b kickoff」)
> **Owner**:Chris(Tech Lead + stakeholder)+ AI(implementation)
> **Approved by**:Chris — ADR-0029 **Accepted (Option C `/kb/[id]/docs/[docId]`)** 2026-05-16 W19 F6 + ADR-0030 **SKIPPED-absorbed** per W19 F6(Dashboard polish shipped Wave A F2;Trace 3 viz + `/traces` list ship Wave B F5+F6 = this phase)+ Chris kickoff directive 2026-05-17 = the「approved + implement now」authorization per CLAUDE.md §5.1 H1 + §10 R5。`architecture.md v6 §5.5.2 + §5.5.2a + §5.6 + §5.7` inline-tagged amendments land alongside this kickoff in F0(same convention as W20 F0 + W18 ADR-0024 + §3.4/§3.7 precedent — doc version held)。

---

## 1. Scope

W21 = **Wave B of the 4-Wave design-mockups → real-`frontend/` implementation roadmap**(per W19 F4 §1)— the **smallest by file count + backend scope** but **frontend-heavy via 3 viz modes + 3-pane layout**(4 routes touched + 2 NEW backend endpoints)— ships:

- **`/kb/[id]/docs/[docId]`** 3-pane Document Detail per **ADR-0029 Option C**(IA consistency with ADR-0024 flat URL + KB-scoped grouping per W18 ADR-0024)
  - **Left pane**(sticky 240px):Document outline — heading hierarchy from layout_aware chunker;section-scrollable + click-to-jump
  - **Center pane**(1fr):Chunks list within active section — chunk preview cards with section_path + tokens + has_image + low_value badges
  - **Right pane**(sticky 380px):Chunk inspector — metadata badges + section_path + prev/next links + associated image card + **embedding vector preview**(24 sampled dims;Wave B verify feasibility per ADR-0029 §3 alt #3 — if Azure Search exposes vectors via `select=*,content_vector`, implement;if expensive,`<DisabledAffordance variant="p3-preview" showBadge>` "Embedding vector view: Tier 2")
  - **Header**:pipeline stages strip + Image strip(horizontal scroll thumbnails)
- **`/eval`** Eval Console refactor — replaces W15 baseline with the Wave B 6-section overview:
  - **4-metric stat strip**(Precision@5 + Recall@5 + Faithfulness + Answer Relevancy from `EvalReport`)
  - **Reranker Shootout table**(Cohere v4.0-pro production-locked baseline + 5 alternatives + 2 dropped per ADR-0012;consume `POST /eval/shootout` per W17 F3)
  - **Failed queries inspector**(Expected vs Got per `EvalReport.failed_queries[]`)
  - **Recommendation card**(NON-STICKY 0.70 threshold per ADR-0007 + W5 D4)
  - **Ops Metrics card**(p50/p95 latency + cost per query)
  - **CRAG Insight card**(trigger rate + iterations + reasoning;derived from `EvalReport.crag_trigger_rate`)
- **`/traces`** index list view per **ADR-0030 absorbed scope** — NEW endpoint `GET /traces?filter=...&since=...` + 9-col table(timestamp + duration + status + KB + query preview + tokens + cost + CRAG iterations + stage count)+ filter seg(All / Errors / CRAG triggered)+ date range picker;row click → `/traces/[traceId]`
- **`/traces/[traceId]`** 9-stage trace + **3 viz modes** per ADR-0030 absorbed scope:
  - **Vertical**(Tier 1 default — current W18 list style preserved)
  - **Waterfall**(timeline bars with stage start + duration;per-stage tooltip)
  - **Flame**(flame-graph stacked bars showing nested call depth)
  - Viz mode toggle in header(`<ToggleGroup>` per W18 §5.5.4 precedent);persisted to `localStorage['ekp-trace-viz-mode']`
  - Final response card preserved(W16 F5.5 baseline)

**The `<AppShell>` foundation from W18 + Wave A polish from W20 stay unchanged**;W21 is **additive new routes + view refactor** inside the existing shell — NOT a re-layout。

Goals(= ADR-0029 + ADR-0030 absorbed scope mapped onto F1-F8):

- **Backend foundation**(F1 + F2)— land the 2 NEW backend endpoints per W19 F2 §3.3(items 9-10):`GET /kb/{kb_id}/docs/{doc_id}` enriched + `GET /traces?filter=...&since=...` list。**~2 backend days budget**。
- **`/kb/[id]/docs/[docId]` 3-pane**(F3 — ADR-0029 Option C)— NEW route under `(app)/kb/[id]/docs/[docId]/page.tsx`;3-pane layout with outline + chunks + inspector;embedding vector preview verify feasibility(Wave B verify per ADR-0029 §3 alt #3)。**Frontend ~2-3 days**。
- **`/eval` refactor**(F4 — W17 F3 RAGAs consumed,NO new backend)— rewrite `frontend/app/(app)/eval/page.tsx` with 6-section overview consuming existing `POST /eval/run` + `POST /eval/shootout` endpoints。**Frontend ~2 days**。
- **`/traces` index**(F5 — ADR-0030 absorbed)— NEW `(app)/traces/page.tsx` index list view consuming F2 backend。**Frontend ~0.5 days**。
- **`/traces/[traceId]` 3 viz modes**(F6 — ADR-0030 absorbed)— refactor existing W18 page with 3 viz mode toggle(vertical default + waterfall + flame)+ `<ToggleGroup>` persisted to localStorage。**Frontend ~1.5 days**。
- **Cross-cutting polish**(F7 — A11y + Responsive + Dark-mode + Tests)— `[oklch(`=0 milestone preserved + Vitest expansion(W20 F8.4 baseline 14 files/37 tests → W21 target 16-18 files/45+ tests)+ Playwright E2E route updates(4 NEW routes)+ `<DisabledAffordance>` consumed if embedding-vector defers + COMPONENT_CATALOG.md status notes for C01/C03/C06/C07/C09 + PAGE_INVENTORY.md 4 routes status flip。
- **Phase closeout**(F8)— Gate verdict + retro + frontmatter `closed` + `session-start.md` hygiene + W22+ rolling-JIT trigger(NOT pre-created)。

**Out of W21 scope**(stay Wave C / Tier 2 / W16 / future):
- `/settings` 6-tab(per ADR-0026)— **Wave C** W22
- `/users` 4-tab Tier 1.5 RBAC(per ADR-0027 Option A)— **Wave C1** W22
- `/kb/[id]` **Access tab activate** — Wave C1(needs ADR-0027 backend infra:6 NEW Postgres tables + Key Vault SDK + Entra Graph SDK + ACL middleware)
- Real-MSAL feature-flagged path — **Wave C** W22(mock-auth default through Wave C per user 岔口 2)
- 2 NEW dependencies(Key Vault SDK + Entra Graph SDK)— **Wave C kickoff** per ADR-0017 Plan B sequencing decision
- Track A IT cred items — still W16 F1(parallel track,unaffected)
- 25% Beta cohort rollout + daily metric monitor + Q15 weekly signal report — W16 F2-F3(Beta phase)
- Full NVDA/JAWS/VoiceOver screen-reader audit(Tier 2 — CO_W15_F3_aria_full_audit;W21 F7 = a11y spot-check on new surfaces only)
- **Rule-of-3 wizard primitive promotion**(W20 F6.2 carry-over)— Wave B has **NO wizard surface**(doc detail + eval + traces 全部 non-wizard),所以 defer 到 standalone refactor commit OR Wave C(which has /settings + /users with wizard surfaces);per Karpathy §1.3 surgical — don't bundle unrelated refactor into Wave B
- Embedding vector preview if Azure Search doesn't expose vectors cheaply — Tier 2 disabled affordance per ADR-0029 §3 alt #3

**Pre-condition for W21 promotion**(satisfied 2026-05-17):
- ADR-0029 **Accepted Option C**(W19 F6 Chris pick 2026-05-16)
- ADR-0030 **SKIPPED-absorbed**(W19 F6 — Dashboard polish shipped Wave A F2;Trace 3 viz + /traces list ship Wave B F5+F6 = this phase)
- W20-frontend-wave-a = **closed**(Gate PASS WITH SMOKE-USER-DEFERRED CAVEAT 2026-05-17;Wave A 6 ADRs Implementation Status appended;<AppShell> + design tokens unchanged Wave B inherits)
- W19 audit/W19-backend-gap-map.md §3.3 = file:line evidence for 2 NEW endpoints(items 9-10)+ 11 Tier 1 already-supported endpoints(`/eval/run` + `/eval/shootout` + `/debug/trace/{id}` all wired W17 F3 + W16 F5.5)
- W19 audit/W19-wave-breakdown.md §2 = Wave B scope skeleton signed off
- W16 F1-F4 = Track-A-blocked(parallel track — W21 does not depend on Q11 cred populate event;mock-auth default per user 岔口 2)
- W17-beta-hardening = closed(RAGAs 4-metric backend per ADR-0012 + W17 F3 — Wave B `/eval` consumes,no new backend for eval)
- W18-app-shell-ia = closed(Unified `<AppShell>` IA per ADR-0024 — Wave B routes render inside the existing shell;`/traces/[traceId]` flat URL preserved)
- CLAUDE.md v1.7 H7 Design Fidelity Hard Constraint(2026-05-17 promotion)— Wave B inherits;3-pane layout + 3 viz modes + Eval Console refactor all gate on mockup fidelity

## 2. Deliverables(F0-F8)

### F0 — Kickoff cascade(ADR-0029 Status verify Accepted + ADR-0030 absorbed footnote + spec amendment — landed at kickoff)

- **Component(s)**:cross-cutting governance(docs)
- **Spec ref**:CLAUDE.md §10 R1(kickoff)+ R5(ADR-before-implement);ADR-0029;ADR-0030 absorbed;`architecture.md v6 §5.5.2 + §5.6 + §5.7`
- **OQ deps**:none(Wave B scope locked per W19 F4 §2;Chris kickoff directive 2026-05-17 IS authorization)
- **Acceptance criteria**:
  - F0.1 ADR-0029 Status verify **Accepted Option C**(no-op — W19 F6 `6a34a41` already accepted);**Implementation Note** appended at W21 kickoff explaining the Wave B implementation phase(same convention as W20 F0 / W18 ADR-0024)
  - F0.2 ADR-0030 SKIPPED footnote preserved per W19 F6 closeout(README footnote unchanged — Dashboard polish shipped Wave A F2;Trace 3 viz + /traces list ship Wave B F5+F6)
  - F0.3 `docs/architecture.md` — inline-tagged amendments(doc version held per W18 ADR-0024 + §3.4/§3.7 precedent):
    - **§5.5.2 KB Detail Chunks tab** — unchanged annotation;cross-ref to NEW §5.5.2a Document Detail page
    - **§5.5.2a NEW** Document Detail page 3-pane per ADR-0029(`/kb/[id]/docs/[docId]`)— outline + chunks + inspector with embedding vector preview(Wave B verify feasibility);header pipeline stages strip + image strip
    - **§5.6 Eval Console** — 6-section refactor per Wave B(consume W17 F3 RAGAs 4-metric)
    - **§5.7 Traces** — `/traces` index NEW + `/traces/[traceId]` 3 viz modes per ADR-0030 absorbed scope
  - F0.4 `docs/01-planning/W21-frontend-wave-b/{plan,checklist,progress}.md` created — `status: active`(per Chris kickoff directive 2026-05-17;same pattern as W20 D0 + W19 D0)
  - F0.5 `docs/12-ai-assistant/01-prompts/01-session-start.md` §10 W21 row added(`active`)+ §12 milestones row added(`active`)+ Update history entry
- **Effort estimate**:0.3 day(W21 D0 kickoff — same-day as W20 F9 closeout push 2026-05-17;all 3 docs same-session creation;same pattern as W20 D0 0.5d)
- **Owner**:AI(draft)+ Chris(authorize via kickoff directive — already given)

### F1 — Backend `GET /kb/{kb_id}/docs/{doc_id}` enriched per ADR-0029(C01 + C03)

- **Component(s)**:**C01** Ingestion Pipeline(parse/embed timing data persistence)+ **C03** Indexing Service(outline + image_refs aggregation)
- **Spec ref**:ADR-0029 §3 Backend addition;W19 F2 §3.3 item 9;architecture.md v6 §5.5.2a
- **OQ deps**:none(endpoint scope clear from ADR-0029)
- **Acceptance criteria**:
  - F1.1 NEW Pydantic v2 schemas in `backend/api/schemas/listing.py`(or `documents.py` if new file makes sense):
    - `DocumentDetail` — `doc_id` / `title` / `source` / `source_url` / `file_type` / `size_kb` / `pages` / `language` / `chunk_strategy` / `total_chunks` / `total_images` / `total_tokens` / `low_value_chunks` / `parse_duration_ms` / `embed_duration_ms` / `indexed_at` / `outline: list[OutlineNode]` / `image_refs: list[ImageRef]`
    - `OutlineNode` — `level: int` / `title: str` / `chunk_count: int` / `page: int | None`
    - mypy strict clean
  - F1.2 NEW route `GET /kb/{kb_id}/docs/{doc_id}` in `backend/api/routes/documents.py`:
    - Auth-gated via `Depends(get_current_user)`(per W17 F2)
    - Aggregates outline via `engine.list_chunks(kb_id, doc_id=doc_id)` + heading hierarchy reconstruction from `section_path` field
    - Aggregates `image_refs` via existing W17 F4.1 `embedded_images_json` select extension(W20 F5.2 precedent)
    - Returns 404 if kb_id or doc_id missing
    - Parse + embed durations:**deviation seam** — Wave B sources from ingestion result persistence if available(`backend/persistence/ingestion_results/`),else returns `parse_duration_ms = None` + `embed_duration_ms = None`(forward-compat fields documented as Wave C+ wiring)
  - F1.3 Backend pytest `backend/tests/api/test_documents_detail_route.py` — coverage ≥ 80% per H6;test cases:happy path(rich outline + image refs)/ missing kb 404 / missing doc 404 / cross-user isolation(if applicable)/ empty outline gracefully handled
  - F1.4 mypy strict clean;`pytest` pass
- **Effort estimate**:1 day(W21 D1 — schema + route + pytest)
- **Owner**:AI(implementation)

### F2 — Backend `GET /traces?filter=...&since=...` list per ADR-0030 absorbed(C07)

- **Component(s)**:**C07** Observability Stack(Langfuse Postgres query + filter)
- **Spec ref**:ADR-0030 absorbed scope(W19 F6 SKIPPED-but-implemented);W19 F2 §3.3 item 10;architecture.md v6 §5.7
- **OQ deps**:none(Langfuse Postgres backing decision already locked W17 F4 + ADR-0017 occurrence #7)
- **Acceptance criteria**:
  - F2.1 NEW Pydantic v2 schema in `backend/api/schemas/observability.py`:
    - `TraceSummary` — `trace_id` / `timestamp` / `duration_ms` / `status: Literal['ok', 'error', 'crag_triggered']` / `kb_id` / `query_preview: str`(first 100 chars)/ `total_tokens` / `cost_usd` / `crag_iterations: int | None` / `stage_count: int`
    - `TraceListResponse` — `{items: list[TraceSummary], total: int, limit: int, offset: int}`
    - mypy strict clean
  - F2.2 NEW route `GET /traces` in `backend/api/routes/debug.py`(or new `traces.py` if scope warrants):
    - Auth-gated via `Depends(get_current_user)`
    - Query Langfuse Postgres for top-N trace summaries(default 50;configurable via `?limit=`)
    - Filter:`?filter=all|errors|crag_triggered` + `?since=ISO8601` + `?kb_id=` optional
    - Sort:default by `timestamp DESC`;configurable via `?sort=`
    - Returns `TraceListResponse` paginated
  - F2.3 Backend pytest `backend/tests/api/test_traces_route.py` — coverage ≥ 80%;test cases:happy path / filter=errors / filter=crag_triggered / empty result / pagination
  - F2.4 mypy strict clean;`pytest` pass
- **Effort estimate**:1 day(W21 D1-D2 — schema + route + pytest;Langfuse query layer simple per W17 F4 + W18 F4 health pattern)
- **Owner**:AI(implementation)

### F3 — `/kb/[id]/docs/[docId]` 3-pane Doc Detail per ADR-0029 Option C(C09 + C01 + C03)

- **Component(s)**:**C09** Admin Console UI(NEW route)+ consume **C01** + **C03** via F1 endpoint
- **Spec ref**:ADR-0029 Decision §1;architecture.md v6 §5.5.2a NEW;CLAUDE.md §3.2.1 H7 design fidelity(`ekp-page-doc-detail.jsx PageDocDetail`)
- **OQ deps**:**Embedding vector preview feasibility**(per ADR-0029 §3 alt #3)— Wave B verify:if Azure Search exposes vectors via `select=*,content_vector`, implement;if expensive,`<DisabledAffordance variant="p3-preview" showBadge>` "Embedding vector view: Tier 2 — request to enable"。Decision at F3.5 implementation time(not kickoff blocker)。
- **Acceptance criteria**:
  - F3.1 NEW route `frontend/app/(app)/kb/[id]/docs/[docId]/page.tsx` — 3-pane layout(`grid-cols-[240px_1fr_380px]` baseline;responsive breakpoint at < 1200px collapses left pane to drawer + right pane to overlay)
  - F3.2 NEW `frontend/lib/api/docDetail.ts` — typed client for `GET /kb/{kb_id}/docs/{doc_id}` consuming F1 backend
  - F3.3 **Left pane** Document Outline — `<DocumentOutline>` component;sticky 240px;heading hierarchy from `DocumentDetail.outline[]`;`<button>` per node;active node tracked via `IntersectionObserver` on center pane chunks + click-to-jump scroll
  - F3.4 **Center pane** Chunks list — `<ChunkList>` component;1fr;cards per chunk with section_path + tokens + has_image badge + low_value badge + content preview(highlight `<mark>` for emphasized text from layout_aware chunker)+ associated image thumbnail(if `embedded_images[0]` exists)
  - F3.5 **Right pane** `<ChunkInspector>` component;sticky 380px;metadata badges(chunk_index + tokens + embedded_images count + low_value badge)+ section_path + prev/next chunk links + associated image card + **embedding vector preview**(24 sampled dims in 8-col grid + "+1000 more dims" tail caption);**feasibility verify**:if `chunk.embedding_vector` field exists in `Chunk` schema OR retrievable via Azure Search `select=*,content_vector` extension,render the grid;if expensive,replace with `<DisabledAffordance variant="p3-preview" showBadge reason="Embedding vector view: Tier 2 — request to enable" tier2Trigger="Azure Search vector field exposure">`
  - F3.6 **Header** pipeline stages strip — 5 stages(Parse / Extract / Chunk / Embed / Index)+ timing data from `DocumentDetail.parse_duration_ms` + `embed_duration_ms`(other 3 stages — forward-compat seam,Tier 1 = parse + embed only;Extract/Chunk/Index stage durations show "—" with tooltip "Stage timing — Wave C+ instrumentation")
  - F3.7 **Image strip** — horizontal scroll thumbnails(`<ImageStripScroller>`);per-image badge(SHA256 hash + dim + size + low_value/dedup);click → `<ScreenshotModal>`(reuse Wave A pattern)
  - F3.8 Navigation deep-link from `/kb/[id]` Documents tab row → `<Link href={\`/kb/${kbId}/docs/${docId}\`}>` per ADR-0029 + W20 F5 Documents tab preserved
  - F3.9 Loading skeletons(`<DocDetailSkeleton>` per pane)+ error banners(per-pane destructive text)+ empty states(no outline → "No headings detected" placeholder)
  - F3.10 Tokens 100%(`Grep '\[oklch'` across `frontend/` = 0 preserved);`tsc --noEmit` exit 0;`next lint` clean
  - F3.11 File header docstring + Vitest test scaffold deferred → F7.4 batches per W20 F1.7 / W19 F8.4 precedent
- **Effort estimate**:2-3 days(W21 D2-D4 — largest deliverable;3-pane layout + 3 NEW components + embedding vector feasibility verify)
- **Owner**:AI(implementation)+ user(UX review on 3-pane density + embedding vector grid)

### F4 — `/eval` Eval Console refactor per W17 F3 RAGAs(C09 + C06)

- **Component(s)**:**C09** Admin Console UI(refactor)+ consume **C06** Eval Framework via existing `POST /eval/run` + `POST /eval/shootout`(W17 F3 RAGAs)
- **Spec ref**:architecture.md v6 §5.6;CLAUDE.md §3.2.1 H7 design fidelity(`ekp-page-eval.jsx PageEval`)
- **OQ deps**:**no new backend**(F4 consumes existing W17 F3 endpoints — verified W19 F2 backend gap map line 115-118 all ✅ supported)
- **Acceptance criteria**:
  - F4.1 Rewrite `frontend/app/(app)/eval/page.tsx`(replaces W15 baseline)with 6 sections:
    - **Section 1 — 4-metric stat strip** — 4 `<StatCard>` cards(Precision@5 + Recall@5 + Faithfulness + Answer Relevancy)from `EvalReport`;loading skeleton + run-vs-baseline delta chips
    - **Section 2 — Reranker Shootout table** — consume `POST /eval/shootout` → `ShootoutReport`;5 rerankers + 2 dropped(Voyage + ZeroEntropy per ADR-0012);Cohere v4.0-pro highlighted as production-locked baseline;per-row 4-metric chips + winner badge
    - **Section 3 — Failed queries inspector** — collapsible `<details>` per `EvalReport.failed_queries[]`;Expected vs Got side-by-side;jump-to-trace link → `/traces/[traceId]` for any logged failed query
    - **Section 4 — Recommendation card** — text card explaining current production config(`{reranker: 'cohere-v4', threshold: 0.70, NON_STICKY: true}` per W5 D4);advisory only,no interactive controls
    - **Section 5 — Ops Metrics card** — p50/p95/p99 latency + average cost/query;sourced from `EvalReport.ops_metrics`(if exposed,else `<DisabledAffordance>` "Ops metrics not in EvalReport — Wave C+")
    - **Section 6 — CRAG Insight card** — trigger rate + avg iterations + qualitative reasoning;sourced from `EvalReport.crag_trigger_rate` + `crag_avg_iterations`(verify field per W19 F2 line 118;if missing fields,fallback to coverage-only display)
  - F4.2 "Run eval" button → `POST /eval/run`(consume W17 F3 endpoint)+ result rendered into the 6 sections;optimistic UI + skeleton during run
  - F4.3 "Run shootout" button → `POST /eval/shootout`(consume W17 F3 endpoint)+ Section 2 table populated
  - F4.4 Loading skeletons + error banners + empty states first-class
  - F4.5 Tokens 100%;`tsc --noEmit` exit 0;`next lint` clean;`[oklch`=0 preserved
  - F4.6 File header docstring + Vitest test scaffold deferred → F7.4 batches
- **Effort estimate**:2 days(W21 D4-D5 — frontend-only refactor consuming existing backend)
- **Owner**:AI(implementation)+ user(UX review on 6-section density)

### F5 — `/traces` index list view per ADR-0030 absorbed(C09 + C07)

- **Component(s)**:**C09** Admin Console UI(NEW route)+ consume **C07** via F2 endpoint
- **Spec ref**:architecture.md v6 §5.7;CLAUDE.md §3.2.1 H7 design fidelity(`ekp-page-traces.jsx PageTraces`)
- **OQ deps**:none(F2 backend ships in same phase)
- **Acceptance criteria**:
  - F5.1 NEW route `frontend/app/(app)/traces/page.tsx`(replaces W18 thin index — currently a "Traces — coming Wave B" placeholder)— 9-col table view:
    - Columns:Timestamp / Duration / Status / KB / Query preview(truncate 80 chars + tooltip)/ Tokens / Cost USD / CRAG iter / Stage count
    - Row click → `/traces/[traceId]`
    - Filter seg(All / Errors / CRAG triggered)+ Date range picker(last 24h / 7d / 30d / custom)+ KB filter(dropdown if multiple KBs)
    - Persisted to `localStorage['ekp-traces-filter']`
  - F5.2 NEW `frontend/lib/api/traces.ts` — typed client for `GET /traces?filter=...&since=...` consuming F2 backend
  - F5.3 Loading skeleton + empty state("No traces in selected range")+ error banner
  - F5.4 Pagination — "Load more" button + URL state(`?page=N&size=50`)
  - F5.5 Tokens 100%;`tsc` + lint clean;`[oklch`=0 preserved
  - F5.6 File header docstring + Vitest test scaffold deferred → F7.4 batches
- **Effort estimate**:0.5 days(W21 D5 — small;reuses table pattern from W20 F4.3 kb/page.tsx table view)
- **Owner**:AI(implementation)+ user(filter/date range UX review)

### F6 — `/traces/[traceId]` 9-stage + 3 viz modes per ADR-0030 absorbed(C09 + C07)

- **Component(s)**:**C09** Admin Console UI(refactor)+ consume **C07** via existing `GET /debug/trace/{trace_id}`(W16 F5.5 already supported)
- **Spec ref**:architecture.md v6 §5.7;CLAUDE.md §3.2.1 H7 design fidelity(`ekp-page-traces.jsx PageTraceDetail`)
- **OQ deps**:none(no new backend — schema already has all needed fields per W19 F2 line 121)
- **Acceptance criteria**:
  - F6.1 Refactor `frontend/app/(app)/traces/[traceId]/page.tsx`(W18 vertical list baseline preserved as default mode)
  - F6.2 NEW viz mode toggle in header — `<ToggleGroup>` with 3 options(per W18 §5.5.4 precedent;同 W20 F3.7 citation modes 同 pattern):
    - **Vertical**(Tier 1 default — W18 list style preserved)
    - **Waterfall**(timeline bars `<svg>` based;per-stage tooltip with start_ms + duration_ms + status;sequential layout)
    - **Flame**(flame-graph stacked bars `<svg>` based;showing nested call depth where stage hierarchy exists;最 information-dense)
  - F6.3 NEW components:
    - `frontend/components/traces/trace-viz-vertical.tsx`(extracted from W18 inline rendering — Karpathy §1.3 surgical refactor)
    - `frontend/components/traces/trace-viz-waterfall.tsx`(NEW;SVG-based;~80 lines per Karpathy §1.2 simplicity)
    - `frontend/components/traces/trace-viz-flame.tsx`(NEW;SVG-based;~100 lines)
  - F6.4 Mode toggle persisted to `localStorage['ekp-trace-viz-mode']`(W18 sidebar focus-mode + W20 F3.7 citation-mode pattern)
  - F6.5 Final response card preserved(W16 F5.5 baseline + W18 F8 header role attribute)
  - F6.6 Loading skeleton + error banner unchanged
  - F6.7 Tokens 100%;`tsc` + lint clean;`[oklch`=0 preserved
  - F6.8 File header docstring on 3 NEW viz components + rewritten page;Vitest test scaffold deferred → F7.4 batches
- **Effort estimate**:1.5 days(W21 D5-D7 — 3 NEW SVG viz components + toggle plumbing)
- **Owner**:AI(implementation)+ user(viz mode UX review — 哪一個 mode 最 informative for stakeholder demo)

### F7 — Cross-cutting:responsive + a11y + dark-mode + tests + COMPONENT_CATALOG + PAGE_INVENTORY

- **Component(s)**:cross-cutting(C09 + C01 + C03 + C06 + C07 docs)
- **Spec ref**:CLAUDE.md §3.2.1 H7(design fidelity self-verify);CLAUDE.md §12 self-verification checklist
- **OQ deps**:none
- **Acceptance criteria**:
  - F7.1 Responsive spot-check on new W21 surfaces — `/kb/[id]/docs/[docId]` 3-pane(< 1200px → left pane drawer + right pane overlay)+ `/eval` 6 sections(mobile stacks vertical)+ `/traces` table(horizontal scroll < 1024px)+ `/traces/[traceId]` 3 viz modes(waterfall + flame SVG min-width)。Multi-viewport interactive browser smoke = user pre-Beta(R8 caveat per W18-W20 carry-over pattern)
  - F7.2 a11y spot-check on new W21 surfaces — Vertical viz `<nav aria-label>` / Waterfall + Flame SVG `role="img" aria-label` / 3-pane `<aside>` left + right + `<main>` center semantic landmarks / outline `<button aria-current="location">` active state / Toggle group `aria-pressed` viz mode state。Full screen-reader audit Tier 2 / CO_W15_F3_aria_full_audit defer per W20 carry-over
  - F7.3 Dark-mode `[oklch`=0 re-check — `Grep '\[oklch'` across `frontend/` = **0**(W15→W18→W20→W21 milestone preserved through 9+ commits)。Dark-mode interactive walkthrough = user pre-Beta smoke per CO_W15_F3_dark_mode_visual_verify
  - F7.4 Vitest expansion — W20 baseline 14 files/37 tests → W21 target **16-18 files / 45+ tests**(2-4 NEW test files batch covering F3 doc-detail + F4 eval + F5 traces-list + F6 trace-viz-waterfall/flame);per-file 1-3 tests render-smoke + key a11y attribute + interaction
  - F7.5 Playwright E2E updates — `app-shell-path.spec.ts` +1 NEW(`/kb/[id]/docs/[docId]` route renders 3-pane)+ `golden-path.spec.ts` +2 NEW(/eval 6 sections + /traces table)+ `visual-baseline.spec.ts` +1-2 NEW snapshot(`/kb/[id]/docs/[docId]` 3-pane + `/traces/[traceId]` waterfall mode;flame may defer per data-driven nature)。Interactive run via `PW_CHANNEL=chrome pnpm test:e2e`(ADR-0017 Plan B — system Chrome)= user pre-Beta smoke per W18-W20 carry-over
  - F7.6 `docs/02-architecture/COMPONENT_CATALOG.md` Status rows appended:
    - **C01** — F1 ingestion result persistence forward-compat seam(parse/embed duration fields surfaced)
    - **C03** — F1 outline aggregation via `engine.list_chunks` heading reconstruction
    - **C06** — F4 frontend consumes existing W17 F3 RAGAs endpoints(no backend change)
    - **C07** — F2 NEW `/traces` list endpoint
    - **C09** — F3 NEW `/kb/[id]/docs/[docId]` 3-pane + F4 `/eval` refactor + F5 `/traces` index + F6 3 viz modes
  - F7.7 `references/design-mockups/PAGE_INVENTORY.md` Cn mapping flip — 4 W21-implemented routes status「Wireable today / Wave B」→「Implemented W21 F#」:**#6** `/doc-detail` actual `/kb/[id]/docs/[docId]`(W21 F3 per ADR-0029 Option C)· **#8** `/eval` (W21 F4)· **#9** `/traces` (W21 F5)· **#10** `/traces/[traceId]`(W21 F6;3 viz modes)。Wave C candidates(#11 Settings / #12 Users)deferral notes preserved per ADR-0026/0027 governance
- **Effort estimate**:0.5-1 day(W21 D7 — cross-cutting verify + 2 doc files)
- **Owner**:AI(implementation)

### F8 — Phase closeout + W22+ rolling-JIT trigger

- **Component(s)**:cross-cutting governance
- **Spec ref**:CLAUDE.md §10 R3(plan deviation log)+ R5(ADR-after-implement no-op here since ADR-0029 pre-exists)
- **OQ deps**:none expected(W21 implementation shouldn't resolve / open any OQ)
- **Acceptance criteria**:
  - F8.1 W21 phase Gate verdict landed(PASS / PARTIAL PASS / FAIL with explicit rationale per W18-W20 pattern)
  - F8.2 W21 `progress.md` Retro — 7 sections written(What worked / What didn't & friction / Surprises / Decisions / Carry-overs to W22+ / Time tracking / Spec-ref alignment)
  - F8.3 ADR-0029 status verified `Accepted`(F0 verify no-op at closeout)+ **Implementation Status section appended at W21 Wave B closeout**(same convention as W20 F9.3 — 3 ADR appended Implementation Status sections);README row updated `Accepted` → `Accepted + Wave B implemented`
  - F8.4 W21 `plan.md` + `checklist.md` + `progress.md` frontmatter `status: active` → `closed`
  - F8.5 W22+ phase folder **NOT pre-created**(rolling-JIT per CLAUDE.md §10 R1)— kickoff candidates noted in `progress.md` Day-N retro section:**W22-frontend-wave-c1 + W22b-frontend-wave-c2 SPLIT** per W19 F4 §3.6 trigger(ADR-0026 Option B + ADR-0027 Option A combined ~42 backend days exceeds single-phase budget;Settings 6-tab + /users Tier 1.5 RBAC + Access tab activation + real-MSAL feature-flagged concurrent ship;**2 NEW deps** Key Vault SDK + Entra Graph SDK Plan B sequencing decision per ADR-0017);**Rule-of-3 wizard primitive promotion**(W20 F6.2 carry-over;Wave C surfaces have wizards);**W16 F1-F4 Track A IT cred parallel track**;**W23+ Tier 2 Q12 post-Beta governance**
  - F8.6 `session-start.md` hygiene catch-up — §3 C01/C03/C06/C07/C09 status(W21 Wave B amendments)+ §10 W21 row(closed,Gate verdict)+ W22+ not-pre-created note + §11 carry-overs(W21-closed items + any new 🚧 deferrals)+ §12 milestones row + Last-Updated + Update-history;`COMPONENT_CATALOG.md` + `PAGE_INVENTORY.md` already touched in F7.6 + F7.7
  - F8.7 OQ + ADR SKIPPED footnote — confirm no new OQ surfaced(R4 no-op expected);ADR-0030 SKIPPED footnote preserved per W19 F6 closeout;embedding vector preview feasibility outcome recorded(Implementation Status or `<DisabledAffordance>` deferral)
- **Effort estimate**:0.5 days(W21 D7 — closeout housekeeping cascade per W18-W20 pattern)
- **Owner**:AI(implementation)+ user(stakeholder verify ADR-0029 Implementation Status note)

---

## 3. Success Criteria(Phase Gate)

W21 phase Gate **PASS condition**:
1. F1 Backend `GET /kb/{kb_id}/docs/{doc_id}` enriched landed — `DocumentDetail` + `OutlineNode` schemas + pytest ≥ 80%
2. F2 Backend `GET /traces?filter=...&since=...` list landed — `TraceSummary` + `TraceListResponse` schemas + pytest ≥ 80%
3. F3 `/kb/[id]/docs/[docId]` 3-pane shipped per ADR-0029 Option C — outline + chunks + inspector;embedding vector preview feasibility decided(implement OR Tier 2 disabled affordance)
4. F4 `/eval` 6-section refactor shipped — consume existing W17 F3 RAGAs endpoints;NO new backend
5. F5 `/traces` index list view shipped — table + filter + date range + pagination
6. F6 `/traces/[traceId]` 3 viz modes shipped — vertical default + waterfall + flame;mode toggle persisted to localStorage
7. F7 cross-cutting verified — `[oklch`=0 milestone + tsc/lint clean + Vitest 45+ tests pass + Playwright route updates + COMPONENT_CATALOG + PAGE_INVENTORY notes
8. F8 closeout — Gate verdict + retro + frontmatter `closed` + session-start.md hygiene + W22+ rolling-JIT trigger
9. CLAUDE.md §3.2.1 H7 design fidelity — each F3/F4/F5/F6 surface 對齊 mockup per `references/design-mockups/ekp-page-doc-detail.jsx` + `ekp-page-eval.jsx` + `ekp-page-traces.jsx`(layout / spacing / typography / color tokens / interaction states / responsive / a11y);唔對齊嘅地方 STOP+ask per §5.7 H7 trigger 或標 🚧 deferred + reason

W21 phase Gate **PARTIAL PASS** acceptable per Karpathy §1.4:
- F3.5 embedding vector preview — if Azure Search doesn't expose vectors cheaply,fall back to `<DisabledAffordance variant="p3-preview" showBadge>` Tier 2(per ADR-0029 §3 alt #3)— PARTIAL acceptable(rendering implemented but data not real)
- F4.5 Ops Metrics — if `EvalReport.ops_metrics` field doesn't exist,`<DisabledAffordance>` "Ops metrics — Wave C+"(Karpathy §1.2 don't pre-build)
- F4.6 CRAG Insight — if `EvalReport.crag_avg_iterations` field missing,fallback to coverage-only display
- F7.1 multi-viewport browser smoke — deferred → user pre-Beta(R8 / CO_W15_F4_browser_binaries / `PW_CHANNEL=chrome` Plan B);responsive classes are the deliverable
- F7.5 Playwright full run + visual baseline first-capture — same R8 caveat as W18-W20(spec compile-check is the deliverable;run = user pre-Beta smoke)
- F6.3 Flame viz visual baseline — flame-graph stacked-bar depth depends on real trace data with nested stages;Wave A trace data may be flat(stage list,no nesting)so flame mode renders as waterfall-equivalent → visual baseline defer to Wave C+ when nested-stage traces become common
- a11y — spot-check on new surfaces only(full screen-reader audit stays Tier 2)

W21 phase Gate **FAIL condition**:
- Tier 2 leak — implementing 2 NEW deps(Key Vault SDK + Entra Graph SDK)— they're Wave C kickoff scope
- Real-MSAL feature flag accidentally enabled in Wave B(mock-auth default continues through Wave C per user 岔口 2)
- `frontend tsc --noEmit` / `next lint` regression(must stay clean);`pnpm test:unit` regression below W20 F8.4 baseline 14 files/37 tests
- `[oklch`=0 milestone broken(W15/W18/W20 milestone must hold through Wave B)
- Backend test coverage on new `/kb/{kb_id}/docs/{doc_id}` or `/traces` routes < 80%(per CLAUDE.md §3.1 H6)
- 3-pane layout collapses content at standard desktop viewports(1280px+)— responsive breakpoint MUST be < 1200px,not at standard desktop
- ADR-0029 Implementation Status section NOT appended at closeout(F8.3 = the closeout housekeeping discipline per W20 F9.3 precedent)
- CLAUDE.md §3.2.1 H7 violation — "大概模仿" Doc Detail / Eval / Traces mockups(must 100% reproduce per CLAUDE.md v1.7 Hard Constraint)

## 4. Risks(Phase-Specific)

| Risk | Likelihood | Impact | Mitigation |
|---|---|---|---|
| Embedding vector preview cost — Azure Search `select=*,content_vector` may be slow / metered | Medium | Medium | F3.5 verify feasibility upfront(grep + small test query);if expensive,fall back to `<DisabledAffordance variant="p3-preview" showBadge>` Tier 2 per ADR-0029 §3 alt #3 — UI rendering preserved,data layer disabled affordance |
| 3-pane responsive at narrow viewports breaks layout | Medium | Medium | Responsive breakpoint at < 1200px → left pane collapses to drawer(`<Sheet>` per W18 AppShell drawer pattern)+ right pane to overlay modal;`grid-cols-[240px_1fr_380px]` baseline desktop;test at 1280 / 1024 / 768 / 375 viewports per W18 BUG-002 lesson |
| Flame viz needs nested stage data,Wave A traces are flat | High | Low | F6.3 flame component rendering implemented,but visual baseline + flame-specific test scenarios defer Wave C+ when nested-stage traces become common(per ADR-0020 Context Expander multi-step traces);PARTIAL PASS allows |
| 3 viz mode toggle proliferation(WB precedent says toggles are simple) | Low | Low | 3 modes locked per ADR-0030 absorbed;no semantic search / fuzzy filter / other modes;`<ToggleGroup>` is single primitive |
| Eval Console 6-section density at mobile viewport | Low | Medium | Stack vertically per `flex-col md:grid` responsive;all 6 sections collapsible via `<details>` if scope drift |
| W17 F3 RAGAs endpoint shape changes between W17 close and W21 implementation | Low | Low | Grep-verify W17 F3 endpoint contract at F4 implementation start(`backend/api/routes/eval.py:104` + `139`);if drift detected,STOP+ask before refactor |
| `npx playwright install chromium` still R8-blocked(W18-W20 same risk) | High | Low | Known(CO_W15_F4_browser_binaries / ADR-0017 Plan B realised W15 D5 + 2026-05-13 via `PW_CHANNEL=chrome`);F7.5 deliverable = spec compile-check + the run via `PW_CHANNEL=chrome pnpm test:e2e`(uses system Chrome per ADR-0017 Plan B (a)) |
| F3 3-pane scope sprawl(power-user features beyond ADR-0029) | Medium | Medium | Strict ADR-0029 acceptance criteria;NO file editing / chunk editing / re-chunking from this surface(those are Tier 2);inspector is **read-only**;Chunking Lab tab in `/kb/[id]` is the editing surface |
| Mockup vs backend contract conflict in F3 chunk inspector(prototype shows fields backend may not provide) | Medium | Medium | Per CLAUDE.md §13 — backend wins per §4 authority ordering(per W20 F7.2 precedent);visual polish-only migrate from mockup;defer unknown-field fields to Wave C+ |
| ADR-0027 Option A RBAC backend leaks into Wave B | Low | Medium | Wave B doesn't touch RBAC at all(Wave C1 scope);grep-verify no `from backend.api.routes.users import` or `roles` table reference in Wave B code |

## 5. Day-by-Day Breakdown(rough)

| Day | Date(tentative) | Focus |
|---|---|---|
| W21 D0 | 2026-05-17 | Kickoff — ADR-0029 status verify Accepted(no-op + Implementation Note appended)+ ADR-0030 absorbed footnote preserved + `architecture.md v6 §5.5.2 + §5.5.2a NEW + §5.6 + §5.7` inline-tagged amendments + this `plan.md` + `checklist.md` + `progress.md` created(`status: active`)+ `session-start.md` §10 W21 row + §12 milestones row added |
| W21 D1 | 2026-05-18 | F1 — `DocumentDetail` + `OutlineNode` schemas + `GET /kb/{kb_id}/docs/{doc_id}` route + pytest ≥ 80% |
| W21 D1-D2 | 2026-05-18 to 2026-05-19 | F2 — `TraceSummary` + `TraceListResponse` schemas + `GET /traces?filter=...&since=...` route + pytest ≥ 80% |
| W21 D2-D4 | 2026-05-19 to 2026-05-21 | F3 — `/kb/[id]/docs/[docId]` 3-pane(outline + chunks + inspector with embedding viz feasibility verify;largest deliverable) |
| W21 D4-D5 | 2026-05-21 to 2026-05-22 | F4 — `/eval` 6-section refactor consuming existing W17 F3 RAGAs endpoints |
| W21 D5 | 2026-05-22 | F5 — `/traces` index list view + table + filter + date range(small) |
| W21 D5-D7 | 2026-05-22 to 2026-05-24 | F6 — `/traces/[traceId]` 3 viz modes(vertical default + waterfall + flame SVG components + toggle)|
| W21 D7 | 2026-05-24 | F7 — responsive + a11y + dark-mode re-check + Vitest expansion 45+ tests + Playwright route updates + COMPONENT_CATALOG.md + PAGE_INVENTORY.md notes |
| W21 D7 | 2026-05-24 | F8 — closeout(Gate verdict + retro + ADR-0029 Implementation Status appended + frontmatter `closed` + `session-start.md` hygiene + W22+ rolling-JIT trigger) |

**Day-by-day caveat**:dates tentative;real-calendar collapse is the W12-W20 pattern(actual ~1-2 days vs ~9 plan-day budget;W20 was 12× collapse,W21 likely 4-9× similar). The `start_date`/`end_date` frontmatter is a window, not a commitment. If overflow:F5/F6/F7/F8 absorb into D7;F3 is the long pole(3-pane layout + 3 NEW components)。

## 6. Dependencies on Prior Phase / Carry-overs Addressed

From `session-start.md` §11 + W20 retro carry-overs — W21 directly addresses:
- **ADR-0029 + ADR-0030 absorbed implementation** — the whole phase(F0 Status verify + F1-F7 implement the 2 ADRs scope per W19 F6)
- **Wave B backend foundation** — 2 backend items from W19 F2 §3.3(items 9 + 10)
- **W19 F1 §2.1 D5 D6 D7** — mockup audit findings for Doc Detail / Eval / Traces all addressed in F3 + F4 + F5 + F6 implementation
- **W20-closeout follow-up** — `<DisabledAffordance>` shared component reused across F3.5 embedding-vector + F4.5 Ops Metrics + F4.6 CRAG fields(if missing)+ any new Tier 2 leak surface

W21 does **NOT** address(stay Wave C / Tier 2 / W16 / future):
- ADR-0026 `/settings` 6-tab — **Wave C** W22(Settings tab not in Wave B scope)
- ADR-0027 `/users` 4-tab Tier 1.5 RBAC — **Wave C1** W22
- `/kb/[id]` **Access tab activate** — Wave C1
- Real-MSAL feature-flagged ship — **Wave C** W22(mock-auth default through Wave C per user 岔口 2)
- 2 NEW dependencies(Key Vault SDK + Entra Graph SDK)— **Wave C kickoff** per ADR-0017 Plan B sequencing decision
- CO16 Track A IT cred populate event + R-B1 closure(W16 F1 — external dependency;W21 unaffected)
- CO17 — 🚧 F1.5b Postgres-path runtime smoke + 🚧 F3.5b RAGAs live-verify(R8/Azure-key-bound;W21 doesn't touch — F4 uses existing W17 F3 endpoints via in-memory fallback testing)
- CO19 25% Beta cohort rollout activation(W16 F2)
- CO_F6a/b/c ACS email retry / BackgroundTasks / SPF-DKIM(Track A — W16 F1)
- CO_W15_F1_eval_set_v1 — `eval-set-v1.yaml` final still needs Chris's SME reference-answer labels(F4 surfaces this if real eval runs land,but doesn't unblock — Q14 hold)
- CO_W15_F3_aria_full_audit — full NVDA/JAWS/VoiceOver audit(Tier 2;W21 F7.2 = new-surface spot-check only)
- CO13 / AF3 code fix(ADR-0013 reserved)— unrelated to Wave B
- **Rule-of-3 wizard primitive promotion**(W20 F6.2 carry-over)— Wave B has **NO wizard surface**(doc detail + eval + traces 全部 non-wizard);defer to standalone refactor commit OR Wave C(wizard-heavy phase per /settings + /users)— per Karpathy §1.3 surgical,don't bundle unrelated refactor into Wave B
- ADR-0030 + ADR-0032 SKIPPED footnote — preserve per W19 F6 closeout(Wave A absorbed Dashboard + Topbar/Sidebar polish;Wave B absorbed Trace 3 viz + /traces list)

## 7. Plan Changelog

| Date | Change | Reason | Approver |
|---|---|---|---|
| 2026-05-17 | Initial draft + `status: active` + W21 folder created(`plan.md` + `checklist.md` + `progress.md`)| Chris directive at the W20-frontend-wave-a F9 closeout post-push session:「開 W21-frontend-wave-b kickoff」= the post-Wave-A-closeout(W20 PASS WITH SMOKE-USER-DEFERRED CAVEAT)implementation authorization per CLAUDE.md §10 R1 + R5(ADR-before-implement discipline). F1-F8 map onto ADR-0029 Option C `/kb/[id]/docs/[docId]` 3-pane + ADR-0030 absorbed Trace 3 viz + /traces list scope. `architecture.md v6 §5.5.2 + §5.5.2a NEW + §5.6 + §5.7` inline-tagged amendments + ADR-0029 status verify + `session-start.md` §10 W21 row + §12 milestones row + Update-history all land at this kickoff. | Chris(stakeholder + architecture decision owner)|

---

**Lifecycle reminder**:呢份 plan `status=active`(2026-05-17,per Chris directive「開 W21-frontend-wave-b kickoff」)。重大 deviation 入第 7 節 changelog(per R3)。Next-phase folder(W22+)**唔會** pre-create(per CLAUDE.md §10 R1 rolling-JIT)。
