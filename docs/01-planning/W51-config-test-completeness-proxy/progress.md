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

### Commits
- (F0 kickoff commit pending)

### Blockers / carry-over
- 無 blocker。infra 已起(azurite 23252 / backend 8000 W49 code / frontend 46364 clean .next)。**注**:F1 backend 改完要 restart backend 先 live 反映(同 W48→W49)。
