# W85 checklist — profile→chunk_strategy F0 實證 gate

> Atomic items per deliverable。每日 tick。Source of truth = `plan.md`。

## F0 — 實證 gate（零 production code 改動）
- [ ] F0.1 離線 chunk 結構對比 script：代表 docx（P1 圖密SOP / P2 散文 / P5 表單）× {heading_aware, layout_aware}
      → chunk 數 / token 大小分布 / section 完整性 / 圖分布 metrics
- [ ] F0.1 判讀：profile-differentiated 是否有結構性意義（某 profile 用對 strategy 明顯更合理）
- [ ] F0.2（conditional on F0.1 有信號）self-retrievability 相對信號：wire 最小 live runner（set strategy →
      reindex 1 個 throwaway/test KB → W52 synthetic recall）+ 誠實標 confounded 限制
- [ ] F0 gate 判決：PASS（某 profile 顯著優勢 → F1 框架 + ADR-0066）/ FAIL·marginal（無顯著差異 → defer + 記 DD）
- [ ] F0 closeout：plan §7 changelog + progress retro + gate 判決記錄 +（若 defer）DEFERRED_REGISTER 新 DD

## F1+ — 完整框架（conditional on F0 PASS，rolling JIT，未 pre-create）
- 🚧 F0 PASS 才開：ADR-0066（H1）+ ingest-time profile preset + orchestrator 延後選 chunker + L3/Settings UI +
  re-index wiring。**禁止 F0 gate 前預寫**（rolling JIT R1）。
