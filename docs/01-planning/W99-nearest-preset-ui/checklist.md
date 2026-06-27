# W99 Checklist — nearest 融入自動配對 + 前端 UI

> 對應 `plan.md` §2 Deliverables。每完成一項 tick + 對應 `progress.md` Day-N。

## F1 — backend preset 自動配對

- [ ] `profile_presets.py` P1_sop_imgdense 加 `section_anchor_nearest=True`
- [ ] `profile_presets.py` P1_sop_imgdense `section_anchor_max_per_anchor` 5→8（對齊 drive-images-1 F3）
- [ ] `test_profile_routing.py` `test_p1_imgdense_preset_aligns_good_config` 加 nearest assertion + cap 5→8
- [ ] pytest（profile_routing + 相關）+ ruff + mypy --strict clean

## F2 — frontend 3 surface expose nearest

- [ ] `doc-config.ts` DocConfig interface 加 `section_anchor_nearest?: boolean | null`
- [ ] `doc-config-tab.tsx` `DOC_TUNE_KNOB_KEYS` 加 `'section_anchor_nearest'`
- [ ] `doc-config-tab.tsx` W81 image-anchor group 加 nearest `DocSwitchKnob`（跟既有 pattern）
- [ ] `settings-doc-profiling.tsx` EditPresetDialog section-錨定 field 加 nearest toggle
- [ ] `settings-doc-profiling.tsx` `fmtAnchor` table cell 反映 nearest 狀態
- [ ] H7 self-check:零新 component / 零新視覺 / 跟既有 design-stage expansion 方案 A
- [ ] `pnpm lint` + 既有/新 frontend test 綠

## F3 — verify + doc-sync + close

- [ ] running backend `GET /profile-presets` P1_sop_imgdense 反映 nearest+cap8
- [ ] ADR-0056 §Amendment 更新（preset-level flip done,non-global default）
- [ ] memory [[project_per_kb_tunable_config_vision]] append W99 段 + [[project_inline_image_markers_w70]] 註
- [ ] G-W99 Phase Gate verdict 入 progress retro
