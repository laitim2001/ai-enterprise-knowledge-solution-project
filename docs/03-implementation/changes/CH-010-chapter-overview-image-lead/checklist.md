---
change_id: CH-010
spec_ref: ./spec.md
adr_ref: ../../../adr/0047-chapter-overview-image-lead-and-step-completeness.md
---

# CH-010 — Checklist

> 逐項 atomic;done → `→[x]`,未做標 🚧 + 理由(per CLAUDE.md sacred rule)。**Approach 1 = per-KB 完整性 config。Code/config GATED on ADR-0047 Accept(H1)。**

## Pre-gate
- [x] P0 — spec(Approach 1 鎖定)+ ADR-0047 Proposed + README index
- [ ] 🚧 P1 — **ADR-0047 Proposed → Accepted(Chris)** ← config/eval GATE,等用戶

## F — Apply + measure(Approach 1;GATED on P1)
- [ ] 🚧 F1 — baseline 量化:現況 GL narrow query(「confirm voucher transactions」)candidate 圖數 + 概覽是否 lead(對照用,記 progress)
- [ ] 🚧 F2 — drive-images-1 per-KB config PATCH:`enable_citation_neighbour_images=true` + `citation_neighbour_section_path_prefix_depth=1` + `citation_neighbour_max_aux_images=12`(起點)
- [ ] 🚧 F3 — (verify 時決定是否需要)complementary combo:`enable_parent_doc_retrieval=true` + `enable_citation_post_hoc_expansion=true` + `citation_expansion_section_path_prefix_depth=1` + `citation_expansion_max_aux=10`
- [ ] 🚧 F4 — `max_aux` 校:按章節實際圖數 + 跨文件 eval 結果調 `citation_neighbour_max_aux_images`(bounded by cap 20)

## V — Verify
- [ ] 🚧 V1 — `/query/stream` drive-images-1 GL narrow query **AC1**:figure 1 = §3.1.1 概覽圖(`60a8a6e9` / `cfe10a8d`)lead
- [ ] 🚧 V2 — **AC2**:候選池含該章全部相關步驟圖(§3.1.3/3.1.4/3.1.5)+ 概覽;顯示首 20 document-order,其餘入 Image Library;vs baseline 明顯增加覆蓋
- [ ] 🚧 V3 — **AC4 跨文件 30-query eval(必須)**:recall / faithfulness flat + p95 latency 增幅記錄;對照 memory `[[project_chat_demo_rag_quality_followups]]` #1
- [ ] 🚧 V4 — **AC3 + 無 regression**:無 Overview 子節 / 已 retrieve §3.1.1 query 無重複 / 無 spurious;其他 KB(per-KB null)行為不變;CH-009 OD-4 + document-order + cap 不受影響
- [ ] 🚧 V5 — chat live 驗(**用戶**):chat 問 GL,確認概覽圖 lead + 步驟圖補齊
- [ ] 🚧 V6 — backend pytest(generation)+ ruff + mypy 改檔 0 新 error;config-resolution / attach test(AC6)

## Closeout
- [ ] 🚧 C1 — ADR-0047 Proposed → Accepted(README index 同步)
- [ ] 🚧 C2 — spec status → done;progress closeout retro
- [ ] 🚧 C3 — commits 對應 Day-N(R2);ff-merge(用戶確認)
