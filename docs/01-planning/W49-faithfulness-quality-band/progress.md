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

### F1 backend(同日)
- `schemas/config_test.py`:`ConfigRunSummary.faithfulness` `float | None` → **`MetricBand | None`**(docstring 更新:band over runs + 2026-06-06 noise 證據)
- `routes/config_test.py`:NEW `_faithfulness_band(faithfulness_fn, query, per_run_qa)` helper —— `asyncio.gather(*[asyncio.to_thread(faithfulness_fn, query, ans, ctx) ...])` 並發逐 run judge → filter None → `_band(ok)` if ok else None;`_run_n` 主 loop 改 capture **每 run** `(answer, [c.chunk_text for c in resp.retrieved_chunks])` 入 `per_run_qa`(取代只存 last_*)→ call `_faithfulness_band`
- 驗:ruff check+format clean;mypy --strict **我兩個檔零 error**(exit 1 純跨模組 pre-existing,同 W48 一樣)

### F2 frontend(同日,H7 design-first)
- mockup `ekp-page-kb.jsx` `KbTestResultCard`:signature 加 `faithBand` + `runs`;headline 由單值 → mean + `±{faithBand}`(N≥2)/ 單值 + 「單次 judge · 方向性 · 重跑次數調高至 ≥2 先見穩定度 band」warning(N=1);2 call site 更新(DRAFT faith 0.78 ±0.16 runs 3 揭噪音 / SAVED 0.92 ±0.05)
- mockup footer(`:942`,`16fc51f` 改過嗰句)→「忠實度質素軸 + presentation counters 逐 run 算 band · N=1 只方向性」
- `config-test.ts`:`faithfulness: number | null` → **`MetricBand | null`**(reuse 既有 presentation `MetricBand` TS type)
- `page.tsx` `ConfigResultCard`:headline `summary.faithfulness.mean.toFixed(2)` + `±band`(`summary.runs.length >= 2`)+ N=1 warning(`summary.runs.length === 1`);footer(`:2211`)同步
- 驗:tsc --noEmit clean

### F3 tests(同日)
- backend `test_config_test_route.py`:`_computed` 改 MetricBand 斷言(mean=0.95 + band=0);NEW `_band_over_runs`(threadsafe iter [0.9,0.5,0.7] → min .5/max .9/band .4/mean .7,order-independent)+ `_n1_band_zero`(runs=1 → `{min:.8,max:.8,mean:.8,band:0}`)+ `_partial_none`(iter [0.9,None,0.5] → band over 成功 run);`_disabled`+`_graceful` None case 不變
- frontend `kb-settings-tuning.test.tsx`:FAKE_RESULT draft/saved runs 補至 3 entries + faithfulness → MetricBand(draft ±0.16 / saved ±0.05);主 A/B test 改驗 `±0.16`/`±0.05` band span + 無「單次 judge」warning;NEW N=1 test(`mockResolvedValueOnce` runs=1 → 「單次 judge」warning + mean 0.80 無 band span)
- 驗:backend **pytest 17 passed**(config_test 10 + eval_ragas 7)0 regression;frontend **kb-settings-tuning 4 passed** + full vitest **106 passed**(kb-detail/kb-settings-reindex full-suite flaky timeout = loaded machine,隔離單跑 5 passed 證非 regression;「Error: boom」= intentional pre-existing)+ tsc + lint(唯一 pre-existing chat `<img>` warning)+ `[oklch`=0

### F4 doc-sync(同日)
- architecture.md §5.5.5 加 **W49 amendment**(faithfulness 逐 run judge → `MetricBand`;`_faithfulness_band` gather;N≥2 mean±band / N=1 warning;成本 = 用戶 runs;length-bias known limitation note)
- roadmap:§3 候選行 → ✅ W49 shipped;逐期重點 bullet header → ✅ shipped(採 Option (a)+(c);(d) length-bias 對沖留未來,保留 證據①② context);§5 決策 7 → ✅ RESOLVED;修訂史加 2026-06-05 W49 entry。**連帶 commit 咗 2026-06-06 獨立 session 未 commit 嘅 candidate 內容**(11 行:候選行 + 逐期重點 bullet 證據①② + 決策 7)— 該 session 留底但未 commit,W49 doc-sync 自然帶入
- session-start §10 W49 closed row(local-only,gitignored)+ plan.md status→closed + changelog

### Phase Gate G1-G5 — **PASS**

| # | Criterion | Verdict | Evidence |
|---|---|---|---|
| G1 | faithfulness 返 N-run `MetricBand`(量化噪音)| ✅ PASS | `_band_over_runs` min=0.5/max=0.9/band≈0.4(A/B 各一 MetricBand);`_computed` mean+band |
| G2 | graceful degradation | ✅ PASS | `_partial_none` band over 成功 run;`_disabled`/`_graceful` → None;config-test 唔 fail |
| G3 | frontend render band + N=1 warning 100% match mockup | ✅ PASS | design-first mockup KbTestResultCard mean±band/N=1 warning → page.tsx match;vitest 主 A/B ±band + N=1「單次 judge」test |
| G4 | pytest+ruff+mypy+tsc/lint/build clean | ✅ PASS | backend 17 pass + ruff + mypy(我兩檔零 error);frontend vitest 106 pass + tsc + lint(唯一 pre-existing chat `<img>`)|
| G5 | judge gpt-5.4-mini + cost=用戶 N + 無新 ADR/vendor | ✅ PASS | reuse `azure_openai_deployment_llm_judge`;無 toggle 成本由 runs 控;extend ADR-0040(無新 ADR)|

**判決:Phase Gate 通過(PASS)**。決策 7 RESOLVED(Option 1);質素軸由 single-shot → N-run band,用戶試跑見到噪音先可信「撥到滿意」。

### Retro
- **設計收斂(Karpathy §1.2 simplicity)**:R6 grep 早發現 `MetricBand`/`_band()` 現成 → faithfulness 沿用零新 model,改動極窄(schema 1 欄 type + 1 helper + `_run_n` capture 換 list)。無 over-engineer N-run 專屬 model。
- **成本由用戶 N 控(Option 1 精髓)**:唔加 toggle、唔強制固定 N → judge 成本 = 用戶為 presentation band 已 opt-in 嘅 `runs`,自然對齊。否決 Option 3(固定 N 脫鈎 + 強制成本)。
- **並發 judge graceful**:`asyncio.gather` 逐 run judge,per-call None(撞 rate limit / error)→ band over 成功 run,全 fail 先 None;`_partial_none` test 證。
- **H7 design-first 順暢**:mockup KbTestResultCard 先加 `faithBand`+`runs` + N=1 warning,再令 page.tsx match;順帶第三度改正 footer copy(W48 `16fc51f`「每 config 算一次」→ W49「逐 run 算 band」)。
- **getByText nested-text 坑**:faithfulness headline mean + `±band` span 令 textContent = "0.78±0.16" → `getByText('0.78')` exact-match fail;改驗 band span leaf(`±0.16` 唯一)+ N=1 mean leaf(無 band span 時 textContent 純 "0.80")。
- **Watch(carry W50+)**:(1) live-verify W49 band 喺真 pipeline(需 restart backend + N judge 成本,stretch 未做);(2) **length-bias 對沖**(roadmap 證據②:faithfulness 系統性懲罰長/全面答案,可能同 completeness 反相關)= 決策 7 Option (d),留未來期 — 配 recall 對沖指標 / UI 標示。

### Post-closeout live-verify(同日稍後,用戶要求親眼睇 ±band)— ✅ **band 重現成功**
- **restart backend** pick up W49(W48 雙進程樹 taskkill /T 連子樹清 → venv `-m api.server` /health 全綠;OpenAPI 確認 `faithfulness` schema number → `anyOf[MetricBand, null]`)。
- **Run 1**(`test-kb-20260531-v1`,runs=3,A/B,query「manage AR…」,draft `citation_expansion_max_aux=10`):draft + saved faithfulness 兩邊 **{min:1.0,max:1.0,mean:1.0,band:0}**(質素軸三跑穩定 1.0,presentation cit 8/8/7 微動)→ band=0 = 有效訊號(此 config 質素穩定),但**冇噪音可睇**。
- **Run 2**(runs=4,draft only,**列舉型 query**「list every step…」+ completeness-max:parent_doc on + citation_expansion_max_aux=10 + section_path_prefix_depth=1 + max_images=20):**faithfulness {min:0.545, max:0.95, mean:0.779, band:0.405}** — per-run cit 15/19/8/16、chars 2442–4005、figRaw 20(capped)。**同一 config 四跑 faithfulness 0.545↔0.95 擺動 0.405**,正正重現 roadmap 證據①(drive_user_manuals 0.929↔0.53,~0.4 swing)。
- **驗證價值**:W48 single-shot 會隨機顯示 0.545(「好差」)或 0.95(「好正」)→ 憑運氣誤判;W49 顯示 **0.78 ± 0.41** → 用戶即知質素軸對此 config **唔穩定、勿單次定論**。**G1 band 量化噪音 live 證實**(非 mock)。同時觀察到 Run 2 長答案(>3500 字)+ 列舉 query 正係噪音高發區,印證證據② length-bias watch(留 W50+)。

### Carry-overs → W50+(rolling JIT)
- ~~🚧 live-verify W49 band~~ → ✅ **RESOLVED 2026-06-05**(Run 2 band=0.405 重現噪音;見上 Post-closeout live-verify)
- faithfulness **length-bias 對沖**(證據②;Option (d):completeness/recall 對沖指標 + UI 標示)
- (前期 carry 不變)per-document scope(決策 1)/ AUDIT-D (ii) correctness+context_recall / production v1→v2(Track A 決策 4)/ presets+config 版本史(決策 5)/ Layer C 視覺內容揀圖(Tier 2 決策 3)/ heading_aware footgun

### Commits
- `05019c7` F0 kickoff + `ace414b` F1-F3 code+tests + F4 closeout commit(pending)

### Blockers / carry-over
- 無 blocker。infra 已起(azurite 23252 / backend 8000 **跑緊 W48 code,W49 改動未 reload** / frontend 46364 clean .next)。**注**:要 live 驗 W49 band 需 restart backend(同 W48→W47F5)。
