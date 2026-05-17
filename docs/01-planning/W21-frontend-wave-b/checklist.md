---
phase: W21-frontend-wave-b
plan_ref: ./plan.md
status: active
last_updated: 2026-05-17
---

# Phase W21 — Checklist

> Atomic checkbox(每 item ≤ 0.5–2 hour effort)。Status:`active` from kickoff 2026-05-17(Chris directive「開 W21-frontend-wave-b kickoff」+ ADR-0029 Accepted + ADR-0030 absorbed = the authorization)。
> 每 item done 後 `[ ]→[x]` + commit ref;延後項標 🚧 + reason(per CLAUDE.md §10 sacred rule — 唔可以刪未勾選 item)。
> Deliverable ↔ ADR mapping:F0=ADR-0029 verify + ADR-0030 absorbed footnote + spec amend / F1=ADR-0029 §3 backend / F2=ADR-0030 absorbed backend / F3=ADR-0029 Decision §1 / F4=W17 F3 RAGAs consume / F5=ADR-0030 absorbed list / F6=ADR-0030 absorbed 3 viz / F7=cross-cutting / F8=closeout。

## F0 — Kickoff cascade(ADR-0029 verify Accepted + ADR-0030 absorbed footnote + spec amend — landed at kickoff)

- [ ] F0.1 `docs/adr/0029-doc-detail-3-pane-layout.md` Status verify **Accepted Option C**(no-op — W19 F6 `6a34a41` already accepted);Implementation Note appended at W21 kickoff(same convention as W20 F0 / W18 ADR-0024 Implementation Deliverables)
- [ ] F0.2 ADR-0030 SKIPPED footnote preserved per W19 F6 closeout(README.md footnote unchanged — Dashboard polish shipped Wave A F2;Trace 3 viz + /traces list ship Wave B F5+F6 = this phase)
- [ ] F0.3 `docs/architecture.md` — 4 inline-tagged §5 amendments landed kickoff(§5.5.2 KB Detail Chunks tab unchanged annotation + cross-ref to NEW §5.5.2a / §5.5.2a NEW Document Detail page 3-pane per ADR-0029 / §5.6 Eval Console 6-section refactor per Wave B / §5.7 Traces `/traces` index NEW + `/traces/[traceId]` 3 viz modes per ADR-0030 absorbed)
- [ ] F0.4 `docs/01-planning/W21-frontend-wave-b/{plan,checklist,progress}.md` created `status: active` 2026-05-17 kickoff
- [ ] F0.5 `docs/12-ai-assistant/01-prompts/01-session-start.md` §10 W21 row added(`active`)+ §12 milestones row added(`active`)+ Last-Updated + Update-history entry

## F1 — Backend `GET /kb/{kb_id}/docs/{doc_id}` enriched per ADR-0029(C01 + C03)

- [ ] F1.1 NEW Pydantic v2 schemas — `DocumentDetail`(15+ fields:doc_id / title / source / source_url / file_type / size_kb / pages / language / chunk_strategy / total_chunks / total_images / total_tokens / low_value_chunks / parse_duration_ms / embed_duration_ms / indexed_at / outline / image_refs)+ `OutlineNode`(level / title / chunk_count / page);file location `backend/api/schemas/listing.py`(or new `documents.py` if scope warrants)
- [ ] F1.2 NEW route `GET /kb/{kb_id}/docs/{doc_id}` in `backend/api/routes/documents.py` — `Depends(get_current_user)`-gated + outline reconstruction from `engine.list_chunks(kb_id, doc_id=doc_id)` `section_path` field + `image_refs` from W17 F4.1 `embedded_images_json` select extension(W20 F5.2 precedent)
- [ ] F1.3 Parse + embed duration seam — Wave B sources from `backend/persistence/ingestion_results/` if available,else `None`(forward-compat documented;parse_duration_ms / embed_duration_ms = forward-compat Tier 1 acceptable)
- [ ] F1.4 Backend pytest `backend/tests/api/test_documents_detail_route.py` — coverage ≥ 80% per CLAUDE.md §3.1 H6;6+ test cases(happy path / missing kb 404 / missing doc 404 / cross-user 404 / empty outline / empty image_refs)
- [ ] F1.5 mypy strict clean(same baseline as W20 F5.1)+ `pytest` pass
- [ ] F1.6 File header docstring on NEW schemas + route module

## F2 — Backend `GET /traces?filter=...&since=...` list per ADR-0030 absorbed(C07)

- [ ] F2.1 NEW Pydantic v2 schemas — `TraceSummary`(trace_id / timestamp / duration_ms / status: Literal['ok', 'error', 'crag_triggered'] / kb_id / query_preview / total_tokens / cost_usd / crag_iterations / stage_count)+ `TraceListResponse`(items / total / limit / offset);file location `backend/api/schemas/observability.py`(extend existing W18 baseline)
- [ ] F2.2 NEW route `GET /traces` in `backend/api/routes/debug.py`(reuse existing module — W20 F5 pattern)— `Depends(get_current_user)`-gated + Langfuse Postgres query layer per W17 F4 + filter seg(All / Errors / CRAG triggered)+ `?since=ISO8601` + `?kb_id=` + `?limit=` + `?offset=` pagination + default sort by `timestamp DESC`
- [ ] F2.3 Backend pytest `backend/tests/api/test_traces_route.py` — coverage ≥ 80%;5+ test cases(happy path / filter=errors / filter=crag_triggered / empty result / pagination + offset)
- [ ] F2.4 mypy strict clean + `pytest` pass
- [ ] F2.5 File header docstring on NEW schemas + extended route module

## F3 — `/kb/[id]/docs/[docId]` 3-pane Doc Detail per ADR-0029 Option C(C09 + C01 + C03)

- [ ] F3.1 NEW route `frontend/app/(app)/kb/[id]/docs/[docId]/page.tsx` — 3-pane layout(`grid-cols-[240px_1fr_380px]` baseline desktop + responsive breakpoint < 1200px collapses left pane to drawer + right pane to overlay)
- [ ] F3.2 NEW `frontend/lib/api/docDetail.ts` — typed client for `GET /kb/{kb_id}/docs/{doc_id}` consuming F1 backend(`useQuery(['kb', kbId, 'docs', docId])`);file docstring
- [ ] F3.3 NEW `<DocumentOutline>` component — sticky 240px left pane;heading hierarchy from `DocumentDetail.outline[]`;`<button>` per node + `aria-current="location"` active state via `IntersectionObserver` + click-to-jump scroll
- [ ] F3.4 NEW `<ChunkList>` component — 1fr center pane;cards per chunk with section_path + tokens + has_image badge + low_value badge + content preview(highlight `<mark>` for emphasized text)+ associated image thumbnail
- [ ] F3.5 NEW `<ChunkInspector>` component — sticky 380px right pane;metadata badges + section_path + prev/next chunk links + associated image card + **embedding vector preview**(24 sampled dims in 8-col grid + "+1000 more dims" tail caption);**feasibility verify**:if `chunk.embedding_vector` retrievable via Azure Search `select=*,content_vector`,render grid;else `<DisabledAffordance variant="p3-preview" showBadge reason="Embedding vector view: Tier 2 — request to enable" tier2Trigger="Azure Search vector field exposure">`
- [ ] F3.6 Header pipeline stages strip — 5 stages(Parse / Extract / Chunk / Embed / Index)+ timing data from `DocumentDetail.parse_duration_ms` + `embed_duration_ms`(other 3 stages forward-compat seam with "—" tooltip "Stage timing — Wave C+ instrumentation")
- [ ] F3.7 Image strip — horizontal scroll thumbnails `<ImageStripScroller>`;per-image badge(SHA256 hash + dim + size + low_value/dedup);click → `<ScreenshotModal>`(reuse Wave A pattern)
- [ ] F3.8 Navigation deep-link from `/kb/[id]` Documents tab row → `<Link href={\`/kb/${kbId}/docs/${docId}\`}>` per ADR-0029 + W20 F5 Documents tab preserved
- [ ] F3.9 Loading skeletons(`<DocDetailSkeleton>` per pane)+ error banners(per-pane destructive text)+ empty states(no outline → "No headings detected" placeholder)
- [ ] F3.10 Tokens 100%(`Grep '\[oklch'` = 0 preserved);`tsc --noEmit` exit 0;`next lint` clean
- [ ] F3.11 CLAUDE.md §3.2.1 H7 design fidelity — 對齊 `references/design-mockups/ekp-page-doc-detail.jsx PageDocDetail`(layout / spacing / typography / color tokens / interaction states / responsive / a11y);唔對齊嘅地方 STOP+ask per §5.7 H7 trigger 或標 🚧 deferred + reason
- [ ] F3.12 File header docstring + Vitest test scaffold deferred → F7.4 batches per W20 F1.7 / F3.15 precedent

## F4 — `/eval` Eval Console refactor per W17 F3 RAGAs(C09 + C06)

- [ ] F4.1 Rewrite `frontend/app/(app)/eval/page.tsx`(replaces W15 baseline)with 6 sections per plan §2 F4
- [ ] F4.2 Section 1 — 4-metric stat strip(Precision@5 + Recall@5 + Faithfulness + Answer Relevancy)from `EvalReport`;`<StatCard>` × 4 + loading skeleton + run-vs-baseline delta chips
- [ ] F4.3 Section 2 — Reranker Shootout table consume `POST /eval/shootout` → `ShootoutReport`;5 rerankers + 2 dropped(Voyage + ZeroEntropy per ADR-0012);Cohere v4.0-pro highlighted as production-locked baseline;per-row 4-metric chips + winner badge
- [ ] F4.4 Section 3 — Failed queries inspector;collapsible `<details>` per `EvalReport.failed_queries[]`;Expected vs Got side-by-side;jump-to-trace link → `/traces/[traceId]`
- [ ] F4.5 Section 4 — Recommendation card;text explaining current production config(`{reranker: 'cohere-v4', threshold: 0.70, NON_STICKY: true}` per W5 D4);advisory only
- [ ] F4.6 Section 5 — Ops Metrics card;p50/p95/p99 latency + avg cost/query;sourced from `EvalReport.ops_metrics`(if exposed,else `<DisabledAffordance>` "Ops metrics — Wave C+")
- [ ] F4.7 Section 6 — CRAG Insight card;trigger rate + avg iterations + qualitative reasoning;sourced from `EvalReport.crag_trigger_rate` + `crag_avg_iterations`(verify field;fallback to coverage-only if missing)
- [ ] F4.8 "Run eval" button → `POST /eval/run`(consume W17 F3) + "Run shootout" button → `POST /eval/shootout`(consume W17 F3);optimistic UI + skeleton during run
- [ ] F4.9 Loading skeletons + error banners + empty states first-class
- [ ] F4.10 Tokens 100%;`tsc` + `lint` clean;`[oklch`=0 preserved
- [ ] F4.11 CLAUDE.md §3.2.1 H7 design fidelity — 對齊 `references/design-mockups/ekp-page-eval.jsx PageEval`
- [ ] F4.12 File header docstring + Vitest test scaffold deferred → F7.4 batches

## F5 — `/traces` index list view per ADR-0030 absorbed(C09 + C07)

- [ ] F5.1 NEW route `frontend/app/(app)/traces/page.tsx`(replaces W18 thin index)— 9-col table view(Timestamp / Duration / Status / KB / Query preview / Tokens / Cost USD / CRAG iter / Stage count)
- [ ] F5.2 NEW `frontend/lib/api/traces.ts` — typed client for `GET /traces?filter=...&since=...` consuming F2 backend
- [ ] F5.3 Row click → `/traces/[traceId]`;filter seg(All / Errors / CRAG triggered)+ Date range picker(24h / 7d / 30d / custom)+ KB filter dropdown;persisted to `localStorage['ekp-traces-filter']`
- [ ] F5.4 Loading skeleton + empty state("No traces in selected range")+ error banner;pagination "Load more" + URL state(`?page=N&size=50`)
- [ ] F5.5 Tokens 100%;`tsc` + `lint` clean;`[oklch`=0 preserved
- [ ] F5.6 CLAUDE.md §3.2.1 H7 design fidelity — 對齊 `references/design-mockups/ekp-page-traces.jsx PageTraces`
- [ ] F5.7 File header docstring + Vitest test scaffold deferred → F7.4 batches

## F6 — `/traces/[traceId]` 9-stage + 3 viz modes per ADR-0030 absorbed(C09 + C07)

- [ ] F6.1 Refactor `frontend/app/(app)/traces/[traceId]/page.tsx`(W18 vertical list baseline preserved as default mode);viz mode toggle in header — `<ToggleGroup>` with 3 options(Vertical default + Waterfall + Flame)+ persisted to `localStorage['ekp-trace-viz-mode']`(W20 F3.7 citation-mode pattern)
- [ ] F6.2 NEW `frontend/components/traces/trace-viz-vertical.tsx` — extracted from W18 inline rendering per Karpathy §1.3 surgical(no logic change,just extract)
- [ ] F6.3 NEW `frontend/components/traces/trace-viz-waterfall.tsx` — SVG-based timeline bars per stage start + duration;per-stage tooltip;sequential layout(~80 lines per Karpathy §1.2 simplicity)
- [ ] F6.4 NEW `frontend/components/traces/trace-viz-flame.tsx` — SVG-based flame-graph stacked bars showing nested call depth(~100 lines);Wave A flat-trace data renders waterfall-equivalent;nested-stage support forward-compat for ADR-0020 Context Expander multi-step traces
- [ ] F6.5 Final response card preserved(W16 F5.5 baseline + W18 F8 header role attribute)
- [ ] F6.6 Loading skeleton + error banner unchanged
- [ ] F6.7 Tokens 100%;`tsc` + `lint` clean;`[oklch`=0 preserved
- [ ] F6.8 CLAUDE.md §3.2.1 H7 design fidelity — 對齊 `references/design-mockups/ekp-page-traces.jsx PageTraceDetail`(3 viz modes)
- [ ] F6.9 File header docstring on 3 NEW viz components + rewritten page + Vitest test scaffold deferred → F7.4 batches

## F7 — Cross-cutting:responsive + a11y + dark-mode + tests + COMPONENT_CATALOG + PAGE_INVENTORY

- [ ] F7.1 Responsive spot-check on new W21 surfaces — `/kb/[id]/docs/[docId]` 3-pane(< 1200px breakpoint;left drawer + right overlay)+ `/eval` 6 sections(mobile stacks vertical)+ `/traces` table(horizontal scroll < 1024px)+ `/traces/[traceId]` 3 viz modes(waterfall + flame SVG min-width);multi-viewport interactive browser smoke = user pre-Beta per W18-W20 carry-over
- [ ] F7.2 a11y spot-check on new W21 surfaces — 3-pane `<aside>` + `<main>` semantic landmarks + outline `<button aria-current="location">` + Toggle group `aria-pressed` viz mode state + viz SVG `role="img" aria-label`;full screen-reader audit Tier 2 / CO_W15_F3_aria_full_audit defer
- [ ] F7.3 Dark-mode `[oklch`=0 re-check — `Grep '\[oklch'` across `frontend/` = **0**(W15→W18→W20→W21 milestone preserved through 10+ commits);dark-mode interactive walkthrough = user pre-Beta smoke
- [ ] F7.4 Vitest expansion — W20 baseline 14 files/37 tests → W21 target **16-18 files / 45+ tests**(2-4 NEW test files batch:`doc-detail.test.tsx` + `eval-console.test.tsx` + `traces-list.test.tsx` + `trace-viz-modes.test.tsx`);per-file 1-3 tests covering render-smoke + key a11y attribute + interaction
- [ ] F7.5 Playwright E2E updates — `app-shell-path.spec.ts` +1 NEW(`/kb/[id]/docs/[docId]` 3-pane render)+ `golden-path.spec.ts` +2 NEW(/eval 6 sections + /traces table)+ `visual-baseline.spec.ts` +1-2 NEW snapshot(`/kb/[id]/docs/[docId]` 3-pane + `/traces/[traceId]` waterfall mode);interactive run via `PW_CHANNEL=chrome pnpm test:e2e` = user pre-Beta smoke
- [ ] F7.6 `docs/02-architecture/COMPONENT_CATALOG.md` Status rows appended — C01 + C03 + C06 + C07 + C09 W21 Wave B amendments
- [ ] F7.7 `references/design-mockups/PAGE_INVENTORY.md` Cn mapping flip — 4 W21-implemented routes status flipped「Wireable today / Wave B」→「Implemented W21 F#」:#6 `/doc-detail` / #8 `/eval` / #9 `/traces` / #10 `/traces/[traceId]`

## F8 — Phase closeout + W22+ rolling-JIT trigger

- [ ] F8.1 W21 phase Gate verdict landed(PASS / PARTIAL PASS / FAIL with explicit rationale per W18-W20 pattern)
- [ ] F8.2 W21 `progress.md` Retro — 7 sections written(What worked / What didn't & friction / Surprises / Decisions / Carry-overs to W22+ / Time tracking / Spec-ref alignment)
- [ ] F8.3 ADR-0029 status verified `Accepted`(F0 verify no-op at closeout)+ **Implementation Status section appended at W21 Wave B closeout**(same convention as W20 F9.3 — 3 ADRs appended Implementation Status sections);README row updated `Accepted` → `Accepted + Wave B implemented`
- [ ] F8.4 W21 `plan.md` + `checklist.md` + `progress.md` frontmatter `status: active` → `closed`
- [ ] F8.5 W22+ phase folder **NOT pre-created**(rolling-JIT per CLAUDE.md §10 R1)— kickoff candidates noted in `progress.md` Day-N retro section(W22-frontend-wave-c1 + W22b-frontend-wave-c2 SPLIT per W19 F4 §3.6 trigger / Rule-of-3 wizard primitive promotion W20 F6.2 carry-over / W16 F1-F4 Track A IT cred parallel)
- [ ] F8.6 `session-start.md` hygiene catch-up — §3 C01/C03/C06/C07/C09 status(W21 Wave B amendments)+ §10 W21 row(closed,Gate verdict)+ W22+ not-pre-created note + §11 carry-overs(W21-closed items + any new 🚧 deferrals)+ §12 milestones row + Last-Updated + Update-history
- [ ] F8.7 New OQ surfaced(if any) → sync `decision-form.md` per R4;ADR-0030 + ADR-0032 SKIPPED footnote preserved per W19 F6 closeout;embedding vector preview feasibility outcome recorded in F8.3 Implementation Status

---

## Cross-Cutting(must verify each commit + at closeout)

- [ ] CC1 Each commit references `progress.md` Day-N entry(R2)
- [ ] CC2 Component tag in commit message — F1=C01+C03 / F2=C07 / F3=C09+C01+C03 / F4=C09+C06 / F5=C09+C07 / F6=C09+C07 / F7=cross-cutting / F8=governance
- [ ] CC3 OQ status sync to `decision-form.md`(R4)— **no-op expected**:Q6 / Q15 / Q11 / Q8 / Q16 / Q20 all stay Open(W21 doesn't resolve any);ADR-0017 occurrences if any new R8 hit → log
- [ ] CC4 Risk register — no new W21 risk expected;`npx playwright install chromium` block stays under ADR-0017 Plan B realised(use `PW_CHANNEL=chrome`)
- [ ] CC5 CLAUDE.md §5.1 H1 check — Wave B authorized by ADR-0029 Accepted(W19 F6)+ ADR-0030 absorbed(W19 F6 SKIPPED-but-implemented decision);no other architectural change;F1-F7 implement amended §5.5.2a + §5.6 + §5.7;NO Tier 2 leak
- [ ] CC6 CLAUDE.md §5.2 H2 check — **no new dependency**(Wave B uses existing `psycopg>=3.2` + shadcn/ui + tokens;NO Key Vault SDK / NO Entra Graph SDK — those are Wave C)
- [ ] CC7 CLAUDE.md §3.2 conventions — `tsc --noEmit` exit 0 + `next lint` "No ESLint warnings or errors";no `any`;shadcn/ui only;design tokens via `tokens.ts`(`[oklch`=0);App Router only;Server Components default;Client Components have `"use client"` + docstring
- [ ] CC8 CLAUDE.md §3.1 conventions — Python 3.12+ + mypy strict clean + async by default + Pydantic v2 + structlog JSON + absolute imports;function length soft cap 50 lines;pytest + pytest-asyncio;coverage ≥ 80% on F1 `/kb/{id}/docs/{id}` + F2 `/traces` new endpoints
- [ ] CC9 CLAUDE.md §5.5 H5 — no secret committed;no hardcoded tenant/subscription/resource;`/traces` user_id scope via `get_current_user`(no PII;no plaintext-prompt logging changed)
- [ ] CC10 CLAUDE.md §5.4 H4 — Tier 2 boundary held:Embedding vector preview Tier 2 disabled affordance if Azure Search vector exposure expensive / Ops Metrics Tier 2 disabled affordance if EvalReport field missing / no GraphRAG / no multi-agent / no multi-tenancy / no multi-modal-search / no auto-sync / no fine-tune leak
- [ ] CC11 Karpathy §1.3 surgical — preserve existing chunks tab + Documents tab + W18 trace baseline unchanged in W21(only `/kb/[id]/docs/[docId]` NEW + `/traces` index NEW + `/traces/[traceId]` refactor with extract-only approach);additive content only;no "順手" refactor of adjacent code;Rule-of-3 wizard primitive promotion **DEFER**(Wave B has no wizard surface;don't bundle unrelated refactor into Wave B per Karpathy §1.3)
- [ ] CC12 CLAUDE.md §3.2.1 H7 — design fidelity gate at each F3/F4/F5/F6 surface(mockup 對齊 100% reproduction;唔對齊嘅地方 STOP+ask per §5.7 H7 trigger);frontend-only F-deliverables each have explicit H7 acceptance criterion item

---

**Lifecycle reminder**:呢份 checklist 衍生自 `plan.md` deliverables。新加 deliverable 必須先入 plan + §7 changelog,然後再加 checklist item。延後 item 標 🚧 + reason,**唔可以刪**未勾選 `[ ]`。
