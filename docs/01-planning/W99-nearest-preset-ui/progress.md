# W99 Progress — nearest 融入自動配對 + 前端 UI

> Daily progress + decisions + commits + 結尾 retro。對應 `plan.md` / `checklist.md`。

## Day 1（2026-06-27）— kickoff（active）

**Context**:W98 收尾後,用戶問「W98 嘅功能有冇配合到之前建立嘅自動分析判斷文件 → 分配配置策略?又是否可以喺頁面自行設定?」。查代碼確認:`section_anchor_nearest`（W98 knob）**未入** `profile_presets.py`（grep 11 檔無一係 profile_presets.py）+ **未上**前端（doc-config-tab 得返舊 section-anchor knob）。用戶 2026-06-27 批准「接埋呢兩步令 W98 同願景完全融合」。

**開工前讀 4 surface 確認既有 pattern**（Karpathy §1.1 think-before-coding,memory 數日舊先對代碼）:
- `profile_presets.py` — P1_sop_imgdense 而家 cap=5,無 nearest;只有 P1_sop_imgdense 開 `enable_section_anchored_aux_images`（nearest 只對佢有意義）。
- `doc-config-tab.tsx` — `DOC_TUNE_KNOB_KEYS` array 加 key 即自動 wire setKnob/dirty/save;W81 image-anchor group（line 487-505）用 `DocTuneGroup` + `DocSwitchKnob` + `DocTuneKnob`,user-approved 方案 A 零新視覺。
- `settings-doc-profiling.tsx` — EditPresetDialog draft 由完整 effective config spread（PUT full replacement → 隱藏 field 唔會洗走）;section-錨定 field 有 toggle+cap input。
- `test_profile_routing.py` — `test_p1_imgdense_preset_aligns_good_config` assert cap==5 等,改 preset 要同步。

**順帶決定（向用戶 surface）**:preset cap 5→8 對齊 drive-images-1（F3 §15 sweet spot）,令新 ingest P1 文件唔比 drive-images-1 差。

**今日產出**:W99 三件套（plan / checklist / progress）。F1-F3 分段:backend preset 自動配對 → frontend 3 surface → verify + doc-sync。

**H1**:屬 W98 ADR-0056 §Amendment 列明嘅「另一決定」preset-level flip（非 global default flip,`Settings.section_anchor_nearest` 仍 False）→ ADR-0056 §Amendment 更新,非新 ADR。

**Commits（Day 1）**:
| Hash | Subject | 對應 |
|---|---|---|
| (本 commit) | docs(planning): W99 kickoff | F0 kickoff |
