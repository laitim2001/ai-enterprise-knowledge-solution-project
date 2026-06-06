# W51 — Config-Test Completeness Proxy · Checklist

> Atomic items per deliverable。不可刪未勾項(只 `[x]` 或標 🚧 + reason)。
> **F2 frontend = H7 design-first**(mockup 先改再 match);**reuse 既有 `MetricBand`/`_band` 不另造**;**proxy 非 recall** 誠實 framing(R1)。

## F0 — Phase kickoff
- [ ] F0.1 plan/checklist/progress committed(R1);scope(proxy 非 recall / per-run band / Tier 1)+ key design 鎖定;R6 grep 記 progress

## F1 — Backend:distinct-sections per-run band
- [x] F1.1 `RunMetrics` 加 `distinct_sections: int`
- [x] F1.2 `ConfigRunSummary` 加 `distinct_sections: MetricBand`(docstring 標清 coverage proxy 非 recall)
- [x] F1.3 `_run_n` 主 loop 逐 run `len({tuple(c.section_path) for c in resp.citations})` → RunMetrics + `_band([float(m.distinct_sections) ...])` 聚合
- [x] F1.4 mypy --strict clean(我兩個檔零 error;exit 1 純跨模組 pre-existing)+ ruff check+format clean

## F2 — Frontend:涵蓋章節數 render + caveat 更新(H7 design-first)
- [x] F2.1 mockup `ekp-page-kb.jsx` 先改:`KbTestResultCard` signature 加 `sec`/`secBand` + grid 加「涵蓋章節數」metric(band,引用數 後)+ sub「completeness proxy · 非 recall」+ 2 call site(DRAFT sec 1 / SAVED sec 5)
- [x] F2.2 mockup W50 caveat note 更新:「對照引用數 / 字數(+ 將來 recall)」→「對照涵蓋章節數 / 引用數 / 字數」+ 「高涵蓋章節數」入 bias 條件
- [x] F2.3 `config-test.ts`:`RunMetrics` 加 `distinct_sections: number` + `ConfigRunSummary` 加 `distinct_sections: MetricBand`(docstring 非 recall)
- [x] F2.4 `page.tsx` `ConfigResultCard` 加「涵蓋章節數」`<ConfigMetric>`(`fmt` + band + sub)+ caveat span 更新 match mockup
- [x] F2.5 tsc --noEmit clean + next lint clean(唯一 pre-existing chat `<img>` warning)+ `[oklch`=0 preserved

## F3 — Tests
- [x] F3.1 backend:`_multi_run_counts_and_band` 加 distinct_sections 斷言(mock [Doc,A]/[Doc,B] = 2 → r0 distinct_sections=2 / band mean=2/band=0)
- [x] F3.2 backend:既有 config_test 10 + eval_ragas 7 = **17 passed** 0 regression
- [x] F3.3 frontend vitest:`kb-settings-tuning` 主 A/B test `getAllByText('涵蓋章節數') ≥2`;FAKE_RESULT draft/saved summary 補 `distinct_sections` band(draft 1 / saved 5)→ **4 passed** + kb-detail/reindex 5 passed

## F4 — Doc-sync + closeout
- [x] F4.1 architecture.md §5.5.5 加 W51 amendment(completeness proxy distinct-sections band;**標清 proxy 非 recall**)+ 縮短 W50 amendment caveat 引文(避 stale quote)
- [x] F4.2 roadmap W49 bullet (d) → ✅ W51 shipped(ideal 半邊;synthetic-QA recall 留更未來)+ 修訂史 entry
- [x] F4.3 session-start §10 W51 closed row + W52+ rolling JIT(local-only,gitignored)+ plan.md status→closed + changelog
- [x] F4.4 Phase Gate G1-G4 = **PASS** + retro + carry-overs + checklist 全 tick(無 🚧)+ W52+ candidates
