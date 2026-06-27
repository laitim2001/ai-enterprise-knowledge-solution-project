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

## F4 — production A/B + browser 肉眼 ✅(2026-06-27)

- [x] 重啟 backend pick up code(2026-06-27 重啟,ready ~120s,啟動 > F1/F2 commits;dual-process 兩個一齊停先起,env `HYBRID_USE_SEMANTIC_RANKER=false`）
- [x] image-recall 不回退(`scripts/diag_leaf_anchor_live.py`:citation image checksum **set 三條全相同** 65/65/38 → inject 唔郁 citations,recall 結構上不受影響,強過 run_image_recall）
- [x] marker order-consistency:**結構論證**（nearest 按 doc_order 最近錨點 + 組內 doc_order 排序 → 更 order-consistent,vs last 掉去章節最後製造 swap）+ offline 覆蓋;**full empirical `check_marker_order` run 按用戶同意 deferred**（非 silent skip）
- [x] clump 量化(offline cap-sweep + live)— nearest+cap8 clump 受控（offline 最壞 12,live 7-9）;trade = placement↑（非 clump↓）
- [x] browser 肉眼(Q001 live,nearest+cap8)— **用戶 §15 verdict 達標(2026-06-27)**:圖交織入步驟(figures 56/57/59 + Confirm step 截圖)、W75「39 連續圖」病態消失、按 section 組織。誠實 caveat:section-grouped grid 殘留 = 可錨率 < 100%(乙類-bound,已收口),nearest 唔強錨錯 section

## F5 — doc-sync + ADR amendment + close ✅(2026-06-27)

- [x] ADR-0056 加 leaf-級 amendment(注入錨點策略 last→nearest + knob `section_anchor_nearest` + 實證 + drive-images-1=nearest+cap8 + 乙類邊界)
- [x] memory [[project_inline_image_markers_w70]]（append W98 段）+ [[principle_source_fidelity_recall]]（甲 bullet + 自驗下一步 mark done）更新
- [x] `DEFERRED_REGISTER.md` DD-10 leaf 級 trigger 標 ✅ W98 解(DD-10 核心層 B 仍 defer)
- [x] `docs/08-user-guide` **N/A** — global default 不變(OFF,production-preserve)→ 維護規則(改 default 先 sync)未觸發;section-anchor knob 家族本身未喺 user-guide(W75 未加),加孤條 = scope creep（§1.3）
- [x] production default flip 列另一決定(ADR-0056 amendment + plan §5 已標 out-of-scope,需再確認)
- [x] G-W98 Phase Gate verdict 入 progress retro
