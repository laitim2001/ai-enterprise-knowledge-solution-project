# W68 — checklist(dedup-before-cap,ADR-0054)

## F1 — ADR
- [ ] `docs/adr/0054-dedup-before-cap-image-budget.md`(Accepted,approver Chris 2026-06-12)
- [ ] `docs/adr/README.md` index 加行

## F2 — code
- [ ] `cap_images_per_answer` 改寫(unique 預算 + dup 剪走;None passthrough 不變)+ docstring 指 ADR-0054
- [ ] ruff check + format clean

## F3 — tests
- [ ] 改寫 `test_cap_trims_cumulative_total_across_citations`(distinct checksums)+ `test_cap_above_total_keeps_objects_untrimmed`(同)
- [ ] 新增:dup 唔食預算 / dup 喺預算內都剪 / within-citation dup
- [ ] `test_effective_config.py` + `test_ch010_chapter_overview_pin.py` + `test_config_test_route.py` 全綠

## F4 — A/B 驗證
- [ ] backend 重啟(載新 code)+ health
- [ ] 9/9 image-recall run @ cap=70(F5 先 persist)→ `reports/image_recall_ar_dedup_cap70.yaml`
- [ ] AC3:Q001 ~1.00 / Q043 升幅記錄 / 對照 1.00 / precision ≥0.95

## F5 — persist
- [ ] PATCH drive-images-1 cap 50→70 + readback=70(喺 F4 run 之前做,A/B 即係 persisted 終態)

## F6 — 收爐
- [ ] rollup + memory + plan closeout + progress retro
