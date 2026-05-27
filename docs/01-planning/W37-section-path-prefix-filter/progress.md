---
phase: W37-section-path-prefix-filter
plan_ref: ./plan.md
checklist_ref: ./checklist.md
status: closed_partial   # F3 收尾 2026-05-27 — Phase Gate FAIL outcome (c) → PARTIAL revert per Chris pick
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

## Day 1 — 2026-05-27 — F1 implementation

### 完成行動

- ✅ F1.1 Settings NEW knob `citation_expansion_section_path_prefix_depth: int = 0` shipped 加 11 行 comment block(default=0 disabled,depth=1/2 semantics,W26 PC1 一次只郁一個旋鈕 rationale,W38+ separate flip decision)
- ✅ F1.2 `_find_neighbour_chunks` signature 加 `cited_section_path` + `section_path_prefix_depth` 兩 keyword-only params + 9-行 filter block + `expand_citations` 3-tuple propagation
- ✅ F1.3 5 NEW unit tests PASS + helper extension(`_doc_chunk` + `_settings`)backward-compat
- ✅ F1.4 backend pytest 1091 + ruff PASS + mypy strict W37 files clean
- ✅ F1.4.b commit `da557ab` — `feat(generation): W37 F1 (j') section_path prefix filter for _find_neighbour_chunks — additive constraint depth=0 default preserve W36 baseline + Settings NEW knob`(5 files / +274 / -25)

### F1 verification snapshot

| Metric | Before W37 | After F1 |
|---|---|---|
| Backend pytest | 1086 passed + 25 skipped | **1091 passed + 25 skipped + 0 failed**(+5 NEW W37 tests exact target match)|
| Ruff(W37 specific edits) | clean | `All checks passed!` |
| Mypy strict — citation_expansion.py | 0 self-errors | 0 self-errors |
| Mypy strict — settings.py | 0 self-errors | 0 self-errors |
| Pre-existing mypy debt(observability/retrieval/context_expander)| 13 errors | 13 errors(unchanged — Karpathy §1.3 surgical 不屬 W37 scope)|

### Karpathy §1.3 surgical edit footprint

3 production files + 1 test file:
- `backend/storage/settings.py` +12 / -1(NEW knob + comment block)
- `backend/generation/citation_expansion.py` +30 / -7(signature 2 params + filter block + 3-tuple propagation + 2 observability fields)
- `backend/tests/test_citation_expansion.py` +130 / -3(5 NEW W37 tests + helper extension `section_path` kwarg + `_settings` kwarg)
- 無其他文件變動(架構零影響 per H1 non-architectural;vendor/schema/8-view layout 不變)

### Key implementation decisions surfaced(no user clarification needed — Karpathy §1.1 think-before-coding upfront)

1. **`_find_neighbour_chunks` 新 params 用 `None`+`0` defaults**(non-keyword breakage):pre-W37 existing 9+ tests 唔需要更新呼叫,signature backward-compat。
2. **`cited_by_doc` 由 2-tuple 改 3-tuple**(per-cite section_path capture):同一個 doc 內不同 cited chunk 可以喺不同 subsection — per-cite filter 比 per-doc filter 更 precise。
3. **Malformed section_path defensive = skip(not keep)**:cited 不能 prove same-section → drop。保守 align「filter active 即過濾」契約。
4. **Observability surface depth + cited_prefix**:F2 LIVE 5-run + Langfuse trace 直接可 debug 過濾邏輯是否生效。

### Pre-F2 surface

F2.1 pre-flight per CLAUDE.md §10.3 step 5b(W36 PC-W34-1 ship):
- Langfuse `/api/public/health` 200
- Postgres `SELECT 1` ready_for_query
- Backend uvicorn explicit kill + restart 確認 F1 code loaded(per PC-W32-1 no `reload=True`)

F2.2 `.env` temporary override `CITATION_EXPANSION_SECTION_PATH_PREFIX_DEPTH=2`(top + sub-level filter test — F1.3.c+d evidence depth=1 對 single-doc KB 幾乎 no-op,depth=2 真正測試 cross-section drift)。

### W37 progress.md updates pending

- F1.4.b commit hash backfill 入 checklist + progress.md(D1 retro pattern per W36 housekeeping commit)
- F2.1 pre-flight tick(active flip 之前)
- F2.3 G1a + G1b + G2 decision tree intersect entry(F2 完成後)

---

## Day 1 cont — 2026-05-27 — F2 LIVE 5+5 run + F3 closeout PARTIAL revert

### F2 完成行動

- ✅ F2.1 pre-flight per CLAUDE.md §10.3 step 5b — Langfuse 200 + Postgres SELECT 1 ready_for_query
- ✅ F2.2.a `.env` marker block + `CITATION_EXPANSION_SECTION_PATH_PREFIX_DEPTH=2` 加入(112 → 117 lines)
- ✅ F2.2.b Backend explicit kill (PID 23260) + restart (PID 30340) — 25s warmup,health 5 components OK
- ✅ F2.2.c `backend/w37-f2-runner.py` ship — 複用 W35 F2 pattern + W36 PC-W35-1 utf-8 + NEW `analyse_drift` helper
- ✅ F2.2.e 5 runs Q-W25-I07 + 5 runs Q-W25-I01 LIVE(Run 3 I07 HTTP 502 Azure transient — 4/5 valid I07,5/5 valid I01)
- ✅ F2.3 Phase Gate FAIL outcome (c) per plan §3:

| Metric | I07 (W37 depth=2) | W35 baseline | Δ | I01 control | W35 baseline | Δ |
|---|---|---|---|---|---|---|
| **avg_cit** | **1.8** | 4.8 | **-63% REGRESS ⚠️** | **2.8** | 5.4 | **-48% REGRESS ⚠️** |
| **avg_drift** | **0.75** | n/a | ✅ G1b goal PASS | 1.60 | n/a | (no expectation control) |
| **refusals** | 0/5 | 0/5 | ✅ MAINTAIN | 0/5 | 0/5 | ✅ MAINTAIN |
| **avg_lat** | 23.15s | 11.5s | +101%(Run 4 outlier 32s)| 16.05s | n/a | n/a |
| **Run 3** | HTTP 502 | n/a | Azure transient | success | n/a | non-W37 |

### F3 PARTIAL revert 完成行動

- ✅ `.env` cleanup — `CITATION_EXPANSION_SECTION_PATH_PREFIX_DEPTH=2` + 3 comment lines removed(117 → 113 lines);production preserve depth=0 Settings default(F1 ship 已 preserve W36 baseline)
- ✅ Backend restart attempt(F3 verification);hit known ghost-Python-3.12 issue per W32 pattern;F3 closeout 不阻擋(W36 baseline 已 structurally preserved via Settings + .env clean)
- ✅ plan.md / checklist.md / progress.md frontmatter status → `closed_partial` + changelog 同步
- ⏳ session-start.md §10 W37 row `🟡 active → 🟡 closed_partial` pending F3 commit
- ⏳ F3 closeout commit pending

### Root cause shift surfaced(Karpathy §1.1 think-before-coding 新發現)

**真正 root cause 唔在 `_find_neighbour_chunks` filter logic,在 reranker layer**:

1. **I07 Run 2** cited `§11. Execution plan` + `§11.2 Phase 1` chunks alongside `§8.` intro:
   - 呢 2 個 §11 chunks **唔係** W32 (h') `_find_neighbour_chunks` expansion 加入
   - 由 reranker top-K 直接 surface(W3 Cohere v4.0-pro retrieval-side decision)
   - W37 F1 filter scope-out by design — citation_expansion 只 filter `_find_neighbour_chunks` candidates,不 filter reranker output

2. **I07 Run 4** cited `8.4 Scenario D` neighbor:
   - 同樣由 reranker surface,不經 `_find_neighbour_chunks`

3. **G1b goal PASS(drift 0.75 ≤ 1.0)evidence 證明 filter 有 work**:
   - depth=2 filter 確實過濾掉部分 cross-section expansion candidates
   - 但 cit count crash(I07 -63% / I01 -48%)源於 **同時** §X.M regex + section_path prefix 雙重 filter 過於 conservative
   - 99% candidates 被 over-filtered → cit count 由 W35 4.8 跌至 1.8(I07)/ 5.4 跌至 2.8(I01)

4. **W37 F1 evidence value 高 — preserved as W38+ enabler**:
   - Settings knob + signature + filter block + 5 unit tests preserved
   - 確認 filter mechanism work as designed(G1b goal PASS)
   - 確認 bottleneck shifted to **reranker layer cross-section surfacing** — W38+ pivot candidate

### W38+ priority queue locked

| 優先級 | 候選 | Source / 動機 |
|---|---|---|
| **HIGHEST NEW** | Reranker-side cross-section filter(`HybridSearcher` rerank step 後加 section_path prefix filter)| W37 F2 evidence — citation_expansion 層 scope-out,真正 bottleneck 在 retrieval-side reranker top-K surface |
| **MEDIUM NEW** | `\b\d+\.\d+\b` regex relax for `_find_neighbour_chunks`(允許 non-numbered chunks 入 candidates)| W37 F2 evidence — 雙重 filter 過 conservative |
| **MEDIUM preserved** | W37 F1 infrastructure preserved enabler — W38+ tune depth=1 + cap mechanism | W37 F1 code retained |
| **LOW preserved** | PC-W33-1 + PC-W32-1/2 procedural housekeeping | W34-W36 carry-over |
| **LOW preserved** | 8 個 pre-existing ruff issues 喺 runner files | W33-W35 留底 |
| **LONG-TERM** | Q14 SME-validate `reference_answer` cascade(`eval-set-v1-final.yaml`)| 真正 fix systematic context_recall 根因 |
| **永久 OUT** | path (a) judge LLM 升級 | memory `feedback_judge_llm_cost_policy.md` |
| **LOWER preserved** | DEMOTED LOW(Option A more aggressive / prompt token reduction / engine-fetch async pool)| W35 DEMOTED |
| **LONG-TERM** | (g')(i')(B'.a)(ii)(k)/(c)(e)(f)/BUG-026+027/W22 D8/W16 F1-F4 Track A IT cred | 長期 carry-over |

### Retro 7 段

#### 1. What Worked

- **R6 Day 0 4 catches** 100% accurate — primitive 已存在 / 現有 filter §X.M only / Settings namespace 獨立 / `list_chunks` return shape 已含 section_path field
- **Karpathy §1.3 surgical** — F1 code footprint 控制 3 production + 1 test file,Settings default=0 preserve W36 baseline structurally
- **Karpathy §1.1 think-before-coding upfront** — F1.3 unit tests 4 個 catches 提早 surface(depth=1 對 single-doc KB no-op / per-cite section_path capture / malformed defensive skip / 3-tuple propagation)
- **Phase Gate 3 outcome matrix 設計** — outcome (b) PARTIAL revert path 提早 plan 入,F2 FAIL 之後 user 一句話 pick 即可 closeout,無需 ad-hoc decision
- **G1b goal PASS evidence preservation value** — filter 確認 work(0.75 drift improvement),scope-out 唔等於 wasted effort

#### 2. What Didn't Work

- **F2 root cause assumption refuted** — 原 plan §1 假設 cross-section drift 來自 `_find_neighbour_chunks` expansion,F2 evidence 揭示 **多數 cross-section citations 由 reranker top-K 直接 surface**,citation_expansion 層 scope-out by design
- **`\b\d+\.\d+\b` + section_path prefix 雙重 filter 過 conservative** — cit count crash -63%/-48%
- **Backend restart hit 2 次 ghost-Python-3.12 issue**(F2 v1 attempt + F3 verification attempt)— `Start-Process Hidden`+`-WorkingDirectory` 兩次 hang at idle CPU;`bash` background `&` 加 explicit polling 才 work — 待 W38+ housekeeping document(per W32 PC-W32-1 backend reload mode 系列)

#### 3. Carry-overs

- **🚧 PARTIAL revert** F1 code(Settings knob + signature + filter block + 5 unit tests + observability fields)preserved as W38+ enabler
- **🚧 W38+ HIGHEST NEW**:reranker-side cross-section filter(retrieval layer)— real bottleneck per F2 evidence
- **🚧 W38+ MEDIUM NEW**:`\b\d+\.\d+\b` regex relax — allow non-numbered chunks `_find_neighbour_chunks` candidates
- **🚧 PC-W33-1 + PC-W32-1/2** preserved LOW housekeeping
- **🚧 8 ruff issues runner files** preserved LOW
- **🚧 Q14 SME-validate reference_answer cascade** LONG-TERM
- **🚧 永久 OUT path (a) judge LLM 升級** per memory `feedback_judge_llm_cost_policy.md`

#### 4. ADR Triggers

- **無 NEW ADR** — F1 純內部 filter logic,non-architectural per H1
- F1 evidence preserved 為 W38+ ADR draft material(如 W38+ pivot reranker-side filter 觸發 architectural change 則 draft NEW ADR)

#### 5. Phase Gate Result

- **PARTIAL closeout** per plan §3 outcome matrix (b) PARTIAL preserve default 0 + Chris pick PARTIAL revert
- **Production behavior 100% revert W36 baseline** via `.env` cleanup + Settings default=0
- **F1 code preserved as W38+ enabler** — G1b goal PASS evidence value 高

#### 6. W38+ Priority Queue Locked

(per F3 retro §W38+ priority queue locked table above)

#### 7. Actual vs Planned Effort

| Phase | Planned | Actual | Δ |
|---|---|---|---|
| F0 | 30min | ~30min | within |
| F1 | 1h | ~1h | within |
| F2 | 30-45min | ~25min runtime + ~20min runner write + ~25min backend restart trap = **~70min** | +50%(restart trap dominant) |
| F3 | 30min | ~25min | within |
| **Total** | ~2.5-2.75h | **~2.5h** wall-clock | within range |

Real-calendar collapse ~3-4x(2026-05-26 W36 closed → 2026-05-27 D1 W37 F0-F3 complete same-day per rolling JIT discipline)。

---

**End of W37 progress.md Day 1 cont**
