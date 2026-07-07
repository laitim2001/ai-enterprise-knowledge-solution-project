---
id: BUG-040
title: 文件 ingest 的 parse/chunk 在 async 事件迴圈內同步阻塞(並發 hang)
severity: Sev2          # 潛在多用戶阻塞(production 並發下觸發;dev 單用戶看不出)
status: done            # 2026-07-07 用戶 approve → fix landed + 驗證全綠(60 test / ruff / mypy)
reported: 2026-07-06
reporter: pipeline review(`docs/09-analysis/pipeline_review_20260706.md` I-R1/I-R2,代碼核對)
backlog: B-11
related: BUG-030(image-heavy docx upload race — 同屬 ingest 併發面)
---

# BUG-040 — ingest parse/chunk 同步阻塞事件迴圈

## 1. 現象(代碼核對,非用戶報告)

文件入庫(`POST /kb/{kb_id}/documents` 及 reindex)的 **parse 與 chunk 兩步在 async request handler 內直接同步執行,無 `asyncio.to_thread`**。單一大檔(大 PDF / 大 docx)入庫期間,**整個 uvicorn 事件迴圈被阻塞,所有並發 request(其他上載、查詢、`/health`)一齊 hang**,直到該檔 parse/chunk 完成。

現階段單用戶 dev 環境看不出;production 多用戶並發下,一個大檔上載會拖冧全部人。

## 2. 根因(對 code first-hand 核對)

- `backend/ingestion/orchestrator.py:152`(`parser.parse`)、`:170`(`chunker.chunk`)是**直接 blocking call**,無 `asyncio.to_thread` 包裹。
- **契約落差**:`backend/ingestion/parsers/base.py:10-11` 的 docstring 明寫「orchestrator wraps in `asyncio.to_thread`」——**實作與 docstring 承諾不符**。
- P4 掃描件 guard(ADR-0065,`documents.py:871`)只擋掃描 PDF(會 hang 8–9 分鐘),born-digital 大檔仍會長時間阻塞事件迴圈。
- 全條 ingest 同步、無佇列(`documents.py:1433` docstring 自認「no background job」),回 202 但實際做完才返。

## 3. 建議修法(Tier 1 緩解 — 等 approve)

**範圍鎖定 = Tier 1 內的最低成本緩解,不觸架構邊界:**

1. **`orchestrator.py`**:把 `parser.parse`(`:152`)與 `chunker.chunk`(`:170`)包入 `asyncio.to_thread(...)`,令 CPU-bound 的 parse/chunk 離開事件迴圈 → 並發 request 不再被單一大檔阻塞。
2. 同步修正 `parsers/base.py:10-11` docstring 使其與實作一致(此前是 docstring 對、實作漏)。
3. 確認 thread-safety:chunker / parser 目前每 request 新建(`documents.py:908-915`,非共享 singleton 於 ingest 路徑),`to_thread` 安全;embedder / populator 是 lifespan 共享的 async client,不入 `to_thread`。

**明確不在本 BUG 範圍(標記為 Tier 2 候選)**:真正的**背景 ingest 佇列 / job queue**。architecture.md「no background job」是 Tier 1 刻意取捨,完整佇列觸 H4/需 ADR,另作 Tier 2 候選記錄(不在此修)。本 BUG 只解「事件迴圈被阻塞」,ingest 仍維持同步語義(request 等做完才返)。

## 4. 驗收標準(success criteria — 等 approve 後據此驗)

- 並發測試:一個大檔 ingest 進行中,同時打 `/health` 或 `/query` **不 hang**(回應時間不受 ingest 影響)。
- `parsers/base.py` docstring 與實作一致。
- 既有 ingest 測試全綠(parse/chunk 結果 bit-identical,只改執行執行緒不改邏輯)。
- ruff / mypy clean。

## 5. 風險與注意

- 低-中:`to_thread` 只改執行位置不改邏輯;主要風險是 parser/chunker 隱含共享狀態(需確認每 request 新建 = 無共享)。
- 不解「大檔 HTTP timeout」根本問題(那需背景佇列 = Tier 2);但顯著降低「一個大檔拖冧全部並發」的爆炸半徑。

## 6. Fix landed

- `orchestrator.py` — `ingest()` 內 parse / profile / chunk 三個 sync + CPU-bound 步驟各包 `asyncio.to_thread`,離開 uvicorn 事件迴圈;`ingest` 本身已 async,call site 無 churn。parser/chunker 每 request 新建(`documents.py`),無跨 thread 共享狀態 → `to_thread` 安全;embedder/populator 係 lifespan 共享 async client,**不**入 `to_thread`。
- `parsers/base.py` — docstring 對齊實作(明標 BUG-040:orchestrator 經 `asyncio.to_thread` 執行,大檔唔會 block event loop)。
- `test_orchestrator.py` — 加 2 個 test:`test_ingest_offloads_parse_and_chunk_to_worker_thread`(thread-id 檢查 parse/chunk 喺 worker thread 而非 loop thread,無 timing flakiness)+ `test_ingest_blocking_parse_keeps_event_loop_responsive`(parse 阻塞 worker thread 期間並發 coroutine 仍推進 = event loop 唔凍)。
- **驗證全綠**:60 test passed / `ruff check` All checks passed / `mypy --explicit-package-bases` exit 0。
- **範圍鎖定**:只解「事件迴圈被單一大檔阻塞」;背景 ingest 佇列(architecture.md「no background job」)= Tier 2,不在此(per §3)。

## 7. Changelog

| 日期 | 動作 | 決定人 |
|---|---|---|
| 2026-07-06 | 立案(pipeline review I-R1/I-R2 → BUG-040,Sev2,`status: proposed`,未動 code) | pipeline review / 待用戶 approve |
| 2026-07-07 | 用戶 approve 4 bug → fix landed(parse/profile/chunk offload `to_thread`,前 session 起草 + 本 session 驗證)+ 60 test/ruff/mypy 全綠 → `status: done` | 用戶 approve / Claude |
