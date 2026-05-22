---
bug_id: BUG-010
report_ref: ./report.md
checklist_ref: ./checklist.md
status: done
last_updated: 2026-05-22
---

# BUG-010 — Progress

> Bug-fix workflow per `PROCESS.md §4`。

## Day 1 — 2026-05-22

### Investigation

BUG-009 用戶驗證:KB `sample-kb-test-1` ingest 一個 docx,backend log 顯示 `images_uploaded: 8`,但 UI「Images 0」。逐項隔離:

- `GET /kb/sample-kb-test-1` → `total_screenshots: 0`(badge / stat 數據源)
- `GET /kb/sample-kb-test-1/images` → 正確回 **8** 個 item(每個有裸 blob URL)
- `curl <裸 blob URL>` → **403 AuthorizationFailure**(Azurite private container)
- code review:`update_metrics`(Protocol + InMemory + Postgres)+ `record_doc_event` 全無 `screenshots_delta`;`storage.py` docstring 早已明文 defer `total_screenshots`

→ 兩個 dormant gap:A(counter 未 wire)+ B(private blob 渲染唔到)。

### Decisions

- **D1** — 分類 Bug-fix BUG-010 Sev3。用戶 chat 確認開 BUG。
- **D2** — Gap B serving 方案:用戶 AskUserQuestion 揀 **backend proxy route**(blob 維持 private;local/cloud 一致;無 SAS lifecycle)。
- **D3** — Gap A delete/reindex screenshot decrement **不做** — dedup 跨文件共享需 ref-counting,維持原 `storage.py` documented future-tier 立場;只做 upload-increment。
- **D4** — proxy URL 用 `request.base_url` 砌**絕對 URL**(前端 / 後端跨 origin :3001↔:8000,relative URL 唔 work)→ 前端零改動。
- **D5** — 無 ADR:非架構/vendor/storage-layout 改動。

### Code changes

| 檔案 | 改動 | Gap |
|---|---|---|
| `kb_management/storage.py` | `KBStorageBackend` Protocol + `InMemoryKBBackend.update_metrics` 加 `screenshots_delta`(`total_screenshots` floor-at-0)| A |
| `kb_management/postgres_backend.py` | `update_metrics` SQL 加 `total_screenshots = GREATEST(0, total_screenshots + %s)` + param | A |
| `kb_management/service.py` | `record_doc_event` 加 `screenshots_delta` pass-through | A |
| `api/routes/documents.py` | `_run_ingest_pipeline` 傳 `screenshots_delta=result.images_uploaded`;NEW proxy route `GET /kb/{kb_id}/screenshots/{blob_name}`;`screenshot_proxy_url` helper;`list_kb_images` `url` rewrite;`_SCREENSHOT_BLOB_RE` | A + B |
| `ingestion/screenshots/uploader.py` | NEW `download_screenshot(connection_string, container, blob_name)` helper | B |
| `api/routes/query.py` | NEW `_proxy_citation_images` — rewrite citation `embedded_images` blob URL;wired 非-streaming `/query` + streaming `/query/stream` | B |
| `tests/api/test_documents_route.py` | +4 test(counter integration + proxy 200/404/422)| — |
| `tests/api/test_query_screenshot_proxy.py` | NEW — +3 test(`_proxy_citation_images`)| — |

### Verify gates

- `ruff check`(8 檔)→ **All checks passed**
- `mypy`(5 改動檔隔離)→ **Success: no issues**;`postgres_backend.py` 有 7 個 `_row_to_kb` tuple/dict error → **pre-existing**(line 172 喺改動範圍之前 = 證實 zero new;psycopg `dict_row` row_factory mypy 睇唔到 — 既有 tech debt,per §1.3 不順手修)
- `pytest tests/` → **930 passed, 25 skipped, 0 failed**(923 + 7 NEW BUG-010 test)
- **Runtime verify**:Azurite + backend(BUG-010 code)重啟 → `GET /kb/sample-kb-test-1/images` 個 `url` 已係 `http://127.0.0.1:8000/kb/sample-kb-test-1/screenshots/<sha>.png`;`curl` 嗰條 proxy URL → **HTTP 200 / image/png / 513068 bytes**(pre-fix = 403 AuthorizationFailure)

### Commits

_(見 commit footer — `fix(kb): ...` BUG-010)_

### Retro

- **Counter 嘅 forward-looking 性質**:`total_screenshots` 只喺 ingest 成功時 increment。現有 `sample-kb-test-1` 喺 fix 之前 ingest,`total_screenshots` 仍 0 —— 用戶 re-index 該文件(或 ingest 新文件)後 badge 先更新。Integration test 已證 wiring 正確。
- **Scope 紀律**:BUG-009 解上載 → 驗證時發現 counter + serving 兩個 dormant gap → 開 BUG-010(冇 silent 擴大 BUG-009)。chat 圖片本可另開 bug,但同屬一條 proxy route + 一個 query-path rewrite,fold 入 BUG-010 慳一次 round-trip。
- **隔離試驗價值**:逐個 curl(`/images` / proxy URL / KbStatus)定位「8 張圖上載成功但 UI 0」嘅真因 = counter 未 wire + private blob,而非 BUG-009 失敗。
- 🚧 delete/reindex 嘅 `total_screenshots` decrement 未做(dedup ref-counting,per `storage.py` 既有 documented future-tier 立場)。
