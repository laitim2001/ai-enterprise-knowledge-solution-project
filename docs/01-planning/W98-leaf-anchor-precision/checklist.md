# W98 Checklist — Leaf-level 圖片步驟級錨定

> 對應 `plan.md` §2 Deliverables。Atomic items;每完成一項 tick + 對應 `progress.md` Day-N。
> **狀態:draft —— 待確認轉 active 先開 F1。**

## F1 — nearest-anchor 策略 + knob + 單元測試 ✅(2026-06-26）

- [x] `Settings` 加 `section_anchor_nearest: bool = False`(ADR-0040 四層,storage/settings.py)
- [x] `KbConfig` / per-doc config schema 加同名欄位(`api/schemas/kb.py` + doc_config）
- [x] `effective_config.py` resolve `section_anchor_nearest`(per-query > per-doc > per-KB > global;PerQueryOverrides + EffectiveConfig + resolve block）
- [x] `section_anchor_markers.py` 加 nearest 錨點選擇(同章節 `doc_order` 最近 anchored marker;tie → earliest offset),參數化 `nearest: bool`,default False = 現行章節最後（統一邏輯,`nearest=False` byte-identical）
- [x] knob OFF byte-identical 測試（既有 14 測試全過 + `test_nearest_defaults_false_preserves_w75`）
- [x] nearest 行為測試:多錨點 spread / 單錨點 nearest≡last 等價 / cap per-anchor 互動（4 新測試）
- [x] pytest（67 passed)+ ruff（clean)+ mypy --strict（clean,`--explicit-package-bases`）

## F2 — wire knob 經 pipeline 兩個注入點 ✅(2026-06-26)

- [x] `/query`(query.py:529)帶 `nearest=effective.section_anchor_nearest`
- [x] `/query/stream`(`_inject_stream_answer` callback,query.py:714)帶同一 knob
- [x] off bit-identical 覆蓋:effective_config 四層 resolve 測試(5 個,default False)+ 既有 route 測試全過(70 passed,default 行為不變)+ F1 function byte-identical(W75 既有 pattern:無獨立 route inject 測試,靠 effective_config + function 層)
- [x] try/except graceful 保留(未碰;注入失敗 → 原 answer)
- _note_:mypy query.py 既有 81-error baseline(line 82/203/723/767 pre-existing,非本改動;529/714 唔在 list)→ §1.3 surgical 唔掂無關 error

## F3 — cap 互動 + drive-images-1 config 決定 ✅(2026-06-27)

- [x] cap-sweep（`scripts/diag_leaf_anchor_capsweep.py`,offline reuse 18 captures)量 `{last,nearest} × cap∈{0,3,5,8}` 嘅 clump/placed/trailing trade（`reports/leaf_anchor_capsweep.json`）
- [x] 揀 drive-images-1 推薦 config = **nearest + cap8**（用戶 2026-06-27 拍板;置 218/235 vs 現 79、trailing 156→17、clump 最壞 38→12）
- [x] cap 惡化可接受性已決:nearest 每 cap 壓倒 last;§15 角度 trailing（還原失敗)比 clump（密但近步驟)更傷 → 用戶取 §15 優先 + clump 受控（cap8 最壞 12）

## F4 — production A/B + browser 肉眼

- [ ] 重啟 backend pick up code(確認啟動時間 ≥ 最後 commit;reload=False stale）
- [ ] image-recall A/B(`run_image_recall`)— knob ON 唔回退(≈1.0)
- [ ] marker order-consistency(`check_marker_order`)— 唔回退(local_swap 0)
- [ ] clump 量化(diag harness running-backend 或 offline apply)— 確認降
- [ ] browser 肉眼高圖密 query(Q001/Q036)— 圖分散到步驟、末尾堆唔回歸、無新 clump regression(W75 DD-1 教訓)

## F5 — doc-sync + ADR amendment + close

- [ ] ADR-0056 加 leaf-級 amendment(注入錨點策略 last→nearest + knob `section_anchor_nearest`）
- [ ] memory [[project_inline_image_markers_w70]] + [[principle_source_fidelity_recall]] 更新(甲類 leaf 級落地）
- [ ] `DEFERRED_REGISTER.md`「leaf 級精準錨」close
- [ ] `docs/08-user-guide` 若涉 default / knob 同步(per 其 README 維護規則)
- [ ] production default flip 列另一決定(out-of-scope,需 F4 正向 + 再確認)
- [ ] G-W98 Phase Gate verdict 入 progress retro
