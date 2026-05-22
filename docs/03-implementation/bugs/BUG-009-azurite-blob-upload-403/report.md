---
bug_id: BUG-009
title: "Screenshot blob upload fails against Azurite (403 SharedKey signature mismatch) — R12; explicit path-style connection string + uploader=None left embedded images permanently empty"
severity: Sev3          # Sev1 | Sev2 | Sev3 | Sev4 (per PROCESS.md §4.5)
status: done            # triaged | investigating | fixing | verifying | done | wont-fix
reported: 2026-05-22
reporter: "AI — surfaced while investigating why KB `sample-doc-for-rag-knowledge-1` returns no embedded images in chat"
affects_components: [C01, C12]   # C01 Ingestion (screenshot pipeline) + C12 DevOps/Infra (Azurite emulator); upload-route wiring in C08
spec_refs:
  - architecture.md §3.5      # ChunkRecord.embedded_images metadata (citation render)
  - architecture.md §4.6      # async Blob screenshot uploader + SHA256 dedup
  - RISK_REGISTER.md R12      # Azurite SDK signature mismatch (NEW W2 D3 finding)
  - ADR-0028                  # KbConfig multimodal Tier 1 fields (extract_embedded_images)
---

# BUG-009 — Screenshot blob upload fails against Azurite (403 SharedKey signature mismatch)

> **Report version**:1.0(initial)
> **Triage approver**:AI self-triaged **Sev3**(text retrieval / Gate 1 R@5 完全不受影響 — `embedded_images` 只係 citation-render metadata per architecture.md §3.5;受影響者僅 multimodal「圖片返回」功能,且過往從未 wire 過 production 上線);**用戶 chat 確認「開 BUG 去 close R12」+「成功就即刻開 BUG 落實」2026-05-22**。

## 1. Symptom

任何 KB(例:`sample-doc-for-rag-knowledge-1`)ingest 含內嵌圖片嘅文件之後,chat 回應**從來唔會顯示 referenced screenshots**;`GET /kb/{kb_id}/images` 永遠回空 list。即使 KB 喺 `/kb/new` Step-4 wizard 撳開 `extract_embedded_images`,圖片都唔會出。

底層用 azure-storage-blob SDK 直接打 Azurite,所有 blob 操作 fail:

```
azure.core.exceptions.HttpResponseError: Server failed to authenticate the
request. Make sure the value of the Authorization header is formed correctly
including the signature.
ErrorCode: AuthorizationFailure        (HTTP 403)
```

## 2. Reproduction Steps

1. 本機行 Azurite emulator(npm `azurite` 3.35.0,或 docker `azurite` container)
2. `backend/.venv` 已裝 `azure-storage-blob 12.28.0`(per `pyproject.toml` pin `>=12.28`)
3. 用 `.env` 嘅顯式 connection string(`AccountName=devstoreaccount1;...;BlobEndpoint=http://127.0.0.1:10000/devstoreaccount1`)建 `BlobServiceClient`,打任何 blob op(`create_container` / `upload_blob` / `get_blob_properties`)
4. Observed:`AuthorizationFailure`(403)

**Reproduction reliability**:Always(deterministic)。2026-05-22 用 `_r12_azurite_probe.py`(spawn Azurite + 真實 blob round-trip)逐項隔離驗證。

**Environment**:Windows 11 + Python 3.12 + `azure-storage-blob 12.28.0` + Azurite 3.35.0(npm latest)。

## 3. Expected vs Actual

| 範疇 | Expected | Actual |
|---|---|---|
| Local dev 上載 screenshot 去 Azurite | SDK 連 Azurite,blob round-trip 成功 | 403 `AuthorizationFailure`(signature mismatch) |
| 部署上 Azure 環境 | SDK 自動連真 Azure Blob,**code 零改動** | (設計意圖正確;但 local 路徑壞咗,圖片功能從未真正 work 過) |
| `documents.py` 上載 route | orchestrator 攞到真 uploader,圖片上載 + `embedded_images` 填充 | `IngestionOrchestrator(uploader=None)` hard-code — screenshot 上載被完全 skip |
| Chat referenced screenshots | 2+ 圖片 citation → `ImageGallery` 渲染 | 永遠空(`embedded_images_json` 一律 `[]`) |

## 4. Impact

- **Affected scenario**:任何想用 multimodal「圖片返回」功能嘅 KB。Tier 1 ADR-0028 提供 `extract_embedded_images` toggle,但即使開咗都冇效果。
- **兩層 + 一個 latent 問題疊埋**(全部 2026-05-22 隔離確認):
  1. **API version 太新** — SDK 12.28.0 預設送 `x-ms-version: 2026-02-06`,Azurite 3.35.0(npm latest,無更新版本)唔識 → `InvalidHeaderValue`。
  2. **SharedKey signature mismatch(R12)** — `.env` 用**顯式 path-style `BlobEndpoint` connection string**,azure-storage-blob 12.28 對 path-style account 嘅 canonicalized-resource 計算同 Azurite 對唔上 → 403 `AuthorizationFailure`。R12(W2 D3 finding)記載 Azurite debug log 顯示 canonicalized-resource = `/devstoreaccount1/devstoreaccount1/`,SDK 計 `/devstoreaccount1/`。
  3. **Latent — corrupted AccountKey** — `settings.py` default、`.env`、`.env.example` 三處嘅 Azurite well-known key 都打漏咗一個 `+`(`...JGdu/XpGV1...`,正確 `...JGdu+/XpGV1...`)。錯 key → HMAC signature 必 fail。此問題被 (2) 遮蓋(兩者都係 403),但屬獨立 latent bug。
- **`uploader=None`**:`documents.py:475` 因應 R12 故意 hard-code `uploader=None`(documented forward-compat seam)— 即使前 3 個問題修好,上載仍被 skip。
- **Workaround available?**:無(local-dev 完全做唔到圖片功能)。
- **Data loss / corruption?**:No(text retrieval 不受影響 — `embedded_images` 純 citation-render metadata per architecture.md §3.5)。
- **Security implication?**:No。
- **Why latent until now**:R12 W2 D3 首次發現,當時結論「Azurite emulator bug,W7+ cloud deploy 先 verify」→ F3 sanity 用 AsyncMock,真實 Azurite blob round-trip 從未跑通。`documents.py` 上載 route W16 F5 (CH-001) landed 時就以 `uploader=None` 落地。2026-05-22 用戶問「點解 KB 冇圖」→ 系統性調查先逐項隔離出三層成因。

## 5. Severity Justification

**Sev3** per `PROCESS.md §4.5`:text retrieval / Gate 1 / chat 答案本身完全正常 —— 受影響者僅 multimodal 圖片返回(per architecture.md §3.5,`embedded_images` 係 citation-render metadata,Gate 1 R@5 基於 text + embedding)。無 data loss、無 security、預設 text-only KB 路徑無 broken。非 Sev1/Sev2。但對「local dev 用圖片功能」係硬 blocker。Sev3 → **無需 postmortem**。

## 6. Initial Diagnosis（root cause confirmed）

2026-05-22 用 `_r12_azurite_probe.py`(spawn `azurite@<version>` + 用 project SDK 12.28.0 跑真實 blob round-trip)逐項隔離:

| 試驗 | 結果 | 結論 |
|---|---|---|
| `3.35.0` plain | `InvalidHeaderValue — API version 2026-02-06 not supported` | 問題 1 — API version |
| `3.35.0` + `--skipApiVersionCheck` | `AuthorizationFailure`(403) | 過咗 API check,撞問題 2 — signature |
| `3.35.0` + 顯式 conn string + pin api_version × 4(2025-11-05 / 2025-07-05 / 2025-01-05 / 2024-08-04) | 全 `AuthorizationFailure` | signature mismatch 同 API version **無關**,獨立問題 |
| `3.35.0` + `UseDevelopmentStorage=true` + `--skipApiVersionCheck` | **SUCCESS** | ✅ |
| `3.35.0` + `UseDevelopmentStorage=true` + pin api_version | **SUCCESS** | ✅ |

**Root cause**:
- **問題 1**:azure-storage-blob 12.28 預設 API version 超過 Azurite 3.35.0(npm 無更新版本)所支援 → Azurite launch 加 `--skipApiVersionCheck` 解決(basic blob op = PutBlob/GetBlob,skip-check 安全)。
- **問題 2(R12)**:顯式 path-style `BlobEndpoint` connection string 令 SDK 計錯 canonicalized-resource。SDK 提供專用 Azurite 捷徑 `UseDevelopmentStorage=true`,行內部 Azurite-correct path-style 邏輯 → signature 一致。
- **問題 3**:corrupted AccountKey — 改用 `UseDevelopmentStorage=true` 後 SDK 由內部提供正確 well-known key,顯式 key 字串整段移除,問題自然消失。

**為何 `UseDevelopmentStorage=true` 正正係用戶想要嘅 auto-switch 模型**:`AZURE_BLOB_CONNECTION_STRING` env var 就係切換點 — local `.env` = `UseDevelopmentStorage=true`(SDK 行 Azurite),cloud 環境 = 真 `DefaultEndpointsProtocol=https;...` connection string(SDK 行真 Azure Blob),**application code 零改動**。

非架構 / vendor / storage-layout 改動(仍係 Azure Blob + Azurite,connection-string 值 + Azurite launch flag + 收口一個 deferred seam)→ **唔觸發 H1 / H2,唔需 ADR**。

## 7. Acceptance for Fix（checklist preview）

- [ ] Root cause confirmed — 三層成因(API version / path-style signature R12 / corrupted key)via `_r12_azurite_probe.py` 隔離試驗
- [ ] `backend/storage/settings.py` — `azure_blob_connection_string` default `DefaultEndpointsProtocol=http;...`(顯式 path-style + corrupted key)→ `UseDevelopmentStorage=true`
- [ ] `.env`(本機,gitignored,**不 commit**)— `AZURE_BLOB_CONNECTION_STRING` line → `UseDevelopmentStorage=true`
- [ ] `.env.example`(committed)— LOCAL DEV line → `UseDevelopmentStorage=true` + 解釋註解;CLOUD section 不變
- [ ] `infrastructure/docker-compose.yml` — azurite `command:` 加 `--skipApiVersionCheck`;image tag `:latest` → pin `:3.35.0`(reproducibility);npm fallback 註解同步加 flag
- [ ] `backend/api/routes/documents.py` — `_run_ingest_pipeline` 嘅 `IngestionOrchestrator(uploader=None)` → wire 真 `ScreenshotUploader`(`async with`,connection string + container 由 `get_settings()` 提供);更新 3 處 stale `uploader=None` / R12 註解(§GET images docstring / orchestrator 構造 / upload route docstring)
- [ ] `docs/setup.md` — `.env` 範例 + §8.1 Azurite troubleshooting(R12 resolved + `--skipApiVersionCheck` 說明)+ npm fallback 指令同步
- [ ] `docs/01-planning/RISK_REGISTER.md` — R12 entry 標 **Resolved**(2026-05-22,fix = `UseDevelopmentStorage=true` + `--skipApiVersionCheck`)
- [ ] **無新 contrived unit test** — fix 主體係 connection-string 值 + infra flag + wiring;`documents.py` 既有 route test 跑通即覆蓋 wiring(per Karpathy §1.2 唔寫 contrived test;同 BUG-008 一致)
- [ ] **Runtime verify(= 主 acceptance)** — Azurite(`--skipApiVersionCheck`)+ backend 重啟 → 建 / 設定一個 `extract_embedded_images=True` 嘅 KB → ingest 含圖片文件 → `GET /kb/{kb_id}/images` 回真實圖片 → chat referenced screenshots 渲染
- [ ] verify gates — backend `pytest tests/` **0 failed** + `mypy` clean(改動檔)+ `ruff` 零新 error
- [ ] cleanup — 刪 temp `backend/_r12_azurite_probe.py`
- [ ] **Out of scope（不修）**:Azurite emulator 本身嘅 path-style canonicalization bug(third-party,upstream);cloud Azure Blob 路徑(本身無此 bug);`ScreenshotUploader` / orchestrator 邏輯(行為正確,只係從未獲得有效 connection)

## 8. Report Changelog

| Date | Change | Reason | Approver |
|---|---|---|---|
| 2026-05-22 | Initial triage(Sev3)+ root cause confirmed via `_r12_azurite_probe.py` 三層隔離試驗(API version / path-style signature R12 / corrupted key);fix = `UseDevelopmentStorage=true` + `--skipApiVersionCheck` + wire uploader | 用戶問「點解 KB `sample-doc-for-rag-knowledge-1` 冇提取圖片」→ 系統調查 → 用戶確認「開 BUG 去 close R12」+「成功就即刻開 BUG 落實」 | 用戶(chat-confirm 2026-05-22)|

---

**Lifecycle reminder**:Sev3 → `postmortem.md` 不需要(only Sev1/Sev2 mandatory per `PROCESS.md §4.5`)。
