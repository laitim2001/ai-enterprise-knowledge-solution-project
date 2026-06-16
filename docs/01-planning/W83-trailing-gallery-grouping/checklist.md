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

## F2 — chat page trailing render 改分組 ✅（code；build clean-exit 待 F4 停 dev 後跑）
- [x] F2.1 `chat/page.tsx` `trailingImages.map` → `groupTrailingBySection` 外層 map（`<section>` wrapper + 章節 header 復用 `muted mono text-xs` uppercase + `badge badge-muted` + 組內 `InlineImageCard` props 不變）+ import 加 `groupTrailingBySection`
- [x] F2.2 production-preserve：trailing 空 → `groupTrailingBySection` 回 `[]` → 0 組無渲染 bit-identical
- [x] F2 gate（code）：type-check 0 + lint 零新 warning（唯一 = pre-existing `no-img-element` 行號由 1858→1882 位移）；build clean-exit 受並行 `next dev` `.next` race 阻 → F4 停 dev 後 confirm（dev compile chat route 已覆蓋 compile 驗證）

## F3 — Browser 驗（playwright）✅
- [x] F3.1 chat `drive-images-1` 跑 FA query → 末尾 **35 張** trailing 按 §2.1.x 分組（§2.1.4 13張 + §2.1.5 22張）+ 章節小標 + 圖數 badge（DOM evaluate + screenshot 雙驗）
- [x] F3.2 inline 交織圖（10 張）在 answer body 不受影響 + figure 編號連續（`figureIdx` helper 保留）
- [x] F3 gate：分組 render **PASS**；console 4 errors 全 pre-existing `/api/backend/notifications` 404，我 component 零 error；視覺 header 對齊 ImageGallery primitive（uppercase muted mono + badge）

## F4 — closeout ✅
- [x] F4.1 frontend gate 全綠（type-check 0 + lint 零新 + **clean build exit 0**〔`/chat` 46.8 kB / 15-15 static pages〕+ browser PASS）
- [x] F4.2 plan closed full PASS + progress retro
- [x] F4.3 ADR-0064 README index（kickoff 已加 row + next → 0065）
- [x] F4.4 DEFERRED_REGISTER 更新（層 C confirm defer DD-12 + A max_aux 否決記錄 + B 落地；kickoff 已落）
- [x] F4.5 memory `project_per_kb_tunable_config_vision` + MEMORY.md index 更新（W83 段 + 三正交層全有結論）
