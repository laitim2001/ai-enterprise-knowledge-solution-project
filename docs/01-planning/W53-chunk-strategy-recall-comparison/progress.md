# W53 — Chunk-Strategy Recall Comparison · Progress

> Daily progress + decisions + commits + 結尾 retro。每 daily commit 對應 Day-N entry(R2)。

---

## Day 1 — 2026-06-06

### Context / kickoff
W52 closed + pushed(`ef34692`,synthetic-QA recall 基建)。用戶 pick 兩者合一下半截 = **W53 chunk-strategy 比較**(用 W52 recall 跨 strategy)。

### 決策(AskUserQuestion 2026-06-06)
- **比較軸 = 實作 `heading_aware` 真 strategy**(Chris;否決 image-cap 軸[只 image-dense 有信號] + chunk-size plumbing[較大 scope])
- **Recall 方法學 = per-config 重生 QA**(Chris;否決 shared text-anchored controlled A/B[需新 keyword harness])→ 每 strategy reindex 後由自己 chunks 重生 synthetic QA 跑 W52 strict recall,直接 reuse `run_synthetic_recall`

### R6 grep 驗證(plan kickoff — 揭三個令字面前提唔成立嘅 code-reality)
1. **chunk_strategy degenerate**:`strategies.py` —— `auto`/`layout_aware`/`slide_based` 全 delegate LayoutAwareChunker;`heading_aware` raise NotImplementedError → 冇兩個唔同 strategy 可比 → **本期實作 heading_aware**。
2. **`_select_chunker`(documents.py:137-150)只睇 `chunker_max_images_per_chunk`,IGNORE chunk_strategy** → 即使實作 heading_aware,reindex(`run_kb_reindex`→`_run_ingest_pipeline`→line 615 `_select_chunker`)都唔用佢;W46 reindex docstring(line 749-751)「chunk_strategy change takes effect」係 over-promise → **本期補 wiring,順帶 close gap**。
3. **跨 reindex chunk_id 變** → W52 strict chunk_id recall 唔能跨 strategy reuse → **per-config 重生 QA 方法學解決**(每 strategy 用自己 index 量自己 chunks)。
- LayoutAwareChunker 旋鈕:`target_tokens`/`hard_cap_tokens`/`min_chunk_merge_floor`/`max_images_per_chunk`(`layout_aware.py:78-94`)→ heading_aware reuse section-walk + token + image-cap 基礎設施,只換 split/merge policy。
- 下一個 ADR = **0044**(接 chunker lineage 0041/0042/0043)。

### heading_aware 語意(ADR-0044 核心 — kickoff lock)
section-bounded:每 heading section 盡量一 chunk,只超 `hard_cap_tokens`(embedding 8191 安全)先 split,**無 target_tokens 平衡 split、無 min-merge** → vs layout_aware(target-balanced + merge)= 更粗/少 chunk。仍 honor image-cap force-split(保 W44 圖洪保護)。

### 誠實 framing(R1/R2)
per-config 重生 QA → 每 strategy 問題集唔同(自己 chunks 生)→ recall 差異含**問題難度 confounding** → 量度 **self-retrievability(自檢索性)非 controlled A/B**;且建基 W52 synthetic recall(非人手 ground truth)。報告/docstring/ADR 三處標清。

### Done(F0)
- F0 R1 phase 三件套建立(plan/checklist/progress);Phase Gate G1-G5 定義

### F1 ADR-0044(同日)
- `docs/adr/0044-heading-aware-chunk-strategy.md`(Context 三 R6 發現;Decision heading_aware section-bounded[target=hard_cap + min_merge=0 thin subclass] + _select_chunker dispatch;6 Alternatives;Consequences;References)Status=Accepted;README index + next NNNN → 0045

### F2 chunker + wiring(同日,C01)
- NEW `backend/ingestion/chunker/heading_aware.py`:`HeadingAwareChunker(LayoutAwareChunker)` thin subclass(super().__init__ 後 flip target_tokens=hard_cap + min_chunk_merge_floor=0;其餘全 inherit)
- `strategies.select_chunker`:heading_aware → HeadingAwareChunker(移除 NotImplementedError + docstring 同步);`documents.py _select_chunker`:按 kb_config.chunk_strategy dispatch(strategy≠heading_aware bit-identical fall-through)→ reindex 真 honor strategy(close W46 over-promise gap)
- test_parser_factory regression-fix(NotImplementedError 斷言 → HeadingAwareChunker + policy params);ruff clean;mypy 兩改檔零 error(exit 1 純 layout_aware:114/170 + parser pre-existing);chunker/parser/kb_reindex/detail/effective_config **65 passed** 0 regression

### F3 比較 harness + CLI(同日,C06)
- NEW `backend/eval/strategy_comparison.py`:`run_strategy_recall_comparison(kb_id, strategies, *, reindex_with_strategy_fn, recall_fn, top_k)` → `StrategyRecallComparison`(per strategy recall+chunk數+sample+errored;best=最高 self-retrievability);**reuse run_synthetic_recall 零新 recall 數學**;依賴注入
- CLI `scripts/run_strategy_recall_comparison.py`:`async with lifespan(app)` 攞 populated state + Request shim 餵 run_kb_reindex;wire update_config→reindex→synthetic recall(smoke-deferred)
- ruff clean;mypy strategy_comparison.py 零 error

### F4 tests(同日,H6)
- `test_heading_aware_chunker.py`:behavior 4(no-sub-target-split heading 1 < layout ≥2 / no-merge tiny siblings layout 1 vs heading 2 / hard_cap 仍 split / image-cap force-split 繼承 cap 8)+ dispatch 5(heading_aware→HeadingAware / +cap override / layout_aware→singleton 非 HeadingAware / auto+cap→factory / None→singleton)
- `test_strategy_comparison.py`:orchestration loop + report assemble + best pick + empty case
- 驗:heading/strategy/parser/chunker **49 passed**;kb_reindex/synthetic_qa/eval_runner/W53 **34 passed** = 0 regression

### F4 doc-sync(同日)
- architecture.md §5.5.5 NEW **W53 amendment**(heading_aware 真 strategy + chunk_strategy wiring + 比較 harness;標明 chunker 改動屬 §3.3/§3.5 per ADR-0044 + self-retrievability 非 controlled A/B)
- eval-methodology.md §10.6 加 **W53 per-config 重生 QA confounding note**(self-retrievability 非 controlled A/B)
- roadmap line 112 → ✅ W53 shipped + 修訂史 2026-06-06 W53 entry
- session-start §10 W53 closed row + W54+ rolling JIT row(local-only,不入 git)
- plan.md status→closed + changelog(含 F2 subclass 實作細節 deviation note)

### Phase Gate G1-G5 — **PASS**

| # | Criterion | Verdict | Evidence |
|---|---|---|---|
| G1 | heading_aware 真 chunker(section-bounded,明顯異於 layout_aware)| ✅ PASS | `test_no_sub_target_split`:heading 1 chunk < layout ≥2;`test_no_adjacent_merge`:tiny siblings layout 1 merged vs heading 2;image-cap force-split 繼承 |
| G2 | `_select_chunker` 真 honor chunk_strategy(reindex 用對 chunker)| ✅ PASS | dispatch 5 case test(heading_aware→HeadingAwareChunker / layout_aware→singleton 非 HeadingAware / cap combine)|
| G3 | 比較 harness 跨 strategy reuse W52 recall(零新 recall 數學)| ✅ PASS | `test_strategy_comparison`:stub reindex+recall → 報告 assemble + best pick;`run_strategy_recall_comparison` 直接 call run_synthetic_recall |
| G4 | self-retrievability framing 誠實(非 controlled A/B,建基 synthetic recall)| ✅ PASS | module docstring + dataclass + CLI output + eval-methodology §10.6 + arch/roadmap amendment 多處標明 |
| G5 | ADR-0044 written + pytest+ruff+mypy clean + 0 regression + 無新 vendor/dep | ✅ PASS | ADR-0044 Accepted;49+34 passed 0 regression;ruff clean;mypy 改檔零 error;無新 dep |

**判決:Phase Gate 通過(PASS)**。兩者合一下半截 done —— heading_aware 真 strategy(ADR-0044)+ chunk_strategy reindex wiring(close W46 gap)+ self-retrievability 比較 harness 落地。W52+W53 合成完整「per-config tunable config → synthetic recall 量度 → 跨 strategy 比較」鏈。

### R5 closeout recheck(§3/§4 touch?)
- **有 architectural touch → 已寫 ADR-0044**(H1):heading_aware 改 §3.3/§3.5 chunking 行為 + chunk_strategy ingest wiring。其餘(strategy_comparison.py = C06 eval;CLI = script)非 architectural。無其他未記 ADR 嘅 architectural 改動。

### Retro
- **think-before-coding 揭穿 degenerate 前提(§1.1 + R6 — 本期最大價值)**:W53 字面「跨 chunk_strategy 比較」其實三重唔成立(strategy degenerate / _select_chunker ignore strategy / chunk_id 跨 reindex 變)。kickoff R6 grep + AskUserQuestion surface 咗,先拍板再落 code,避免起一個 degenerate 誤導 harness。順帶發現 + close W46 reindex docstring over-promise gap。
- **Karpathy zero parsing rewrite**:heading_aware = LayoutAwareChunker subclass flip 2 個 policy knob(target=hard_cap + min_merge=0),而非全新 chunker —— section-walk/token/image-cap/table/low_value 全 reuse。「真 strategy class」(discoverable + 獨立 test)同最大 reuse 兼得。
- **誠實 framing 連續第三期守住(R1/R2)**:W51 proxy 非 recall → W52 synthetic 非人手 ground truth → W53 self-retrievability 非 controlled A/B。每期都明標限制,唔 over-claim;controlled A/B 留 W54。
- **bit-identical fall-through 保 0 regression**:_select_chunker strategy≠heading_aware 行原 path → test_kb_reindex/chunker 全綠(dispatch test 明確驗 layout_aware → singleton 非 HeadingAware)。
- **Watch(carry W54+)**:controlled shared-question A/B(text-anchored,嚴謹版);heading_aware live eval 對真 KB(smoke-deferred);heading_aware 對 image-dense doc 嘅 chunk 數變化(image-cap 主導 vs no-merge 主導,屬 live 後評)。

### Carry-overs → W54+(rolling JIT)
- **controlled shared-question A/B**(strategy-independent text-anchored ground truth + keyword-mode recall — W53 self-retrievability 嚴謹版,需新 harness)
- heading_aware **live eval 對真 KB**(smoke-deferred;judge cred + indexed KB + 原始檔 + 402 繞)+ chunk 數變化後評
- (前期 carry 不變)per-document scope(決策 1 + AUDIT-E)/ AUDIT-D (ii) correctness+context_recall(需人手標註集)/ production v1→v2(Track A 決策 4)/ presets+config 版本史(決策 5)/ Layer C 視覺內容揀圖(Tier 2 決策 3)/ heading_aware footgun

### Blockers / carry-over
- 無 blocker。live 比較 run 對 Azure 屬 smoke-deferred(judge cred + indexed KB + 原始檔 + Free-tier 402 繞;整合由 F4 stub 全測)。

### Commits
- `1cac9e6` F0 kickoff + `b94bffc` F1 ADR-0044 + `a9b635c` F2 chunker+wiring + `32c8147` F3-F4 harness+tests + F4 closeout commit(pending)
