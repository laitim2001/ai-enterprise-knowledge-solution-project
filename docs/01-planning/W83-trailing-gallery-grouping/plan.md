# W83 plan — 末尾無錨圖 gallery 章節分組（B,ADR-0064）

**Status**: closed（2026-06-16，full PASS — F1 helper + unit test（42 passed）+ F2 chat 分組 render + F3 browser 驗 35 張分 2 章節組 + clean build exit 0）
**Kickoff**: 2026-06-16
**Phase 類型**: frontend-only 呈現層 feature（純 chat render；零 backend / 零 retrieval 改動；
H7 design-stage expansion edit — mockup 無分組 gallery 設計；ADR-0064 Accepted）
**ADR**: ADR-0064（末尾無錨圖按 `source_section` 分組 + 章節小標 — 復用既有 gallery primitive）

---

## §1 Context / 緣起

用戶 2026-06-16 提「層 C 圖片按相關性揀」推進請求。三條真實 query live 診斷
（`drive-images-1`：FA「create fixed asset master record」/ GL「process journal voucher」
/ GL「post journal entry」）**推翻層 C 前提**：

1. **層 C 無效** — 召回圖（FA 48 / GL 40）**全部相關**，沒有「不相關的圖要砍」。痛點不是
   relevance(precision)，是 anchoring(圖多於文字步驟)。砍圖反噬 W59–W68「全圖召回」定調。
2. **A（調 `citation_neighbour_max_aux_images`）實證否決** — 乾淨 A/B（max_aux 40 vs 80 各 3 run，
   答案長度穩定 ~9500 字 variance 排除）：召回**都係 40**。`max_aux` 不是上限，召回 40/49 的 gap
   在更深候選構造機制（image-recall 弧教訓「每層天花板都係下層機制偽裝」）；再挖觸 H1 + 反噬 + ROI 低。
3. **真因 = 圖粒度 > 文字步驟粒度** — FA `chunk-0009` 633 字 ~12 步但綁 47 圖（required 12 欄位 +
   technical 14 欄位**每欄一截圖**）→ 35 張欄位截圖無步驟可錨 → 堆末尾成「一堆無序圖」。

**唯一真實改善 = B 末尾 gallery 組織化**（用戶 2026-06-16 揀方案 1）：把 `trailingImages` 那排無分組
大卡，按 `source_section` 分組 + 章節小標，令「一堆無序圖」變「分章節的截圖附錄」（知道每張屬哪步驟章節）。
對 FA 型（逐欄位截圖文件，35 張）價值最大；GL 型（8 張）較小但同受惠。

**落點 grounding（plan kickoff,R6）**：
- `frontend/app/(app)/chat/page.tsx`：
  - `trailingImages`（line 1170）= `imagePlan.trailing` = capped 圖 minus anchored（無 marker 圖）。
  - render line 1299-1309：`trailingImages.map(...)` → 一排獨立 `InlineImageCard`,**無分組**（B 改點）。
  - `ImageGallery`（line 1932）= 底部「Referenced screenshots」縮圖 grid,傳 `cappedImages` 全部,flat
    （**本 phase 不動** — 索引總覽性質）。
  - 章節 header 視覺源 = ImageGallery header（line 1962-1971）`muted mono text-xs` uppercase（復用）。
- `frontend/lib/chat/citation-images.ts`：
  - `imageSectionPath(image, citation)`（line 207）= 每圖 section（`source_section` ?? citing `section_path`）
    — 分組 key 現成。
  - `PlacedImage`（line 147）= `{ entry: DedupedCitationImage; figureIdx: number }`,trailing 已連續編號。
  - 新 helper `groupTrailingBySection` 落此檔（純函數,可單測,mirror 既有 helper style）。

---

## §2 Scope / Deliverables

### F1 — `groupTrailingBySection` helper + unit test
- **F1.1** `citation-images.ts` 加 `groupTrailingBySection(trailing: PlacedImage[]):
  TrailingSectionGroup[]`（`{ sectionPath: string[]; sectionLabel: string; items: PlacedImage[] }`）：
  - 用 `imageSectionPath(entry.image, entry.citation)` 取每圖 section,按**完整 section_path** 分組。
  - 組順序 = 第一次出現順序（`trailing` 已 doc_order 排序 → 組順序自然 doc_order）；組內保留原順序。
  - `sectionLabel` = section leaf（最後一節,如「2.1.3 System Instruction for each step」）；
    section 空 → fallback「Other」（純防禦,正常 source_section 已 populate）。
  - **不改 `figureIdx`** — 只分組,連續編號保留（inline → trailing 跨組連續）。
- **F1.2** unit test（`frontend/tests/unit/citation-images.test.ts` 加）：分組正確 / 組順序 doc_order /
  figureIdx 連續不變 / 空 trailing → `[]` / 單一 section → 單組 / section 缺 → fallback。
- **acceptance**：type-check 0 + 純函數測試綠。

### F2 — chat page trailing render 改分組
- **F2.1** `chat/page.tsx` 1299-1309：`trailingImages.map(...)` → `groupTrailingBySection(trailingImages)`
  外層 map：每組先渲染**章節 header**（復用 ImageGallery header 同款 `muted mono text-xs` uppercase +
  圖數 `badge badge-muted`,視覺零發明）,再 map 該組 `items` 的 `InlineImageCard`（props 不變）。
- **F2.2** production-preserve：`trailingImages` 空（knob off / 全錨）→ 0 組 → 無渲染,bit-identical pre-W83。
- **acceptance**：type-check 0 + lint 零新 warning + build ✓；章節 header 全用既有 primitive（H7 視覺零發明）。

### F3 — Browser 驗（playwright）
- 起 infra（per `ekp-restart`，本 session 服務已 live）→ chat `drive-images-1` 跑 FA query
  「what are the steps to create a fixed asset master record」→ 確認末尾 35 張 trailing 圖**按 §2.1.x 分組 +
  章節小標**（非一片無序）；inline 交織圖不受影響；figure 編號連續。
- **acceptance**：分組 render 對齊（章節 header + 組內 InlineImageCard）；console 僅 pre-existing `/notifications` 404。

### F4 — closeout
- frontend gate 全綠（type-check/lint/build + browser）；plan closed + progress retro +
  ADR-0064 README index + DEFERRED_REGISTER 更新（**層 C confirm defer = DD-12** + **A max_aux 否決記錄** +
  本 phase B 落地）+ memory `project_per_kb_tunable_config_vision` 更新（W83 段 + 層 C/A 收斂）。

---

## §3 設計原則（ADR-0064）

1. **視覺零發明** — 章節 header + 圖卡全復用既有 primitive（ImageGallery header + InlineImageCard）；
   H7 方案 1（用戶揀,最低 H7 風險,同 W81 缺口 A precedent）。
2. **純前端呈現層** — 零 backend / 零 retrieval / 零 ingest 改動；不改召回（A 否決）、不改圖數、不砍圖。
3. **production-preserve** — trailing 空 → bit-identical pre-W83（knob off 答案不受影響）。
4. **doc_order 保留** — 組間 + 組內順序維持 `dedupeCitationImages` 的 doc_order 排序；figure 編號連續。
5. **聚焦 trailing** — 只組織 `trailingImages`（用戶痛點「沒跟隨文字、最後面」直接對應）；ImageGallery 縮圖
   grid 保持 flat 總覽（索引性質,不動）。

---

## §4 Non-goals（明確唔做）

- **層 C「按相關性揀」** — 實證無效（圖全相關）→ confirm defer DD-12,不做。
- **A 調 `max_aux` 補召回** — 乾淨 A/B 實證否決（40 vs 80 召回都 40）→ 不做。
- **改召回機制 / chunker 拆 mega-chunk** — 觸 H1 + 反噬全召回定調 + ROI 低,不做。
- **ImageGallery 縮圖 grid 分組** — 保持 flat 總覽索引；本 phase 只動 trailing 大卡。
- **改 backend / mockup** — 方案 1 復用既有 primitive；mockup 補分組 gallery 設計走獨立 design sync。

---

## §5 Risks

- **R1 H7 design-stage expansion**（mockup 無分組 gallery）— 緩解：用戶 explicit 揀方案 1 復用既有 primitive
  （視覺零發明）+ 記 ADR-0064；mockup 補設計走獨立 design sync（同 W81 ADR-0060 precedent）。
- **R2 figure 編號斷裂** — 緩解：helper 只分組不改 `figureIdx`；F1.2 測 figureIdx 連續不變。
- **R3 分組後視覺過碎**（FA 35 張可能散成多 §2.1.x 組）— 緩解：組順序 doc_order + 章節 header 清晰;
  browser 驗實際觀感,若過碎 F3 記 + 評估（但分組總比無序好）。
- **R4 production-preserve 破壞** — 緩解：trailing 空 → 0 組無渲染回歸測 + F2.2 bit-identical。

---

## §6 紀律自檢（kickoff）

- **H1** ⚠️→✅ image presentation documented behavior change — ADR-0064 Accepted（用戶 AskUserQuestion 揀方案 1）；
  純前端呈現層,零 retrieval / index schema / vendor 改動。
- **H2** ✅ 零新 dep。
- **H4** ✅ 純呈現層,無 image embedding / multimodal（層 C 否決正因守 H4）。
- **H6** ✅ helper 純函數寫 unit test。
- **H7** ⚠️→✅ design-stage expansion（mockup 無分組）— 用戶 STOP+ask 後揀方案 1 復用既有 primitive（視覺零發明）,
  記 ADR-0064；mockup 補設計獨立 design sync。
- **Karpathy** ✅ think（三 query 診斷 + A/B 實證否決 A,不硬做）、simple（聚焦 trailing 分組純函數 + 復用 primitive）、
  surgical（零 backend、trailing 空 bit-identical）、surface（層 C/A/B + H7 全 STOP+ask 畀用戶揀）。

---

## §7 Changelog

- 2026-06-16 kickoff — plan active,F1-F4 scope locked;ADR-0064 Accepted（用戶揀方案 1 復用既有 gallery primitive）；
  層 C confirm defer（實證無效）+ A 調 max_aux 實證否決;落點 ground（`trailingImages` render 1299-1309 +
  `imageSectionPath` 分組 key + ImageGallery header primitive 復用）。
- 2026-06-16 F1（commit `a4cfa17`）— `groupTrailingBySection` 純函數 + `TrailingSectionGroup` type（`citation-images.ts`）+
  unit test；vitest **42 passed**（原 35 + 新 7）+ type-check 0。
- 2026-06-16 F2（commit `25ef5ad`）— `chat/page.tsx` trailing render 改分組（`<section>` wrapper + 章節 header 復用
  ImageGallery `muted mono` + `badge badge-muted` primitive）+ import `groupTrailingBySection`；type-check 0 +
  lint 零新 warning（pre-existing `no-img-element` 行號位移）。
- 2026-06-16 F3 browser 驗 PASS（playwright，FA query）— 末尾 **35 張** trailing 分 §2.1.4（13）+ §2.1.5（22）兩組 +
  章節小標 + 圖數 badge（DOM evaluate + screenshot 雙驗）；inline 10 張不受影響；console 全 pre-existing `/notifications` 404。
- 2026-06-16 F4 closeout — **clean build exit 0**（停 dev 後跑，`/chat` 46.8 kB / 209 kB，15/15 static pages）+ 重啟 dev；
  plan closed **full PASS**，F1-F4 全 tick；ADR-0064 README index + DEFERRED DD-12（kickoff 已落）；memory 更新。
