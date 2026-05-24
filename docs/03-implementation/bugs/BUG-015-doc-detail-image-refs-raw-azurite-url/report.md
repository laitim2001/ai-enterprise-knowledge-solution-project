---
bug_id: BUG-015
title: "Document Detail image_refs[].blob_url returns raw Azurite URL → browser-blocked private blob → 8 image cards show colored placeholder fallback instead of thumbnails"
severity: Sev3
status: done
reported: 2026-05-24
reporter: "Chris(chat 2026-05-24 W25 D2 — screenshot of /kb/sample-document-with-image-1/docs/dce-integration-platform-implementation-plan showing 8 image cards rendering as colored gradient placeholders despite total_images=8 + image_refs count=8 in backend payload)"
affects_components: [C08, C09]    # API Gateway backend route + Admin Console UI ImageThumb (Issue 1 H7 deviation scope addition)
spec_refs:
  - architecture.md §4.6     # screenshot blob serving + private-blob proxy
  - architecture.md §5.5.2a  # Document Detail 3-pane (ADR-0029 Wave B)
related: [BUG-009, BUG-010, BUG-011, BUG-012, BUG-013, BUG-014]
---

# BUG-015 — Document Detail image_refs[].blob_url is raw Azurite URL (browser-blocked)

> **Report version**:1.0(initial)
> **Triage approver**:AI self-triaged Sev3;Chris chat-acknowledged via 2026-05-24 W25 D2 screenshot of broken Document Detail page。

## 1. Symptom

User opens `/kb/sample-document-with-image-1/docs/dce-integration-platform-implementation-plan` Document Detail 3-pane page(ADR-0029 Wave B)。Top-bar stats correctly show `chunks_strategy: layout_aware`、`5 EXTRACT`、**`8 imgs`**、**`63 chunks`**、`0 vis`、`5 opened` — so backend aggregation knows 8 images exist。But the「Extracted Images」section renders **8 colored gradient placeholder cards** instead of actual thumbnails(per 2026-05-24 W25 D2 user screenshot)。

## 2. Reproduction Steps

1. Have at least one KB with `extract_embedded_images=True` containing a multi-image docx(e.g., `sample-document-with-image-1`)
2. Navigate to `/kb/<kb_id>/docs/<doc_id>` Document Detail page
3. Observe「Extracted Images」section above the Document outline / Chunks / Chunk inspector panels
4. **Expected**:N thumbnails(actual PNG/JPEG from Azurite blob storage)
5. **Actual**:N colored gradient placeholder cards(broken-image onError fallback identical to BUG-011 design)

**Reproduction reliability**:Always — every Document Detail page for any KB with images。Independent from BUG-013 Bearer-injection fix and BUG-014 rate-limit fix(those targeted `/kb/[id]?tab=images` KB Detail Images tab,a different route)。

## 3. Expected vs Actual

| 範疇 | Expected | Actual |
|---|---|---|
| `GET /kb/<kb_id>/docs/<doc_id>` payload `image_refs[i].blob_url` | Same-origin proxy URL — `/api/backend/kb/<kb_id>/screenshots/<sha>.png`(per BUG-012 fix pattern) | Raw Azurite URL — `http://127.0.0.1:10000/devstoreaccount1/ekp-kb-<kb_id>-screenshots/<sha>.png` |
| Frontend `<img src={image.blob_url}>` browser fetch | Same-origin proxy → backend auth + private blob fetch → 200 PNG | Cross-origin fetch to Azurite → blocked(no CORS / no SAS / private blob;BUG-009 設計初心 = proxy via `/api/backend/.../screenshots/<sha>.png` 帶 auth)→ `<img>` onError fallback → colored gradient placeholder |
| User experience | 8 thumbnails render | 8 broken-image placeholders |

## 4. Impact

**Production-relevant** — surface of every Document Detail page for any image-rich KB:
- W25 image-association deep-fix scope visible-output regression
- Citation viewer Wave B+ deep-link path likely affected too(同一 image_refs schema reuse)
- Inconsistent UX:KB Detail Images tab(`/kb/[id]?tab=images` via BUG-012 fix)works correctly → 8 thumbnails;Document Detail page(`/kb/[id]/docs/[doc_id]`)broken → 8 placeholders。Same data,two URL shapes,one shape broken。

**Affected users / scenarios**:every user opening Document Detail for any image-rich KB(Tier 1 baseline scenario — Drive Project docx 全部含 embedded images)
**Workaround available?**:None for end user(must fix backend URL emission)
**Data loss / corruption?**:None — backend aggregation correctness intact;only URL shape wrong
**Security implication?**:None — private blob remains private(raw Azurite URL is inaccessible anyway,user just sees broken image instead of correct thumbnail)
**Cost implication?**:None

## 5. Severity Justification

**Sev3** per `PROCESS.md §4.5`:user-visible image-rendering regression on Document Detail surface but text retrieval / Gate 1 / chat 文字 unaffected。No data loss、no security regression。Same tier as BUG-010/011/012/013/014 cascade。

## 6. Initial Diagnosis(root cause confirmed)

`backend/api/routes/documents.py:184` `get_kb_images()` aggregator(W20 F5.2 + BUG-012 fix)emits same-origin proxy URL via `screenshot_proxy_url()` helper:
```python
"url": screenshot_proxy_url(kb_id, blob_name)  # → /api/backend/kb/<kb_id>/screenshots/<sha>.png
```

But `backend/api/routes/documents.py:402-413`(approx)doc-detail aggregator builds `image_refs` from chunks' `embedded_images_json` and **passes through the raw `blob_url` field unchanged** from the chunk record:
```python
for chunk in chunks:
    raw = chunk.get("embedded_images_json") or "[]"
    images = json.loads(raw)
    for img in images:
        sha = img.get("checksum_sha256")
        if sha not in seen_images:
            seen_images[sha] = ImageRef(
                blob_url=img.get("blob_url"),  # ← raw Azurite URL from ingestion-time write
                ...
            )
```

The `embedded_images_json` field was written at ingestion-time by `orchestrator.ingest()` with `sha_to_url` lookup pointing to the **raw Azurite URL**(from `ScreenshotExtractor.extract` upload),NOT the proxy URL(which didn't exist at the time the schema field was designed)。

**Fix shape**:in doc-detail aggregation,re-derive the proxy URL from `sha`(same as `/kb/{id}/images` aggregator does via `screenshot_proxy_url`)— don't trust the raw `blob_url` stored in chunk records。Alternative = also re-derive in `/kb/{id}/images` aggregator(which is already doing it correctly post-BUG-012)。

```python
from api.routes.documents import screenshot_proxy_url  # BUG-012 helper

for chunk in chunks:
    ...
    for img in images:
        sha = img.get("checksum_sha256")
        blob_name = f"{sha}.png"  # extension always .png per BUG-009 + _SCREENSHOT_BLOB_RE
        if sha not in seen_images:
            seen_images[sha] = ImageRef(
                blob_url=screenshot_proxy_url(kb_id, blob_name),  # ← override with proxy URL
                ...
            )
```

非架構 / vendor / storage-layout 改動(URL shape derivation in aggregator only)→ **唔觸發 H1 / H2,唔需 ADR**。

## 7. Acceptance for Fix(checklist preview)

- [ ] Root cause confirmed:`image_refs[].blob_url` returns raw Azurite URL stored at ingestion time vs `/kb/{id}/images` aggregator correctly re-derives via `screenshot_proxy_url`
- [ ] **Fix** — `backend/api/routes/documents.py` doc-detail aggregator(`get_doc_detail`):override `blob_url` with `screenshot_proxy_url(kb_id, f"{sha}.png")`
- [ ] Tests — `tests/api/test_documents_detail_route.py` add:assert `image_refs[i].blob_url` startswith `/api/backend/` proxy prefix(not `http://127.0.0.1:10000/`)
- [ ] Verify gates — `pytest tests/` 0 fail vs current baseline 939
- [ ] Runtime verify — user reload `/kb/<kb_id>/docs/<doc_id>` → 8/8 thumbnails render in「Extracted Images」section + DevTools Network 8 × `/api/backend/.../screenshots/<sha>.png` 200 each

## 8. Alternatives Considered

| # | Alternative | Pros | Cons | Verdict |
|---|---|---|---|---|
| 1 | Re-ingest all KBs with new orchestrator writing proxy URLs to `embedded_images_json` | Aligns ingestion-time data with proxy-URL convention | Requires re-ingest of all existing KBs;blob_url drift between ingestion-era;coupling of presentation URL to ingestion-time schema is fragile | Rejected — schema-level fix |
| 2 | Add CORS headers to Azurite + frontend `<img>` fetch with `crossorigin=use-credentials` | Direct fetch works | Azurite emulator doesn't ship CORS configuration;production Azure Blob requires SAS tokens(more architecture);bypasses BUG-009 private-blob-proxy intent | Rejected — defeats privacy model |
| 3 | **Re-derive proxy URL in doc-detail aggregator**(this report)| Surgical;mirrors BUG-012 fix pattern in sister aggregator;zero schema migration | Aggregation duplicates URL derivation logic across 2 routes — single helper could be reused | **Selected**(reuses existing `screenshot_proxy_url` helper from BUG-012)|
| 4 | Frontend-side URL rewrite(detect raw Azurite + replace with proxy prefix)| No backend change | Frontend now coupled to backend URL convention;tests cross-cut | Rejected — backend should emit correct shape |

## 9. Report Changelog

| Date | Change | Reason | Approver |
|---|---|---|---|
| 2026-05-24 | Initial triage(Sev3)— W25 D2 user-eye fidelity verify session surfaced post-BUG-013/014 commit chain | Document Detail page broken-image cascade missing from BUG-009-014 scope | Chris(chat-confirm via Option 1 pick 2026-05-24)|

---

**Lifecycle reminder**:Sev3 → `postmortem.md` 不需要(only Sev1/Sev2 mandatory per `PROCESS.md §4.5`)。
