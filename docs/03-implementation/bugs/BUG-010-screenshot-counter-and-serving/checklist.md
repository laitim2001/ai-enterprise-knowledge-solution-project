---
bug_id: BUG-010
report_ref: ./report.md
status: done            # in-progress | done
last_updated: 2026-05-22
---

# BUG-010 — Checklist

> Derived from `report.md §7 Acceptance for Fix`。延後項標 🚧 + reason(per CLAUDE.md sacred rule — 唔可以刪未勾 `[ ]`)。

## Fix

- [x] **T1** — Root cause confirmed:Gap A(`update_metrics`/`record_doc_event` 冇 `screenshots_delta`)+ Gap B(private Azurite container → 裸 blob URL 403)
- [x] **T2** — Gap A:`kb_management/storage.py` — `KBStorageBackend` Protocol `update_metrics` + `InMemoryKBBackend.update_metrics` 加 `screenshots_delta: int = 0`(`total_screenshots` floor-at-0 read-modify-write)
- [x] **T3** — Gap A:`kb_management/postgres_backend.py` `update_metrics` — SQL 加 `total_screenshots = GREATEST(0, total_screenshots + %s)`
- [x] **T4** — Gap A:`kb_management/service.py` `record_doc_event` 加 `screenshots_delta` 參數 + pass-through
- [x] **T5** — Gap A:`api/routes/documents.py` `_run_ingest_pipeline` 成功路徑 `record_doc_event(..., screenshots_delta=result.images_uploaded)`
- [x] **T6** — Gap B:新 route `GET /kb/{kb_id}/screenshots/{blob_name}` — `Path(...).name` + `_SCREENSHOT_BLOB_RE` sanitize → `kb_id_to_screenshot_container` → `download_screenshot`(NEW helper in `screenshots/uploader.py`)→ `Response`(bytes + content-type);404 if blob absent / 422 bad name
- [x] **T7** — Gap B:`documents.py` `list_kb_images` — `KbImageItem.url` → `screenshot_proxy_url(request, kb_id, blob_url)` 絕對 proxy URL(`request.base_url` base)
- [x] **T8** — Gap B:chat citation image URL — `query.py` `_proxy_citation_images` rewrite,covers 非-streaming `/query`(`build_citations` 之後)+ streaming `/query/stream`(`event_serializer` 攔截 `citation` event)
- [x] **T9** — Tests:`test_documents_route.py` +4(counter integration + proxy 200/404/422);NEW `test_query_screenshot_proxy.py` +3(`_proxy_citation_images`)
- [x] **T10** — Runtime verify:Azurite + backend 重啟 → `GET /kb/sample-kb-test-1/images` `url` 已係 proxy URL;`curl` 嗰條 proxy URL → **HTTP 200 / image/png / 513068 bytes**(pre-fix 403)。Counter:integration test `test_upload_increments_total_screenshots_counter` 綠(現有 KB 因 pre-fix ingest 仍 0,re-index 後更新 — 見 progress.md retro)
- [x] **T11** — verify gates:`pytest tests/` **930 passed + 25 skipped + 0 failed** + `ruff` `All checks passed`(8 檔)+ `mypy` 5 改動檔 `Success`;`postgres_backend.py` 7 個 `_row_to_kb` tuple/dict error 屬 pre-existing(line 172 喺改動範圍之前 → 證實 zero new)

## Cross-Cutting

- [x] No ADR — H1(無架構/vendor/storage-layout 改動 — 加 endpoint + counter 參數 + URL 表述層改寫)+ H2(無新 dependency)均不觸發
- [x] H5 — backend proxy 方案令 blob **維持 private**(無 public-read 洩露風險);proxy route 喺 `/kb` auth-protected prefix 下
- [x] H6 — `api/routes/query.py` 屬 H6 mandatory list → `_proxy_citation_images` 有 `test_query_screenshot_proxy.py` 同步 test;proxy route + counter 亦有 `test_documents_route.py` 覆蓋
- [x] H7 — N/A(無 frontend / mockup 改動 — proxy 用絕對 URL,前端 `<img>` 零改動)
- [x] Commit references `progress.md` entry
- [x] `report.md` status `fixing → done`;`checklist.md` `in-progress → done`;`progress.md` written

## 🚧 Out of scope（不修,per report.md §7）

- 🚧 delete / reindex 路徑嘅 `total_screenshots` decrement — dedup 跨文件共享需要 ref-counting;維持原 `kb_management/storage.py` module docstring 已 documented 嘅「future-tier follow-up」立場。BUG-010 只做 upload-increment(fresh KB ingest 完全準確)
- 🚧 `storage_size_mb` drift — 同一段 documented deferral,與圖片功能無關
