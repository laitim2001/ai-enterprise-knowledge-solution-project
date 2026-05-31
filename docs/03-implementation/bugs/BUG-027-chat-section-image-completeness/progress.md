---
bug_id: BUG-027
report_ref: ./report.md
checklist_ref: ./checklist.md
status: fix-verified-pending-enablement-decision
---

# BUG-027 — Progress

## Day 1 — 2026-05-31

### Triage
- W42 follow-up:user live-UI test `what is the Integration scenarios ? also how many ?` → 文字列全 5 scenario 但只 2 張圖(缺 §8.3/8.4/8.5)。
- 區分:**非 BUG-026**(那是 dedup 重複);本 bug 是 completeness 不足。

### Diagnosis(ground-truth,無推斷)
- backend `/query/stream` payload:1 citation(chunk 44 §8 intro,parent_doc 聚合 → LLM 列全 5 scenario 但只 cite [1])attach 2 圖(§8.1/8.2)。
- code-trace `citation_image_neighbors.py`:`window=3`(44±3 只到 chunk 47=§8.2,抓不到 49/51/53)+ `max_aux=2`(line 183 一到 2 張就 return)。docstring 明說 first-cut +「section_path matching NOT implemented in this first cut, can be added later」。
- 確認 root cause = first-cut 設計限制(window±N + max_aux=2),非 bug。

### Decision
- user chat AskUserQuestion 選 **Section-aware attach**(精準、不圖洪水、符合 docstring 預留演進)。
- H1 評估:internal citation post-process 邏輯改動 + docstring 已預留 → 不觸發 H1,無新 ADR。

### Done(fix)
- `citation_image_neighbors.py`:`_find_neighbour_images` 加 `section_path_prefix_depth` dispatch + NEW `_find_section_neighbour_images`(section membership 取代 window,nearest-first cap);`attach_neighbour_images` 透傳;docstring 更新。
- `storage/settings.py`:加 `citation_neighbour_section_path_prefix_depth: int = 0`(default 0 backward compat)。
- `api/routes/query.py`:`/query` + `/query/stream` 透傳。
- `tests/test_citation_image_neighbors.py`:+8 NEW section-mode test(同 section 跨 window / cross-section 排除 / cap nearest-first / 無 section_path fallthrough / shallow→[] / dedup / e2e)。

### Verify(全綠)
- pytest **26 passed**(18 既有 window-mode 零 regression + 8 新)/ mypy citation_image_neighbors.py **0 new error**。
- Live(process env override depth=1 + max_aux=8,venv python 重啟 backend):
  - `/query/stream`:§8 citation attach **5 圖**(8.1-8.5,各帶 source_section)。
  - Playwright UI:**5 inline figures** + meta「5 with screenshots」。
  - Control `Component overview`(§4 單圖):**1 圖**,無 regression。

### Blockers
- 🚧 **Enablement 持久化待 user 決定**:目前 backend 跑 process env override(重啟丟失)。持久化選項 = `.env`(類比 memory #1 保守)或 settings.py default flip。

### Commits
| Hash | Subject |
|---|---|
| _(pending — user decision on enablement + commit)_ | fix(generation): BUG-027 section-aware neighbour-image attach |

### Effort
- Planned:1.5h(section-aware cross-layer);Actual:~1.5h;Variance:0

### Lessons
- 文字完整性 與 圖片完整性 是**兩個獨立機制**(citation_expansion vs attach_neighbour_images)— 修了一個不等於另一個跟著修。memory #1 調文字,本 bug 才補圖片。
- 全程 ground-truth driven(backend payload + code-trace + live verify + control),延續 BUG-026 圖片診斷誤判兩次後的「不信任推斷」紀律。
