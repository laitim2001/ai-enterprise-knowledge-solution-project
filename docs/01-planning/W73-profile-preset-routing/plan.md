---
phase: W73
name: profile-preset-routing
status: closed       # draft | active | closed(2026-06-13 — F1-F4 done;32 pytest pass;routing 保守 auto-write D6 守;production-preserve)
created: 2026-06-13
owner: "Claude (AI) — 技術 Lead Chris 審閱"
gap: "ADR-0056 層 A 段 ②a+②b — routing 接駁:profiler 接入 ingest flow(parse 後 compute profile)+ backend PROFILE_PRESETS(profile→DocConfig 值 mapping)+ 保守 auto-write per-doc config(D6 守:已有 manual per-doc config → 跳過)。preset 值對齊 ADR-0056 D1 + 已驗 good config(P1=drive-images-1 式高 cap)避退化;production-preserve(現有 KB 唔 re-ingest 完全不受影響)。令 profile 真正自動驅動 per-doc config = 層 A payoff。"
adr: "ADR-0056(Accepted)D3 端到端流程 'Parse → Profiler → Routing:profile→preset → 套 per-doc config' + D6 admin override + D7 保守 — 本段實作。**唔含** 段②c D8 PDF picture / 段②d 方案 A section 錨定 / 段③ 三層 UI。無新 ADR(D3 已 cover routing 方向)。"
spec_refs:
  - docs/adr/0056-document-profiling-adaptive-recall.md            # D3 routing + D6 override + D7 保守
  - backend/ingestion/orchestrator.py                             # ingest flow(profiler 接入點 = parse 後)
  - backend/ingestion/profiler.py                                 # W72 ProfileResult / DocProfile
  - backend/api/schemas/doc_config.py                             # DocConfig(post-retrieval 旋鈕 only)
  - backend/kb_management/doc_config_store.py                     # DocConfigStore upsert/get(D6 守)
  - backend/api/routes/documents.py                              # _run_ingest_pipeline(routing caller,line 559)
---

# W73 — profile→preset routing 接駁(段 ②a+②b)

> **緣起**:W72 profiler engine 落地(content accuracy 100%)後,用戶揀段②先做、再揀「②a+②b routing 接駁先」+「保守 auto-write(D6 守)」。本段令 profile 真正自動驅動 per-doc config。
>
> **R6 核實(plan-text grounding,2026-06-13 kickoff)**:
> - **profiler 接入點** = `orchestrator.ingest()` parse 後(`result: ParserResult` + `source` 都 ready,line 133)→ compute profile,best-effort。
> - **`DocConfig`**(`doc_config.py`)**只含 post-retrieval 旋鈕**(`answer_detail` / citation expansion / neighbour images / `max_images_per_answer` / `enable_chapter_overview_pin` / `enable_inline_image_markers`)—— **唔含** `top_k`/`rerank`/`parent_doc`(retrieve 入口,留 per-KB)。即 preset 只能設 post-retrieval。
> - **W69 preset 喺 frontend** 套 `KbConfig`(per-KB)→ **唔可以** reuse;routing 要 backend 自定義 `profile→DocConfig` mapping。
> - **`DocConfigStore`**(`doc_config_store.py`)`get`/`upsert`/`delete`/`list_for_kb`,`make_doc_config_store(settings)` factory(Postgres / in-memory)。
> - **routing caller** = `documents.py:_run_ingest_pipeline`(line 559;build orchestrator → `orchestrator.ingest()` line 633)。
> - **settings global default**(保守):`max_images` 細 / `neighbour_max_aux=2` / `markers` off / `overview_pin` off / `answer_detail` concise;ADR-0052 已 flip `parent_doc`+`expansion` on。`drive-images-1`(P1 good config)override cap=80 / max_aux=40 / markers on。

## 1. 行為設計

### ②a profiler 接入 ingest(compute,無 side-effect)
- `orchestrator.ingest()` parse 成功後 compute profile:`IngestionResult` 加 `profile: ProfileResult | None`。
- **best-effort**:profile 計算包 try/except,失敗 → `profile=None`,**唔 abort ingest**(profiler 本身已 robust,但 ingest 唔可以因 profile 掛)。
- profiler 用 module-level singleton(`_PROFILER = DocumentProfiler()`,stateless,唔改 `__init__` 簽名 → 零 caller churn)。
- PDF 加一個 pypdfium2 pre-OCR pass(秒級,best-effort)。

### ②b PROFILE_PRESETS + 保守 auto-write(routing policy,caller 層)
- **新 module `backend/ingestion/profile_presets.py`**:`PROFILE_PRESETS: dict[DocProfile, DocConfig | None]` + `preset_for(profile) → DocConfig | None`。
- **`_run_ingest_pipeline` routing**(ingest 成功後):
  1. `result.profile` 為 None / `too_small` / `unknown` → **唔 routing**(inherit,per D7 保守)。
  2. `preset = preset_for(profile)`;`preset is None` → 唔 routing。
  3. **D6 守**:`existing = await doc_config_store.get(kb_id, doc_id)`;`existing is not None` → **skip**(admin manual override 永遠優先,唔覆蓋)。
  4. 否則 `await doc_config_store.upsert(kb_id, doc_id, preset)`(auto-write)。
  5. log routing 決定(profile / 套 preset / skip 原因)供觀測。
- **職責分離**:orchestrator = compute profile(純);caller = routing policy(preset + D6 + upsert)。

### PROFILE_PRESETS proposal(post-retrieval 旋鈕,對齊 D1 + 已驗 good config)

| profile | max_images | neighbour | max_aux | markers | overview_pin | answer_detail | 依據 |
|---|---|---|---|---|---|---|---|
| `P1_sop_imgdense` | 80 | on | 40 | on | on | detailed | drive-images-1 已驗 good config(D1 高 cap + 錨定 + marker)|
| `P1_sop_text` | 20 | on | 10 | on | on | detailed | D1 步驟錨定 + 低 cap(低圖)|
| `P2_prose` | 12 | **off** | — | off | off | detailed | D1 末尾堆、**唔做 neighbour 避錯位**;散文要 detailed |
| `P3_slide_imgdense` | 40 | on | 20 | on | off | concise | D1 slide imgdense 開圖流程 |
| `P3_slide_text` | 12 | off | — | off | off | concise | 文字 deck |
| `P4_scan_imgdense` | 20 | off | — | off | off | concise | D1 純 gallery(scan)|
| `P5_form` | 8 | off | — | off | off | concise | D1 table 為主、末尾堆 |
| `too_small`/`unknown` | — None(唔 routing,inherit per-KB/global)| | | | | | D7 保守 |

> ⚠️ **preset 中值(12/20/40/8)係 judgment,未逐一實證**(只 P1=drive-images-1 有 live 背書)。本段 = mechanism + 保守 default;**精確值留段③ UI 俾 admin 逐 KB 調 mapping**(D4 L3)。值可喺本 plan review 調整(R3)。

## 2. 交付物 + Gate

| # | 交付 | Gate |
|---|---|---|
| **F1** | `orchestrator.ingest()` parse 後 compute profile → `IngestionResult.profile`(best-effort);module singleton | mypy 0 + ruff 0;現有 orchestrator test 全綠(IngestionResult 加 field default None 唔 break)|
| **F2** | `profile_presets.py`(`PROFILE_PRESETS` + `preset_for`)+ `_run_ingest_pipeline` 保守 auto-write(D6 守) | mypy 0 + ruff 0;routing unit test |
| **F3** | test:profile compute / preset 值 / D6 守 / auto-write / too_small·None skip / best-effort fail | pytest 綠 + coverage(H6 — orchestrator + ingestion)|
| **F4** | 收爐:memory + closeout + 段②c/②d 交棒 + plan closed | — |

## 3. Acceptance Criteria

- **AC1(profile compute)**:ingest 成功 doc → `IngestionResult.profile` 有 `ProfileResult`(profile fail → None,唔 abort)。
- **AC2(auto-write)**:新 doc 冇 per-doc config + profile 有對應 preset → ingest 後 `DocConfigStore` 有該 doc 嘅 preset。
- **AC3(D6 守)**:doc 已有 manual per-doc `DocConfig` → ingest **唔覆蓋**(skip auto-write)。
- **AC4(保守 inherit)**:`profile ∈ {None, too_small, unknown}` → **唔 routing**(無 per-doc 寫入,inherit per-KB/global)。
- **AC5(production-preserve)**:現有 KB 唔 re-ingest → 零行為改變;`profile=None` 路徑 + 無 store 寫入時 query resolve bit-identical。
- **AC6(preset 對齊)**:`PROFILE_PRESETS[P1_sop_imgdense]` 對齊 drive-images-1 已驗 good config(cap=80 / neighbour / max_aux=40 / markers / overview_pin)→ auto-write 對 P1 不退化。
- **AC7(H6)**:orchestrator profile compute + routing(preset / D6 / skip)有 test。

## 4. 風險

- **R1 🟡 auto-write per-doc override per-KB manual**:resolver per-DOC > per-KB → auto preset 蓋過 KB owner 手調 per-KB config。緩解:① preset 值對齊已驗 good config(P1 不退化)② production-preserve — 現有 KB 唔 re-ingest 就無 auto-write ③ D6 守 per-doc manual。**殘留**:KB owner 改 per-KB 後 re-ingest → auto per-doc(hardcode preset)仍蓋過 → 段③ UI admin 還原(本段 log 套用決定供查)。
- **R2 🟢 orchestrator 加 profile step**:PDF 加 pypdfium2 pass(秒級);best-effort try/except,profile fail 唔 abort ingest。
- **R3 🟡 preset 中值未實證**:除 P1 外中值係 judgment。緩解:D7 保守傾向 + 段③ UI admin 可調 mapping;本 plan review 可改值。
- **R4 🟢 IngestionResult 契約變**:加 `profile` field default None → 現有 caller(test / populate)唔 break。

## 5. 非目標

- ❌ **段②c D8 PDF picture**(`generate_picture_images` + re-index)— stakeholder 成本決定 + 建議獨立 ADR。
- ❌ **段②d 方案 A section 級錨定**(W71 §5 net-new render)— `P1_sop_imgdense` 完整流程依賴,本段 preset 只設現有旋鈕。
- ❌ **段③ 三層 UI**(profile badge / 文件畫像 section / 分類規則設定)— 卡 H7 OQ-B。
- ❌ **admin 可調 profile→preset mapping**(D4 L3)— 段③ UI;本段 PROFILE_PRESETS 係 backend hardcode default。
- ❌ **retrieval-entry 旋鈕**(top_k/rerank/parent_doc)routing — DocConfig 唔含(per-KB only)。
- ❌ **既有 KB 批量 re-profile / re-ingest** — production-preserve,只新 ingest 觸發。

## 6. H 核對

- **H1**:改 `architecture.md §3.3` ingest flow(profiler 接入)+ `§3.7` config(auto-write per-doc)— **ADR-0056 D3 已 Accepted cover** routing 方向。無新 vendor / storage layout(DocConfigStore 已存在)。
- **H2**:零新 dep(profiler / DocConfigStore 都已有)。
- **H3**:不觸(無 Dify)。
- **H4**:profiler 純 rule + PROFILE_PRESETS deterministic mapping,零 LLM / 零 multimodal。
- **H5**:不觸(無 secret / PII)。
- **H6**:`orchestrator.py`(profile compute)+ routing(`_run_ingest_pipeline` / `profile_presets.py`)強制 test。
- **H7**:本段無 UI / 無 frontend 改動,不觸;段③ 先觸 H7 OQ-B。

## 7. Changelog

| Date | Change | Reason |
|---|---|---|
| 2026-06-13 | Initial plan(active)| W72 closeout 後用戶揀段② → 揀「②a+②b routing 接駁先」→ AskUserQuestion 揀「保守 auto-write(D6 守)」。R6 grounding 三 finding:(1) DocConfig 只 post-retrieval 旋鈕;(2) W69 preset=frontend KbConfig 唔可 reuse,routing 要 backend 自定義 profile→DocConfig;(3) 接入點 orchestrator parse 後 + routing caller `_run_ingest_pipeline`。核心風險 R1:per-doc auto preset override per-KB manual → 緩解 preset 對齊 good config + production-preserve。preset 中值未實證 = judgment,段③ UI 可調 |
| 2026-06-13 | Closeout(closed,PASS)| 用戶 confirm preset 值 → F1-F4 全成,32 pytest pass + mypy/ruff clean(`_engine_or_503` pre-existing)。實作對齊 plan:orchestrator compute(best-effort)+ caller routing policy(`_route_profile_preset` D6 守 / D7 inherit / advisory)。F3 full-HTTP-E2E routing 標 nice-to-have 未做(helper unit + reindex 唔 break 覆蓋核心)。無其他 deviation,無 deferred `[ ]` |
