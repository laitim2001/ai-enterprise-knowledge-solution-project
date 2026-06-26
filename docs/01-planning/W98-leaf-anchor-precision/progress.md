# W98 Progress — Leaf-level 圖片步驟級錨定

> Daily progress + decisions + commits + 結尾 retro。對應 `plan.md` / `checklist.md`。

## Day 1（2026-06-26）— kickoff(draft)

**Context**:乙類完整度線(W96 gate + W97 緩解)收口 —— ceiling 診斷(`reports/completeness_ceiling_diag.yaml`,commit `14a5504`)證瓶頸係 generation-side(~0.77,加 context 唔升),用戶拍板**收乙類口、轉甲類圖步驟級錨定**。

**前置 offline 診斷(本 phase 開工前,zero production change)**:
- `scripts/diag_leaf_anchor.py`(commit `70b7b85`):flip drive-images-1 `enable_section_anchored_aux_images` OFF(try/finally 還原)→ capture raw 答案 + citations → offline A/B 現行章節最後錨點 vs `doc_order`-nearest。
- **3-query peek** → nearest 高圖密 Q001 cap5 錨 16 vs 5、nocap clump 19→7。
- **9-query × 2-run broadened**(`reports/leaf_anchor_diag.json`)→ **worse=0 / helped 8/18(全高圖密)/ cap5 多錨 110 張 / nocap clump 平均 −6.67(max −22,Q036 37→16)**;低圖密乾淨 no-op;細 caveat cap5 極高密度最壞 clump +1~2(划算 trade,揭示可放寬 cap)。
- knob 全程由 try/finally 還原;用戶中途斷線時主動 stop + 手動 PATCH 還原 + 驗證(乾淨態先斷線),返嚟重跑 9-query。

**決策**:診斷信號夠硬 + 改動細(pure function 換錨點策略)+ 對齊 §15 → 用戶拍板**寫 W98 plan productionize**。

**今日產出**:
- W98 三件套 draft(plan / checklist / progress)。
- F1-F5 分段:knob `section_anchor_nearest` 四層 default OFF(production-preserve)→ wire 兩注入點 → cap 互動決定 → production A/B + browser → doc-sync + ADR-0056 amendment。
- **H1**:屬 ADR-0056 段②d「leaf 級」pre-scoped 後續 → 預期 ADR-0056 amendment 非新 ADR;scope 若超 leaf-anchor → STOP + 新 ADR。

**Commits（Day 1）**:
| Hash | Subject | 對應 |
|---|---|---|
| `14a5504` | docs(analysis): ceiling diagnostic resolves §6 | 乙類收口(前置)|
| `70b7b85` | chore(eval): leaf-anchor diagnostic harness | W98 motivation |
| (本 commit) | docs(planning): W98 kickoff(draft) | F0 kickoff |

**F1 落地（用戶確認轉 active 後）**:
- `section_anchor_markers.py`：`inject_section_anchored_markers` 加 `nearest: bool = False`。統一 anchor 選擇邏輯 —— `anchored_meta[sha8]=(chapter,doc_order)` + `anchors` list(chapter,doc_order,end_offset);`nearest=False` → target = chapter-last offset(全同章節 aux map 同一 offset = W75 byte-identical);`nearest=True` → target = `min(same-chapter anchors, key=(|doc_order diff|, offset))`。cap 由 per-target offset 套用。
- knob `section_anchor_nearest` 四層:`Settings`(bool=False)/ `KbConfig`(bool|None)/ `DocConfig`(bool|None)/ `PerQueryOverrides`(bool|None)/ `EffectiveConfig`(bool)+ resolve block(per-query > [per-DOC > per-KB] > global,mirror `section_anchor_max_per_anchor`)。
- 測試:4 新 nearest 測試(spread / single-anchor≡last / default-false-preserves-W75 / cap-per-anchor)+ 既有 14 全過 = **byte-identical 驗證**。
- **驗證**:`67 passed`（test_section_anchor_markers + test_effective_config + test_doc_profile_override + test_profile_routing)+ ruff clean + mypy --strict clean(`--explicit-package-bases`，項目無 mypy config)。
- **零行為改動**:default OFF → production 與 pre-W98 bit-identical(H1 production-preserve 達成)。

**Next**:F2（wire knob 經 effective_config → `/query` + `/query/stream` 兩注入點,off bit-identical route 測試）。**未開 —— 等用戶指示繼續定 pause**。

**Carry-over / 待決**:
- F1 knob 設計 = bool `section_anchor_nearest`（vs mode enum）—— 採 bool（Karpathy §1.2 simplicity）。
- F3 cap 決定 = nearest 後 drive-images-1 應否放寬/取消 `section_anchor_max_per_anchor`（診斷示 nearest 自然分散）。
- production default flip = out-of-scope，F5 列另一決定。
