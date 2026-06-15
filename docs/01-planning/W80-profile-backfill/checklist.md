# W80 checklist — Profile-only backfill(ADR-0059)

> tick 規則:完成 `→ [x]`;延後 `[ ]` + 🚧 + reason + target(不可刪)。每 commit 對應 ≥1 項(R2)。

## F1 — backend profile-only backfill endpoint

- [x] F1.1 新 endpoint `POST /kb/{kb_id}/profiles/backfill`(kb.py `backfill_kb_profiles`,對齊 `reindex_kb` 的 404/archived guard)+ helper `run_kb_profile_backfill`(documents.py,`_engine_or_503` 列 doc + `_doc_profile_store` None → 503)
- [x] F1.2 per-doc loop(復用 reindex structure 拔重活)+ `_backfill_one_doc_profile` helper:已有 profile → `skipped_has_profile` / `download_source_document` None → `skipped_no_source` / parse + `_PROFILER.profile`(documents.py module-level singleton)+ persist(D6 守 preserve `manual_override`)+ `_route_profile_preset`(D6 skip-if-manual);單 doc 失敗 → `failed` 不 abort batch;tempfile finally 清理;**無** chunk/embed/upsert/counter
- [x] F1.3 回應 shape `{status:"profiled", kb_id, documents_total, profiled, skipped_has_profile, skipped_no_source, failed, profiles}`
- [x] F1.4 test `test_doc_profile_backfill.py`(H6)8 tests — 補 profile + skip 已有 + skip 無 source + per-doc 容錯 + D6 route skip-if-manual + `_backfill_one_doc_profile` preserve manual_override + 無 ingestion services(不動 retrieval)+ 503;**ruff 0 + mypy 新 code clean(剩 line 120 `_engine_or_503` pre-existing baseline)+ pytest 16 passed(backfill 8 + override 8 regression)**

## F2 — 對現有 KB 觸發 backfill + browser 驗

- [ ] F2.1 起全套 infra(pre-flight)+ `POST /kb/drive-images-1/profiles/backfill` → 確認 `profiled` > 0(若全 `skipped_no_source` → surface 畀用戶)
- [ ] F2.2 browser(playwright)驗 L2 Documents 表 profile 欄 + L3 文件畫像 card 真實顯示 profile(非 null);零臨時污染

## F3 — 驗證 + closeout

- [ ] F3.1 backend pytest 全綠 + ruff + mypy;frontend 不改(確認)
- [ ] F3.2 closeout:plan closed + progress retro + ADR-0059 README index + memory append
