# W49 — Faithfulness Quality-Axis Noise Band · Progress

> Daily progress + decisions + commits + 結尾 retro。每 daily commit 對應 Day-N entry(R2)。

---

## Day 1 — 2026-06-05

### Context / kickoff
本 session 連收 W47 F5(reindex UI live-verify RESOLVED,`6db270e`)+ W48 footer copy 修正(`16fc51f`)。用戶問「W43 開始嘅 vision 仲有幾多未做」→ 我據 `ROADMAP-per-kb-tunable-config.md` 給全圖(per-KB 主幹 W43→W48 已交付;未做 = per-document / 質素軸深化 / production reindex / Tier 2 / 操作期)。用戶揀**先做決策 7 faithfulness 抗噪**。

### 決策
- **AskUserQuestion(抗噪做法)**:Chris 揀 **Option 1「沿用重跑次數做 band」** — N≥2 顯示 faithfulness max−min band(同 presentation band 一致量化噪音);N=1 單值 + 「單次方向性」warning;judge 成本 = 用戶自己揀嘅 N(已為 presentation band opt-in),**唔加 toggle**。否決 Option 2(warning-only,唔量化噪音)+ Option 3(固定 N,脫鈎用戶 N + 強制成本)。
- **Key design lock**(plan §2):faithfulness 沿用既有 `MetricBand`(零新 model)+ 逐 run judge `asyncio.gather` 並發 + graceful(per-run None → band over 成功 run;全 None → None)+ N=1 → band=0 + warning + judge 維 gpt-5.4-mini + **無新 ADR**(extend ADR-0040 雙軸)。

### R6 grep 驗證(plan kickoff)— config_test 結構確認
- `MetricBand`(min/max/mean/band)**已存在**(`schemas/config_test.py:74`),presentation counters 全部經 `_band()`(`config_test.py:58`)用緊 → faithfulness 沿用零新 model。
- W48 `_run_n`(`config_test.py:67`)現只 capture `last_answer`+`last_contexts` 做**一次** `asyncio.to_thread(faithfulness_fn,...)`(line 113-117)→ W49 改 capture 每 run + gather N judge。
- `make_faithfulness_evaluator` 簽名 `(question, answer, contexts) -> float | None` 不變(reuse)。
- **無 plan-text contamination**:plan 引用嘅 function/field 全部 grep 對齊現 code(R6 recursive scope 過)。

### Done
- F0 R1 phase 三件套建立(plan/checklist/progress);Phase Gate G1-G5 定義

### Commits
- (F0 kickoff commit pending)

### Blockers / carry-over
- 無 blocker。infra 已起(azurite 23252 / backend 8000 W48 code / frontend 46364 clean .next)。**注**:F1 改完後端要 restart backend 先 live 反映(同 W48→W47F5 一樣)。
