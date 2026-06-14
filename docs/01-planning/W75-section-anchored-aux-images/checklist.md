# W75 checklist — section-anchored aux images(方案 A)

> tick 規則:完成 `→ [x]`;延後 `[ ]` + 🚧 + reason + target(不可刪)。每 commit 對應 ≥1 項(R2)。

## F1 — config knob 四層

- [ ] F1.1 `settings.py` 加 `enable_section_anchored_aux_images: bool = False`(mirror :160 inline marker)
- [ ] F1.2 `effective_config.py` `QueryConfigOverlay` 加 `enable_section_anchored_aux_images: bool | None = None`
- [ ] F1.3 `effective_config.py` `EffectiveConfig` 加 `enable_section_anchored_aux_images: bool`
- [ ] F1.4 `effective_config.py` `_resolve` 四層(pq → dc → kb → settings)
- [ ] F1.5 `kb.py` `KbConfig` 加 `enable_section_anchored_aux_images: bool | None = None`
- [ ] F1.6 `doc_config.py` `DocConfig` 加 `enable_section_anchored_aux_images: bool | None = None`
- [ ] F1.7 mypy --strict 0 + ruff 0

## F2 — inject function + query.py wire

- [ ] F2.1 新 module `backend/generation/section_anchor_markers.py` `inject_section_anchored_markers(answer, citations, *, section_prefix_depth=1)`
- [ ] F2.2 演算法:抽已有 anchored sha8 → 建 sha8→source_section → un-anchored set → 同章節 match → 插 marker(doc_order 排)
- [ ] F2.3 query.py post-`pin_chapter_overview_images` gate wire(`effective.enable_section_anchored_aux_images` ON → call;try/except graceful)
- [ ] F2.4 mypy --strict 0 + ruff 0

## F3 — test

- [ ] F3.1 inject pure function test:同章節 un-anchored 圖錨定入答案
- [ ] F3.2 inject test:無同章節 anchored marker → 不注入(留 trailing)
- [ ] F3.3 inject test:doc_order 排序 + knob OFF/不 call → answer bit-identical
- [ ] F3.4 resolve 四層 test(`test_effective_config` append)
- [ ] F3.5 pytest 綠(H6)

## F4 — preset 接駁 + 實測 + 收爐

- [ ] F4.1 `profile_presets.py` P1_sop_imgdense preset 加 `enable_section_anchored_aux_images=True`
- [ ] F4.2 實測 drive-images-1(per-KB knob ON)/query 末尾堆 22-55% → 大幅縮小驗證
- [ ] F4.3 memory `project_inline_image_markers_w70.md` append 方案 A 落地
- [ ] F4.4 closeout:plan status closed + progress retro + 段③ 交棒
