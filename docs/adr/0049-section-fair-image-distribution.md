# ADR-0049: Section-fair 圖片分配(neighbour-image attach 跨 sub-section round-robin)

**Date**: 2026-06-09
**Status**: Accepted
**Approver**: Chris

## Context

CH-011(ADR-0048)落地 per-image `doc_order` + document-span 揀圖後,chat 圖片**順序**已正確,但**完整性**仍未解。2026-06-09 對 drive-images-1 GL03「process and confirm journal voucher transactions」做 /query 診斷,揭示**尾段 section 圖片被完全餓死**:

- 13 citations 中,**全部 20 張圖堆喺 §3.1.1 Overview lead citation**,其餘 12 個 citation 零圖。
- 嗰 20 張只涵蓋 §3.1.1 + §3.1.3;**§3.1.4(Approve/Reject)+ §3.1.5(Post)零圖**。

根因 = 兩重 front-loading cap 疊加:
1. `_find_section_neighbour_images`(ADR-0034 + ADR-0048)match `section_path[:1]`= 成個章,候選按 `chunk_index` 升序 truncate 取頭 `max_aux=18` → 細 chunk_index(§3.1.1-§3.1.3)塞滿,大 chunk_index(§3.1.4/§3.1.5)被擠走。
2. `cap_images_per_answer=20`(ADR-0040)greedy in-order,lead citation 食晒 budget,後面清空。

用戶 2026-06-09 framing:程序問題嘅每個步驟都應有圖;尾段步驟零圖 = 完整性缺陷(Gap C C-2,per `docs/02-architecture/per-document-config-platform-design.md` §3.3)。

## Decision

**`_find_section_neighbour_images` 由「純 document-order front-load」改為「跨 sub-section round-robin」選圖**:

- 候選 chunk 按比 match-depth **更深一層嘅 sub-section key**(`section_path[:section_path_prefix_depth+1]`)分組。
- Budget(`max_aux`)以 **round-robin** 輪流跨 sub-section 取圖(每組內維持 `chunk_index` document order),而非單組 truncate。
- 效果:`max_aux=18` 嘅配額 **spread 過 §3.1.1-§3.1.5**,每個 sub-step 都有代表圖,而非頭段塞滿。
- 退化保證:只得一層(無更深 sub-section)→ 退回現狀 document-order(bit-identical);`section_path_prefix_depth=0`(attach off)→ 完全不影響。

**`cap_images_per_answer` section-fair budget** 列為 conditional 次修(CH-012 §3.2):視主修實測效果,若 attach 已令圖 section-fair 則 cap 順 trim 已足,**不做投機改動**(Karpathy §1.2)。

**信號限制(H4)**:分配只用 `section_path` / `doc_order` / `source_section` 文字信號;**絕無** image embedding / 視覺相似(= Tier 2 multi-modal retrieval,H4 禁)。

## Alternatives Considered

- **B — 純升 `max_images_per_answer` cap(~35)**:reject。圖洪水風險 + 仍 front-load(lead citation 食更多);唔解分配不公根因。用戶 2026-06-09 reject。
- **C — A + 適度升 per-doc cap**:reject(暫)。完整性最高但 payload / 圖洪水風險大;per-doc cap 屬 Gap A / P2,留後。
- **維持現狀 + 靠 frontend doc_order sort**:reject。sort 只改 render 次序,救唔到被 cap 擠走、根本未 attach 嘅尾段圖。

## Consequences

- **Positive**:程序型 query 每個步驟 section 都有代表圖(尾段唔再零圖);維持 cap=20 圖洪水紀律;無 re-index、無 schema、無 frontend、無 vendor 改動。
- **Negative**:`_find_section_neighbour_images` 由單一 truncate 變 round-robin,邏輯略增(grouping + 輪轉);多 sub-section doc 嘅同段密集圖 representation 由「頭 N 張」變「每段攤分」(設計意圖,但若某 query 真係只關注一個 sub-section,該段圖數會比舊少 —— 由 doc_order sort + cap 內仍涵蓋緩解)。
- **Neutral**:`cap_images_per_answer` 次修待實測決定;per-doc cap 可調仍是 Gap A 將來工作。

## References

- ADR-0048(per-image doc_order + document-span selection;本 ADR 延伸其「揀圖模式」)
- ADR-0034(neighbour-image attach)/ ADR-0047(chapter overview pin)/ ADR-0040(cap_images_per_answer / config scope)
- CH-012 spec:`docs/03-implementation/changes/CH-012-section-fair-image-distribution/spec.md`
- 平台藍圖:`docs/02-architecture/per-document-config-platform-design.md` §3.3(Gap C C-2)
- 診斷數據:2026-06-09 /query drive-images-1(20 圖全在 §3.1.1 lead;§3.1.4/3.1.5 零圖)
