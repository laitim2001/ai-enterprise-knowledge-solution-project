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

**F2 落地**:
- 兩個注入點各加 `nearest=effective.section_anchor_nearest`：`/query`（query.py:529)+ `/query/stream` `_inject_stream_answer` callback（query.py:714)。try/except graceful 未碰。
- 測試:`test_effective_config.py` 加 5 個 `section_anchor_nearest` 四層 resolve 測試（global default False / per-KB / per-DOC / per-query wins / legacy dict None）。**70 passed**（effective_config + query_per_kb_config + query_doc_config_overlay + section_anchor_markers)+ ruff clean。
- **off bit-identical**:default resolve False（測試）+ 既有 route 測試全過（行為不變）+ F1 function byte-identical（mirror W75 既有 pattern:無獨立 route inject 測試）。
- **mypy note**:query.py 既有 81-error baseline（line 82/203/723/767 等 pre-existing tech debt,項目無 mypy config / route 檔無 clean --strict baseline)；我加嘅 529/714 唔在 error list = 本改動 type-clean。§1.3 surgical 唔掂無關 error。

**F3 落地（offline,零 backend）**:
- `scripts/diag_leaf_anchor_capsweep.py` reuse 18 captures,用**生產函數**跑 `{last,nearest} × cap∈{0,3,5,8}`（`reports/leaf_anchor_capsweep.json`）。總可錨 aux = 235。
- 數據（clump 平均/最壞 · placed · trailing）:

  | config | clump 平均 | clump 最壞 | placed | trailing |
  |---|---|---|---|---|
  | last_cap0 | 13.89 | 38 | 235 | 0 |
  | last_cap5（現 prod） | 5.22 | 7 | 79 | 156 |
  | last_cap8 | 6.56 | 10 | 103 | 132 |
  | nearest_cap0 | 7.22 | 16 | 235 | 0 |
  | nearest_cap5 | 5.44 | 9 | 189 | 46 |
  | **nearest_cap8** | 6.33 | 12 | 218 | 17 |

- **洞察**:現 prod（last_cap5)掉 156/235（66%)去 trailing = §15 還原缺口;nearest 每 cap 壓倒 last（多 placed + 細 clump,因分散）。trailing（圖脫離步驟)比 clump（密但近步驟)更傷 §15。
- **決定（用戶 2026-06-27)**:drive-images-1 = **nearest + cap8**（置 218/235 = 93%,trailing 17,clump 最壞 12 << 現無-cap 38）。cap0 極致（全置)留 fallback;cap5 保守留 fallback。
- config 套用 + 驗證留 F4（production A/B + browser）。

**Next**:F4（production A/B + browser）—— **需重啟 backend**（running server 仲係 pre-F1 stale,要 pick up nearest wiring）+ 設 drive-images-1 per-KB `section_anchor_nearest=true` + `section_anchor_max_per_anchor=8` + image-recall/marker-order 唔回退 + browser 肉眼。**等用戶指示**。

**Carry-over / 待決**:
- F1 knob 設計 = bool `section_anchor_nearest`（vs mode enum）—— 採 bool（Karpathy §1.2 simplicity）。
- F3 cap 決定 = nearest 後 drive-images-1 應否放寬/取消 `section_anchor_max_per_anchor`（診斷示 nearest 自然分散）。
- production default flip = out-of-scope，F5 列另一決定。
