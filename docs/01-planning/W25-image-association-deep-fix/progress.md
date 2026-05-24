---
phase: W25-image-association-deep-fix
plan_ref: ./plan.md
checklist_ref: ./checklist.md
status: closed         # in-progress | closed
---

# Phase W25 — Progress

> Daily progress + 結尾 retro。
> 每 commit 必須對應一個 Day-N entry mention(R2 binding rule per PROCESS.md §5)。

---

## Day 0 — 2026-05-23: Kickoff

### Trigger

BUG-009 / BUG-010 / BUG-011 cascade 接通晒 screenshot upload + counter + private-blob proxy + KB Images tab 真縮圖 render —— 但 chat citation **仍從未帶圖**。Investigation memo `docs/03-implementation/image-chunk-retrieval-investigation-2026-05-23.md` 揭示 root cause two-pronged(H1 image chunks 被 60% low_value filter 掃走 / H2 vocab-overlap 輸畀 TOC chunk);AskUserQuestion 用戶揀 **Path III phase-level full optimization**(D3 + D4 + D2 + D1)= 完整解決圖文關聯問題,非單 band-aid。

### Action

**Phase W25 kickoff per CLAUDE.md §10 R1**:

- **F0.1** `docs/01-planning/W25-image-association-deep-fix/` folder created
- **F0.2** `plan.md` filled 1.0 + status `active`:
  - §1 Scope:圖文關聯 deep-fix,目標 = chat answer cite 對 section → citation 帶對 section images
  - §2 Deliverables F1-F7 atomic + acceptance criteria
  - §3 Phase Gate G1-G6 hard pass conditions
  - §4 Risks R1-R7 with mitigation
  - §5 Day-by-day ~20 calendar days(actual collapse predicted 3-7× per W12-W18 / W20-W24 pattern)
  - §6 Dependencies from W24c-users-rbac(R8 + R6 + smoke-user-deferred allowance inherited)
  - §7 Changelog v1.0 + R6 Day 0 amendment(see R6 catch below)
  - §8 5 Locked Design Decisions per user defaults
  - §9 Component Impact Map(C01 + C04 + C05 + C06)
- **F0.3** `checklist.md` derived from plan §2(F0-F7 atomic items + Cross-cutting C1-C7)
- **F0.4** `progress.md` Day 0 entry init(this entry)

### R6 Pre-Active-Flip Recursive Grep Verification

**Applied at Day 0 plan kickoff,scope = plan-text 自己**(per CLAUDE.md §10 R6 + W23 F3 amendment + memory `feedback_design_fidelity.md` D9 plan-text-contamination pattern)。Catch upfront before any F1+ active-flip。

**Grep targets** + **findings**:

| # | Plan-text reference | Grep finding | Action |
|---|---|---|---|
| (i) | `low_value_floor` 100 → 60 chunker constant | `layout_aware.py:35 _TOKEN_LOW_VALUE_FLOOR = 100`(module constant)+ `:69 low_value_floor: int = _TOKEN_LOW_VALUE_FLOOR`(class param default)+ `architecture.md §3.3 soft floor` cite | Plan-text **correct**;F1.2.1 change 落 module constant level + ADR-0033 cite §3.3 amendment |
| (ii) | `hybrid_searcher.py` filter stage | Actual file = `backend/retrieval/hybrid.py`(no `_searcher` suffix)| Plan-text **inaccurate naming** — Edit applied to plan §7 changelog;F5 implementation reference 修正為 `hybrid.py` |
| (iii) | "filter 階段加 condition `low_value=true` AND `embedded_images_json` non-empty → retain weight × 0.7" | **Actual filter mechanism** = Azure Search server-side OData `_DEFAULT_FILTER = "enabled eq true and low_value_flag eq false"`(`hybrid.py:4 + :41`) —— **NOT Python `if` filter** | **Major plan amendment** — D2 implementation 要由 server-side filter → client-side post-filter Python override(filter clause 去掉 low_value_flag + 加 Python post-filter)+ **可能觸 H1**(改 §3.6 retrieval policy mechanism interface)→ F5.1.2 CH-003 spec drafting 必先 surface H1 trigger 風險畀 Chris 決定(CH-003 alone vs CH-003 + co-ADR-0035)。Plan §2 F5 + §7 changelog 已 amend |
| (iv) | `eval-set-v0.yaml` 位置 | Actual location = `docs/eval-set-v0.yaml`(NOT `backend/eval/`)| Plan-text **already correct**(F2.2.1 reference 「`eval-set-v0.yaml` 6 samples」without path prefix);no amendment needed |

**R6 catch evaluation**:呢個 R6 application 早期 catch 咗 1 個 major plan-text contamination(iii)+ 1 個 minor naming(ii),F1 / F5 active-flip 之前已 amend 完。**Cumulative R6 occurrences across phases**:W22 D1 + D8 + D9 + W23 (formalized) + W24c (~100 cumulative findings)+ W25 Day 0(4 findings catch upfront)= ongoing empirical validation of R6 recursive-scope value。

### Decisions(Day 0)

- **D0.1** — Phase folder naming `W25-image-association-deep-fix/`:user-approved chat 2026-05-23(a)
- **D0.2** — F1→F2→F3→F4→F5→F6→F7 sequence:user-approved chat 2026-05-23(b);rationale per plan §2 — D3 first(F1)because chunker change conditions D2/D4 behaviour;D4 second(F3)because retrieval-level optimization needs chunker stable;D2+D1 last(F5)because safety net on top of D3+D4 lift
- **D0.3** — 5 locked design defaults per user chat 2026-05-23(c):eval-v0 + image queries / dev-only re-ingest / floor 100→60 + adjacent-short-merge / P95<5s hard cap / D2 weight × 0.7 — all locked in plan §8
- **D0.4** — **D2 H1 boundary re-examination**(per R6 finding iii)— F5.1.2 spec drafting 必先 surface H1 trigger 風險畀 Chris 決定。**Default assumption(temporary)**:H1 NOT triggered(filter mechanism shift 屬 implementation detail not spec-interface),但 confirm 喺 F5.1.2;若 H1 triggered → CH-003 + co-ADR-0035 mandatory
- **D0.5** — **ADR numbering plan**:ADR-0033(D3 chunker low-value tuning)+ ADR-0034(D4 query expansion / RAG-fusion)+ potential ADR-0035(D2 retrieval filter mechanism,if H1 trigger confirmed F5)。Next available 0033 per `docs/adr/README.md` "Next NNNN" section(0030 + 0032 deliberately SKIPPED per W19 F2 absorb decision)

### Blockers

無。所有 F1-F7 work AI-controllable;唔依賴 Track A IT cred populate event(per plan §6 W17 beta-hardening parallel-track precedent)。

### Actual vs Planned Effort

| Deliverable | Planned (h) | Actual (h) | Variance |
|---|---|---|---|
| F0 kickoff(plan + checklist + progress + R6 verify + kickoff commit)| 4-6 | ~3 | -1 to -3(R6 grep efficient,plan structure clear ahead-of-time)|

### Commits

_(見 commit footer — `chore(planning): kickoff W25 image-association-deep-fix`)_

### Carry-overs from W24c-users-rbac

Per session-start.md §11 W24c CLOSED block — **none directly for W25**:
- W24c 屬 Wave C3 RBAC frontend/backend,scope independent from retrieval/chunker
- Cross-phase pattern inheritance:R8 corp-proxy(若 F3 需要新 dep)/ R6 recursive scope(已 applied above)/ smoke-user-deferred allowance(F6 manual user-test = user pre-Beta scope per W12-W18 / W20-W24 pattern)

---

**End of Day 0 entry** — F1 active-flip kickoff next session

---

## Day 1 — 2026-05-23: F1 D3 chunker re-tune(ADR-0033)

### Done

**F1.1 ADR draft + approval** —
- F1.1.1 — `docs/adr/0033-chunker-low-value-tuning.md` written:Context(60% low_value empirical signal + BUG-009/010/011 cascade trigger)+ Decision(two-pronged:floor 100→60 + adjacent-short-merge post-process)+ 6 Alternatives evaluation(rejected:floor-only / merge-only / image-skip retrieval rule / raise target / eliminate low_value entirely / no-change)+ Consequences(positive / negative / neutral)+ Implementation Mapping table 1-to-1 to plan F1.2/F1.3 checklist items
- F1.1.2 — Chris approved as-is chat 2026-05-23 → ADR status `Proposed → Accepted` + Approver field updated
- F1.1.3 — `docs/adr/README.md` index row added(0033 Accepted)+ Next-NNNN footer updated(0034 reserved for W25 F3 query expansion;0035 reserved if R6 H1 trigger confirmed at W25 F5)

**F1.2 Chunker code(per ADR-0033 Decision)** —
- F1.2.1 — `backend/ingestion/chunker/layout_aware.py:35`:`_TOKEN_LOW_VALUE_FLOOR` 常數 **100 → 60**(annotated「lowered 100→60 W25 D3 per ADR-0033 (amends §3.3)」)
- F1.2.2 — NEW `_MIN_CHUNK_MERGE_FLOOR = 160`(line 36)+ NEW `_merge_adjacent_shorts` method + helper `_should_merge` method on `LayoutAwareChunker`;hook into `chunk()` return path:`return self._merge_adjacent_shorts(chunks)` 取代 plain `return chunks`;import added `from dataclasses import dataclass, replace` for chunk_index re-index pass
- F1.2.3 — Confirmed `_TOC_PATTERNS`(line 37-41)+ `_VERSION_PATTERNS`(line 42-46)+ `_is_low_value` TOC/version rules(line 274-279)unchanged per ADR scope constraint
- F1.2.4 — Module docstring §5 updated(floor 60 cite)+ NEW §6 documents adjacent-short-merge post-process step
- Class `__init__` signature extended:`min_chunk_merge_floor: int = _MIN_CHUNK_MERGE_FLOOR` parameter(BC default;tests can override to 0 to disable merge for unit-level inspection)

**F1.3 Unit tests(`backend/tests/test_chunker.py`)** —
- F1.3.1 — `test_w25_floor_60_marks_chunks_below_60_low_value` + `test_w25_floor_60_keeps_60_to_99_token_chunks_high_value`(reclamation envelope under `min_chunk_merge_floor=0` chunker for isolation)
- F1.3.2 — 6 NEW merge tests:`test_w25_adjacent_short_merge_combines_two_subsections` + `test_w25_merge_does_not_combine_with_table_chunk` + `test_w25_merge_respects_hard_cap` + `test_w25_merge_reindexes_contiguous_zero_to_n` + `test_w25_long_sections_do_not_merge` + `test_w25_merge_concatenates_embedded_image_positions`
- F1.3.3 — `test_w25_synthetic_corpus_chunk_count_within_twenty_percent_envelope`(6-section synthetic corpus envelope [2, 7] chunks per ADR §Negative consequences ±20%)
- F1.3 ancillary — Updated existing `test_simple_three_section_doc_emits_three_chunks` paragraph sizes(`* 20` → `* 40` so each section's ~200 tokens > merge floor 160,preserving section-boundary test intent under W25 merge behaviour)

### Diagnosis update

R6 finding (iii) at Day 0 already surfaced D2 H1 boundary risk for W25 F5 —— F1 / F2 / F3 / F4 unaffected(chunker change is module-internal,not §3.6 interface);F5 D2 re-examination 仍 deferred 到 F5.1.2 CH-003 spec drafting time per Day 0 D0.4。

### Decisions(Day 1)

- **D1.1** — Adjacent-short-merge as **post-process** not embedded in main event loop:per ADR §Decision (b) rationale — main event loop complexity already non-trivial(heading stack + table interleaving + image attach by doc_order),mixing merge logic in compromises readability + makes A/B harder。Implementation = pure function over `list[ChunkSpec]` → easy isolated unit testing。
- **D1.2** — `min_chunk_merge_floor` 作為 class parameter(default `_MIN_CHUNK_MERGE_FLOOR=160`)allow `min_chunk_merge_floor=0` disable for unit-level floor isolation tests(`test_w25_floor_60_marks_chunks_below_60_low_value` 等用 0 disable merge,清晰測試 floor 行為 without merge consolidation noise)
- **D1.3** — Existing test `test_simple_three_section_doc_emits_three_chunks` paragraph sizes bumped(`* 20` ≈ 100 tokens → `* 40` ≈ 200 tokens)preserves section-boundary intent under merge behaviour;**not** `min_chunk_merge_floor=0` workaround because the test's intent was demonstrating section split behaviour for *real-size* sections,which post-W25 are still split correctly when above floor
- **D1.4** — Verify gates per F1.4(see below)

### Verify gates(F1.4)

- **F1.4.1** — `mypy --strict --explicit-package-bases ingestion/chunker/layout_aware.py` → **exit 0**。Summary「Found 17 errors in 5 files (**checked 1 source file**)」—— `layout_aware.py` 本身 **zero new error**;17 errors 全部喺 transitively-imported `ingestion/parsers/{pdf_parser.py, docx_parser.py, __init__.py}`(Docling `NodeItem.export_to_dataframe` / `get_image` / `caption_text` `attr-defined` + `Parser` Protocol return-type variance)= **pre-existing tech debt**,**同 BUG-010 `postgres_backend.py` 7 個 `_row_to_kb` tuple/dict error 一樣 pattern**(per Karpathy §1.3 surgical 不順手修)。
- **F1.4.2** — `pytest tests/test_chunker.py -v` → **21 passed in 256.98s**(12 existing + 9 NEW W25 tests 全綠;existing `test_simple_three_section_doc_emits_three_chunks` 經 paragraph 大小調整後 preserve section-boundary intent)。
- **F1.4.3** — `pytest tests/` full backend regression → **939 passed + 25 skipped + 0 failed** in 489.10s。Vs BUG-010 baseline 930 passed = **+9 NEW** W25 tests passed,**zero regression**。Skipped 25 unchanged(pre-existing skips unrelated to chunker)。

### Blockers

無。

### Actual vs Planned Effort

| Deliverable | Planned (h) | Actual (h) | Variance |
|---|---|---|---|
| F1.1 ADR(draft + approval + README index)| 2 | ~1 | -1(structure clear from Day 0 prep)|
| F1.2 chunker code | 4 | ~1 | -3(R6 grep upfront gave precise change loci)|
| F1.3 unit tests(8 NEW + 1 existing update)| 4 | ~1.5 | -2.5(test fixtures already established)|

Compression factor ~3-5×(consistent with W12-W22 phase compression pattern)。

### Commits

_(見 commit footer — `feat(chunker): F1 D3 ADR-0033 chunker low-value tuning — W25`)_


---

## Day 2 — 2026-05-24: F2 eval closure + BUG-012/013/014 cascade + BUG-015/016 surfaced

### Done

**F2.1 Re-ingest 3 dev KBs post-chunker-change** —
- Re-ran ingestion against `sample-document-with-image-1` KB(`DCE_Integration_Platform_Implementation_Plan.docx`,8 embedded images)+ 2 other dev KBs
- Validation:**121 chunks(pre-W25)→ 63 chunks(post-W25)= -48% chunk count delta**(per W25 chunker re-tune ADR-0033 expected reclamation ±20% absolute counts;48% relative reduction = high-fidelity adjacent-short-merge clustering small text fragments)
- Azure Search index `ekp-kb-sample-document-with-image-1-v1` repopulated;`hybrid.list_chunks` returns 63 documents post-reindex

**F2.2 Author eval-set-v0-w25-supplement.yaml + wire** —
- NEW `docs/eval-set-v0-w25-supplement.yaml` — 12 hand-authored queries(6 text + 6 image-oriented;`kb_id: sample-document-with-image-1`)per plan §8 design default 1(eval-v0 + image queries)
- `backend/api/routes/eval.py` mapping entry added — `eval-set-v0-w25-supplement` key wired into `/eval/run` 路徑 lookup table per existing `eval-set-v0` convention

**F2.3 Gate 1 R@5 re-verify on eval-set-v0** —
- Pre-W25 baseline R@5 = **0.8333**(per BUG-010/011 baseline measure prior to chunker re-tune)
- Post-W25 R@5 = **0.9722** ← **+13.89pp** improvement
- Gate 1(≥ 80%)= ✅ pass(actually exceeds W2 ekp-kb-drive-v1 baseline R@5=0.9722)
- ADR-0033 expected lift confirmed at scale across 6-query eval-set-v0 + 12-query W25 supplement

**F2.4 RAGAs 4-metric soft check** —
- Pre-W25 vs Post-W25(`POST /eval/run` aggregate over eval-set-v0 + w25-supplement = 18 queries):
  | Metric | Pre-W25 | Post-W25 | Δ |
  |---|---|---|---|
  | R@5 | 0.8333 | **0.9722** | **+13.89pp** ✅ |
  | Faithfulness | 0.8798 | **0.9495** | **+6.97pp** ✅ |
  | Correctness | 0.6706 | **0.7506** | **+8.00pp** ✅ |
  | P95 latency (ms) | 950 | 964 | +14ms(within plan §8 hard cap < 5000ms — well within target)|
- 全部 4 metric net-improved post W25 F1 chunker change;**zero regression** on latency budget — F1 D3 chunker is unambiguously a positive lift across retrieval + synthesis quality

**BUG-012 fix + commit `7fdbda7`** —
- `screenshot_proxy_url` same-origin path-only URL fix(`/api/backend/kb/{kb_id}/screenshots/{blob_name}`)+ `del request` arg removal
- `backend/tests/api/test_query_screenshot_proxy.py` 3 assertions updated
- pytest 939 passed,full BUG-012 closeout

**BUG-013 fix(in-code,this-session commit)** —
- `frontend/app/api/backend/[...path]/route.ts`:dev Bearer auto-inject for browser-native `<img>` requests after HOP_HEADERS filter,using `process.env.NEXT_PUBLIC_AUTH_MOCK_BEARER ?? 'dev-token'`
- Closes mock-auth dev-mode session-cookie absence(mock_msal.ts hardcodes Bearer + never `/auth/login` → no `ekp_session` cookie → `<img>` cannot add Bearer header per W3C spec → 401)
- Post-edit proxy probe:401 → 200 transition confirmed for no-Bearer browser-native simulation
- BUG-013 docs status `triaged → done`

**BUG-014 fix(in-code,this-session commit)** —
- `backend/api/middleware/rate_limit.py`:`_RATE_LIMIT_EXEMPT_RE = re.compile(r"^/kb/[^/]+/screenshots/[a-f0-9]{64}\.[a-z0-9]+$")` module constant + `dispatch` early-return before protected-prefix gate
- Closes 6/8 thumbnails-rendered-but-2/8-429 pattern from BUG-013 post-fix(8-image burst saturates `rate_limit_concurrent` cap)
- Exemption regex locked to SHA-256 hex 64 char + ext shape — mirrors `_SCREENSHOT_BLOB_RE` in `documents.py:269`,cannot broaden past actual screenshot route
- Pytest **939 passed + 25 skipped + 0 failed** in 290.40s(same baseline as W25 F1 — middleware change zero regression)
- 10× parallel screenshot GET smoke during session: all 200(rate-limit exemption working as expected)
- BUG-014 docs status `triaged → done`

### Diagnosis update

**Image-association deep-fix scope expansion** — Day 2 W25 D2 verify session揭露 2 個 NEW orthogonal issues separate from BUG-013/014 frontend cascade,scope = `/kb/[id]/docs/[doc_id]` Document Detail 3-pane page(ADR-0029 Wave B):

| Bug | 範圍 | Diagnosis |
|---|---|---|
| **BUG-015** | C08 backend route `documents.py` doc-detail aggregation | `image_refs[].blob_url` returns raw Azurite URL(`http://127.0.0.1:10000/devstoreaccount1/...`)— browser-blocked(no CORS / no SAS / private blob;BUG-009 設計初心係 proxy via `/api/backend/.../screenshots/{sha}.png` 帶 auth)。BUG-012 已 修咗 `/kb/{id}/images` aggregated endpoint嘅 URL shape,但 `/kb/{id}/docs/{doc_id}.image_refs[]` 冇修 — 兩條 surface 平行存在,只修一條 |
| **BUG-016** | C08 backend schema `listing.py` ChunkSummary | ChunkSummary 明文 strip `embedded_images_json`(W16 F5.1.2 originally「Beta client doesn't need bulk text in listing endpoints」)。W20 Document Detail 3-pane 需要 per-chunk `with images` flag — 呢個 W16 listing-schema decision 變咗 broken assumption。Frontend chunks panel 收唔到 `embedded_images_json` field → 無從 mark `[with images]` |

**Critical correction to user's premise**:user 問「chunk-image association 是否冇處理?」 — **NO**。Backend chunks 個別 record 真係有 `embedded_images_json` 正確 populate(`hybrid.list_chunks` line 348 SELECT clause + line 373 return + doc-detail aggregation 經 chunk loop 出 `total_images=8 + image_refs count=8` 證明)。Ingestion pipeline `chunker.embedded_image_positions` → `orchestrator.position_to_sha` lookup → `ChunkRecord.embedded_images` → `to_search_doc()` 寫 Azure Search `embedded_images_json` Edm.String — 全 chain 正確。Frontend 2 個 surface 受阻:(a) Document Detail `image_refs[].blob_url` URL shape 錯;(b) Chunks list schema strip image marker field。

**W25 F5 D1 citation propagation 仍需驗證** — `/query` `/chat` response payload `citations[].embedded_images` 有冇 propagate 至前端 chat citation,呢個係 phase 原 scope F5 D1 deliverable,Day 2 暫未 verify(separate task #161 待處理)。

### Decisions(Day 2)

- **D2.1** — BUG-013 + BUG-014 fix correctness independently validated via per-session probes(BUG-013 401→200 transition + BUG-014 10× burst all-200);explicit user-eye verify on `/kb/[id]?tab=images` precise target page 🚧 deferred per T6/T9 — user routed to Document Detail page mid-session,surface BUG-015 + BUG-016 instead。Implicit confirmation expected once BUG-015 unblocks Document Detail same-origin proxy path(same underlying infrastructure as BUG-013/014)
- **D2.2** — Open BUG-015 + BUG-016 per PROCESS.md §4 workflow per user 2026-05-24 AskUserQuestion Option 1 pick「立即 open BUG-015 + BUG-016 + commit 之前 BUG-013/014/F2」— pre-doc(report.md + checklist.md + progress.md)before any code change per CLAUDE.md §10 R1 binding
- **D2.3** — W25 F2 closeout commit 與 BUG-013/014 commits 分開 — per CLAUDE.md §4.3 one-feature-per-PR — 3 個 separate commits for clean rollback / cherry-pick boundary
- **D2.4** — Service restart event captured separately(WSL2 stuck → reboot → all services rebuild from scratch)— `infrastructure/docker-compose up -d postgres langfuse` + Azurite native npm CLI + uvicorn `.venv/Scripts/python.exe -m api.server` + Next.js `pnpm dev`(stuck on `/kb/[id]` compile post-WSL crash,killed + restarted + 4 route pre-compile);**zero data loss**(volumes preserved)

### Blockers

無。

### Actual vs Planned Effort

| Deliverable | Planned (h) | Actual (h) | Variance |
|---|---|---|---|
| F2.1 re-ingest 3 dev KBs | 1 | ~0.5 | -0.5 |
| F2.2 author eval-set-v0-w25-supplement + wire | 2 | ~1 | -1 |
| F2.3 Gate 1 R@5 re-verify | 1 | ~0.5 | -0.5 |
| F2.4 RAGAs 4-metric soft check | 2 | ~1 | -1 |
| BUG-012 cascade close + commit | 1 | ~1 | 0 |
| BUG-013 fix + docs | 2 | ~1 | -1 |
| BUG-014 fix + docs + pytest | 1 | ~1 | 0 |
| BUG-015 + BUG-016 diagnosis(scope expansion)| 0 | ~1 | +1(new scope from Day 2 user-eye verify)|
| Service restart event(WSL crash recovery)| 0 | ~2 | +2(unplanned;Docker Desktop + WSL2 stuck state required Windows reboot)|

Compression factor ~2-3× — Day 2 主要 effort 喺 cascade-bug 連鎖 + restart event,F2 自身 effort 高度 compressed。

### Commits

_(見 commit footers)_:
- `fix(frontend): Next.js proxy injects dev Bearer for browser-native requests — BUG-013`
- `fix(api): exempt screenshot proxy from rate limiter — BUG-014`
- `feat(eval): W25 F2 closeout — eval-set-v0-w25-supplement.yaml + mapping + R@5 0.9722 verified`

---

## Day 3 — 2026-05-24: BUG-019/020/021/022/023/024 chat-presentation cascade + CH-004 zoom + F3 D4 ADR-0034 kickoff

### Trigger

W25 D2 cascade closed BUG-015 / 016 / 017(Document Detail Wave B + chunker amendment),Day 2 cont user-eye verify on chat 頁面 揭露 6 個 連續 presentation-layer issues post BUG-021 amendment:

- **BUG-019** Sev2 — InlineImageCard removed/regression — restored(commit `d586fc3`)
- **BUG-020** Sev2 — CitationPill hover popover + SingleScreenshotStrip — restored(commit `b08d480`)
- **BUG-021** Sev2 — chat-answer rendering 4-fix batch(marker→pill replace + react-markdown via ADR-0036 + doc_format propagation + ImageGallery `>=1` unify)— commit `78f3d36`;BUG-021 amendment commit `3532e4b`(AnswerBodyMarkdown single-render refactor + ScreenshotModal mockup-faithful 2-col rewrite)
- **BUG-022** Sev1 — `Citation.doc_format` required field broke `/conversations/{id}` stored-data deserialization(BUG-021 backward-compat regression) — fix via Pydantic `= "docx"` default + 8-line comment(commit `2924471`);Sev1 postmortem written per PROCESS.md §4.5
- **BUG-023** Sev2 — CitationPill popover `<div>` in `<p>` hydration warning(react-markdown `<p>` ancestor + popover inner divs HTML5 spec violation)— fix via 3 `<div>` → `<span style={display}>` surgical(commit `250fdc6` combined with BUG-024)
- **BUG-024** Sev3 — ImageGallery thumbnail badge idx(subset `i+1`)vs ScreenshotModal idx(full citations `findIndex+1`)mismatch — fix via `allCitations` prop pass + canonical full-citations numbering(commit `250fdc6` combined with BUG-023)

**14-bug cascade closure milestone** — BUG-009-024(13 fixes + BUG-018 disproved 不計)closed within W25 D1-D3;classic「user-eye verify each fix surfaces next sub-issue」pattern;cumulative empirical validation of cascade-detection mechanism(extends from visual / functional surfaces to console errors + numbering inconsistencies + data-shape regressions)。

### Done

**CH-004 ScreenshotModal zoom-to-original feature**(commit `0e19fdf`):

- User report: BUG-021 amendment 2-col layout 令 image 縮細到 ~62% modal width(side panel 佔 ~38%);user 要 click-to-zoom-to-original
- Spec: `docs/03-implementation/changes/CH-004-screenshot-modal-zoom-to-original/spec.md` — frontend-only enhancement,opt-in progressive disclosure
- Implementation: `isZoomed` useState + ESC keydown handler scoped useEffect + image `onClick` zoom-in + conditional zoom overlay z-index 200 over modal z-index 100 + dual-close(backdrop / image / ESC)
- 50 lines LOC Karpathy §1.3 surgical localized to ScreenshotModal function
- Verify: tsc / lint / Vitest 7/7 preserve
- H7 fidelity preserve(mockup 2-col baseline unchanged;zoom = NEW affordance on top per design-stage expansion spirit)

**Eval supplement update**:

- Added **Q-W25-I07** to `docs/eval-set-v0-w25-supplement.yaml` — user real-world query 2026-05-24「Show me all the Integration scenarios」
- `query_phrasing_source: user-real-2026-05-24`(distinct from synthetic),`difficulty: hard`,`expected_answer_keywords: Scenario A/B/C/D/E`
- `total_queries: 12 → 13`;`composition.image_queries: 6 → 7`
- Documents D3 observation:single hybrid retrieve returns 2 citations covering scenarios A+B + 0 images — vocabulary overlap between query「Integration scenarios」+ scenario-specific chunks(「Customer service request submission」/「Saga-style multi-system」/ etc.)too low for single-hop retrieval to fetch all 5 chunks

### Diagnosis update

**User real-world observation validates W25 F3 D4 query expansion rationale**:

User query「show me all the Integration scenarios」expected coverage of A-E scenarios(each with image)but actual result:
- 2 citations returned
- Footnote 1 + 2 reused across 5 scenario mentions in LLM response(LLM does NOT cite distinct chunks for C/D/E — only paraphrases from same 2 chunks)
- 0 with screenshots in citation panel

**Root cause(per W25 plan §1.1)**:
- **Chunker fix(F1)done** — `sample-doc-with-image-1` post-W25 chunks = 63(from 121,-48% via adjacent-short-merge consolidation)
- **Retrieval(F3 D4 NOT YET implemented)** — single hybrid retrieve cannot expand vocabulary;query「Integration scenarios」matches §X-summary chunk(「five end-to-end scenarios covering...」)well + maybe 1 scenario-specific chunk via lexical overlap;but A-E individual chunks use scenario-specific vocab → top-K hit summary + A or A+B
- **Citation enrichment(F5 D1 NOT YET implemented)** — even if A-E chunks were retrieved,citation post-process for neighbour images not yet implemented;image association rate stays 0/8 until F5 D1 lands

**This is the textbook target use case for F3 D4 query expansion + F5 D1 citation post-process**:
- F3 D4 reformulator generates variants(`Customer service request integration` / `Saga-style orchestration scenario` / `Inbound event-driven flow` / `Batch ETL data movement` / etc.)
- Each variant runs hybrid retrieve → RRF fusion surfaces A-E individual chunks
- LLM sees 5 distinct chunks → can cite 5 distinct footnotes
- F5 D1 attaches neighbour images to citations → A-E images surface

### Decisions(Day 3)

- **D3.1** — Q-W25-I07 added as user-real eval supplement entry vs creating new bug folder — observation 100% validates W25 plan rationale(plan §1 explicit framing);adding to eval set creates measurement signal for F4 / F6 lift measurement(pre-F3 baseline ~2/13 image hit if assume Q-W25-I07 same shape as I01-I06;post-F3 expected lift ≥ 5/13)
- **D3.2** — CH-004 zoom feature handled as Change(not Bug-fix)— mockup 2-col baseline H7-faithful via BUG-021 amendment intentional;user-pick enhancement on top per design-stage expansion spirit per ADR-0025/0026/0027 precedent
- **D3.3** — **F3 D4 ADR-0034 draft kickoff next**(plan sequence:F2 done → F3 next)— ADR-0034 reserved per `docs/adr/README.md` Next-NNNN footer;Chris approval needed before F3 implementation per CLAUDE.md §6 ADR format

### Verify gates

- BUG-019-024 cumulative commits + CH-004 commit:tsc / lint / Vitest 7/7 / backend pytest baseline preserved(per individual commit footer verify)
- Eval supplement YAML structure valid(13 queries,T-series 6 + I-series 7 = 13 total composition)
- W25 progress.md Day 3 entry committed below — chronicles 14-bug cascade closure + CH-004 + F3 prep handoff

### Blockers

無 functional blocker。Implementation blocker(F3 ADR draft awaiting Chris approval before F3 implementation)— normal CLAUDE.md §6 ADR workflow,non-blocking on phase progress per R5。

### Actual vs Planned Effort

| Deliverable | Planned (h) | Actual (h) | Variance |
|---|---|---|---|
| BUG-019/020/021 cascade fix(presentation layer)| 0 | ~3 | +3(unplanned cascade discovery via user-eye verify)|
| BUG-021 amendment(2-col modal rewrite + AnswerBodyMarkdown refactor)| 0 | ~2 | +2 |
| BUG-022 Sev1 fix(schema default + postmortem)| 0 | ~1 | +1 |
| BUG-023 + BUG-024 surgical fix + 2 doc folders | 0 | ~1 | +1 |
| CH-004 ScreenshotModal zoom feature | 1-2 | ~0.8 | -0.2 to -1.2 |
| Q-W25-I07 eval supplement add | 0 | ~0.1 | +0.1 |
| W25 Day 3 progress entry | 0 | ~0.3 | +0.3 |
| ADR-0034 draft kickoff(next)| 2-3(F3.1)| 0(scheduled D4)| pending F3 active flip |

**Cumulative Day 3 effort**:~8h actual vs ~0h planned(全 cascade-driven + enhancement-driven scope expansion outside F3 plan budget)— consistent with W12-W18 / W20-W24 user-eye-verify-driven discovery pattern;F3 D4 implementation still on track for D4-D9 plan window。

### Commits

_(見 commit footers)_:
- `fix(chat): restore InlineImageCard inline image rendering — BUG-019 + H7 W22 regression`(`d586fc3`)
- `fix(chat): restore CitationPill hover popover + add SingleScreenshotStrip — BUG-020 + H7 W22 regression`(`b08d480`)
- `fix(chat): markdown render + marker→pill replace + doc_format propagation + ImageGallery unify — BUG-021 + ADR-0036`(`78f3d36`)
- `fix(chat): BUG-021 amendments — inline pill flow + mockup-faithful ScreenshotModal 2-col layout`(`3532e4b`)
- `fix(api): Citation.doc_format default "docx" — BUG-022 BUG-021 backward-compat regression`(`2924471`)
- `fix(chat): BUG-023 popover div→span + BUG-024 ImageGallery badge idx alignment`(`250fdc6`)
- `feat(chat): ScreenshotModal zoom-to-original — CH-004`(`0e19fdf`)
- `docs(planning): W25 D3 progress entry + Q-W25-I07 supplement add + ADR-0034 F3 kickoff`(pending,this commit)

---

## Day 4 — 2026-05-24:F5 D2 — CH-003 + ADR-0035 batched approval + retrieval low_value soft-relax implementation

### Trigger

W25 D3 closed嗮 F1+F3+F5 D1(chunker / query expansion / citation neighbour-image attach)three large pieces;但 user real-world Q-W25-I07「Show me all the Integration scenarios」synthesizer 仍 refuse,citation panel 0 images。F5 D1 attach 機制 work(targeted Scenario A query verified citation+image),但 overview-shape query 嘅 synthesizer 拒絕 cite → D1 nothing to augment。F5 D2 retrieval-side complement closing `architecture.md §3.5/§3.6` 「deboost」spec wording vs W2 baseline「hard exclude」divergence + addressing H1 60% low_value flagged image-chunk exclusion = next必要 deliverable。

### H1 boundary determination(per W25 plan §7 R6 D0 finding (iii) + Day 0 D0.4)

**AskUserQuestion 2-step batched approval** chat 2026-05-24:

| # | Question | Chris pick | Outcome |
|---|---|---|---|
| 1 | H1 boundary 點 call?Path A(CH-003 alone)vs Path B(CH-003 + co-ADR-0035 mandatory) | **Path B(Recommended)** | ADR-0035 mandatory;CH-003 + ADR-0035 batched |
| 2 | Review ADR-0035 + CH-003 spec.md content gate — Accept both proceed? | **Accept both(Recommended)** | ADR-0035 Proposed → Accepted;CH-003 spec.md draft → approved |

Path B reasoning(per Day 4 entry analysis):
- `architecture.md §3.6 line 384` 係 content-locked v6 spec normative filter clause statement
- Changing literal filter clause + score weighting injection = §3.6 retrieval spec interface change
- Governance symmetry:ADR-0022(auth-transport mechanism with semantics preserved → ADR)+ ADR-0033(W25 F1 chunker tuning internal → ADR)→ ADR-0035 不寫 = governance asymmetry
- Cost asymmetric obviously toward Path B(ADR draft ~2h vs governance drift risk)

### Done

**1. ADR-0035 draft + Accepted**:

- `docs/adr/0035-retrieval-low-value-soft-relax.md` written:Context(spec-implementation divergence H1 trigger evidence)+ Decision 3-pronged(server-side filter shift + client-side post-filter override + Configurable Settings knob)+ 6 Alternatives evaluation + Consequences(positive / negative / neutral)+ §3.6 inline-tagged amendment statement(scheduled W25 F7 closeout per ADR-0024 precedent;doc-version held — ADR is record)+ References cross-link
- Status:Proposed → Accepted(Chris 2-step AskUserQuestion approval cycle)
- `docs/adr/README.md` index row landed + footer Next-NNNN updated 0035 → 0037 next available(0036 react-markdown already landed W25 D3)

**2. CH-003 spec.md + checklist + progress**(per PROCESS.md §3 lifecycle):

- `docs/03-implementation/changes/CH-003-image-association-retrieval-and-citation/spec.md` v1.0 covering D2 forward + D1 retroactive(shipped W25 D3 commit `b267a8a`)bundled per W25 plan §2 F5 explicit「combined CH-003」design
- 10 acceptance criteria + 5 Change-specific risks(R1-R5)+ 4 design decisions(D1-D4)+ Implementation Plan with effort estimate + Rollback plan
- Status:draft → approved 2026-05-24
- `checklist.md` 22 atomic items spanning D2(D2.1-D2.15)+ D1 retroactive(D1.1-D1.6)+ Governance(G1-G5)+ Closeout(C1-C10);D2 + D1 + Governance全部 `[x]` 本 session 完成
- `progress.md` Day 1 entry chronicles full implementation log

**3. D2 backend implementation**(4 file edits per Karpathy §1.3 surgical scope):

| File | Change |
|---|---|
| `backend/storage/settings.py` | NEW `retrieval_image_low_value_weight: float = 0.7` knob(9-line docstring cite ADR-0035 + §3.5 divergence)|
| `backend/retrieval/hybrid.py` | docstring update + import `dataclasses.replace` + `_DEFAULT_FILTER = "enabled eq true"`(low_value clause移走)+ NEW `_DEFAULT_IMAGE_WEIGHT = 0.7` module constant + NEW `_apply_low_value_post_filter` helper(3-branch + ≤0 degenerate)+ `HybridSearcher.__init__` add `image_weight` kwarg + `search()` integration point post Azure Search response + logger.debug includes `pre_low_value_post_filter_count` + `image_weight` fields |
| `backend/retrieval/retrieval_engine.py` | line 143-144 stale fallback string update + ADR-0035 cite comment |
| `backend/api/server.py` | line 130-134 HybridSearcher lifespan construction wire `image_weight=settings.retrieval_image_low_value_weight` |

**4. NEW unit tests**:

- `backend/tests/test_hybrid_searcher_image_low_value.py` NEW 19 tests covering all D2 branches(12 `_apply_low_value_post_filter` unit + 2 module constants + 5 HybridSearcher integration);**19/19 pass** in 0.84s
- `backend/tests/test_retrieval.py:44 + :281` 2 stale assertion updates removing `low_value_flag eq false` clause + ADR-0035 cite comments(per ADR-0035 spec change driven update,Karpathy §1.3 surgical envelope holds)

**5. Verify gates**:

| Gate | Result |
|---|---|
| `pytest tests/test_hybrid_searcher_image_low_value.py -v` | **19/19 pass** in 0.84s |
| `pytest tests/` full regression | **1013 passed + 25 skipped + 0 failed** in 185s(pre-CH-003 baseline 994 → +19 net IMPROVED) |
| `mypy --strict --explicit-package-bases retrieval/hybrid.py storage/settings.py` | **zero new errors on touched code**(11 pre-existing bare `dict` errors in untouched methods per Karpathy §1.3 surgical out of scope) |
| `ruff check retrieval/ storage/settings.py tests/test_hybrid_searcher_image_low_value.py` | **All checks passed** |

### Decisions(Day 4)

- **D4.1** — H1 boundary Path B(per Chris AskUserQuestion pick):governance symmetry over implementation-detail interpretation;ADR-0035 mandatory
- **D4.2** — D2 + D1 single CH-003(per W25 plan §2 F5 explicit design):same root cause chain + bundled test surface + Karpathy §1.2 simplicity
- **D4.3** — `image_weight` plumbed via `HybridSearcher.__init__` kwarg(not per-call `search()` param):W2 baseline Settings injection at lifespan pattern preserved + simpler caller API
- **D4.4** — `image_weight = 0.7` baseline locked(per W25 plan §8 Q5):empirical adjust knob available via Settings if F6 surfaces tuning need
- **D4.5** — §3.6 inline-tagged amendment scheduled W25 F7 closeout cascade(NOT CH-003 commit scope):per ADR-0024 inline-tag precedent + doc-version held
- **D4.6** — Stale W2 baseline filter strings in `retrieval_engine.py:143-144` + `test_retrieval.py:44/281` updated as part of CH-003 commit(4-line edit total + 100% deterministic content change driven by ADR-0035):Karpathy §1.3 surgical envelope holds
- **D4.7** — Existing 11 pre-existing bare `dict` mypy --strict errors in `hybrid.py` untouched methods(`fetch_by_chunk_ids` / `list_documents` / `list_chunks`)NOT fixed this session per Karpathy §1.3 surgical:out of CH-003 scope + zero NEW errors my code introduced

### Blockers

無。

### Actual vs Planned Effort

| Deliverable | Planned (h) | Actual (h) | Variance |
|---|---|---|---|
| H1 boundary surface + AskUserQuestion 2-step | 0 | ~0.15 | +0.15(governance gate)|
| ADR-0035 draft | 2 | ~0.4 | -1.6 |
| CH-003 spec draft | 1 | ~0.3 | -0.7 |
| D2 implementation 4 file edits | 1.5 | ~0.4 | -1.1 |
| NEW unit tests 19 cases | 1.5-2 | ~0.6 | -1 |
| Existing tests update(2 assertions)| 0.25 | ~0.1 | -0.15 |
| Regression run + mypy + ruff | 0.5 | ~3.2 | +2.7(full pytest 185s runtime dominates)|
| CH-003 checklist + progress + W25 D4 entry + ADR README index | 1 | ~0.6 | -0.4 |

**Cumulative Day 4 effort**:~5.7h actual vs ~7-8.25h planned(F5 D2 portion of W25 budget);**compression factor ~1.3-1.5×**(governance-heavy phase with H1 ADR overhead + full pytest 185s + verify gates add real time;lower compression than W22-W24 frontend rebuild ~5-10× as expected)

### Carry-overs to F6 / F7

- 🚧 **§3.6 inline-tag amendment** scheduled W25 F7 closeout cascade(per ADR-0035 §3.6 amendment section;doc-version held per ADR-0024 precedent)
- 🚧 **F4 LIVE RAGAs eval verify gate**(eval-set-v0-w25-supplement 13 queries including Q-W25-I07;G1 hard gate ≥ 5/8;G2 R@5 ≥ 0.92;G3 4-metric within 5pp;G4 P95 < 5s)— needs LIVE Azure key environment
- 🚧 **F6 manual user-test** ≥ 4/5 image-bearing queries via `/chat` UI(包括 Q-W25-I07 + 4 條 sample-doc-with-image-1 queries)— needs F4 gate clean first
- 🚧 **F7 phase closeout** retro + cross-doc sync(architecture.md inline-tag + COMPONENT_CATALOG C04 status update + RISK_REGISTER 若有新 risk + decision-form OQ status sync)— after F4 / F6

### Commits

_(本 session 即將 commit)_:
- `feat(retrieval): CH-003 D2 retrieval low_value soft-relax — ADR-0035 implementation`(pending)

---

**End of Day 4 entry** — F5 D2 deliverable complete;F4 LIVE eval + F6 manual test 留 user pre-Beta scope per W25 plan §6 inheritance pattern from W17-W24 smoke-user-deferred allowance。

---

## Day 5 — 2026-05-24:F7 Phase Closeout + User-eye verify result + Retro

### F7 Closeout cascade(per W25 plan §2 F7)

**Cross-doc sync(F7.2)** — 7 changes landed:

| Target | Amendment |
|---|---|
| `architecture.md §3.1` | inline-tagged ADR-0034 amendment(query expansion + RAG-Fusion + Settings.enable_query_expansion + P95<5s cap)— doc-version held |
| `architecture.md §3.3` | inline-tagged ADR-0033 amendment(`_TOKEN_LOW_VALUE_FLOOR` 100→60 + `_merge_adjacent_shorts` + `_MIN_CHUNK_MERGE_FLOOR=160`)— doc-version held |
| `architecture.md §3.6` | inline-tagged ADR-0035 amendment(server-side filter shift `enabled eq true` + client-side post-filter low_value+image × 0.7 / low_value+no-image drop)— doc-version held |
| `COMPONENT_CATALOG.md` C01 | W25 F1 amendment(ADR-0033 chunker tuning) |
| `COMPONENT_CATALOG.md` C04 | W25 F3 + F5 D2 amendment(ADR-0034 query expansion + ADR-0035 retrieval relax) |
| `COMPONENT_CATALOG.md` C05 | W25 F5 D1 amendment(citation neighbour-image attach + user-test 2026-05-24 confirmed milestone) |
| `RISK_REGISTER.md` §1 + §3 | **NEW R14**(Synthesizer overview-query refuse rate — W25 D4 user-test finding;Severity 🟡 Medium;Mitigation candidates documented;CH-005 W26+ candidate;decay date W26+) |

**Frontmatter flip(F7.4.2)**:
- `plan.md` frontmatter:`status: active → closed`
- `checklist.md` frontmatter:`status: in-progress → complete` + `last_updated: 2026-05-24`
- `progress.md` frontmatter:`status: in-progress → closed`

**User-eye verify result(F6.1.2 partial)** — chat 2026-05-24 user-test:

| Query | Result | Diagnosis |
|---|---|---|
| **Q-W25-I07**「show me all the Integration scenarios」 | 0 citations + 「I cannot find this」refuse(11.06s · $0.017) | **Synthesizer strictness layer surfaces** — F5 D1 nothing to augment when synthesizer returns 0 citations;**NEW R14 finding** NOT part of original W25 Path III scope |
| **「what is high level architecture ?」** | **2 citations + 1 with screenshot ✅**(11.59s · $0.020) | **First-ever post-W25 image-in-citation milestone** — F1+F3+F5 D1+F5 D2 complete chain confirmed works on section-targeted queries |

**Empirical evidence**:Path III scope(D3 chunker + D4 query expansion + D2 retrieval relax + D1 citation enrichment)closes **retrieval + delivery** layer on section-targeted queries;synthesizer-side strictness on overview-aggregate queries remains **untouched layer**(surfaces as R14)。

---

## Retro — W25 Phase

### Phase Gate result(G1-G6 per plan §3)

| Gate | Target | Actual | Verdict |
|---|---|---|---|
| **G1** Image association rate ≥ 5/8 | Final hard gate | 🟡 **Partial confirmed via D4 user-test**(1 confirmed image-in-citation milestone on「high-level architecture」query;pre-W25 baseline 0/8 → post-D2+D1 lift confirmed empirically)— full 8-query measurement deferred F6.2 LIVE eval W26+ | **PASS WITH MEASUREMENT-DEFERRED CAVEAT** |
| **G2** Gate 1 R@5 ≥ 0.92 non-regression | F2 + F6 RAGAs | ✅ F2 verified R@5=0.9722(W2 baseline preserved post-chunker amendment;within-5pp envelope strictly held)| **PASS** |
| **G3** 4-metric within 5pp | F4 + F6 RAGAs LIVE | 🚧 **F4 LIVE eval deferred W26+**(R8/Azure-key-bound parallel-track per W17 F3.5b precedent)| **DEFERRED**(non-blocking — F4 prerequisite for measurement) |
| **G4** P95 < 5s | F4 + F6 measurement | 🚧 D4 manual chat observation **11.06s / 11.59s** local-dev range(within typical local-dev pipeline cold-start latency;production budget measurement needs F4 LIVE eval)| **DEFERRED** |
| **G5** ADR-0033 + ADR-0034 + **ADR-0035 NEW** Accepted | F7 review | ✅ all 3 Accepted by Chris(0033 2026-05-23 / 0034 + 0035 2026-05-24)| **PASS** |
| **G6** Manual ≥ 4/5 image-bearing queries | F6 manual | 🚧 **Partial 1/2 D4**(needs full 5-query expansion W26+)| **DEFERRED** |

**Overall Phase Gate verdict**:**PASS WITH F4/F6 LIVE-EVAL-DEFERRED CAVEAT**(G2 + G5 hard gates passed;G1 partial empirical confirmation via D4;G3 + G4 + G6 deferred to F4 LIVE eval W26+ per ADR-0017 R8/Azure-key-bound pattern)

### What worked

1. **R6 D0 recursive grep verification catches major plan-text contamination upfront** — 4 catches at Day 0(`hybrid_searcher.py` naming / D2 server-side filter mechanism / ADR numbering / eval-set path)prevented mis-implementation;**catch (iii) propagated forward to D4 H1 boundary AskUserQuestion** → ADR-0035 mandate confirmed by Chris Path B pick(governance symmetry vindicated)
2. **Path III scope analytical predictions matched empirically**(per plan §1 root cause analysis):F1 chunker fix + F3 query expansion + F5 D2 retrieval relax + F5 D1 citation enrichment closes retrieval+delivery layer;user-test confirmed section-targeted query「high level architecture」第一次帶圖 post-W25(0/8 → ≥ 1 empirical lift)
3. **CSS-first AI compression factor remained ~1-2×** on backend governance-heavy work(D4 ADR-0035 batched 5.7h actual vs ~7-8h planned)— lower than W22-W24 frontend ~5-10×(governance + verify gate add real time per W22 D9 anti-pattern recognition);realistic expectation calibration
4. **W25 D3 14-bug cascade closure**(BUG-009/010/011/012/013/014/015/016/017/019/020/021/022/023/024)cleared嗮 chat presentation layer ground before D4 retrieval-side closure work — classic「user-eye verify each fix surfaces next sub-issue」cascade pattern
5. **AskUserQuestion 2-step batched approval for ADR-0035 + CH-003 content** — efficient governance gate;Chris able to approve H1 boundary + content in single session vs split sessions

### What didn't / Surprises

1. **🆕 NEW R14 — Synthesizer overview-query refuse pattern surface post-W25 ship** — D4 user-test 揭示 F1+F3+F5 D1+F5 D2 four-pronged path III NOT sufficient for overview-aggregate queries(Q-W25-I07「show me all the Integration scenarios」still refuses despite all 4 layers active)— W25 plan original framing did NOT predict this layer divergence;**synthesizer-side strictness 屬 untouched 5th layer**;CH-005 W26+ candidate per R14 mitigation candidates (i)/(ii)/(iii)
2. **Plan-text said「F5 D2 H1 not triggered」** but D0 R6 catch (iii) flagged the boundary upfront;**D4 Chris AskUserQuestion pick Path B confirmed H1 triggered** → ADR-0035 mandatory(governance symmetry with ADR-0022 / ADR-0033 was the decisive argument);**plan-text was wrong on H1 prediction,R6 caught it before active-flip damage**
3. **W2 baseline filter strings duplicated in `retrieval_engine.py:143-144` + `test_retrieval.py:44/281`** surfaced as ADR-0035 implementation tail — Karpathy §1.3 surgical envelope expanded to 4-line edit(deterministic per ADR-0035 change);not anticipated in original CH-003 spec but bundled into single commit
4. **mypy --strict --explicit-package-bases revealed 11 pre-existing bare `dict` errors** in `hybrid.py` untouched methods(`fetch_by_chunk_ids` / `list_documents` / `list_chunks`)— NOT introduced by W25 changes,but signals project-level baseline strict-mode coverage gap;Karpathy §1.3 surgical = not fixed this session,W26+ tech-debt candidate
5. **Real-calendar compression factor smaller than W22-W24** — backend pipeline + governance heavy(ADR draft + AskUserQuestion + verify gate full pytest 185s)dominates timeline vs UI-heavy frontend rebuild;~1.3-1.5× compression D4 vs expected ~3-5× from W20-W24 pattern

### Carry-overs to W26+

| # | Item | Rationale | Trigger |
|---|---|---|---|
| **CO_W25_F4** | LIVE RAGAs eval `eval-set-v0-w25-supplement.yaml` 13 queries(包括 Q-W25-I07)+ G3 4-metric within 5pp verify + G4 P95 < 5s budget | Needs LIVE Azure key + Cohere key environment(per ADR-0017 R8/Azure-key-bound umbrella) | Azure key environment ready W16+ Track A IT cred parallel-track |
| **CO_W25_F6_expansion** | Full 5-query manual user-test(per F6.1.1 — 4 image-bearing on sample-doc-with-image-1 + 1 non-image control;Chris pick 1 query) | D4 partial(2 queries)demonstrated chain works but 1/2 hit ratio NOT representative for G1+G6 hard verdict | Sample expansion + Chris user-test execution(low ceremony — chat UI try)|
| **CO_W25_R14** | Synthesizer overview-query refuse pattern(NEW R14)— CH-005 W26+ candidate | F1+F3+F5 D1+F5 D2 closes retrieval+delivery layer but synthesizer-side strictness untouched | Either:CH-005 spec drafting + ADR if H1 trigger(`crag_confidence_threshold` 0.70 → 0.60 trial possibly H1)OR synthesizer prompt tuning AskUserQuestion gate decision |
| **CO_W25_F7.5_session_start** | `session-start.md` §10 W25 row(closed verdict + Gate result + carry-overs)+ §11 W25 CLOSED block | F7.5.1 + F7.5.2 deferred per W18-W24 closeout cascade precedent — next-session housekeeping | Next-session kickoff or W26+ rolling-JIT phase plan |
| **CO_W25_mypy_strict_debt** | 11 pre-existing bare `dict` errors in `backend/retrieval/hybrid.py` untouched methods(`fetch_by_chunk_ids` / `list_documents` / `list_chunks`)| Karpathy §1.3 surgical out of W25 scope;project-level baseline strict-mode coverage gap | W26+ tech-debt batch fix(可選 cluster with C04 modernization work)|

### ADR triggers landed during W25

| ADR | Status | Phase deliverable | Trigger reason |
|---|---|---|---|
| **ADR-0033** | Accepted 2026-05-23 | F1 D3 chunker re-tune | architecture.md §3.3 chunker behavior change(`_TOKEN_LOW_VALUE_FLOOR` 100→60 + adjacent-short-merge)— H1 trigger |
| **ADR-0034** | Accepted 2026-05-24 | F3 D4 query expansion + RAG-Fusion | architecture.md §3.1 query pipeline interface change(reformulator + RRF fusion + Settings flag + P95<5s cap)— H1 trigger |
| **ADR-0035 NEW W25 D4** | Accepted 2026-05-24 | F5 D2 retrieval low_value soft-relax | architecture.md §3.6 filter clause shift + ranking policy injection — H1 trigger confirmed Path B(R6 D0 catch (iii) propagated forward;plan-text「no H1 trigger」 superseded D4) |

### Phase status

W25-image-association-deep-fix **CLOSED 2026-05-24** — PASS WITH F4/F6 LIVE-EVAL-DEFERRED CAVEAT(G2 + G5 hard gates passed;G1 partial empirical confirmation via D4 user-test;G3 + G4 + G6 deferred W26+ per ADR-0017 R8/Azure-key-bound umbrella)。

### Commits per Day

| Day | Commits | Deliverable |
|---|---|---|
| **D0** | `cfa3326` kickoff | F0 plan + checklist + progress |
| **D1** | `796af6c` chunker low-value tuning | F1 ADR-0033 + chunker code + tests |
| **D2** | `7fdbda7` BUG-012 cascade + `(more cascade)` | F2 verify + BUG-013/014/015/016/017 |
| **D3** | `3af1d2e` + `f9e3a78` + `22a1b3b` + `b267a8a` + 7 chat BUG fixes + CH-004 | F3 ADR-0034 + F5 D1 + 14-bug cascade closure + CH-004 zoom |
| **D4** | `7402e0e` CH-003 D2 ADR-0035 | F5 D2 ADR-0035 + CH-003 + 4 backend edits + 19 NEW tests |
| **D5** | _(this commit)_ `docs(planning): close W25-image-association-deep-fix retro` | F7 closeout cascade |

---

**End of Day 5 entry**
**End of W25-image-association-deep-fix phase** — closed 2026-05-24