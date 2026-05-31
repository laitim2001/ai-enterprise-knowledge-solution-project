---
bug_id: BUG-027
title: Chat image incompleteness — multi-sub-scenario section attaches only 2 of N figures
severity: Sev3
status: fix-verified-pending-enablement-decision
opened: 2026-05-31
related:
  - BUG-026 (chat duplicate images + labels — sibling chat-image bug, different root cause)
  - ADR-0034 (citation neighbour-image attach — first-cut window±N)
  - ADR-0037 (parent-doc retrieval — drives the single §8 intro citation)
  - memory project-chat-demo-rag-quality-followups #1 (TEXT completeness — sibling, citation_expansion)
---

# BUG-027 — Chat image incompleteness (section-aware neighbour attach)

## 1. Symptom

W42 follow-up — user tested chat in live UI(KB `test-kb-20260530-1`):

> Query: `what is the Integration scenarios ? also how many Integration scenarios ?`
> Answer TEXT: lists all **5** scenarios A–E(complete ✅, all cite `[1]`)
> Images: only **2**(figure 1 = §8.1 Scenario A, figure 2 = §8.2 Scenario B)— **缺 §8.3/§8.4/§8.5(Scenario C/D/E)**

文字完整但圖片不完整。**這跟 BUG-026 不同**:BUG-026 是「同一張圖重複」(dedup);本 bug 是「應有 5 張只有 2 張」(completeness)。兩者 root cause 完全獨立。

## 2. Root Cause

Ground-truth diagnosis(backend `/query/stream` payload + code-trace,無推斷):

- 答案只有 **1 citation**(chunk 44 = §8 intro)。`parent_doc_retrieval`(ADR-0037)把整個 §8 section 聚合進該 anchor 的 context,所以 LLM 從這 1 個 parent-aggregated chunk 就列出全 5 個 scenario → 只 cite `[1]`。
- 圖片走 **`attach_neighbour_images`**(ADR-0034 / `citation_image_neighbors.py`),與文字 citation 完全不同的機制。它有兩個 first-cut 限制疊加:
  - `citation_neighbour_window = 3` → §8 intro chunk_index 44,window=3 只涵蓋 chunk 41–47 → 抓到 §8.1(45)/§8.2(47),**抓不到 §8.3(49)/§8.4(51)/§8.5(53)**。
  - `citation_neighbour_max_aux_images = 2` → `_find_neighbour_images` 一到 2 張就 return(line 183),即使 window 夠大也只 2 張。
- `citation_image_neighbors.py` docstring(原 line 15-19)明說這是 **first-cut**:「Cap at max_aux=2 to avoid 圖洪水」+「**section_path matching is NOT implemented in this first cut** ... can be added later」。

**結論**:非 bug、是 documented first-cut 設計限制。對「一個 section 有 N 個 sub-scenario 各帶圖」的 case(§8 = 5),window±N + max_aux=2 不足。**用戶 2026-05-31 chat 選 Section-aware attach 方向**。

| 面向 | 機制 | 之前狀態 |
|---|---|---|
| 文字完整性(列全 5 scenario) | `citation_expansion`(W32 h' / W37 j') | ✅ memory #1 已調好 |
| 圖片不重複 | frontend `dedupeCitationImages` | ✅ BUG-026 已修 |
| **圖片完整性(5 scenario → 5 圖)** | `attach_neighbour_images` | ❌ **本 bug** |

## 3. Fix

**Section-aware neighbour-image attach**(複用 W37 `citation_expansion_section_path_prefix_depth` 慣例,保持一致):

- `citation_image_neighbors.py`:
  - `_find_neighbour_images` 加 `section_path_prefix_depth: int = 0`;>0 且 citation 有 section_path 時 dispatch 到 NEW `_find_section_neighbour_images`。
  - `_find_section_neighbour_images`:用 `chunk.section_path[:depth] == citation.section_path[:depth]` 取代 chunk_index ±window —— **section membership 取代 window proximity**,同 section 圖不限距離;candidates 按 chunk-index 距離 nearest-first 排序後 cap max_aux;dedup against own + 彼此;citation section_path 比 depth 短 → 回 `[]`(無穩定 section key)。
  - `attach_neighbour_images` 加 `section_path_prefix_depth` 參數透傳。
- `storage/settings.py`:加 `citation_neighbour_section_path_prefix_depth: int = 0`(default 0 = window±N 行為 bit-identical;measurement-first 紀律,production flip 是獨立 user decision)。
- `api/routes/query.py`:`/query` + `/query/stream` 兩條路徑都從 settings 透傳。

**H1 邊界**:`attach_neighbour_images` 是 generation 層 citation post-process;改 neighbour 選擇邏輯(window → +section)是 docstring 明確預留的既定演進,不改 §3/§4 component / vendor / storage layout / 8-view → **不觸發 H1,無新 ADR**。default 0 保持 backward compat。

**Enablement**(啟用 section-mode 完整 5 圖需 depth>0 + 提高 max_aux):
- `CITATION_NEIGHBOUR_SECTION_PATH_PREFIX_DEPTH=1`(top-level section,如 §8.* 歸 §8)
- `CITATION_NEIGHBOUR_MAX_AUX_IMAGES=8`(window cap=2 對 5-scenario section 太低;8 = 5 + buffer)
- 🚧 **持久化方式待 user 決定**(.env override 類比 memory #1 保守 / settings.py default flip)。

## 4. Verify

- **Code**:pytest `test_citation_image_neighbors.py` **26 passed**(既有 18 window-mode 零 regression + 8 NEW section-mode);mypy `citation_image_neighbors.py` **0 new error**(7 pre-existing 全在 observability/retrieval/citation_enrichment)。
- **Live(process env override depth=1 + max_aux=8 重啟 backend via venv python)**:
  - backend `/query/stream`(`test-kb-20260530-1`,同 query):1 citation(chunk 44 §8 intro)attach **5 張圖** = §8.1/8.2/8.3/8.4/8.5(各帶自己 source_section,C-ii),之前 2 張。
  - Playwright fresh context UI:**5 inline figures**(figure 1-5 = Scenario A/B/C/D/E)+ meta「**5 with screenshots**」。
  - **Control(無 regression)**:`what is Component overview?`(§4 單圖 section)= **1 圖**(figure「4. High-level architecture」)—— section-mode 精準,單圖 section 不變多、不圖洪水。

## 5. Acceptance

- [x] §8 多 scenario query → 5 圖(API + UI)
- [x] 單圖 section query → 1 圖(無 regression)
- [x] window-mode(depth=0)行為 bit-identical(既有 18 test 全綠)
- [x] section-mode 跨 window 距離取同 section 圖 + cap + dedup + cross-section 排除(8 NEW test)
- [ ] 🚧 enablement 持久化(.env vs default flip)— 待 user 決定

## 6. Changelog

| Date | Change | Approver |
|---|---|---|
| 2026-05-31 | Triage Sev3 + ground-truth root cause(attach_neighbour_images window=3 + max_aux=2 first-cut)+ section-aware fix + code/live/UI verify | user(chat AskUserQuestion 選 Section-aware attach)|
