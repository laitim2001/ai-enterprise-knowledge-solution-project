# W99 — nearest 錨點融入自動配對 + 前端 UI(願景融合）

| 項目 | 值 |
|---|---|
| Phase | W99-nearest-preset-ui(ADR-0056 層 A 段②d leaf 級 productionize 收尾 · 願景融合）|
| Status | **active**（用戶 2026-06-27 批准「接埋兩步令 W98 同願景完全融合」→ 直接開工）|
| Tier | Tier 1（改 `profile_presets.py` 自動配對 + 3 前端 surface expose 既有 knob;無新 vendor / 無檢索改動）|
| 依賴 | W98（`section_anchor_nearest` knob 四層 + drive-images-1=nearest+cap8 已落地）+ ADR-0056 層 A（profiler 六類 + profile→preset 自動配對 W73 + 三層 UI W78-82）|
| 錨點 | ADR-0056 §Amendment(W98)「default flip = 另一決定」· W98 plan §下一期 · CLAUDE.md §15 北極星 · memory [[project_per_kb_tunable_config_vision]] 願景 |
| 粗估 | 細-中（F1 backend 1 preset + 1 test;F2 frontend 3 surface + test;F3 verify + doc-sync + close）|

> **H1 gating**:本 phase **唔改架構** ——（a）`profile_presets.py` P1_sop_imgdense 加 `section_anchor_nearest`（W98 已存在嘅 knob,只係寫入 preset 值）+ cap 5→8（對齊 drive-images-1 F3 §15 決定）;（b）前端 3 surface expose 同一 knob,跟既有 design-stage expansion 方案 A 零新視覺。屬 W98 ADR-0056 §Amendment 明文列為「另一決定」嘅 **preset-level flip**（**非 global default flip** — `Settings.section_anchor_nearest` 仍 False）→ **ADR-0056 §Amendment 更新**（非新 ADR）。Global default 不變 = 非 P1 / 其他 KB production-preserve。

## §1 目標(Why)

**現狀缺口(W98 收尾後發現)**:W98 落地咗 `section_anchor_nearest` knob（四層 config）+ 為 drive-images-1 人手 set（per-KB nearest+cap8）。但呢個新 knob **未融入 ADR-0056 願景嘅兩個 surface**:
1. **未入自動配對** —— `profile_presets.py` 嘅 `P1_sop_imgdense` preset 冇 `section_anchor_nearest`,所以**新 ingest** 嘅圖密 SOP 文件唔會自動有 nearest（要人手 set）。
2. **未上前端** —— per-doc config tab + admin preset 映射 UI 得返舊嗰批 section-anchor knob，冇 nearest toggle，用戶喺頁面調唔到。

**目標**:把 W98 嘅 nearest 接入呢兩個 surface,令「自動判斷文件 → 自動配對策略」+「頁面自助調試」對 nearest 都成立 —— W98 同 ADR-0056 願景**完全融合**。

**北極星(§15)**:令**新上載**嘅圖密 SOP 文件,一 ingest 就自動得到同 drive-images-1 一樣嘅圖文還原體驗（圖錨到對應步驟,非堆章節尾）。

## §2 Deliverables(F1–F3)

| # | Deliverable | Acceptance |
|---|---|---|
| **F1** | `profile_presets.py` P1_sop_imgdense 加 `section_anchor_nearest=True` + `section_anchor_max_per_anchor` 5→8（對齊 drive-images-1 F3 §15 sweet spot,令新 P1 文件唔比 drive-images-1 差）+ update `test_profile_routing.py` P1 assertion | preset 含 `section_anchor_nearest is True` + `cap == 8`;`_route_profile_preset` auto-write 帶 nearest（既有 routing test 覆蓋）;**只改 P1_sop_imgdense**（其他 profile 冇開 `enable_section_anchored_aux_images` → nearest 無意義,不碰 = D7 保守 + §1.3 surgical）;pytest + ruff + mypy clean |
| **F2** | 前端 3 surface expose `section_anchor_nearest`:（a）`doc-config.ts` DocConfig type 加 field;（b）`doc-config-tab.tsx` W81 image-anchor group 加 nearest `DocSwitchKnob` + key 入 `DOC_TUNE_KNOB_KEYS`;（c）`settings-doc-profiling.tsx` EditPresetDialog section-錨定 field 加 nearest toggle + `fmtAnchor` table 顯示 | nearest 喺 per-doc tab 可調（繼承/覆寫/還原 = 跟既有 `DocSwitchKnob` pattern）;admin preset editor 可調 + table 反映;**跟既有 design-stage expansion 方案 A 零新視覺**（H7 self-check:無新 component / 無新 mockup deviation,複用 `DocSwitchKnob` + `.switch` row）;`pnpm lint` + 既有/新 test 綠 |
| **F3** | 端到端 verify + doc-sync + close | （a）`GET /profile-presets` P1_sop_imgdense 反映 nearest+cap8（running backend）;（b）ADR-0056 §Amendment 更新（preset-level flip done,non-global）;（c）memory [[project_per_kb_tunable_config_vision]] append W99 段 + [[project_inline_image_markers_w70]] 註 nearest 入 preset;（d）G-W99 verdict 入 progress retro |

## §3 Phase Gate

- **G-W99**:F1 preset 含 nearest+cap8 + test 綠（production-preserve:只 P1_sop_imgdense,其他 profile / global default 不變）+ F2 三 surface 可顯示可調 + frontend lint/test 綠 + H7 self-check（零新視覺,跟既有 expansion pattern）+ 端到端 `GET /profile-presets` 反映 + ADR-0056 §Amendment 更新。
- 若 F2 任何 surface 要新 mockup component（非複用既有 `DocSwitchKnob`/`.switch`）→ **STOP per §5.7 H7**,先確認。

## §4 Risks

- 🟡 **cap 5→8 影響將來 P1 文件**:F3 cap-sweep 已證 cap8 clump 最壞 12（vs cap5 之 9）—— 用戶 W98 為 drive-images-1 已接受呢個 §15-優先 trade;P1 一致化採同一決定。**向用戶 surface**（順帶決定）。
- 🟡 **admin preset PUT full replacement**:`settings-doc-profiling.tsx` draft 由完整 effective config spread（line 256）→ 即使唔加 UI toggle nearest 都唔會被洗走;加 toggle = 令 admin **可調** + 透明（非防洗走）。
- 🟢 **H7**:3 surface 全屬 W78/W81/W82 已 user-approved design-stage expansion（mockup 無 doc-level/preset-edit design,方案 A 零新視覺）→ 加 nearest 跟同 group/dialog 既有 toggle pattern,不 introduce 新 deviation。self-check 確認 visual consistency。
- 🟢 **零新 vendor / dep / 檢索改動**;blast radius 細（1 backend preset + 3 frontend surface)。
- 🟢 **現有文件不受影響**:改 preset 只影響**將來 ingest**（auto-write per-doc,D6 守 manual override）;drive-images-1 已 per-KB set,照行。

## §5 Out of scope(留後續)

- **Global default flip**（`Settings.section_anchor_nearest` OFF→ON）= 仍係另一決定;本 phase 只做 **preset-level**（P1_sop_imgdense)+ UI。非 P1 / 其他 KB 維持 global default OFF。
- **其他 profile 加 nearest**:P1_sop_text / P3_slide_* 冇開 `enable_section_anchored_aux_images`,nearest 無效;P2/P4/P5 散文/掃描/表單唔做 section 錨定 → 不碰。
- **leaf 級 full empirical `check_marker_order`**（W98 deferred,沿用結構論證）。
- **現有 P1 文件 backfill nearest**:可用既有 W80 backfill route,但屬另一觸發,本 phase 不做。

## §6 Changelog

| 日期 | 變動 | 由 |
|---|---|---|
| 2026-06-27 | Phase kickoff（active）— 用戶 2026-06-27 批准「接埋兩步令 W98 同願景完全融合」。先讀 4 surface 確認既有 pattern（`profile_presets.py` / `doc-config-tab.tsx` / `settings-doc-profiling.tsx` / `test_profile_routing.py`）→ 寫 plan。F1 backend preset（nearest+cap8）→ F2 frontend 3 surface → F3 verify + doc-sync。cap 5→8 對齊 drive-images-1 = 順帶決定,向用戶 surface。**ADR-0056 §Amendment 更新（preset-level flip,non-global）** | kickoff |
