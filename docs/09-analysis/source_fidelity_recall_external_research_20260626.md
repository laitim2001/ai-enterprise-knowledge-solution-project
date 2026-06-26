# 圖文還原度(Source Fidelity Recall)— 外部市場 / 學術實證調查 第三輪(2026-06-26)

**Date**: 2026-06-26
**Status**: Research brief — 外部證據彙整,**未決策、未開 phase**(交俾 Chris 定方向)。EKP-specific 比對 / 檢討見 §8。
**Scope**: 2026-06-20(第一輪)+ 2026-06-25(第二輪,乙類方向,從未存檔)之 **FOLLOW-UP 第三輪**;聚焦 2025-Q3 之後新證據,**並針對 W97「乙類 coverage-prompt」2026-06-26 實證失敗後尋找替代**。
**讀者**: Chris(技術 Lead)+ Claude Code(本 repo AI 助手)
**研究方法**: deep-research harness — 6 路 fan-out web search → 28 sources fetched → 127 falsifiable claims → 三票對抗式驗證 top 25(需 2/3 反證才剔除)→ **19 confirmed / 6 killed / 14 after synthesis**(111 agent calls)
**前兩輪**: `source_fidelity_recall_external_research_20260620.md`(第一輪,4 方向)+ 第二輪(2026-06-25,乙類方向 A,deep-research 跑過但**未存成 doc** → 結論已 fold 入 W96 完整度 gate + ADR-0069;本 doc 順帶修補嗰條 dangling reference)

> **遵守 CLAUDE.md §15 North-Star Principle**:本調查出發點係「忠實還原原文檔內容結構 + 圖文關係」,非「掃走多餘圖」。

---

## 1. 一句話結論

本輪研究**唔係推翻**前兩輪,而係**從外部獨立佐證咗 W97 點解失敗**(完整度瓶頸係 generation-side ceiling,非 retrieval gap)**+ 點解 per-answer 完整度 gate 不可靠**(只可 aggregate);但同時誠實揭示:**冇任何一條 finding 提供已喺 SOP / RAG 場景驗證有效嘅 over-summarisation 修法** —— 最有希望嘅替代(DIPPER / EVE / Auto-Merging parent retrieval)全部係 domain-mismatch 嘅**待驗證假設**,而非已證手段。

---

## 2. 三個 meta 結論(直接打中 EKP)

| # | 發現 | 對 EKP 意義 | 可信度 |
|---|---|---|---|
| 1 | **完整度瓶頸主要係 generation-side ceiling,非 retrieval gap** — CRUX(EMNLP 2025,arXiv 2506.20051):畀 oracle 100% coverage context,生成都只還原 **62-65%**(64.6 DUC / 61.8 Multi-News),human gold ~94-95%,留 ~30pp gap | **解釋 W97 點解失敗**:問題唔係「叫佢答完整啲」,係生成階段本身有天花板 → 純 prompt 郁唔到 | peer-reviewed(2-1);**但 generator = Llama-3.1-8B 非 `gpt-5.5`,絕對值未必 transfer** |
| 2 | **per-answer 完整度量度本質不可靠,只可 aggregate** — AutoNuggetizer(TREC 2024,arXiv 2504.15068):run-level Kendall tau 0.73-0.90,但 **per-topic 跌到 0.30-0.54**,作者明文「inadequate for fine-grained debugging of individual answers」 | **獨立佐證 W96 實測 0.18↔0.88 + 放棄 per-answer gate、只用 aggregate A/B 嘅決定** | peer-reviewed(2-1)|
| 3 | **「reasoning 模型無 temperature 控制」kill 一整類方法** | 確認硬約束殺傷力,慳走冤枉路(見 §4 kill list)| peer-reviewed + vendor docs |

---

## 3. 逐方向發現(標票數 + 來源 + EKP 可用性)

### 3.1 方向 A — 乙類完整度(prompt 失敗後嘅替代)

#### A(i) 非 prompt 層(retrieval / chunking / structured extraction)

| 手段 / 來源 | 票 | 成本 / re-index | EKP 可用性 |
|---|---|---|---|
| **LlamaIndex Auto-Merging Retriever**(vendor docs + 源碼)— leaf chunk 檢索後,同 parent 下 sibling 命中比例 > threshold(default 0.5)即合併回完整 parent node 進 context | 3-0 | 中 / 視做法 | ✅ **最低成本替代** — EKP 已有 `parent_doc` ON,可延伸 section-merge。caveat:合併 conditional(≥50% sibling 命中),非保證完整 parent 入 context |
| **S-RAG**(arXiv 2511.08505)— ingestion 建 schema/SQL 結構化表示,inference NL→SQL,對 aggregative 查詢勝 vector-RAG | 3-0 | 高 / 是 | ❌ **不適配** — 限 homogeneous entity-per-doc(一 hotel 一檔),唔啱 heterogeneous SOP;auto-schema 大幅退化(0.845→0.500);針對 cross-doc aggregative 非 per-answer 乙類 |
| **Query decomposition**(arXiv 2510.18633,EACL 2026)— 拆 subquery 各自檢索補齊被丟分支 | 框架 3-0 /**performance 數字反證 0-3** | 中 / 否 | ⚠️ 可用但要控 query 數 — trade-off:retrieve more 引 noise + 撞 context 上限;「increasing rewritten queries not always advantageous」 |

#### A(ii) sampling-free 生成手段(繞過 no-temperature 約束)

| 手段 / 來源 | 票 | EKP 可用性 |
|---|---|---|
| **DIPPER**(arXiv 2412.15238,NeurIPS 2024 workshop)— training-free,平行餵一組 diverse prompts 把單一 LLM 變 inference-time ensemble,**diversity 來自 prompt 變化非 temperature**(明文 deterministic,independent of sampling temperature)| 3-0 | ✅ **最有希望 sampling-free ensemble** — 直接繞過 `gpt-5.5` temp≠1 約束。**caveat**:只喺小 math 模型(Qwen2-MATH)驗,RAG/completeness transfer **未證**;需 prompt 優化 pipeline(200 candidate)工程成本不低;workshop 非 main-track |
| **EVE**(arXiv 2602.06103,2026-02)— Extraction-Validation-Enumerate 多次 LLM call(multi-query majority voting 非 temperature),recall+24%/precision+29%/F1+31% | 2-1;**「prompt-only」子claim 反證 1-2** | ⚠️ 技術可用(multi-call)— **caveat**:domain = STPA safety patents **non-RAG**(full single doc in-context,作者明言「RAG optimizes relevance not coverage」);best-case relative gain;**唔係純 prompt 係 multi-call pipeline** |
| **self-consistency / temperature best-of-N**(arXiv 2502.18581)| — | ❌ **不可用** — diversity 來自 temperature sampling(原 paper sample 64 @ temp=0.6),`gpt-5.5` 拒 temp≠1 → N 樣本塌縮成一樣 |
| **self-certainty selection**(arXiv 2502.18581)| 2-1 | ❌ **不可用** — 需 full-vocabulary logits(softmax over ~100k V),Azure chat top_logprobs cap 20,且 `gpt-5.5` reasoning 端點連 logprobs 都回 **null** → 結構性算唔到 |

#### A(iii) completeness 可靠量度(新工具)

| 來源 / 工具 | 票 | EKP 意義 |
|---|---|---|
| **AutoNuggetizer**(arXiv 2504.15068)| 2-1 | **直接佐證 W96「per-answer 不可靠、只可 aggregate」決定**(per-topic tau 0.30-0.54)|
| **VITAL**(arXiv 2510.07083,2025-10 NEW)— importance-weighted coverage,分 vital / okay / less-important,唔再把所有 claim 等同 | 3-0 | ⭐ **唯一可能改善 per-answer 穩定性嘅新量度** — peripheral 噪音降權或令 variance 跌 → 值得小規模試。caveat:preprint 未 venue;係 measurement 非 fix |
| **CRUX**(arXiv 2506.20051)— question-based context-completeness coverage metric | 3-0;**「coverage 比 recall 更 predict completeness」子claim 反證 0-3** | 可借鑑量度框架,但同受 per-answer variance 限制;**不應宣稱 coverage 係比 recall 更強 proxy** |
| **comprehensiveness metrics**(arXiv 2510.07926,ACL 2026 Findings)— 簡單 end-to-end「直接 identify missing content」勝 NLI/Q&A | 3-0 / 2-1 | 可 runtime 跑(no fine-tune);**但 E2E 變體 5x variance(std 0.044)再次印證 per-answer 不穩** |

### 3.2 方向 B — 圖文錨定 / 高召回 ≠ 正確錨定(EKP 已實作 section 級)

| 來源 | 票 | EKP 意義 |
|---|---|---|
| **UniDoc-Bench**(arXiv 2510.03663,2025-Q4)— image retrieval 一致 higher recall / lower precision(text 0.796R/0.406P vs image 0.829R/0.275P),作者明言「completeness 優勢不轉化為更好 end-to-end」| 2-1;**「text-image fusion 勝」子claim 反證 0-3** | **再次獨立確認 EKP「高召回≠正確錨定」係業界已知未解難題,非 EKP bug**;反證項**支持 EKP 唔做 image embedding 嘅決定** |
| **LAD-RAG**(arXiv 2510.07233,2025-10)— ingestion-time symbolic document graph(reading-order / section / figure-caption linkage)+ neural embeddings 並存 | 3-0;**「core problem = oversummarisation」子claim 反證 1-2** | ingestion-time 細粒度 metadata 方向最新實例;**但依賴 LVLM at ingestion → 撞 EKP no-multimodal 約束**,只 metadata 思路(reading-order/caption)可借鑑,唔可照搬 |

---

## 4. 硬約束下嘅明確 kill list（慳走冤枉路）

研究最實用嘅一部分 —— 直接排除一整類喺 EKP locked stack 上**結構性不可用**嘅方法:

1. **標準 self-consistency / temperature-based best-of-N** ❌ — `gpt-5.5` 拒 temperature≠1 → 多樣本塌縮,best-of-N 效益中和。
2. **self-certainty selection** ❌ — 需 full-vocabulary logits,Azure `gpt-5.5` reasoning 回 null,算唔到。
3. **S-RAG schema-guided** ❌ — 需 homogeneous single-schema 語料,唔啱 heterogeneous SOP。
4. **LAD-RAG 整套** ❌(部分)— LVLM at ingestion 撞 no-multimodal 約束;只 metadata 重建思路可借。
5. **image embedding / multimodal fusion retrieval** — UniDoc 反證「fusion 勝」(0-3),**佐證 EKP 唔做嘅決定**。

**仍存活嘅 sampling-free 路**:DIPPER(prompt-variation ensemble)+ EVE / query decomposition(multi-call structured)+ Auto-Merging(retrieval 層)。

---

## 5. 對 EKP 既有決定嘅驗證

| EKP 決定 | 外部佐證 | 結論 |
|---|---|---|
| **W97 revert coverage-prompt**(2026-06-26)| CRUX generation-ceiling(prompt 郁唔到天花板)| ✅ 方向正確 |
| **W96 放棄 per-answer gate、只 aggregate A/B** | AutoNuggetizer per-topic tau 0.30-0.54 + comprehensiveness E2E 5x variance | ✅ 雙重獨立佐證,本輪最 solid 嘅發現 |
| **唔做 image embedding / multimodal retrieval** | UniDoc「fusion 勝」被反證 0-3 | ✅ 支持 |
| **image-recall 弧追全圖召回**(W59-68 ~1.0)| UniDoc「high recall ≠ correct grounding」 | ⚠️ 召回已封頂,真痛點喺錨定 precision(同 EKP W83 診斷一致)|

---

## 6. 最關鍵 Open Question(會改變方向優先序)

CRUX 個 **62-65% generation ceiling 係用 Llama-3.1-8B 量**。**若 `gpt-5.5` 喺 EKP SOP 場景 ceiling 接近 90%+,咁乙類根因就唔係 generation,而係偏返 retrieval / anchoring** → 方向 A(generation-side 替代)大部分白費,應轉去步驟級錨定(方向 B)。

→ **未實測前,方向 A vs B 優先序就係估。** 而呢個診斷 = **fixed-context oracle A/B(畀完美 context 量 GPT-5.5 還原上限),零 production 改動**,可用現有 W96 harness 改。**建議任何後續 implementation 之前先做呢個診斷。**

---

## 7. 建議 ROI 排序(全部係待驗證假設,非已證手段)

1. **(零成本診斷,最該先做)** fixed-context oracle ceiling 測試 — 決定後面一切(ceiling 高 → 轉錨定;低 → DIPPER/EVE 值得試)。
2. 若郁完整度:**section-merge parent retrieval**(延伸現有 `parent_doc`,runtime 層,成本最低)。
3. **VITAL** importance-weighted coverage:小規模試,睇能否令 per-answer signal 變可用。
4. **DIPPER / EVE**:工程成本高 + domain transfer 未證,排最後。

---

## 8. Caveats(誠實交代,避免 over-claim）

1. **Domain mismatch 係最大不確定性** — 幾乎所有來源 domain 都唔係 SOP/企業手冊(news / safety patents / hotels / Wikipedia),generator 多係 8B 小模型或非 `gpt-5.5` reasoning。對 EKP 場景**全部未直接驗證**,只能講 mechanistically plausible。
2. **Best-case framing** — 帶數字嘅 finding(S-RAG 0.845/0.909、EVE +24%/29%/31%、LAD-RAG >90% recall)全部作者自報、strongest-config / gold-schema / aggregate-only;實際可部署版大幅退化(S-RAG auto-schema 0.845→0.500;LAD-RAG「perfect recall」係自訂 binary metric 非標準 IR recall)。
3. **時間敏感** — VITAL / LAD-RAG / EVE 仍係 preprint 未 venue peer-review;CRUX / comprehensiveness / AutoNuggetizer / query-decomp / S-RAG 係 peer-reviewed/peer-track。
4. **measurement vs fix** — 最 solid 嘅係 measurement-side 佐證(per-answer 不可靠);**fix-side 一個都未喺 EKP 場景證過**。
5. **未做反證** — CRUX 62-65% ceiling 用 8B 模型,`gpt-5.5` ceiling 可能顯著更高;「generation-side ceiling 係主因」對 EKP 嘅定量強度**未驗**(正係 §6 open question)。

---

## 9. 來源清單(主要 confirmed,標 quality）

| URL | quality | 方向 | 票 |
|---|---|---|---|
| https://arxiv.org/abs/2506.20051(CRUX,EMNLP 2025)| primary | generation ceiling + coverage metric | 2-1 / 3-0 |
| https://arxiv.org/html/2504.15068v1(AutoNuggetizer,TREC 2024)| primary | per-answer 不可靠佐證 | 2-1 |
| https://developers.llamaindex.ai/python/examples/retrievers/auto_merging_retriever/ | vendor docs | parent-section retrieval | 3-0 |
| https://arxiv.org/pdf/2511.08505(S-RAG,ICLR 2026 review)| primary | schema-guided(不適配)| 3-0 |
| https://arxiv.org/html/2510.18633(query decomposition,EACL 2026)| primary | subquery 補齊 | 3-0(perf 反證 0-3)|
| https://arxiv.org/pdf/2412.15238(DIPPER,NeurIPS 2024 workshop)| primary | sampling-free ensemble | 3-0 |
| https://arxiv.org/abs/2602.06103(EVE,2026-02)| primary | multi-call extraction | 2-1 |
| https://arxiv.org/pdf/2502.18581(Self-Certainty)| primary | self-consistency 不可用佐證 | 2-1 |
| https://arxiv.org/abs/2510.07926(comprehensiveness metrics,ACL 2026)| primary | 完整度量度 | 3-0 / 2-1 |
| https://arxiv.org/abs/2510.07083(VITAL,2025-10)| primary | importance-weighted coverage | 3-0 |
| https://arxiv.org/abs/2510.07233(LAD-RAG,2025-10)| primary | ingestion graph 錨定 | 3-0 |
| https://arxiv.org/html/2510.03663v2(UniDoc-Bench,2025-Q4)| primary | 高召回≠錨定 | 2-1 |

> **統計**:6 angles / 28 sources fetched / 127 claims / 25 verified / **19 confirmed / 6 killed** / 14 after synthesis / 111 agent calls。

### 被反證項（6,透明列出,避免誤用）

1. query decomposition「35% precision / 15% α-nDCG gain」(0-3)→ 只取 trade-off 框架,不取數字。
2. self-certainty「只係 selection metric,candidate 仍需 temperature sample」(0-3)→ 但反證理由本身 = 對 EKP 有用結論(temperature 路塌縮)。
3. 「coverage metric 比 recall 更 predict answer completeness」(0-3)→ 不應宣稱 coverage 係更強 proxy。
4. 「EVE 係純 prompt 框架打破 coverage-accuracy trade-off」(1-2)→ EVE 係 multi-call pipeline 非純 prompt。
5. 「LAD-RAG core problem = oversummarisation」(1-2)→ LAD-RAG 解 page-level evidence retrieval 非 over-summarisation。
6. 「text-image fusion 勝 text-only + joint multimodal」(0-3)→ **支持 EKP 唔做 image embedding**。

---

## 10. 與前兩輪 + W96/W97 嘅銜接

- **第一輪(2026-06-20)4 方向** ← 本輪補:方向 1(錨定)有 LAD-RAG 新實例 + UniDoc 再確認「高召回≠錨定」;方向 3(乙類完整度,第一輪覆蓋最弱)本輪由「open question」變成「有方向但全 domain-mismatch + 根因係 generation ceiling」。
- **第二輪(2026-06-25,乙類方向 A,未存檔)** → 結論 fold 入 W96 完整度 gate + ADR-0069;本輪**反證咗嗰輪嘅 prompt-coverage 假設**(W97 已實證 + revert),並補上「點解失敗」嘅外部解釋(generation ceiling)。
- **W96 完整度 gate** ← AutoNuggetizer + comprehensiveness 雙重佐證「per-answer 不可靠、只可 aggregate」決定正確。
- **W97 coverage-prompt revert** ← CRUX generation-ceiling 解釋「prompt 郁唔到天花板」;ADR-0069 §Outcome「乙類唔係穩定可 prompt-fix 嘅系統性缺陷」獲外部佐證。

---

**End — 本文件係外部實證調查 brief,非 implementation order;決策權喺 Chris。下一步建議先做 §6 零成本 ceiling 診斷再定方向。**
