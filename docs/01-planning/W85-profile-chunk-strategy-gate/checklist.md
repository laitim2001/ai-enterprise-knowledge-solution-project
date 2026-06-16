# W85 checklist — profile→chunk_strategy F0 實證 gate

> Atomic items per deliverable。每日 tick。Source of truth = `plan.md`。

## F0 — 實證 gate（零 production code 改動）
- [x] F0.1 離線 chunk 結構對比 script（`scripts/w85_chunk_structure_compare.py`）：5 代表 docx（P1×2 / P2×2 / P5×1）
      × {heading_aware, layout_aware} → chunk 數 / token 分布 / section 完整性(frag) / 圖分布 metrics
- [x] F0.1 判讀：**偏向無顯著 profile-differentiated 差異** — 圖分布兩 strategy 完全相同（圖由 parser 定）+ 結構差異
      3–27% 小 + heading 賣點「1 section 1 chunk」在圖密 SOP(最需要)失效(frag 2.0–2.4)/ 純散文接近理想但 layout 也接近(沒差)。
      根因：2 chunker 本質太相似（差別只在 target-balance + merge），內容結構（圖+table+短 section）淹沒 strategy 差異
- [ ] F0.2（conditional on F0.1 有信號）self-retrievability 相對信號：wire 最小 live runner（set strategy →
      reindex 1 個 throwaway/test KB → W52 synthetic recall）+ 誠實標 confounded 限制
- [ ] F0 gate 判決：PASS（某 profile 顯著優勢 → F1 框架 + ADR-0066）/ FAIL·marginal（無顯著差異 → defer + 記 DD）
- [ ] F0 closeout：plan §7 changelog + progress retro + gate 判決記錄 +（若 defer）DEFERRED_REGISTER 新 DD

## F1+ — 完整框架（conditional on F0 PASS，rolling JIT，未 pre-create）
- 🚧 F0 PASS 才開：ADR-0066（H1）+ ingest-time profile preset + orchestrator 延後選 chunker + L3/Settings UI +
  re-index wiring。**禁止 F0 gate 前預寫**（rolling JIT R1）。
