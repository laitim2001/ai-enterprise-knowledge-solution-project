---
change_id: CH-010
title: "Chapter-overview image lead + step-image completeness — 程序類答案概覽圖行頭 + 補齊缺失步驟圖"
status: approved       # draft | approved | done — Approach 1 locked(Chris 2026-06-08);code/config GATED on ADR-0047 Accept
adr_ref: ../../../adr/0047-chapter-overview-image-lead-and-step-completeness.md  # Proposed — code/config GATED on Accept(H1)
affects_components: [C05, C03]   # C05 Generation (citation attach/expansion);C03 per-KB config (ADR-0040 tunable knobs — runtime,無 re-index)
spec_refs:
  - architecture.md §3.6 (index schema / citation embedded_images)
  - architecture.md §3.7 (citation expansion / post-hoc neighbour materialization)
  - ADR-0034 (neighbour image attach) · BUG-027 (section-aware attach `section_path_prefix_depth`) · ADR-0040 (per-KB tunable config) · CH-009 / ADR-0046 (decorative filter + document-order)
  - memory `[[project_chat_demo_rag_quality_followups]]` #1（完整性已 root-caused + 跨文件 30-query eval PASS，default flip 待決）
---

# CH-010 — Chapter-overview image lead + step-image completeness

> **接 CH-009 衍生 + 用戶「做到足」要求(2026-06-08)**。CH-009 OD-3 revert 已令 chat 圖照 document-order 排，OD-4 修咗裝飾燈泡。但 live 診斷揭**兩個並存問題**:① 章節概覽/流程圖(§X.1 Overview)冇 attach → 冇 lead;② 其他 §X.x 步驟圖缺失(唔齊)。用戶要求 CH-010 **同時**解兩者(概覽圖行頭 + 補齊缺失步驟圖)。
>
> **Status draft — DECISION PENDING(Approach 1 vs 2)+ code/config GATED on user approve + ADR-0047 Accept(H1)。本 spec 唔含 code、唔建 checklist/progress,等方案鎖定。**

## 1. Problem(2026-06-08 live 診斷,drive-images-1)

### 1.1 證據

`/query/stream`(CRAG-on,「process and confirm journal voucher transactions」):

| Citation | section_path | embedded_images |
|---|---|---|
| CIT 1-2 | §3.1.3 | §3.1.3 步驟圖(去重後 ~11 張)|
| CIT 3-13 | §3.1.3 / §3.1.4 / §3.1.5 | **大部分 0 張** |
| §3.1.1 Overview | (本 query 未 retrieve / 0 張)| — |

對照「GL03 overview」query(§3.1.1 有被 retrieve 時)→ 帶 `60a8a6e9` **367×87** High Level Process + `cfe10a8d` **1167×565** Business Process Flow。

### 1.2 drive-images-1 per-KB config 現況(API 實測)

**所有完整性 knobs = `null`(fallback 全域 default = 關 / 最小)**:
- `enable_parent_doc_retrieval: null`(default `False`)
- `enable_citation_neighbour_images / citation_neighbour_section_path_prefix_depth / citation_neighbour_max_aux_images: null`(default depth `0` / max_aux `2`)
- `enable_citation_post_hoc_expansion / citation_expansion_section_path_prefix_depth / citation_expansion_max_aux: null`(default depth `0` / max_aux `2`)
- `default_rerank_k: 5`(只有 5 個 reranked chunk 做 primary citation)
- `max_images_per_answer: 20`(顯示 cap)

### 1.3 根因

1. **只有 5 個 chunk 入 citation**(`rerank_k=5`)→ primary citation 池細;
2. **neighbour-attach depth=0 + max_aux=2** → 每 citation 只帶 chunk_index ±3 窗內最近 2 張新圖 → 遠離嘅 §3.1.1 概覽 + 其他 §3.1.x 步驟圖**唔入候選池**;
3. 前端已 document-order 排序 + cap=20 未滿 → **唔係 cap 截斷 / 唔係排序 bug,係候選池本身唔齊**;
4. 概覽圖**存在於 index**(attach 到 §3.1.1 chunk),只係冇被帶入 → 一旦帶入,document-order 自動令其 lead。

**非 recall 章節錯**(答案文字 + section 正確)、**非 CH-009 decorative**(燈泡已修)。係**圖片候選池完整性**。

## 2. Scope — 兩個 goal,一套機制覆蓋(DECISION PENDING)

> **Goal A(做到足)**:補齊該程序章節(如 GL03 §3.1.x)嘅**所有相關步驟圖** + 概覽圖,入候選池(顯示量受 per-KB cap=20 bound)。
> **Goal B(概覽 lead)**:章節 §X.1 Overview 概覽/流程圖**排最前**。
> **關鍵 insight**:Goal A 嘅機制(section-aware 同章節 attach)順帶解 Goal B —— 一旦概覽圖被 attach,前端既有 document-order 排序(§3.1.1 < §3.1.3)**自動**令其 lead。所以「補齊」+「lead」可一套機制達成。
> **H4 硬邊界**:全程只用 section / 文字信號,**嚴禁 image embedding / multimodal**(Tier 2 禁)。

### Approach 1 — Per-KB 完整性 config(推薦;最少新 code)

**機制**:為 drive-images-1 開啟 per-KB 完整性 knobs(ADR-0040 tunable,**runtime config,零 re-index**):
1. `enable_citation_neighbour_images=true` + `citation_neighbour_section_path_prefix_depth=1`(同章節 attach,繞 window 距離)+ `citation_neighbour_max_aux_images` 調大(建議 ≈ display cap,如 20)→ 把該章**全部** §3.1.x 圖(含 §3.1.1 概覽)attach 入 citations;
2.(可選,for 文字完整性)`enable_parent_doc_retrieval=true` + `enable_citation_post_hoc_expansion=true` + `citation_expansion_section_path_prefix_depth=1` + `citation_expansion_max_aux` 調大 —— 即 memory `[[project_chat_demo_rag_quality_followups]]` #1 跨文件 eval 已 PASS 嘅完整性組合;
3. 前端 dedup + document-order + cap=20 → 概覽圖 lead + 步驟圖按文件次序補齊,超 20 入 Image Library。

**Files**:主要 = per-KB config patch(drive-images-1)+ 可能微調 `_find_section_neighbour_images` 嘅 cap 行為;**無 / 極少新 code**。
**Pros**:用現成已驗證機制;一套解兩 goal;per-KB 隔離(唔影響其他 KB)。
**Cons**:depth=1 + 大 max_aux 有**圖洪水**傾向(靠 cap=20 bound + 必須跨文件 eval);overview-lead 靠「概覽圖入到候選池 + document-order」**間接**達成 —— 若某 query 概覽 chunk 距離極遠 + max_aux 不足,理論上仍可能漏(由 Approach 2 補強)。

### Approach 2 — Approach 1 + 明確章節概覽 pin(最 robust)

**機制**:Approach 1 **加** 一個明確「章節概覽 pin」(原 spec Option A):偵測主導章節 → 明確攞該章 §X.1 Overview 圖 → pin attach 到 lead citation(繞過 max_aux cap),**保證**概覽圖 lead,即使日後 cap 收窄 / max_aux 不足。

**Files**:Approach 1 config + 新 pure function(`chapter_overview_pin`,no IO)於 `citation_image_neighbors.py` + wire `synthesizer.py` + settings/per-KB flag gate(default off)。
**Pros**:overview-lead **保證**(唔靠距離 / cap 運氣);完整性 + lead 兩者都 explicit。
**Cons**:新 code 較多;需「Overview section 偵測」+「主導章節」heuristic。

### 對比

| 維度 | Approach 1(config 完整性)| Approach 2(config + pin)|
|---|---|---|
| 新 code | 無 / 極少 | 中(pin function + wire)|
| 補齊步驟圖(Goal A)| ✅ section-aware attach | ✅ 同 1 |
| 概覽 lead(Goal B)| 間接(document-order;靠概覽入池)| ✅ **保證**(explicit pin)|
| 圖洪水風險 | 中(cap bound + eval)| 中(同 1)|
| Regression 驗證 | **跨文件 30-query eval 必須** | 同 1 + pin 單元 test |
| Rollback | per-KB config 還原 | config 還原 + flag off |

## 3. Acceptance Criteria(draft — 待方案鎖定 finalize)

- **AC1(Goal B)** — GL03 narrow-step query → inline figure 1 = §3.1.1 概覽/流程圖(`60a8a6e9` 或 `cfe10a8d`),lead 步驟圖。
- **AC2(Goal A 補齊)** — GL03 query 候選池含該章**全部**相關步驟圖(§3.1.3/3.1.4/3.1.5)+ 概覽圖;顯示首 20(document-order),其餘入 Image Library;對比現況(只 ~11 張 §3.1.3)**明顯增加覆蓋**。
- **AC3** — 無 Overview 子節 / 已 retrieve §3.1.1 嘅 query → 無重複(dedup holds)、無 spurious。
- **AC4(無 regression — 必須)** — 跨文件 30-query eval(per memory 既有 harness)recall / faithfulness flat;p95 latency 增幅可接受(neighbour-attach 多 list_chunks fetch + 更多圖);CH-009 OD-4 decorative + document-order + cap 不受影響;其他 KB(per-KB null → 行為不變)。
- **AC5** — pin(若 Approach 2)與 cap 互動明確:pinned 概覽計入 cap 但永遠排最前。
- **AC6** — backend pytest(generation)+ ruff + mypy 改檔 0 新 error;若純 config(Approach 1)→ 加 config-resolution / attach test。

## 4. H1 / H4 / H7 flags

- **H1** ✅:開 §3.6/§3.7 attach / expansion documented behavior(即使 per-KB config)+ 確立完整性 recipe → **需 ADR-0047**。code/config GATED on Accept。
- **H4** ✅:只用 section / 文字信號;**無 image embedding / multimodal**(Tier 2 禁);ADR 明文記。
- **H7** ✅:frontend 零改動(Approach 1 純 backend config;Approach 2 pin 亦 backend);概覽 lead + 補齊對齊 mockup「程序由概覽行先 + 步驟齊全」閱讀流程。

## 5. Test plan

- **單元**:
  - Approach 1:per-KB config resolution(`effective_config`)+ `_find_section_neighbour_images` depth=1 / 大 max_aux 行為(同章節全 attach + dedup + cap)。
  - Approach 2:額外 chapter-overview pin(Overview-section 偵測 + 主導章節 tie-break + pin + dedup + bypass-cap + 無 Overview 章 no-op)。
- **整合 / live**:`/query/stream` drive-images-1 GL narrow query →(AC1)概覽 lead +(AC2)步驟圖覆蓋明顯增加。
- **跨文件 eval(必須,AC4)**:30-query harness → recall / faithfulness flat + latency 增幅記錄;對照 memory `[[project_chat_demo_rag_quality_followups]]` #1 既有結果。

## 6. Risks

- **R1 圖洪水**:depth=1 + 大 max_aux → 同章節大量圖;靠 cap=20 bound + document-order + 跨文件 eval 緩解。
- **R2 latency**:更多 list_chunks fetch + 更多圖序列化 → p95 升;eval 量化,必要時調 max_aux。
- **R3 Overview 偵測(Approach 2)**:section 命名("Overview" / "Business Process Flow" 各自子節 / 中文)→ robust 偵測規則待鎖定。
- **R4 主導章節 ambiguity(Approach 2)**:citations 跨章 → deterministic tie-break(出現最多;tie 取最前 document-order)。
- **R5 default flip vs per-KB**:本期只 drive-images-1 per-KB(隔離、可逆);全域 default flip 屬另一決定(memory 記「eval 背書但待決」),CH-010 **不**順手 flip 全域,除非用戶明示。
- **R6 cap 互動**:concept「補齊」會撞 cap=20 上限 → 超出部分入 Image Library(可接受;概覽 + 程序開頭 lead,其餘可查)。

## 7. Changelog

| Date | Change | Reason |
|---|---|---|
| 2026-06-08 | spec draft 建立(原範圍:概覽圖 lead;Option A pin vs B config)| CH-009 衍生:OD-4 修燈泡後,次序根因(章節概覽圖未 attach)獨立成 CH-010 |
| 2026-06-08 | **scope 擴大 → 概覽 lead + 步驟圖完整性(用戶「做到足」)**;重寫 §2 為 Approach 1(per-KB 完整性 config)vs 2(+ 明確 pin)| 用戶要求 CH-010 連「補齊缺失步驟圖」一齊做。grounding:drive-images-1 完整性 knobs 全 null(關)+ rerank_k=5 + cap=20 實測;memory 完整性組合已跨文件 eval PASS 未 flip。**DECISION PENDING — 無 code** |
| 2026-06-08 | **Approach 1 鎖定**(Chris AskUserQuestion)+ status draft → approved + ADR-0047 Proposed 寫 | Chris 揀 Approach 1(per-KB 完整性 config)over Approach 2(+明確 pin;留作日後 cap 收窄 robustness 補強)over 先實測。ADR-0047 Proposed + README index;**code/config GATED on ADR-0047 Accept(H1)— 仍無 code/config** |
