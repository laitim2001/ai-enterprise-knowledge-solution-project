# W51 — Config-Test Completeness Proxy · Checklist

> Atomic items per deliverable。不可刪未勾項(只 `[x]` 或標 🚧 + reason)。
> **F2 frontend = H7 design-first**(mockup 先改再 match);**reuse 既有 `MetricBand`/`_band` 不另造**;**proxy 非 recall** 誠實 framing(R1)。

## F0 — Phase kickoff
- [ ] F0.1 plan/checklist/progress committed(R1);scope(proxy 非 recall / per-run band / Tier 1)+ key design 鎖定;R6 grep 記 progress

## F1 — Backend:distinct-sections per-run band
- [ ] F1.1 `RunMetrics` 加 `distinct_sections: int`
- [ ] F1.2 `ConfigRunSummary` 加 `distinct_sections: MetricBand`
- [ ] F1.3 `_run_n` 主 loop 逐 run `len({tuple(c.section_path) for c in resp.citations})` → RunMetrics + `_band([float(m.distinct_sections) ...])` 聚合
- [ ] F1.4 mypy --strict clean(我改動零 error)+ ruff check+format clean

## F2 — Frontend:涵蓋章節數 render + caveat 更新(H7 design-first)
- [ ] F2.1 mockup `ekp-page-kb.jsx` 先改:`KbTestResultCard` grid 加「涵蓋章節數」metric(band,近 引用數)+ 2 call site 加示例 distinct(DRAFT 多 sections / SAVED)
- [ ] F2.2 mockup W50 caveat note 更新:「對照引用數 / 字數」→「對照涵蓋章節數 / 引用數 / 字數」
- [ ] F2.3 `config-test.ts`:`RunMetrics` 加 `distinct_sections: number` + `ConfigRunSummary` 加 `distinct_sections: MetricBand`
- [ ] F2.4 `page.tsx` `ConfigResultCard` render 涵蓋章節數 metric(`fmt` + band)+ caveat 更新;100% match 更新後 mockup
- [ ] F2.5 tsc --noEmit clean + next lint clean(唯一 pre-existing chat `<img>` warning)+ `[oklch`=0 preserved

## F3 — Tests
- [ ] F3.1 backend:`_run_n` mock chunks(section_path ["Doc","A"]/["Doc","B"] = 2 distinct)→ `distinct_sections` band mean=2/band=0;核 RunMetrics distinct_sections present
- [ ] F3.2 backend:既有 config_test 10 + eval_ragas 7 = 17 0 regression
- [ ] F3.3 frontend vitest:`kb-settings-tuning` 試跑 test assert 涵蓋章節數 render;FAKE_RESULT draft/saved 補 `distinct_sections` band + `runs` entries distinct_sections;0 regression

## F4 — Doc-sync + closeout
- [ ] F4.1 architecture.md §5.5.5 加 W51 amendment(completeness proxy distinct-sections band;**標清 proxy 非 recall**)
- [ ] F4.2 roadmap 決策 7 Option (d) ideal 半邊 → ✅ done(distinct-sections proxy;synthetic-QA recall 留更未來)+ 修訂史 entry
- [ ] F4.3 session-start §10 W51 closed row + W52+ rolling JIT(local-only,gitignored)+ plan.md status→closed + changelog
- [ ] F4.4 Phase Gate G1-G4 = **PASS** + retro + carry-overs + checklist 全 tick(無 🚧)+ W52+ candidates
