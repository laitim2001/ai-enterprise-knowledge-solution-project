# W75 checklist — section-anchored aux images(方案 A)

> tick 規則:完成 `→ [x]`;延後 `[ ]` + 🚧 + reason + target(不可刪)。每 commit 對應 ≥1 項(R2)。

## F1 — config knob 四層

- [x] F1.1 `settings.py` 加 `enable_section_anchored_aux_images: bool = False`(mirror :160 inline marker)
- [x] F1.2 `effective_config.py` `QueryConfigOverlay` 加 `enable_section_anchored_aux_images: bool | None = None`
- [x] F1.3 `effective_config.py` `EffectiveConfig` 加 `enable_section_anchored_aux_images: bool`
- [x] F1.4 `effective_config.py` `_resolve` 四層(pq → dc → kb → settings)
- [x] F1.5 `kb.py` `KbConfig` 加 `enable_section_anchored_aux_images: bool | None = None`
- [x] F1.6 `doc_config.py` `DocConfig` 加 `enable_section_anchored_aux_images: bool | None = None`
- [x] F1.7 mypy --strict 0 + ruff 0

## F2 — inject function + query.py wire

- [x] F2.1 新 module `backend/generation/section_anchor_markers.py` `inject_section_anchored_markers(answer, citations, *, section_prefix_depth=1)`
- [x] F2.2 演算法:抽已有 anchored sha8 → 建 sha8→source_section → un-anchored set → 同章節 match → 插 marker(doc_order 排,back-to-front splice)
- [x] F2.3 query.py wire:**/query**(line 499 前 inject `final_synth.answer`)+ **/query/stream**(`compose_query_stream` 新 `answer_post_process` callback,done event answer);兩處 gate + try/except graceful
- [x] F2.4 mypy --strict 0(新 code 0;剩 6 pre-existing 我冇 touch)+ ruff 0

## F3 — test

- [x] F3.1 inject pure function test:同章節 un-anchored 圖錨定入答案
- [x] F3.2 inject test:無同章節 anchored marker → 不注入(留 trailing)
- [x] F3.3 inject test:doc_order 排序 + no-marker/全錨定/空 citations no-op + dedup by sha8 + 多章節 + 最後一個錨點 + too-shallow skip(共 10 case)
- [x] F3.4 resolve 四層 test(`test_effective_config` append 5 case)
- [x] F3.5 pytest 綠(H6):51 passed(inject 10 + W75 resolve 5 + stream_composer 既有)+ query route 48 passed(wire 唔 break)

## F4 — preset 接駁 + 實測 + 收爐

- [x] F4.1 `profile_presets.py` P1_sop_imgdense preset 加 `enable_section_anchored_aux_images=True`(只 P1 圖密;test_profile_routing assert 加;7 passed)
- [x] F4.2 實測 drive-images-1 真實 /query(舊 code capture answer+citations,offline apply inject)末尾堆 **28-85% → 0%**(3 query 全錨,注入 8-52 圖/query;章節級可錨率 100% 兌現)
- [x] F4.3 memory `project_inline_image_markers_w70.md` append 方案 A 落地 + MEMORY.md 2 pointer(inline-markers 全弧 + config-vision 段②d)
- [x] F4.4 closeout:plan status closed + progress retro + 段③/leaf 級交棒

## F5 — 每錨點 cap(DD-1 後 clump 優化,reopen)

- [ ] F5.1 `settings.py` 加 `section_anchor_max_per_anchor: int = 0`(0 = 無 cap)
- [ ] F5.2 `effective_config.py` QueryConfigOverlay(`int | None`)+ EffectiveConfig(`int`)+ _resolve 四層
- [ ] F5.3 `kb.py` + `doc_config.py` 加 `section_anchor_max_per_anchor: int | None = None`
- [ ] F5.4 inject 函數加 `max_per_anchor: int = 0` 參數(每章節 doc_order 前 N,超出不注入留 trailing)
- [ ] F5.5 query.py 兩處傳 `max_per_anchor=effective.section_anchor_max_per_anchor`
- [ ] F5.6 test:cap 截斷(每章節前 N)+ 0 = bit-identical(無 cap)+ resolve 四層
- [ ] F5.7 mypy 新 code 0 + ruff 0 + pytest 綠
- [ ] F5.8 實測 browser:不同 N(如 3/5/8)clump maxRun 改善 + 末尾堆回歸量 + 肉眼確認
- [ ] F5.9 closeout:plan closed + progress + memory
