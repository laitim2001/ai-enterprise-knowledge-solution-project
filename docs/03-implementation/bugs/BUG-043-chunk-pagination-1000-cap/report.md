---
id: BUG-043
title: delete / restamp / list 硬假設 <1000 chunks/doc,超過靜默漏尾
severity: Sev3          # 資料完整性(超大 doc 條件下)
status: done            # 2026-07-07 用戶 approve → fix landed + 2 分頁 test 全綠
reported: 2026-07-06
reporter: pipeline review(`docs/09-analysis/pipeline_review_20260706.md` I-R7,代碼核對)
backlog: B-14
related: ADR-0044(chunk_id 位置 index-based)/ BUG-040(ingest 健壯性)
---

# BUG-043 — <1000 chunks/doc 假設,delete/restamp 靜默漏尾

## 1. 現象(代碼核對)

多個對 Azure Search 的操作用 `top=1000` **單頁查詢、無分頁**:delete 整份文件的 chunk、更新文件 classification、更新文件 `allowed_principals`、`list_documents` / `_doc_exists_in_kb`。一份文件若 > 1000 chunk,這些操作**只處理頭 1000,其餘靜默殘留**:

- delete 漏尾 → 舊 chunk orphan 殘留(reindex 時新舊混雜)。
- restamp(classification / ACL)漏尾 → 尾段 chunk **保留舊安全標記**(安全相關)。

## 2. 根因(對 code first-hand 核對)

- `backend/retrieval/populate.py:344-346`(`delete_doc`)、`:422-427`(`update_doc_classification`)、`:514-519`(`update_doc_principals`)全部 `top=1000` 單頁、無分頁 loop。
- `_doc_exists_in_kb` / `list_documents` 同樣單頁。
- Tier 1 隱含假設「一份文件 < 1000 chunk」;實測 drive 文件約 369 chunk 未觸,但無硬性保證(大手冊 / 合併文件可超)。

## 3. 建議修法(等 approve)

1. 把上述操作改為**分頁遍歷**(Azure Search continuation token 或 loop until empty),確保覆蓋全部 chunk。
2. (可選)ingest 時記錄 doc 的 chunk 總數作 sanity,超大 doc 告警。

## 4. 驗收標準(等 approve 後據此驗)

- 建構 > 1000 chunk 的測試 doc,delete / classification restamp / ACL restamp **全部 chunk 生效**、無殘留。
- < 1000 chunk 文件結果 bit-identical(單頁路徑不變,production-preserve)。
- ruff / mypy clean。

## 5. 風險與注意

- 低:分頁是標準做法;注意 restamp 的冪等性與大 doc 的多輪呼叫成本。
- 安全維度(ACL restamp 漏尾)使本項優先於純 perf 類。

## 6. Fix landed

- `populate.py` — 抽 `_collect_doc_chunk_ids` 分頁 helper(skip/top loop,page size = `_AZURE_BATCH_LIMIT`=1000,直到短頁 break);`delete_doc` / `update_doc_classification` / `update_doc_principals` 三方法 Step 1 改用佢收集**全部** chunk_id(唔止頭 1000)。Step 2(delete/merge 分批)不變。< 1000 chunk 第一頁即 break = 單頁路徑不變(production-preserve);index missing(404)→ None → caller return 0(語義不變);log event 名經 `op` 前綴保留原 telemetry(`delete_doc_*` / `restamp_doc_*` / `restamp_principals_*`)。
- `test_populate.py` — 補 2 test:delete 分頁全覆蓋(1500 chunk / 2 search page skip 遞增 + 2 delete batch,全 chunk 順序覆蓋)+ ACL restamp 分頁全覆蓋(1200 chunk,防 stale ACL 尾巴 = 安全)。
- **驗證全綠**:25 test passed(現有 23 無破壞 + 新 2)/ `ruff check` All passed / `mypy` exit 0。populate.py + test_populate.py 全檔 `format --check` fail = **pre-existing 格式 debt**(upload trailing-comma / 方法簽名多行 / `import json` 後空行,`git diff` 確認唔喺本 fix 改動行)→ 屬 BACKLOG B-20,不在本 fix(surgical);本 fix 新增 code 本身 format clean。

## 7. Changelog

| 日期 | 動作 | 決定人 |
|---|---|---|
| 2026-07-06 | 立案(pipeline review I-R7 → BUG-043,Sev3,`status: proposed`,未動 code) | pipeline review / 待用戶 approve |
| 2026-07-07 | 用戶 approve → fix landed(抽 `_collect_doc_chunk_ids` 分頁 helper,3 方法 Step 1 共用收集全部 chunk_id)+ 補 2 分頁 test + 25 test/ruff-check/mypy 全綠 → `status: done`。pre-existing format debt 屬 B-20 不在此 | 用戶 approve / Claude |
