---
title: "Investigation — Why image-bearing chunks never reach chat citations"
status: investigated     # investigated | actioned | superseded
created: 2026-05-23
author: AI(per Chris chat directive 2026-05-23 「問題 2 另開 investigation」)
domain: [C01 chunker, C04 retrieval, C05 generation citations]
related:
  - bugs/BUG-009-azurite-blob-upload-403/         # upload pipeline closure
  - bugs/BUG-010-screenshot-counter-and-serving/  # counter + private-blob proxy
  - bugs/BUG-011-kb-images-tab-no-thumbnails/     # frontend ImageCard render
spec_refs:
  - architecture.md §3.3 chunking philosophy
  - architecture.md §3.5 layout-aware chunker
  - architecture.md §3.6 hybrid retrieval + low_value filter
  - ingestion/chunker/layout_aware.py:11-12,165-166,236,271-279
---

# Investigation — Why image-bearing chunks never reach chat citations

> **Memo type**:standalone investigation(per W11 D2 「drive corpus scope clarification」precedent;**not** a Change spec / Bug-fix report — outcome 未定,可能 land 為 CH / ADR / Tier 2 defer,等用戶決定 next step)。
>
> **Scope**:診斷為何 chat 答案明明引用對 doc + 對 section,卻從未 citation 帶圖 —— 即使 doc 真係有 8 張內嵌圖、`/images` endpoint 正確回 8、blob proxy 200 OK。
>
> **Out of scope**:fix。本 memo 結尾 surface 5 個 candidate direction + 推薦下一步,等用戶決定走 CH-003 / ADR / Tier 2 defer。

---

## 1. Trigger

2026-05-23 用戶報告:

> `/chat` 問同 `sample-doc-with-image-1` 入面有圖嘅 section 相關問題,**LLM 答案文字正確**,但**citation 完全唔帶圖**。

呢個係 BUG-009 / BUG-010 / BUG-011 closure cascade 之後剩低嘅最後一塊:upload + counter + proxy + frontend render 全部 wired,但 chat 嘅 citation 唔出現圖 —— 用戶要知道**係咪 bug,定係更深嘅 design issue**。

---

## 2. Empirical evidence

### 2.1 Prior session — chat citation 觀察

3 條 query 試咗,全部 cited chunk `embedded_images: 0`:

| Query | Retrieved chunks(top 8) | Cited chunks | 帶圖? |
|---|---|---|---|
| "what is the high level architecture" | (8 chunks)| `chunk-0001`(**"Contents" 目錄**)| 0 |
| section-4 specific 內容 | (8 chunks) | `chunk-0017` / `0002` / `0004` | 全 0 |
| section-4 開頭原句逐字 | `0001 / 0017 / 0020 / 0043 / 0052 / 0050 / 0116 / 0064` | (`citations:0`)| 全 0 |

最後一條 query 用 section 4 原文(`"The diagram below presents the high-level architecture..."`)逐字搜,**`chunk-0016`「4. High-level architecture」係預期應該出現嘅 chunk —— 但連 retrieved 都唔入 top-8**。

### 2.2 本 session — `/docs/{doc_id}` 結構觀察(2026-05-23)

```
GET /kb/sample-doc-with-image-1/docs/dce-integration-platform-implementation-plan
→ total_chunks: 121
   low_value_chunks: 72    ← 60% flagged low-value
   image_refs: 8           ← 8 unique screenshot sha aggregated
```

**Critical**:
- `image_refs` 由 `chunks` walk 出嚟(`documents.py:386-408`),walk 8 個 unique sha → 證明**至少一啲 chunks 嘅 `embedded_images_json` 真係 populated**。即係**「圖喺 chunk 入面」呢層 wiring work**。
- **`low_value_chunks: 72 / 121 = 60%`** —— chunker 對 `DCE Integration Platform Implementation Plan.docx` 嘅 layout 反應係**過度切碎**:小於 100-token floor 嘅 chunk 比例非常高。

### 2.3 Chunk-to-image association 機制(per `layout_aware.py`)

```python
# Line 11-12 — module docstring:
# 4. Embedded image positions: associate by doc_order — each image attached to
#    the chunk whose section spans its doc_order.

# Line 165-166 — event sequencing:
for img in parser_result.embedded_images:
    events.append((img.doc_order, "image", img.doc_order))

# Line 236 — chunk emit:
embedded_image_positions=list(acc.image_positions),
```

即係:**圖唔係獨立 chunk,而係 attach 落 「`doc_order` 範圍包含圖嘅嗰個 text chunk」**。所以「有圖嘅 chunk」 = 「正文 + 圖(可能仲有 figure caption)」嘅混合 chunk。

### 2.4 Low-value 過濾規則(per `layout_aware.py:271-279`)

```python
def _is_low_value(self, title: str, body: str, token_count: int) -> bool:
    if token_count < self.low_value_floor:      # default 100
        return True
    for pat in _TOC_PATTERNS:
        if pat.match(title) or pat.match(body):
            return True
    ...
```

`token_count < 100` 嘅 chunk **無條件 low_value**。一個典型「圖 + figure caption」chunk(例:「圖 4-1: System architecture」+ 一兩段描述)token 數可能就喺 100 邊緣;chunker 嘅 layout-aware 切割越 aggressive,圖被切落獨立 short chunk 嘅機率越高。

---

## 3. Root cause — 兩條 hypothesis 並列

### H1(最強懷疑):**Image-bearing chunks 被 `low_value_flag` filter 掃走,從未進入 retrieval candidate pool**

證據:
- 121 chunks 入面 **72 個 low_value flagged**(60%)—— chunker stress signal 強烈
- 8 張圖 attach 嚟嘅 chunks 唔知具體 chunk_index(本 endpoint schema 冇暴露 per-image chunk mapping),但**機率分佈上**,有圖嘅 chunk 容易因「圖 + 短 caption」 → token < 100 → low_value
- 架構 §3.6 + retrieval engine 對 `low_value=true` chunk 嘅處理:**通常喺 retrieval 時 filter 或 down-weight** —— 結果係即使該 chunk 帶圖、攞到正文 query 都唔會 surface
- chat 引用嘅 `chunk-0001`「Contents 目錄」係 high token count、TOC pattern 匹配 query 詞彙(目錄列住所有 section 名),自然贏

### H2(輔助):**Image-bearing chunks 即使唔 low_value,文字密度仍 weaker 過 TOC / 純文 chunk**

證據:
- query「what is the high level architecture」直接撞中 chunk-0001 目錄(`Contents`)入面嘅文字「4. High-level architecture」,vocabulary-overlap 贏到正文 chunk
- 即使 `chunk-0016`(section 4 標題 + 開頭)有「architecture」一字,但 token 密度同 keyword density 低過目錄(目錄一行就 condensed 一個 section 標題)
- embedding similarity 對短文本 bias 較大,目錄通常嬴

兩條 hypothesis 並非互斥 — **H1 解釋「為何永遠唔出現」,H2 解釋「即使 H1 close 都未必嬴」**。

---

## 4. Why this is NOT a quick bug fix

呢個唔係 BUG-009/010/011 嗰種**確定鏈條一條接通**嘅 bug —— 而係**retrieval relevance + chunking 設計交叉**嘅問題:

| 屬性 | BUG-009/010/011 | Problem 2 |
|---|---|---|
| Symptom 重現? | 100% deterministic | 100% deterministic |
| Root cause locus | 明確嘅單一 module / 一行 code | retrieval 排序 + chunker 切割 + low_value heuristic 交叉 |
| Fix 範疇 | minimal,< 50 LOC | varies 5 LOC(D1)to multi-day chunker re-think(D3) |
| H1 / H2 / H7 trigger? | 全部 No | **D3 / D4 可能 triggers H1** — chunker 屬 §3.5 spec component |

→ 開 BUG 唔啱;適合 standalone investigation → 用戶決定走 Change(D1)/ ADR(D3-D4)/ Tier 2 defer(D5)。

---

## 5. Candidate directions(5 options)

排序由「最少改動 + 最快得結果」到「最 architectural」:

### D1 — Citation post-processing:被 cite 嘅 chunk → 找鄰近 ±N doc_order 內有圖嘅 chunk → 加入 citation images

- **Where**:`backend/generation/citation_enrichment.py`(或 `query.py` `_proxy_citation_images` 嘅旁邊 helper)
- **Logic**:當 LLM 答案 cite `chunk-0017`(section 4 正文),搜 `chunk-0014` 到 `chunk-0019`(`section_path` 相同 OR doc_order 鄰近),嗰幾個如果有 `embedded_images_json`,就**附帶**喺 citation 入面
- **Pros**:**0 chunker change** + **0 retrieval change** + 完全 backward-compat;符合「答案引用呢個 section,就應該見到呢個 section 嘅圖」嘅產品本意
- **Cons**:係 heuristic,可能引入唔相關嘅圖(eg. 一張 dedup-跨 section 嘅 logo);需要 cap(`max_aux_images_per_citation` ≤ 2);係「補救」唔係「真修」
- **Classification**:Change(CH-003 candidate)— Tier 1 scope,< 3 days,not architectural
- **Risk**:Low

### D2 — Retrieval-time low_value soft-relaxation when chunk has `embedded_images_json` non-empty

- **Where**:`backend/retrieval/` HybridSearcher pre-filter
- **Logic**:`low_value=true` BUT `embedded_images_json` non-empty → **唔 hard-filter,而係 boost score 一啲**(eg. 保留但乘以 0.7);保留 vanilla low_value filter 嘅 noise rejection 同時 reclaim 圖 chunks
- **Pros**:Tier 1 scope;對「圖 chunk 被 low_value 掃走」H1 嘅直接 fix;改動 self-contained 喺 retrieval module
- **Cons**:涉及 retrieval ranking change → 要重新 eval(RAGAs 4 metric)確保 Faithfulness 唔退步;若 H2 主導,呢個 fix 仍未夠
- **Classification**:Change(CH-004 candidate)or 邊緣 H1(retrieval policy = §3.6 architectural)— 要看具體 implementation 是否觸動 spec interface
- **Risk**:Medium — eval regression risk;need W4 reranker shootout-style sanity

### D3 — Chunker change:adjust low_value floor / merge adjacent short chunks to give image-bearing chunks richer text

- **Where**:`backend/ingestion/chunker/layout_aware.py:271-279` `_is_low_value` + `:172-200` chunk accumulator
- **Logic**:lower `low_value_floor` from 100 → 60(現存 60% chunks 被 flagged 嘅 stress signal 證明 100 太 aggressive)OR adjacent-short-chunk merge before emit
- **Pros**:**修返 chunker 本身**(原 spec design 嘅 100-token floor 對 `sample-doc-with-image-1` 過 aggressive 已係 H1-relevant 觀察);non-image content 都受惠
- **Cons**:**Touches §3.3 chunking philosophy + §3.5 layout-aware chunker** → **H1 trigger** → 要 ADR;改 chunker 要 re-ingest 所有 KB 證明 Gate 1 R@5 唔退;eval set v0 / v1 都要 re-run
- **Classification**:**ADR-required**(non-trivial chunker design change)
- **Risk**:High — touches Gate 1 baseline

### D4 — Query expansion / RAG-fusion(多 query 變體 + 合併)

- **Where**:`backend/pipeline/query_pipeline.py` 加 query reformulator
- **Logic**:user query → 2-3 reformulations(eg.「architecture」→「architecture diagram」「system layout」「component overview」)→ 各自 retrieve → fuse → 提升 hit rate 嘅 surface 多樣性
- **Pros**:不單修圖問題,亦改善 general retrieval recall
- **Cons**:**Touches §3.7 / §4.5 query orchestration** → H1 trigger → ADR;cost 3-4× embed calls per query;latency 上升;需要 W4 shootout-style eval
- **Classification**:ADR-required
- **Risk**:High

### D5 — Defer Tier 2:pure 視覺 retrieval(text query → CLIP-style image embedding match)

- **Per** `architecture.md §11`:Multi-modal retrieval(B 類純圖片搜索)= **Tier 2 explicit**
- **Trigger criteria**:Tier 2 governance review post-W12 production launch(per Q12)
- **Not** Problem 2 嘅根本治療 —— Problem 2 唔係「我用文字搵圖」,而係「文字答案應該帶 contextually-relevant 嘅圖」。所以 D5 唔係 Problem 2 嘅 solution;只係其 **upper bound** —— 若 D1-D4 都唔 work,Tier 2 multi-modal 係 ultimate fallback
- **Classification**:Tier 2 defer,W12+ governance trigger only

---

## 6. Recommendation(等用戶決定)

**Stepwise**:

1. **第一步:D1**(citation post-processing,CH-003)—— minimal 風險、最快出產品本意效果。若答案 cite section 4 而 section 4 有圖,就 attach;若 section 4 無圖,當然 attach 唔到。Acceptance:用戶手動 query 3-5 條 image-bearing section 嘅 query,citation 至少出一張對應 section 嘅圖。
2. **第二步(if D1 insufficient)**:D2(retrieval low_value soft-relaxation)—— 真正令 image chunks 進入 candidate pool。需要 eval regression gate(RAGAs 4 metric within 5pp)。
3. **第三步(if 仍 insufficient)**:D3 chunker re-tune via ADR —— 觸 §3.3/§3.5,正式 architectural decision。

**避免**:直接跳 D3 / D4 / D5 ——
- D3 / D4 vs D1 effort ratio = ~10×,需要 chunker / pipeline re-design + eval regression gate
- D5 唔解 Problem 2 嘅產品本意(citation contextual image,而非 visual search)

---

## 7. Decision needed — 用戶答邊個方向?

| Option | Action | Effort |
|---|---|---|
| **(a)** | 即開 **CH-003**(D1 citation post-processing)→ 寫 spec.md → 落實 |  ~1 day code + eval sanity |
| **(b)** | 直接跳 **D2**(retrieval low_value soft-relax)寫 ADR-route Change |  ~2-3 days + eval regression run |
| **(c)** | 直接 **D3** chunker re-tune ADR |  ~3-5 days + Gate 1 R@5 re-verify |
| **(d)** | **Defer 全部** post-W16 / Tier 2 governance — 用戶 chat 引用嘅文字答案準確就已可接受 | 0 work now;Q12 governance trigger later |

呢個 memo **唔自動 promote 為 work** —— 等用戶選(a)/(b)/(c)/(d)先做下一步。

---

## 8. Out-of-band observations(非 Problem 2,順便記錄)

調查途中發現嘅 adjacent 信號,將來 W19+ rolling JIT 可能會 trigger 獨立 task:

- **`low_value_chunks: 72 / 121 = 60%`** for 一個 production-realistic docx (DCE Integration Platform Implementation Plan, 26 pages)。原 spec 100-token floor 可能對「真實 corporate doc 嘅 layout-aware split」過 aggressive。若呢個 ratio 喺 Drive corpus 全集都係 60%,Gate 1 R@5 嘅 baseline 可能有壓力(雖然 W2 Gate 1 PASS R@5=0.9722,but eval set 用嘅係 6-sample subset 可能未 surface)。**Candidate**:W19+ eval-set-v1 land 後,跑 corpus-wide low_value ratio measurement → 若 > 50% systemic → trigger §3.3 low_value heuristic tuning ADR。
- **`/docs/{doc_id}` `ImageRef` schema 冇 `chunk_indices`** —— mockup `ImageDetailModal`(`ekp-page-kb-extras.jsx:209-232`)期望「Referenced by N chunks」+ click-to-jump chunk reference list,但現有 backend `ImageRef`(`documents.py:402-408`)只有 `blob_url / alt_text / sha / width / height`,**冇 chunk_indices 反向映射**。將來 if `/docs/{doc_id}` 嘅 W21 F1 viewer 想 render 該 mockup component,要先 backend extend `ImageRef`。**Candidate**:W19+ if doc-detail viewer 要 land mockup `ImageDetailModal`,先 extend `ImageRef`(zero index change,純 backend response field add — 不觸 H1)。

---

**End of investigation memo**

> **Cross-ref next step**:用戶 chat 答(a)-(d)→ AI 對應啟動 CH-003 spec / ADR draft / governance backlog item。
