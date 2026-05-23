---
phase: W25-image-association-deep-fix
plan_ref: ./plan.md
status: in-progress    # in-progress | complete
last_updated: 2026-05-23
---

# Phase W25 — Checklist

> Atomic checkbox 每 item ≤ 1-2 hour effort。Derived from `plan.md §2` deliverables。
> AI tick 完成嘅 item;延後項標 🚧 + reason(per CLAUDE.md sacred rule — 唔可以刪未勾 `[ ]`)。

## F0 — Kickoff(Day 0)

- [x] **F0.1** — `W25-image-association-deep-fix/` folder created
- [x] **F0.2** — `plan.md` written + locked(5 design defaults captured per §8)
- [x] **F0.3** — `checklist.md` derived from plan §2
- [x] **F0.4** — `progress.md` Day 0 entry init
- [ ] **F0.5** — Kickoff commit `chore(planning): kickoff W25-image-association-deep-fix`

## F1 — D3 chunker re-tune(ADR-0033)

### F1.1 ADR draft + approval
- [x] **F1.1.1** — Draft `docs/adr/0033-chunker-low-value-tuning.md`:Context(60% low_value empirical signal)+ Decision(floor 60 + adjacent-short-merge combined)+ 6 Alternatives + Consequences + Implementation Mapping + References
- [x] **F1.1.2** — Chris approval(chat 2026-05-23「Approve as-is」)→ ADR status `Proposed → Accepted`
- [x] **F1.1.3** — Update `docs/adr/README.md` index row + Next-NNNN footer(0033 landed Accepted;0034 reserved for W25 F3;0035 reserved if R6 H1 trigger confirmed at W25 F5)

### F1.2 Chunker code
- [x] **F1.2.1** — `layout_aware.py:35`:`_TOKEN_LOW_VALUE_FLOOR` module constant **100 → 60**(annotated with ADR-0033 cite)
- [x] **F1.2.2** — `layout_aware.py`:NEW `_MIN_CHUNK_MERGE_FLOOR = 160` constant + NEW `_merge_adjacent_shorts` + `_should_merge` methods on `LayoutAwareChunker`;hook 入 `chunk()` return path(post-process pass over emitted chunks);re-index 0..N-1 contiguous via `dataclasses.replace`(import added)
- [x] **F1.2.3** — `_TOC_PATTERNS` + `_VERSION_PATTERNS` unchanged(verified — no edit touched lines 37-46;only floor constant + new merge methods added)
- [x] **F1.2.4** — `mypy --strict --explicit-package-bases` on `backend/ingestion/chunker/layout_aware.py` — see F1.4 verify gates

### F1.3 Unit tests
- [x] **F1.3.1** — `backend/tests/test_chunker.py`:`test_w25_floor_60_marks_chunks_below_60_low_value` + `test_w25_floor_60_keeps_60_to_99_token_chunks_high_value`(reclamation envelope under merge-disabled chunker)
- [x] **F1.3.2** — `backend/tests/test_chunker.py`:`test_w25_adjacent_short_merge_combines_two_subsections` + `test_w25_merge_does_not_combine_with_table_chunk` + `test_w25_merge_respects_hard_cap` + `test_w25_merge_reindexes_contiguous_zero_to_n` + `test_w25_long_sections_do_not_merge` + `test_w25_merge_concatenates_embedded_image_positions`
- [x] **F1.3.3** — `backend/tests/test_chunker.py`:`test_w25_synthetic_corpus_chunk_count_within_twenty_percent_envelope`(6-section synthetic envelope `[2, 7]` chunks per ADR §Negative Consequences ±20%)
- [x] **F1.3.4** — `pytest backend/tests/test_chunker.py` full file — see F1.4 verify gates
- [x] **F1.3 ancillary** — Update existing `test_simple_three_section_doc_emits_three_chunks` paragraph sizes(`* 20` → `* 40`)so section-boundary intent preserved post-merge consolidation

## F1.4 — Verify gates

- [x] **F1.4.1** — `mypy --strict --explicit-package-bases ingestion/chunker/layout_aware.py` → **exit 0**(zero new error on layout_aware.py;17 pre-existing parser tech debt unchanged per Karpathy §1.3 surgical, same convention as BUG-010 postgres_backend tuple/dict carve-out)
- [x] **F1.4.2** — `pytest tests/test_chunker.py -v` → **21 passed in 256.98s**(12 existing + 9 NEW W25 tests)
- [x] **F1.4.3** — `pytest tests/` full backend regression → **939 passed + 25 skipped + 0 failed** in 489.10s(+9 vs BUG-010 baseline 930;zero regression)

## F2 — F1 verify gate:Gate 1 R@5 re-verify + dev-KB re-ingest

### F2.1 Re-ingest
- [ ] **F2.1.1** — Re-ingest `sample-doc-with-image-1`(verify post-F1 chunk count change ≤ 20% envelope)
- [ ] **F2.1.2** — Re-ingest `sample-kb-test-1`
- [ ] **F2.1.3** — Re-ingest `sample-doc-for-rag-knowledge-1`
- [ ] **F2.1.4** — `GET /kb/{kb_id}` for each → `total_chunks` matches re-ingested expectation;`total_screenshots` BUG-010 wiring preserved unchanged

### F2.2 Eval set v0 + image queries supplement
- [ ] **F2.2.1** — Confirm `eval-set-v0.yaml` 6 samples loadable + queryable post-F1 re-ingest
- [ ] **F2.2.2** — Author `eval-set-v0-image-queries.yaml`:5-8 image-bearing queries on `sample-doc-with-image-1`(eg. "high-level architecture diagram" / "integration components" / "deployment topology" / "API contracts" / "executive summary visualization" + Chris pick 1-2)
- [ ] **F2.2.3** — Wire `eval-set-v0-image-queries.yaml` into eval harness as supplementary set(eval CLI flag OR fold under v0 as section)

### F2.3 Gate 1 R@5 re-verify
- [ ] **F2.3.1** — Run R@5 on `eval-set-v0`(6 samples)post-F1 re-ingest → record value
- [ ] **F2.3.2** — Hard pass condition:R@5 ≥ **0.92**(W2 baseline 0.9722,-5pp envelope)— if < 0.92 → STOP + ADR-0033 amendment
- [ ] **F2.3.3** — Record chunk count change `sample-doc-with-image-1`:121(pre) → ___ (post);expected ~80-100 range

### F2.4 RAGAs 4-metric soft gate(F2)
- [ ] **F2.4.1** — Run RAGAs 4-metric on `eval-set-v0` post-F1 → soft-check within 5pp of W6 baseline(hard gate at F4)
- [ ] **F2.4.2** — If any metric > 5pp degradation → flag F4 design intent + early warning to user

## F3 — D4 query expansion / RAG-fusion(ADR-0034)

### F3.1 ADR draft + approval
- [ ] **F3.1.1** — Draft `docs/adr/0034-query-expansion-rag-fusion.md`:Context + Decision(RRF + GPT-5.5-mini reformulator + P95<5s latency cap)+ Alternatives(no expansion / heavier multi-step CoT reformulation)+ Consequences
- [ ] **F3.1.2** — Chris approval → ADR status `Proposed → Accepted`
- [ ] **F3.1.3** — Update `docs/adr/README.md` index

### F3.2 Query reformulator
- [ ] **F3.2.1** — `backend/pipeline/query_reformulator.py` NEW module:`async def reformulate(query: str, max_variants: int = 3) -> list[str]`
- [ ] **F3.2.2** — 用 Azure OpenAI GPT-5.5-mini chat completion(per H2 vendor lock — 唔加新 dependency)生 N-1 個 reformulation
- [ ] **F3.2.3** — Hard latency cap:wall-clock `asyncio.wait_for(timeout=4.5s)` for reformulation call(留 buffer for downstream;P95 5s end-to-end target)
- [ ] **F3.2.4** — Fall back path:`max_variants=2`(original + 1 reformulation only)若 P95 budget exceeded

### F3.3 Result fusion (RRF)
- [ ] **F3.3.1** — `backend/retrieval/result_fusion.py` NEW module:`async def fused_retrieve(queries: list[str], k: int, kb_id: str) -> list[ChunkRecord]`
- [ ] **F3.3.2** — RRF score formula:`sum(1/(60+rank))` across queries(per `architecture.md §3.6` hybrid retrieval RRF convention)
- [ ] **F3.3.3** — Configurable `enable_query_expansion` flag — F3 D1 decision:`Settings.enable_query_expansion_default: bool = True`(global default,override per request via query param OR `KbConfig` future)
- [ ] **F3.3.4** — Type hints + mypy strict on both new modules

### F3.4 Pipeline integration
- [ ] **F3.4.1** — `backend/pipeline/query_pipeline.py`:branch on `enable_query_expansion` setting → `reformulator → fused_retrieve`(vs plain `hybrid_searcher.search`)
- [ ] **F3.4.2** — BC verification:`enable_query_expansion=False` 路徑 unchanged(原 `/query` 行為 identical)— integration test

### F3.5 Tests
- [ ] **F3.5.1** — `test_query_reformulator.py`:cheap-LLM mock return predetermined variants;assert variants > 1 + ≤ max_variants
- [ ] **F3.5.2** — `test_query_reformulator.py`:latency fallback path(mock LLM 觸發 timeout → 2-query 變體 default)
- [ ] **F3.5.3** — `test_result_fusion.py`:RRF formula correctness — known rank inputs produce known fused order
- [ ] **F3.5.4** — `test_query_pipeline_expansion.py`:integration E2E `/query` with `enable_query_expansion=True` → top-K chunks 數量 + diversity check
- [ ] **F3.5.5** — `pytest tests/` full backend regression → 0 fail(W24c baseline 908 + W25 net add)

## F4 — F3 verify gate:RAGAs 4-metric regression + latency budget check

### F4.1 RAGAs run
- [ ] **F4.1.1** — Run RAGAs 4-metric on `eval-set-v0` + `eval-set-v0-image-queries` post-F3 with `enable_query_expansion=True`
- [ ] **F4.1.2** — Hard pass condition:all 4 metric within **5pp** of W6 baseline(Faithfulness / Correctness / Context-relevancy / Answer-relevancy)
- [ ] **F4.1.3** — If any metric > 5pp degradation → STOP;ADR-0034 amendment OR disable `enable_query_expansion_default=False`

### F4.2 Latency budget
- [ ] **F4.2.1** — Run 50-query benchmark via `/query` with expansion on
- [ ] **F4.2.2** — Measure P50 / P95 / P99 — record
- [ ] **F4.2.3** — Hard cap:P95 < **5s** — if violated → fall back to 2-query 變體 default;if still > 5s → disable `enable_query_expansion_default=False`

### F4.3 Image association soft gate
- [ ] **F4.3.1** — Measure citation-with-image hit rate on F2 `eval-set-v0-image-queries`
- [ ] **F4.3.2** — Soft target:≥ 3/8(non-blocking;chunker fix + query expansion should already surface some)
- [ ] **F4.3.3** — Compare pre-W25(0/8)vs post-F4 → record signal for F5 D2+D1 baseline

## F5 — D2 + D1 combined CH-003

### F5.1 CH-003 spec
- [ ] **F5.1.1** — Create `docs/03-implementation/changes/CH-003-image-association-retrieval-and-citation/` folder
- [ ] **F5.1.2** — Draft `spec.md`:scope(D2 retrieval relax + D1 citation post-process)+ acceptance(F5 sub-items below)+ ~3 day estimate + Tier 1 (no H1 trigger)
- [ ] **F5.1.3** — Chris approval(implicit via plan §8 default Q5)→ spec status `approved`
- [ ] **F5.1.4** — Derive `checklist.md` + `progress.md` Day 1 init

### F5.2 D2 retrieval low_value soft-relax
- [ ] **F5.2.1** — `backend/retrieval/hybrid_searcher.py`:filter 階段 condition「`low_value=true` AND `embedded_images_json` non-empty」→ retain(score × `retrieval_image_low_value_weight`)
- [ ] **F5.2.2** — `backend/storage/settings.py`:add `retrieval_image_low_value_weight: float = 0.7`(per user default Q5)
- [ ] **F5.2.3** — Unit test `test_hybrid_searcher_image_low_value.py`:image+low_value retained × 0.7;non-image low_value still dropped
- [ ] **F5.2.4** — `mypy --strict` clean

### F5.3 D1 citation post-process
- [ ] **F5.3.1** — `backend/generation/citation_image_neighbors.py` NEW(or extend existing `citation_enrichment.py`):
  - `async def attach_neighbor_images(cited_chunks, all_chunks, max_aux=2) -> list[CitationWithAux]`
  - Lookup logic:cited chunk's `section_path` match OR `doc_order ± N=3` range
  - 攞 neighbors 嘅 `embedded_images_json` → flatten → dedup by sha → cap at `max_aux_images_per_citation=2`
- [ ] **F5.3.2** — `backend/api/schemas/query.py`(or wherever `Citation` Pydantic lives):add field `aux_embedded_images: list[ImageRef] = []`(BC additive)
- [ ] **F5.3.3** — `backend/api/routes/query.py` `_proxy_citation_images`:integrate `aux_embedded_images` → 同 `embedded_images` 一齊行 proxy URL rewrite(streaming + non-streaming 兩路)
- [ ] **F5.3.4** — Unit test `test_citation_image_neighbors.py`:section_path match + doc_order ±3 range + cap-at-2 behaviour
- [ ] **F5.3.5** — Integration test `test_query_aux_embedded_images.py`:end-to-end `/query` with image KB → citation `aux_embedded_images` populated + proxy URL rewritten

### F5.4 Frontend compat check
- [ ] **F5.4.1** — `frontend/components/chat/ImageGallery.tsx`(or wherever citation viewer renders images):check `aux_embedded_images` 是否自動接住(若 Pydantic 同 TypeScript schema 兼容 fold-in,frontend 零改動)
- [ ] **F5.4.2** — 若 frontend 要 explicit support,scope 範圍 minimal(zero new visual surface — render aux 同 main `embedded_images` 同 component / 同 grid;non-H7-trigger 因 mockup unchanged)

### F5.5 CH-003 closeout
- [ ] **F5.5.1** — CH-003 `progress.md` closeout summary + status `approved → done`
- [ ] **F5.5.2** — CH-003 commit `feat(retrieval): D2 image-bearing low_value soft-relax + D1 citation image neighbors — CH-003`

## F6 — F5 verify gate:end-to-end manual + image association measurement

### F6.1 Manual user-test
- [ ] **F6.1.1** — Prepare 5 queries(4 image-bearing on `sample-doc-with-image-1` + 1 non-image control;Chris pick 1 query in F6.1.2)
- [ ] **F6.1.2** — Chris user-test execution(or chat 提供 5 queries + AI 跑 + paste citation result)
- [ ] **F6.1.3** — Pass condition:**≥ 4/5 image-bearing queries 嘅 citation 帶有至少一張對應 section 嘅圖**;non-image query control 應該 0 圖(false-positive control)

### F6.2 Image association rate measurement
- [ ] **F6.2.1** — Run F2 `eval-set-v0-image-queries` post-F5 → measure citation-with-image hit rate
- [ ] **F6.2.2** — Final target:**≥ 5/8**(pre-W25 baseline 0/8)
- [ ] **F6.2.3** — If < 5/8 → CH-003 amendment(adjust `retrieval_image_low_value_weight` from 0.7 → 0.5 / 0.8 per R7 mitigation;or adjust `max_aux_images_per_citation` cap)

### F6.3 Final RAGAs + latency check(non-regression)
- [ ] **F6.3.1** — Run RAGAs 4-metric post-F5 — all 4 still within 5pp of W6 baseline
- [ ] **F6.3.2** — Run latency P95 check post-F5 — still < 5s hard cap

## F7 — Phase closeout

### F7.1 Deliverable verification
- [ ] **F7.1.1** — Walk F1-F6 → confirm all `[x]` OR `🚧 deferred + reason` in progress.md
- [ ] **F7.1.2** — ADR-0033 status `Accepted` + ADR-0034 status `Accepted` confirmed via `docs/adr/` frontmatter
- [ ] **F7.1.3** — CH-003 status `done`

### F7.2 Cross-doc sync
- [ ] **F7.2.1** — `architecture.md v6 §3.3` inline-tagged amendment(ADR-0033 chunker low_value tuning note)— doc version not bumped(W17 precedent)
- [ ] **F7.2.2** — `architecture.md v6 §3.7` inline-tagged amendment(ADR-0034 query expansion note)— doc version not bumped
- [ ] **F7.2.3** — `COMPONENT_CATALOG.md` C01 Ingestion Pipeline status note(ADR-0033 reference)
- [ ] **F7.2.4** — `COMPONENT_CATALOG.md` C04 Retrieval Engine status note(ADR-0033 + ADR-0034 + CH-003 reference)
- [ ] **F7.2.5** — `docs/decision-form.md` OQ status no change(Q1-Q22 all unchanged by W25)— verify

### F7.3 Risk register
- [ ] **F7.3.1** — `RISK_REGISTER.md` review — add any new pattern surfaced(eg. if R1 / R2 / R3 / R5 / R7 materialized,record)
- [ ] **F7.3.2** — `R-B1`(Beta block)unchanged

### F7.4 Retro
- [ ] **F7.4.1** — `progress.md` Retro section:What worked / What didn't / Surprises / Carry-overs to W26+ / ADR triggers / Phase Gate G1-G6 result / Phase status
- [ ] **F7.4.2** — Frontmatter status flip `active → closed`
- [ ] **F7.4.3** — Closeout commit:`docs(planning): close W25-image-association-deep-fix retro`

### F7.5 Memory + session-start sync
- [ ] **F7.5.1** — Update `docs/12-ai-assistant/01-prompts/01-session-start.md` §10 W25 row(closed verdict + Gate result + carry-overs)
- [ ] **F7.5.2** — Update §11 carry-overs(W25 CLOSED block)
- [ ] **F7.5.3** — Memory append if new feedback / project pattern surfaced(eg. if D4 latency budget pattern repeatable,append to `feedback_*` memory)

---

## Cross-Cutting

- [ ] **C1** — All deliverables committed to git per R2(daily commit references progress Day-N entry)
- [ ] **C2** — All OQ status changes reflected in `decision-form.md` per R4(預想 W25 唔 resolve 新 OQ,verify)
- [ ] **C3** — All architectural-adjacent decisions documented as ADR per R5(F1 → ADR-0033,F3 → ADR-0034;F5 D2+D1 屬 H1 boundary → 純 retrieval policy + delivery layer,non-architectural,CH-003 sufficient — 已 plan §2 F5 確認 H1 not triggered)
- [ ] **C4** — `progress.md` retro section written per R3
- [ ] **C5** — `progress.md` frontmatter status flipped to `closed`
- [ ] **C6** — Phase W26+ kickoff trigger noted in retro(rolling JIT per CLAUDE.md §10)
- [ ] **C7** — Pre-active-flip 5-step grep verification recursive scope applied per CLAUDE.md §10 R6 — applied to F1 / F3 / F5 plan-text upfront(see Day 0 progress entry for upfront-verify記錄)

---

**Lifecycle reminder**:呢份 checklist 隨 plan §2 deliverables 衍生。新加 deliverable 必須先入 plan §7 changelog,然後再加 checklist item(R3 binding)。延後項標 🚧 + reason,不可刪 `[ ]`(CLAUDE.md sacred rule)。
