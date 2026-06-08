---
change_id: CH-010
title: "Chapter-overview image lead — 程序類答案自動帶章節概覽/流程圖行頭"
status: draft          # draft | approved | done
adr_ref: TBD (next NNNN=0047) — H1, code GATED on user approve + ADR Accept
affects_components: [C05]   # C05 Generation (citation attach/expansion);Option A 預期 backend-only,frontend 既有 document-order 排序自動令概覽圖 lead
spec_refs:
  - architecture.md §3.6 (index schema / citation embedded_images)
  - architecture.md §3.7 (citation expansion / post-hoc neighbour materialization)
  - ADR-0034 (neighbour image attach) · BUG-027 (section-aware attach `section_path_prefix_depth`) · CH-009 / ADR-0046 (chat image relevance — decorative filter + document-order)
---

# CH-010 — Chapter-overview image lead

> **接 CH-009 衍生**:CH-009 OD-3 revert 已令 chat 圖**照 document-order 排序**(概覽 → step),但 live 診斷(2026-06-08,drive-images-1,「confirm voucher transactions」narrow query)揭一個**獨立根因**:當 query 命中嘅係某章節嘅**具體步驟**(§3.1.3/3.1.5),該章 §X.1 Overview 嘅概覽/流程圖**根本冇 attach 到任何 citation** → 無圖可排頭。用戶要求程序類答案由章節概覽流程圖(High Level Process / Business Process Flow,Word page 20)行先。
>
> **Status draft — DECISION PENDING(Option A vs B)+ code GATED on user approve + ADR Accept(H1)。本 spec 唔含 code、唔建 checklist/progress,等方案鎖定。**

## 1. Problem(2026-06-08 live 診斷)

**證據**(`/query/stream` CRAG-on,drive-images-1,「How do I process and confirm journal voucher transactions」):

| Citation | section_path | embedded_images |
|---|---|---|
| CIT 1-11 | 全部 §3.1.3 / §3.1.4 / §3.1.5(步驟) | 步驟截圖 |
| **§3.1.1 Overview**(CIT 12)| `3 GL03 > 3.1.1 Overview` | **0 張** |

對照另一條 query(「GL03 high level process overview」)當 §3.1.1 Overview chunk **有被 retrieve** 時,佢帶住:
- `60a8a6e9` **367×87** = High Level Process(GL03-1/2/3 細橫圖)
- `cfe10a8d` **1167×565** = Business Process Flow(swimlane 大流程圖)

**根因**:概覽圖**存在於 index**(attach 到 §3.1.1 Overview chunk),但:
1. narrow step query retrieve 嘅係 §3.1.3/3.1.5,§3.1.1 Overview chunk 未被 retrieve;
2. 現有 attach 機制(`attach_neighbour_images` / `citation_expansion`)即使開 `section_path_prefix_depth`,亦有 **`max_aux` cap + nearest-first ordering** —— §3.1.1 Overview chunk(chunk ~20)離命中嘅 §3.1.5 步驟 chunk(~31)太遠,個 cap 俾近距離步驟圖食晒 → 概覽圖無被帶出;
3. 前端已按 document-order 排序(§3.1.1 < §3.1.3),**所以只要可靠 attach 到概覽圖,佢就會自動 lead** —— 缺失嘅唯一一環係「reliably attach 章節概覽圖」。

**非 recall bug**:答案文字正確、步驟圖正確;純粹「概覽流程圖未被帶入候選池」。亦**非** CH-009 decorative filter(OD-4)範圍(嗰個係燈泡,已修)。

## 2. Scope — 兩個候選方案(DECISION PENDING)

> 共通目標:**當答案 citations 集中喺某章節時,確保該章 §X.1 Overview 嘅概覽/流程圖被 attach**;前端既有 document-order 排序自動令其 lead。**H4 硬邊界**:只用文字 / section 信號,**嚴禁 image embedding / multimodal**(Tier 2 禁)。

### Option A — Chapter-overview pin(推薦,backend-only,explicit)

**機制**:citation 組裝後(`attach_neighbour_images` / `expand_citations` 之後),新增一個「章節概覽 pin」步驟:
1. 偵測 citations 嘅**主導章節**(`section_path[0]`,或 `[:1]` 出現次數最多者);
2. 喺已 fetch 嘅 doc chunk list(`engine.list_chunks`,attach 階段已攞,**零額外 IO**)揾該章 **Overview chunk**(`section_path` 命中 `[chapter]` 且 leaf section 名含 "Overview" / 係該章首 §X.1 子節);
3. 抽其概覽圖,**pin attach 到 lead citation**(繞過 `max_aux` nearest-first cap,但仍 dedup against 既有),令 document-order 排序把佢排第一。

**Files**:
- 新函式(pure,no IO)於 `backend/generation/citation_image_neighbors.py`(或新 `chapter_overview_pin.py`)；
- wire 入 `backend/generation/synthesizer.py` citation 組裝路徑(`expand_citations` 之後);
- settings flag gate(`chapter_overview_pin_enabled`,default **off** 待驗);
- 可選 per-KB override(對齊 ADR-0040 per-KB tunable config 方向)。

**Pros**:explicit / 可預測;document-order 自動 lead;**對冇 Overview 子節嘅章節零副作用**;bypass-cap 確保概覽圖必出;**frontend 零改動**(C10 不動)。
**Cons**:新 code 較多;需「Overview section 偵測」heuristic(section 名 match);需「主導章節」規則(citations 跨章時)。

### Option B — Config 微調(現有機制 knobs)

**機制**:開 `section_path_prefix_depth=1`(`attach_neighbour_images` + `citation_expansion`)+ 改 `_find_section_neighbour_images` nearest-first ordering 令 **Overview-section 候選優先於距離** + 調大 `max_aux`。

**Files**:
- `backend/api/server.py` / settings(`citation_neighbour_section_path_prefix_depth` + `citation_expansion_section_path_prefix_depth` + `max_aux`)；
- `backend/generation/citation_image_neighbors.py` `_find_section_neighbour_images` ordering tweak(Overview-section 置頂)。

**Pros**:新 code 最少(config + 細 ordering tweak)。
**Cons**:**heuristic**;depth=1 會 pull 全章節 sibling 圖(**圖洪水** risk → `max_aux` 要調 + 需與 CH-009 OD-2 per-KB cap 互動驗證);調大 `max_aux` 影響**所有** citation / 章節;與 memory `[[project_chat_demo_rag_quality_followups]]` 完整性 tuning(`parent_doc` / `citation_expansion_max_aux=10` / `prefix_depth=1`)互動 → **必須跑跨文件 eval 確認無 regression**。

### 對比表

| 維度 | Option A (pin) | Option B (config) |
|---|---|---|
| 新 code 量 | 中(新函式 + wire)| 細(config + ordering tweak)|
| 可預測性 | 高(explicit 偵測 + pin)| 中(heuristic,受 cap/距離影響)|
| 副作用面 | 窄(只影響有 Overview 子節嘅章節 lead citation)| 闊(改全域 neighbour-attach 行為)|
| 圖洪水風險 | 低(只 pin Overview 圖)| 中-高(depth=1 全章節 sibling)|
| Frontend 改動 | 無 | 無 |
| Regression 驗證需求 | 單元 + GL live | 單元 + GL live + **跨文件 30-query eval** |
| Rollback | flag off | config 還原 |

## 3. Acceptance Criteria(draft — 待方案鎖定 finalize)

- **AC1** — GL03 narrow-step query(如「confirm voucher transactions」)→ inline figure 1 = §3.1.1 概覽/流程圖(`60a8a6e9` 367×87 或 `cfe10a8d` 1167×565),lead 步驟截圖。
- **AC2** — 冇 Overview 子節嘅章節 / 已 retrieve §3.1.1 嘅 query → 行為不變(無重複概覽圖,dedup holds;無 spurious 圖)。
- **AC3** — citations 跨多章節時主導章節規則 deterministic(無亂 pin)。
- **AC4** — **無 regression**:跨文件 30-query eval(per memory `[[project_chat_demo_rag_quality_followups]]` 既有 harness)recall / faithfulness flat;CH-009 decorative filter(OD-4)+ document-order + per-KB cap 不受影響。
- **AC5** — backend pytest(generation)+ ruff + mypy 改檔 0 新 error。
- **AC6** — pin 嘅概覽圖與 CH-009 OD-2 per-KB cap 互動明確(決定:pinned overview 是否計入 cap;建議**計入**但永遠排 cap 內最前)。

## 4. H1 / H4 / H7 flags

- **H1** ✅:改 §3.6/§3.7 citation attach / expansion documented behavior → **需新 ADR(NNNN=0047)**。code GATED on Accept。
- **H4** ✅:只用 section / 文字信號偵測 Overview chunk,**無 image embedding / multimodal**(Tier 2 禁區);ADR 明文記。
- **H7** ✅(Option A frontend 零改動):概覽圖 lead 對齊 mockup「程序由概覽行先」嘅閱讀流程(同 CH-009 OD-3 revert 方向一致);Option B 亦 frontend 零改動。

## 5. Test plan

- **單元**(pure function,no mock):
  - Option A:Overview-section 偵測(section 名 match / §X.1 首節)+ 主導章節選擇(跨章 tie-break)+ pin attach + dedup + bypass-cap + 無 Overview 章節 no-op。
  - Option B:`_find_section_neighbour_images` Overview-section 置頂 ordering + cap 行為。
- **整合 / live**:`/query/stream` drive-images-1 GL narrow query → 概覽圖 lead(AC1)。
- **跨文件 eval**(尤其 Option B):30-query harness → recall / faithfulness 無 regression(AC4)。

## 6. Risks

- **R1**:「Overview section」偵測 heuristic —— section 命名可能係 "Overview" / "Business Process Flow" 各自獨立子節 / 中文。需 robust 偵測規則(spec 鎖定方案後 finalize)。
- **R2**:主導章節 ambiguity(citations 跨章節)→ 需 deterministic tie-break(建議:出現最多 citations 嘅章;tie 取最前 document-order)。
- **R3**:概覽章可能有多張圖(High Level Process 細橫圖 367×87 + Business Process Flow 大圖 1167×565)→ 決定 pin 邊張 / 全 pin(建議全 pin,document-order 內部排序)。
- **R4**:Option B depth=1 圖洪水 + 與既有完整性 tuning 互動 → 必須跨文件 eval。
- **R5**:pin bypass-cap 與 per-KB `max_images_per_answer`(CH-009 OD-2)互動(見 AC6)。

## 7. Changelog

| Date | Change | Reason |
|---|---|---|
| 2026-06-08 | spec draft 建立 | CH-009 衍生:OD-4 修燈泡後,次序根因(章節概覽圖未 attach)獨立成 CH-010。用戶(Chris)揀「先寫 spec 詳細評估」兩方案 tradeoff,讀完再決定 Option A/B + 是否寫 ADR。**DECISION PENDING — 無 code** |
