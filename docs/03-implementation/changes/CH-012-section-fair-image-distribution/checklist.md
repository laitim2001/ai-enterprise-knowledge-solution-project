---
change_id: CH-012
spec_ref: ./spec.md
status: implementing     # planning | implementing | verifying | done
last_updated: 2026-06-09
---

# CH-012 — Checklist

> 逐項 atomic;done → `→[x]`,未做標 🚧 + 理由。Spec approved 2026-06-09(方向 A）。

## Setup
- [x] S1 — ADR-0049 寫 + Accepted(Chris）+ README index
- [x] S2 — spec status → approved
- [ ] S3 — branch `feat/chat-image-section-fair`(off main）

## Fix（主修）
- [ ] F1 — `_find_section_neighbour_images`(`backend/generation/citation_image_neighbors.py`):候選由「`chunk_index` 升序 truncate」改「按 sub-section key(`section_path[:section_path_prefix_depth+1]`)分組 → round-robin 跨組取圖,組內 doc order,直到 max_aux」;只一層 sub-section / 無細分 → 退回現狀 document-order(bit-identical）
- [ ] F2 — 實測決定次修:跑 /query drive-images-1,若主修已令 §3.1.1-§3.1.5 每段有圖且 survive cap → `cap_images_per_answer` **唔改**(Karpathy §1.2);若 cap 仍餓死尾段 → 加 section-fair budget(`citation_enrichment.py`）。決定記 progress

## Test（H6 — C05 image pipeline）
- [ ] T1 — `_find_section_neighbour_images` round-robin unit test:多 sub-section fixture(§a/§b/§c 各數圖),assert max_aux 內每 sub-section 有代表(非頭組塞滿）
- [ ] T2 — production-preserve regression:單層 sub-section → document-order bit-identical;depth=0 → 唔行;既有 neighbour-image test 全綠
- [ ] T3 —(若 F2 改 cap）cap section-fair test

## Verify
- [ ] V1 — pytest 相關 test 綠;ruff/format/mypy(改檔)clean
- [ ] V2 — /query drive-images-1 GL03:§3.1.1/3.1.3/**3.1.4/3.1.5** 每段 ≥1 圖(對比 baseline 全在 §3.1.1）(AC1）
- [ ] V3 — 用戶 live 驗(chat UI hard refresh + 問 GL03,確認 Approve/Reject + Post 步驟有圖 + 順序 + 文字格式仍 OK）
- [ ] V4 —(可選 AC6）BUG-037 `--kb-id drive-images-1` eval 順手量化(視 Azure key + load）

## Closeout
- [ ] C1 — spec status → done;progress retro
- [ ] C2 — commit + ff-merge(用戶確認）;platform design doc §3.3 C-2 標 done
