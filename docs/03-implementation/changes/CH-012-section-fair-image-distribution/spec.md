---
change_id: CH-012
title: "Section-fair 圖片分配 — 解決程序尾段 section 圖片餓死(Gap C C-2 完整性)"
status: approved        # proposed | approved | implementing | done
created: 2026-06-09
author: "Claude (AI)"
approver: "Chris (approved 2026-06-09 — 方向 A section-fair)"
classification: Change   # per PROCESS.md §1 — 改既有 image-selection 行為,< 3 days
affects_components: [C05]   # generation citation image pipeline
adr_trigger: ADR-0049    # extends ADR-0048 (揀圖模式) — section-fair distribution
spec_refs:
  - architecture.md §3.7   # citation expansion / image attach
  - ADR-0048               # per-image doc_order + document-span selection (CH-011)
  - ADR-0034               # neighbour-image attach
  - ADR-0047               # chapter overview pin (CH-010)
  - ADR-0040               # config scope / cap_images_per_answer
  - docs/02-architecture/per-document-config-platform-design.md §3.3 (Gap C C-2)
---

# CH-012 — Section-fair 圖片分配(Gap C C-2 完整性)

> **緣起**:用戶 2026-06-08/09 chat 三問之 Q1「完整性」—— GL03「How do I process and confirm
> journal voucher transactions?」應出 ~35 圖,實際得 ~15,且**全部集中程序頭段**。CH-011(C-1
> doc_order/排序)已 merge;本 change 係 Gap C 嘅 **C-2(完整性)**,用戶 2026-06-09 揀 **方向 A
> (section-fair 分配)**。

## 1. 問題(實測根因,2026-06-09 /query 診斷 drive-images-1）

**唔係隨機唔齊,係尾段 section 被完全餓死。** 實測 13 citations 嘅 `embedded_images`:

| Citation | chunk | section | 圖數 |
|---|---|---|---|
| **[0]** chunk 24 | §3.1.1 Overview | **20**(全部喺呢度) | 只涵蓋 §3.1.1 + §3.1.3 |
| [1]–[12] | §3.1.3 / §3.1.4 / §3.1.5 | **0** | — |

**兩重 front-loading cap 疊加**:
1. **Section-attach `max_aux=18`**(`_find_section_neighbour_images`,`citation_image_neighbors.py`):
   match `section_path[:1]`= 成個 GL03 章,候選按 **document order(chunk_index 升序)** 排,truncate
   取頭 18 → 頭 18 張係 §3.1.1+§3.1.3(細 chunk_index),**§3.1.4(Approve/Reject)+ §3.1.5(Post)
   被 max_aux 擠走**,全堆落 §3.1.1 lead citation(再加 CH-010 overview-pin)。
2. **`cap_images_per_answer=20`**(`citation_enrichment.py` L111):順序 walk,citation[0] 食晒 20
   budget → citations[1-12](先 own §3.1.4/3.1.5)全部清空。
3. Frontend `dedupeCitationImages` 嘅 decorative filter(CH-009 OD-1/OD-4)再 trim 20→**15 顯示**。

**淨結果**:用戶見到 15 張**全部係 §3.1.1-§3.1.3**;Approve/Reject(§3.1.4)+ Post(§3.1.5)**零圖**。

## 2. 目標(方向 A — section-fair 分配)

喺**唔放寬 cap**(維持圖洪水紀律)嘅前提下,令 max_images budget **公平覆蓋程序嘅每個 sub-section**,
使每個步驟(§3.1.1-§3.1.5)至少有圖,取代而家 greedy 堆晒落 lead + 文件頭段。

**Non-goal**:升 cap(方向 B/C 已 reject);per-doc cap 可調留 Gap A / P2;image embedding(H4 禁)。

## 3. 設計

### 3.1 主修 — Section-attach 改 round-robin across sub-sections

`_find_section_neighbour_images`(`backend/generation/citation_image_neighbors.py`):
- **現狀**:候選 chunk 按 `chunk_index` 升序排,逐個攞圖直到 `max_aux` → 純 document order front-load。
- **改為**:候選按**更深 sub-section key**(`section_path[:section_path_prefix_depth+1]` 或 leaf,即 §3.1.1
  / §3.1.3 / §3.1.4 / §3.1.5)分組,**round-robin** 跨 sub-section 取圖(每組內維持 document order),
  直到 `max_aux`。→ 18 張會 spread 過 §3.1.1-§3.1.5,而非頭 18 張塞滿 §3.1.1-§3.1.3。
- 無 sub-section 細分(只得一層)時 → 退回現狀 document-order(bit-identical)。
- Dedup(checksum)+ max_aux truncate 不變。

### 3.2 次修 — `cap_images_per_answer` section-fair budget(若 3.1 未足)

`cap_images_per_answer`(`backend/generation/citation_enrichment.py`):
- **現狀**:greedy in-order,citation[0] 食晒 budget。
- **候選改法**:把跨 citation 嘅圖按 **image `source_section`** 分組,budget round-robin 分配跨 section
  (每 section 內 doc_order;dedup-aware,distinct 計數),保證每 section 有配額。
- **判斷**:若 3.1 已令 lead citation 嘅 18 張 spread 晒 §3.1.1-§3.1.5,則 cap=20 順 trim 已足
  (圖已 section-fair);3.2 視 3.1 實測效果**可能唔需要**(Karpathy §1.2 唔做投機改動)。spec 先標
  3.2 為 conditional,實作時用 /query 數據決定要唔要。

### 3.3 Production-preserve

- `max_images=None`(冇 per-KB cap 嘅 KB)→ `cap_images_per_answer` 仍 early-return 不變。
- 單一 sub-section query(冇跨 section 候選）→ round-robin 退化 = document order,行為不變。
- `section_path_prefix_depth=0`(section-attach off)→ 唔行 `_find_section_neighbour_images`,不變。

## 4. Acceptance Criteria

- **AC1**:GL03「process and confirm journal voucher」query,§3.1.1 / §3.1.3 / §3.1.4 / §3.1.5
  **每個有圖 ≥1**(尾段 Approve/Reject + Post 唔再零圖);總顯示圖數仍 ≤ cap(decorative filter 後)。
- **AC2**:Production-preserve — `max_images=None` KB + 單 sub-section query + depth=0 行為 bit-identical
  (既有 test 全綠)。
- **AC3**:無 H1 8-view image-display **layout** 改動(純 backend 選圖分配;frontend 顯示/排序不變,
  仍靠 CH-011 doc_order sort)。
- **AC4**:H4 — 分配信號限 `section_path` / `doc_order` / `source_section` 文字信號,**無 image embedding**。
- **AC5**:Test(H6 — C05 image pipeline):round-robin 跨 sub-section unit test + production-preserve
  regression + GL03-like fixture(多 sub-section,verify 尾段有圖)。
- **AC6**(可選):/eval 或 /query 實測 drive-images-1 確認 §3.1.4/3.1.5 有圖(用 BUG-037 解鎖嘅
  `--kb-id`;視 Azure key + machine load）。

## 5. Scope(檔案)

| 檔案 | 改動 | Component |
|---|---|---|
| `backend/generation/citation_image_neighbors.py` | `_find_section_neighbour_images` round-robin across sub-sections | C05 |
| `backend/generation/citation_enrichment.py` | `cap_images_per_answer` section-fair(**conditional** per §3.2) | C05 |
| `backend/tests/test_*` | round-robin + production-preserve + GL03 fixture | C06/test |
| `docs/adr/0049-*.md` | ADR section-fair distribution(extends ADR-0048) | doc |

**唔掂**:frontend(顯示/排序不變)；schema(無 field 加)；ingestion / index(無 re-index)。

## 6. ADR Trigger(H1）

改 image-selection 分配演意(影響所有設 `max_images_per_answer` 嘅 KB)= ADR-0048「揀圖模式」延伸 →
**ADR-0049**(approve spec 後寫）。**非** re-index、**非** schema、**非** vendor、**非** 8-view layout
redesign(顯示層不變）。

## 7. Changelog

| Date | Change | Reason |
|---|---|---|
| 2026-06-09 | Initial spec(方向 A，pending Chris approve） | 用戶揀 section-fair；實測根因 = 尾段 section 餓死 |
