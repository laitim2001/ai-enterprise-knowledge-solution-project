# ROADMAP — 自助可調配置 Vision(per-KB / per-document tunable config)

> **性質**:策略藍圖(candidate roadmap)。**唔係** pre-created phase plans —— 每期 kickoff 先正式建 `W{NN}-*/plan.md`(守 CLAUDE.md §10 rolling JIT R1)。本文件純為「睇清全圖 + 拍板決策」用。
> **建立**:2026-06-02(W43 closeout 後)
> **Owner**:Chris(技術 Lead)
> **錨點**:ADR-0040(per-KB config-scope,Accepted)+ memory `project_per_kb_tunable_config_vision`(foundational vision)+ W43 phase folder
>
> **🔍 Audit 校準(2026-06-03)**:本文件經三個獨立 session 落 code 交叉審查(問題:可行性 + 能否達到所述預期效果)。**核心結論不變 —— 可行、診斷準、Tier 邊界誠實**;但 5 處表述按 code-grounded 證據校準,inline 標 `[AUDIT-A]`..`[AUDIT-E]`:
> - **[AUDIT-A]** 圖數實測 **20–57 張**(峰值 `ci=15=57`),原文「33/20」係示意數且**低估**嚴重性 —— 反而強化 W44 必要性。
> - **[AUDIT-B]** W44 可經**現成 doc-level reindex**(`documents.py:786-884`,非 stub)獨立驗證,**唔懸空、唔卡 W45/Track A**。
> - **[AUDIT-C]** Track A 擋嘅係 **production 零 downtime 安全 reindex**,**唔係**「能否建造 / 能否 demo」—— 兩層,唔好一刀切。
> - **[AUDIT-D]** 自助試跑 harness **只有 presentation 軸,缺 RAGAs 質素軸**(ADR-0040 自己定義咗雙軸卻未喺自助面交付)→ 補分兩步 item。
> - **[AUDIT-E]** W46 retrieval 旋鈕 per-doc 解析語意問題;Layer C 嘅 Tier 線重畫成「**章節語意(T1)vs 視覺內容語意(T2)**」。

---

## §1 Vision(用戶 foundational framing)

> 唔同文件因格式內容唔同,需要唔同嘅 **process(切 chunk / 解析)+ retrieval(查詢時)策略**。呢啲策略要可以落到 **per-KB(或 per-document)**作用域;UI 要備齊**完整詳細嘅配置**,畀用戶**自己調整 + 平台試跑驗證,直至滿意先持久化**到該 KB —— 而**唔係**好似開發階段噉,一直喺後台代碼改 / 修。

落到工程,vision 拆成 **2 條正交軸 + 1 個自助閉環**:

```
              Process(切 chunk / 解析)       Retrieval(查詢時策略)
              ─────────────────────         ──────────────────────
  全域          (今日基線)                     (今日基線)
  per-KB        ❌ 未做 → W44 / W45            ✅ W43 已做
  per-document  ❌ 未做 → W46(視乎決策 1)      ❌ 未做 → W46(視乎決策 1)

  + UI 自助配置面 + 平台試跑 loop:
      Retrieval 側 🟡 W43 已做(presentation 軸)| 質素軸(RAGAs)❌ 未做 | Process 側 ❌ 未做(W45)
```

memory 嘅 3 正交層對應:
- **Layer A — per-document profile** → 本 roadmap 決策點 1 + W46。**自動 seed 機制深化**（用 multimodal LLM 讀文件 → 自動產出建議 config + bootstrap 評測）見 **[addendum:LLM Document-Profiler](./ROADMAP-per-kb-tunable-config-addendum-llm-profiler.md)**（design-proposal,Tier 2 定位,未 ADR;2026-06-03 brainstorm 完整留底）
- **Layer B — query-intent gate**(列舉 vs 具體)→ 條件觸發期
- **Layer C — image relevance**(揀啱嗰幾張圖)→ **章節語意揀圖 = Tier 1 可達**(W44 metadata + 既有 section-aware attach)/ **視覺內容語意揀圖 = Tier 2 閘**(見 §3 [AUDIT-E] 重畫)

---

## §2 已交付:W43(地基,STRONG PASS 2026-06-02)

填咗 **「Retrieval × per-KB + 自助 loop」** 嗰格:
- 12 個 runtime 旋鈕(parent_doc / citation_expansion / citation_neighbour + `max_images_per_answer`),`KbConfig` Optional 欄位,`None`=繼承全域。
- `EffectiveConfig` resolver:**per-query > per-KB > 全域** 優先序。
- `POST /kb/{id}/config-test` 平台試跑 harness(multi-run + variance band + A/B)。
- UI:KB Settings 配置面(分組 + 進階收合 + 繼承/覆寫態)+ 試跑面板。
- 驗證:G2 live 2-KB(AR 保守 3cit/8img + DCE inherit 5/5,全域零改)+ 雙軸 no-regression(**注:雙軸喺 phase gate F4.2 另跑 `/eval/run` 達成,見下局限**)。

**[AUDIT-D] 自助 loop 嘅雙軸缺口(誠實補)**:config-test harness 出嘅信號**只有 presentation counters**(citation / figure raw+dedup / latency / answer_chars / refused,`config_test.py` `RunMetrics` 證)—— **無 RAGAs 質素軸**。雙軸的 RAGAs 半邊只喺 phase gate(F4.2)另跑 `/eval/run`,**唔喺用戶日常自助 loop 內**。即 ADR-0040 Decision §3「harness 必須出雙軸信號」**未喺自助面交付**:用戶撥旋鈕「調到滿意」,目前只係 presentation 層面滿意,**見唔到 faithfulness 由 0.99 跌到 0.85**。補法見 §3 NEW「質素軸」item。

**局限**(誠實,**[AUDIT-A]+[AUDIT-D]**):
- **圖洪水鈍刀**:只做到 `max_images_per_answer` cap(砍到 N 張,但揀唔到邊 N 張先啱)。單一 mega-chunk 自帶圖數**實測 20–57 張**(峰值 `ci=15=57`,memory `project_chat_demo_rag_quality_followups` #7;原文「33 圖」係示意數且**低估** —— 真峰值 57 比 33 嚴重 73%)—— ingestion-bound,runtime 解唔到根。
- **自助驗證單軸**:試跑 harness 只見 presentation(圖/citation 數),**見唔到答案 faithfulness/correctness 退步**(見上 [AUDIT-D])。

---

## §3 多期 Roadmap(candidate)

| 期 | 區塊 | 解決乜 | Tier | 依賴 | 關鍵決策 |
|---|---|---|---|---|---|
| ✅ **W43** | per-KB retrieval 配置 + UI + 試跑 loop | retrieval 策略自助(presentation 軸),唔使改後台 | T1 | — | (已完成) |
| ✅ **W48**(本期)| config-test 加 reference-free `faithfulness` | 自助 loop 補**質素軸**(反幻覺半邊)| T1 | W43(**不卡 Track A / 不需標註集**)| ✅ **shipped 2026-06-05**(收 AUDIT-D / ADR-0040 雙軸:`ConfigRunSummary.faithfulness` + `make_faithfulness_evaluator` additive helper + 試跑 panel 忠實度 headline;每 config 算一次 cost-conscious;graceful None;judge 維 gpt-5.4-mini。**runtime config-test only** — ingestion config 質素需 reindex→eval 屬未來)|
| ✅ **W49**(本期)| config-test faithfulness N-run band 抗噪 | 解忠實度單次計算噪音(同一 SAVED config 兩跑 0.929↔0.53)| T1 | W48(不卡外部依賴)| ✅ **shipped 2026-06-05**(決策 7 Option 1:`ConfigRunSummary.faithfulness` float→`MetricBand`;`_faithfulness_band` 逐 run judge `asyncio.gather`;N≥2 顯示 mean±band / N=1 單值+warning;成本 = 用戶 `runs`;judge 維 gpt-5.4-mini;無新 ADR)|
| ✅ **W44** | Chunker 深層修(ADR-0041,切法 D + cap 8)| 圖洪**根治**(實測 57→8)+ process 策略基礎 | T1 | —(doc-level reindex 驗證,不卡 Track A)| ✅ **closed 2026-06-04 Gate PARTIAL→PASS**(recall/faith flat + corr −2.28pp answer_relevancy noise + 三源證實 = no-regression;SME eval-set-v1-draft validated 順帶解 Q14)|
| ✅ **W45**(本期)| per-KB 圖數 cap → KbConfig(ADR-0042)| W44 全域 cap 8 → **per-KB 可調**(延 ADR-0040 config-scope 由 query-time 到 **ingest-time**)| T1 | W44 + reuse W20 F4.2 `kb_config` ingest 路徑(不卡 Track A)| ✅ **shipped 2026-06-04**(`KbConfig.chunker_max_images_per_chunk` None=inherit/正整數=cap;`_select_chunker` + factory wiring;+5 test 0 regression;**UI 暴露 out-of-scope** → 下方「UI ingestion 配置」候選)— 收 W44 carry-over「per-KB 圖數 cap 降 KbConfig」|
| ✅ **W46**(本期)| UI 開放 ingestion 配置 + **真** KB-level re-index(ADR-0043)| process 策略**上 UI 自助**(per-KB cap + chunk_strategy 解鎖)+ 真 KB-level reindex(dev/demo 層)| T1 | W45 per-KB cap + 原始檔 blob 儲存(ADR-0043)| ✅ **shipped 2026-06-05**(原始檔 `-sources` container + `run_kb_reindex` in-place + Settings unlock chunk_strategy/圖數cap + Reindex modal/summary;**prod v1→v2 原子切換仍 Track A** per 決策 4)|
| **後續候選 — per-document**(原標 W46;名讓予本期 ingestion-config phase)| per-document scope | 一個 KB 溝多格式文件 | T1 | W43 resolver(加一層;**[AUDIT-E]** retrieval 旋鈕語意見下)| **決策 1(per-KB 夠未)** |
| 條件觸發 | Query-intent gate(Layer B)| 自動辨查詢類型揀配置 | T1(heuristic)| W43 | 需唔需要 |
| ⚠️ Tier 2 | Image relevance ranking(Layer C 深層)| 按**視覺內容**相關性揀圖(**章節**相關性 = T1,見下)| **T2** | W44 metadata | 決策 3(Tier 2 閘)|
| 操作期(**presets 宜提前**)| config 版本史 / presets / who-can-edit 審計 | 配置生命週期成熟度;**presets 係自助可用性 enabler,唔應排最後** | T1 | W43 | 決策 5(優先序)|

### 逐期重點

- **W44 — Chunker 深層修(最高價值 next)**
  - 根因(W43 live 證,**[AUDIT-A]**):圖密 mega-chunk 自帶圖數**實測 20–57 張**(`ci=15=57 / ci=8=27 / ci=31=25`,memory #7)→ 切 chunk 時把成節「System Instruction」連截圖塞晒入一個 chunk;chunker **零 per-chunk 圖數上限**(`ingestion/chunker/layout_aware.py` 只有 1500-token hard cap)。
  - 做乜:圖密章節**細分** + 標 per-image metadata,令檢索攞到「啱嗰幾張」而非一嚿 57 圖。
  - 為何另起一期:改 `architecture.md §3.3` chunker + **要重新索引** → H1 架構改動 → **ADR-0041**。
  - 純 Tier 1,唔使等 Azure/Track-A。**[AUDIT-B] 驗證路徑現成**:改完即可用 `POST /kb/{id}/documents/{doc_id}/reindex`(真刪 + 真 `_run_ingest_pipeline`,`documents.py:786-884`,**非 stub** —— 有別於 KB-level `kb.py:252-280` 嗰個 stub)對單份文件驗效果。**唔懸空、唔等 W45**(W43 重建 `drive_user_manuals` 287 chunks 就係行緊呢條 pipeline)。

- **✅ W45(本期)— per-KB 圖數 cap → KbConfig(ADR-0042,shipped 2026-06-04)**
  - W44 落地嘅 `chunker_max_images_per_chunk` 全域 cap 8 → **per-KB 可調**:`KbConfig.chunker_max_images_per_chunk`(`None`=inherit 全域 / 正整數=該 KB cap;per-KB 不能設無 cap,只全域 level 設得到)。
  - 延伸 ADR-0040 per-KB config-scope 由 **query-time** 到 **ingest-time** —— ingest 時 `documents.py:_select_chunker(deps, kb_config)` 解析:`None` reuse 全域 singleton(零 construct,bit-identical),設值經 `app.state.make_ingestion_chunker` factory 砌 per-ingest chunker。
  - reuse W20 F4.2 已 thread 嘅 `kb_config` ingest 路徑;窄 scope = backend 欄 + wiring + test,**經既有 `PATCH /kb/{id}/settings` 可設,唔加 endpoint**;UI 暴露留下方候選。re-index 先生效(同 W44)。

- **✅ W46(本期,shipped 2026-06-05)— UI 開放 ingestion 配置 + 真 KB-level re-index(ADR-0043)**
  - **已交付(dev/demo 層)**:(1) 原始檔 blob 儲存 `ekp-kb-{kb_id}-sources`(`source_store.py`,ingest best-effort persist)— 解開「真 reindex 要 re-parse 原檔但原檔冇存」root blocker;(2) `POST /kb/{id}/reindex` stub→真(`run_kb_reindex` iterate docs → 由 `-sources` download → 每 doc in-place delete+reingest via BytesIO-UploadFile adapter 復用 `_run_ingest_pipeline`);(3) Settings UI 解鎖 `chunk_strategy` + NEW per-KB 圖數 cap 欄(embedding 維 locked)+ Reindex 卡 confirm modal + per-doc summary(H7 design-first per ADR-0024)。pre-W46 無原檔 doc → `skipped_no_source` report。
  - **production 層仍 Track A**(下方兩層拆解不變):in-place 接受短暫不一致窗口;v1→v2 原子切換 + R@5 gate + Standard S1 屬決策 4 後置。
  - _(以下為原候選 design rationale,仍適用作 dev-vs-prod 兩層 context)_
  - 今日 `chunk_strategy` / embedding 喺 UI **locked**;**KB-level** `POST /kb/{id}/reindex` 係 **stub**(假 task_id,no-op,`kb.py:252-280`)。但 **doc-level** `documents/{doc_id}/reindex` 已係 **real**(見 W44),KB-level 只係未串。本期 per-KB cap 已開後端 config foundation,呢個候選 = UI surface + 真 KB-level reindex。
  - **[AUDIT-C] 兩層,唔好一刀切**:
    - **dev / demo 層(不卡 Track A)**:KB-level reindex 可由「iterate docs → 逐個 reuse 現成 doc-level reindex」砌出 + 喺現有 dev Free-tier Azure Search 測試。**整個 process-軸自助 loop 可以 demo,唔等 Track A。**
    - **production 層(雙閘)**:對 live KB 改切法 = 重切所有文件,in-place 有「舊 chunk 已刪、新 chunk 未上完」**不一致窗口** → 要 **v1→v2 索引原子切換**(net-new infra,`kb_naming.py` 目前固定 `-v1`、無 alias、in-place)**+ R@5 gate**,再加 **Track A(Standard S1 + IT cred)**。
  - ⚠️ 所以卡 Track A 嘅係「**production 零 downtime 安全 reindex**」,**唔係**「能否建造 / 能否 demo」。決策 4 因此可後置(先 W44 + W45-dev 證價值,production 化投資再排)。

- **後續候選 — per-document scope(原標 W46;名讓予本期 ingestion-config phase)**
  - resolver 加一層:**per-query > per-document > per-KB > 全域**(additive,延伸 W43)。
  - **[AUDIT-E] 兩類旋鈕 per-doc 解析語意唔同(「加一層」唔係全部都成立)**:
    - **可乾淨 resolve**:ingestion 旋鈕(切法)每份文件獨立 → 零歧義;post-retrieval **per-citation** 旋鈕(`citation_expansion` / `neighbour_images`)→ 「此 citation 屬 doc X → 用 doc X 值」可行。
    - **語意未定義**:**KB-wide 初始檢索**旋鈕(`default_top_k` / hybrid 搜索本身)係整個 index 一齊搵,**搵完先知道結果屬邊份文件** → 一個答案跨多份 config 唔同文件時用邊個值,「加一層」回答唔到。W46 真難點喺此,要另想 resolve 語意(或限 per-doc scope 只作用於 ingestion + post-retrieval 旋鈕)。
  - 觸發條件 = 決策 1(KB 會唔會溝多格式)。

- **✅ W48(本期,shipped 2026-06-05)— config-test 補質素軸 [AUDIT-D / ADR-0040 雙軸]**
  - 自助 loop 目前單軸(presentation),用戶見唔到 faithfulness 退步(見 §2 局限)。
  - **分兩步**(避開「per-KB 標註集 vs 非技術自助」嘅內在張力):
    - **✅ (i) 已交付(W48)**:config-test 加 **reference-free `faithfulness`**(只量「答案宣稱是否被檢索 context 支撐」,**不需 ground truth**)。實作:`ConfigRunSummary.faithfulness` + additive `make_faithfulness_evaluator`(judge `gpt-5.4-mini`)+ 試跑 panel 忠實度 headline。**成本決策修正**:由 plan 原「每 run + opt-in toggle」改為 **每 config 只算一次**(last-run,無 toggle keep H7 surface 細),judge 內部多次調用故單次更穩。graceful None(無 judge / error)。
    - **(ii) 後期**:`correctness` / `context_recall` 需 per-KB 標註集 → 留工程閘或 synthetic-QA auto-gen;唔強塞自助面。**ingestion config 質素**(chunk_strategy / 圖數cap)config-test 試唔到(query-pipeline-only)→ reindex→eval 屬另一機制,留未來期。
  - **ROI 最高 next 候選 — 已實現**:不卡 Track A、不卡 chunker,補 ADR-0040 自己定義咗卻未交付嘅雙軸前提。

- **✅ W49(本期,shipped 2026-06-05)— faithfulness 質素軸抗噪 N-run band(決策 7 Option 1)**
  - **已交付**:faithfulness 由「每 config 算一次」改為 **逐 run judge 聚合成 `MetricBand`**(同 presentation band 一致)——`_faithfulness_band()` 用 `asyncio.gather(asyncio.to_thread(...))` 並發逐 run judge,band over judge 成功嘅 run(graceful);panel N≥2 顯示 `mean ± band`(揭噪音)/ **N=1 單值 + 「單次 judge · 方向性」warning**。**judge 成本 = 用戶揀嘅 `runs`**(無新 toggle,Chris AskUserQuestion Option 1);judge 維 `gpt-5.4-mini`;無新 ADR(extend ADR-0040 雙軸)。backend +3 test / frontend +1 test。
  - **採用 Option (a) N-run band**(下方候選做法)+ **(c) N=1 warning**;**(d) length-bias 標示** → ✅ **W50 shipped**(平 part:UI explainer affordance);**(d) completeness 對沖指標** → ✅ **W51 shipped**(ideal 半邊:**「涵蓋章節數」(distinct-sections-cited)per-run band** = coverage proxy 擺 faithfulness 旁,caveat 指向佢;誠實標明 **proxy 非 ground-truth recall**)。**synthetic-QA 真 recall** → ✅ **W52 shipped**(更深半邊:offline 工程閘 `backend/eval/synthetic_qa.py` — 由 KB chunk LLM 生成問題,source chunk = ground truth,餵現有 `EvalRunner` strict-mode 量 self-supervised Recall@K;**非人手 ground-truth recall**,bias disclosure 見 eval-methodology.md §10.6;**兩者合一 W52 基建** → W53 reindex strategy 比較候選)。
  - **現狀(交付前)**:W48 faithfulness **每 config 只算一次**(last-run,無 N-run band)為省 judge 成本(plan §2 刻意取捨)→ single-shot 噪音大。
  - **2026-06-06 live 實測證據①(噪音)**:同一個 `drive_user_manuals` **SAVED config**(全繼承=好預設),兩次試跑(API run vs UI run,相隔約 4 分鐘)faithfulness **0.929 ↔ 0.53**,擺動 ~0.4;presentation 軸(引用數 23.5、圖片 ~60)同期穩定。即噪音集中喺質素軸單次 judge eval(長答案 3370 字 + 58 圖 context judge 易擺)。
  - **2026-06-06 live 實測證據②(反轉 / length bias — 更強)**:列舉型 query(「list every step…」)退化 vs 好預設 A/B,presentation 軸戲劇化(引用 2.5 vs 15.0=6×、distinct sections 1 vs 3、答案字數 1246 vs 4486=3.6×)= 完整性差異真實;但 faithfulness **反轉** —— 更完整嘅 SAVED 答案 **0.019**,退化短答案 DRAFT **1.0**。根因:RAGAs faithfulness **系統性懲罰長/全面答案**(claim 多 → 未逐句對上大 context 機會大)→ **質素軸可能同完整性反相關**,對列舉/綜合型 query 尤其誤導。
  - **風險**:用戶試跑「撥到滿意」可能基於一次好彩/差彩 judge run 誤判 config —— 對齊 memory `project_synthesizer_overview_refuse_w25_d4` 嘅 W25 D4 stochastic-run over-claim 教訓(同一模式套落 W48 質素軸)。
  - **候選做法**(權衡 judge 成本,維 gpt-5.4-mini per memory `feedback_judge_llm_cost_policy`):(a) faithfulness 加 N-run band(同 presentation band)→ judge 成本翻 N 倍;(b) 加「忠實度需 ≥K 次重跑先可信」warning gate(最平);(c) 維持單次但 UI 明標「方向性、勿單次定論」;(d) **NEW(證據② 驅動)**:UI 明標 faithfulness 對長答案有 **length bias**、勿與 completeness 混為一談;理想配 completeness/recall 對沖指標(對齊 addendum §4 槓桿 6「偏向檢索錨定而非答案相似度」)。
  - 純 Tier 1,不卡 Track A / 不卡 chunker。決策 7 → ✅ **RESOLVED(W49 Option 1)**。

- **Layer B — query-intent gate(條件觸發,非排定)**
  - 證偽實驗已證 AR **唔需要**(避免 over-engineer per Karpathy §1.2);留 seam,遇「缺 summary chunk」文件先觸發。

- **Layer C — image relevance([AUDIT-E] Tier 線重畫)**
  - **Tier 線唔係畫喺「位置 vs 語意」,而係「章節語意 vs 視覺內容語意」**:
    - **章節相關性 = Tier 1 可達**:BUG-027 已 ship 嘅 `_find_section_neighbour_images`(`citation_neighbour_section_path_prefix_depth`)已做「只 attach 同章節嘅圖」;W44 切細 chunk + per-image section metadata 令呢個 section-matching **更精準**。對結構良好嘅手冊,「同章節嘅圖」往往**就係**對嘅圖 —— 唔使 vision 模型。
    - **視覺內容相關性 = Tier 2**:「呢張圖是否真係展示咗問嘅嘢」需 vision/relevance 模型 = **multi-modal retrieval**(H4 邊界,需新 ADR + stakeholder)。
  - 即 W44 + 既有 section-aware attach 能把「揀圖」推到**章節精度**,多數 use case 可能**已經夠好**;Tier 2 vision 揀圖係錦上添花而非必需。

---

## §4 依賴關係

```
W43(done)
  ├─→ W44 chunker(ADR-0041)─[驗證:現成 doc-level reindex,不卡 Track-A]
  │     ├─→ W46 UI ingestion ─ ✅ dev/demo shipped 2026-06-05(原始檔 storage + 真 KB reindex + Settings unlock,ADR-0043)
  │     │                    └─ production:v1→v2 原子切換 + ⚠️Track-A(仍未做)
  │     └─→ Layer C:章節語意(Tier 1,已部分 ship)| 視覺內容(⚠️ Tier 2 閘)
  ├─→ 後續候選 per-document(原標 W46;resolver 加層;retrieval 旋鈕語意待解;視乎決策 1)
  ├─→ Layer B query-intent(條件觸發)
  ├─→ NEW 質素軸:config-test + reference-free faithfulness(並行,零阻塞)
  └─→ 操作期(版本史 / presets〔宜提前〕/ 審計)
```

---

## §5 你要拍板嘅 6 個決策點

| # | 決策 | 影響 | 預設傾向 |
|---|---|---|---|
| **1** | **per-KB 夠,定要 per-document?** | 決定 W46 做唔做 | KB 放同類文件 → per-KB 夠;會溝格式 → 要 per-document |
| **2** | **W44 切法策略** | 圖密章節點切(按圖數上限 / 子標題 / 段落)| W44 kickoff 時 ADR-0041 評 |
| **3** | **Tier 2 閘** | 「按**視覺內容**相關性揀圖」開 Tier 2 multi-modal?(章節相關性 Tier 1 已可達,見 Layer C)| 預設守 Tier 1(H4)|
| **4** | **production 安全 reindex 投資時機**(**[AUDIT-C]** 重定義)| **非**「等 Track A 先能動」—— dev/demo 唔卡;呢個係「幾時投 v1→v2 原子切換 + Track A 做 production 零 downtime」 | 先 W44 + W45-dev 證價值,production 化後置 |
| **5** | **深度 vs 廣度優先** | 先 W44(根治圖洪)定先 W46(覆蓋更多文件)? | 建議深度優先(W44)|
| **6** | **質素軸 next?**(**[AUDIT-D]** NEW)| config-test 加 reference-free faithfulness(解自助 loop 盲點,不卡外部依賴)排幾前? | ✅ **RESOLVED — W48 shipped 2026-06-05**(高優先 ROI 最高拍板先行) |
| **7** | **faithfulness 抗噪策略**(NEW 2026-06-06 live 證)| W48 質素軸 single-shot 噪音(SAVED 同 config 兩跑 0.929↔0.53)→ 加 N-run band(judge 成本翻倍)/ warning gate / 維單次標「方向性」 | ✅ **RESOLVED — W49 shipped 2026-06-05**(Chris 揀 Option 1「沿用重跑次數做 N-run band」;成本 = 用戶 `runs`,N=1 配 warning)|

---

## §6 建議下一步

**兩條並行、都唔卡外部依賴**:
1. **W44 chunker 深層修**(深度優先):(a) 圖洪係反覆撞到嘅具體痛點(實測峰值 57 圖);(b) W44 係 process 策略地基,W45 自助 UI + Layer C 都靠佢;(c) 純 Tier 1,**且驗證路徑現成**(doc-level reindex,**[AUDIT-B]**)。
2. **config-test 補 reference-free faithfulness**(**[AUDIT-D]**,正交可並行):解自助 loop 單軸盲點,不卡 chunker / 不卡 Track A,直接補 ADR-0040 雙軸前提 —— **ROI 最高**。

per-document(W46)等決策點 1 拍板先排;production 化 reindex(原子切換 + Track A)按決策 4 後置(**唔阻 W44 / W45-dev / 質素軸**)。

---

## §7 Cross-ref
- **[addendum:LLM Document-Profiler](./ROADMAP-per-kb-tunable-config-addendum-llm-profiler.md)** — Layer A 自動 seed 機制（multimodal LLM 讀文件 → 建議 config + bootstrap 評測 + 循環論證防禦 + probe 質素 + Gate D + 兩集 governance）;design-proposal,Tier 2,未 ADR（2026-06-03 brainstorm 完整留底）
- ADR-0040 — per-KB config-scope(Accepted;W43 validated STRONG PASS)
- W43 phase folder `docs/01-planning/W43-per-kb-tunable-retrieval-config/`(plan / checklist / progress)
- memory `project_per_kb_tunable_config_vision`(foundational vision + 證偽實驗)
- memory `project_chat_demo_rag_quality_followups`(#7 圖洪 實測 `ci=15=57` + #8 W43 F1 live A/B + ingestion-bound 證據)
- architecture.md §3.3(chunker — W44 觸及)/ §3.1 + §3.7(retrieval config — W43 已改)
- **Audit code anchors(2026-06-03)**:`backend/generation/effective_config.py`(resolver)/ `backend/api/routes/config_test.py`(試跑 harness,presentation-only `RunMetrics`)/ `backend/api/routes/kb.py:252-280`(KB-level reindex **stub**)/ `backend/api/routes/documents.py:786-884`(doc-level reindex **REAL**)/ `backend/ingestion/chunker/layout_aware.py`(零 per-chunk 圖數閘)/ `backend/api/schemas/kb.py:62-73`(13 旋鈕)

---

**狀態**:living roadmap。每期 kickoff 正式建 phase folder 時,回頭 update 本表對應行(done / 決策已拍板)。

**修訂史**:
- **2026-06-06 W52 shipped → 決策 7 Option (d) 更深半邊 done(synthetic-QA 真 recall — offline 工程閘)** —— 補返 W51 留低嘅真 recall 半邊,但**唔放 config-test panel**(ROADMAP line 107「synthetic-QA auto-gen → 留工程閘」)。NEW offline harness `backend/eval/synthetic_qa.py`(C06):由 KB indexed chunk LLM 生成問題(gpt-5.4-mini;source chunk = ground truth)→ formatted `acceptable_chunk_ids=[source]`+`validated=True` 餵現有 `EvalRunner` strict-mode(**零新 recall 數學**)→ self-supervised Recall@K。Reuse judge client(`patch_for_gpt5`)+ chunk 枚舉(`list_documents`/`list_chunks`/NEW `RetrievalEngine.fetch_by_chunk_ids` passthrough,R3 deviation)。Live driver `scripts/run_synthetic_recall.py`。**誠實 framing(R1)**:self-supervised synthetic recall **非人手 ground-truth recall**(bias disclosure eval-methodology.md §10.6;用途 = 相對比較非絕對 verdict)。Chris AskUserQuestion 揀 **兩者合一** → W52 recall 基建 / W53 reindex strategy 比較(rolling JIT 不預寫)。無新 ADR/vendor/dep;backend-only 無 H7;eval suite 65 passed + test_retrieval 31 passed 0 regression。commit `97acd8b`;phase folder `W52-synthetic-qa-recall-harness/`。line 112 (d) 更深半邊標 W52 shipped。
- **2026-06-05 W51 shipped → 決策 7 Option (d) ideal 半邊 done** —— config-test 加 **completeness proxy =「涵蓋章節數」(distinct-sections-cited)per-run band**(`RunMetrics.distinct_sections` + `ConfigRunSummary.distinct_sections: MetricBand`;`_run_n` 逐 run `len({tuple(c.section_path) ...})` 沿用 `_band` 零新 model)。Frontend(H7 design-first)result card grid 加「涵蓋章節數」metric 擺 faithfulness 旁 + W50 caveat 指向佢。**誠實 framing**:coverage proxy(廣度)**非 ground-truth recall**(無標註集;sub「completeness proxy · 非 recall」+ docstring)。synthetic-QA 真 recall 留更未來。Chris AskUserQuestion 揀 W51 = 對沖指標(C ingestion eval 留 W52)。backend +distinct_sections 斷言 17 passed / frontend +`涵蓋章節數` 斷言。commit `ff8657a`;phase folder `W51-config-test-completeness-proxy/`。
- **2026-06-05 W50 shipped → 決策 7 Option (d) 平 part done** —— config-test 試跑 panel 加 **length-bias explainer affordance**(忠實度 label `title` tooltip + A/B grid 下 `AlertTriangle` caveat note:「faithfulness 對長/全面答案有 length bias,低分配高引用/長答案多為 bias 非 config 差,對照引用數/字數判讀」)。**frontend-only static explainer**(無 backend / 無新 metric / 無 threshold / 無新 ADR);收 W49 known limitation(證據②)嘅教育半邊。**completeness/recall 對沖指標**(Option d「ideal」半邊)留 W51+。commit `ad2c93e`;phase folder `W50-faithfulness-length-bias-affordance/`。逐期重點 W49 bullet (d) 標 W50 shipped。
- **2026-06-05 W49 shipped → 決策 7 RESOLVED** —— config-test faithfulness 由「每 config 算一次」改為 **N-run `MetricBand`**(逐 run `asyncio.gather` judge;N≥2 顯示 mean±band / N=1 單值+warning;成本 = 用戶 `runs`;judge 維 gpt-5.4-mini;無新 ADR)。Chris AskUserQuestion 揀 **Option 1「沿用重跑次數做 band」**。§3 候選行 → ✅ W49;§5 決策 7 → ✅ RESOLVED;逐期重點 bullet 標 shipped(採 Option (a)+(c);(d) length-bias 對沖留未來)。backend +3 / frontend +1 test;commit `ace414b`。phase folder `W49-faithfulness-quality-band/`。
- **2026-06-06 live 驗證 → 新增候選「質素軸抗噪」** —— 獨立 session live-verify 配置面 + 試跑 loop(`drive_user_manuals`)期間實測:同一 SAVED config 兩次試跑 faithfulness 0.929↔0.53(presentation 軸同期穩定)→ W48 質素軸 single-shot 噪音明文化。新增:§3 table 候選行 + 逐期重點 bullet(帶 live 證據)+ §5 決策 7(抗噪策略,預設先加 warning gate)。同步記 memory `project_per_kb_tunable_config_vision`(註⑤)。**核心結論不變;此為 W48 已交付質素軸嘅 known limitation,非新風險。**
- **2026-06-03 addendum 連結** —— 新增 [addendum:LLM Document-Profiler](./ROADMAP-per-kb-tunable-config-addendum-llm-profiler.md)（§1 Layer A bullet + §7 Cross-ref 加 pointer）。完整捕捉 2026-06-03 brainstorm:multimodal LLM 文件畫像自動 seed config + bootstrap 評測;schema 三層 / 閉環 7 步 / 循環論證五槓桿 / probe 五閘 + config-aware + genre-constrain / Gate D 判別預檢 / config-tuning vs production 兩集 governance / KbConfig 對接 + granularity 結論（切塊可 per-doc / 檢索停 per-KB）。Tier 2 定位,未 ADR,不觸發實作。
- **2026-06-02** 建立(W43 closeout 後)。
- **2026-06-03 三-session code-grounded audit 校準(A–E)**:(A) 事實修正圖數 20–57(峰值 `ci=15=57`,原「33/20」低估);(B) 標明 doc-level reindex 現成驗證路徑,W44 不懸空;(C) Track A 兩層化(dev/demo 不卡 / production 原子切換才卡)+ 決策 4 重定義為 production 化投資時機;(D) 自助 loop 質素軸缺口明文 + 補分兩步 NEW item(reference-free faithfulness 先行)+ 決策 6;(E) W46 retrieval 旋鈕 per-doc 解析語意 + Layer C Tier 線重畫「章節語意 T1 / 視覺內容 T2」+ presets 提前。**核心結論(可行 / 診斷準 / 邊界誠實)不變。**
