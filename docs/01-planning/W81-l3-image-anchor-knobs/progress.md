# W81 progress — L3 image-anchor knobs UI(缺口 A,ADR-0060)

## Day 1 — 2026-06-15(kickoff)

**Context**:W80 後做「層 A UI 可調性 gap 分析」,坐實兩缺口:**A** = L3 缺三圖錨旋鈕
(`enable_inline_image_markers` W70 / `enable_section_anchored_aux_images` + `section_anchor_max_per_anchor`
W75);**B** = Settings preset mapping 唯讀(獨立 phase)。用戶揀**先做缺口 A**。

**H7 STOP+ask**:ground 揭 inline marker 喺 mockup KB 層有 `KbTuneGroup` 設計(`ekp-page-kb.jsx:918`)+ KB
層 frontend 已落地;但 section 錨定兩旋鈕 **mockup + KB 層 frontend 都冇**(W75 比 mockup 晚)→ 觸 H7。
surface 三方案(A 復用既有模式延伸 / B 改 mockup / C 只做 inline marker)→ **用戶揀方案 A**。

**ADR-0060 Accepted**(本 session):L3 新增「Inline 圖文錨定」`DocTuneGroup`,復用既有 mockup-aligned
component(`DocTuneGroup`/`DocSwitchKnob`/`DocTuneKnob`)裝三旋鈕;backend 零改動(`DocConfig` + `PUT /config`
已支援)。性質 = design-stage expansion(mockup 之外 UI,視覺零發明,H7 deviation 用戶批准)。

**落點 ground(R6)**:`DOC_TUNE_KNOB_KEYS`(doc-config-tab:94)加 key → setKnob/buildDraftConfig/dirty/
saveMutation 自動納入(零新 plumbing);插入點 = 「Citation neighbour images」`DocTuneGroup`(442-470)後。

**設計決定**:inline marker 做 `DocTuneGroup` 主 toggle(對齊 mockup KB 層 inline marker)、section 錨定 +
cap 做進階 children(section 錨定依賴 inline marker 機制,W75 preset 兩者同 ON → 主/進階關係合理)。

**Scope 邊界**:只補 doc 層 L3;KB 層 section 錨定 UI 同樣缺(另議);Settings preset mapping(缺口 B)獨立
phase;mockup 暫不動(方案 A,將來補 mockup 走獨立 design sync)。

**紀律自檢**:H7 design-stage expansion 用戶批准(ADR-0060)/ H1 ✅ / H2 ✅ 零 dep / H4 ✅ 層 A /
Karpathy ✅ reuse 既有 component + KNOB_KEYS 機制 + backend 零改動。

**Plan 落地**:W81 folder + plan.md(active)+ checklist.md(F1-F3)+ progress.md + ADR-0060 + README index。

**F1 implement(Day 1)**:
- **doc-config.ts**:`DocConfig` interface 加三 optional 欄位(mirror backend)。
- **doc-config-tab.tsx**:`DOC_TUNE_KNOB_KEYS` 加三 key + import `Tag` + docstring 補 ADR-0060
  design-stage expansion note(誠實標記「the one deliberate departure from strict mockup fidelity」)+
  新「Inline 圖文錨定」`DocTuneGroup`(toggle=`enable_inline_image_markers` + children:section 錨定
  `DocSwitchKnob` + 每錨點 cap `DocTuneKnob`)插「Citation neighbour images」組後。
- **gate**:type-check 0 + lint 零新 warning(唯一 warning line 1858 別檔 pre-existing)+ build ✓(exit 0)。

**F2 browser 驗(Day 1,playwright)**:
- 起 dev :3001(build 覆蓋 .next → wipe .next + 重啟 dev,warm route 150s timeout 過首次 OneDrive compile)。
- navigate L3(dev auto-login,無 redirect)→ click「Per-doc 配置」tab → 「Inline 圖文錨定」組 render。
- **視覺**:`DocTuneGroup` collapsible 進階(既有行為,預設收起)→ 展開見 section 錨定 + 每錨點上限;
  switch×2(group toggle + section switch)+ number input×1 + 全用既有「繼承 KB / 未覆寫 · 沿用 KB」
  badge/hint = **零發明 H7 OK**(復用既有 component 必然視覺對齊)。
- **UI 寫端到端 PASS**:click inline marker group toggle → `data-on=true` + badge「已覆寫」+ save button
  enable(證明 setKnob 觸發 dirty,新 key 納入既有機制)→ 儲存 → **`PUT /config` persist
  `enable_inline_image_markers=true`**(API GET 確認)。
- **零污染**:`DELETE /config` 還原 → GET 全 null(原狀)。console 7 errors 全 `/notifications` 404
  pre-existing 無害。

**Retro(Day 1)**:
- **加 `DOC_TUNE_KNOB_KEYS` key = 零新 plumbing**:setKnob/buildDraftConfig/dirty/overriddenCount/
  saveMutation 全靠呢個 key list 驅動,加三 key 即自動納入 → UI 寫路徑 by construction 正確(既有機制
  + type-check pass)。新 code 最少(interface 3 欄位 + key list + 1 組 DocTuneGroup)。
- **H7 方案 A 兌現「視覺零發明」**:全用既有 `DocTuneGroup`/`DocSwitchKnob`/`DocTuneKnob`(同 class →
  必然視覺對齊),browser evaluate 確認 badge/hint/switch/input 全既有模式。mockup 之外 expansion 的
  H7 風險靠「復用既有 mockup-aligned component」最低化(ADR-0060 核心)。
- **backend 零改動**:`DocConfig` schema + `PUT /config` 早已支援三欄位(W70/W75 落 backend 但無 UI);
  本 phase 純 frontend 補 UI surface。GET /config 一開始就返回三欄位(全 null)= backend round-trip 已通。
- **dev/build .next 衝突坑重現**:build(覆蓋 production .next)+ dev(用 .next)同時 → :3001 timeout;
  標準解 = 停 dev + wipe .next + 重啟 dev + warm route(memory `project_frontend_next_cache_corruption`)。
- **交棒**:缺口 B(Settings preset mapping 編輯,需 backend write API)獨立 phase;KB 層 section 錨定 UI
  同樣缺(另議);mockup 補 section 錨定設計走獨立 design sync(將來)。

**Commits**:
- `ac2b01f` docs(planning): W81 kickoff + ADR-0060 — L3 image-anchor knobs UI
- `0321a43` feat(frontend): W81 F1 L3 image-anchor knobs UI (ADR-0060)
- (closeout)docs(planning): W81 closeout — full PASS
