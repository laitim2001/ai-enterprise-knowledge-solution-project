# ADR-0033: Chunker low-value tuning — floor 100→60 + adjacent-short-merge post-process

**Date**: 2026-05-23
**Status**: Accepted
**Approver**: Chris(chat 2026-05-23「Approve as-is」)
**Phase context**: `W25-image-association-deep-fix` F1 deliverable
**Related**:
- ADR-0018 multi-KB kb_id propagation(per-KB index unchanged by this ADR)
- ADR-0024 unified application shell IA(unrelated;Frontend IA layer)
- Investigation memo `docs/03-implementation/image-chunk-retrieval-investigation-2026-05-23.md`

---

## Context

**Trigger**(BUG-009/010/011 closure cascade + investigation memo 2026-05-23):

BUG-009 + BUG-010 + BUG-011 cascade closed嗮 screenshot upload + counter + private-blob proxy + KB Images tab 真縮圖 render —— 但 chat 答案 citation **仍從未帶圖**。Investigation memo 2026-05-23 用 3 條 query 跨 2 sessions empirically establish 兩條 root cause hypotheses:

- **H1**:`sample-doc-with-image-1` 121 chunks 中 **72(60%)被 `low_value_flag=True` 掃中**;Azure Search server-side filter `enabled eq true and low_value_flag eq false`(`backend/retrieval/hybrid.py:4 + :41`)會 hard-filter 走低 score chunks → image-bearing chunks 機率上 token<100 floor → **從未進入 retrieval candidate pool** → LLM 完全睇唔到。
- **H2**(輔助):vocab-overlap 競爭 — TOC chunk「Contents」目錄一行就 condensed 「4. High-level architecture」phrase,密度高過 section 4 正文;即使 H1 closed,H2 仍可能令 image chunks 排得低。

**Spec baseline**(`architecture.md §3.3` chunking philosophy):
> "low_value_flag heuristic:chunk_token_count < 100(soft floor per spec)OR chunk title/text matches TOC pattern OR version statement"

100-token soft floor 喺 W1-W6 baseline period 由 Chris 設定,當時 eval set 用 6-sample subset。**W25 D0 empirical re-evaluation 揭示對真實 corporate docs(eg. DCE Integration Platform Implementation Plan.docx,26 頁,8 張 embedded images)100 太 aggressive** —— layout-aware section flush 喺 sub-heading 結尾 emit 短 chunk(eg. 「Deliverables」/「Exit criteria」呢類 30-50 token 嘅 sub-section bodies)會大量 trigger low_value。

**Code locus**(per W25 D0 R6 pre-active-flip recursive grep verification):

```python
# backend/ingestion/chunker/layout_aware.py:35
_TOKEN_LOW_VALUE_FLOOR = 100  # per architecture.md §3.3 soft floor

# backend/ingestion/chunker/layout_aware.py:69-73
def __init__(self, ..., low_value_floor: int = _TOKEN_LOW_VALUE_FLOOR) -> None:
    self.low_value_floor = low_value_floor

# backend/ingestion/chunker/layout_aware.py:208-216  ← short-chunk emission point
def _flush_text_section(self, acc, base_index):
    if not acc.paragraphs:
        return []
    return [self._build_text_chunk(acc, acc.paragraphs, acc.token_count, base_index)]
# ↑ Emits whatever's in accumulator regardless of size when heading changes / EOF

# backend/ingestion/chunker/layout_aware.py:271-280
def _is_low_value(self, title, body, token_count):
    if token_count < self.low_value_floor:    # ← FLOOR check
        return True
    for pat in _TOC_PATTERNS: ...
    for pat in _VERSION_PATTERNS: ...
    return False
```

W25 phase 嘅 Path III 解法要求 **完整解決圖文關聯問題**(per user chat 2026-05-23「我需要的是完整地解決圖片和文字內容的關聯問題」+ AskUserQuestion Path III pick)。**D3 chunker re-tune 屬呢條 chain 嘅根源修**,觸 CLAUDE.md §5.1 H1(改 `architecture.md §3.3` chunker behaviour)→ 必須寫 ADR。

---

## Decision

**Two-pronged**(per W25 plan §8 locked default Q3「兩樣都做」):

### (a) Lower `_TOKEN_LOW_VALUE_FLOOR` from 100 → 60

```python
# backend/ingestion/chunker/layout_aware.py:35
_TOKEN_LOW_VALUE_FLOOR = 60  # per ADR-0033, lowered from 100 (W25 D3)
```

**Rationale**:60% low_value ratio on a representative corporate docx = empirical signal that 100 too aggressive。60 留低 ~30-50 token sub-section bodies(典型「Deliverables」/「Exit criteria」content)while still filtering真正 trivial 嘅 ≤60 token orphans(eg. floating「Page break」style fragments)。

### (b) Add `_merge_adjacent_shorts` post-process pass

```python
# backend/ingestion/chunker/layout_aware.py — new module-level constant
_MIN_CHUNK_MERGE_FLOOR = 160  # threshold below which adjacent text chunks consolidate
```

**Mechanism**(post-process,**after** main event loop emits raw chunks,**before** `LayoutAwareChunker.chunk` returns):

1. Walk emitted `chunks: list[ChunkSpec]` sequentially
2. For each adjacent pair `(prev, curr)`:
   - **Skip** if either is `chunk_kind == "table"`(tables stay independent per `architecture.md §3.3`「table 獨立 chunk」)
   - **Skip** if `chunk_index` not sequential(safety against existing logic that may interleave indices)
   - **Skip** if either `chunk_token_count >= _MIN_CHUNK_MERGE_FLOOR`(neither is short enough to need merge)
   - **Skip** if `combined token_count > self.hard_cap_tokens`(don't break hard cap)
   - **Merge**:concat text(`"\n\n".join`)+ sum tokens(re-encode for accuracy)+ concat `embedded_image_positions` + re-compute `low_value_flag` per combined content + keep `prev` 嘅 `section_path` / `chunk_title` / `heading_anchor`(因為 merge backward)
3. Re-index resulting chunks 0..N-1 contiguous

**Why post-process not embedded in main loop**:
- Main event loop algorithm complexity already non-trivial(heading stack + tables interleaving + image attach by doc_order);加 merge logic 入去會 mix concerns
- Post-process 易單元測試(input ChunkSpec list → output merged list,pure function over ChunkSpec)
- 易 disable for A/B(comment out the merge call,recover pre-ADR behaviour)

### (c) Spec amendment

`architecture.md §3.3` inline-tagged amendment(per W17 precedent — doc version not bumped, ADR is the record):
- Original「`chunk_token_count < 100`(soft floor per spec)」→ updated「`chunk_token_count < 60`(lowered W25 per ADR-0033)」
- Add note about adjacent-short-merge post-process

---

## Alternatives Considered

1. **Floor adjustment only(100 → 60)**
   - Pros:simplest change(one constant);easy to A/B
   - Cons:**doesn't consolidate** short-section emissions —— 60% flagged ratio 雖然會降,但 chunker stress signal underlying「太多 short sub-section flushes」未解;image-bearing chunks 仍可能 land 50-60 token range marginal zone
   - Rejected because **partial fix not aligned with user「完整解決」framing**

2. **Adjacent-short-merge only(keep floor 100)**
   - Pros:沒有改 `§3.3` 100-floor cite,less spec drift
   - Cons:merge 後嘅 100-159 token chunks 仍 flag low_value(花咗 effort 但個 chunks 仍 filter 走);無解決真正 60-99 token image chunks 嘅 visibility
   - Rejected because **doesn't address H1 root cause**(low_value filter scope)

3. **Combined floor + merge(this ADR)**
   - Pros:floor relaxation reclaim 60-99 token image chunks + merge 解 30-60 token orphans;**both sides of the 60% stress signal addressed**
   - Cons:two changes 一次過 land,Gate 1 R@5 regression 風險疊加(需 phase verify);merge_floor=160 係 heuristic empirical adjust
   - **Selected**:aligned with user「完整解決」+ W25 Path III scope;single ADR reduces ADR sprawl

4. **Image-bearing-skip-low-value retrieval rule**(exempt chunks with `embedded_images_json` from low_value filter)
   - Pros:tightly targeted to image-association problem
   - Cons:**chunker emit chunks before retrieval sees them — image association 係 chunker structural property**;改 retrieval filter 屬 retrieval-side mitigation 唔解 chunker stress
   - **Deferred to D2(CH-003)**:orthogonal to D3 chunker re-tune;F5 phase deliverable

5. **Increase `_TOKEN_TARGET`(500 → 800)** to encourage larger chunks
   - Pros:fewer chunks emitted → fewer short ones
   - Cons:`target_tokens` 已 balance「answer relevancy vs context」;raising 可能 degrade Faithfulness gate(LLM hallucination 風險 within larger context);**唔係 the right lever for image-association problem**
   - Rejected

6. **Eliminate low_value flag entirely**
   - Pros:trivial removal
   - Cons:TOC + version-statement filtering 仍有 clear positive value(W2 D5 hand-eyed observe 過 — Contents 目錄 / 版本 statement chunks 確實係 noise 對 BM25)
   - **100-token floor 係 specific stress signal,not whole heuristic**;rejected

---

## Consequences

### Positive
- **Image-bearing chunks more likely 進入 retrieval candidate pool** → reach LLM → reach citation(W25 Phase Gate G1 target)
- **60% low_value ratio 預期降至 ~30-40%** — chunker stress signal 緩解
- **General corpus quality improvement** — 不單 image chunks 受惠,所有 short-section content(eg. exit criteria / acceptance criteria / numbered list items)變得 retrievable
- **Tier 1 scope contained** — chunker code change only,no new dependency,Azure Search index schema unchanged,ParserResult / ChunkSpec interface unchanged

### Negative
- **Gate 1 R@5 baseline 必須 re-verify**(W2 D5 0.9722 → W25 F2 expected R@5 ≥ 0.92 per Phase Gate G2 5pp envelope)
- **Re-ingest required** for all KBs that want the new chunking(per W25 plan §8 default Q2 — dev-only re-ingest,Beta-track 留 W16 Track A)
- **`merge_floor = 160` 係 heuristic** — empirical adjust 可能 needed per F4 verify;若 merge 過 aggressive(content lose discrimination)→ raise to 200;若 merge 過 conservative(short chunks 仍 low_value 太多)→ lower to 120
- **Chunk count drop** — `sample-doc-with-image-1` 121 → expected ~80-100 per merge consolidation(F1 unit test enforce ≤ ±20% envelope)

### Neutral
- ChunkSpec dataclass interface unchanged — `chunk_index` re-indexed post-merge but field type / shape identical
- BM25 + embedding pipeline downstream 不受影響(chunks 仍 emit 同一 schema)
- Pre-existing chunker test cases majority 仍 pass(假設 6-sample W2 corpus 唔重 trigger merge — merge 主要 affect long-tail short sub-sections)
- `embedded_image_positions` merge correctly preserves all positions across merged chunks

---

## Implementation Mapping

Mapped 1-to-1 to W25 plan F1.2 checklist items:

| Plan checklist | ADR section |
|---|---|
| F1.2.1 — `_TOKEN_LOW_VALUE_FLOOR` 100 → 60 | Decision (a) |
| F1.2.2 — `_emit_chunk` adjacent-short-merge post-process | Decision (b) |
| F1.2.3 — `_TOC_PATTERNS` + version-statement rules unchanged | implicit — Decision constrains scope to floor + merge only |
| F1.2.4 — `mypy --strict` clean | implicit — type hints + slots preserve existing pattern |
| F1.3.1 — Floor edge case test(59/60/61)| Decision (a) test surface |
| F1.3.2 — Adjacent-short-merge test | Decision (b) test surface |
| F1.3.3 — 6-sample W2 corpus chunk count ≤ ±20% envelope | Negative consequences mitigation |

---

## References

- W25 plan.md F1 deliverable + §8 design defaults Q3
- Investigation memo `docs/03-implementation/image-chunk-retrieval-investigation-2026-05-23.md`
- `backend/ingestion/chunker/layout_aware.py:35` `_TOKEN_LOW_VALUE_FLOOR = 100`(W25 D0 R6 grep confirmed)
- `backend/ingestion/chunker/layout_aware.py:208-216` `_flush_text_section`(short-chunk emission point)
- `backend/ingestion/chunker/layout_aware.py:271-280` `_is_low_value`(floor check)
- `backend/retrieval/hybrid.py:4 + :41` `_DEFAULT_FILTER = "enabled eq true and low_value_flag eq false"`(downstream filter that motivates this ADR)
- `architecture.md §3.3` chunking philosophy(soft floor cite — to be inline-tagged amended on ADR-0033 acceptance)
- CLAUDE.md §5.1 H1 architectural change trigger(chunker behaviour ⊂ §3 RAG core component)
- CLAUDE.md §10 R6 pre-active-flip recursive grep verification(applied at W25 D0 — caught the floor constant location + filter mechanism upfront)
- Memory `feedback_design_fidelity.md` D9 plan-text-contamination pattern(R6 motivator)

---

**End of ADR-0033**

> **Lifecycle**:Status `Proposed → Accepted` on Chris approval(W25 F1.1.2 gate);spec amendment in `architecture.md §3.3` applied on Acceptance(W25 F7.2.1);code change executed per F1.2 checklist items after Acceptance。
