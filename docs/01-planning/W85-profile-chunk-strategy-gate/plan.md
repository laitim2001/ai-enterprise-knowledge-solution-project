# W85 plan — profile→chunk_strategy ingest 路由 F0 實證 gate

**Status**: active（kickoff 2026-06-16）
**Kickoff**: 2026-06-16
**Phase 類型**: diagnostic-first（F0 純實證 gate，零 production code 改動；F1+ 完整框架 conditional on
F0 PASS，屆時才開 H1 ADR）
**ADR**: 無（F0 不改 production code）。F0 PASS → F1 框架才寫 ADR-0066（H1 ingest 流程 + config-scope 擴展）。

---

## §1 Context / 緣起

用戶 status review 後揀推進**缺口①** — 把「處理流程」從檢索後延伸到 ingest 階段（profile→chunk_strategy
路由），= vision「不同文件用不同處理流程」最完整一塊。用戶揀 **F0 實證 gate 先**（避免幻影價值，呼應 W83
「先 live 診斷確認真缺口」教訓）。

**Grounding 發現（plan kickoff,R6）**：
- **技術可行** — `orchestrator.ingest()` step 順序 = `parse(141)→ profile(153)→ chunk(159)`，profile 在
  chunk **之前**已算好。
- **但 chunker parse 前就選死** — `_select_chunker`（`documents.py:184`）route 層用 `KbConfig.chunk_strategy`
  選好再傳入 orchestrator 建構式固定住 → 要按 profile 路由須把 chunker 選擇**延後到 profile 後**（改
  orchestrator 簽名）。
- **選擇空間小** — 實際只 **2 個 chunker class**：`LayoutAwareChunker`（layout_aware + slide_based 都用它）
  + `HeadingAwareChunker`（W53）。`auto` 現只按格式分（docx/pdf→layout、pptx→slide）。profile→strategy 現階段
  真正能路由 = **heading vs layout 二選一**，且只對 **docx 類**有對比意義（pptx slide_based=layout / scan OCR 後 layout）。
- **「掃描件 OCR」已自動** — Docling 對無文字層 PDF 自動 OCR（parser 層，非 chunker 層；W84 guard 防它慢）。
  缺口①真正內容**只剩 chunk_strategy 路由**。
- **W53 live runner 不存在** — `strategy_comparison.py`（工具）只有 unit test（stub），docstring 提的
  `scripts/run_strategy_recall_comparison.py` 從未落地；`controlled_comparison.py` 零引用。且其方法論是
  **self-retrievability**（per-config QA 各自重生 → confounded by question difficulty）+ synthetic GT（非 human）
  → 只能作**相對信號非絕對 verdict**。

**核心擔憂（決定做 F0 的理由）**：做 profile→chunk_strategy「框架」成本中等，但能路由的只有 heading vs layout
二選一 → **風險是做了框架卻發現對不同 profile heading vs layout 無顯著差異 = 幻影價值**。F0 先驗證增量真實。

---

## §2 Scope / Deliverables

### F0 — 實證 gate（零 production code 改動，純 diagnostic）

- **F0.1 離線 chunk 結構對比**（主信號，不需 KB / index / judge）— 寫離線 script：代表 profile 的 **docx** 文件
  （P1 圖密SOP=`DRIVE_User Manual` / P2 散文=`AI-Governance-Guideline` / P5 表單=`AI_Project_Registration_Form`）
  × {`heading_aware`, `layout_aware`} chunker → 比 chunk 結構 metrics：**chunk 數 / token 大小分布（mean/p50/max）
  / section 完整性（一 section 是否被切碎跨多 chunk）/ 圖分布**。判「profile-differentiated 是否有結構性意義」。
- **F0.2 self-retrievability 相對信號**（conditional on F0.1 有信號）— wire 最小 live runner（set strategy →
  reindex 1 個代表 KB → W52 synthetic recall）補一個 KB 的相對 recall。**誠實標 confounded 限制**，作佐證非主判據。
- **F0 gate** — 綜合 F0.1（結構）+ F0.2（相對 recall）判斷 profile-differentiated chunking 是否有意義增量：
  - **PASS**（某 profile 用對 strategy 有明顯結構/recall 優勢）→ F1+ 開完整框架（ADR-0066）。
  - **FAIL / marginal**（heading vs layout 對各 profile 無顯著差異）→ **defer**，記 `DEFERRED_REGISTER`
    新 DD + 結論（誠實:框架選擇空間不足以支撐增量，等更多 chunker strategy 落地再評估）。

### F1+ — 完整框架（conditional on F0 PASS，不預寫，rolling JIT）

F0 PASS 才開：ADR-0066（H1）+ ingest-time profile preset（profile→chunk_strategy，與現有 post-retrieval
`PROFILE_PRESETS` 分層）+ orchestrator 延後選 chunker + L3/Settings UI（顯示+override，標「改 strategy 要 re-index」）
+ re-index wiring。

---

## §3 設計原則

1. **F0 零 production 改動** — 純離線 diagnostic + 最小 live runner；不碰 `orchestrator` / `_select_chunker` /
   `PROFILE_PRESETS`。
2. **結構分析為主信號** — self-retrievability confounded（W53 docstring 自承），故 F0.1 結構對比為主、F0.2 recall 為佐證。
3. **避免幻影價值** — F0 gate 明確判增量是否真實，FAIL 就誠實 defer（W83 教訓）。
4. **誠實方法論標註** — 所有 recall 數字標 self-retrievability + synthetic GT 限制，不當絕對 verdict。

---

## §4 Non-goals（明確唔做）

- **F0 不改任何 production code**（orchestrator / chunker selector / preset / UI 全不動）。
- **不做 parser / OCR 路由** — 掃描件 OCR 已自動（Docling），非缺口。
- **不預寫 F1 框架** — conditional on F0 PASS（rolling JIT）。
- **不解 human GT 缺口** — F0 用 self-retrievability + 結構分析繞過（prose human GT 仍卡用戶）。
- **不擴 chunker class** — F0 只比現有 heading vs layout；新 strategy（form/scan-specific）屬 F1+ 或更後。

---

## §5 Risks

- **R1 F0 self-retrievability 證明力間接**（confounded + synthetic）→ 緩解:F0.1 結構分析為主判據，F0.2 僅佐證 +
  誠實標限制;gate 判斷以結構信號為錨。
- **R2 F0 PASS 但 F1 框架選擇空間小**（只 heading vs layout）→ 緩解:F0 gate 明確要求「某 profile 有顯著優勢」才
  PASS;marginal 即 defer，不勉強做框架。
- **R3 F0.2 reindex 污染代表 KB**（in-place reindex 改 KB 狀態）→ 緩解:用 throwaway / test KB（如 `w56-drive-ab-1`
  已 heading_aware），或跑完還原;絕不對 production KB（drive-images-1）做。

---

## §6 紀律自檢（kickoff）

- **H1** ✅ F0 零 production 改動不觸 H1;F1 框架觸 H1（ingest 流程 + config-scope）→ F0 PASS 後才開 ADR-0066。
- **H2** ✅ 零新 dep（F0 用現有 parser/chunker/eval building blocks）。
- **H4** ✅ chunk_strategy 純結構策略，無 Tier 2 feature。
- **H6** ✅ F0 若寫可復用 production helper 補 test;F0 純 script diagnostic 則不強制（非 production module）。
- **Karpathy** ✅ think（grounding 揭 live runner 不存在 + 選擇空間小 → F0 先驗證避免幻影）、simple（離線結構對比
  最輕，不建重 live runner 直到 F0.1 有信號）、surgical（零 production 改動）、surface（H1 + F0 方法論限制 + 例子修正
  「OCR 已自動」全 upfront 畀用戶）。

---

## §7 Changelog

- 2026-06-16 kickoff — plan active;用戶 status review 後揀推進缺口① + 揀 F0 實證 gate 先。Grounding 揭 5 發現
  （profile 在 chunk 前可用 / chunker parse 前選死 / 只 2 chunker class 選擇空間小 / OCR 已自動非缺口 / W53 live
  runner 不存在 + self-retrievability confounded）→ F0 方法論定為「結構分析為主 + self-retrievability 佐證」;
  F1 框架 conditional on F0 PASS（屆時開 ADR-0066）。
