---
id: CH-021
title: ingest ACL fail-open 加可觀測告警(RBAC backend 缺失時 chunk 印成 public)
status: done            # 2026-07-07 用戶 approve 保守版 → 告警落地 + 3 新 test 綠
created: 2026-07-06
requester: pipeline review(`docs/09-analysis/pipeline_review_20260706.md` I-R4,代碼核對)
backlog: B-16
related: BUG-041(查詢層圖片 ACL 漏 — 同屬 fail-open 主題)/ ADR-0066
---

# CH-021 — ingest ACL fail-open 告警

## 1. 背景

入庫解析文件 ACL 時,若 `rbac_backend` 為 None / in-memory 未 seed,`resolve_doc_principals` 回 `[]`,而檢索層把空 `allowed_principals` 視為 **public** → 該文件所有 chunk **變全員可見**,且**無任何告警**。同理 classification store 未 wire 時 `documents.py:928-932` 退回 `"internal"`,restricted 標記**靜默降級**。

這是「production-preserve 的 fail-open 過渡設計」,方向為「寧鬆勿死」;但**缺乏可見性** —— 一次 backend 短暫故障就靜默把文件印成 public,無人知。

## 2. 行為規格(等 approve)

**保守版(建議):只加可觀測性,不改 fail-open 語義本身**

- ingest 時偵測「ACL 解析落入 fail-open 分支」(`rbac_backend` None / principals 空但 KB 非 public / classification store 缺失退 internal)→ 記 **warning log + metric**,明確標示「此 doc 以 fail-open 印成 public/internal」。
- (可選)在 KB / dashboard 層暴露「以 fail-open 入庫的文件」清單,供事後 re-stamp。

**進取版(需用戶定,可能改 production-preserve)**

- 改為 **fail-safe**:backend 未 ready 時**拒絕 ingest**(或標記 doc 為 pending-ACL 不可檢索),直到 principals 可正確解析。此選項改變現有 fail-open 取捨,需明確評估。

## 3. 唔做(out of scope)

- 保守版不改 fail-open → fail-safe 的核心取捨(除非用戶選進取版)。
- 不改檢索層對空 `allowed_principals` 的 public 解釋。

## 4. 邊界 / 待確認

- 保守版 vs 進取版由用戶定(涉安全 posture:可見性 vs 硬阻擋)。
- 進取版屬 H1-adjacent(改 ingest 準入行為)—— 若選進取版,approve 時確認是否需 ADR。
- 與 BUG-041(查詢層圖片漏 trim)同屬 fail-open 主題,可一併考量整體 ACL fail 策略。

## 5. 驗證(等 approve 後據此驗)

- backend 缺失 / 未 seed 時 ingest,產生**明確 warning log + metric**(保守版);或按進取版拒絕/標記。
- backend 正常時 ingest 無 regression(無多餘告警)。

## 6. 實作記錄

**採用保守版(只加可觀測性,不改 fail-open 語義本身)。**

- `backend/api/routes/documents.py` — `_run_ingest_pipeline` 在 resolve `allowed_principals` + `classification` 之後、`orchestrator.ingest()` 之前,加 fail-open 偵測 + structured warning(固定 event name → log aggregator 可當 metric count):
  - `deps.rbac_backend is None` → `logger.warning("ingest_acl_fail_open", reason="rbac_backend_unwired", ...)`(RBAC backend 未 wire → resolve 回 [] → chunk 印成 public)。
  - backend 有但 `allowed_principals` 空 → 同 event(reason=`empty_principals`,供事後 re-stamp 判斷:可能真 public KB,也可能 ACL 漏設 / 被誤刪)。
  - `deps.doc_classification_store is None` → `logger.warning("ingest_classification_fail_open", ...)`(classification 靜默退 `"internal"`,restricted tag 可能降級)。
  - **不改 fail-open 語義**:正常 backend + 有 grant → 零告警(production-preserve);orchestrator / retrieval 層完全不動。
- `backend/tests/api/test_documents_route.py` — 補 fixture `_ingest_log_capture`(structlog→stdlib bridge,teardown `reset_defaults` 免污染同檔其他 test;沿用 `test_audit_log._structlog_capture` 慣例)+ 3 test:
  - `test_ingest_acl_fail_open_warns_when_backend_unwired`(backend None → `ingest_acl_fail_open` + reason `rbac_backend_unwired`)。
  - `test_ingest_classification_fail_open_warns_when_store_unwired`(store None → `ingest_classification_fail_open`)。
  - `test_ingest_no_acl_fail_open_warning_when_principals_resolved`(backend wired + KB grant → 無多餘告警,對應 §5「正常時無多餘告警」regression)。
- **驗證**:3 新 test passed;`ruff check` All passed;`mypy` 我改動行零 error(`documents.py:155` + 別檔 57 個 = 整 codebase pre-existing strict debt,屬 BACKLOG B-20,surgical 不碰);新增 code `ruff format` clean(整檔 `format --check` fail = pre-existing 2-per-line / trailing-comma debt,B-20)。整檔 51-test regression 喺重度 loaded 機器上約 3 分鐘/test 極慢(估 ~2 小時),用戶 2026-07-07 approve 用已完成驗證 commit;**已綠嘅頭 10 個正是 ingest / upload 路徑相關 test(含被本改動影響嗰批 + 3 新 test),剩餘 41 個(delete / reindex / kb 建刪 / list images)與本改動的 ingest ACL / classification 告警碼無關**。改動純加 `logger.warning`(不改控制流 / 回傳),結構上不可能破壞既有 test。

## 7. Changelog

| 日期 | 動作 | 決定人 |
|---|---|---|
| 2026-07-06 | 立案(pipeline review I-R4 → CH-021,`status: proposed`,未動 code) | pipeline review / 待用戶 approve |
| 2026-07-07 | 用戶 approve 保守版 → 告警落地(3 fail-open 偵測分支 + structured warning)+ 3 新 test 綠 + ruff / mypy / format 驗證(pre-existing debt 屬 B-20)→ `status: done` | 用戶 approve / Claude |
