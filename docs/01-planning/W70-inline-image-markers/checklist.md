# W70 — checklist(inline-image-markers)

## F1 — ADR
- [x] `docs/adr/0055-inline-image-markers-b2-dual-field.md`(B2 雙欄位 + sha8 標記語法 + per-KB 開關 + B1 reject 理據;2026-06-12 雙 session 合併稿 Accepted)
- [x] `docs/adr/README.md` index 加 0055

## F2 — chunker(marked text 組裝)
- [ ] `_SectionAccumulator` 加 ordered `flow`(paragraph / image 事件按 doc_order 入列)
- [ ] `ChunkSpec.chunk_text_marked` 欄位 + `_build_text_chunk` 組裝 marked 文字
- [ ] 三個 flush 點(`_flush_text_section` / token-cap 內 flush / `_force_flush_images`)flow 重置正確
- [ ] `_merge_adjacent_shorts` 合併 marked text
- [ ] tests:標記位置按 doc_order / `chunk_text` bit-identical / 三 flush 點 + merge case
- [ ] 既有 chunker tests 全綠

## F3 — orchestrator + index schema
- [ ] orchestrator `[IMG@n]` → `[IMG#sha8]` 改寫 pass(uploader 跳過嘅圖標記剝走)
- [ ] `ChunkRecord.chunk_text_marked` 欄位(`to_search_doc` 自動帶)
- [ ] `schema.json` 加 `chunk_text_marked`(searchable false / retrievable true)
- [ ] 現存 index PUT 遷移:先 GET 對照,再對 drive-images-1 重發 `create_index_for_kb`
- [ ] tests:sha8 改寫 / 缺 sha 剝走 / search doc 欄位形狀

## F4 — config 開關
- [ ] `backend/storage/settings.py` 加 `enable_inline_image_markers: bool = False`
- [ ] `backend/api/schemas/kb.py` KbConfig 加 knob(`bool | None = None`)
- [ ] `effective_config.py`:`PerQueryOverrides` + `EffectiveConfig` + `resolve_effective_config` 四層解析
- [ ] tests:OFF 繼承 global False / per-KB ON 覆寫 / per-query 最優先

## F5 — prompt 路徑(三條)
- [ ] `prompt_builder._format_chunk` dispatch:knob ON 用 `chunk_text_marked or chunk_text`
- [ ] `parent_doc_retriever` parent_section_text 組裝 marked 變體(knob threading)
- [ ] `context_expander` expanded_text 組裝 marked 變體(knob threading)
- [ ] system prompt 附加規則(knob-gated):重現步驟時保留 `[IMG#...]` 標記原位
- [ ] tests:OFF bit-identical / ON 三路徑都帶標記 / system rule 出現條件

## F6 — 前端(最小面)
- [ ] mockup 先行:`ekp-page-kb.jsx` tuning card 加開關行
- [ ] `kb/[id]/page.tsx`:`TuneKnobKey` + `TUNE_GROUPS` 加 `enable_inline_image_markers`
- [ ] 答案顯示 marker strip(`AnswerBodyMarkdown` + streaming 半截標記 buffer)
- [ ] tests:開關 PATCH body / strip 完整標記 / strip streaming 半截
- [ ] tsc 0 / eslint 0 / H7 fidelity check(tuning card 行對齊 mockup)

## F7 — re-index drive-images-1
- [ ] pre-flight(Langfuse 200 + Postgres SELECT 1 + backend /health + azurite)
- [ ] index PUT 更新(F3 遷移步驟)
- [ ] re-upload 全 doc(multipart runbook)→ chunk 數對齊 369 / `chunk_text_marked` 有值

## F8 — 驗證
- [ ] `scripts/run_marker_placement.py`(四指標:validity / coverage / placement accuracy / dup rate + 人工覆核表輸出)
- [ ] drive-images-1 knob ON(per-KB PATCH,跑完保留俾 W71 判斷)
- [ ] 九 query 實跑 → 報告 `reports/marker_placement_ar.yaml`
- [ ] image-recall 對照跑(knob ON)→ mean recall 對 W68 基線跌幅 ≤ 0.02
- [ ] 人工覆核 placement 錯位 → AC4 判決寫入 progress.md

## F9 — 收爐
- [ ] user-guide `03-configuration-reference.md` 加新旋鈕
- [ ] DEFERRED_REGISTER 記 copy-含標記 caveat(W71 處理)
- [ ] memory 更新 + plan closeout + progress retro
