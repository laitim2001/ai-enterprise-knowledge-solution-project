# W63 — progress(Q005 section-miss 診斷)

> Daily progress + decisions + commits + 結尾 retro。對應 plan.md / checklist.md。

## Day 1(2026-06-12)— kickoff

### 背景
- 隊列 ②(用戶 2026-06-12「繼續執行下一項」)。起點 = W62 假設:rerank=10 → Q005 6/6 = 1.00;
  rerank=5 → 擲毫(跨 W61+W62:1.00/0/1.00/0/0)。
- Q005 GT:S17–S22 六 section(collection letter 設定 + 生成),32 圖,單一文件
  `drive-user-manual-0601-ar-fna-ar-management-v0-03`。
- 三個候選機制:(a) rerank 邊界浮沉 /(b) synthesizer cite 隨機 /(c) neighbour 收割 artifact。

### R6 核實(詳 plan.md 頭注)
- V4 `retrieval-test` schema(rank/section_path/score)✅;`/query` per-query `top_k_rerank`
  (CH-007)✅ → 零 KB PATCH 設計;Citation 有 section_path ✅。
- KB 現狀已係原值(W62 F4 復原 readback 為證),本 phase 不郁。

### 三件套 committed(R1 gate)
- `docs(planning): W63 Q005 section-miss diagnosis kickoff`(`86d0689`)

### F1 — V4 retrieve-only ×5 ✅ AC1:**機制 (a) 反證**
- 5 runs top-20 **逐位元相同**(rank/score/chunk 全同)→ retrieval + rerank 層完全 deterministic
  (hybrid 無 semantic ranker + Cohere 對同 input 同 output)。
- GT section 排位極好:**top-5 = AR07 8.1.2 ×4(ci 65/66/68/67)+ AR06 7.1.2 ×1(ci=60,rank 3)**;
  rank 6-15 仲有 AR06 ×4 + AR07 ×3 + doc-root(ci=1,rank 8)。
- **關鍵結構事實:rerank=5 嘅候選池入面 AR06(Setup)只有一條** — 單錨點。

### F2 — `/query` @ rerank=5 ×6 ✅ AC2:**flip 喺 cite 層,兩種失敗子模式**
| Run | cits | 圖 ref / unique | GT hit | cited sections | 分類 |
|---|---|---|---|---|---|
| 1 | 10 | 20 / — | — | **Scope ×3** + AR07 ×7(**AR06=0**)| **b-1 位移** |
| 2 | 11 | 20 / — | — | AR06 ×4 + AR07 ×7 | 全覆蓋 |
| 3 | 11 | 20 / — | — | AR06 ×4 + AR07 ×7 | 全覆蓋 |
| 4 | **0** | **0 / 0** | 0/32 | (無) | **b-2 零引用** |
| 5 | 11 | 20 / 9 | 9/32 | AR06 ×4 + AR07 ×7 | 全覆蓋 |
| 6 | 14 | 20 / 9 | 9/32 | AR06 ×4 + AR07 ×7 + Scope ×3 | 全覆蓋(pin 附加)|

- **b-1 位移**:LLM 唔 cite 唯一嗰條 AR06(rank 3)→ expansion(prefix_depth=1)無 AR06 錨點可擴
  → Setup 半邊連文帶圖消失,引用被 Scope/overview 取代。
- **b-2 零引用**:synthesizer 出咗答案但**一條 citation 都冇**(cits=0/imgs=0)— 就係 W61/W62
  cap=60 嘅 returned 0↔32 flip 真身;W25 D4 refuse-pattern 同族。
- Scope ×3 引用 = `enable_chapter_overview_pin=true`(per-KB)附加,**唔係** flip 源頭(機制 (c) 排除為次要)。

### F3 — `/query` @ rerank=10 ×6 ✅ AC3:**假設證實,機制清晰**
- **6/6 runs 結構完全一致**:11 citations = AR06 ×4 + AR07 ×7,零位移、零零引用。
  連同 W62 6 runs = **rerank=10 累計 12/12 零 flip** vs rerank=5 異常率 ~1/3(本日 2/6)。
- **點解穩**:top-10 候選有 **三條 AR06**(ci 58/59/60)→ 錨點冗餘,LLM 點揀都有 AR06 入 cite 池
  → expansion 必有錨點 → Setup 永遠覆蓋。rerank=5 嘅單錨點 = single point of failure。

### 額外發現(code 核實)— cap 預算被重複 ref 食
- 全部成功 run:20 個圖 ref 只有 **9 個 unique**(GT 9/32)— expansion aux citation 重複嵌入
  section-mates 嘅圖,`cap_images_per_answer`(citation_enrichment.py:111)**by design 唔做
  cross-citation dedup**(ADR-0040 blunt;docstring 明文)→ cap=20 預算 >50% 浪費喺重複。
- 呢個 + W62 拼出完整鏈:**cap=20 → 9 unique;cap≈50 + max_aux=40 → 32/32**(W62 D/E/F 臂)。
- 候選改善(**未做,H1-adjacent**):cap 前先 dedup = pipeline 行為改動 → 要 STOP+ask/ADR;
  或者直接用 W62 preset(cap≈50)令問題 moot。

### F4 — 判決 + 一般化(AC4)
1. **機制判決:(b) cite 層雙模式**((a) retrieval 反證 deterministic;(c) pin 次要非源頭):
   - **b-1 單錨點位移**(~1/6 @ rerank=5):multi-part query 嘅其中一 part 喺 rerank cutoff 內
     只有一條 chunk → LLM cite 隨機性直接賭嗰一條。
   - **b-2 零引用**(~1/6 @ rerank=5):synthesizer 無引用輸出(refuse 同族,獨立於 k 嘅
     synthesizer 行為;rerank=10 嘅 12 runs 未見,但唔可以斷言 k 直接消除佢)。
2. **rerank_k=10 = 錨點冗餘 fix**(per-KB 零 code)— 證據型機制,非 W62 碰彩。
3. **風險一般化**:任何「set up X and then do Y」跨章節雙段 query,當其中一章喺 top-k 代表
   不足(1 條)就有 b-1 風險;圖密手冊常見(章節多、每章 chunk 數少)。「成功定義 = section
   覆蓋」嘅指標會直接捕捉 b-1(支持用戶 pending 嘅定義決策方向)。
4. **AC5 ✅**:全程 per-query override,零 KB 狀態改動(免復原)、零 code、無 ADR。

### Retro
- 分層設計(V4 retrieve-only vs `/query` full pipeline)一 phase 內反證一個機制、證實一個機制、
  捉到兩個失敗子模式現行 — 5 + 12 = 17 個 run,半日內完成,零狀態殘留。
- per-query `top_k_rerank`(CH-007)係診斷利器:免 PATCH 免復原,A/B 喺 request 層面完成。
- 連 W62:圖密 KB preset 配方更新為**四件套**:`max_aux=40` + `rerank_k=10`(錨點冗餘)+
  `cap≈50` + (可選)overview pin;b-2 零引用係剩餘 ~低概率殘留風險,等 production 觀察。
- 下一步(隊列):③ faithfulness 警告閘 / ④ 圖片指標入 UI / ⑤ 圖密 preset persist —
  ⑤ 而家有齊 W62+W63 實證,係最快可收割嘅一項,但 persist 係用戶決策。
