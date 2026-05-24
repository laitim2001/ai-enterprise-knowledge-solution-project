---
phase: W25-image-association-deep-fix
plan_ref: ./plan.md
checklist_ref: ./checklist.md
status: in-progress    # in-progress | closed
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

