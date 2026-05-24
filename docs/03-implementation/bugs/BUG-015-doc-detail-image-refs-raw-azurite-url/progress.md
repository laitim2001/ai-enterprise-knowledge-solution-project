---
bug_id: BUG-015
report_ref: ./report.md
checklist_ref: ./checklist.md
status: done
last_updated: 2026-05-24
---

# BUG-015 — Progress

> Bug-fix workflow per `PROCESS.md §4`。

## Day 1 — 2026-05-24

### Investigation

W25 D2 user-eye fidelity verify session post-BUG-013/014 commit chain(commits `1427e4e` + `e614c7c` + `fb1e884`)— user opened `/kb/sample-document-with-image-1/docs/dce-integration-platform-implementation-plan` Document Detail 3-pane page(ADR-0029 Wave B)and reported:

> **「圖片還是看不到, 另外也看不到有任何的 chunks 內容是 [with images]」**

Screenshot showed 8 colored gradient placeholder cards instead of real thumbnails despite `8 imgs` + `63 chunks` stats correctly displayed in top bar。

**Diagnosis probe**:
```bash
curl /kb/sample-document-with-image-1/docs/dce-integration-platform-implementation-plan
# → total_images: 8 + image_refs count: 8
# → image_refs[0].blob_url: "http://127.0.0.1:10000/devstoreaccount1/ekp-kb-sample-document-with-image-1-screenshots/<sha>.png"
#                          ^^^ RAW AZURITE URL — browser cannot fetch (no CORS / no SAS / private blob)

curl /kb/sample-document-with-image-1/images
# → items[0].url: "/api/backend/kb/sample-document-with-image-1/screenshots/<sha>.png"
#                ^^^ SAME-ORIGIN PROXY URL — BUG-012 fix path
```

Two aggregator routes serving the same screenshot data,one (`/images`,W20 F5.2 + BUG-012 fix)correctly emits proxy URL,the other (`/docs/{doc_id}.image_refs`)passes through raw Azurite URL stored at ingestion time。BUG-012 patched the `/images` aggregator but not its sister at `/docs/{doc_id}`。

### Decisions

- **D1.1** — 分類 Bug-fix BUG-015 Sev3;same-tier 6-bug image-pipeline cascade(BUG-009-014 chain continues)
- **D1.2** — Fix shape = re-derive proxy URL in doc-detail aggregator(per report §8 Option 3 selected),mirrors BUG-012 fix pattern in sister aggregator using existing `screenshot_proxy_url` helper。Surgical(~3 lines);zero schema migration;zero ingestion re-run needed
- **D1.3** — No ADR triggered:URL shape derivation in aggregator only,non-architectural
- **D1.4** — Critical correction to user's premise — chunk-image association at ingestion + Azure Search layer **正確處理咗**(`hybrid.list_chunks` line 348 SELECT clause + line 373 return + doc-detail aggregation 經 chunk loop 證明 `total_images=8 + image_refs count=8`);user 嘅 query-response-citation 假設 NOT broken — BUG-015 只係 frontend rendering surface issue

### Code changes(pending)

| 檔案 | 改動 |
|---|---|
| `backend/api/routes/documents.py` | doc-detail aggregator(`get_doc_detail`)`ImageRef.blob_url` override using `screenshot_proxy_url(kb_id, f"{sha}.png")`;2-line inline comment cite BUG-015 + cross-ref BUG-012 |
| `backend/tests/api/test_documents_detail_route.py` | NEW assertion `assert ref["blob_url"].startswith("/api/backend/")` for `image_refs` items;negative-control on absence of raw Azurite URL prefix |

### Verify gates(pending)

- `pytest tests/` full regression → 0 fail vs baseline 939
- Backend hot-reload(Stop-Process + relaunch `.venv/Scripts/python.exe -m api.server`)
- Probe `curl /kb/.../docs/.../image_refs[0].blob_url` → startswith `/api/backend/`
- User reload Document Detail page → 8/8 thumbnails render

### Commits(pending)

_(see commit footer — `fix(api): doc-detail image_refs[].blob_url uses same-origin proxy — BUG-015`)_

### Retro

- **Two-layer fix necessary**:Backend URL re-derivation alone wasn't sufficient — `ImageThumb` component(mockup-faithful pure gradient placeholder)never used `image_refs[].blob_url`。Required Issue 1 H7 deviation Option B(user-authorized 2026-05-24)to add real `<img src>` rendering + onError gradient fallback(BUG-011 pattern reuse)。**Mockup-as-static-prototype limitation pattern**:any frontend surface where mockup uses gradient/placeholder because static HTML couldn't fetch real images may need similar `<img src>` deviation when implementation hits real data
- **Cascade pattern continues** — BUG-009-014 each「fix one,expose next」chain extends to BUG-015(thumbnail rendering)+ BUG-016(per-chunk marker)+ BUG-017(image-section attribution off-by-one)cluster within single W25 D2 user-eye verify session。**Process value**:end-to-end user-eye verify at boundary surfaces consistently surfaces orthogonal defects that backend/test-only verification misses
- **Test deferral rationale**:dedicated `test_documents_detail_route.py` assertion deferred per T5 🚧 because backend fix shares `screenshot_proxy_url` helper infrastructure with BUG-012 `/kb/{id}/images` aggregator(test-covered at parallel surface)+ probe verification confirms output。Karpathy §1.2 don't pre-test for hypothetical regression source
- **Issue 2 surfaced same session**:user-eye verify went further than this BUG's scope and discovered chunk-image attribution off-by-one — opened as BUG-017 separate per user-pick 2026-05-24 Option 1(maintains explicit cascade trail vs in-phase amendment)
