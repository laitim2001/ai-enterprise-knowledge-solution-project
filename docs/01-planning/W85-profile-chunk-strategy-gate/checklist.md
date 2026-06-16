# W85 checklist — profile→chunk_strategy F0 實證 gate

> Atomic items per deliverable。每日 tick。Source of truth = `plan.md`。

## F0 — 實證 gate（零 production code 改動）
- [x] F0.1 離線 chunk 結構對比 script（`scripts/w85_chunk_structure_compare.py`）：5 代表 docx（P1×2 / P2×2 / P5×1）
      × {heading_aware, layout_aware} → chunk 數 / token 分布 / section 完整性(frag) / 圖分布 metrics
- [x] F0.1 判讀：**偏向無顯著 profile-differentiated 差異** — 圖分布兩 strategy 完全相同（圖由 parser 定）+ 結構差異
      3–27% 小 + heading 賣點「1 section 1 chunk」在圖密 SOP(最需要)失效(frag 2.0–2.4)/ 純散文接近理想但 layout 也接近(沒差)。
      根因：2 chunker 本質太相似（差別只在 target-balance + merge），內容結構（圖+table+短 section）淹沒 strategy 差異
- [x] ~~F0.2 self-retrievability~~ **取消（PIVOT）** — 路由方向已被 F0.1 否決，recall 佐證無意義（plan §7 changelog）

## F0.3 — 差異化 chunker 診斷（PIVOT 後新增）
- [x] F0.3.1 dump candidate（P5 表單 + P1 FA imgdense）layout_aware chunk 實際結構（`scripts/w85_chunk_dump.py`）：
      **P5 表單 frag=10 非硬切損害** — layout_aware 按 table row group 切，每 chunk = 一組相關欄位+勾選框，語意完整
      （#0 基本資料 / #1 描述 / #2 AI Type / #3 資料存取 / #5 第三方 / #6 Output / #7 Stage / #8 Review）;
      **P1 FA imgdense top6 chunk 全 img=8（cap 撐滿）** = W83 已揭 anchoring 失配（圖粒度>步驟粒度），已被 W59-83 處理
- [x] F0.3.2 評估：**兩 candidate 都不需要差異化 chunker** — P5 表單 layout_aware 已合理切（table row group）/ P1 圖密
      已被 W59-83 呈現層吸收（image-recall + 錨定 + 分組 + cap）。根因:`layout_aware` 已相當通用（table+heading+
      image-grouped via doc_order），profile 差異化需求已被吸收或他層處理
- [ ] F0.3 gate 判決：→ **defer**（缺口① 兩條路〔路由 F0.1 / 造 chunker F0.3〕都實證否決;有價值負面實證:現有
      ingest 已足夠好，profile-differentiated chunking 在 Tier 1 無明確增量）→ 記 DD（待用戶確認）
- [ ] F0 closeout：plan §7 changelog + progress retro + gate 判決 +（若 defer）DEFERRED_REGISTER 新 DD

## F1+ — 造差異化 chunker（conditional on F0.3 gate，rolling JIT，未 pre-create）
- 🚧 F0.3 gate PASS 才開：ADR-0066（H1，造新 chunker class）+ profile→新 chunker 接駁 + test + re-index wiring +
      （若涉 UI）L3/Settings 顯示。**禁止 F0.3 gate 前預寫**（rolling JIT R1）。
