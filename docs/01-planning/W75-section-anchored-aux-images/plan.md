---
phase: W75
name: section-anchored-aux-images
status: active       # reopened 2026-06-14 加 F5 每錨點 cap(DD-1 揭示 clump maxRun=39,用戶 trigger 優化)
created: 2026-06-14
owner: "Claude (AI) — 技術 Lead Chris 審閱"
gap: "ADR-0056 段 ②d 方案 A — `P1_sop_imgdense` 文件嘅 section 級錨定。把 post-synthesis attach_neighbour_images 撈嘅 un-anchored aux 圖(永遠冇 marker → 落末尾堆),按 source_section 章節級錨定入答案對應章節。實測 gate 三輪 PASS(末尾堆 22-55% + 章節級可錨率 100%)。"
adr: "ADR-0056(Accepted 2026-06-13)段②d render-side net-new 工作 cover。新 config knob = ADR-0040 四層擴展,非 new ADR。"
spec_refs:
  - docs/adr/0056-document-profiling-adaptive-recall.md          # 段②d 方案 A / line 117 / 252-253
  - backend/generation/citation_image_neighbors.py              # attach_neighbour_images(un-anchored aux 圖來源)
  - backend/api/routes/query.py                                 # :464 attach / :484 pin — 注入點 post-pin
  - frontend/lib/chat/citation-images.ts                        # :173 planAnchoredImages(reuse,零改動)
  - frontend/lib/chat/inline-image-markers.ts                   # :72 parseInlineImageMarkers(membership 保護)
  - backend/generation/effective_config.py                      # :54/:99/:292 knob 四層 mirror
  - backend/ingestion/profile_presets.py                        # P1_sop_imgdense preset 接駁
---

# W75 — section-anchored aux images(方案 A,ADR-0056 段②d)

> **緣起**:用戶開段②d → 我 push-back「先實測末尾堆殘餘量」(ADR-0056 roadmap conditional)→
> 三輪 gate 全 PASS(末尾堆 22-55% / 章節級可錨率 100%)→ 用戶拍板「開 W75 phase build」。本段兌現。
>
> **R6 grounding(已做齊)**:
> - **un-anchored 來源**:`attach_neighbour_images`(`citation_image_neighbors.py`)post-synthesis 撈
>   aux 圖入 `citation.embedded_images`,synthesizer prompt 見唔到 → 永遠冇 `[IMG#sha8]` marker。
> - **frontend 分流**:`planAnchoredImages(content, capped)`(`citation-images.ts:173`)regex parse 答案
>   marker,有 marker = inline / 無 = `trailing`(末尾堆)。`parseInlineImageMarkers` 有 membership +
>   first-occurrence dedup(`inline-image-markers.ts:72`)。
> - **方向判斷(H7 關鍵)**:採**方向 1 — backend marker 注入**(post-attach 喺答案文字流插 un-anchored
>   圖 marker)→ frontend `planAnchoredImages` 照常 parse,圖自動變 inline → **frontend 零改動 → H7
>   唔 trigger**。方向 2(frontend 改 render 按 section 插)= H7 trigger 要 mockup,**不採**。
> - **gate via config knob**:`enable_inline_image_markers` 四層(settings:160 / effective_config:54+99+292
>   / kb:115 / doc_config:60)mirror;新 knob `enable_section_anchored_aux_images` 同模式。knob OFF =
>   bit-identical(末尾堆現狀,production-preserve)。
> - **profile gate**:ADR-0056「條件式」核心 — 方案 A 只喺 P1 結構化 SOP 收益高風險低,P2/prose 反噬。
>   gate via knob(W73 PROFILE_PRESETS P1_sop_imgdense → knob ON),非 query 時重算 profile。

## 1. 行為設計

### D1 — config knob `enable_section_anchored_aux_images`(ADR-0040 四層)
- `settings.py`:global default **False**(production-preserve;mirror `enable_inline_image_markers`)。
- `effective_config.py`:`QueryConfigOverlay`(`bool | None`)+ `EffectiveConfig`(`bool`)+ `_resolve`
  四層(pq → dc → kb → settings)。
- `kb.py` / `doc_config.py`:`bool | None = None`(per-KB / per-doc override)。

### D2 — 注入 pure function `inject_section_anchored_markers`(新 module `section_anchor_markers.py`)
- 簽名:`inject_section_anchored_markers(answer: str, citations: list[Citation], *, section_prefix_depth: int = 1) -> str`。
- 演算法:
  1. regex `[IMG#<sha8>]` 抽答案**已有** anchored marker sha8 set(synthesizer 寫,chunk 自帶圖)。
  2. 建 `anchored sha8 → source_section`(從 `citations.embedded_images` sha8 match)。
  3. **un-anchored** = `citations.embedded_images` 中 sha8 **不在**答案 marker set 的圖。
  4. 每個 un-anchored 圖(按 `doc_order` 排),按 `source_section[:depth]` match 答案中**同章節最後一個**
     anchored marker,喺其後插 `[IMG#<sha8>]`。
  5. **無同章節錨點** → 不注入(留 trailing,frontend 末尾堆 — 對齊章節級可錨率 < 100% 的殘餘)。
- **純函數零 IO**(answer text + citations → new answer text);testable 無 mock。
- **placement trade-off**:同章節多 un-anchored 圖 clump 喺「最後一個 anchored marker 後」(aux-heavy query
  章節內堆),按 `doc_order` 排序緩解閱讀流;比末尾堆明顯貼近原文。leaf 級精準錨(2-82%)留後續優化。

### D3 — query.py wire(gate)
- `effective.enable_section_anchored_aux_images` ON → **post-`pin_chapter_overview_images`**(citations 最終
  確定後)call `inject_section_anchored_markers(answer, citations)` 改 answer text;OFF → 不 call(bit-identical)。
- graceful:注入 try/except → 失敗 fallback 原 answer(per ADR-0034 §Consequences degradation 模式)。
- **frontend membership 保護**:注入被 frontend cap 掉的 sha8 → `parseInlineImageMarkers` strip(merge text),無害。

### D4 — W73 preset 接駁
- `profile_presets.py` `P1_sop_imgdense` preset 加 `enable_section_anchored_aux_images=True`(接 W73 routing
  auto-write,P1 圖密 SOP 自動開);其餘 profile preset 不設(繼承 global False = 末尾堆,避反噬)。

### D5 — 每錨點 cap(F5,DD-1 後 clump 優化)
- 新 config knob `section_anchor_max_per_anchor: int`(ADR-0040 四層,global default **0 = 無 cap**)。
- inject 函數加 `max_per_anchor: int = 0` 參數:每章節注入時取 `doc_order` 前 N 圖,**超出不注入**(留 trailing 末尾堆)。
- 0 = 無 cap(F1-F4 行為 bit-identical);N>0 = clump 限 N,超出回末尾堆。
- **trade-off**:clump 限 N vs 末尾堆部分回歸(DD-1 量 39 圖,cap=N → N inline + (39-N) trailing)。實測 browser 定 N。
- **placement 不變**:仍插同章節最後一個 anchored marker 後,只係 cap 注入數。leaf 級精準錨另議(可錨率 tension)。

## 2. 交付物 + Gate

| # | 交付 | Gate |
|---|---|---|
| **F1** | config knob `enable_section_anchored_aux_images` 四層(settings / effective_config QueryConfigOverlay + EffectiveConfig + _resolve / kb / doc_config) | mypy 0 + ruff 0;`test_effective_config` 全綠 + resolve test |
| **F2** | `section_anchor_markers.py` `inject_section_anchored_markers` pure function + query.py post-pin gate wire | mypy 0 + ruff 0;query 既有 test 全綠 |
| **F3** | test:inject pure function(同章節錨定 / 無錨點留 trailing / doc_order 排序 / knob OFF bit-identical)+ resolve 四層 | pytest 綠(H6 — generation 模組同步 test)|
| **F4** | preset 接駁(`profile_presets.py` P1_sop_imgdense knob=True)+ 實測 drive-images-1 /query 末尾堆縮小 + memory + closeout | 末尾堆 22-55% → 大幅縮小;closed |
| **F5** | 每錨點 cap(DD-1 後優化):`section_anchor_max_per_anchor` 四層 knob + inject `max_per_anchor` 參數 + query.py 兩處傳 + test + 實測 browser clump 改善 | clump maxRun 39 → N;末尾堆回歸量量度;browser 肉眼確認 |

## 3. Acceptance Criteria

- **AC1(章節級錨定)**:knob ON,un-anchored aux 圖(`source_section[:1]` match 答案已有 anchored marker
  章節)→ 注入 marker → frontend `planAnchoredImages` 變 inline;實測 drive-images-1 末尾堆 22-55% 大幅縮小。
- **AC2(production-preserve)**:knob OFF → `inject` 不 call → answer text bit-identical 現狀(末尾堆不變)。
- **AC3(無錨點留 trailing)**:un-anchored 圖無同章節 anchored marker → 不注入 → 留 frontend 末尾堆
  (對齊章節級可錨率 < 100% 殘餘,唔強行錯位錨定)。
- **AC4(frontend 零改動 → H7 唔 trigger)**:frontend reuse W71 `planAnchoredImages` + `InlineImageCard`,
  render 機制零改動;視覺 = W71 inline card 更多咗,樣式不變。
- **AC5(profile gate)**:W73 PROFILE_PRESETS P1_sop_imgdense → knob ON;P2/prose 繼承 global False(末尾堆,避反噬)。
- **AC6(H6)**:inject pure function + resolve 四層有 test。

## 4. 風險

- **R1 🟡 章節內 clump**:aux-heavy query(如 create-FA 6 anchored / 43 un-anchored)同章節圖 clump 喺一個
  anchored marker 後。緩解:注入按 `doc_order` 排序;比末尾堆明顯改善。leaf 級精準錨留後續(query-dependent)。
- **R2 🟢 frontend cap mismatch**:backend 注入被 cap 掉的 sha8 → frontend membership check strip(merge text),
  無害(`parseInlineImageMarkers` 已驗證)。
- **R3 🟢 純文字 section 錨唔到**:答案 prose 無 section heading,純文字 section(無 chunk 自帶圖 = 無 anchored
  marker)錨唔到 → un-anchored 圖留 trailing(AC3)。章節級可錨率 100% 保證每圖搵到同章節錨點。
- **R4 🟢 knob OFF 零回退**:gate via config,OFF bit-identical(AC2)。

## 5. 非目標

- ❌ **frontend 改 render**(方向 2)— 採方向 1 backend 注入,frontend 零改動。涉 frontend 改 = H7 STOP+ask。
- ❌ **leaf 級精準錨定**(2-82%)— 先做章節級(prefix-1,100%);leaf 級 query-dependent 留後續。
- ❌ **跨模組查詢精準寬度**(層 B,OQ-E)— 方案 A 縮窄單一 P1 文件末尾堆;跨模組靠 `max_images_per_answer` 鈍器。
- ❌ **P2/P3/P4/P5 profile section 錨定** — 只 P1_sop_imgdense(條件式,避反噬 per ADR-0056 D7)。
- ❌ **三層 UI**(段③)— 卡 H7 OQ-B 無 mockup。

## 6. H 核對

- **H1**:改 generation pipeline(query.py 加 marker 注入 step)— **ADR-0056 段②d render-side cover**
  (line 117 / 252-253 明列方案 A net-new);新 config knob = ADR-0040 四層擴展,非 new vendor / component → 非 new ADR。
- **H2**:零新 dep(regex / pure function,reuse 現有)。
- **H3**:不觸。
- **H4**:section 錨定 = text / section signal only(source_section 章節 match),**無** image embedding /
  multimodal retrieval(Tier 2 禁)— 不觸。
- **H5**:不觸。
- **H6**:inject pure function + resolve 四層同步 test(generation 模組)。
- **H7**:**方向 1 frontend 零改動 → 唔 trigger**。若 implement 發現 frontend 需改 render → **STOP+ask**。

## 7. Changelog

| Date | Change | Reason |
|---|---|---|
| 2026-06-14 | Initial plan(active)| 用戶開段②d → push-back 先實測(三輪 gate PASS:末尾堆 22-55% / 章節級可錨率 100%)→ 拍板開 W75。R6 grounding 確認方向 1(backend marker 注入 → frontend 零改動 → H7 唔 trigger);gate via ADR-0040 四層 knob(mirror enable_inline_image_markers);profile gate via W73 PROFILE_PRESETS P1_sop_imgdense |
| 2026-06-14 | Closeout(closed,PASS)| F1-F4 全成。F1 knob 四層 + F2 inject pure function + /query + /query/stream 兩處 gate wire(stream 經 compose_query_stream 新 answer_post_process callback,done.answer BUG-028 ② replace → frontend 零改動,H7 實證唔 trigger)+ F3 10 inject + 5 resolve test + F4 preset 接駁 + 實測。**實測末尾堆 28-85% → 0%**(3 真實 query 全錨,offline apply on 舊 code /query 答案,零 restart)。mypy 新 code 0 + ruff clean;pytest 51 + 48 + 7 全綠。無 deviation。**deferred**:DD-1 browser 肉眼(W71 同款 headless-only)。**carry-over**:段②d leaf 級精準錨(2-82%,query-dependent)+ 段③ 三層 UI(卡 H7 OQ-B mockup)|
| 2026-06-14 | Reopen 加 F5(active)| DD-1 browser 肉眼揭示 clump 偏重(每步驟圖卡 [39,1,1,1,1,1,1],maxConsecutiveFigureRun=39)。用戶初選接受現狀,後 trigger「每錨點 cap 試吓改善 clump」→ 重開加 F5。D5 = `section_anchor_max_per_anchor` 四層 knob(global default 0 = 無 cap,保 F1-F4 bit-identical)+ inject `max_per_anchor` 參數(每章節注入 doc_order 前 N,超出回 trailing)。trade-off:clump 限 N vs 末尾堆部分回歸,實測 browser 定 N |
