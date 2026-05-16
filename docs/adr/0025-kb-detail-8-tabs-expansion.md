# ADR-0025: KB Detail 5 → 8 tabs expansion(Images + Chunking Lab + Access)

**Date**: 2026-05-16
**Status**: **Accepted**(W19 F6 Chris approval 2026-05-16 — consensus decision, no option set)
**Approver**: Chris(Tech Lead + stakeholder)

## Context

`architecture.md v6 §5.5 KB Detail` 原 spec = **5 tabs**:Documents / Chunks / Pipeline / Retrieval Testing / Settings。`references/design-mockups/ekp-page-kb.jsx PageKbDetail`(per W19 F1 audit) implements **8 tabs**:Documents / Chunks / **Images** / **Chunking Lab** / Pipeline / Retrieval Testing / **Access** / Settings。

3 NEW tabs:

1. **Images tab**(`TabImages` in `ekp-page-kb-extras.jsx`)— image library per-KB with SHA256 dedup viz + chunk references + 4-stat strip(extracted / dedup / blob storage / low_value)+ filter seg(6 types incl. low_value)+ grid + ImageDetailModal。Backed by `MOCK_IMAGES` shape matching `backend/api/schemas/query.py:8 ImageRef`。
2. **Chunking Lab tab**(`TabChunkingLab`)— sample doc selector + chunking parameters(chunk size + overlap)+ 4-strategy comparison(`layout_aware` ✅ + `slide_based` ✅ + `heading_aware` ❌ NotImplementedError + `auto` ✅)+ output preview。Backed by `MOCK_CHUNKING_COMPARISON` — currently NO matching backend schema。
3. **Access tab**(`TabKbAccess` in `ekp-page-users.jsx`)— per-KB ACL with visibility radio(Private / Workspace / **Public Tier 2 disabled**)+ members & permissions table(Manage/Edit/Query per-KB role override)+ Add Entra group。**Hard dep on ADR-0027 RBAC acceptance**。

Per CLAUDE.md §5.1 H1 — KB Detail tab list 改動屬 architectural change(影響 §5.5 layout philosophy + C02 / C03 / C09 component scope) → requires ADR。

## Decision

**Adopt the 8-tab layout** for `/kb/[id]` per the prototype。 Amend `architecture.md v6 §5.5` with 3 new sub-sections:
- **§5.5.6 Images tab** — image library viz per-KB,reads `ImageRef` enriched with `used_in_docs[]` + `used_in_chunks[]` + `dedup_savings` cross-refs
- **§5.5.7 Chunking Lab tab** — strategy comparison dry-run on sample doc,reads `ChunkingComparison` schema(NEW)
- **§5.5.8 Access tab** — per-KB ACL with visibility + members + groups,reads `KbAcl` schema(NEW,depends on ADR-0027)

Tab ordering(post-amendment):Documents → Chunks → **Images** → **Chunking Lab** → Pipeline → Retrieval Testing → **Access** → Settings(content order matches prototype)。

Backend additions(per W19 F2 §3.2):
- `GET /kb/{kb_id}/images` → list[ImageRef enriched](Wave A blocker — ADR-0025 dep,~1d backend)
- `POST /chunking-preview` body={kb_id, sample_doc_id, strategy, chunk_size, overlap} → list[StrategyResult](Wave A blocker — ADR-0025 dep,~1.5d backend)
- `GET /kb/{kb_id}/acl` + `POST/PATCH/DELETE /kb/{kb_id}/acl/members` + `POST /kb/{kb_id}/acl/groups`(Wave C — depends on ADR-0027 Postgres `kb_acl` table)

**Wave A scope decision**(per W19 F2 §4):**ship 7-tab Wave A**(`-Access`),Access tab ships in Wave C alongside `/users` RBAC。**NOT recommend** Wave A 6-tab(`-Access -Chunking Lab`)— would defeat ADR-0025 acceptance + cost stakeholder confidence。

## Alternatives Considered

1. **Stay 5-tab per spec** — rejected。Prototype explicitly covers Images + Chunking Lab content + Access is a real per-KB ACL requirement per stakeholder Beta cohort scope。Cutting 3 tabs defeats the design-mockups premise(per user directive 2026-05-16「先把 design-mockups 的內容 先進行實作」).
2. **Split Images + Chunking Lab into separate `/kb/[id]/images` + `/kb/[id]/chunking-lab` pages** — rejected。Fragments KB Detail nav for Tier 1 scope;tabs preserve the unit-of-context(per ADR-0024 unified shell;single-route deeper exploration via tabs is the EKP pattern,Linear-grade)。
3. **Promote Images + Chunking Lab to Tier 2** — rejected。Backend Images endpoint enrichment(`/kb/{kb_id}/images`)is small(C01 + C02 + C03 already have the data via ingestion pipeline — just need to surface);Chunking Lab dry-run is moderate scope but high admin value(stakeholder needs to see "what would chunking look like with these params" before committing re-index)。
4. **Keep Access tab at workspace `/settings` → KB Permissions section instead of per-KB** — rejected。Per-KB ACL semantically belongs with the KB(prototype design choice mirrors permission inheritance flow:Workspace role → per-KB override)。Workspace-level KB permissions overview can be separate Wave C `/users` enhancement(deferred decision per F2 §6)。

## Consequences

**Positive**:
- KB admins gain self-service image library visibility(SHA256 dedup proof + low_value filter audit + chunk-reference cross-ref)+ chunking strategy preview(experiment before commit re-index)+ per-KB ACL management(replace global Workspace role for sensitive KBs)
- All 3 new tabs map cleanly to existing Cn ownership(C01 + C02 + C03)+ new Wave C `kb_acl` table per ADR-0027
- Backend additions are well-bounded:2 NEW endpoints for Wave A(Images list + Chunking preview)+ 1 endpoint group for Wave C(Per-KB ACL CRUD)

**Negative**:
- Wave A KB Detail ships **7-tab not 8**(`-Access`)until Wave C ADR-0027 RBAC lands;Access tab = disabled affordance「Tier 1.5 RBAC pending Wave C」for ~2 weeks
- Chunking Lab `POST /chunking-preview` dry-run requires extracting chunker code into a callable that takes a single doc(currently ingestion runs on full KB);refactor ~1.5d C01 work
- `ChunkingComparison` NEW schema needs design — Wave A scope sketch:`{strategies: [{id, supported, chunks_emitted, avg_tokens, median_tokens, p95_tokens, low_value_count, images_associated, sample_chunks}]}` matching prototype's `MOCK_CHUNKING_COMPARISON.strategies[]` shape

**Neutral**:
- `architecture.md v6 §5.5` 5-tab → 8-tab is inline-tagged amendment(doc version held — per the ADR-0024 / ADR-0023 / ADR-0022 W17/W18 precedent)— amendment lands at `W20-frontend-wave-a` phase kickoff(per CLAUDE.md §10 R5 ADR-before-implementation)
- `COMPONENT_CATALOG.md` C09 KB Detail row gets「8-tab per ADR-0025」status note at Wave A close

## References

- `architecture.md v6 §5.5` KB Detail(5-tab original spec)
- `references/design-mockups/ekp-page-kb.jsx`(`PageKbDetail` lines 140-235;8-tab navigation array lines 144-153)
- `references/design-mockups/ekp-page-kb-extras.jsx`(`TabImages` lines 4-98 + `TabChunkingLab` lines 257-350)
- `references/design-mockups/ekp-page-users.jsx`(`TabKbAccess` lines 390-519)
- `references/design-mockups/ekp-data.jsx`(`MOCK_IMAGES` lines 235-334 + `MOCK_CHUNKING_COMPARISON` lines 377-440)
- W19 F1 audit `docs/01-planning/W19-frontend-audit-and-adr-draft/audit/W19-mockup-jsx-audit.md` §2.1 D1
- W19 F2 backend gap map `docs/01-planning/W19-frontend-audit-and-adr-draft/audit/W19-backend-gap-map.md` §3.2 items 7-8 + §5 ADR-0025 row
- ADR-0024 unified shell IA(amends ADR-0015)— KB Detail tabs preserved through W18 restructure
- ADR-0027 /users Tier 1.5 RBAC(hard dep — Access tab implementation)
- ADR-0021 Retrieval Testing tab(preserved unchanged in 8-tab — Retrieval Testing remains 6th tab)
