# W98 — Leaf-level(doc_order-nearest)圖片步驟級錨定(甲類)

| 項目 | 值 |
|---|---|
| Phase | W98-leaf-anchor-precision(source-fidelity §15 北極星線 · ADR-0056 段②d leaf 級)|
| Status | **closed — G-W98 PASS**(2026-06-27;F1-F5 全完成,leaf 級 nearest knob 落地,drive-images-1=nearest+cap8,ADR-0056 amendment)|
| Tier | Tier 1(改 `section_anchor_markers.py` 注入定位策略,knob-gated default 保留現狀)|
| 依賴 | ADR-0056 段②d(章節級 section-anchor inject 已落地 W75)+ W98 前置 offline 診斷(`scripts/diag_leaf_anchor.py`,commit `70b7b85`)|
| 錨點 | **CLAUDE.md §15 北極星**・ADR-0056 段②d roadmap「leaf 級精準錨」・memory [[principle_source_fidelity_recall]] 甲類・[[project_inline_image_markers_w70]] W75 段 |
| 粗估 | 中(F1-F5;pure function 換錨點策略 + knob + config + A/B + browser 驗)|
| 下一期 | production default flip(另一決定,類 ADR-0052;需 F4 正向 + 再確認)|

> **H1 gating**:本 phase 改 `section_anchor_markers.py` 注入定位(§3 RAG core-adjacent),但 **(a)** knob-gated default 保留現狀(production-preserve)+ **(b)** 屬 ADR-0056 段②d **pre-scoped「leaf 級精準錨」** 嘅後續落地 → 預期 **ADR-0056 amendment**(非新 ADR)。若實作中 scope 超出 leaf-anchor(例如改檢索 / 改 chunk / 加 vendor)→ **STOP + 新 ADR**(§5.1 H1)。

## §1 目標(Why)

**北極星(§15)**:答案要忠實還原原文圖文鄰接 —— 原文某步驟有圖跟隨,recall 嗰步時圖應落喺嗰步旁。

**現狀缺口(W75 段②d 章節級)**:`inject_section_anchored_markers` 把同章節全部 un-anchored aux 圖注入到**章節最後一個 anchored marker 後**(`source_section[:1]` 章節級),`doc_order` 只用嚟 sort 唔用嚟揀錨點。高圖密 query 因此把幾十張圖 clump 喺一個步驟後(W75 DD-1 肉眼見 `[39,1,1,…]`),cap5 緩解後 overflow 又掉返 trailing。

**前置診斷實證(W98 offline,18 captures,9 query × 2 run,`reports/leaf_anchor_diag.json`)**:把錨點由「章節最後」改成「**`doc_order` 最近**」(leaf 級)係 **Pareto 正向** ——
- **worse = 0**(nocap clump 從不更差、cap5 錨定數從不更少);
- **幫到 8/18**(全部高圖密),低圖密 10 個乾淨 no-op(章節單錨點 → nearest=last);
- production cap5 下 **110 張圖由 trailing 救返正確步驟**(Q036/Q043 單條多達 +23~28);nocap clump 平均 −6.67(最大 −22,Q036 37→16)。
- 細 caveat:cap5 下 4 個極高密度 capture 最壞 clump 輕微 +1~2(因錨定多咗成倍)→ 划算 trade + 揭示可放寬 cap。

**緩解 = 把注入錨點由「章節最後」改成「`doc_order` 最近」**,令高圖密 query 嘅圖分散到對應步驟旁(§15 還原度),knob-gated 保留現狀。

## §2 Deliverables(F1–F5)

| # | Deliverable | Acceptance |
|---|---|---|
| **F1** | `section_anchor_markers.py` nearest-anchor 策略 + 新 knob `section_anchor_nearest`(bool,ADR-0040 四層,default **False** = 現行章節最後)+ 單元測試 | knob OFF → `inject_section_anchored_markers` 輸出 **byte-identical** pre-W98(substring + byte test);knob ON → 每個 un-anchored aux 錨到同章節 `doc_order` 最近 anchored marker(tie → earliest offset);單錨點章節 nearest≡last(等價測試);cap 互動測試;pure function 零 IO;pytest + ruff + mypy clean |
| **F2** | Wire knob 經 `effective_config` → 兩個注入點(`/query` query.py + `/query/stream` `answer_post_process` callback)| effective config → inject 正確帶 `section_anchor_nearest`;**off bit-identical**(route 測試);try/except graceful 保留 |
| **F3** | cap 互動 + drive-images-1 config 決定(nearest 自然分散 → 或可放寬/取消 `section_anchor_max_per_anchor`)| 用既有 diag harness 量 nearest × cap∈{0,5,higher} 嘅 clump↔placement↔trailing trade,揀 drive-images-1 推薦 config(nearest + cap 調整);記 trade 數據 |
| **F4** | **Production A/B 驗證(running backend,非 offline)+ browser 肉眼** | 重啟 backend pick up code(reload=False,[[project_stale_backend_no_reload]]);image-recall **唔回退**(≈1.0,`run_image_recall`)+ marker order-consistency **唔回退**(`check_marker_order`)+ clump 量化降;**browser 肉眼**高圖密 query(Q001/Q036)確認圖分散到步驟、唔 clump(W75 DD-1 教訓:headless 靚 ≠ 視覺靚)|
| **F5** | Doc-sync + ADR-0056 amendment + memory + DEFERRED close + production default flip 列另一決定 | ADR-0056 加 leaf-級 amendment(注入錨點策略 + knob);`docs/08-user-guide` 若涉 default 同步;memory [[project_inline_image_markers_w70]] + [[principle_source_fidelity_recall]] 更新;DEFERRED「leaf 級精準錨」close;**default flip(knob OFF→ON / preset)= out-of-scope 另一決定** |

## §3 Phase Gate

- **G-W98**:F1 knob OFF byte-identical(production-preserve)+ nearest 單元測試綠(spread / single-anchor 等價 / cap 互動)+ F4 production A/B **clump↓ + placement↑ 且 image-recall / marker-order 唔回退** + browser 肉眼確認 + ADR-0056 amendment(非新 ADR 確認)。
- A/B 若 image-recall 或 marker-order 回退、或 browser 見新 clump regression → **唔可以** flip default,先診斷根因(W75 教訓:offline 量化 ≠ 視覺品質,兩者都要過)。

## §4 Risks

- 🟡 **cap5 最壞 clump 輕微 +1~2(極高密度)**:診斷已見(Q036.0 7→9)→ F3 cap re-tune;A/B 同睇 max-run 唔好惡化。
- 🟡 **synthesizer stochastic**(W75 教訓 7):同 query 不同 run 答案結構唔同 → A/B 用 same-structure run 或 offline apply on 固定答案量化更穩;browser 對比要 same-structure。
- 🔴 **backend reload=False**:改 prompt/inject code 後**必須重啟** pick up([[project_stale_backend_no_reload]];pytest 綠 ≠ running server 有該 code)。
- 🟡 **H1**:ADR-0056 amendment gating;scope 若超 leaf-anchor → STOP + 新 ADR。
- 🟡 **PATCH config 受 `require_kb_acl("edit")` 守衛**(W88 P0):A/B 若需 flip per-KB config,dev-token 須有 edit ACL(診斷用 GET+PATCH 已驗可行)。
- 🟢 **零新 vendor / dep**;pure function 改動,blast radius 細。

## §5 Out of scope(留後續)

- **Production default flip**(`section_anchor_nearest` OFF→ON 全域 / preset)= 另一決定(類 ADR-0052),需 F4 正向 + 再確認。本 phase 只 land 策略 + knob + A/B 驗。
- **乙類完整度**(W96/W97 收口,generation-side ceiling,`source_fidelity_recall_external_research_20260626.md` §6)— 不屬本 phase。
- **image embedding / multimodal retrieval**(H4)— 純文字 / section / doc_order 信號。
- **caption 抽取 / alt_text**(原文 figure 無 caption)— 不碰。

## §6 Changelog

| 日期 | 變動 | 由 |
|---|---|---|
| 2026-06-26 | Phase draft kickoff — 乙類收口(generation-ceiling 診斷)後用戶拍板轉甲類圖錨定;W98 前置 offline 診斷(18 captures)證 doc_order-nearest = Pareto 正向(worse=0 / 110 張救返 / clump 37→16)→ 寫 plan productionize。F1-F5 分段,knob-gated default 保留現狀,ADR-0056 amendment(leaf 級 pre-scoped)。**待確認轉 active** | 草案 |
| 2026-06-26 | **用戶確認轉 active → F1 落地**:核心 `inject_section_anchored_markers` 加 `nearest: bool=False` 參數(doc_order 最近錨點選擇,統一邏輯 `nearest=False` byte-identical)+ knob `section_anchor_nearest` 四層(Settings/KbConfig/DocConfig/PerQueryOverrides/EffectiveConfig+resolve)+ 4 個 nearest 測試;67 passed(含既有 14 byte-identical)+ ruff + mypy --strict clean | F1 |
| 2026-06-27 | **F2-F5 完成 → G-W98 PASS,phase closed**:F2 wire 兩注入點 + 5 resolve 測試（`828f85b`）;F3 cap-sweep → drive-images-1=nearest+cap8 用戶拍板（`8ca31a2`）;F4 production A/B（recall set 不變 + backend honors nearest + browser §15 verdict PASS）（`d7762b1`）;F5 ADR-0056 amendment + memory + DEFERRED DD-10 leaf trigger close + user-guide N/A（global default 不變）。**無新 ADR / 無新 vendor / global default OFF production-preserve**。甲類 nearest 上限 = 乙類完整度（已收口）兩腿相連 | F2-F5 + close |
