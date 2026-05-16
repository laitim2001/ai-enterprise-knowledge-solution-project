# ADR-0029: /doc-detail 3-pane layout(outline + chunks + inspector)

**Date**: 2026-05-16
**Status**: **Accepted (Option C `/kb/[id]/docs/[docId]`)** — W19 F6 Chris pick 2026-05-16。Chris selected Option C(nested-under-KB URL,IA consistency with ADR-0024 flat URL convention)over Option A `/doc-detail/[kbId]/[docId]`(prototype default)和 Option B `/doc/[kbId]/[docId]`(shorter)
**Approver**: Chris(Tech Lead + stakeholder)

## Context

`architecture.md v6 §5.5.2` 原 spec — Chunk inspector at `/admin/kb/[id]/chunks/[doc_id]`(ADR-0024 flat → `/kb/[id]/chunks/[doc_id]`) — single-view doc chunks listing with chunk inspector side panel。

`references/design-mockups/ekp-page-doc-detail.jsx PageDocDetail`(per W19 F1 audit) implements **standalone `/doc-detail/[kbId]/[docId]` route with 3-pane layout**:

- **Left pane(sticky 240px)**:Document outline — heading hierarchy from layout_aware chunker(`MOCK_DOC_DETAIL.outline[]` with `{level, title, chunk_count, page, active?}`)。Section-scrollable + click-to-jump。
- **Center pane(1fr)**:Chunks list within active section — 5 sample chunks with section_path + tokens + has_image badge + low_value badge + content preview(highlighted with `<mark>` for `**bold**` per markdown)+ associated image thumbnail
- **Right pane(sticky 380px)**:Chunk inspector(`ChunkInspector` component)— metadata badges(chunk_index + tokens + embedded_images + low_value)+ section_path + prev/next chunk links + associated image card + **embedding vector preview**(24 dims shown in grid + "+1000 more dims" placeholder)
- **Header**:pipeline stages strip(5 stages — Parse / Extract / Chunk / Embed / Index with timing data from `MOCK_DOC_DETAIL`)
- **Image strip**:horizontal scroll thumbnails of all images in doc(SHA256 hash + dim + size + low_value/dedup badge)

Route topology change vs spec:
- spec was `/admin/kb/[id]/chunks/[doc_id]`(nested under KB Detail Chunks tab semantically)
- ADR-0024 flat → `/kb/[id]/chunks/[doc_id]`(URL flat,still nested-under-KB)
- Prototype uses **`/doc-detail/[kbId]/[docId]`**(standalone route at root)

Per W19 F2 §3.3 item 9:**NEW backend endpoint needed** — `GET /kb/{kb_id}/docs/{doc_id}` enriched with outline + parse_duration_ms + embed_duration_ms + total_images + image refs(currently only `GET /kb/{kb_id}/chunks?doc_id=...` available — chunks only,no doc-level metadata + outline)。

Per CLAUDE.md §5.1 H1 — `architecture.md v6 §5.5.2` route topology + layout change(single-view → 3-pane)= architectural → requires ADR。

## Decision

Adopt **3-pane layout `/doc-detail/[kbId]/[docId]`** per prototype。Amend `architecture.md v6 §5.5.2` to distinguish:

- **§5.5.2 KB Detail Chunks tab**(per ADR-0024 unchanged — `/kb/[id]` Chunks tab)— browse all chunks in KB with split-2 layout(chunks list + chunk preview)— **lighter weight**,for at-a-glance KB chunk inspection
- **§5.5.2a Document Detail page**(NEW — `/doc-detail/[kbId]/[docId]` 3-pane)— per-document deep inspection with outline + chunks-in-section + inspector with embedding viz — **heavier weight**,for chunk-level debugging + doc structure verification

Both surfaces coexist:**Documents tab row → `/doc-detail/[kbId]/[docId]`**(navigation per prototype `ekp-page-kb.jsx TabDocuments` line 285 `onClick → onNavigate("doc-detail", ...)`);Chunks tab is for KB-wide chunk browsing without doc-level context。

**Route name decision deferred to F6 Chris pick**:
- Option A:**`/doc-detail/[kbId]/[docId]`** per prototype — bare "doc-detail" route segment,decoupled from KB hierarchy
- Option B:**`/doc/[kbId]/[docId]`** — shorter route segment;reads "/doc/drive-manuals/d365_fno_gl_v2.4" cleaner
- Option C:**`/kb/[id]/docs/[docId]`** — keeps nested-under-KB URL hierarchy(closer to spec §5.5.2)+ more discoverable from `/kb/[id]/documents` Documents tab → click row navigates to `/kb/[id]/docs/[docId]`
- Recommended:**Option C** for IA consistency with ADR-0024 flat URL convention + KB-scoped grouping

Backend addition(per W19 F2 §3.3 item 9):
- `GET /kb/{kb_id}/docs/{doc_id}` → `DocumentDetail` schema(NEW)including:
  - `doc_id` / `title` / `source` / `source_url` / `file_type` / `size_kb` / `pages` / `language`
  - `chunk_strategy` / `total_chunks` / `total_images` / `total_tokens` / `low_value_chunks` / `parse_duration_ms` / `embed_duration_ms` / `indexed_at`
  - `outline: list[OutlineNode]` — list of `{level, title, chunk_count, page}` from layout_aware chunker
  - `image_refs: list[ImageRef]` — all images in this doc(reuse `ImageRef` from `schemas/query.py:8`)
- Effort:~1 day(C01 + C03 extend ingestion result persistence + new endpoint)

Embedding vector preview(Power-user spec per W19 F1):
- Frontend renders 24 sampled dims(8-col grid)from chunk embedding via existing `chunks/{chunk_id}` retrieval(no new backend) — verify Wave B implementation if Azure Search exposes embedding fields per chunk;if not(production data layer doesn't expose vectors by default for cost),defer to Tier 2 or surface as "raw embedding view" Power-user-only feature

## Alternatives Considered

1. **Stay single-view chunk inspector per spec §5.5.2** — rejected。Prototype's 3-pane(outline + chunks-in-section + inspector with embedding viz)is the Notion / Linear-grade information density EKP positions itself for(per ADR-0015 Dify-leaning aesthetic + per stakeholder W18 closeout IA gap signal)。Single-view loses the outline navigation + multi-chunk-in-section context that operators need for chunk-level debugging。
2. **Split into separate `/doc-outline/{docId}` + `/doc-chunks/{docId}` + `/doc-inspector/{chunkId}` 3 routes** — rejected。3-pane single-route is the unit-of-context(operator's mental model = "looking at this document")— fragmenting to 3 routes breaks the back/forward navigation + the sticky-pane synchronization。
3. **Drop embedding vector preview**(too power-user) — considered but not yet rejected。Embedding vector preview is high-value for chunk-level debugging(operator can see if related chunks have similar embedding patterns)but requires Azure Search to expose vectors via `select=*,content_vector` which may need permission tuning。**Wave B will verify feasibility + decide**:if cheap,keep;if expensive,Tier 2 promote。
4. **Route name `/doc-detail/[kbId]/[docId]`** vs `/doc/[kbId]/[docId]` vs `/kb/[id]/docs/[docId]` — strategic call deferred to F6 Chris pick。Recommended Option C(nested-under-KB)。

## Consequences

**Positive**:
- 3-pane layout matches operator chunk-level debugging mental model(outline left for navigation + chunks center for context + inspector right for detail)— consistent with Linear's issue detail / Notion's database row detail pattern
- Backend `GET /kb/{kb_id}/docs/{doc_id}` enriched endpoint encapsulates doc-level metadata(outline + image refs + timing data)— reusable for future surfaces(doc detail in Search results / doc citation expansion in Chat)
- `DocumentDetail` schema NEW + `OutlineNode` NEW are bounded additions(no impact on existing Document / Chunk / ImageRef schemas)
- Image strip in header surfaces cross-doc-image dedup visibility(useful for operators auditing why a screenshot appears across multiple manuals)

**Negative**:
- 3-pane layout at narrow viewports(< 1200px)needs responsive breakpoint:left pane可能 collapse to drawer / right pane可能 hide and reopen via button。Wave B implementation needs responsive design per @media query(prototype uses fixed grid `240px 1fr 380px` which would overflow on mobile)
- Embedding vector preview feasibility unverified — Wave B confirms;if expensive,UI shows "Embedding vector view: Tier 2 — request to enable" affordance(small frontend refactor)
- Route name decision opens FE refactor(`<Link href>` references + Playwright spec route refs + sidebar Tools potential entry)— small scope but careful per ADR-0024 W18 F3 lesson

**Neutral**:
- `architecture.md v6 §5.5.2` single-view spec → §5.5.2 + §5.5.2a dual-surface amendment inline-tagged at W21-frontend-wave-b kickoff
- `COMPONENT_CATALOG.md` C09 row gets「Doc Detail 3-pane per ADR-0029」status + new endpoint documented under C01 + C03
- Existing `lib/api/debug.ts` style typed client extends to `lib/api/docDetail.ts` for `/kb/{id}/docs/{docId}` consumption

## References

- `architecture.md v6 §5.5.2` Chunk inspector(single-view original spec)
- `references/design-mockups/ekp-page-doc-detail.jsx`(`PageDocDetail` lines 6-209;ImageThumb lines 212-254;ChunkInspector lines 257-380)
- `references/design-mockups/ekp-data.jsx`(`MOCK_DOC_DETAIL` lines 337-374 with outline + timing data)
- W19 F1 audit §2.1 D5(3-pane + route topology change)
- W19 F2 backend gap map §3.3 item 9(`GET /kb/{kb_id}/docs/{doc_id}` enriched endpoint)+ §5 ADR-0029 row
- ADR-0024 unified shell IA(route flattening convention `/admin/*` → `/kb/*`)
- ADR-0025 KB Detail 8-tab(Documents tab row → /doc-detail navigation)
- ADR-0021 Retrieval Testing tab(unrelated but informs the chunk-level inspection vocabulary)
