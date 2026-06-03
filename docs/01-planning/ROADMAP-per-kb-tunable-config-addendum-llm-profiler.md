# Addendum — LLM Document-Profiler 自動 seed 機制（per-KB tunable config 願景延伸）

> **性質**:design-proposal addendum to [`ROADMAP-per-kb-tunable-config.md`](./ROADMAP-per-kb-tunable-config.md)。**唔係** accepted decision、**唔係** ADR、**唔係** pre-created phase plan。純為「把一次深度 brainstorm 完整留底,唔好散咗」。
> **建立**:2026-06-03（W44 F4.6 SME block 期間,brainstorm session 衍生）
> **Owner**:Chris（技術 Lead）
> **定位**:**Tier 2 / future direction**。觸及 multimodal vision（H4 邊界）+ 架構改動（H1）→ 任何實作前需 ADR + stakeholder。本文件**不觸發實作**。
> **錨點**:主 roadmap §1 Layer A（per-document profile）+ 決策 1（per-doc 夠未）+ 決策 6（質素軸）+ Layer C（vision Tier 線）;memory `project_per_kb_tunable_config_vision`;W44 F4.5/F4.6（content-based GT pivot,本願景嘅人手對照組）。
> **來源**:用戶 2026-06-03 idea —— 「LLM 咁強,除咗理解文字,仲可以『用眼』識別文件入面文字同圖（含 table/chart）嘅關係;預處理時是否可以畀 LLM 先讀整份文件,再產出最優嘅 chunking + retrieval 策略建議,自動把配置設好,更高效開始測試?」

---

## §0 核心原則（一句定調，全文圍住佢）

> **Model 可以「提案（propose）」同「定位（locate）」,但永遠唔可以做「真理嘅唯一裁判（sole arbiter of truth）」。** 真理由外部錨定（source 文件 / 異源 judge / 人手 held-out / 真 user query）;自動化只負責減 tedium,外部錨保住意義。

呢句係成個願景嘅成敗線。佢亦正正係 W44 F4.6 我哋手做緊嗰套（AI 草擬 keyword → 人複核 → eval 驗證）—— 本願景 = 把呢套由人手變自動,**同時保留所有外部錨**。**邊一層錨甩咗,個 gold 數字就退化成自我確認。**

---

## §1 idea 緣起 + 真正價值

**痛點（W44 親證）**:成個 W44 嘅根源就係「**冇人預先知道 DRIVE manual 係圖密程序型文件、要落 image cap、要開 parent-doc 檢索**」—— 要靠人診斷先發現。冷啟動（cold-start）一個新 KB / 新 doc,今日係「用全域默認硬試 → 撞板 → 人手調」。

multimodal LLM「用眼讀整份文件」剛好擊中三樣今日做唔到嘅嘢:
1. **文件畫像（profiling）**:讀完 → 判斷「圖密 step-by-step 手冊」/「表格密集 reference」/「純敘述」→ 對應唔同切塊 + 檢索配置。
2. **圖文關係識別**:用眼睇到「呢張截圖綁住緊上面嗰個 step」→ chunking 應保持佢哋同 chunk;「呢個係 table / chart」→ 應結構化解析。正係 W44 image pile-on / cap 想解、但只能用「位置」啟發式逼近嗰樣嘢。
3. **減少盲試**:新 KB 唔使由全域默認硬試,畀個 smart 起點。

**價值嘅誠實上限**（呢個係關鍵 reframe,詳見 §4）:LLM 產出嘅係**假設**,唔係**驗證過嘅最優**。佢**唔取代評測 loop**,只係畀**更聰明嘅起點**。慳到嘅係「盲試嘅頭幾轮」,唔係「驗證本身」。

---

## §2 Profiler 輸出 schema —— 三層

心法:**唔好當 profiler 係「config 神諭」,要當佢係「假設產生器 + 搜尋空間剪枝器」**。佢嘅職責唔係「畀最終最優」,而係「把無限搜尋空間收窄到幾個聰明候選 + 指出邊幾條軸值得掃」,最後由 eval 揀。

```yaml
document_profile:
  doc_id: ...
  profiler_model: <vision LLM>
  # ── 第 1 層:特徵訊號（證據 — 可審計）──
  signals:
    genre: procedural_manual         # 程序手冊 | 表格 reference | 敘述 | 混合
    image_role: screenshot_step_coupled  # 截圖綁步驟 | 圖表(data) | 裝飾
    image_density_per_section: high
    table_role: data                 # 數據(要結構化) | 純排版
    heading_depth: 3
    section_length_skew: high        # 有冇巨型 section（W44 圖洪根源）
    cross_reference_density: medium   # "見 X 節" 幾密
    query_orientation: lookup         # 查單步 | 跨節綜合 | 混合
    evidence:                         # ★ 點解 — LLM 引用實際位置
      - "§8.1.2 有 57 張內嵌截圖,每張跟住一個編號步驟"
  # ── 第 2 層:建議配置（可行動）──
  recommended_config:
    chunking: { strategy: layout_aware, max_images_per_chunk: 6, heading_split_depth: 2 }
    retrieval: { enable_parent_doc_retrieval: true, citation_expansion_max_aux: 8,
                 citation_expansion_section_path_prefix_depth: 1, rerank_top_k: 6 }
    rationale:                        # ★ 每個旋鈕點解咁揀
      max_images_per_chunk: "圖密步驟 section（>50圖）會 pile 成一個 chunk;cap 令 citation 聚焦"
    confidence:
      overall: 0.7
      low_confidence_knobs: [rerank_top_k]   # ★ 信心低 → 交畀 eval 掃
  # ── 第 3 層:eval 鈎（profiler 同時 bootstrap 評測）──
  proposed_eval:
    probe_queries: [...]              # 每個主要 section 自動生一條探測 query
    knobs_to_sweep:                   # 信心低嘅軸 → A/B/C 候選
      - { knob: rerank_top_k, values: [5, 6, 8] }
      - { knob: max_images_per_chunk, values: [6, 8, null] }
```

- **第 1 層（證據）+ 第 2 層嘅 `rationale`/`confidence` 係靈魂**:冇佢哋,config 係黑盒,人複核唔到、debug 唔到。有咗,就同 F4.6 proposal 一樣可審計（每條有 flag + 理由）。
- **第 3 層** 把 profiler 同 eval 扣埋:佢唔單止出 config,仲**順手 bootstrap GT + 探針 + 指明邊條軸要掃**。

---

## §3 自助閉環 —— 7 步

關鍵:**profiler 唔單止出 config,佢同時 bootstrap 埋 GT**（讀完 doc 順手生「探測 query + 預期答案內容」）。即係 **F4.5/F4.6 我哋手做嘅嘢（discover candidates → 草擬 GT）泛化成自動**。

```
1. PROFILE    multimodal LLM 讀 doc → document_profile（signals + 候選 config + confidence + probe queries）
2. 人 GATE    SME 複核（同 F4.6 一樣）:批/改建議 config、批 probe query + GT
3. SEED+INDEX 套用候選 config A/B/C → 切塊 + index（每個候選一個變體）
4. EVAL       跑評測;喺 profiler 標「信心低」嗰幾條軸做 A/B 掃（sweep）
5. COMPARE    用評測指標揀贏家（唔係 profiler 揀,係客觀數字揀）
6. PERSIST    贏嘅 config 持久化落 KbConfig;profile + eval 結果 + 決定 = 審計軌跡
7. REFINE     production 真 user query 入嚟 → 定期 re-eval → 微調
```

**eval 嘅職責 = 喺 profiler 收窄咗嘅幾個候選之間做判別**。若 profiler 只出一個 config 而 eval「pass」,你**永遠唔知另一個更唔更好** —— 評測嘅價值喺**比較**,所以 profiler 一定要出**候選集 + 掃描軸**,唔係單一答案。

---

## §4 循環論證（make-or-break 風險）+ 五槓桿

### 問題講到最 sharp

同一個 LLM（或同 model 家族）可能身兼四角:
1. **Reader/profiler** — 提 config
2. **GT 作者** — 寫 probe query + 預期答案
3. **被評嘅 synthesizer** — pipeline 生答案（EKP = `gpt-5.5`）
4. **Judge** — RAGAs 打分（EKP = `gpt-5.4-mini`）

若 1+2+4 同源 → 「judge 用自己寫嘅 GT,去評自己提嘅 config 跑出嚟、又係自己生嘅答案」→ 量度緊嘅唔係「現實啱唔啱」,而係「一個 model 自己世界觀嘅內部一致性」→ **可以好自信噉錯到底**。

**最毒**:profiler 全部意義就係慳人手,但令 GT「gold」嘅唯一嘢就係外部錨。一自動化埋 GT 又抽走人 → 把「畀數字意義」嗰樣自動化走咗 → 天真版全自動 **自我拆台**。

### 五（+1）槓桿（分層防禦,唔係單一 fix）

- **槓桿 1 — judge 同 author 異源（model diversity）**:寫 GT 嗰個 model 唔可以兼任 judge;理想 judge 換另一 vendor 家族。EKP 已有少少分離（synthesizer `gpt-5.5` vs judge `gpt-5.4-mini`,但同 vendor → 共享盲點）。**警告**:只減低、唔消除相關性（LLM 共享訓練分佈偏差）→ 單靠唔得。
- **槓桿 2 — GT 錨定喺 source,唔錨定喺 model paraphrase（抽取式 GT）【最強嗰層】**:probe 預期答案要係**抽取式**——指向 source 入面**真實存在嘅 span / 字詞**（即 F4.6 嘅 content-based keyword）。Model 角色由「發明真理」縮成「喺 source 定位真理」= **可驗證**（grep 得返條 keyword）。**循環喺呢度斷開。**
- **槓桿 3 — 人手抽樣 gate,按風險加權**:唔驗全部,驗「分層抽樣 + 全部低信心/flagged 嗰啲」（即 F4.6 🔴🟡）。抽樣同意度高 → 其餘可信多啲;低 → profiler 對呢份 doc 唔可信,降級/全人手。人 gate 由「全做」變「校準自動化嘅可信度」。
- **槓桿 4 — held-out 外部真理偵測器【最乾淨】**:保留一批 profiler **從未見過**嘅 GT（真 user query log / 人手 calibration set）。自動 GT 調出嘅 config,**同時要喺呢批 held-out 上 work**。「自動分高、held-out 分跌」= **循環警報**。最直接量到「個 loop 有冇喺度自我過擬合」。
- **槓桿 5 — 對抗式 / 範圍外（OOS）探針**:profiler 要**強制生文件答唔到嘅 query**,eval 檢查系統有冇正確拒答。自我確認 loop 傾向只生易答放水題 → 全 pass 但無意義。EKP 已有 `expected_refusal` OOS（Q031-Q035）→ 泛化。
- **（附）槓桿 6 — 指標選擇:偏向檢索錨定,而非答案相似度**:RAGAs `context_precision` / `context_recall` + content-based recall（正確 source 文字有冇 retrieve 到）比 `answer_relevancy`（會獎勵流暢自我一致）**難 game**。選 config 贏家時重心擺檢索錨定 + 內容導向 recall。

---

## §5 Probe query 自動生質素

### Reframe:probe = 測量儀器

喺 config 選擇語境,probe query **唔係 UX 產物,係一支測量儀器**,目的 = 判別 config A/B/C。所以「質素」=**判別力（discriminative power）**,唔係「真唔真實」。一條「真實但人人 config 都答到」嘅 query 判別力 = 0;「冇人答到」嘅都 = 0。

### 主導 failure mode（W44 F4.6 親證）:可答性 / 覆蓋錯配

F4.6 嗰 9 條 🔴（troubleshooting / 跨模組）全部係 W4「user-collected」自動生 query,**全部跌穿門檻** —— 唔係 retrieval 差,係**語料根本答唔到**（procedural manual 冇 diagnostic 內容）。**靜靜混入答唔到嘅 query 會毒化 config 選擇訊號**（每個 config 對佢都失敗,判別唔到嘢,純加 noise,仲令人誤以為 retrieval regression —— 正是 F4 eval-harness decay 一半成因）。

→ 自動生器頭號職責 = **只出語料答得到嘅 query**,或**明確標 unanswerable 做 OOS 探針**。

### 五道閘 + 兩個 insight

```
Gate A 抽取錨定:生成器要 cite source span,指唔到 → drop（hallucinate）
Gate B 可答性來回（round-trip）:retrieve+answer 被 cited span 支撐?否 → 隔離（hard/OOS）
Gate C genre 一致:query_type ∈ profiler genre 支撐嘅類型?否 → reject
Gate D 判別預檢:對 2 個刻意唔同嘅 config 跑,score 一樣 → 非判別性,留覆蓋但唔加權（詳見 §6）
Gate E 人手 spot-check:分層抽樣 + 全部隔離項（F4.6 風險加權 gate）
Gate F 去重 / 去 trivial:答案字面喺 query 入面 → drop
```

- **insight 1 — generation 要 config-aware**:偏向「被掃嗰幾條旋鈕咬得到」嘅 query。測 `chunker_max_images_per_chunk` → 生答案橫跨圖密多步驟 section 嘅 query;測 `parent_doc` / `citation_expansion` → 生「列出所有 X」枚舉型 query（memory Q-W25-I07「show me all integration scenarios」係經典）;測 chunk 大小 → 生答案橫跨 section 邊界嘅 query。⚠️ 循環風險（生 probe 去「證」偏好 config）靠 Gate A + 抽取式 GT 守住。
- **insight 2 — genre 要 constrain 探針類型**:profiler 嘅 `genre` 訊號**直接管住可出嘅 `query_type`**。procedural manual → 只 `{single_step_lookup, multi_step_synthesis}`,**禁 `troubleshooting`**（語料根本冇嗰種內容）。W4 eval-set 嘅錯本質就係對 procedural 語料生 troubleshooting query —— 呢個 constraint 一加,F4.6 嗰 9 條 🔴 由源頭就唔生出嚟。

### 探針 schema（帶來源、可審計;相容現有 eval-set）

```yaml
probe:
  query_id: auto-AR01-001
  query_text: "How do I record a payment collection from a customer?"
  query_type: single_step_lookup          # 受 profiler genre constrain
  source_anchor: {doc_id, section_path: ["2 AR01. Payment Collection", ...], char_span}
  expected_answer_keywords: ["Payment Collection", "customer payment journal", "AR01"]  # 由 anchor 抽取（Gate A）
  answerability: verified                  # Gate B
  discrimination: {tested_configs: [capNone, cap8], score_spread: 0.18}  # Gate D（optional）
  generated_by: <model>
  validated: false                          # Gate E 人手 gate
```

= `eval-set-v1-draft.yaml` 結構 + `source_anchor`（錨定）+ `answerability` + `discrimination` → **完全相容現有 eval-set,唔使另起爐灶**。

---

## §6 Gate D 判別預檢 —— 點實作

### 本質:sensitivity test,唔係 selection

Gate D 問「**呢條 query 對緊我要掃嗰個旋鈕,敏唔敏感**」,唔係「邊個 config 好」:

```
spread(Q, knob) = | score(Q, knob=max) − score(Q, knob=min) |
spread ≈ 0  → Q 對呢個旋鈕「盲」→ 喺呢個旋鈕嘅 sweep 入面冇用（drop / 只留覆蓋）
spread 大   → Q 對呢個旋鈕敏感 → 高判別價值
```

係 **per-knob** 嘅 → 結果係「query × knob」一張敏感度矩陣,唔係單一 pass/fail。

### 實作 1:用平嘅 metric,唔好用貴嘅 judge

絕大多數旋鈕（`parent_doc` / `citation_expansion` / chunk 邊界 / `rerank_top_k`）**改嘅係「retrieve 到咩」**。所以 Gate D 用**最平 proxy = retrieve-only content-based recall**（即 `EvalRunner` 嗰半,唔行 synthesizer / RAGAs judge）。貴嘅 RAGAs judge 留返最終 selection。對應 EKP 兩層 eval:
- `EvalRunner`（recall,平,retrieve-only）← **Gate D 用呢個**
- `run_eval_pipeline`（RAGAs synth+judge,貴）← 最終 selection

### 實作 2:成本喺「旋鈕類型」分叉（同 F4.5 教訓再撞）

| 旋鈕類型 | Gate D 成本 | 點解 |
|---|---|---|
| **查詢時**（`parent_doc` / `citation_expansion` / `rerank_top_k`）| **平** | 同一 index,靠 `EffectiveConfig` per-query override 切 min/max,re-run retrieve |
| **Ingestion**（`chunker_max_images_per_chunk` / `chunk_strategy`）| **貴** | min/max = 兩個唔同 re-chunk 嘅 index,要 re-ingest;且 **GT 必須 content-based**（chunk_id 跨 index 唔同 — F4.5 發現再現） |

→ 策略:查詢時旋鈕 **per-probe** 做 Gate D;ingestion 旋鈕**唔好 per-probe re-index**（爆成本）,改「**per-candidate 先 re-index 一次**（cap=None / cap=8 兩個 index）→ 所有 probe 喺兩 index 跑 recall」,spread 喺 per-probe recall 對比浮現 → Gate D 同最終 selection **共用嗰兩次 re-index,唔額外付**。

### 局限（誠實標）

Gate D **只測敏感度,唔測方向啱唔啱** —— query 可以敏感但 metric 升錯方向。方向正確性靠 **metric 本身可信**（content-based recall 對 validated GT）+ §4 循環五槓桿。Gate D = **必要非充分**。

### EKP hooks（全部現成）

- min/max 切換:`EffectiveConfig` per-query override
- recall:`EvalRunner`（retrieve-only,平）
- ingestion 旋鈕 re-index:doc-level reindex（`documents.py`,W44 F3 用過）
- → **Gate D 可完全砌喺現有 primitive 上,唔使新基建。**

---

## §7 config-tuning 集 vs production 集 —— governance

### 兩集本質

- **config-tuning 集**:自動生、語料保真、答得到、用嚟**揀 config**。可重生（綁 corpus 版本）。
- **production 集**:真 user query log + 人手 GT、用嚓**驗實戰 + 做循環論證 held-out 偵測器**（= §4 槓桿 4）。不可重生,只 curate。

### 六個 governance 維度

1. **出處 + 可變性**:tuning 集 = 機器生、可重生（corpus 變就重生,衍生物）;production 集 = 人/log 來源、**append-only 不可變**,只增補 curate。規則:tuning 集 GT 唔可由判分 model 衍生;production 集 GT **必須人手**（佢係錨）。
2. **洩漏防火牆【最重要】**:production 集**必須 held-out 喺 tuning loop 之外**。拎 production 分數做 optimize 目標 = 污染獨立驗證器 → 唔再 independent。
   ```
   tuning 集    → 入 optimize loop（sweep / select）
   production 集 → 只喺 selection 之後做 GATE（「揀咗嘅 config 喺真 query 上 pass 嗎?」），唔入 optimize objective
   ```
   即把 train/test split 紀律搬落 RAG config tuning;production 集對 optimizer **read-only**,最後先投一票 pass/fail。
3. **刷新節奏 + 漂移**:tuning 集綁 corpus 版本（corpus 變就重生）;production 集由 log 持續長大,定期人手 curate,盯**分佈漂移**。規則:每個 query 集打 **timestamp + corpus-version tag**;eval 結果只對 `{config 版本 × corpus 版本 × query-set 版本}` 三元組有效。
4. **大小 + 抽樣**:tuning 集可大（自動、平,全 section 覆蓋）;production 集細（人手 GT 貴）但要係真 query 分佈嘅**分層抽樣**。質 > 量。
5. **晉升路徑 + 永久 held-out 保留區**:production query 若驗到「答得到 + 有判別力」可**晉升**入 tuning 集（補抽取式 GT）;但一旦晉升就唔再 held-out → **永久保留一批絕不晉升**做防火牆。規則:明確 promotion log + never-promote 保留區。
6. **分歧訊號（payoff）**:

   | tuning | production | 解讀 | 行動 |
   |---|---|---|---|
   | ↑ | ↑ | 真改善 | ship |
   | ↑ | ↓ | **過擬合自動 query / 循環** | **唔好 ship** |
   | ↓ | ↑ | 自動集 mis-spec（probe 太難 / 錯 genre）| 修 generator |

   規則:每個 config 決定**同時 log 兩個分數 + 一致性判決**;分歧超門檻 → block 晉升 + 觸發調查。

### EKP grounding（唔係空談）

- registry 喺 `eval.py` 嘅 `eval_set_id → path` mapping。現有:`eval-set-v0`（MFP,棄用）/ `eval-set-v1-draft`（55q）/ `eval-set-v0-w25-supplement` / `eval-set-w42diag-testkb`。
- **關鍵 insight**:`eval-set-v1-draft` 而家係 **synthetic（Q001-Q030）+「user-collected」（Q036-Q055）撈埋一個 file** —— 正正係兩種集混咗。Q001-Q030 = config-tuning 性質;Q036-Q055（W4 模擬真實語氣）= production-representativeness 雛形。**F4 之所以混亂,一半就係呢個 conflation**（synthetic 答得到 + user-collected 答唔到,撈埋算 recall）。
- **第一步根本唔使等 profiler**:喺 `eval.py` registry **標 set type（tuning / production）** + **拆開** `eval-set-v1-draft` → 一個 tuning 集 + 一個 production held-out 集。
- production 集 = **Q14 SME 人手 GT 嘅真正歸宿** + §4 槓桿 4 嘅實現。

---

## §8 KbConfig / settings.py 對接 + granularity

### 好消息:三層解析鏈已存在

EKP 已有 `EffectiveConfig`（`generation/effective_config.py`）做**查詢時三層解析**:`per-query override > per-KB (KbConfig) > global (Settings)`;`KbConfig` 嘅 W43/ADR-0040 runtime 旋鈕全部 `| None` = 「None 繼承全域」。→ profiler 唔使搞 granularity 機制,只需產出值塞落呢條鏈。

### 三類旋鈕（按「幾時生效 × 住喺邊」）

**第 1 類 — Ingestion-baked（改咗要 re-index）:**
| 旋鈕 | 現狀 |
|---|---|
| `chunk_strategy` / `extract_embedded_images` / `slide_screenshots` / `dedup_strategy` | ✅ 已喺 `KbConfig`（per-KB） |
| `chunker_max_images_per_chunk`（W44 加） | ⚠️ **只喺 `Settings`（全域）**,`server.py` startup 注入單一 chunker — **缺口** |
| heading 細分深度 / merge 門檻 | ❌ chunker 內部,**無 knob** |

**第 2 類 — 查詢時 runtime（唔使 re-index,行 `EffectiveConfig`）:**
| 旋鈕 | 現狀 |
|---|---|
| `enable_parent_doc_retrieval` / `parent_doc_*` / `citation_expansion_*` / `citation_neighbour_*` / `max_images_per_answer` / `default_rerank_k` | ✅ 已喺 `KbConfig`,per-KB **+ per-query override** |
| `retrieval_image_low_value_weight` / `reranker_cross_section_deboost` / `query_expansion_*` | ⚠️ **只喺 `Settings`（全域）** — 要 per-KB 就要 promote |

**第 3 類 — 真全域（profiler 唔應掂）:** `reranker_kind` / endpoints / auth / rate limit / vendor 選擇。

### Profiler 輸出 → EKP 對接（mapping）

| `recommended_config` | EKP 目標 | 今日粒度 | 缺口 |
|---|---|---|---|
| `retrieval.enable_parent_doc` | `KbConfig.enable_parent_doc_retrieval` | per-KB + per-query | ✅ 通 |
| `retrieval.parent_doc_*` | `KbConfig.parent_doc_*` | per-KB | ✅ 通 |
| `retrieval.citation_expansion_*` | `KbConfig.citation_expansion_*` | per-KB | ✅ 通 |
| `retrieval.rerank_top_k` | `KbConfig.default_rerank_k` | per-KB | ✅ 通 |
| `chunking.strategy` / `extract_images` | `KbConfig.chunk_strategy` / `extract_embedded_images` | per-KB | ✅ 通 |
| `chunking.max_images_per_chunk` | `Settings.chunker_max_images_per_chunk` | **全域 only** | ⚠️ promote 落 KbConfig + orchestrator 按 doc 讀 |
| `chunking.heading_split_depth` | （無 knob） | — | ❌ 新增 chunker 旋鈕 |

**punchline**:profiler **檢索半邊今日幾乎全通**（PATCH `/kb/{kb_id}/settings` 就 apply,零 glue）;**切塊半邊只通一半**（W44 image cap 全域缺口、heading 細分無 knob,且切塊改 = re-index）。

### 設計原則

> **`document_profile.recommended_config` 嘅 field 名應該直接 mirror `KbConfig`** → 「apply」= 一個 `PATCH /kb/{kb_id}/settings`,**零翻譯層**。

配合 `None`-inherit:profiler 只 emit 有意見嗰幾個 field,其餘繼承全域。`signals` / `confidence` / `rationale` **唔放入 `KbConfig`**,住喺另一 profile store 做審計軌跡 → 唔污染 config。

### per-document vs per-KB granularity（結論）

- **per-KB = 原生 end-to-end**:index（`ekp-kb-{kb_id}-v1`）/ `KbConfig` / re-index 全部 per-KB。profiler 出 per-KB config 今日 work。
- **per-document 查詢時旋鈕:唔 compose** —— 一條 query 跨同一 KB 多份 doc,用邊份嘅 `parent_doc` / `citation` 設定?無解 → **查詢時 config 留 per-KB（或 per-query）**。
- **per-document 真正意義 = per-document *ingestion*（切塊）config**:doc A 用 cap 6、doc B 用 cap 10,切完落同一 per-KB index。Feasible 但要:(1) 一個 **per-doc profile store**（keyed by `doc_id`）存切塊 config;(2) ingestion orchestrator **按每 doc profile 配 chunker**（而非 startup 單一全域 chunker）。
- **粒度結論:切塊 = 可去到 per-document;檢索 = 停喺 per-KB。** 對應 memory 願景 Layer A。

### 串返 W44

W44 加嘅 `chunker_max_images_per_chunk` 係**全域**;主 roadmap §6 carry-over 🚧「per-KB 圖數 cap（降 `chunker_max_images_per_chunk` 落 `KbConfig`）」**正正係上面缺口表第一個 promotion**。順序自然:

```
W44 全域 cap（done）→ promote 落 KbConfig（per-KB cap,roadmap carry-over）
   → orchestrator 按 doc 配 chunker（per-document cap）→ profiler 自動產出呢個值
```

→ **務實切入唔係由 profiler 開始,而係由「逐個旋鈕 promote 落 KbConfig + 確保 EffectiveConfig 解析到」開始** —— 基建鋪好,profiler 先有「靶」可射。射靶嗰枝箭（multimodal LLM）反而係最後、最 Tier 2 嗰塊。

---

## §9 三個深層張力（總綱,跨全文）

1. **循環論證 / 自己改自己**（§4）—— 頭號風險;靠五槓桿打破,核心係「propose/locate 可以,sole arbiter 唔得」。
2. **內容導向 GT 係硬前提**(§5/§6/§8)—— 多個切塊候選 re-chunk → chunk_id 全變(F4.5 發現),跨候選比較**必須 content-based GT**(keyword/reference),唔可以 chunk_id。**F4.5 R3 deviation 係呢個願景嘅地基。**
3. **唔好畀 profiler 自動 flip Tier 2 架構**(§2)—— 佢調**已存在旋鈕**得;「要唔要 GraphRAG / 多跳 / agentic」係 H1+H4 Tier 2 架構決定,profiler 最多 flag「呢份 doc 似乎需要跨節綜合,建議人考慮 Tier 2」。

---

## §10 最薄第一刀（thin slice）+ 落地順序

唔好一開始全自動。最小可證價值版本:

> profiler 只做**文件分類（genre + image_role）+ 對住現有旋鈕提 2-3 個候選 config**,**唔生 GT**（用現有 eval-set）,餵落**現有 eval** 揀贏家。

冇新旋鈕、冇 GT 自動生、冇 vision 深水區 —— 純「分類 → 候選 → 現有評測判別」。證到「profiler 候選 比 全域默認 好」之後,先逐步加 vision 圖文識別、GT 自動草擬、per-document 配置。最唔觸 H1/H4。

**建議落地順序（每步都有獨立價值,可隨時停）:**
```
0. （基建）逐個 Settings 旋鈕 promote 落 KbConfig + EffectiveConfig 解析（roadmap W44 carry-over 起步）
1. config-tuning 集 vs production 集 拆開 + registry 標 type（§7,唔使等 profiler）
2. Gate D 敏感度矩陣（§6,砌喺 EvalRunner + EffectiveConfig）
3. thin-slice profiler:genre 分類 + 候選 config（無 GT 生成）
4. probe 自動生 + 五閘（§5）+ GT bootstrap（§3 step 1）
5. multimodal vision 圖文關係識別（⚠️ Tier 2 閘,H4,需 ADR + stakeholder）
6. per-document 切塊 config（profile store + orchestrator per-doc chunker）
```

---

## §11 與現有 roadmap 嘅扣接

- **Layer A（per-document profile）** ← 本 addendum = Layer A 嘅**自動 seed 機制**深化。
- **決策 1（per-KB 夠未）** ← §8 granularity 結論「切塊可 per-doc / 檢索停 per-KB」直接餵呢個決策。
- **決策 6（質素軸 next）** ← §3 閉環 step 4-5 + §7 兩集 governance = ADR-0040 雙軸前提嘅自動化形態;reference-free faithfulness（roadmap NEW item）係呢度嘅最小一步。
- **Layer C（image relevance Tier 線）** ← §10 step 5 vision 圖文識別 = Layer C「視覺內容語意 = Tier 2」嗰邊;profiler `image_role` 訊號餵「章節語意 = Tier 1」嗰邊。
- **W44 carry-over（per-KB 圖數 cap）** ← §8「串返 W44」= 本願景第一塊地基,已喺 W44 plan §6 排隊。

---

## §12 與 W44 F4.5/F4.6 嘅 dogfooding 關係（重要）

我哋 W44 手做緊嘅嘢,本身就係呢個自動化願景嘅**人手對照組**:

| 自動化願景組件 | W44 手做對照 |
|---|---|
| §4 槓桿 2 抽取式錨定 | F4.6 content-based keyword GT（由 source chunk 抽取） |
| §4 槓桿 3 風險加權人 gate | F4.6 🔴🟡 flag + Chris 複核 |
| §4 槓桿 4 held-out 偵測器 | （未做）→ production 集 = Q14 SME GT 歸宿 |
| §4 槓桿 5 OOS 探針 | `expected_refusal`（Q031-Q035） |
| §4 槓桿 1 judge 異源 | synthesizer `gpt-5.5` ≠ judge `gpt-5.4-mini`（雛形） |
| §5 覆蓋驅動生成 | F4.5 `discover_chunk_ids.py`（每 query top-k） |
| §5 Gate A 抽取 | F4.6 keyword 由 chunk preview 抽 |
| §6 content-based GT 跨 re-chunk | F4.5 R3 deviation（chunk_id chunker-specific）|

→ **F4.5/F4.6 唔係紙上談兵 —— 係呢個願景每一層錨定嘅 working proof-of-concept。** 將來自動化 = 把呢套由人手變「自動提案 + 保留四層錨定」。

---

## §13 未決問題（open questions,留將來 ADR 決）

- **OQ-P1**:vision LLM 讀整份大文件（幾百頁 / 幾百圖）嘅**成本 + 可重現性**（同一 doc 兩次跑出唔同 config）—— 一個會持久化嘅配置,可重現性點保證?
- **OQ-P2**:profiler `confidence` 點 calibrate（自報信心同實際準確度嘅相關性）?
- **OQ-P3**:per-document 切塊 config 嘅 profile store 點落（新 table? 擴 `KbConfig` 加 per-doc override 子結構?）+ orchestrator 按 doc 配 chunker 嘅改動面（今日 `server.py` startup 單一 chunker instance）。
- **OQ-P4**:`image_association` metric（圖密 doc 判別關鍵,今日 0 / deferred）幾時 wire live —— 冇佢,圖文配置揀唔到贏家。
- **OQ-P5**:Gate D 「方向正確性」點獨立驗證（敏感度 ≠ 方向啱）?
- **OQ-P6**:production 集 held-out 嘅最小可信規模（人手 GT 貴,幾多條先夠做循環偵測器）?

---

## §14 Cross-ref

- 主 roadmap [`ROADMAP-per-kb-tunable-config.md`](./ROADMAP-per-kb-tunable-config.md)（Layer A / 決策 1,6 / Layer C / W44 carry-over）
- ADR-0040 — per-KB config-scope（Accepted;W43 STRONG PASS）
- ADR-0041 — W44 chunker image-density deep fix（`chunker_max_images_per_chunk` 來源）
- memory `project_per_kb_tunable_config_vision`（foundational vision）
- W44 phase folder `docs/01-planning/W44-chunker-image-density-deep-fix/`（F4.5/F4.6 dogfooding 對照）
- Code anchors:`backend/generation/effective_config.py`（resolver）/ `backend/api/schemas/kb.py:9-73`（`KbConfig` 13 旋鈕）/ `backend/storage/settings.py`（全域旋鈕）/ `backend/eval/runner.py`（`EvalRunner` 平 recall）/ `backend/eval/orchestrator.py`（RAGAs 貴）/ `backend/api/routes/eval.py`（eval-set registry）/ `backend/api/routes/documents.py`（doc-level reindex）

---

**狀態**:design-proposal addendum（living）。**未實作、未 ADR、Tier 2 定位**。任何實作前需 ADR + stakeholder（尤其 §10 step 5 vision = H4 閘）。

**修訂史**:
- **2026-06-03 建立** —— 完整捕捉 2026-06-03 brainstorm session（W44 F4.6 SME block 期間衍生）:§0 核心原則 / §2 schema 三層 / §3 閉環 7 步 / §4 循環論證五槓桿 / §5 probe 五閘 + config-aware + genre-constrain / §6 Gate D 實作 / §7 兩集 governance / §8 KbConfig 對接 + granularity / §9-§13 張力 + thin-slice + roadmap 扣接 + dogfooding + open questions。
