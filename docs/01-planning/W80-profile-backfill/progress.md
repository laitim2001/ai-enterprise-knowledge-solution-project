# W80 progress — Profile-only backfill(ADR-0059)

## Day 1 — 2026-06-15(kickoff)

**Context**:W72-W79 建齊 profiling pipeline,但 profiler 由 W73 先接入 ingest → **W73 之前 ingest 嘅現有
doc 冇 profile**(read surface 全 null,W78 UI 喺真實 KB 係空殼)。用戶 2026-06-15 揀候選 4 = **(b) 輕量
profile-only backfill**(非 (a) 完整 re-ingest),照 ① → ② → ③ 走。

**Ground(plan kickoff,R6 5-step)**:讀 `profiler.py`(input = `ParserResult` + `source_path`)/ `orchestrator.py`
(W73 profiler 接入點)/ `documents.py` `_run_ingest_pipeline`(profile persist 878-892 + route 905)+
`run_kb_reindex`(948,KB-level loop:download source → re-parse → re-ingest)+ `source_store.py`
`download_source_document`(W46)。**結論**:backfill = `run_kb_reindex` loop **拔掉 chunk/embed/upsert** 嘅
輕量版;原始檔由 W46 / ADR-0043 source blob 取得(W46 前 ingest 冇 → skipped_no_source)。

**ADR-0059 Accepted**(本 session):profile-only backfill endpoint。Alternatives:A 完整 re-ingest(reject —
重量 + 繞過 production-preserve D6 守 + retrieval 風險)/ C read-time lazy compute(reject — read path 唔應
重 parse + 無 persist)/ B(採用)backfill endpoint(surgical + reuse 最多基建)。

**設計決定**:
- endpoint `POST /kb/{kb_id}/profiles/backfill`(KB-level,對齊 reindex pattern)。
- idempotent:已有 profile → skip(`skipped_has_profile`);冇 source → `skipped_no_source`。
- D6 守:preserve `manual_override`(re-profile system fact 但唔失人手覆寫)+ `_route_profile_preset`
  skip-if-manual config。
- deps:**唔用** `_ingestion_deps_or_503`(嗰個 require embedder/populator 否則 503);只 `_engine_or_503`
  (列 doc)+ `doc_profile_store` + `doc_config_store` + blob connection string + standalone parser/profiler。
- UI button **唔做**(一次性 ops + 避 H7,mockup 冇呢個 button);用 API 觸發。

**已 flag 限制(upfront)**:W46(2026-06-04)前 ingest 嘅 doc 冇 source blob → backfill skip;F2 browser
驗時確認 drive-images-1 嘅 `profiled` > 0,若全 skip 即 surface 畀用戶(要先 doc-level reindex re-upload)。

**紀律自檢**:H1 ✅(ADR-0059 Accepted)/ H2 ✅(零新 dep)/ H4 ✅(層 A)/ H6 ✅(F1.4 route test)/ H7 ✅
(backend-only,UI button non-goal)/ Karpathy ✅(reuse run_kb_reindex/download_source/profiler/persist 守)。

**Plan 落地**:W80 folder + plan.md(active)+ checklist.md(F1-F3)+ progress.md + ADR-0059 + README index。

**F1 implement(Day 1)**:
- **documents.py**:import `DocumentProfiler` + module-level `_PROFILER` singleton(stateless 純規則,多 instance
  無害);`_backfill_one_doc_profile`(re-parse 一個 stored doc → `_PROFILER.profile` → persist D6 守 preserve
  `manual_override` + `_route_profile_preset` D6 skip-if-manual;tempfile finally;**無** chunk/embed/upsert);
  `run_kb_profile_backfill`(`_engine_or_503` 列 doc + `_doc_profile_store` None → 503;per-doc:已有 profile →
  `skipped_has_profile` / 無 source → `skipped_no_source` / 否則 backfill;單 doc 失敗 → `failed` 不 abort batch;
  KB-level kb_config 讀一次對齊 `extract_embedded_images` img 信號)。
- **kb.py**:`POST /kb/{kb_id}/profiles/backfill`(`backfill_kb_profiles`,對齊 `reindex_kb` 的 404/archived guard +
  local import 避 route-module cycle)。
- **test**:`test_doc_profile_backfill.py` 8 tests(duck-typed `ParserResult` mock 餵真 `_PROFILER` → P1_sop_imgdense;
  monkeypatch `download_source_document` + `select_parser`;endpoint 經 kb router)。

**F1 驗證**:ruff 0 + mypy 新 code clean(剩 line 120 `_engine_or_503` `return engine` Any = W79 已記 pre-existing
baseline,加 `_PROFILER` 3 行令 line 116→120 shift)+ pytest **16 passed**(backfill 8 + override 8 regression)。

**設計細節(implement)**:
- backfill **唔用** `_ingestion_deps_or_503`(嗰個 require embedder/populator/chunker 否則 503)— test
  `test_backfill_succeeds_without_ingestion_services` 證 backfill 喺零 ingestion services 下成功 = 零 retrieval 依賴。
- idempotent skip 已有 profile → override doc(W79)走 `skipped_has_profile`,**唔會被重 profile**(D6 守);
  `_backfill_one_doc_profile` 仍保 manual_override merge(future force-mode parity)。

**W74 fixture debt(F1 regression 副產品)**:F1 跑鄰近 regression 時 `test_documents_route.py` 15 failures。
**`git stash` 移走 W80 改動後 baseline 同 fail 同樣錯**(`select_parser(path, extract_images=...)` lambda 不接
kwarg)→ 確認 W74/ADR-0057 落地時 `_patch_orchestrator` stub 漏更新,**W80 net-new = 0**。用戶揀「順手修」→ stub
加 `extract_images=False` kwarg → 41 passed(15 回綠)。commit `8f9160a`。

**F2 驗證(Day 1,用戶揀「重啟 backend + API 驗」非 browser)**:
- **pre-flight**:backend /health 200 但 `POST /profiles/backfill` → **404 = 舊 code**(W79 backend,W80 endpoint
  未 pick up)+ azurite ✅ + Postgres healthy。**殺 W79 dual-process**(venv parent 56632 → system child 56768,
  正是上 session background backend task `bxbvsm2su`,殺後它 exit 255)+ port 8000 free → **重啟 backend(W80 code)**
  輪詢 /health 200 ~42s。
- **POST backfill**:`202 profiled: 6` — 全 6 docs(AR/AP/GL/CB/BM/FA manual)判 **P1_sop_imgdense**;
  `skipped_has_profile`/`skipped_no_source`/`failed` **全空** → 證 6 docs 之前全 null(無 profile)+ source blob
  都在(W46 後 re-index 過)。
- **GET /documents read surface**:6 docs 全 profile=P1_sop_imgdense + confidence **0.95**(高信心非 fallback)+
  `total_chunks` 不變(78/74/28/16/90/83)= **零 retrieval 影響**(backfill 零動 chunks 坐實)。
- **達標**:候選 4「令現有 doc 有 profile」完成 — W78 三層 UI + W79 override 喺 drive-images-1 真正生效
  (不再淨係臨時 doc 驗)。frontend render 不重驗(W78 已驗 + W80 零 frontend 改動)。

**Retro(Day 1)**:
- **backfill = `run_kb_reindex` 輕量版** — 高度復用(download_source / profiler / persist / route),拔掉 chunk/
  embed/upsert,新 code 最少(2 helper + 1 endpoint)。「零 retrieval 影響」by construction(零 populator call)+
  test `test_backfill_succeeds_without_ingestion_services` 證 + F2 `total_chunks` 不變坐實。
- **改 backend 後必須重啟先 pick up**(W79 教訓重現):pre-flight `POST` endpoint 404 = 舊 code 直接坐實,
  省卻盲猜;重啟前先 pre-flight probe endpoint 存在性 = 好習慣。
- **殺 backend 前確認 dual-process + 非別 session**:TaskList 空 + 進程穩定 18 小時 = 上 session 遺留(非別
  session 啱啱起)→ 安全殺整對(parent+child);殺後上 session background task notification exit 255 = 預期。
- **regression 用 `git stash` 科學辨 pre-existing vs net-new**:15 failures 一度似 W80 引入,stash baseline 跑同
  test 同 fail → 確證 pre-existing,避免錯誤 attribute + 順帶清咗 W74 遺留 debt。
- **交棒**:現有 doc backfill 已完成(drive-images-1 6 docs);其他現有 KB(如 `drive_user_manuals`)同樣可 `POST
  backfill` 補(rolling JIT,等需求)。② D8 PDF/scan robustness(profiler 準確度,等真實 backfill 數據判缺口真偽)
  → ③ 層 B 查詢意圖 gate(全新正交層 conditional)為下一步。

**Commits**:
- `6a71e14` docs(planning): W80 kickoff + ADR-0059 — profile-only backfill
- `8ccea0a` feat(api): W80 F1 profile-only backfill endpoint (ADR-0059)
- `8f9160a` test(api): fix W74/ADR-0057 _patch_orchestrator select_parser stub
- (closeout)docs(planning): W80 closeout — full PASS
