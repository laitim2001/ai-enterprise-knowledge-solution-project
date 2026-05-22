---
bug_id: BUG-010
title: "Screenshots upload but stay invisible — total_screenshots counter never wired (badge shows 0) + blob URLs are private (browser <img> gets 403)"
severity: Sev3          # Sev1 | Sev2 | Sev3 | Sev4 (per PROCESS.md §4.5)
status: done            # triaged | investigating | fixing | verifying | done | wont-fix
reported: 2026-05-22
reporter: "AI — surfaced during BUG-009 user verification: KB sample-kb-test-1 ingested 8 images but UI shows Images 0"
affects_components: [C02, C08, C10]   # C02 KB Manager (counter) + C08 API Gateway (proxy route) + C10 Chat (citation image URLs)
spec_refs:
  - architecture.md §4.5      # KbStatus.total_screenshots field
  - architecture.md §4.6      # screenshot blob storage
  - ADR-0023                  # swappable KBStorageBackend (counter lives here)
related: BUG-009              # BUG-009 fixed the UPLOAD; this fixes the two dormant gaps it exposed
---

# BUG-010 — Screenshots upload but stay invisible (counter + serving)

> **Report version**:1.0(initial)
> **Triage approver**:AI self-triaged **Sev3**(text retrieval / chat answer 不受影響;受影響者僅圖片**可見性** — counter badge + blob 渲染);**用戶 chat 確認開 BUG + 揀 serving 方案 = backend proxy route 2026-05-22**。

## 1. Symptom

BUG-009 修好 screenshot 上載後,用戶建 KB `sample-kb-test-1`(`extract_embedded_images=True`)、上載一個 docx。Backend log 證實 **8 張圖成功提取 + 上載**(`images_uploaded: 8`),但:

- KB Detail 頁「Images」tab badge 顯示 **0**(`ImagesTab` 個 stat 卡都 0)
- screenshot blob URL 喺 browser `<img>` 渲染唔到

## 2. Reproduction Steps

1. 建 KB,`extract_embedded_images=True`,上載含內嵌圖片嘅 docx
2. `GET /kb/{kb_id}` → `total_screenshots: 0`(實際上載咗 8)
3. `GET /kb/{kb_id}/images` → 正確回 8 個 item,但每個 `url` 係裸 Azurite URL
4. `curl <裸 blob URL>` → **403 AuthorizationFailure**(private container)

**Reproduction reliability**:Always(deterministic)。

## 3. Expected vs Actual

| 範疇 | Expected | Actual |
|---|---|---|
| `KbStatus.total_screenshots` ingest 後 | = KB 內 distinct screenshot 數 | 永遠 `0` |
| KB Images tab badge / stat | 顯示真實圖片數 | `0` |
| `<img src=blob_url>` | 渲染到圖片 | `403 AuthorizationFailure` |

## 4. Impact

兩個 BUG-009 解通上載後浮現嘅 **dormant gap**(整個圖片 feature 之前因 R12 從未端到端跑通,下游從未被驗證):

- **Gap A — `total_screenshots` counter 從來冇 wire**:`record_doc_event` / `KBStorageBackend.update_metrics` 只有 `documents_delta` / `chunks_delta`,**冇 `screenshots_delta`**。`storage.py` module docstring 明文寫咗「`total_screenshots` ... drift is documented as a known future-tier follow-up」——即係原 CH-001 作者 deliberately defer 咗。BUG-009 令 screenshots 真正存在,所以呢個 deferral 而家要 close。
- **Gap B — blob URL browser 攞唔到**:`/images` endpoint(`KbImageItem.url`)+ chat citation(`embedded_images[].blob_url`)回嘅係裸 Azurite/Azure Blob URL。Container 預設 **private**,browser `<img>` 無 auth → 403。production 真 Azure Blob 一樣。

- **Data loss / corruption?**:No(圖片 blob 本身上載成功,index `embedded_images_json` 正常)。
- **Security implication?**:No —— 反之,backend-proxy 方案**保持 blob private**(避免 public-read 洩露 Ricoh 內部文件截圖)。
- **Workaround?**:用戶可㩒入「Images」tab,個圖片**格子**用 `/images` endpoint(回 8)—— Gap B 修好後格子會渲到圖,但 badge 仍受 Gap A 影響。

## 5. Severity Justification

**Sev3** per `PROCESS.md §4.5`:text retrieval / Gate 1 / chat 答案文字完全正常;受影響僅圖片**可見性**(metadata + 渲染)。無 data loss、無 security regression。預設 text-only KB 路徑無 broken。對「圖片功能」係硬 blocker。Sev3 → **無需 postmortem**。

## 6. Initial Diagnosis（root cause confirmed）

2026-05-22 經 backend log + `GET /kb/.../images` + `GET /kb/.../{KbStatus}` + curl 裸 blob URL 逐項確認:

- **Gap A root cause**:`KBStorageBackend.update_metrics`(Protocol + `InMemoryKBBackend` + `PostgresKBBackend` 三處)+ `KBService.record_doc_event` 都冇 `screenshots_delta` 參數;`documents.py` ingest 成功路徑只傳 `documents_delta` / `chunks_delta`。`IngestionResult.images_uploaded`(post-dedup unique 數)其實已有,只係從未接落 counter。
- **Gap B root cause**:`ScreenshotUploader` `create_container` 用預設(private)access;回傳裸 `blob_client.url`(無 SAS）。前端 `<img>` 無從 auth。

**Fix(用戶 2026-05-22 揀定 backend proxy route)**:
- **Gap A**:`update_metrics` × 3 + `record_doc_event` 加 `screenshots_delta`;`documents.py` `_run_ingest_pipeline` 傳 `screenshots_delta=result.images_uploaded`。Delete/reindex 嘅 screenshot decrement 因 dedup 跨文件共享需要 ref-counting,維持原 `storage.py` documented「future-tier follow-up」立場 — BUG-010 只做 upload-increment(fresh KB ingest = 完全準確;delete-path drift = 已知 limitation)。
- **Gap B**:新 auth-protected route `GET /kb/{kb_id}/screenshots/{blob_name}` — backend 用 connection string download private blob,`StreamingResponse` 串返 browser(blob 維持 private)。`/images` endpoint + chat citation enrichment 嘅 image URL → 用 `request.base_url` 砌絕對 proxy URL。前端零改動(`<img>` 靠 cookie 自動帶 auth — route 喺 `/kb` protected prefix 下)。

非架構 / vendor / storage-layout 改動(加一條 endpoint + counter 參數 + URL 表述層改寫;Azure Blob + Azurite vendor 不變)→ **唔觸發 H1 / H2,唔需 ADR**。

## 7. Acceptance for Fix（checklist preview）

- [ ] Root cause confirmed — Gap A(counter 未 wire)+ Gap B(private blob)
- [ ] **Gap A** — `kb_management/storage.py`(Protocol + `InMemoryKBBackend.update_metrics`)+ `kb_management/postgres_backend.py`(`update_metrics` SQL)+ `kb_management/service.py`(`record_doc_event`)加 `screenshots_delta: int = 0`
- [ ] **Gap A** — `documents.py` `_run_ingest_pipeline` 成功路徑 `record_doc_event(..., screenshots_delta=result.images_uploaded)`
- [ ] **Gap B** — 新 route `GET /kb/{kb_id}/screenshots/{blob_name}`:sanitize blob_name → resolve container(`kb_id_to_screenshot_container`)→ `BlobServiceClient` download → `StreamingResponse`(content-type 由 blob 屬性)+ 404 if not found
- [ ] **Gap B** — `documents.py` `list_kb_images`:`KbImageItem.url` → proxy 絕對 URL(`request.base_url` + `/kb/{kb_id}/screenshots/{blob_name}`)
- [ ] **Gap B** — chat citation image URL(`generation/citation_enrichment.py` 或 query 路徑)→ 同樣 rewrite 成 proxy URL
- [ ] Tests — counter:`update_metrics` `screenshots_delta` unit test(InMemory）;proxy route:200 stream + 404 + path-traversal reject
- [ ] Runtime verify — `sample-kb-test-1` re-query:`GET /kb/{kb_id}` `total_screenshots` = 8;proxy URL `curl` 回 PNG bytes(非 403);用戶 browser KB Images tab badge = 8 + 縮圖渲染 + chat referenced screenshots 渲染
- [ ] verify gates — backend `pytest tests/` 0 failed + `mypy`(改動檔)clean + `ruff` 零新 error
- [ ] **Out of scope（不修）**:delete/reindex 嘅 `total_screenshots` decrement(dedup ref-counting — 維持原 `storage.py` documented future-tier 立場);`storage_size_mb` drift(同一段 documented deferral,與圖片無關)

## 8. Report Changelog

| Date | Change | Reason | Approver |
|---|---|---|---|
| 2026-05-22 | Initial triage(Sev3)— BUG-009 用戶驗證時發現 8 張圖上載成功但 UI Images 0;隔離出 Gap A(counter 未 wire)+ Gap B(private blob 403);用戶揀定 serving 方案 = backend proxy route | BUG-009 解通上載後 dormant 下游 gap 浮現 | 用戶(chat-confirm + AskUserQuestion 2026-05-22)|

---

**Lifecycle reminder**:Sev3 → `postmortem.md` 不需要(only Sev1/Sev2 mandatory per `PROCESS.md §4.5`)。
