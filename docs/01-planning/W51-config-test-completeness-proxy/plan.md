---
phase: W51-config-test-completeness-proxy
name: "Config-Test Completeness Proxy (distinct-sections band — 決策 7 Option d ideal 半邊)"
sprint_week: W51
start_date: 2026-06-05
end_date:                     # set at closeout
status: active
spec_refs:
  - ROADMAP-per-kb-tunable-config.md 決策 7 Option (d) ideal 半邊(completeness/recall 對沖指標)+ 證據②(faithfulness 同 completeness 反相關)
  - ADR-0040 (per-KB config-scope + config-test 雙軸)
  - architecture.md §5.5.5 (KB Detail Settings config-test 試跑 panel)
  - W49(faithfulness N-run band)+ W50(length-bias affordance — 本期補量化 completeness 訊號)
  - backend/api/routes/config_test.py + backend/api/schemas/config_test.py(_run_n + MetricBand + RunMetrics)
  - backend/api/schemas/query.py:41(Citation.section_path — proxy 資料來源)
prior_phase: W50-faithfulness-length-bias-affordance
---

# Phase W51 — Config-Test Completeness Proxy

> **Plan version**:1.0(initial)
> **Owner**:Chris(Tech Lead)
> **Approved by**:Chris(2026-06-05 AskUserQuestion:W51 起點 = **對沖指標**;C ingestion 質素 eval 留 W52)

## 1. Scope

收 **決策 7 Option (d) 嘅「ideal 半邊」**:W50 加咗 length-bias 文字 caveat(教育),但用戶仍只係靠 prose 對照 —— 無一個**量化嘅 completeness 訊號**擺喺 faithfulness 旁。本期加一個 **completeness proxy = 「涵蓋章節數」(distinct-sections-cited)per-run band**,令用戶**直接睇到** faithfulness↓ 但 completeness↑ 嘅 trade-off(證據②:RAGAs faithfulness 同完整性反相關),唔再淨係文字提醒。

**Proxy 定義**:每 run 答案引用嘅 **distinct section_path**(full tuple,即唯一葉章節)數量 —— breadth/coverage proxy(廣度,非深度;多 distinct sections = 答案橫跨更多文件章節 = 更完整)。沿用既有 `MetricBand`(同 presentation counters / W49 faithfulness 一致),per-run band。

**Scope kickoff R6 grep 已驗**:`Citation.section_path: list[str]`(query.py:41)現成;`_run_n` 已用 `c.section_path`(per_citation last-run);`MetricBand` + `_band()` 現成 → proxy 沿用零新 model;per-run distinct-sections 由 `resp.citations` 算(逐 run capture,非 last-run only)。

**Out-of-scope(誠實 + Karpathy simplicity)**:
- **true recall / synthetic-QA**:distinct-sections 係 **coverage proxy 非 ground-truth recall**(無標註集 → 真 recall 計唔到)。文案 / label 必須標清係 proxy,**唔可以 over-claim 做 recall**(對齊 R1)。synthetic-QA recall 留更未來。
- **ingestion 質素 eval**(C)→ W52 候選。
- per-document scope(決策 1)/ 其他前期 carry。
- judge LLM / faithfulness 計算(不動)。

**Sprint week origin**:roadmap 決策 7 Option (d) ideal 半邊;Chris 2026-06-05 pick(W50 closeout 後)。

## 2. Key Design Decisions(kickoff lock)

- **Proxy = distinct full section_path per run**:`len({tuple(c.section_path) for c in resp.citations})`。breadth proxy,沿用既有 `MetricBand`(零新 model)。
- **per-run band**(非 last-run only):同 W49 faithfulness / presentation counters 一致 —— `_run_n` 主 loop 逐 run 算 distinct → `_band`。
- **誠實 framing(R1)**:label「涵蓋章節數」(coverage)非「recall」;UI / 文案標清係 **completeness proxy**(廣度),非 ground-truth recall。
- **Frontend(H7 design-first)**:mockup 先改 → page.tsx match;涵蓋章節數 metric 擺 result card grid(近 引用數,同為 coverage 訊號)+ 更新 W50 caveat 引用佢(由「對照引用數/字數」→「對照涵蓋章節數/引用數/字數」)。
- **無新 ADR / vendor / dep**:extend 既有 config-test component + 既有 MetricBand;judge 不涉。

## 3. Deliverables

### F0 — Phase kickoff
- **Acceptance criteria**:plan/checklist/progress committed(R1);scope(proxy 非 recall / per-run band / Tier 1)+ key design 鎖定;R6 grep 記 progress
- **Owner**:AI

### F1 — Backend:distinct-sections per-run band
- **Spec ref**:`config_test.py` `_run_n` + `schemas/config_test.py`;reuse `MetricBand`/`_band`;`Citation.section_path`
- **Acceptance criteria**:
  - `RunMetrics` 加 `distinct_sections: int`
  - `ConfigRunSummary` 加 `distinct_sections: MetricBand`
  - `_run_n` 主 loop 逐 run `len({tuple(c.section_path) for c in resp.citations})` → RunMetrics + `_band([...])` 聚合
  - mypy --strict clean(我改動零 error)+ ruff check+format clean
- **Owner**:AI

### F2 — Frontend:涵蓋章節數 render + caveat 更新(H7 design-first)
- **Spec ref**:§5.5.5;mockup `ekp-page-kb.jsx` KbTestResultCard
- **Acceptance criteria**:
  - mockup `ekp-page-kb.jsx` 先改:`KbTestResultCard` grid 加「涵蓋章節數」metric(band,近 引用數)+ 2 call site 加示例 distinct;W50 caveat note 更新引用「涵蓋章節數」
  - `config-test.ts`:`RunMetrics` 加 `distinct_sections: number` + `ConfigRunSummary` 加 `distinct_sections: MetricBand`
  - `page.tsx` `ConfigResultCard` render 涵蓋章節數 metric + caveat 更新;100% match 更新後 mockup(H7 fidelity)
  - tsc --noEmit clean + next lint clean + `[oklch`=0 preserved
- **Owner**:AI

### F3 — Tests
- **Acceptance criteria**:
  - backend:`_run_n` mock chunks(2 distinct section_path)→ `distinct_sections` band(mean 2 / band 0);既有 config_test test 0 regression
  - frontend vitest:`kb-settings-tuning` 試跑 test assert 涵蓋章節數 render;FAKE_RESULT 補 distinct_sections band;0 regression
  - 既有 backend 17 + frontend 0 regression
- **Owner**:AI

### F4 — Doc-sync + closeout
- **Acceptance criteria**:
  - architecture.md §5.5.5 加 W51 amendment(completeness proxy distinct-sections band;標清 proxy 非 recall)
  - roadmap 決策 7 Option (d) ideal 半邊 → ✅ done(distinct-sections proxy)+ 修訂史 entry
  - session-start §10 W51 row + plan.md status→closed + changelog
  - Phase Gate G1-G4 + retro + carry-overs + checklist tick / 🚧
- **Owner**:AI

## 4. Success Criteria(Phase Gate)

| # | Criterion | Target | Measure | Block closeout? |
|---|---|---|---|---|
| G1 | config-test 返 distinct-sections completeness proxy band | `MetricBand` on summary(A/B 各一)| pytest + manual | Yes |
| G2 | frontend render 涵蓋章節數 + caveat 引用佢 100% match mockup | H7 fidelity | mockup 對齊 + vitest | Yes |
| G3 | proxy framing 誠實(label coverage 非 recall)| UI/文案 review | review | Yes |
| G4 | pytest + ruff + mypy + tsc/lint/build clean;0 regression;無新 ADR/vendor | all green | CI commands | Yes |

## 5. Risks(Phase-Specific)

| # | Risk | Likelihood | Impact | Mitigation |
|---|---|---|---|---|
| R1 | over-claim distinct-sections 做 recall(誤導)| Med | High | label「涵蓋章節數」(coverage proxy)非 recall;UI/文案/docstring 標清係廣度 proxy 非 ground-truth recall |
| R2 | distinct-sections 對某些 query 唔敏感(coverage 訊號弱)| Low | Low | 本期交付 proxy + 渲染;敏感度分析屬後評(同 W49 R5) |
| R3 | H7 mockup drift(metric 視覺 / caveat 改動)| Low | Med | design-first 先改 mockup;不清晰 → STOP+ask(§5.7)|
| R4 | schema 加欄爆既有 frontend/test | Med | Low | 同期更新 consumer(config-test.ts + page.tsx + vitest FAKE_RESULT + backend test)|

## 6. Day-by-Day Breakdown(rough)

| Day | Date | Focus | Deliverables |
|---|---|---|---|
| D1 | 2026-06-05 | F0 kickoff + F1 backend + F2 frontend + F3 tests + F4 closeout（小 phase,同日）| F0-F4 |

## 7. Plan Changelog

| Date | Change | Reason | Approver |
|---|---|---|---|
| 2026-06-05 | Initial plan | W51 kickoff;Chris AskUserQuestion 揀 W51 = **對沖指標**(distinct-sections completeness proxy per-run band;proxy 非 recall;C ingestion eval 留 W52)| Chris |

---

**Lifecycle reminder**:plan locked after status=active。重大 deviation 入第 7 節 changelog。**F2 frontend = H7 design-first**(mockup 先改再 match)。**Reuse 既有 `MetricBand`/`_band`**(零新 model);**proxy 非 recall** 必須誠實 framing(R1)。
