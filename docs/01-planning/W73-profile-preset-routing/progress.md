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

---

## Day 1 (cont) — 2026-06-13 — F1+F2+F3 落地 + closeout

### 做咗咩
- 用戶 confirm PROFILE_PRESETS 值「用呢套值,開始 implement」。
- **F1**:`orchestrator.ingest()` parse 後 compute profile(module singleton `_PROFILER`,best-effort try/except)→ `IngestionResult.profile`;4 個 return path 帶 profile。
- **F2**:`profile_presets.py`(`PROFILE_PRESETS` + `preset_for` return copy)+ `documents.py:_run_ingest_pipeline` 保守 auto-write(`_route_profile_preset` helper;D6 守 + D7 inherit + advisory wrap)+ `_IngestionDeps.doc_config_store`(從 app.state)。
- **F3**:`test_profile_routing.py`(7 test:presets 值 / D6 守 / auto-write / inherit)+ `test_orchestrator.py` append `test_ingest_computes_profile`。

### Gate = PASS
- mypy strict:W73 code clean(`_engine_or_503:111` no-any-return = **pre-existing**,git diff 核冇 touch body)。
- ruff clean + **32 pytest pass**(test_profile_routing + test_orchestrator + test_kb_reindex 唔 break)。

### 關鍵實作決定
- profiler 接入 = orchestrator 內部 module singleton compute(零 `__init__` churn,best-effort fail→None);routing policy 喺 caller `_run_ingest_pipeline`(職責分離:orchestrator compute / caller route)。
- `_route_profile_preset` = 保守 auto-write:`preset_for(profile)` None(too_small/unknown)→ skip(D7);`store.get` 已有 → skip(D6);否則 upsert。全程 advisory(try/except wrap,routing fail 唔 fail ingest)。
- `preset_for` return `model_copy()` 防 in-memory store share module-level singleton instance。
- production-preserve:現有 KB 唔 re-ingest = 零 auto-write;`doc_config_store` absent(test)→ routing skip。

## Closeout retro — 2026-06-13

**Phase verdict:PASS**。ADR-0056 層 A 段 ②a+②b(routing 接駁)落地完成,AC 全過:
- AC1 profile compute / AC2 auto-write / AC3 D6 守 / AC4 保守 inherit / AC5 production-preserve / AC6 P1 preset 對齊 good config / AC7 H6 test ✅

**Commits**:
| Hash | 內容 |
|---|---|
| `0d98d93` | W73 phase kickoff(plan/checklist/progress)|
| `0ad916c` | F1-F3 profile→preset routing(orchestrator + profile_presets + documents + test)|

**教訓**:
1. **grounding 揭兩個 finding 改變設計**:DocConfig 只 post-retrieval 旋鈕(preset 掂唔到 top_k/rerank)+ W69 preset=frontend KbConfig 唔可 reuse(routing 要 backend 自定義 mapping)。
2. **per-doc auto preset override per-KB manual** 係真退化風險(resolver per-DOC > per-KB)→ 緩解 = preset 值對齊已驗 good config(P1=drive-images-1)+ production-preserve(唔 re-ingest)+ D6 守。
3. **advisory routing** 守住 ingest 穩定:profile compute + auto-write 全 best-effort,任何失敗都唔 fail 已 index 嘅 doc。

### 段 ②c / ②d 交棒記錄
- **段 ②c D8 PDF picture**(`generate_picture_images=True` + re-index PDF KB)= **stakeholder 成本決定 + 建議獨立 ADR**;PDF 圖類 profile(P1_sop_imgdense / P3_slide PDF)嘅 preset 已備(markers/cap),但 PDF 圖入唔到庫 → preset 對 PDF 圖類空轉,要先解 D8。
- **段 ②d 方案 A section 級錨定**(W71 §5 net-new)= `P1_sop_imgdense` 完整 render 流程;本段 preset 只設**現有**旋鈕(cap/neighbour/markers/overview_pin),section 級錨定係 net-new,未做。
- **段 ③ 三層 UI**:profile badge / 文件畫像 section / **分類規則設定(admin 調 PROFILE_PRESETS mapping)**;卡 H7 OQ-B(無 mockup)。本段 PROFILE_PRESETS 係 backend hardcode default,段③ 先俾 admin 可調。
- **preset 中值微調**:除 P1 外中值(20/12/40/8)未實證,段③ admin UI 或實證 A/B 可 refine。

### 本 phase 無 deferred `[ ]`(checklist 全 tick;F3 full-HTTP-E2E routing 標 nice-to-have 未做,helper unit + reindex 唔 break 已覆蓋核心)。後續 = 段②c/②d/③,等用戶 trigger(rolling JIT)。
