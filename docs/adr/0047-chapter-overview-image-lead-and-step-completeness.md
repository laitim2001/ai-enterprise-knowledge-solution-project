# ADR-0047: Chapter-overview image lead + step-image completeness via per-KB completeness config

**Date**: 2026-06-08
**Status**: Proposed
**Approver**: Chris(pending)

## Context

CH-009(ADR-0046)修咗 chat 圖片兩件事:OD-3 revert → 圖照 document-order 排;OD-4 → 隔走裝飾燈泡 icon。但 live 診斷(2026-06-08,drive-images-1,「process and confirm journal voucher transactions」)揭**兩個並存、未解嘅問題**,用戶明確要求「**做到足**」一齊解:

1. **章節概覽/流程圖冇 lead**:用戶期望程序類答案由章節 §X.1 Overview 概覽圖(GL03 `60a8a6e9` 367×87 High Level Process + `cfe10a8d` 1167×565 Business Process Flow,Word page 20)行先,但呢條 query 嘅 figure 全部係 §3.1.3 步驟圖。
2. **步驟圖唔齊**:同章節其他 §3.1.x 步驟圖缺失。

**根因(drive-images-1 per-KB config API 實測)**:所有完整性 knobs = `null`(fallback 全域 default = 關 / 最小):
- `enable_citation_neighbour_images / citation_neighbour_section_path_prefix_depth(0)/ citation_neighbour_max_aux_images(2)`
- `enable_parent_doc_retrieval(False)`
- `enable_citation_post_hoc_expansion / citation_expansion_section_path_prefix_depth(0)/ citation_expansion_max_aux(2)`
- `default_rerank_k = 5`(只 5 個 chunk 做 primary citation)、`max_images_per_answer = 20`(顯示 cap)

即:只有 5 個 reranked chunk 入 citation,neighbour-attach ±3 window + max_aux=2 帶唔到遠離嘅 §3.1.1 概覽 + 其他 §3.1.x 步驟圖 → **圖片候選池本身唔齊**(非 recall 章節錯、非 CH-009 decorative、非 cap 截斷 — cap=20 未滿)。

**關鍵 insight**:概覽圖**存在於 index**(attach 到 §3.1.1 chunk),只係冇被帶入候選池。一旦帶入,前端既有 document-order 排序(§3.1.1 < §3.1.3)**自動**令其 lead。所以「補齊步驟圖」嘅機制(section-aware 同章節 attach)**順帶**解「概覽 lead」—— 一套機制解兩 goal。

呢啲 knobs 全部係 **per-KB tunable(ADR-0040)**,而且 memory `[[project_chat_demo_rag_quality_followups]]` #1 記錄過一套完整性組合已跑**跨文件 30-query eval PASS**(只係 default flip 待決)。改 §3.6/§3.7 attach / expansion documented behavior(即使 per-KB config)→ 觸 **H1**。

## Decision

採 **Approach 1 — Per-KB 完整性 config**(用戶 2026-06-08 AskUserQuestion 揀;Approach 2 明確 pin 留作日後 cap 收窄時 robustness 補強,本期不做):

為 **drive-images-1**(per-KB,ADR-0040,**runtime config,零 re-index**)開啟完整性 config:

**Core(圖片完整性 + 概覽 lead — 主要 lever)**:
- `enable_citation_neighbour_images = true`
- `citation_neighbour_section_path_prefix_depth = 1`(同章節 attach,繞 chunk-distance window)
- `citation_neighbour_max_aux_images` 調大(**起點 12,verify 時按實際章節圖數 + 跨文件 eval 校**;bounded by display cap 20)

**Complementary(文字 / citation 完整性 — memory 已驗證組合,verify 時確認是否需要)**:
- `enable_parent_doc_retrieval = true`
- `enable_citation_post_hoc_expansion = true` + `citation_expansion_section_path_prefix_depth = 1` + `citation_expansion_max_aux = 10`

效果:同章節全部 §3.1.x 圖(含 §3.1.1 概覽)入候選池 → 前端 dedup + document-order + cap=20 → 概覽圖 lead + 步驟圖按文件次序補齊,超 20 入 Image Library。

**H4 硬邊界**:全程只用 section / 文字信號;**嚴禁 image embedding / 純圖片 multimodal 檢索**(Tier 2 禁)。
**範圍邊界**:只改 drive-images-1 per-KB(隔離、可逆);**不**順手 flip 全域 default(屬另一決定);**不**改 `default_rerank_k`(section-aware 同章節 attach 已覆蓋,rerank_k 改動屬另一 retrieval 決定)。

## Alternatives Considered

- **Approach 2(Approach 1 + 明確章節概覽 pin)**:加新 code 保證概覽 lead(即使 cap 收窄)。Reject 本期 — cap=20 充裕,document-order 已足夠令概覽 lead;pin 屬 robustness 補強,Karpathy §1.2 不提前 over-engineer。日後 cap 收窄 / eval 揭概覽仍被埋 → 再 promote。
- **全域 default flip 完整性 knobs**:memory eval 背書但影響所有 KB。Reject 本期 — per-KB 隔離先,全域 flip 屬獨立 stakeholder 決定。
- **調大 `default_rerank_k`(5 → 更多)**:更多 primary citation。Reject — section-aware 同章節 attach 已覆蓋完整性;改 rerank_k 影響 retrieval 核心 + latency,屬另一 ADR scope。
- **Image embedding / multimodal 揀圖**:技術上可按圖內容排,但 = Tier 2(H4 禁)+ 需新 vendor(H2)。Reject。
- **Frontend 改動**:無需要 — document-order 排序既有,純 backend config 達標(H7 frontend 零改動)。

## Consequences

- **Positive**:章節概覽/流程圖 lead + 同章節步驟圖補齊,符合手冊「概覽 → 步驟」閱讀流程;用現成已驗證機制,**零 / 極少新 code**、runtime config、零 re-index;per-KB 隔離可逆;frontend 零改動。
- **Negative**:depth=1 + 大 max_aux 有**圖洪水**傾向(靠 cap=20 bound + 必須跨文件 30-query eval 防 regression);更多 `list_chunks` fetch + 更多圖序列化 → p95 latency 升(eval 量化);`max_aux` 值要 live 校。
- **Neutral**:其他 KB(per-KB null → inherit 全域 OFF)行為不變;CH-009 OD-4 decorative + document-order + cap 不受影響;stored 圖 / index 不變(純 query-time config)。

## References

- CH-010 spec(`docs/03-implementation/changes/CH-010-chapter-overview-image-lead/spec.md`)
- CH-009 / ADR-0046(decorative filter + document-order)· ADR-0034(neighbour image attach)· BUG-027(section-aware attach `section_path_prefix_depth`)· ADR-0040(per-KB tunable config)
- architecture.md §3.6(index / citation embedded_images)/ §3.7(citation expansion)
- memory `[[project_chat_demo_rag_quality_followups]]` #1(完整性組合跨文件 30-query eval PASS,default flip 待決)
- H1(§3.6/§3.7 attach/expansion behavior)· H4(Tier 2 multimodal 邊界)
