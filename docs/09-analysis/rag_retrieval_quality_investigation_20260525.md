# RAG Retrieval Quality Investigation Brief

**Date**: 2026-05-25
**Status**: Investigation brief — handed to AI assistant for research & tuning
**Scope**: Chat-page query quality(內容 recall、內容/圖 relevance、圖文關聯一致性)
**讀者**: Claude Code(本 repo AI 助手)
**Related prior doc**: `docs/03-implementation/image-chunk-retrieval-investigation-2026-05-23.md`

---

## 0. 俾 AI 助手嘅前置指示(讀落去之前必讀)

呢份 brief 係**調查 + 調優方向**,唔係 implementation order。落手之前:

- **遵守 CLAUDE.md Hard Constraints**。下面每個方向都標明咗係 🟢 Tier-1-safe(調參 / bug-fix,可自行做)定 🟡 trigger H1/H2/H4(STOP and ask + 寫 ADR)。**唔可以**因為「順手」就把 🟡 方向當 🟢 做。
- **遵守 §10 R1**:任何 multi-day implementation 之前要有對應 phase `plan.md`。本 brief 唔等於 plan。
- **遵守 §1 Karpathy baseline**:eval-driven,一次郁一個旋鈕,唔好憑感覺一次過改多樣嘢。
- 唔清楚 → ask,唔好 guess(§13)。

---

## 1. 問題現象(觀察到嘅 symptom)

測試 query:**「show me all the Integration scenarios」**,KB = `sample-document-with-image-1`(source doc `DCE_Integration_Platform_Implementation_Plan`,88 chunks)。

1. **回答唔完整 + 有唔相關內容**:文件實際有 5 個 integration scenario,但回答只有 Scenario A 有名,其餘籠統;同時夾雜咗唔相關段落。
2. **圖唔完整 + 有唔相關圖**:返回 4 張圖,其中 figure 4「3.1 Platform composition」屬 §3(Architectural principles),同 query 嘅 §8(Integration scenarios)唔同節 → topically off。
3. **計數唔一致**:回答 body 顯示 4 張 figure,但「REFERENCED SCREENSHOTS」strip 同右邊 Sources panel 都只顯示 3。

### 關鍵反證(重要 context)
同一條 query 喺 **Dify(用住 rerank-v4.0-pro)上一樣 fail**,直接答「I'm not sure about that」。Dify 用 `Top K = 3~4`、General(定長)chunking mode。**結論:呢個唔係 EKP 獨有 implementation bug,而係「enumeration query」同「定長 chunking + top-k retrieval」架構嘅本質 mismatch。** 調 rerank 參數只能改善,解決唔到根本。

---

## 2. Root cause 拆解(三個問題分屬唔同層,唔好當同一件事修)

### 問題 3 — 純前端顯示計數 bug(🟢 bug-fix,同 RAG 無關)
- 實際只 cite 咗 3 個 chunk(#44 / #55 / #8),但 chunk #44 身上掛住 **2 張圖** → 3 citations × 圖 = 4 張。
- Inline figure 用 `flatMap` 攤平所有圖 → 數到 4(`frontend/app/(app)/chat/page.tsx:1228-1245`)。
- Referenced screenshots strip 每個 citation **只取第一張** `c.embedded_images[0]`(`chat/page.tsx:1797`)→ 只出 3 個 thumbnail。
- Sources panel 嘅「N with screenshots」數**有圖嘅 citation 數**,唔係圖數(`chat/page.tsx:2126`)。
- **即係三個 UI 表面用咗三套唔同計數語意**(一套數圖、兩套數 citation)。Deterministic,改完即一致。要決定:gallery flatMap 全部圖(同 inline 對齊)定 sources 改成數圖。**⚠️ 注意 H7**:呢個改 UI rendering,要對住 `references/design-mockups/` 對應頁睇清楚 mockup 點處理 multi-image citation,唔可以 approximate。

### 問題 1 — Enumeration query 撞正 factoid-tuned pipeline(🟡 根治 trigger H1)
- `top_k_rerank` 預設 = 5;Cohere rerank `top_n=min(top_k,…)` 之後淨低 5 個 chunk。
- **Cohere rerank 完全冇 score threshold**(`backend/retrieval/reranker/cohere.py:96-130`,純粹攞 top_n,唔理 relevance 幾低)→ 排第 4/5 嘅低分 chunk 照入 context → **唔相關內容**來源。
- 「show me **all** X」需要**高 recall + 跨 chunk 聚合**(砌返成個 §8 五個 scenario),但 top-5 precision-oriented retrieval 本質做唔到窮舉 → **回答唔完整**來源。
- chunk #8(§3.1,relevance 0.916)被 cite 係 retrieval precision 外溢:語意接近但 topically off。

### 問題 2 — 圖靠「位置鄰近」而非「query 相關」(🟢 調參 / 🟡 根治視乎做法)
- `attach_neighbour_images()`(`backend/generation/citation_image_neighbors.py:41-132`)喺每個 cited chunk **±3 chunk**(`neighbour_window=3`)內、最多 +2 張(`max_aux_per_citation=2`)鄰居圖塞落去,**只靠 `chunk_index` 鄰近,完全唔睇張圖同 query 相唔相關**。
- `backend/retrieval/hybrid.py:66-97` 對 low-value-chunk-with-image 用 `image_weight=0.7` 保留(唔 drop)。
- 兩個機制都係「寧濫莫缺」塞圖 → **唔相關圖**來源。

---

## 3. 調優方向(分 Tier-1-safe vs 需 ADR)

### 🟢 Tier-1-safe(調參 / bug-fix,可自行做,但仍要 eval-driven + 守 H7)

| # | 方向 | 動哪裏 | 預期效果 |
|---|---|---|---|
| A | **加 rerank score threshold** | `backend/retrieval/reranker/cohere.py` 加 relevance floor(初值試 0.3~0.4,drop 低於 floor) | 砍走唔相關內容 + 唔相關圖;最高 ROI 一刀 |
| B | **修前端計數一致** | `chat/page.tsx:1797 / 2126` | 解問題 3;**先對 mockup(H7)** |
| C | **收窄 / gate neighbour-image** | `citation_image_neighbors.py` 調 `neighbour_window` / `max_aux_per_citation`;或加「鄰居圖要 section_path 同源 / 過 relevance」gate | 減唔相關圖 |
| D | **調 `image_weight`** | `backend/retrieval/hybrid.py` low-value-image 保留權重 | 減 low-value image 上位 |

> ⚠️ 方向 D 注意:`image_weight` 屬 retrieval scoring 行為,如果只係改數值 = 🟢;如果改保留**邏輯**(drop/keep 規則)可能觸及 storage/retrieval 設計,要先判斷係咪 H1。

### 🟡 需 STOP and ask + ADR(architectural change,唔可自行做)

| # | 方向 | 觸發 constraint | 點解值得做 |
|---|---|---|---|
| E | **Parent-document / section-level retrieval**(small-to-big):retrieve 細 chunk 命中 §8,但餵成個 section 俾 LLM | H1(改 retrieval 架構 + storage 取用) | 對「show me all」最對症;一次過齊 5 個 scenario。Dify 嘅 Parent-child mode 就係呢樣 |
| F | **Query intent routing**:偵測 all/list/全部 → 動態 ↑top_k + 放寬 cutoff + 走 section retrieval | H1(新 component) | 唔影響 factoid query 嘅 precision |
| G | **Multimodal 圖文關聯**:用 image embedding 算 query↔image 相關度,取代純位置鄰近 | H2(新 vendor:CLIP-style / Cohere multimodal / Azure AI Vision) | 根治「唔相關圖」 |
| — | GraphRAG / 全局聚合 query | **H4 — Tier 2,Tier 1 唔做** | 明確 out of scope |

---

## 4. 「點調」—— Eval-driven 方法論(核心,唔好憑感覺)

之前「調極都唔好」嘅核心問題:**冇量度住嚟調**,唔知係 recall 唔夠定 precision 唔夠,結果亂試。正確流程:

1. **先量度,唔好先調。** 用 RAGAs + `docs/eval-set-v0.yaml`(+ `eval-set-v0-w25-supplement.yaml`),對失敗 query 跑:
   - **Context Recall** — 需要嘅 chunk 有冇 retrieve 到?低 → recall 問題(↑top_k / parent-child)。
   - **Context Precision** — retrieve 到嘅 chunk 相唔相關?低 → precision 問題(↑score threshold)。
2. **一次只郁一個旋鈕**,每次重新跑 eval,記低 metric delta。建議次序:
   - `score_threshold`(加 floor)→ 睇 precision 升幾多、recall 跌幾多
   - `top_k`(對 enumeration query 調高)→ 睇 recall 升幾多
   - chunk size / overlap / parent-child → 最後先郁(要 re-embed,影響最大)
3. **揀令 recall/precision 平衡最好嗰組值**,有客觀數字支撐,而唔係「順眼啲」。

**關鍵 insight**:`top_k` 同 `score_threshold` 係一對 **recall/precision 反向旋鈕**。
- Dify:top_k=3 想加 threshold → 兩個都扭去 precision 極端 → enumeration query 直接死。
- EKP 現狀:top_k=5 但**完全冇 threshold** → 另一個極端(塞 irrelevant)。
- 理想:兩個都有、按 query 類型微調。

### Rerank Setting 點揀(commonly asked)
- **Weighted Score**(semantic/keyword slider,無 cross-encoder):快、平,適合 keyword-heavy query。
- **Rerank Model**(cross-encoder,EKP 用緊 Cohere v4.0-pro):semantic precision 高,代價 latency + API call。
- **EKP 默認用 Rerank Model 係啱嘅,唔好轉去 Weighted Score**(§13 quality 唔可 compromise)。只有 latency/成本壓力大且 query keyword-heavy 先考慮轉。

---

## 5. 市場 / 學術參考(俾 AI 助手做 research 嘅起點)

**內容 recall / 聚合(對應問題 1)**:
- Parent-Document / Auto-merging retriever(LangChain `ParentDocumentRetriever`、LlamaIndex auto-merging)— 業界標準解「chunk 太碎、答案唔完整」。
- Query routing / intent classification(LlamaIndex router;Microsoft RAG patterns docs)。
- Rerank + relevance threshold gating(EKP 而家就差呢步)。

**圖文關聯(對應問題 2,近一兩年最熱方向)**:
- **ColPali / ColQwen2(2024)** — vision-based document retrieval,multi-vector late-interaction,原生解「邊張圖 belong to 邊段」,唔靠位置鄰近 heuristic。
- Multimodal embeddings(CLIP / Cohere Embed multimodal / Voyage multimodal)做 query↔image relevance scoring。

**量化**:
- RAGAs context-precision / context-recall(已在 stack 內,優先用嚟診斷)。

---

## 6. 建議落手次序

1. **(🟢 即做)用 RAGAs 對失敗 query 跑 context recall / precision baseline** → 得到客觀數字,confirm 係 recall 定 precision 主導。**唔 trigger H1,但若 multi-day 要先有 phase plan(§10 R1)。**
2. **(🟢)修問題 3 前端計數一致**(對 mockup,守 H7)。
3. **(🟢)加 rerank score threshold + neighbour-image gating**,eval-driven 調值。
4. **(🟡)若 1~3 之後 enumeration query 仍唔完整 → STOP and ask:開 parent-document retrieval / query routing 嘅 ADR**(H1)。

---

## 7. 參考 — 關鍵 code 位置(俾 AI 助手導航)

| 範圍 | 檔案:行 |
|---|---|
| Hybrid retrieval + overfetch | `backend/retrieval/retrieval_engine.py:94-192`、`backend/retrieval/hybrid.py:210-296` |
| RRF fusion(query expansion) | `backend/retrieval/result_fusion.py:82-181` |
| Low-value image post-filter | `backend/retrieval/hybrid.py:66-97`(`image_weight`) |
| Cohere rerank(**無 threshold**) | `backend/retrieval/reranker/cohere.py:84-130` |
| CRAG grade / threshold 0.70 | `backend/generation/crag.py:176-209, 265-430` |
| Synthesis + citation 抽取 | `backend/generation/synthesizer.py:52-59, 119-164` |
| Citation enrichment(圖 parse) | `backend/generation/citation_enrichment.py:26-103` |
| Neighbour image attach(±3) | `backend/generation/citation_image_neighbors.py:41-132` |
| Image proxy rewrite | `backend/api/routes/query.py:44-62, 252-327` |
| Chat 前端 inline figure | `frontend/app/(app)/chat/page.tsx:1228-1245`(InlineImageCard) |
| Referenced screenshots strip | `frontend/app/(app)/chat/page.tsx:1747-1889`(ImageGallery,line 1797 取 `[0]`) |
| Sources panel 計數 | `frontend/app/(app)/chat/page.tsx:2117-2186`(line 2126) |

---

**End of brief.**
