# W81 checklist — L3 image-anchor knobs UI(缺口 A,ADR-0060)

> tick 規則:完成 `→ [x]`;延後 `[ ]` + 🚧 + reason + target(不可刪)。每 commit 對應 ≥1 項(R2)。

## F1 — L3 image-anchor 旋鈕組(frontend)

- [x] F1.1 `doc-config.ts` `DocConfig` interface 加三 optional 欄位(`enable_inline_image_markers` / `enable_section_anchored_aux_images` / `section_anchor_max_per_anchor`,mirror backend)
- [x] F1.2 `doc-config-tab.tsx` `DOC_TUNE_KNOB_KEYS` 加三 key(自動納入 setKnob/buildDraftConfig/dirty/overriddenCount/saveMutation)+ import `Tag` + docstring 補 ADR-0060 design-stage expansion note(誠實標記 mockup 之外偏離)
- [x] F1.3 新 `DocTuneGroup`「Inline 圖文錨定」(icon=Tag)插「Citation neighbour images」組後:toggle=`enable_inline_image_markers` + children(`DocSwitchKnob` section 錨定 + `DocTuneKnob` 每錨點 cap)+ hint 文案
- [x] F1.4 type-check 0 + lint 零新 warning(唯一 warning = line 1858 `<img>` 別檔 pre-existing)+ **build ✓**(exit 0,15 路由含 `/kb/[id]/docs/[docId]` 通過);視覺用既有 component(零發明)

## F2 — 驗證 + browser

- [x] F2.1 type-check / lint / build 全綠
- [x] F2.2 browser(playwright)驗:L3「Inline 圖文錨定」`DocTuneGroup` render(toggle + collapsible 進階)+ 三旋鈕(inline marker toggle + section 錨定 `DocSwitchKnob` + 每錨點 cap `DocTuneKnob`,switch×2 + input×1,全用既有「繼承 KB / 未覆寫」badge 模式 = **視覺零發明 H7 OK**)+ **UI 寫端到端 PASS**(toggle inline marker → badge「已覆寫」+ save enable → 儲存 → `PUT /config` persist `enable_inline_image_markers=true`,API GET 確認)+ DELETE 還原全 null 零污染;console 7 errors 全 `/notifications` 404 pre-existing 無害(非我引入)

## F3 — closeout

- [x] F3.1 type-check/lint/build + browser 全綠
- [x] F3.2 closeout:plan closed + progress retro + ADR-0060 README index(kickoff done)+ memory append
