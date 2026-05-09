---
phase: W14-admin-views
plan_ref: ./plan.md
status: draft
last_updated: 2026-06-10
---

# Phase W14 — Checklist

> Atomic checkbox(每 item ≤ 0.5–2 hour effort per W6 C10 calibration)。
> Status:`draft` 自 2026-06-10 W13 D5 cont F7 closeout cascade rolling-JIT。
> 全 unchecked 至 W14 D1 implementation start post stakeholder authorization。

## F1 — V2 Admin Dashboard refactor + CO_F5d-cont session-token mode

- [ ] F1.1 Stats card row(4 shadcn Card)at top of `frontend/app/admin/page.tsx`:KB count / doc count / query count / system status badge;data via TanStack Query(existing W12 baseline)or static placeholder if backend endpoint pending
- [ ] F1.2 Recent ingestion log(table OR list)below stats — last 10 ingestion events(doc_id / kb_id / status / timestamp);pull from existing observability API if available;empty state if none
- [ ] F1.3 Quick actions row(3 shadcn Button asChild + Link):Create KB → `/admin/kb/new` + Test query → `/chat` + View eval → `/eval`
- [ ] F1.4 Responsive layout — stats cards `grid-cols-1 sm:grid-cols-2 md:grid-cols-4`;Recent ingestion horizontal-scroll mobile;Quick actions stack vertical mobile
- [ ] F1.5 CO_F5d-cont session-token mode:extend `frontend/lib/auth/index.ts` with session-token branch(read `SESSION_TOKEN_STORAGE_KEY` from localStorage;return as bearer if present;else fall through to existing mock/MSAL switching);parallel to backend `dependency.get_current_user` session branch architecture;non-breaking if localStorage empty

## F2 — V3 KB List card grid refactor

- [ ] F2.1 `frontend/app/admin/kb/page.tsx` rebuild from plain-table(W12 F4.6 baseline)to card grid per design ref §2.3;Card shows kb_id / display_name / description / doc_count / last_indexed_at / status badge
- [ ] F2.2 Sort dropdown(shadcn Select)— sort by name / created_at / last_indexed_at
- [ ] F2.3 Filter Input search(name / description text match;optional W14 D2 if scope allows)
- [ ] F2.4 Create CTA(shadcn Button + Link)→ `/admin/kb/new`
- [ ] F2.5 Loading state(shadcn Skeleton)while TanStack Query fetching;empty state per design ref §3.4
- [ ] F2.6 Card click navigates to `/admin/kb/[id]` V4 detail
- [ ] F2.7 Responsive — `grid-cols-1 sm:grid-cols-2 md:grid-cols-3`

## F3 — V4 KB Detail 5-tab nav

- [ ] F3.1 `frontend/app/admin/kb/[id]/page.tsx` rebuild with shadcn Tabs primitive — 5 tabs:Documents / Chunks / Pipeline / Retrieval Testing / Settings
- [ ] F3.2 Documents tab — file listing table(doc_id / filename / format / chunk_count / status / uploaded_at)+ Upload Button → existing `/admin/kb/[id]/upload`(W12 F4.7 baseline preserved);empty state
- [ ] F3.3 Chunks tab — chunk listing(chunk_id / doc_id / section_path / token_count / preview);click chunk → shadcn Dialog modal w/ full chunk text in JetBrains Mono(custom Code block per design ref §4)
- [ ] F3.4 Pipeline tab — pipeline config visualization(reranker / LLM / CRAG threshold / top_k);read-only display Tier 1;inline tuning defer W15 if backend not support PATCH
- [ ] F3.5 Retrieval Testing tab — test query Textarea + Run Button → POST `/query`(non-streaming for testing simplicity);display retrieved chunks + relevance scores
- [ ] F3.6 Settings tab — display_name / description Input(editable;PATCH `/kb/[id]`)+ KB ID readonly + danger zone(Re-index Button + Delete Button with shadcn Dialog confirm)
- [ ] F3.7 Tab state via Next.js searchParams(`?tab=documents`)URL bookmark-friendly;default tab = Documents;tab change pushes URL
- [ ] F3.8 Stepper rule-of-3 evaluation:if Pipeline tab introduces wizard-style state machine(reset → re-test → save → re-index)= 3rd state-machine wizard;extract `frontend/components/ui/stepper.tsx` shared per design ref §4 Custom Step indicator listing;else inline retention preserved(W13 D4 decision)
- [ ] F3.9 Responsive — tabs collapse mobile via Select fallback OR Sheet drawer(stacking 5 horizontal tabs unworkable < md)

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
