# W81 plan — L3 暴露 inline marker + section 錨定旋鈕(缺口 A,ADR-0060 落地)

**Status**: closed(2026-06-15,full PASS — F1 frontend + type-check/lint/build + browser UI 寫端到端 PASS)
**Kickoff**: 2026-06-15
**Phase 類型**: frontend feature(H7 design-stage expansion + H1-adjacent;ADR-0060 已 Accepted)
**ADR**: ADR-0060(L3 image-anchor knobs UI — 用戶揀方案 A 復用既有模式延伸)

---

## §1 Context / 緣起

「層 A UI 可調性 gap 分析」坐實**缺口 A**:backend `DocConfig` 支援三個圖錨後處理旋鈕的 per-doc 覆寫,但
L3 `doc-config-tab.tsx` UI 從未暴露:`enable_inline_image_markers`(W70)/ `enable_section_anchored_aux_images`
+ `section_anchor_max_per_anchor`(W75)。`PUT /config` 已能寫(backend 零缺口)。

**H7**:inline marker 喺 mockup KB 層有 `KbTuneGroup` 設計;section 錨定 mockup + KB 層 frontend **都冇**
→ 觸 H7。用戶 STOP+ask 後揀**方案 A**(復用既有 mockup-aligned component 延伸,視覺零發明,記 ADR-0060)。

**落點 grounding(plan kickoff,R6)**:
- `doc-config.ts` `DocConfig` interface(`lib/api/`,line 20-31)— 加三 optional 欄位 mirror backend。
- `doc-config-tab.tsx` `DOC_TUNE_KNOB_KEYS`(line 94-104)— 加三 key → `setKnob`(186)/ `buildDraftConfig`
  (215)/ `dirty`(198)/ `overriddenCount`(204)/ `saveMutation`(`PUT /config`)**自動納入**(零新 plumbing)。
- 既有 component:`DocTuneGroup`(652,toggle+children)/ `DocSwitchKnob`(589,bool)/ `DocTuneKnob`(531,
  number)— 全 mockup-aligned(W78)。
- 插入點:現有「Citation neighbour images + 圖片上限」`DocTuneGroup`(line 442-470)之後,card-body 內。
- **backend 零改動**(`DocConfig` schema + `PUT /config` 已支援三欄位)。

---

## §2 Scope / Deliverables

### F1 — L3 image-anchor 旋鈕組(frontend)
- **F1.1** `doc-config.ts` `DocConfig` interface 加三 optional 欄位:`enable_inline_image_markers?: boolean | null`
  / `enable_section_anchored_aux_images?: boolean | null` / `section_anchor_max_per_anchor?: number | null`。
- **F1.2** `doc-config-tab.tsx` `DOC_TUNE_KNOB_KEYS` 加三 key(自動納入 setKnob/buildDraftConfig/dirty/
  overriddenCount/saveMutation)。
- **F1.3** 新 `DocTuneGroup`「Inline 圖文錨定」(icon=`Tag`)插「Citation neighbour images」組後:
  - toggle = `enable_inline_image_markers`(主 gate)+ onReset → null。
  - children:`DocSwitchKnob`「section 錨定 aux 圖(末尾堆→章節內)」= `enable_section_anchored_aux_images`
    + `DocTuneKnob`「每錨點圖片上限(0=無 cap)」= `section_anchor_max_per_anchor`。
  - hint 文案解釋圖文錨定 + section 錨定 + cap(對齊 mockup KB 層 inline marker desc 語氣)。
- **acceptance**:type-check 0 + lint 零新 warning + build ✓;視覺用既有 component(零發明)。

### F2 — 驗證 + browser
- type-check / lint / build 全綠。
- browser(playwright)驗 L3 顯示新「Inline 圖文錨定」組 + 三旋鈕可調 → 改值 → `PUT /config` persist
  → GET /config 確認(drive-images-1 一個 doc;改完還原免污染)。
- **acceptance**:三旋鈕真實可寫(非 static);對齊既有旋鈕視覺(badge / 還原 / 繼承)。

### F3 — closeout
- type-check/lint/build + browser 全綠;plan closed + progress retro + ADR-0060 README index + memory。

---

## §3 設計原則(ADR-0060)

1. **視覺零發明** — 全用既有 `DocTuneGroup`/`DocSwitchKnob`/`DocTuneKnob`(mockup-aligned)。
2. **backend 零改動** — reuse `DocConfig` + `PUT /config`(三欄位已支援)。
3. **零新 plumbing** — 加 `DOC_TUNE_KNOB_KEYS` key 即自動納入 state / save / draft / dirty。
4. **production-preserve** — 新旋鈕 default null = 繼承 per-KB(未設即 bit-identical)。

---

## §4 Non-goals(明確唔做)
- **KB 層 section 錨定 UI**(同樣缺,本 phase 只補 doc 層 L3;KB 層另議)。
- **Settings preset mapping 編輯**(缺口 B,獨立 phase)。
- **改 mockup**(方案 B;將來補 mockup 走獨立 design sync)。
- **backend 改動 / 新 endpoint**(`PUT /config` 已支援)。

---

## §5 Risks
- **R1 H7 design-stage expansion** — 緩解:用戶 explicit 揀方案 A + 視覺零發明(既有 component)+ 記 ADR-0060。
- **R2 三旋鈕 plumbing 漏接** — 緩解:加 `DOC_TUNE_KNOB_KEYS` key 自動納入(既有機制);F2 browser 驗 persist。
- **R3 inline marker 做主 toggle 語意** — section 錨定依賴 inline marker(W75 preset 兩者同 ON)→ 主/進階
  關係合理。

---

## §6 紀律自檢(kickoff)
- **H7** ⚠️→✅ design-stage expansion(mockup 之外 UI)— 用戶 STOP+ask 後 explicit 揀方案 A,記 ADR-0060。
- **H1** ✅ UI surface 擴展(ADR-0060 Accepted)— 不改 backend contract / layout philosophy / 既有旋鈕。
- **H2** ✅ 零新 dep。
- **H4** ✅ 層 A UI,無 Tier 2。
- **H6** N/A(frontend;既有 vitest doc-config-tab scaffold 不回歸,DD-2)。
- **Karpathy** ✅ reuse(既有 component + KNOB_KEYS 機制)、surgical(加 3 欄位 + 1 組)、goal(F acceptance +
  browser 驗 persist)、think-before(H7 STOP+ask + ground 落點)。

---

## §7 Changelog
- 2026-06-15 kickoff — plan active,F1-F3 scope locked;ADR-0060 Accepted(用戶揀方案 A);落點 ground
  (KNOB_KEYS 自動納入 + 既有 component 復用 + backend 零改動)。
- 2026-06-15 F1 frontend(commit `0321a43`)— `doc-config.ts` 三欄位 + `doc-config-tab.tsx` 三 key + 新
  「Inline 圖文錨定」`DocTuneGroup`(復用既有 component)+ docstring ADR-0060 note;type-check 0 + lint
  零新 warning + build ✓。
- 2026-06-15 **F2 browser 驗端到端 PASS**(playwright)— L3「Inline 圖文錨定」組 render(視覺零發明,既有
  component)+ UI 寫 PASS(toggle inline marker → save → `PUT /config` persist)+ DELETE 還原零污染;
  console errors 全 `/notifications` 404 pre-existing。
- 2026-06-15 closeout — plan closed full PASS,F1-F3 全 tick。
