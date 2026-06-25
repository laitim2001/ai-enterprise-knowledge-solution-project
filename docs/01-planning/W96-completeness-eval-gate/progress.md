# W96 progress — 答案完整度 eval gate

## Day 1 — 2026-06-25(kickoff + F1)

### Context
- 接 2026-06-25 第二輪 source-fidelity 研究結論:乙類(synthesizer over-summarisation)由上輪「幾乎空白」變成本輪覆蓋最強方向,有整條 peer-reviewed 方法線把完整度操作化為 nugget/coverage recall。用戶拍板「先做完整度 eval gate(可機器量度,fit config A/B)」。
- think-before-coding(§1.1):確認 `backend/eval/` 已有 custom metric 先例(`image_recall.py` pure core + `scripts/run_image_recall.py` driver + GT yaml;`marker_placement.py` 同模式)→ 完整度 metric 跟同一 pattern,**唔觸 H1/H2**(eval 加 metric,§5.1 明文容許;用既有 Azure OpenAI infra 無新 vendor)。
- 確認最新 phase = W95 → 本 phase = W96。

### Decisions
- **GT 來源 = LLM 自動抽 query-conditioned nugget**,不用人手 prose GT。理由:① 避開「prose human GT 卡用戶」已知 blocker(memory)② 研究證 LLM-judged coverage run-level 可信(我哋本來就 per-KB config A/B + 多 run)。
- **denominator = 檢索 context(synthesizer 輸入)**,非 answer 自己 cite 嘅 chunk(否則 synthesizer 丟成個 chunk 就唔被 cite → 掩蓋 drop)。對齊 CRUX「retrieved but not answered」。
- **judge model = `gpt-5.4-mini`**(per cost policy memory,非 gpt-5.5)。
- **本 phase 只造尺,唔做緩解**(prompt 改留下一 phase;無尺盲調 = 違 §1.2)。
- core 留 optional `context_coverage` 欄位(CRUX retrieval-ceiling 軸)但本 phase 唔強制計(需 GT-section,卡用戶)。

### F1 done(pure metric core)
- `backend/eval/completeness_coverage.py`:`NuggetJudgement`(text + present)/ `CompletenessMetrics`(total/covered/answer_coverage/missed)/ `compute_metrics` / `CompletenessQueryResult`(+ optional context_coverage)/ `CompletenessReport` / `aggregate` / `report_to_dict`。Frozen slots,純邏輯零 IO,LLM judge 注入為已算 label(mirror `image_recall.py`)。
- `backend/tests/test_completeness_coverage.py`:full / partial / 全掉 / 空 nugget 邊界 / aggregate 混 scored+errored / context_coverage None vs 有值 / report_to_dict 形狀。

### F2 done(LLM judge 層)
- `backend/eval/completeness_judge.py`:`make_completeness_judge`(無 cred → None)+ 2 judge call(query-conditioned nugget 抽取 → presence 判定,`gpt-5.4-mini`,`patch_for_gpt5`)+ 純 parse helper `_parse_nuggets` / `_parse_presence`(容錯 fence / text-align / dropped-nugget=absent / positional fallback)。
- `backend/tests/test_completeness_judge.py`:10 測試綠;ruff clean;mypy clean(my file;3 個 pre-existing error 喺 `ragas_evaluator`/`ragas_runner`,`controlled_comparison` 同樣 import,§1.3 不掂)。

### F3 done(live driver)
- `scripts/run_completeness.py`(mirror `run_image_recall.py`):per query → `/query` → 分母 = `retrieved_chunks[].chunk_text`(rerank 後餵 synthesizer 嘅 context,確認 `query.py:346-354` build 自 `result.chunks`)→ judge → 出 report yaml + per-query missed nugget print。ruff clean。
- 建 `docs/eval-set-completeness-w96.yaml`(GT-free):C001 GL construct-validity + C002-C005 AR baseline,KB = `drive-user-manual-kb-20260618`(369 chunks / 827 imgs,同 analysis conversation `583fa20…`)。

### F4 done(live 驗證 + construct validity)— 3 run band
- Pre-flight:backend 全棧 up + healthy(`azure_openai`/`cohere`/`azure_search` ok),無需重啟;新 code 喺 driver 進程行不經 backend(stale-backend 不適用)。
- **3 run per-query band**(report:`reports/completeness_w96{,_run2,_run3}.yaml`):

  | query | run1 | run2 | run3 | 擺幅 |
  |---|---|---|---|---|
  | C001 GL post journal | 0.67 | 0.89 | 0.83 | 0.22 |
  | C002 payment collection | 1.00 | 0.54 | 1.00 | 0.46 |
  | C003 write off receivable | 0.18 | 0.82 | 0.88 | **0.70** |
  | C004 account statement | 1.00 | 1.00 | 1.00 | 0.00 |
  | C005 aging period | 1.00 | 1.00 | 0.25 | **0.75** |
  | **mean** | 0.770 | 0.849 | 0.792 | 0.08 |

### Phase Gate G-W96 verdict — **PARTIAL（把尺造成 + 教返我哋可靠範圍;未可逐答案用）**
- ✅ 把尺造成 + 端到端跑得 + in-run 有區分力(同 run 內 0.18 vs 1.00 分得開)+ 正確隔離 synthesizer 層(分母 = reranked context,唔屈 synthesizer 孭唔喺其 context 嘅內容 → C001 GL 嘅 RMS/RSP 段唔喺 reranked context 故唔當乙類,對齊 analysis「GL 末尾圖係甲+乙混合,RMS/RSP 偏甲類錨定」)。
- ✅ **實證確認 per-answer 不可靠**(C003 0.18↔0.88、C005 0.25↔1.00、C002 0.54↔1.00)— 三重 variance 疊加(檢索 context 變 → nugget 數變;synthesizer stochastic;judge stochastic)。**單 run 嘅 C003=0.18 唔可以當「呢條答案爛」**(run3 = 0.88)。
- ⚠️ **未可用作 gate as-is**:per-query 不可診斷;5 條 query 嘅 mean 都擺 0.08。要做可靠 gate 需:(a) ≥20-30 query 穩定 mean;**和/或 (b) fixed-context paired A/B 模式**(每 query 檢索一次 + 抽 nugget 一次,A/B 兩臂用**同一** context + 同一 nugget set 各自生成答案再比 coverage → 去掉檢索 + nugget variance,只剩 prompt 效果;precedent = `controlled_comparison.py` shared frozen set);和/或 (c) 每 config 平均 N run。
- **洞察(refine analysis)**:乙類有一部分根本係 synthesizer **非確定性**(同 query 有時完整有時濃縮)→ 緩解唔淨係「寫個 coverage prompt」,要連**穩定性**一齊睇;fixed-context A/B 先量得準 prompt 真效果。

### Next
- F5:eval-methodology §2.5 + memory + DEFERRED_REGISTER(緩解 phase + gate-hardening 列下一步)。
- **緩解 phase 前置條件(改 plan §5 out-of-scope → 變 gate-hardening 前置)**:先把 gate 加 fixed-context paired A/B 模式 + 擴 query set,先有可信尺,再談 coverage prompt(否則盲調 + 噪聲淹冇)。
