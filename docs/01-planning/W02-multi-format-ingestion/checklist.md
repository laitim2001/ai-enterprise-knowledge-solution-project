---
phase: W02-multi-format-ingestion
plan_ref: ./plan.md
status: in-progress
last_updated: 2026-05-02
---

# Phase W02 — Checklist

> Atomic checkbox(每 item ≤ 1–2 hour effort)。
> AI tick 完成嘅 item;唔可以 tick 嘅 item 喺 progress Day-N entry 寫原因。
> Status:`in-progress` 由 W2 D1(2026-05-05)起;W1 D4 draft 階段全 unchecked。

## F1 — Docling .docx parser PoC(carry-over from W1)

- [ ] **R8 ops decision**:Chris confirm Docling install path(VPN/hotspot for pip install OR fallback python-docx)
- [ ] `backend/ingestion/__init__.py` package marker
- [ ] `backend/ingestion/parsers/__init__.py`
- [ ] `backend/ingestion/parsers/base.py` — Parser Protocol + `ParserResult` dataclass
- [ ] `backend/ingestion/parsers/docx_parser.py` — Docling-based(or python-docx fallback)
- [ ] **Heading style ~3% finding mitigation**:font-size heuristic detect section boundary(per W1 D4 F6 finding)
- [ ] Run on 6 sample manuals(`docs/06-reference/01-sample-doc/`)→ extract heading-aware sections + image inventory + table structure
- [ ] Sanity check report:per-doc parse success / fail + section count / image count / table count
- [ ] Update `components/C01-ingestion.md` status `v0-draft → v1-active`(per CC-5)

## F2 — Layout-aware chunker

- [ ] `backend/ingestion/chunker/__init__.py`
- [ ] `backend/ingestion/chunker/layout_aware.py` heading-aware section split + token budget
- [ ] `backend/ingestion/chunker/strategies.py` strategy selector per `KbConfig.chunk_strategy`
- [ ] `low_value_flag` heuristic(< 50 token / TOC / version statement detect)
- [ ] Run on 6 sample → estimated 2000-3000 chunks total
- [ ] Unit test:known input → expected chunk count + boundaries

## F3 — Screenshot extractor + Blob upload

- [ ] `backend/ingestion/screenshots/__init__.py`
- [ ] `backend/ingestion/screenshots/extractor.py` extract embedded images → PIL Image
- [ ] **EMF / WMF conversion via Pillow**(4 EMF found in W1 D4 inspector run)
- [ ] `backend/ingestion/screenshots/uploader.py` async Blob upload to per-KB container
- [ ] SHA256 dedup logic(same image multiple docs → 1 Blob upload)
- [ ] Verify Azurite container `ekp-kb-drive-screenshots` create + populated
- [ ] Update `components/C12-devops.md` Blob container provision section if changed

## F4 — Embedding pipeline first-pass(carry-over from W1 F10)

- [ ] `backend/ingestion/embedding/__init__.py`
- [ ] `backend/ingestion/embedding/azure_openai_embedder.py` async(SDK if R8 unblocks,HTTP REST fallback)
- [ ] text-embedding-3-large + MRL truncate to 1024d
- [ ] Cost log via structlog per chunk(input tokens + output dim)
- [ ] Smoke test:1 sample text → 1024d vector
- [ ] Parallel batch on 100 chunks → < 5s benchmark
- [ ] Q19 decision logged(1024 vs 3072)— W2 D3

## F5 — Index population orchestrator

- [ ] `backend/ingestion/orchestrator.py` end-to-end pipeline:parse → chunk → screenshot → embed → emit ChunkRecord
- [ ] `backend/indexing/populate.py` batch upload to `ekp-kb-drive-v1` via REST `/docs/index`
- [ ] Run on 6 sample → ~2000-3000 chunks indexed
- [ ] `python -m scripts.create_index get` → verify doc count
- [ ] Atomic per-doc transaction:if any chunk fail in a doc → rollback all chunks of that doc
- [ ] Update `components/C01-ingestion.md` and `C03-indexing.md` status v1-active → v2-stable post W2 D5

## F6 — Hybrid retrieval baseline(C04 first-touch)

- [ ] `backend/retrieval/__init__.py`
- [ ] `backend/retrieval/hybrid.py` Azure AI Search hybrid query via REST(BM25 + vector + RRF)
- [ ] Filter clause:`enabled eq true and low_value_flag eq false`
- [ ] `backend/retrieval/retrieval_engine.py` public `retrieve(query, kb_id, top_k)` API
- [ ] Wire to `/query` endpoint(replace 501 stub in C08)— top-50 chunks return
- [ ] Unit test:known query → assert non-empty + ranked output
- [ ] Update `components/C04-retrieval.md` status `v0-draft → v1-active`(per CC-5)

## F7 — Gate 1 evaluation(Recall@5 ≥ 80%)★ HARD GATE

- [ ] `backend/eval/runner.py` invoke C04 retrieval against 30-query eval set
- [ ] Compute Recall@5 per query + aggregate
- [ ] `backend/eval/gates.py` Gate 1 decision logic(R@5 ≥ 80% threshold)
- [ ] Generate `reports/gate1_w2.yaml` per-query + aggregate result
- [ ] **Gate 1 verdict**:pass / fail recorded in W2 progress.md retro
- [ ] If fail → trigger W2 末 retro analysis(chunk strategy / index config / query mismatch root cause)
- [ ] Update `components/C06-eval.md` status `v0-draft → v1-active`

## F8 — F11 ground truth fill(carry-over from W1)

- [ ] `scripts/discover_chunk_ids.py` helper(query populated index,find chunk_id for each eval query expected_answer)
- [ ] Chris(SME)review + validate 30 main queries → mark `annotation.validated: true`
- [ ] Replace placeholder chunk_id with real ones from `ekp-kb-drive-v1`
- [ ] `docs/eval-set-v1.yaml`(rename from v0)
- [ ] `python -m scripts.validate_eval_set docs/eval-set-v1.yaml` → exit 0

## F9 — Admin Console KB views(C09 first-touch)

- [ ] View 2 `/admin` overview component:aggregate KB stats(GET /kb count + total chunks)
- [ ] View 3 `/admin/kb` KB list with shadcn DataTable + TanStack Query useQuery hook
- [ ] View 4 `/admin/kb/[id]` KB detail page + KbConfig form
- [ ] View 4 PATCH wire to `PATCH /kb/{id}/settings`(C02 + C08)
- [ ] View 5 `/admin/kb/[id]/upload` multipart form to C01 ingestion endpoint
- [ ] pnpm lint + type-check clean
- [ ] Update `components/C09-admin-ui.md` status `v0-draft → v1-active`

## F10 — F2 + F7 unit tests retry(carry-over from W1,depends R8)

- [ ] **Pre-condition**:R8 mitigated(P1 VPN/hotspot OR P2 IT whitelist)
- [ ] `pip install -e backend[dev]` success
- [ ] `pytest tests/test_api_skeleton.py` → 8 smoke tests pass(unblock W1 F2 verification)
- [ ] `pytest tests/kb_management/` → CRUD unit tests pass(unblock W1 F7 unit tests)
- [ ] Coverage ≥ 80% on F2/F7 modules per CLAUDE.md H6
- [ ] Update C02 + C08 design notes status to `v2-stable`

## F11 — W2 末 retro + W3 kickoff prep

- [ ] W02 progress.md retro section completed(per `_templates/phase/progress.md.tpl`)
- [ ] Gate 1 verdict explicit + analysis if fail
- [ ] W03 phase folder mkdir + plan.md draft(per PROCESS.md §2.3 kickoff lifecycle)
- [ ] W03 carry-overs documented
- [ ] W02 progress.md frontmatter status flipped to `closed`

---

## Cross-Cutting

- [ ] Each commit references `progress.md` Day-N entry(R2)
- [ ] Component tag in commit message per CC-1(`feat(scope): description (Cn)`)
- [ ] All architectural-adjacent decisions documented as ADR(per CLAUDE.md §5.1 H1)— W2 暫無 expected
- [ ] OQ status sync to `decision-form.md`(R4)— Q19 W2 D3,Q5 W2 末 if Path A/B decided
- [ ] Component design note status bumps(per CC-5)
- [ ] RISK_REGISTER.md update if R8 mitigation lands or new risk surfaces
- [ ] `progress.md` retro section written W2 D5 末
- [ ] `progress.md` frontmatter status flipped to `closed`
- [ ] Phase W03-chat-retrieval-citation kickoff trigger noted in retro

---

**Lifecycle reminder**:呢份 checklist 隨 plan deliverables 衍生。新加 deliverable 必須先入 plan + changelog,然後再加 checklist item。
