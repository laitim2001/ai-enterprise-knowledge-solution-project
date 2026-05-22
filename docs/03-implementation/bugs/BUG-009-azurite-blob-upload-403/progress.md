---
bug_id: BUG-009
report_ref: ./report.md
checklist_ref: ./checklist.md
status: done
last_updated: 2026-05-22
---

# BUG-009 — Progress

> Bug-fix workflow per `PROCESS.md §4`。每個工作 session 一個 entry。

## Day 1 — 2026-05-22

### Investigation

由用戶問「KB `sample-doc-for-rag-knowledge-1` 點解冇提取圖片」開始,系統調查:

- `KbConfig.extract_embedded_images` default `False`(`kb.py:41`)→ orchestrator `orchestrator.py:121-122` short-circuit `screenshot_records=[]`。
- 即使開咗 flag:`documents.py:475` hard-code `IngestionOrchestrator(uploader=None)` — R12 forward-compat seam。
- R12 root cause(`RISK_REGISTER.md`)= Azurite SharedKey signature mismatch,W2 D3 結論「emulator bug,cloud deploy 先 verify」。

寫 `_r12_azurite_probe.py`(spawn `azurite@<version>` via npx + 用 project SDK `azure-storage-blob 12.28.0` 跑真實 blob round-trip),逐項隔離:

| 試驗 | 結果 |
|---|---|
| `3.35.0` plain | `InvalidHeaderValue — API version 2026-02-06 not supported` |
| `3.35.0` + `--skipApiVersionCheck` | `AuthorizationFailure`(403)|
| `3.35.0` + 顯式 conn string + pin api_version × 4 | 全 `AuthorizationFailure` — signature 同 API version 無關 |
| `3.35.0` + `UseDevelopmentStorage=true` + `--skipApiVersionCheck` | **SUCCESS** |
| `3.35.0` + `UseDevelopmentStorage=true` + pin api_version | **SUCCESS** |

確認三層成因(report.md §6)。額外發現:`settings.py` default / `.env` / `.env.example` 三處 Azurite well-known key 都打漏一個 `+`。

### Decisions

- **D1** — 分類 Bug-fix BUG-009 Sev3。用戶 chat 確認「開 BUG 去 close R12」+「成功就即刻開 BUG 落實」。
- **D2** — Fix = `UseDevelopmentStorage=true`(解 signature R12 + corrupted key)+ Azurite `--skipApiVersionCheck`(解 API version)。**唔** downgrade Azurite — npm 無高於 3.35.0 版本,且 `UseDevelopmentStorage=true` 喺 3.35.0 已通。
- **D3** — 最小 flag set:`--skipApiVersionCheck` 單獨已足夠,**唔需** `--loose`(probe 驗證)。
- **D4** — `documents.py` 用 per-request `async with ScreenshotUploader(...)`,**唔**做 lifespan/app.state wiring(per Karpathy §1.2/§1.3 — `from_connection_string` 係 lazy,per-request 構造成本可忽略;少改 server.py + `_IngestionDeps`)。`extract_embedded_images=False` 嘅 KB orchestrator 唔會 call uploader,所以 unconditional wire 對 default path 零影響。
- **D5** — 無 ADR:非架構 / vendor / storage-layout 改動。

### Code changes

| 檔案 | 改動 | 範疇 |
|---|---|---|
| `backend/storage/settings.py` | `azure_blob_connection_string` default → `"UseDevelopmentStorage=true"`(移除顯式 path-style + corrupted key 字串)+ 解釋註解 | C12 |
| `backend/api/routes/documents.py` | `_run_ingest_pipeline`:`IngestionOrchestrator(uploader=None)` → `async with ScreenshotUploader(...)`(`get_settings()` 提供 connection string + container);kb_config 讀取上移;+2 import;更新 3 處 stale `uploader=None`/R12 註解 | C01 / C08 |
| `infrastructure/docker-compose.yml` | azurite `command:` 加 `--skipApiVersionCheck`;`image` tag `:latest` → `:3.35.0`;npm fallback 註解加 flag + `azurite@3.35.0` pin | C12 |
| `.env.example` | LOCAL DEV `AZURE_BLOB_CONNECTION_STRING` → `UseDevelopmentStorage=true` + 註解 | — |
| `.env`(本機,gitignored,**不 commit**) | 同上 — 令本機即時生效 | — |
| `docs/setup.md` | `.env` 範例 + §8.1 troubleshooting(R12 resolved row + NEW `--skipApiVersionCheck` row)+ npm 指令 | — |
| `docs/01-planning/RISK_REGISTER.md` | R12 summary row + 詳細 entry → **Resolved 2026-05-22** | — |

### Verify gates

- `ruff check api/routes/documents.py storage/settings.py` → **All checks passed**
- `mypy`(各檔隔離,`--follow-imports=silent`)→ **Success: no issues found**(兩檔)
- `pytest tests/` → **923 passed, 25 skipped, 0 failed**(3:41;`test_documents_route.py` 全通 — uploader wiring 無 regression)
- `_r12_azurite_probe.py` → SDK 12.28.0 ↔ Azurite 3.35.0 blob round-trip:`UseDevelopmentStorage=true` + `--skipApiVersionCheck` SUCCESS
- `_r12_uploader_smoke.py` → 真 EKP `ScreenshotUploader`(用 `settings` default)→ container create + upload(28 bytes,`deduped=False`)+ 重 upload(`deduped=True`)全 PASS
- Azurite(npm 3.35.0,`--skipApiVersionCheck`)running + backend `python -m api.server` 重啟 → `/health` 200(`postgres/azure_search/azure_openai` ok)
- 兩個 temp probe / smoke script 已刪

> **用戶最終確認**:用 `sample-doc-for-rag-knowledge-1`(或新 KB,`extract_embedded_images=True`)re-ingest 含圖片文件 → chat referenced screenshots 渲染。儲存層 + uploader class 已全綠,此步等同 BUG-007 嘅 browser verify(需用戶實際文件)。

### Commits

_(見 commit footer — `fix(ingestion): ...` BUG-009)_

### Retro

- 用戶 push back「Azurite 唔係本來就模擬 blob 上傳咩」糾正咗初版過度設計嘅「另寫 local FS uploader」方案 — 正確方向係修好 Azurite 連接本身,保持 connection-string auto-switch 模型。
- 隔離試驗(`_r12_azurite_probe.py` 逐個變數固定:plain / skipcheck / api-pin / devstorage)係定位「三成因疊加」bug 嘅關鍵 — 單看 403 無法區分 API-version / signature / key 三者。
- W2 D3 R12 結論「emulator bug,cloud 先 verify」過於保守:root cause 其實係 client-side connection-string 形式選擇,`UseDevelopmentStorage=true` 即可本機驗證。

