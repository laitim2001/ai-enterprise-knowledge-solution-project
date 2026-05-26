---
phase: W37-section-path-prefix-filter
plan_ref: ./plan.md
checklist_ref: ./checklist.md
status: active   # F0 啟動 2026-05-27
last_updated: 2026-05-27
---

# W37 — Progress Log

## Day 0 — 2026-05-27 — F0 啟動

### 啟動行動

- ✅ F0.1 建立 `docs/01-planning/W37-section-path-prefix-filter/` folder
- ✅ F0.2 R6 Day 0 recursive grep 驗證 — 4 catches surfaced
- ✅ F0.3 起草 `plan.md` 7 段
- ✅ F0.4 起草 `checklist.md` 原子化勾選項
- ✅ F0.5 起草 `progress.md` Day 0(本 entry)
- ✅ F0.6 啟動 commit `65694d6` — `docs(planning): kickoff W37-section-path-prefix-filter + R6 Day 0 4 catches surface (j') quality-of-cite refinement scope confirmed`(3 files / +513 insertions)
- ✅ F0.7 session-start.md §10 W37 row append `🟡 active 2026-05-27` + W37+ → W38+ placeholder rename(commit `6cdece6`,2 files / +4 / -3)

### R6 Day 0 4 catches 報告

#### 🚨 catch (1) — `HybridSearcher.fetch_chunks_by_section_path` 已存在(W26 F2 ADR-0037 leaf primitive)

**Evidence**:
- `backend/retrieval/hybrid.py:213-307`(`fetch_chunks_by_section_path` async method)
- `backend/tests/test_hybrid_section_path.py`(20 處 section_path,~300 行 unit tests covering empty input guards / OData filter / single-quote escaping / orderby chunk_index ASC / response shape transform / dynamic index name)
- 屬 W26 F2 parent-doc retrieval leaf primitive,**被 `parent_doc_retriever.py` 用作 section-level aggregation**

**Implication**:
- ✅ W37 (j') **唔需要** build NEW section_path filter primitive — 已有,但**用途不同**
- W37 (j') 真正 scope 係 *citation-side* `_find_neighbour_chunks` 內 additive filter(W32 (h') module enhancement)
- 兩個機制共用 `section_path` Azure Search index field 但屬不同 surface:
  - W26 parent_doc = retrieval-side aggregation(`hybrid.fetch_chunks_by_section_path` + `parent_doc_retriever.py`)
  - W37 (j') = citation-side post-rerank filter(`citation_expansion._find_neighbour_chunks` + W32 (h') engine-fetch baseline)

#### 🚨 catch (2) — `_find_neighbour_chunks` 當前 filter 只用 `chunk_title regex \b\d+\.\d+\b`

**Evidence**:
```python
# backend/generation/citation_expansion.py line 99-101
cand_title = str(chunk.get("chunk_title", "") or "")
if not _SECTION_NUMBER_PATTERN.search(cand_title):
    continue
```

**Implication**:
- W37 (j') 加 NEW additive filter 在 line 101 之後(`continue` 後)
- 與現有 §X.M regex filter 串聯(AND 關係 — 兩個 filter 都要 pass 先入 candidates list)
- 唔影響 W32 (h') existing behavior(depth=0 default = filter disabled = unchanged)

#### 🚨 catch (3) — `Settings.py:198-228` 4 處 section_path reference 屬 W26 parent-doc context

**Evidence**:
- `Settings.parent_doc_section_depth_offset` (line 202)
- Comments reference `section_path[:-1] (drop last level)` + `section_path/any() filterable` + `parent_path empty fallback`
- 全部屬 W26 F2 ADR-0037 parent-doc namespace

**Implication**:
- W37 NEW knob **必須** 用獨立命名空間 `citation_expansion_section_path_prefix_depth`(NOT `parent_doc_section_path_*` family)
- Naming convention 對齊 W32 (h') family:`citation_expansion_window` + `citation_expansion_max_aux` + NEW `citation_expansion_section_path_prefix_depth`
- 避免 conceptual confusion — parent-doc(retrieval-side aggregation)vs citation-expansion(citation-side post-rerank filter)係不同 surface

#### 🚨 catch (4) — `list_chunks` return shape 已含 section_path field

**Evidence**:
- `backend/retrieval/hybrid.py:512-514` — `list_chunks` select clause include `section_path`
- `backend/retrieval/hybrid.py:533` — return dict shape:`section_path: list(item.get("section_path") or [])`
- `backend/tests/test_citation_expansion.py:69` — `_doc_chunk` helper 已有 `"section_path": []` field(post-W20 F5.2 W17 amendment 已 ship)

**Implication**:
- ✅ W37 implementation **完全 internal** — no schema change,no `list_chunks` modification needed
- F1.3 NEW unit tests 可以直接 reuse existing `_doc_chunk` helper + add `section_path=["Doc", "§8"]` kwarg pattern
- F2 5-run runner 直接從 API response `citations[].section_path` 提取 cross-section drift metric

### W32-W36 (j') preserved 連鎖 evidence

| Phase | 來源 | 內容 |
|---|---|---|
| **W32** | progress.md line 327 + 348(原始 surface) | **NEW (j')** Section_path prefix filter for `_find_neighbour_chunks` — Run 1/3/4 mix multiple section walkthroughs(§3/§6/§7/§9 alongside §8)。Could be tighter scope if same-top-level-section preference applied。But Phase Gate already PASS so deferred。**Alternative**:tighter same-section expansion scope to avoid cross-section walkthroughs。Quality-of-cite refinement vs raw G1 throughput already maxed |
| **W33** | progress.md line 250 | **(j') NEW section_path prefix filter** preserved W34+ — quality-of-cite refinement(Run 1/3/4 cross-section §3/§6/§9 alongside §8;tighter same-section expansion via `_find_neighbour_chunks`)|
| **W34** | progress.md line 377 + 400 | **(j') NEW section_path prefix filter** preserved W35+ — quality-of-cite refinement,**independent axis from G1/G2 measurement**;`(j') section_path prefix filter` quality-of-cite refinement |
| **W35** | progress.md line 316 + 365 + 392 | **MEDIUM**(j') section_path prefix filter quality-of-cite refinement;preserved W36+ MEDIUM |
| **W36** | checklist.md line 95(§B.2)| (j') section_path prefix filter 保留 MEDIUM(W37+ kickoff candidate)|

**累積 5 個 phase preserve(W32→W36)→ W37 兌現**,符合 rolling JIT 紀律(原候選 W32 surface 後在 5 phase 之間 evaluate 優先級 + ROI tradeoff,W37 由 user 2026-05-27 explicit pick 啟動)。

### F-phase pre-implementation surface

#### F1 implementation surface(execution sequence)

```python
# Step 1: backend/storage/settings.py:275 (after citation_expansion_max_aux: int = 2)
citation_expansion_section_path_prefix_depth: int = 0
# Default 0 = filter disabled (W37 baseline preserve W36).
# depth=1 = top-level section match (e.g. all "Doc" tree).
# depth=2 = top + sub-level match (e.g. ["Doc", "§8"] cite only expands within §8).

# Step 2: backend/generation/citation_expansion.py:_find_neighbour_chunks signature
def _find_neighbour_chunks(
    cited_chunk_index: int,
    cited_doc_id: str,
    doc_chunks: list[dict[str, Any]],
    *,
    already_cited: set[str],
    window: int,
    max_aux: int,
    cited_section_path: list[str],          # W37 NEW
    section_path_prefix_depth: int,          # W37 NEW
) -> list[str]:

# Step 3: Filter block after existing §X.M regex (line 99-101 area)
if section_path_prefix_depth > 0:
    cand_section_path = chunk.get("section_path") or []
    if not isinstance(cand_section_path, list):
        continue
    if cand_section_path[:section_path_prefix_depth] != cited_section_path[:section_path_prefix_depth]:
        continue

# Step 4: expand_citations propagate (line 216-)
# cited_chunk's fields.section_path → cited_section_path
# settings.citation_expansion_section_path_prefix_depth → depth
```

#### F2 verification surface

- F2.1 pre-flight per CLAUDE.md §10.3 step 5b(W36 PC-W34-1 ship)— Langfuse 200 + Postgres SELECT 1
- F2.2 `.env` temporary override `CITATION_EXPANSION_SECTION_PATH_PREFIX_DEPTH=2`(top + sub-level filter — 真正測試 cross-section drift filter,depth=1 對 single-doc KB 幾乎 no-op)
- F2.3 G1a MAINTAIN + G1b drift ≤ 1 goal / = 0 stretch + G2 control non-regression

#### F3 closeout surface

- production preserve `depth=0` default(per Q4 measurement-experiment-fail-policy + W26 PC1「一次只郁一個旋鈕」)
- W37 F1 infrastructure preserved as W38+ enabler
- `.env` marker block removed F3 commit time(per W27/W29 pattern)

### Phase preconditions verify ✅

| Precondition | Status |
|---|---|
| W36 PC-W34-1 ship — CLAUDE.md §10.3 step 5b pre-flight protocol | ✅ commit `3f65531` |
| W36 PC-W35-1 ship — runner cp1252 fix(4 files)| ✅ commit `5520918` |
| W32 (h') `citation_expansion.py` module shipped | ✅ commit `e9bd188` |
| W32 F1.8 `expand_citations` 3-tuple return + neighbor_chunks materialize | ✅ in module |
| W17 ingestion `section_path` Azure Search filterable per architecture.md §3.6 line 364 | ✅ confirmed via hybrid.py:213-307 fetch_chunks_by_section_path primitive |
| Working tree clean(0 ahead origin/main)| ✅ W36 closed PASS pushed |
| Active phase = W37(rolling JIT)| ✅ W36 closed,W37 唯一 active |

### Cost containment policy reminder

Per `memory/feedback_judge_llm_cost_policy.md`(W36 saved 2026-05-26):
- ✅ W37 不涉及 LLM cost upgrade — F1 純 internal filter logic,F2 LIVE run 用現有 backend(synthesizer `llm_primary=gpt-5.5` + judge `llm_judge=gpt-5.4-mini` 維持 H2 lock)
- ✅ W37 不觸 path (a) judge LLM 升級(永久 OUT per memory)

---

**End of W37 progress.md Day 0**
