---
phase: W14-admin-views
plan_ref: ./plan.md
status: active
last_updated: 2026-06-10
---

# Phase W14 — Checklist

> Atomic checkbox(每 item ≤ 0.5–2 hour effort per W6 C10 calibration)。
> Status:`active` 自 2026-06-10 W14 D1 implementation start(real-calendar same-day collapse cycle 3 of 4 per pivot momentum continuation of W13 closeout)。

## F1 — V2 Admin Dashboard refactor + CO_F5d-cont session-token mode

- [x] F1.1 Stats card row(4 shadcn Card)at top of `frontend/app/admin/page.tsx`:**deviation logged plan §7 changelog 2026-06-10 (D1)** — KB count / doc count / **chunks count(W12 baseline preserved)** / system status badge(plan said "query count" but no backend endpoint readily available;chunks count 仍 useful Tier 1 ingestion KPI;Karpathy §1.2 simplicity-first 不 add backend endpoint just for stat card)
- [x] F1.2 Recent ingestion log → **deviation logged plan §7 changelog 2026-06-10 (D1)** — 采「Failed ingestion」derived from `kbApi.list .failed_documents` arrays(W7 baseline data structure already returns failure rows per KB);empty state w/ CheckCircle2 「No failed ingestion」;Skeleton placeholder during loading;Table 顯示 first 10 failures w/ KB / Doc id / Stage Badge / Error message
- [x] F1.3 Quick actions row(3 shadcn Button outline asChild + Link):Create KB → `/admin/kb/new` w/ Plus icon + Test query → `/chat` w/ MessageSquare icon + View eval → `/eval` w/ FlaskConical icon;ActionButton component pattern(icon + label + description)
- [x] F1.4 Responsive layout — stats cards `grid-cols-1 sm:grid-cols-2 md:grid-cols-4`;Failed ingestion table horizontal-scroll mobile via `<table>` natural overflow;Quick actions `grid-cols-1 sm:grid-cols-3`;Section spacing `space-y-8` per design ref §3.7
- [x] F1.5 CO_F5d-cont session-token mode:`SESSION_TOKEN_STORAGE_KEY` 移去 `lib/auth/index.ts`(canonical auth domain;`lib/api/auth.ts` re-exports to break api-client → auth → api/auth circular import);**`getBearer()` 加 session branch BEFORE mock/MSAL fork** via `readSessionBearer()` helper(reads localStorage;returns `{scheme,token}` if present;else null fall-through);non-breaking when localStorage empty;defensive `try/catch` for privacy/sandbox modes;parallel to backend `dependency.get_current_user` session branch architecture(W13 D5 F5.6)

## F2 — V3 KB List card grid refactor

- [x] F2.1 `frontend/app/admin/kb/page.tsx` rebuild from plain-table(W12 F4.6 baseline)to card grid;Card shows kb_id(font-mono small)+ name(CardTitle line-clamp-1)+ description(CardDescription line-clamp-2 min-h)+ doc_count + chunks_count + last_indexed_at + derived status badge
- [x] F2.2 Sort dropdown(shadcn Select)— **deviation logged plan §7 changelog 2026-06-10 (D2)** — sort by name / **last_indexed(recent first;null at end)** / **documents(most first)**;`created_at` plan-literal 缺乏 KbStatus API field;采 3 useful operational dimensions
- [x] F2.3 Filter Input search(name / kb_id / description text match case-insensitive)+ Search lucide icon as adornment;state-driven via useMemo + useState;empty filter shows all
- [x] F2.4 Create CTA(shadcn Button asChild + Link)at page header right + Plus lucide icon → `/admin/kb/new`;empty state secondary Create CTA
- [x] F2.5 Loading state — `KbGridSkeleton`(6 Skeleton cards w/ matching shape per design ref §3.5);Empty state — `KbEmpty` per design ref §3.4(Database / Search icon + heading + subtext + CTA);Error state — destructive boundary preserved from W12 baseline
- [x] F2.6 Card click navigates to `/admin/kb/[id]` V4 detail — **deviation logged plan §7 changelog 2026-06-10 (D2)** — entire Card wrapped in Link(best accessibility + middle-click new tab support);Upload secondary action dropped from Card to avoid nested-anchor HTML invalid(user navigates into KB detail page for Upload)
- [x] F2.7 Responsive — `grid-cols-1 sm:grid-cols-2 md:grid-cols-3`;Toolbar `flex-col sm:flex-row` collapse mobile;Header CTA stack `flex-col sm:flex-row` mobile

## F3 — V4 KB Detail 5-tab nav

- [x] F3.1 `frontend/app/admin/kb/[id]/page.tsx` rebuild with shadcn Tabs primitive(W12 D3 installed)— 5 tabs:Documents / Chunks / Pipeline / Retrieval Testing / Settings;TabsTrigger w/ lucide icon + label;header 加 back-to-KBs Link + Upload CTA
- [x] F3.2 Documents tab — **deviation logged plan §7 changelog 2026-06-10 (D3)** — backend `GET /kb/{id}/documents` 仍 W2 stub 501;采 stats card row(total docs/chunks/storage)+ existing kb.failed_documents list + BackendStubNote + Upload CTA(empty/dashed state pattern per design ref §3.4)
- [x] F3.3 Chunks tab — **deviation logged plan §7 changelog 2026-06-10 (D3)** — backend `GET /kb/{id}/documents/{id}/chunks` 仍 W2 stub 501;采 stats card(chunks + screenshots)+ BackendStubNote + cross-reference Card directing user to Retrieval Testing tab(citation cards 提供 chunk_id / section_path drill-down via其他 path)
- [x] F3.4 Pipeline tab — **deviation logged plan §7 changelog 2026-06-10 (D3)** — read-only ConfigRow display(Indexing card + Retrieval card);inline tuning defer W15+;Pipeline 唔 introduce wizard state machine = F3.8 Stepper rule-of-3 trigger NOT fired
- [x] F3.5 Retrieval Testing tab — Textarea + Run Button → `streamQuery` SSE generator + AbortController;collect citations + answer + reranker_used;Synthesized answer Card + Retrieved chunks list w/ chunk_title / doc_title / section_path / relevance_score Badge;refused / error states;ApiError envelope branching via toast.error
- [x] F3.6 Settings tab — **deviation logged plan §7 changelog 2026-06-10 (D3)** — name + description display-only(`kbApi.patchSettings` 只 takes `Partial<KbConfig>`);Identity card readonly + Indexing config card editable(embedding_model + dimension + chunk_strategy Select + top_k + rerank_k);Save persists via PATCH;CO_W15 follow-up trigger noted for backend name/description PATCH endpoint
- [x] F3.7 Tab state via Next.js searchParams(`?tab=documents`)URL bookmark-friendly;`activeTab` derived from `searchParams.get('tab')` w/ fallback to 'documents';`handleTabChange` pushes new URL via `router.push` w/ `scroll: false`(prevents scroll jump on tab switch)
- [x] F3.8 Stepper rule-of-3 evaluation:**NOT triggered** — Pipeline tab implemented read-only ConfigRow display 唔 introduce wizard state machine;Pipeline wizard W12 + Register W13 仍 = 2 active state-machine wizards;**inline retention preserved** per W13 D4 decision;next wizard usage emergence trigger preserved for W15+ OR future
- [x] F3.9 Responsive — TabsList wrapped in `overflow-x-auto` div for mobile horizontal-scroll(simpler than Sheet/Select fallback per Karpathy §1.2);Header `flex-col sm:flex-row` collapse;StatCards `grid-cols-1 sm:grid-cols-2 sm:grid-cols-3` natural responsive
- [x] Danger zone Re-index/Delete shadcn Dialog confirm + structured backend status disclosure + toast info「pending backend stub」 — non-blocking UI wire test;`DangerAction` reusable component pattern

## F4 — Cross-cutting refactors + token cleanup

- [ ] F4.1 Stepper rule-of-3 trigger evaluation(F3.8 outcome);if extracted,refactor W12 F4.9 KB wizard + W13 F4 Register + F3 Pipeline tab to consume shared component
- [ ] F4.2 Sidebar consistency review — verify `bg-muted/40` + active state `bg-muted text-foreground` consistent across all admin pages(W12 F4.1 baseline)
- [ ] F4.3 Token consumption audit — `grep oklch frontend/app/admin/` should remain 0 hits(W12 D2 strict baseline);fix any leak Karpathy §1.3 surgical
- [ ] F4.4 Cross-view UserMenu / Breadcrumb behavior verify(no regression vs W12 F4.2 baseline)

## F5 — Phase Gate closeout + W15 phase folder kickoff

- [ ] F5.1 W14 phase Gate verdict landed(PASS / PARTIAL PASS / FAIL with explicit rationale per W12 F5.1 + W13 F7.1 pattern)
- [ ] F5.2 W14 progress.md retro 7 sections complete(What worked / What didn't / Surprises / Decisions / Carry-overs / Time tracking / Spec ref alignment)
- [ ] F5.3 `docs/01-planning/W15-polish-closeout/{plan,checklist,progress}.md` draft per architecture.md v6 §5.6-§5.7(V5 Eval + V6 Debug)+ design ref §6 W15 scope
- [ ] F5.4 W14 plan + checklist + progress frontmatter status flipped to `closed`
- [ ] F5.5 No new OQ surface expected;if surface → sync to decision-form.md per R4

---

## Cross-Cutting

- [ ] Each commit references `progress.md` Day-N entry(R2)
- [ ] Component tag in commit message per CC-1(C09 / C02 / C01 / C03 / C11)
- [ ] OQ status sync to `decision-form.md`(R4)— no W14 critical OQ expected
- [ ] Risk register update if any new risk surface
- [ ] CLAUDE.md §5.1 H1 boundary check:no architectural change without ADR(W14 scope already covered by ADR-0014 + ADR-0015 + ADR-0016)
- [ ] CLAUDE.md §5.2 H2 boundary check:no new vendor / dependency without ADR
- [ ] CLAUDE.md §3.2 frontend conventions check:no `any` / no @ts-ignore / shadcn/ui only / tokens consumption verified(grep oklch=0 across all touched files)
- [ ] CLAUDE.md §5.5 H5 security check:no secret commit;session token storage cipher review pending Beta hardening

---

**Lifecycle reminder**:呢份 checklist 衍生自 `plan.md` deliverables。新加 deliverable 必須先入 plan + changelog,然後再加 checklist item。
