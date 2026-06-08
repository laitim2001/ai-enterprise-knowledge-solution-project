---
change_id: CH-010
spec_ref: ./spec.md
adr_ref: ../../../adr/0047-chapter-overview-image-lead-and-step-completeness.md
---

# CH-010 — Checklist

> 逐項 atomic;done → `→[x]`,未做標 🚧 + 理由(per CLAUDE.md sacred rule)。**Approach 1 = per-KB 完整性 config。Code/config GATED on ADR-0047 Accept(H1)。**

## Pre-gate
- [x] P0 — spec(Approach 1 鎖定)+ ADR-0047 Proposed + README index
- [x] P1 — **ADR-0047 Proposed → Accepted(Chris 2026-06-08)**

## F — Apply + measure(Approach 1 config → 實證不足 → promote pin)
- [x] F1 — baseline 量化:現況 GL narrow query candidate 只 ~11-15 張 §3.1.3、**概覽唔 lead**(記 progress)
- [x] F2 — Approach 1 config live A/B(neighbour depth=1 max_aux 12→20 + parent_doc + expansion)**全部試過**
- [x] F3 — **root cause 確認**:① neighbour pile-on-lead nearest-first 食晒 cap ② `cap_images_per_answer` citation-order 餓死概覽 citation 圖(null cap 驗證 §3.1.1 keep 返圖)
- [x] F4 — **決策**:Approach 1 config 全 revert baseline;promote Approach 2 explicit pin(cap-aware)

## X — Chapter-overview pin 實作(NEW code)
- [x] X1 — `pin_chapter_overview_images`(`citation_image_neighbors.py`):主導章節偵測 + fetch §X.1 Overview 圖 + prepend lead-citation front + dedup + graceful
- [x] X2 — per-KB flag plumbing:`Settings.enable_chapter_overview_pin`(default False)+ `KbConfig` + `EffectiveConfig` + `PerQueryOverrides` + resolve + `DraftRetrievalConfig`
- [x] X3 — wire `query.py` 兩條 path(attach 後、`cap_images_per_answer` **前**)
- [x] X4 — `tests/test_ch010_chapter_overview_pin.py`(7 tests)

## V — Verify
- [ ] 🚧 V1 — `/query/stream` drive-images-1 GL narrow query **AC1**:figure 1 = §3.1.1 概覽圖(`60a8a6e9` / `cfe10a8d`)lead
- [ ] 🚧 V2 — **AC2**:候選池含該章全部相關步驟圖(§3.1.3/3.1.4/3.1.5)+ 概覽;顯示首 20 document-order,其餘入 Image Library;vs baseline 明顯增加覆蓋
- [ ] 🚧 V3 — **AC4 跨文件 30-query eval(必須)**:recall / faithfulness flat + p95 latency 增幅記錄;對照 memory `[[project_chat_demo_rag_quality_followups]]` #1
- [ ] 🚧 V4 — **AC3 + 無 regression**:無 Overview 子節 / 已 retrieve §3.1.1 query 無重複 / 無 spurious;其他 KB(per-KB null)行為不變;CH-009 OD-4 + document-order + cap 不受影響
- [ ] 🚧 V5 — chat live 驗(**用戶**):chat 問 GL,確認概覽圖 lead + 步驟圖補齊
- [x] V6 — backend pytest 47(7 新 pin + 40 既有)+ ruff 我 code 乾淨(B905 pre-existing)+ ruff format 全過 + mypy --strict 改檔 0 新 error(AC6)
- [ ] 🚧 V-restart — 重啟 backend 載新 code(無 --reload;dual-process;輪詢 /health)→ enable drive-images-1 `enable_chapter_overview_pin=true`(+ neighbour 完整性）

## Closeout
- [x] C1 — ADR-0047 Proposed → Accepted(Chris 2026-06-08;README index 同步)
- [ ] 🚧 C2 — spec status → done;progress closeout retro
- [ ] 🚧 C3 — commits 對應 Day-N(R2);ff-merge(用戶確認)
