---
change_id: CH-010
spec_ref: ./spec.md
checklist_ref: ./checklist.md
status: in-progress     # in-progress | closed
---

# CH-010 — Progress

> Day-N entries + closeout。每 commit 對應 Day-N mention(R2)。

---

## Day 1 — 2026-06-08

### Context
接 CH-009 衍生。CH-009 OD-4 修咗裝飾燈泡(live verified `3c709d2`),但用戶 live 仍見「順序唔對 + 步驟圖唔齊」。診斷確認兩個並存問題:① 章節 §3.1.1 概覽/流程圖未 attach → 無 lead;② 同章節其他 §3.1.x 步驟圖缺失。用戶要求「做到足」一齊解。

### Done(scope + 決策)
- **根因 grounding**(live 實測):drive-images-1 per-KB 完整性 knobs **全部 `null`(關)** + `default_rerank_k=5` + `max_images_per_answer=20`。只 5 個 chunk 入 citation + neighbour-attach depth=0/max_aux=2 → 帶唔到遠離嘅概覽 + 其他步驟圖。圖**存在於 index**,只係冇入候選池。
- **Key insight**:section-aware 同章節 attach 補齊步驟圖之餘,**順帶**令概覽圖入池 → 前端 document-order 自動 lead → 一套機制解兩 goal。
- **CH-010 spec**:scope 由「概覽 lead」擴大到「概覽 lead + 步驟圖完整性」;Approach 1(per-KB 完整性 config)vs Approach 2(+明確 pin)。
- **Approach 1 鎖定**(Chris AskUserQuestion 2026-06-08):per-KB 完整性 config,reuse memory 已 eval 驗證組合,minimal/no code,runtime config 零 re-index,per-KB 隔離可逆。
- **ADR-0047 Proposed** 寫 + README index;spec status draft → approved。

### Decision(Chris 2026-06-08)
- **Approach 1**:drive-images-1 per-KB 開 `enable_citation_neighbour_images=true` + `citation_neighbour_section_path_prefix_depth=1` + `citation_neighbour_max_aux_images=12`(起點,verify 校);可選 complementary parent_doc + expansion 組合(verify 時決定)。
- **不**做:Approach 2 明確 pin(留日後 cap 收窄 robustness)/ 全域 default flip / 改 rerank_k。
- **H4**:只用 section/文字信號,無 image embedding/multimodal。

### Blockers / Carry-over
- 🚧 **P1 ADR-0047 Proposed → Accepted(用戶)** ← config/eval GATE。**未落任何 config / 未跑 eval**,等 Chris Accept。
- 🚧 V3 跨文件 30-query eval(必須,防 regression)— Accept 後做。

### Effort
- Planned ~0.5-1 day(Approach 1 config + verify + eval);Actual:_(填)_

### Commits
| Hash | Subject |
|---|---|
| `f2e44fd` | docs(change): CH-010 spec — chapter-overview image lead (decision pending) |
| `71dd768` | docs(change): CH-010 spec — expand scope to step-image completeness |
| _(本次)_ | docs(adr+change): ADR-0047 Proposed + CH-010 Approach 1 locked |

---

**End of CH-010 progress (Day 1 — Approach 1 locked;ADR-0047 Proposed;config/eval GATED on Accept)**
