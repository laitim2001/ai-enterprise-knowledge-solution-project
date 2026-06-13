# W73 — profile→preset routing progress

## Day 1 — 2026-06-13 — Phase kickoff + R6 grounding + plan lock

### 做咗咩
- W72 profiler engine closeout(content 100%)後,用戶連續拍板:段② → 「②a+②b routing 接駁先」(AskUserQuestion)→ 「保守 auto-write(D6 守)」(AskUserQuestion)。
- R6 grounding:`orchestrator.py`(ingest flow,profiler 接入點 = parse 後)/ `doc_config.py`(DocConfig post-retrieval only)/ `doc_config_store.py`(upsert/get,D6 守)/ `documents.py:_run_ingest_pipeline`(routing caller)/ `settings.py`(global default 值)。
- 建 phase folder `W73-profile-preset-routing/` + 寫 `plan.md`(active,locked)+ `checklist.md`。

### 關鍵 grounding finding
1. **`DocConfig` 只含 post-retrieval 旋鈕** → preset 只能設 cap/expansion/neighbour/markers/answer_detail/overview_pin;top_k/rerank/parent_doc 留 per-KB(routing 掂唔到)。
2. **W69 preset 喺 frontend 套 `KbConfig`** → 唔可 reuse,routing 要 backend 自定義 `profile→DocConfig` mapping(`PROFILE_PRESETS`)。
3. **接入點** = orchestrator parse 後 compute profile(`IngestionResult.profile`)+ caller `_run_ingest_pipeline` 做 routing policy(preset + D6 + upsert);職責分離。
4. **settings global default 保守**(cap 細 / markers off / neighbour_max_aux=2 / answer concise),ADR-0052 已 flip parent_doc+expansion;`drive-images-1`(P1 good config)cap=80 / max_aux=40 / markers on。

### 核心風險(R1)+ 緩解
- **auto-write per-doc preset override per-KB manual**(resolver per-DOC > per-KB)→ 可能退化已調 KB(drive-images-1)。
- 緩解:① preset 值對齊已驗 good config(P1=drive-images-1 式 → 不退化)② production-preserve(現有 KB 唔 re-ingest = 無 auto-write)③ D6 守 per-doc manual。

### 決策
- auto-write 策略 = **保守(D6 守)**:doc 已有 manual per-doc config → skip;profile None/too_small/unknown → skip(inherit)。
- profiler 接入 = orchestrator 內部 module singleton compute(best-effort,fail→None 唔 abort)+ caller routing policy。
- preset 中值(12/20/40/8)= judgment proposal,段③ UI admin 可調 mapping(本 plan review 可改)。

### Commits
- (本 entry 對應 kickoff commit:W73 plan/checklist/progress)

### Next(F1)
- `IngestionResult` 加 `profile` field + orchestrator parse 後 compute profile(best-effort)。

### Blockers / carry-overs
- 無 blocker。段②c(D8 PDF picture)/ ②d(方案 A)/ 段③(UI)= 後續,本段唔掂。
