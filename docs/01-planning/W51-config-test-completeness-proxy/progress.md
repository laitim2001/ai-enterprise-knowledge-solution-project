# W51 — Config-Test Completeness Proxy · Progress

> Daily progress + decisions + commits + 結尾 retro。每 daily commit 對應 Day-N entry(R2)。

---

## Day 1 — 2026-06-05

### Context / kickoff
W50 closed + pushed(`504bf07`,length-bias affordance 平 part)。用戶 pick W51 = **對沖指標**(決策 7 Option d ideal 半邊);C ingestion eval 留 W52。

### 決策
- **AskUserQuestion(W51 起點)**:Chris 揀 **對沖指標**(否決 C ingestion eval = 較大新 harness)。
- **Key design lock**(plan §2):completeness proxy = **distinct full section_path per run**(`len({tuple(c.section_path) for c in resp.citations})`)→ 沿用既有 `MetricBand` per-run band(零新 model)+ **誠實 framing**(label「涵蓋章節數」coverage proxy 非 recall — 無標註集真 recall 計唔到)+ frontend H7 design-first + 無新 ADR。synthetic-QA recall 留更未來。

### R6 grep 驗證(plan kickoff)
- `Citation.section_path: list[str]`(`schemas/query.py:41`)現成;`_run_n` 已用 `c.section_path`(per_citation last-run)→ per-run distinct 由 `resp.citations` 算。
- `MetricBand`(min/max/mean/band)+ `_band()` 現成 → proxy 沿用零新 model(同 W49 faithfulness band pattern)。
- **無 plan-text contamination**:plan 引用 function/field grep 對齊現 code(R6 recursive scope 過)。

### Done
- F0 R1 phase 三件套建立(plan/checklist/progress);Phase Gate G1-G4 定義

### F1 backend(同日)
- `schemas/config_test.py`:`RunMetrics` 加 `distinct_sections: int` + `ConfigRunSummary` 加 `distinct_sections: MetricBand`(docstring 標清 coverage proxy 非 recall)
- `routes/config_test.py` `_run_n`:主 loop 逐 run `distinct_sections = len({tuple(c.section_path) for c in resp.citations})` → RunMetrics;return 加 `distinct_sections=_band([float(m.distinct_sections) for m in metrics])`(沿用既有 `_band`,零新 helper)
- 驗:ruff check+format clean;mypy --strict 我兩個檔零 error(exit 1 純跨模組 pre-existing)

### F2 frontend(同日,H7 design-first)
- mockup `ekp-page-kb.jsx` 先改:`KbTestResultCard` signature 加 `sec`/`secBand`;grid 加「涵蓋章節數」metric(擺 引用數 後,coverage 訊號群組喺 faithfulness 下)+ sub「completeness proxy · 非 recall」(誠實 framing R1);2 call site 加 sec/secBand 示例(DRAFT 1 / SAVED 5);W50 caveat 更新引用「涵蓋章節數」取代「將來 recall」
- `config-test.ts`:`RunMetrics` 加 `distinct_sections: number` + `ConfigRunSummary` 加 `distinct_sections: MetricBand`(docstring 標清非 recall)
- `page.tsx` `ConfigResultCard`:加「涵蓋章節數」`<ConfigMetric>`(`fmt(summary.distinct_sections)` + band + sub)+ caveat span 更新 match mockup
- 驗:tsc --noEmit clean + next lint clean(唯一 pre-existing chat `<img>`)+ `[oklch`=0

### F3 tests(同日)
- backend `test_config_test_route.py`:`_multi_run_counts_and_band` 加 distinct_sections 斷言(mock chunk-a [Doc,A] + chunk-b [Doc,B] = 2 distinct → r0 distinct_sections=2 / band mean=2/band=0)
- frontend `kb-settings-tuning.test.tsx`:FAKE_RESULT draft/saved summary 加 `distinct_sections` band(draft 1 / saved 5)+ 主 A/B test 加 `getAllByText('涵蓋章節數').length >= 2`
- 驗:backend **pytest 17 passed**(config_test 10 + eval_ragas 7)0 regression;frontend **kb-settings-tuning 4 passed**(含新斷言)+ kb-detail/reindex 5 passed(0 regression)

### F4 doc-sync(同日)
- architecture.md §5.5.5 加 **W51 amendment**(涵蓋章節數 distinct-sections band;coverage proxy 非 recall;synthetic-QA recall 留更未來)+ 順手縮短 W50 amendment 嘅 caveat 引文(W51 已改 caveat 文案,避 stale quote)
- roadmap:W49 bullet (d) → ✅ W51 shipped(ideal 半邊);修訂史加 2026-06-05 W51 entry
- session-start §10 W51 closed row + plan.md status→closed + changelog

### Phase Gate G1-G4 — **PASS**

| # | Criterion | Verdict | Evidence |
|---|---|---|---|
| G1 | config-test 返 distinct-sections completeness proxy band | ✅ PASS | `_multi_run_counts_and_band` distinct_sections=2 / band mean=2/band=0(A/B 各一 MetricBand)|
| G2 | frontend render 涵蓋章節數 + caveat 指向佢 100% match mockup | ✅ PASS | design-first mockup KbTestResultCard grid metric → page.tsx ConfigResultCard match;vitest `getAllByText('涵蓋章節數')≥2`;caveat span 同步 |
| G3 | proxy framing 誠實(coverage 非 recall)| ✅ PASS | label「涵蓋章節數」+ sub「completeness proxy · 非 recall」+ schema/TS docstring 標明非 ground-truth recall |
| G4 | pytest+ruff+mypy+tsc/lint clean;0 regression;無新 ADR/vendor | ✅ PASS | backend 17 pass + ruff + mypy(我兩檔零 error);frontend vitest 4 + kb-detail/reindex 5 + tsc + lint;無新 dep/ADR |

**判決:Phase Gate 通過(PASS)**。決策 7 Option (d) ideal 半邊 done;用戶試跑而家見到量化 completeness 訊號(涵蓋章節數)擺 faithfulness 旁 → 直接判讀 length-bias trade-off。

### Retro
- **誠實 framing 守得住(R1)**:distinct-sections 係 coverage proxy 非 ground-truth recall(無標註集真 recall 計唔到)→ label「涵蓋章節數」+ sub「非 recall」+ schema/TS docstring 三處標明,唔 over-claim。synthetic-QA 真 recall 留更未來,唔強塞。
- **Karpathy simplicity / zero-new-model**:R6 grep 早發現 `Citation.section_path` + `MetricBand`/`_band` 現成 → distinct-sections 沿用既有 band pattern(同 W49 faithfulness 一脈),backend 改動極窄(1 schema 欄 ×2 + 1 loop 行 + 1 return 行)。
- **W49/W50/W51 三期一脈**:W49 揭噪音(band)→ W50 教育(length-bias caveat)→ W51 量化(涵蓋章節數 proxy)。三層遞進收齊決策 7(Option 1 + d 平/ideal 兩半)。
- **caveat 連鎖更新**:W51 改 caveat 指向涵蓋章節數 → 順手縮短 architecture.md W50 amendment 嘅 caveat 引文(避免 doc stale quote)。
- **Watch(carry W52+)**:synthetic-QA 真 recall(無標註集 → 生成 QA proxy,較重);distinct-sections proxy 對某些 query 敏感度屬後評;C ingestion 質素 eval(W51 揀 對沖指標時 defer)。

### Carry-overs → W52+(rolling JIT)
- C. ingestion 質素(reindex→eval,新 harness;W51 揀對沖指標時 defer)
- faithfulness **synthetic-QA 真 recall**(決策 7 Option d 更深半邊:無標註集 → 生成 QA pair 量 recall,較重)
- (前期 carry 不變)per-document scope(決策 1 + AUDIT-E)/ AUDIT-D (ii) correctness+context_recall / production v1→v2(Track A 決策 4)/ presets+config 版本史(決策 5)/ Layer C 視覺內容揀圖(Tier 2 決策 3)/ heading_aware footgun

### Commits
- `60856bc` F0 kickoff + `ff8657a` F1-F3 code+tests + F4 closeout commit(pending)

### Blockers / carry-over
- 無 blocker。infra 已起(azurite 23252 / backend 8000 **跑緊 W49 code,W51 改動未 reload** / frontend 46364 clean .next)。**注**:要 live 驗 W51 涵蓋章節數 需 restart backend(同 W48→W49)。
