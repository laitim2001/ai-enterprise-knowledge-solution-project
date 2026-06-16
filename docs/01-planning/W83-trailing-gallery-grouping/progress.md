# W83 progress — 末尾無錨圖 gallery 章節分組（ADR-0064）

> Daily progress + decisions + commits + 結尾 retro。

---

## Day 1 — 2026-06-16

### 緣起 / 診斷（層 C 推進請求 → 收斂到 B）

用戶要推進「層 C 圖片按相關性揀」。三條真實 query live 診斷（`drive-images-1`，`/query` full pipeline）：

| | 召回圖 | 文件實際 | inline marker（穩定） | 堆末尾 |
|---|---|---|---|---|
| FA 建立固定資產 | 48 | 48 | ~13 | **~35 張** |
| GL 傳票 | 40 | 49（§3） | ~32 | ~8 張 |
| GL 過帳 | 40 | 49（§3） | ~32 | ~8 張 |

**三個關鍵實證（全部推翻層 C 前提）**：
1. **層 C 無效** — 召回圖全部相關（FA 同一建立流程欄位截圖 / GL 同一過帳流程），無「不相關圖要砍」。
   `source_section` 48/48 populate（memory「全空」已過時 — BUG-026 C-ii / CH-011 早補）。
2. **A（調 `citation_neighbour_max_aux_images`）實證否決** — 乾淨 A/B（max_aux 40 vs 80 各 3 run，答案
   長度穩定 ~9500 字 variance 排除）：召回**都係 40**。`max_aux` 不是上限；召回 40/49 gap 在更深候選構造
   機制（image-recall 弧教訓）；再挖觸 H1 + 反噬 + ROI 低 → 不做。
3. **真因 = 圖粒度 > 文字步驟粒度** — FA `chunk-0009` 633 字 ~12 步綁 47 圖（required 12 欄位 + technical
   14 欄位每欄一截圖）→ 35 張無步驟可錨堆末尾。GL03 文件 212 圖跨 9 模組,query 正確聚焦 §3（49 圖，
   召回全在 §3，無跨模組洪水 = 層 B 已被 W75 section 錨定吸收的再證）。

**收斂**（用戶 4 輪 AskUserQuestion）：
- 層 C 方向 → 「先給具體痛點 case」（用戶提供 3 條 query）
- 診斷後 → 「兩者都要（先驗證再規劃）」
- A 驗證收斂 → A 實證否決
- B H7 方案 → 「方案 1 復用既有 gallery 延伸」

### 決策

- **ADR-0064 Accepted** — B 末尾無錨圖按 `source_section` 分組 + 章節小標,復用既有 ImageGallery header +
  InlineImageCard primitive（H7 方案 1 視覺零發明）。
- **層 C confirm defer**（DD-12）— 實證無效（圖全相關,無圖可砍 + 反噬全召回定調）,同層 B 被吸收模式。
- **A 調 max_aux 實證否決** — 乾淨 A/B 背書（40 vs 80 召回都 40）,記 progress + DEFERRED,不開工。
- **聚焦 trailing 大卡分組**（用戶痛點「沒跟隨文字、最後面」直接對應）；ImageGallery 縮圖 grid 保持 flat。

### Commits

| Hash | Subject | Checklist |
|---|---|---|
| `5df7dc8` | W83 kickoff + ADR-0064 + 層C/A 收斂 | plan/ADR |
| F1 | `groupTrailingBySection` helper + unit test（42 passed） | F1.1-F1.2 |

### 下一步

- F2 chat page trailing render 改分組（`groupTrailingBySection` 外層 map + 章節 header）。
