---
phase: W03-chat-retrieval-citation
plan_ref: ./plan.md
checklist_ref: ./checklist.md
status: draft     # draft → in-progress → closed
---

# Phase W03 — Progress

> Daily progress + 結尾 retro。
> 每 commit 必須對應一個 Day-N entry mention(R2 binding rule per PROCESS.md §5)。
> Status:`draft` 直到 W2 D5 closeout sign-off + Gate 1 verdict pass。

---

## Day 0 — 2026-05-07: Kickoff prep(W2 D5 末 same-session draft)

**Action**:Phase W03 kickoff prep(per PROCESS.md §2.3 rolling-JIT lifecycle + W2 D5 closeout 同 session)

- Folder `docs/01-planning/W03-chat-retrieval-citation/` created
- Templates copied from `_templates/phase/`(v2.0 unified naming)
- `plan.md` filled with status=`draft`(10 deliverables F1-F10,Cohere Rerank + GPT-5.5 synthesis + SSE streaming + Chat UI + PPT parser + Pipeline wizard + Settings tab + retro)
- `checklist.md` derived from plan deliverables(~70 atomic items)
- `progress.md` Day 0 entry initialized(this file)
- **Carry-over candidates from W02-foundation**(pending Gate 1 verdict + W2 D5 closeout final retro):
  - F7 live Gate 1 eval — pending R8 VPN disconnect(if W2 closes mid-session,W3 D1 morning carries through)
  - F8 ground truth chunk_id discovery + SME validation — Chris async work,W3 D1+ ongoing
  - F3 R12 Azurite — image upload still defer until W7+
  - F1 (W3) Q5 Cohere procurement Path A vs B decision — Chris W3 D1 critical

**Status update will follow at W2 D5 closeout**(Chris approve flip `draft → active` after Gate 1 pass)。If Gate 1 fail → W3 plan **does not flip active**;HALT POC per architecture.md §6.3,foundation iteration loop replaces W3。

---

## Day 1 — 2026-05-04 (Mon — early start same-day W2 closeout 後段)

> Per W2 D5 cont 後段 closeout(2026-05-04)pre-fly:F1 Cohere blocked on Q5 procurement(Chris async),F5 PPT parser independent and able to start。Started F5 only — F2-F4 / F6-F9 await Q5 + Chris signoff to begin sequencing。

### Done

#### F5 — `.pptx` parser(python-pptx)— scaffold + unit tests

- `backend/ingestion/parsers/pptx_parser.py` ✅ NEW(per architecture.md §3.3 + components/C01-ingestion.md §1):
  - `PptxParser` class implements `Parser` Protocol(`base.py`)— `doc_format = "pptx"`、`parse(source) → ParserResult` deterministic + never raises
  - Slide-level structure mapping:per slide emit synthetic `"Slide N"` level=1 heading(stable section_path anchor for F2 chunker)+ title placeholder(if present)level=2 heading + body text frames + tables + pictures + speaker notes prefixed `[Notes] ...`
  - Picture extraction:`shape.shape_type == MSO_SHAPE_TYPE.PICTURE` → blob + ext + SHA256 dedup-ready
  - Table extraction:`shape.has_table` → `Table(headers=row[0], rows=row[1:], doc_order=...)`
  - `doc_order` monotonic across paragraphs / tables / images(F2 chunker contract per W2 design)
  - Edge cases:no-title slide(only Slide-N heading);picture without retrievable blob(skipped);malformed `.pptx`(`ParserResult(parse_failed=True)`)
- `backend/tests/test_pptx_parser.py` ✅ NEW — 9 tests pass:
  - 2-slide deck headings(level=1 Slide N + level=2 title)/ body text extract / speaker notes prefix / picture SHA256 + ext / table headers + rows / `doc_order` monotonic / no-title slide handling / malformed file fallback / Parser Protocol `doc_format` attribute
- Dependency:`python-pptx==1.0.2` already installed via W1 D2 batch(`pyproject.toml` deps,non new install)
- **Real-sample sanity report deferred**:Q2 PPT-share request from Chris pending(per W3 plan R6);once samples arrive可跑 `scripts/run_pptx_parser_sanity.py`(W3 D2-D3 scope alongside orchestrator wire)
- **Orchestrator integration deferred**(W3 D2-D3):`IngestionOrchestrator` parser registry needs `pptx → PptxParser()` entry + format auto-detect;呢個 step 同 F2 GPT-5.5 synthesis 同期做 makes sense(post Q5 path resolution)

#### Test suite

- **Full backend test suite 99/99 pass**(W2 baseline 90 + 9 NEW pptx parser);ruff clean

### Decisions / OQ Resolved

- **Decision** — F5 W3 D1 only(non F1-F4 / F6-F9 batch start)。Rationale:F1 Cohere blocks on Q5(Chris async procurement decision Path A vs B);F2-F4 / F6-F9 序列依賴 F1 + Chris W3 active flip signoff。F5 PPT parser purely additive(C01 expansion),independent of Q5 / chat path / generation pipeline → can land cleanly without prerequisite resolution。Per Karpathy §1.4 goal-driven:F5 acceptance(parser + 9 tests pass)well-defined and self-contained。
- **Decision** — F5 sanity report defer to W3 D2-D3:real PPT samples blocked on Q2(Chris share)。Synthetic fixture已 cover parser logic;real-sample variance(corporate template / SmartArt / linked content)留 W3 D2-D3 跟 sample arrival 一齊做。
- **Decision** — F5 orchestrator wire defer to W3 D2-D3:`pptx → PptxParser()` registry entry + format auto-detect 跟 F2 GPT-5.5 synthesis 同期 makes sense post-Q5。
- **No new OQ resolved**(Q5 Cohere仍 Open W3 D1 critical;Chris async)

### Blockers

- 🔴 **Q5 Cohere procurement Path A vs B** — F1 Cohere Rerank wire blocked;Chris W3 D1 critical decision per `decision-form.md` Q5
- 🟡 **Q2 PPT-share** — F5 sanity report deferred(non blocking F5 parser 落地;impact W3 D2-D3 polish + real-format variance verification)
- ✅ All other W2 D5 cont 後段 housekeeping cleared(99/99 tests + W2 closed + W3 active + ADR 0001-0011 + Q17/Q18 closed + R8 P2 limitation documented)

### Actual vs Planned Effort

| Item | Planned (h) | Actual (h) | Variance | Note |
|---|---|---|---|---|
| F5 PPT parser scaffold | 2.0 | 0.5 | -1.5h | python-pptx mature SDK + dataclass Parser contract = thin wrapper;mirrors docx_parser pattern |
| F5 unit tests(9 tests with synthetic fixture)| 1.0 | 0.5 | -0.5h | python-pptx 同時建 fixture + 解析,test self-contained |
| W3 D1 progress.md entry | 0.3 | 0.3 | 0 | First W3 entry,template-following |
| **Total D1** | **3.3** | **1.3** | **-2.0h** | F5 isolation = clean implementation;real-sample fanout move to D2-D3 |

### Commits

| Hash | Subject |
|---|---|
| `58690a4` | `feat(c01): F5 PPT parser scaffold + 9 unit tests (W3 D1 — F1 Cohere blocked Q5)` |

---

## Day 1 後段 — 2026-05-04 (Mon) — Chris 6-item signoff + F1 Cohere Path A scaffold + F5 real-sample sanity

> Same-day continuation after Chris signoff(W2 closeout review)。Chris confirmed:(1)Gate 1 PASS accepted for W3 unblock(SME-strict cascade non-blocking forward);(2)Q17/Q18 AI inference accepted as Chris-confirmed Resolved;(3)Q5 Cohere → Path A Azure Marketplace;(4)3 PPT samples uploaded;(5)W3 sequencing approved;(6)C09 W3 D5 polish bump approved。

### Done

#### Decision / OQ / Risk doc updates(Chris signoff log)

- **Q5 Cohere procurement → Path A Azure Marketplace**(`docs/decision-form.md`)。Procurement timeline 預期 7-14 工作日;W3 D1-D2 scaffold + procurement parallel
- **Q17 + Q18** Decided By updated `Dev(self,AI inferred)` → `Chris(confirmed 2026-05-04)`(`docs/decision-form.md`)。Status remains Resolved(content unchanged)
- **OQ Dashboard**:14 Open → **11 Open** post Q5 + Q17 + Q18 close;**12 Resolved**(was 9);Q5 = W3 D1 critical → Resolved
- **R3 Cohere Marketplace**:🟡 Active → 🟢 **Resolved 2026-05-04**(Path A;procurement parallel with W3 scaffold)。Index row + detail block both updated
- **Gate 1 PASS treatment**:Chris signoff explicit accepts current keyword-mode + validated=False as W3 unblock signal;SME-strict cascade non-blocking forward(W2 progress § Phase status decision noted in earlier same-day commits)

#### F1 — Cohere Rerank v3.5 scaffold(C04 expansion;W3 D1-D3 spread)

- `backend/retrieval/reranker/__init__.py` ✅ NEW package init
- `backend/retrieval/reranker/base.py` ✅ NEW — `Reranker` Protocol + `RerankedChunk` dataclass(rerank_score / hybrid_score / original_index preserved for trace)
- `backend/retrieval/reranker/cohere.py` ✅ NEW — `CohereReranker` REST client:
  - Async httpx client + tenacity retry on 5xx / TransportError
  - POST `{endpoint}/v2/rerank` with `{"model","query","documents","top_n"}` body
  - Response parses `results[].index` + `results[].relevance_score`,clamps invalid index,emits `RerankedChunk` desc by score
  - structlog event `cohere_rerank` with path / candidates_in / results_out for Langfuse correlation
  - Path A Marketplace endpoint(default)/ Path B direct API(config-flag selectable)— same body schema
- `backend/retrieval/reranker/factory.py` ✅ NEW — `make_reranker(settings) → Reranker | None`;returns None when `cohere_endpoint` 或 `cohere_api_key` 未 populate(allows hybrid-only fallback)
- `backend/storage/settings.py` updated:`cohere_endpoint`(NEW)+ `cohere_procurement_path`(Literal["A","B"],default A)+ `cohere_request_timeout_s`(default 10s)
- `backend/tests/test_reranker.py` ✅ NEW — 8 tests pass:
  - empty candidates → empty result + no API call
  - desc by relevance_score / preserves original_index + hybrid_score
  - payload shape(URL / model / query / documents / top_n)
  - top_n clamped to candidate count
  - invalid index in response skipped
  - factory returns None when endpoint OR key unset
  - factory returns CohereReranker when both populated + path arg propagated

**NOT yet wired into RetrievalEngine**(F1.7 deferred to W3 D2 post Chris .env populate Marketplace endpoint + key);wire-in 改 retrieval_engine.py 加 optional reranker dependency,`hybrid_top_k=50 → reranker.rerank → top_k=5`。

#### F5 — Real PPT sample sanity(unblock Q2)

Chris uploaded 3 .pptx samples to `docs/06-reference/01-sample-doc/`:`FY26 BP - DCE...pptx` / `FY26 BP Template V1 (1).pptx` / `FY26_Budget_Proposal_v2.pptx`。Inline sanity output:

| Sample | parse_failed | Slides | Paragraphs(headings/body)| Tables | Images |
|---|---|---|---|---|---|
| FY26 BP - DCE | False | 17 | 18 / 219 | 11 | 39 |
| FY26 BP Template V1 | False | 13 | 14 / 69 | 3 | 7 |
| FY26 Budget Proposal | False | 9 | 9 / 139 | 2 | 12 |

3/3 parse success;table + image extraction works on real corporate templates;synthetic-test corpus extends well to enterprise samples。Slide title coverage 2/3 samples(samples 1+2)— sample 3 has no title placeholders so only synthetic Slide-N headings emit(as designed)。

#### Test suite

- **Full backend test suite 107/107 pass**(99 → 107,+8 reranker tests);ruff clean

### Decisions / OQ Resolved

- **Q5 Resolved 2026-05-04 → Path A Azure Marketplace**(Chris signoff)— see decision-form + RISK_REGISTER R3 update
- **Q17 + Q18 Resolved 2026-05-04**(Chris confirm AI inference)— see decision-form
- **Decision** — F1 wire-into-RetrievalEngine deferred W3 D2 post .env populate。Rationale:scaffold + tests prove transport contract;wire 是 1-line dependency injection through RetrievalEngine constructor + 1 conditional in retrieve() — clean change once Marketplace endpoint + key available。Procurement async parallel keeps W3 D1 surgical
- **Decision** — Reranker factory returns `None` when not configured(non raise / warning)— allows hybrid-only baseline fallback for local dev / CI / unit tests not exercising rerank。RetrievalEngine W3 D2 wire 同樣 use `Optional[Reranker]` pattern
- **No new OQ resolved beyond the 3 closed today**

### Blockers cleared / remaining

- ✅ **Q5** Resolved Path A → F1 scaffold landed;wire-in pending Chris .env populate post Marketplace deploy
- ✅ **Q2 PPT-share** — 3 samples uploaded;F5 real-sample sanity outcome documented above
- ✅ **Gate 1 PASS treatment** — Chris explicit accepts W3 unblock
- ⏸ **Cohere Marketplace deploy** procurement(7-14d turnaround per Q5 timeline) — Chris async;F1 wire-in cascade post deploy

### Actual vs Planned Effort

| Item | Planned (h) | Actual (h) | Variance | Note |
|---|---|---|---|---|
| Decision / OQ / Risk doc updates(Q5 + Q17/Q18 + R3) | 0.5 | 0.4 | -0.1h | Surgical edits |
| F1 Cohere reranker scaffold(Protocol + REST + factory + settings) | 3.0 | 1.5 | -1.5h | Cohere REST API straightforward;httpx + tenacity 已熟 pattern from W2 |
| F1 unit tests(8 tests + factory tests) | 1.5 | 0.7 | -0.8h | AsyncMock + MagicMock pattern reuse from W2 populate test |
| F5 real-sample sanity(3 samples) | 0.3 | 0.2 | -0.1h | Inline command;parser robust |
| W3 D1 後段 progress.md entry | 0.5 | 0.5 | 0 | This entry + table |
| **Total D1 後段** | **5.8** | **3.3** | **-2.5h** | F1 isolation + scaffold-only scope kept session focused |

### Commits(D1 後段 batch)

| Hash | Subject |
|---|---|
| _pending_ | `docs(decision,risk): Q5 → Path A + Q17/Q18 Chris confirm + R3 Resolved (Chris signoff log)` |
| _pending_ | `feat(c04): F1 Cohere Rerank v3.5 scaffold + Reranker Protocol + factory + 8 tests (W3 D1 — Path A,wire deferred)` |
| _pending_ | `docs(planning): W3 D1 後段 progress entry + F5 real-sample sanity outcome (107/107 tests)` |

---

## Day 3 — 2026-05-10 (Sun)

_(同上)_

---

## Day 4 — 2026-05-11 (Mon)

_(同上)_

---

## Day 5 — 2026-05-12 (Tue)

_(同上 + retro draft 開始)_

---

## Retro(填於 W3 D5 末 / 2026-05-12)

### What worked
_(W3 D5 末 fill)_

### What didn't work / unexpected friction
_(W3 D5 末)_

### Surprises / discoveries
_(W3 D5 末)_

### Carry-overs to W04-crag-eval-shootout
_(W3 D5 末)_

### ADR triggers
_(W3 D5 末)_

### Phase Gate result(per plan.md §3)
- G1-G5:_(W3 D5 末)_

### Phase status
- Closeout commit:_(W3 D5 末)_
- Frontmatter status flipped to `closed`:_(W3 D5 末)_
- Phase W04 kickoff trigger:_(W3 D5 末)_

---

**End of W03 progress**(Day 0 prep stage,daily entries to follow W3 D1 onwards pending Gate 1 pass + Chris flip-active sign-off)
