# W44 — Chunker Image-Density Deep Fix · Checklist

> Atomic items per deliverable(plan §2)。F1+ GATED on F0 PASS。

## F0 — H1 STOP+ask gate ✅ PASS 2026-06-03
- [x] F0.1 Present ADR-0041 H1 boundary + 決策 2 切法選項(A/B/C/D)+ 風險(重切影響 recall)
- [x] F0.2 Chris confirm H1 + 揀**切法 D 混合** + cap default **8**(tolerance 沿 ±2pp)
- [x] F0.3 ADR-0041 Status Proposed → Accepted(切法 D + cap 8)
- [x] F0.4 plan §3 G1 回填 cap **8** + §7 changelog 記 F0 結果

## F1 — Chunker 切法 D(混合) ✅ 2026-06-03
- [x] F1.1 `layout_aware.py` text flush 同步 reset `image_positions`(修 `:207`/`:213-218` pile-on) — `_reset_images_on_flush` gated on cap
- [x] F1.2 `max_images_per_chunk` soft cap **8** force-split(延續 `section_path`,prev/next 連續) — `_force_flush_images` + image-event trigger
- [x] F1.2b `_should_merge` 加 image-count guard(merge 後超 cap 唔 merge)
- [x] F1.3 新 `Settings.chunker_max_images_per_chunk=8` knob(`None`/0 = bit-identical;+ `_flush_text_section` residual-image guard 防 force-split 後殘圖丟失)
- [x] F1.4 `LayoutAwareChunker.__init__` wire knob;`server.py:99` 傳 `settings.chunker_max_images_per_chunk`(orchestrator 用 injected chunker)
- [x] F1.5 ruff(我新增 code clean;layout_aware reformatted。server.py E402 + test pytest F401 = pre-existing 非本次引入)+ mypy(我新增 code clean;17 pre-existing errors = parsers docling stub + 既有 object→ParagraphItem assign)

## F2 — Chunker unit test(H6 mandatory) ✅ 2026-06-03 — pytest 30 passed
- [x] F2.1 新 image-flush 分配 test(圖隨 doc_order 落正確 sub-chunk) — `test_w44_image_cap_no_image_loss`
- [x] F2.2 `max_images_per_chunk` cap force-split test — `test_w44_image_cap_force_splits_dense_section`
- [x] F2.3 default(`None`/0)= 今日行為 bit-identical regression test — `test_w44_cap_none_preserves_whole_section_pile_on` + `test_w44_under_cap_doc_identical_to_no_cap`
- [x] F2.4 既有 ADR-0033 merge + BUG-017 sibling-guard 無 regression(24 既有全綠)+ `test_w44_merge_image_guard_*` + `test_w44_residual_images_flushed_*`

## F3 — Re-index + presentation 驗證 ✅ 2026-06-03 (G1/G2 PASS)
- [x] F3.1 pre-flight(Langfuse 200 / Postgres / backend venv restart 載新 code — ready ~100s,全 component ok)
- [x] F3.2 doc-level reindex 圖密文件(AR `test-kb-20260531-v1` doc `drive-user-manual-0601-ar-...`)重切 → 68→90 chunks,223 img uploaded
- [x] F3.3 **G1 PASS**:max single-chunk 圖數 **57 → 8**(cap 嚴格守)
- [x] F3.4 **G2 PASS**:分佈 baseline(57/27/25/23/18/16/14/12/12/11 多 mega)→ 重切後 0 個 >8、22 chunks at cap;223 unique 全保留(無丟失)

## F4 — Eval no-regression gate(top risk) — 🔄 擴展為 gold-eval rigor track(2026-06-03 user pick)
> 原 F4.1-F4.3 單次 eval 方案被 eval-harness decay 揭示不足(Cohere 連打 rate-limit 401 + eval-set-v1-draft Q14 SME-validation pending empty-GT + before-baseline reindex 走)。User pick 全 rigor 重建。原 items superseded(唔刪,per sacred rule):
- [~] F4.1 重切前 baseline eval — 🚧 superseded:單次 eval 撞 harness decay,改 cap=None before 重建(F4.7)
- [~] F4.2 重切後 eval — 🚧 superseded:改 cap=8 after(F4.8)+ 隔離對比(F4.9)
- [ ] F4.3 Gate verdict → Chris 拍板(待 rigor track 完成;切法 D core no-regression 已三源證實:G1/G2 硬證 + pytest text bit-identical + sanity query healthy)
### Rigor sub-track(gold no-regression,跨 session)
- [ ] F4.4 Cohere 401 rate-limit throttle/retry(eval code)— 我做,所有後續 eval 依賴
- [ ] F4.5 跑 `scripts/discover_chunk_ids.py` 生成 30 main candidate chunk_ids — 我做
- [ ] F4.6 SME GT cascade:Chris pick `acceptable_chunk_ids` + `validated:true`(Q14)— 🚧 BLOCK,需 Chris 人手(AI 做唔到 gold GT)
- [ ] F4.7 cap=None reindex drive(舊 chunker before baseline)+ eval(SME GT)
- [ ] F4.8 cap=8 reindex drive(after)+ eval(SME GT)
- [ ] F4.9 隔離對比 G3/G4(同 GT 同條件,唯一變 cap)→ `scripts/validate_eval_set.py` + Chris gate verdict

## F5 — Closeout
- [ ] F5.1 architecture.md §3.3 amend(inline-tag image-distribution + cap,沿 §3.4/§3.7 precedent)
- [ ] F5.2 ADR-0041 validation note(gate verdict + 實測前後圖數)
- [ ] F5.3 plan/checklist/progress flip closed + retro
- [ ] F5.4 session-start §10 W44 row + roadmap §3 W44 done + [AUDIT-A] 實測數回填
- [ ] F5.5 commit cascade(對應 progress Day-N,R2)
