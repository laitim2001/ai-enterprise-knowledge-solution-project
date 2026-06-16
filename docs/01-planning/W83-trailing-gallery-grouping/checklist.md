# W83 checklist — 末尾無錨圖 gallery 章節分組（ADR-0064）

> Atomic items per deliverable。每日 tick。Source of truth = `plan.md`。

## F1 — `groupTrailingBySection` helper + unit test ✅
- [x] F1.1 `citation-images.ts` 加 `groupTrailingBySection(trailing)` + `TrailingSectionGroup` type
  - [x] 用 `imageSectionPath` 取每圖 section,按完整 `section_path` 分組
  - [x] 組順序 = 第一次出現（doc_order 自然序）；組內保留順序
  - [x] `sectionLabel` = section leaf；section 空 → fallback「Other」
  - [x] 不改 `figureIdx`（連續編號保留）
- [x] F1.2 unit test（`tests/unit/citation-images.test.ts`）：分組正確 / 組順序 doc_order（first-appearance）/ figureIdx 連續 / 空 → `[]` / 單組 / 非連續 run rejoin / section 缺 fallback（7 新 test）
- [x] F1 gate：type-check 0 + vitest **42 passed**（原 35 + 新 7）

## F2 — chat page trailing render 改分組
- [ ] F2.1 `chat/page.tsx` 1299-1309：`trailingImages.map` → `groupTrailingBySection` 外層 map（章節 header 復用 `muted mono text-xs` uppercase + `badge badge-muted` + 組內 `InlineImageCard`）
- [ ] F2.2 production-preserve：trailing 空 → 0 組無渲染 bit-identical
- [ ] F2 gate：type-check 0 + lint 零新 warning + build ✓

## F3 — Browser 驗（playwright）
- [ ] F3.1 chat `drive-images-1` 跑 FA query → 末尾 35 張 trailing 按 §2.1.x 分組 + 章節小標
- [ ] F3.2 inline 交織圖不受影響 + figure 編號連續
- [ ] F3 gate：分組 render PASS；console 僅 pre-existing `/notifications` 404

## F4 — closeout
- [ ] F4.1 frontend gate 全綠（type-check/lint/build + browser）
- [ ] F4.2 plan closed + progress retro
- [ ] F4.3 ADR-0064 README index
- [ ] F4.4 DEFERRED_REGISTER 更新（層 C confirm defer DD-12 + A max_aux 否決記錄 + B 落地）
- [ ] F4.5 memory `project_per_kb_tunable_config_vision` 更新（W83 段 + 層 C/A/B 收斂）
