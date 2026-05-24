---
bug_id: BUG-016
title: "ChunkSummary listing schema strips embedded_images_json → Document Detail chunks panel cannot mark per-chunk [with images] affordance"
severity: Sev3
status: done
reported: 2026-05-24
reporter: "Chris(chat 2026-05-24 W25 D2 — screenshot of /kb/sample-document-with-image-1/docs/dce-integration-platform-implementation-plan showing chunks panel with no [with images] marker on any of 63 chunks despite 8 imgs total)"
affects_components: [C08, C09]    # API Gateway schema + Admin Console UI chunks panel
spec_refs:
  - architecture.md §5.5.2a       # Document Detail 3-pane (ADR-0029 Wave B)
  - architecture.md §3.5 + §3.6   # ChunkRecord schema + chunk-image association
related: [BUG-009, BUG-010, BUG-011, BUG-012, BUG-013, BUG-014, BUG-015]
---

# BUG-016 — ChunkSummary listing schema lacks per-chunk image marker affordance

> **Report version**:1.0(initial)
> **Triage approver**:AI self-triaged Sev3;Chris chat-acknowledged via 2026-05-24 W25 D2 screenshot of broken Document Detail chunks panel。

## 1. Symptom

`/kb/<kb_id>/docs/<doc_id>` Document Detail 3-pane page(ADR-0029 Wave B)— Chunks panel(center pane)lists all 63 chunks of the document but **none** show a `[with images]` marker / badge / affordance, despite 8 images existing across the doc(`total_images=8`)+ chunks individually carrying `embedded_images_json` field at Azure Search storage layer。

## 2. Reproduction Steps

1. Have at least one KB with `extract_embedded_images=True` containing a multi-image docx with images attached to specific section chunks(NOT TOC / NOT version-history chunks per W25 F1 chunker ADR-0033 filter)
2. Navigate to `/kb/<kb_id>/docs/<doc_id>` Document Detail page
3. Observe Chunks panel(center pane,below「Extracted Images」section)
4. **Expected**:chunks that own embedded images marked with `[with images]` / image-icon badge / similar affordance — user can visually identify which sections contain pictures
5. **Actual**:**zero chunks** display any image-related marker — all 63 chunks look identical regardless of image association

**Reproduction reliability**:Always — every Document Detail page for any KB with images。Independent from BUG-015(both surfaces broken in same page,but orthogonal causes:BUG-015 = URL shape;BUG-016 = field stripped at schema layer)。

## 3. Expected vs Actual

| 範疇 | Expected | Actual |
|---|---|---|
| `GET /kb/<kb_id>/documents/<doc_id>/chunks` payload per-chunk | Field `embedded_image_count: int`(or boolean `has_embedded_images: bool`)indicating per-chunk image attachment | No image-related field on ChunkSummary — frontend has no signal to mark `[with images]` |
| Frontend chunks panel rendering | Chunks owning images visually distinguished(badge / count / icon) | All chunks render identically;impossible to identify image-owning chunks from list |
| User mental-model alignment | User clicks a `[with images]` chunk → Chunk Inspector(right pane)shows the attached images + text | User has no path to discover which chunk owns which image without random click-through |

## 4. Impact

**Production-relevant** — surface of every Document Detail page for any image-rich KB:
- W25 image-association deep-fix scope visible-output regression
- Chat citation workflow Wave B+:if downstream UX wants to show「chunk had images attached → citation should preview them」,frontend needs this signal in the chunks listing
- Information architecture broken:Document Detail's 3-pane design intent = outline(left)+ chunks(center)+ inspector(right);chunks panel is supposed to show **per-chunk metadata** so user can drive selection → without image marker,2 of 3 panes are decoupled

**Affected users / scenarios**:every user opening Document Detail for any image-rich KB
**Workaround available?**:None for end user;backend dev can `curl /kb/<id>/docs/<doc_id>` to see `total_images=8 + image_refs[]` aggregated payload to confirm data exists,but the chunks panel UI cannot surface it
**Data loss / corruption?**:None — backend chunks have `embedded_images_json` populated correctly at Azure Search;only listing schema strips it
**Security implication?**:None
**Cost implication?**:None — adding `embedded_image_count: int` to listing schema is backend-cheap(derivable from existing JSON string),no extra Azure Search query

## 5. Severity Justification

**Sev3** per `PROCESS.md §4.5`:user-visible UI affordance regression on Document Detail surface but text retrieval / Gate 1 / chat 文字 / chat citation (separate path,W25 F5 D1 deliverable verifying) unaffected。No data loss、no security regression。Same tier as BUG-010-015 cascade。

## 6. Initial Diagnosis(root cause confirmed)

`backend/api/schemas/listing.py:30-46`(approx)`ChunkSummary` schema:
```python
class ChunkSummary(BaseModel):
    """Chunk-level metadata for doc detail view (per F5.1.2; chunk_text excluded)."""
    chunk_id: str
    chunk_index: int
    chunk_total: int
    chunk_title: str
    section_path: list[str]
    enabled: bool
    low_value_flag: bool
    # ← NO embedded_images_json (intentionally stripped per W16 F5.1.2)
```

Docstring header comment:「Schemas surface Beta-relevant fields only(chunk_text + embedded_images excluded — Beta client doesn't need bulk text in listing endpoints)」(W16 F5.1.2 originally)。

BUT — W20 Document Detail 3-pane(ADR-0029 Wave B) **needs** per-chunk `with images` affordance as part of the chunks-panel interaction model。The W16-era「listing endpoints exclude bulk fields」decision was sound for its time(KB Detail Chunks tab pre-W20),but **didn't anticipate** W20's 3-pane interaction needing per-chunk image marker。

`backend/retrieval/hybrid.py:320-380`(approx)`list_chunks` actually requests + returns `embedded_images_json` correctly(SELECT clause line 348;return at line 373 `str(item.get("embedded_images_json") or "[]")`)— so **raw chunks data has the field**;route handler converts to `ChunkSummary` via pydantic model_dump which **drops** unknown / non-schema fields。

**Fix shape**:add a thin `embedded_image_count: int` field to `ChunkSummary` schema + derive it in the route handler by `len(json.loads(raw_chunk["embedded_images_json"] or "[]"))`。Backend-cheap(parse already-fetched JSON string),frontend-actionable(non-zero count → mark `[with images]`)。Don't add full `embedded_images_json` to listing schema — that's the W16 F5.1.2 decision to preserve(bulk JSON not needed in listing)。

```python
# backend/api/schemas/listing.py
class ChunkSummary(BaseModel):
    """..."""
    chunk_id: str
    ...
    low_value_flag: bool
    embedded_image_count: int = 0  # NEW BUG-016 — non-zero → frontend marks [with images]

# backend/api/routes/documents.py or chunks listing aggregator
import json
chunks = await engine.list_chunks(kb_id, doc_id)
chunk_summaries = []
for chunk in chunks:
    raw = chunk.get("embedded_images_json") or "[]"
    try:
        images = json.loads(raw) if isinstance(raw, str) else raw
        count = len(images) if isinstance(images, list) else 0
    except (json.JSONDecodeError, TypeError):
        count = 0
    chunk_summaries.append(ChunkSummary(..., embedded_image_count=count))
```

非架構 / vendor / storage-layout 改動(additive field on listing schema)→ **唔觸發 H1 / H2,唔需 ADR**。

## 7. Acceptance for Fix(checklist preview)

- [ ] Root cause confirmed:`ChunkSummary` intentionally strips `embedded_images_json` per W16 F5.1.2,but W20 Document Detail 3-pane needs per-chunk image affordance — broken assumption
- [ ] **Fix backend** — `backend/api/schemas/listing.py`:add `embedded_image_count: int = 0` to `ChunkSummary`;backend chunks listing aggregator derives via JSON parse
- [ ] **Fix frontend** — `frontend/app/(app)/kb/[id]/docs/[docId]/...` chunks panel:mark chunks with `embedded_image_count > 0`(badge / `[with images]` text / image icon — pick consistent with mockup per H7)
- [ ] Tests — backend `tests/api/test_documents_detail_route.py`(or chunks listing test):assert `embedded_image_count` field present on `ChunkSummary` items;value matches expected count for fixture chunks
- [ ] Verify gates — `pytest tests/` 0 fail vs current baseline 939
- [ ] Runtime verify — user reload `/kb/<kb_id>/docs/<doc_id>` → chunks owning images marked visually in Chunks panel(N marker count matches `total_images` divided by chunk attachment distribution)
- [ ] H7 self-verify — frontend marker design aligned with mockup spec(if mockup has `[with images]` specific design;else propose surface design + mockup line ref for user confirm)

## 8. Alternatives Considered

| # | Alternative | Pros | Cons | Verdict |
|---|---|---|---|---|
| 1 | Add full `embedded_images_json: str` to `ChunkSummary` | Frontend gets richer per-chunk image data | Violates W16 F5.1.2「listing endpoints don't ship bulk fields」decision;payload bloat across N chunks;frontend mostly only needs count for marker | Rejected — keeps original design intent |
| 2 | Add `has_embedded_images: bool` instead of count | Boolean is simplest signal | Loses count information(user can't see「this chunk has 3 images」);count derivation is same effort | Rejected — count strictly more useful |
| 3 | **Add `embedded_image_count: int`**(this report)| Surgical;frontend-actionable;preserves W16 F5.1.2 bulk-exclusion intent;backend-cheap derivation | Slight schema additive change(forward-compatible — default 0) | **Selected** |
| 4 | Frontend re-fetches `embedded_images_json` per chunk via separate `/chunks/{chunk_id}` endpoint | Avoids listing schema change | N+1 query problem(63 extra requests per Document Detail page);405 errors per BUG-016 D2 probe — endpoint doesn't exist for individual chunk fetch | Rejected — performance + missing endpoint |

## 9. Report Changelog

| Date | Change | Reason | Approver |
|---|---|---|---|
| 2026-05-24 | Initial triage(Sev3)— W25 D2 user-eye fidelity verify session surfaced jointly with BUG-015 post-BUG-013/014 commit chain | Document Detail page chunks-panel affordance missing from W16 F5.1.2 listing-schema decision | Chris(chat-confirm via Option 1 pick 2026-05-24)|

---

**Lifecycle reminder**:Sev3 → `postmortem.md` 不需要(only Sev1/Sev2 mandatory per `PROCESS.md §4.5`)。
