# W96 — 答案完整度 eval gate(乙類 over-summarisation 檢測)

| 項目 | 值 |
|---|---|
| Phase | W96-completeness-eval-gate(source-fidelity §15 北極星線 · 接 ADR-0056 vision 主線) |
| Status | **active**(2026-06-25 kickoff) |
| Tier | Tier 1(加 eval metric;用既有 infra,不觸 H1/H2 — 同 `image_recall.py` / `marker_placement.py` 並存先例) |
| 依賴 | 2026-06-20 + 2026-06-25 兩輪 source-fidelity 研究(`docs/09-analysis/`)+ 分析文件 §5.3/§9 乙類 |
| 錨點 | **CLAUDE.md §15 北極星**・`docs/09-analysis/source_fidelity_recall_external_research_20260625.md`(本輪研究)・`docs/09-analysis/text_image_fidelity_recall_analysis_20260620.md` §5.3 乙類 |
| 粗估 | 中(F1-F5;F1-F3 純加 eval 零 production 改動,F4 需 backend + eval run) |
| 下一期 | **緩解 phase**(coverage-oriented / U-形位置-aware synthesis prompting)— 視本 gate 量到嘅 baseline 決定,可能觸 synthesizer prompt(屆時確認 H 級別) |

> **本 phase 只「造量度」,唔「做緩解」**:目的係先有一把可信、機器可量度嘅尺,檢測 synthesizer 把原文段落濃縮掉(乙類)。**改 prompt 緩解係另一 phase**(Karpathy §1.2 minimum — 無尺之前改 prompt = 盲調)。

---

## §1 目標(Why)

兩輪研究(尤其 2026-06-25)確立:**乙類「合成層掉內容」是公認、可機器量度嘅 first-class 失效模式** —— LLM 答案可以忠實度(faithfulness)高但完整度(completeness)低,且完整度**必須獨立量度,不能由忠實度推導**(FineSurE ACL 2024);商用 RAG 即使內容已檢索到,仍喺合成階段掉約 18-48% core sub-question(Sub-Question Coverage NAACL 2025)。我哋分析文件 §4 實證 GL 手冊「post journal entry」query 漏咗 RMS/RSP 變體段 + Overview 段 = 典型乙類,連帶嗰幾段嘅圖失去文字錨。

**核心**:對齊 §15 北極星 —— 答案更忠實還原原文段落,嗰段嘅圖自然有文字錨(高完整度 + 準確度係還原嘅自然結果)。但**改之前必先量得到**。本 phase = 起一把尺。

**方法線**(全 peer-reviewed,本輪 20 confirmed claim):把「答案掉內容」操作化為 **nugget / atomic-fact coverage recall**(FineSurE / AutoNuggetizer SIGIR 2025 / CRUX EMNLP 2025)。

## §2 Deliverables(F1–F5)

| # | Deliverable | Acceptance |
|---|---|---|
| **F1** | Pure metric core `backend/eval/completeness_coverage.py` + 單元測試 `backend/tests/test_completeness_coverage.py` | coverage 數學(covered/total、aggregate、report_to_dict)pytest 綠 + ruff + mypy clean;**零 IO 零 production 改動**(LLM judge 注入為已算好 label,mirror `image_recall.py`) |
| **F2** | LLM judge 層 — **query-conditioned nugget 抽取**(給 query Q + 檢索 context C → 列出「完整回答 Q 應包含」嘅 atomic 事實/步驟)+ **answer presence 判定**,用 Azure OpenAI `gpt-5.4-mini`(judge cost policy,非 gpt-5.5) | judge 回 nuggets + 每 nugget present bool;低溫近確定性;無 credential 時 graceful None(mirror `make_qa_keyword_generator`);query-conditioned 抽取 → 唔會把「正確過濾掉嘅 irrelevant context」當乙類 |
| **F3** | Live driver `scripts/run_completeness.py` — per GT query → 真 `/query` → 攞 answer + 餵 synthesizer 嘅檢索 context → 抽 nugget → 判 presence → 餵 F1 → 出 report yaml | 沿用既有 eval-set query list(**唔需要人手 prose GT** — 避開「卡用戶」blocker);端到端跑 ≥1 KB 出 report;denominator = **檢索 context**(synthesizer 輸入)非 answer citation(否則縮分母掩蓋 drop) |
| **F4** | Baseline 驗證 run(乙類已知案發 KB:`drive-images-1` / GL 手冊)+ **construct validity 驗證** | 記錄 baseline mean answer_coverage;**證明把尺真係 flag 到已知乙類案**(GL「post journal entry」query answer_coverage 明顯 < 1.0,`missed` 含 RMS/RSP 變體 + Overview nugget);run-level 多 run 睇 band(per 研究 per-answer 不可靠 caveat) |
| **F5** | Doc-sync:`docs/eval-methodology.md` 加完整度 metric 段 + memory 更新 + `DEFERRED_REGISTER.md` 記低「緩解 phase」為下一步 | doc + memory synced;eval-methodology 寫明 run-level gate 用法 + per-answer 不可靠 caveat |

### DD-15 gate hardening(F6–F8 — W96 continuation,per §6 changelog 2026-06-25b)

> F4 證 per-answer 不可靠(3 run band C003 0.18↔0.88)→ 把尺未夠可信驅動 prompt 決策。F6-F8 打三個 variance 源令把尺可信,先解鎖緩解 phase(DD-16)。

| # | Deliverable | Acceptance |
|---|---|---|
| **F6** | **Fixed nugget set** — build-once 模式:per query 抽 nugget 一次 → persist `docs/eval-set-completeness-w96.nuggets.yaml`;scoring 用固定 nugget 只判 presence(skip 抽取)。+ pure helper `mean_std` / paired aggregation + 測試 | 固定 nugget 持久化;scoring 跳過抽取(去掉 nugget-creation variance,research-backed);pure helper pytest 綠 + ruff + mypy |
| **F7** | **Paired A/B + K-run 平均 harness** `scripts/run_completeness_ab.py` — per query:固定 nugget,兩臂(`--config-a`/`--config-b`,QueryRequest override 如 `llm_model`)各生成 K 次 → 平均 coverage → paired delta(B−A)。確定性檢索 → 兩臂同 context | 出 paired report(per-query mean±std + delta + 符號穩定性);K-run 平均;ruff |
| **F8** | **Hardening 驗證** — 擴 query set(~12-20)+ build 固定 nugget + 跑 paired A/B(`gpt-5.5` vs `gpt-5.4-mini`)+ 對照 F4 baseline | 證 per-query std 較 F4 收窄(fixed nugget + K-run 生效)+ paired delta 符號穩定(把尺偵測得到真實 config 差)→ G-W96-H verdict;doc-sync eval-methodology §2.5 補 paired 用法 |

## §3 Phase Gate

- **G-W96**:F1 metric core 測試綠 + F3 driver 出到 baseline + **F4 construct validity 過**(尺 demonstrably flag 到已知乙類案)+ run-level band 已睇(多 run)+ **確認零 production pipeline 改動**(eval-only)。
- 過咗先可以開緩解 phase;尺未證有效之前**唔可以**用佢做任何 prompt 決策(避免「gameable / per-answer 不可靠」陷阱,per 研究 caveat)。

## §4 Risks

- 🟡 **LLM-judge nugget 抽取喺 SOP domain 可靠度**:研究證 run/system-level 可靠(τ 高),**per-answer 不可靠**(τ≈0.30-0.44)→ 只用作 config A/B band + 多 run,**唔可以**單靠佢逐答案 debug;逐答案要配人手。寫入 docstring + eval-methodology。
- 🟡 **denominator 來源**:必須由**檢索 context(synthesizer 輸入)**抽 nugget,非 answer 自己 cite 嘅 chunk(否則 synthesizer 丟成個 chunk 就唔會被 cite → 唔計 → 掩蓋 drop)。需確認 `/query` response 有冇暴露檢索 context;冇就用 V4 `retrieval-test` 或 citation chunk_text 補(F2/F3 拍板)。
- 🟡 **query-conditioned 抽取必要性**:檢索 context 含大量 query-irrelevant chunk,synthesizer 正確丟掉 irrelevant ≠ 乙類。抽 nugget 時必須 query-conditioned(只抽「回答 Q 應包含」嘅事實),否則 metric 懲罰正確過濾。
- 🟢 **成本**:judge 用 `gpt-5.4-mini`(per cost policy memory),非 gpt-5.5;nugget 抽取 + presence 判定每 query 數 LLM call,控制 query 數。
- 🔴 **backend reload=False**:F4 需 backend 行最新 code(per `project_stale_backend_no_reload`);本 phase 大概率零 backend 改動(driver 打既有 `/query`),但 F4 跑之前 pre-flight health check(§10.3 5b)+ 確認 backend 啟動時間。
- 🟡 **construct validity 必驗**:coverage metric 可被 inflate(研究 caveat)→ F4 必須先證佢 flag 到已知案先當佢有效,唔可以一寫完就信。

## §5 Out of scope(留後續 phase)

- **緩解**(coverage-oriented / U-形位置-aware synthesis prompting)= 下一 phase;可能改 synthesizer prompt → 屆時確認 H 級別(§3 RAG core)。
- **Context-coverage 軸**(CRUX retrieval-ceiling:reference = GT-section nugget,分清「context 不足」vs「synthesizer 濃縮」)= 可選 v2,需 GT-section reference(human GT 卡用戶);本 phase core 留 optional 欄位但唔強制計。
- **甲類圖→步驟級錨定**(階梯 ① runtime `doc_order` 鄰近錨定)= 另一條腿,本 phase 不碰。
- **over-generate-then-select**(Ladhak 2022 selector)= 屬旁證(faithfulness-vs-abstractiveness 非直接 coverage),不納入本 gate。

## §6 Changelog

| 日期 | 變動 | 由 |
|---|---|---|
| 2026-06-25 | Phase kickoff — 2026-06-25 研究確立乙類為可機器量度失效模式;用戶拍板「先做完整度 eval gate」。F1-F5 分段;F1-F3 零 production 改動,F4 construct-validity gate。緩解留下一 phase | 開工 |
| 2026-06-25b | **F1-F5 完成 + Gate G-W96 = PARTIAL**(commit `4bca795`):把尺造成但 F4 3 run band 證 per-answer 不可靠。**DD-15 gate hardening 拉入 scope(R3 deviation,原 §5 out-of-scope)**:用戶拍板做。加 F6-F8(fixed nugget + K-run 平均 + paired A/B),打三個 variance 源(nugget 抽取 / 答案 / query offset)。A/B lever 用 `QueryRequest.llm_model`(per-request toggle,無需直呼 synthesizer — 確定性檢索保兩臂同 context) | F1-F5 closeout + DD-15 開工 |
