---
bug_id: BUG-027
report_ref: ./report.md
last_updated: 2026-05-31
---

# BUG-027 — Checklist

## Triage + Diagnosis
- [x] Triage Sev3 + 寫 report.md
- [x] Ground-truth diagnosis(backend `/query/stream` payload:1 citation + 2 圖)
- [x] Code-trace root cause(`window=3` + `max_aux=2` first-cut,docstring 預留 section-aware)
- [x] 區分 BUG-026(dedup)vs 本 bug(completeness)
- [x] user 選方向(Section-aware attach)

## Fix
- [x] `_find_neighbour_images` 加 `section_path_prefix_depth` dispatch
- [x] NEW `_find_section_neighbour_images`(section membership 取代 window + nearest-first cap + dedup + shallow→[])
- [x] `attach_neighbour_images` 透傳 `section_path_prefix_depth`
- [x] `settings.py` 加 `citation_neighbour_section_path_prefix_depth: int = 0`(default 0)
- [x] `query.py` `/query` + `/query/stream` 透傳
- [x] docstring 更新(section-aware 不再 "NOT implemented")
- [x] H1 邊界評估(internal post-process + docstring 預留 → 無 H1 trigger / 無 ADR)

## Test
- [x] 8 NEW section-mode test(同 section 跨 window / cross-section 排除 / cap nearest-first / 無 section_path fallthrough / shallow→[] / dedup / e2e)
- [x] pytest **26 passed**(18 window-mode 零 regression + 8 新)
- [x] mypy `citation_image_neighbors.py` 0 new error

## Verify
- [x] Live `/query/stream`:§8 → 5 圖(8.1-8.5)
- [x] Playwright UI:5 inline figures + meta「5 with screenshots」
- [x] Control `Component overview`(§4 單圖):1 圖,無 regression

## Closeout
- [ ] 🚧 Enablement 持久化決定(.env vs settings.py default flip)— 待 user
- [ ] 🚧 Commit code + doc — 待 user
