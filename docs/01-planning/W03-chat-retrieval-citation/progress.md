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
| _pending_ | `feat(c01): F5 PPT parser scaffold + 9 unit tests (W3 D1 — F1 Cohere blocked Q5)` |

---

## Day 2 — 2026-05-09 (Sat)

_(同上)_

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
