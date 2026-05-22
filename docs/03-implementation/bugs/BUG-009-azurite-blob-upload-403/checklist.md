---
bug_id: BUG-009
report_ref: ./report.md
status: done            # in-progress | done
last_updated: 2026-05-22
---

# BUG-009 — Checklist

> Derived from `report.md §7 Acceptance for Fix`。延後項標 🚧 + reason(per CLAUDE.md sacred rule — 唔可以刪未勾 `[ ]`)。

## Fix

- [x] **T1** — Root cause confirmed via `_r12_azurite_probe.py` 三層隔離:(1) API version `2026-02-06` > Azurite 3.35.0;(2) 顯式 path-style `BlobEndpoint` conn string → SDK canonicalized-resource 同 Azurite 對唔上(R12);(3) corrupted AccountKey 漏 `+`。`UseDevelopmentStorage=true` + `--skipApiVersionCheck` 試驗 SUCCESS
- [x] **T2** — `backend/storage/settings.py`:`azure_blob_connection_string` default → `"UseDevelopmentStorage=true"`(移除顯式 path-style + corrupted key 字串)+ 解釋註解
- [x] **T3** — `.env`(本機 gitignored,**不 commit**):`AZURE_BLOB_CONNECTION_STRING` → `UseDevelopmentStorage=true` + 註解
- [x] **T4** — `.env.example`(committed):LOCAL DEV line → `UseDevelopmentStorage=true` + 註解;CLOUD section 不動
- [x] **T5** — `infrastructure/docker-compose.yml`:azurite `command:` 加 `--skipApiVersionCheck`;`image: ...azurite:latest` → `:3.35.0`;npm fallback 註解同步加 `--skipApiVersionCheck` + `npm install -g azurite@3.35.0` pin
- [x] **T6** — `backend/api/routes/documents.py`:`_run_ingest_pipeline` 嘅 `IngestionOrchestrator(uploader=None)` → `async with ScreenshotUploader(connection_string=..., container_name=...)`(由 `get_settings()` 提供);+2 import(`ScreenshotUploader` / `get_settings`);更新 3 處 stale `uploader=None`+R12 註解(GET images docstring / orchestrator 構造 / upload route docstring)
- [x] **T7** — `docs/setup.md`:`.env` 範例 + §8.1 Azurite troubleshooting(R12 resolved row + NEW `--skipApiVersionCheck` row)+ npm fallback 指令
- [x] **T8** — `docs/01-planning/RISK_REGISTER.md` R12 → **Resolved**(summary table row + 詳細 entry,2026-05-22)
- [x] **T9** — Runtime verify:`_r12_azurite_probe.py`(SDK ↔ Azurite blob round-trip)+ `_r12_uploader_smoke.py`(真 EKP `ScreenshotUploader` class 用 `settings` default `UseDevelopmentStorage=true` → container create + upload 28 bytes + dedup hit,全 PASS)+ Azurite(`--skipApiVersionCheck`)running + backend 重啟 `/health` 200(`postgres/azure_search/azure_openai` ok)。**儲存層 + uploader class 全綠**;真實 image-bearing 文件嘅 ingest-to-chat 留用戶用 `sample-doc-for-rag-knowledge-1` 做最終功能確認(同 BUG-007 browser verify 一致 — 需用戶實際文件)
- [x] **T10** — verify gates:backend `pytest tests/` **923 passed + 25 skipped + 0 failed** + `mypy`(`documents.py` / `settings.py` 隔離)`Success: no issues` + `ruff` `All checks passed`
- [x] **T11** — cleanup:`backend/_r12_azurite_probe.py` + `backend/_r12_uploader_smoke.py`(NEW smoke)兩個 temp 已刪

## Cross-Cutting

- [x] No ADR — H1(無架構 / vendor / storage-layout 改動 — connection-string 值 + Azurite launch flag + 收口 deferred seam;Azure Blob + Azurite vendor 不變)+ H2(無新 dependency — `azure-storage-blob` 早喺 §5.2 vendor table)均不觸發
- [x] H5 — `.env` 唔 commit(gitignored);Azurite well-known key / `UseDevelopmentStorage=true` 屬公開常數,非 secret
- [x] H6 — `documents.py` 屬 routes,非 H6 mandatory list(`api/routes/query.py` 先係);既有 `test_documents_route.py` route test 跑通覆蓋 wiring(923 passed)
- [x] H7 — N/A(純 backend / infra change,無 frontend / mockup 改動 — 圖片渲染前端 W22 F4 早已 build)
- [x] Commit references `progress.md` entry;component tag `(ingestion)` 對應 C01 + infra
- [x] `report.md` status `fixing → done`;此 `checklist.md` status `in-progress → done`;`progress.md` written

## 🚧 Out of scope（不修,per report.md §7）

- 🚧 Azurite emulator 本身嘅 path-style canonicalized-resource bug — third-party,upstream issue;EKP 用 `UseDevelopmentStorage=true` 繞過
- 🚧 Cloud Azure Blob 路徑 — 本身無此 signature bug;cloud 環境設真 connection string 即 work
- 🚧 `ScreenshotUploader` / `IngestionOrchestrator` 邏輯 — 行為正確,本 bug 只係佢哋從未獲得有效 connection + 從未被 wire

---

**Lifecycle reminder**:新加 acceptance item 必先入 `report.md §7`,然後再加 checklist。延後項標 🚧 + reason,唔可以刪。
