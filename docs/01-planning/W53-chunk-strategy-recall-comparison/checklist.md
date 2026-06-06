# W53 — Chunk-Strategy Recall Comparison · Checklist

> Atomic items per deliverable。不可刪未勾項(只 `[x]` 或標 🚧 + reason)。
> **heading_aware 改 chunking = H1 → ADR-0044 必寫**;**reuse W52 `run_synthetic_recall`**(零新 recall 數學)+ LayoutAwareChunker 基礎設施;**per-config 重生 QA = self-retrievability 非 controlled A/B** 誠實 framing(R1/R2);**H6** chunker + harness 同步 test。

## F0 — Phase kickoff
- [x] F0.1 plan/checklist/progress committed(R1);scope(heading_aware 真 strategy / per-config 重生 QA self-retrievability / 三 R6 發現)+ key design 鎖定;R6 grep 記 progress

## F1 — ADR-0044
- [x] F1.1 `docs/adr/0044-heading-aware-chunk-strategy.md`(Context 三 R6 發現;Decision heading_aware section-bounded 語意[target=hard_cap + min_merge=0 thin subclass] + _select_chunker dispatch;Alternatives 6;Consequences;References);Status=Accepted
- [x] F1.2 ADR README index 加 0044 row + next NNNN → 0045

## F2 — heading_aware chunker + chunk_strategy wiring(C01)
- [x] F2.1 `HeadingAwareChunker(LayoutAwareChunker)` thin subclass(`backend/ingestion/chunker/heading_aware.py`)— super().__init__ 後 flip `target_tokens=hard_cap_tokens` + `min_chunk_merge_floor=0`;其餘(hard_cap split / image-cap / table / low_value / section-walk)全 inherit;接 max_images_per_chunk
- [x] F2.2 `strategies.py select_chunker`:heading_aware → HeadingAwareChunker()(移除 NotImplementedError;module docstring bullet 同步更新)
- [x] F2.3 `documents.py _select_chunker`:按 kb_config.chunk_strategy dispatch(heading_aware → HeadingAware(cap inherit/override);else → LayoutAware path bit-identical fall-through)→ reindex 真 honor strategy(close W46 over-promise gap)
- [x] F2.4 ruff check+format clean;mypy --strict 我兩改檔(heading_aware.py/strategies.py)零 error(exit 1 純 layout_aware:114/170 + parser 檔 pre-existing 跨模組);test_parser_factory regression-fix(NotImplementedError 斷言 → HeadingAwareChunker + policy params);chunker/parser/reindex/detail/effective_config 65 passed 0 regression

## F3 — Strategy-recall 比較 harness + CLI(C06)
- [x] F3.1 NEW `backend/eval/strategy_comparison.py`:`run_strategy_recall_comparison(kb_id, strategies, *, reindex_with_strategy_fn, recall_fn, top_k)` → `StrategyRecallComparison`(per strategy recall + chunk 數 + sample 數 + errored;best=最高 self-retrievability);依賴注入(reindex_with_strategy_fn / recall_fn)
- [x] F3.2 thin CLI `scripts/run_strategy_recall_comparison.py`(bootstrap `async with lifespan(app)` 攞 populated state + Request shim 餵 run_kb_reindex;wire update_config→reindex→run_synthetic_recall;live smoke-deferred)
- [x] F3.3 ruff clean;mypy --strict strategy_comparison.py 零 error(exit 純跨模組 pre-existing)

## F4 — Tests(H6)+ Doc-sync + closeout
- [x] F4.1 test `test_heading_aware_chunker.py`:no-sub-target-split(heading 1 chunk < layout ≥2)+ no-merge(tiny siblings layout 1 merged vs heading 2)+ hard_cap 仍 split + image-cap force-split 繼承(cap 8,≤8/chunk)
- [x] F4.2 test:`_select_chunker` dispatch 5 case(heading_aware → HeadingAwareChunker / +cap override / layout_aware → singleton 非 HeadingAware / auto+cap → factory / None → singleton)
- [x] F4.3 test `test_strategy_comparison.py`:`run_strategy_recall_comparison` stub reindex+recall → 比較報告正確 assemble + best pick + empty case
- [x] F4.4 0 regression:test_heading_aware_chunker+test_strategy_comparison+test_parser_factory+test_chunker **49 passed**;kb_reindex+synthetic_qa+eval_runner+W53 **34 passed**
- [x] F4.5 Doc-sync:architecture.md §5.5.5 W53 amendment(標明 chunker 改動屬 §3.3/§3.5 per ADR-0044)+ ADR-0044 cross-ref;eval-methodology.md §10.6 per-config confounding note;roadmap line 112 → ✅ W53 shipped + 修訂史;session-start §10 W53 closed row + W54+(local-only);plan status→closed + changelog
- [x] F4.6 Phase Gate G1-G5 = **PASS** + retro + carry-overs(W54)+ R5 recheck(有 §3/§4 touch → ADR-0044 已寫)+ checklist 全 tick(無 🚧)
