# 可調配置平台(W43–W58)— 工作流盤點與跟進

> **性質**:跨 phase 工作流總結(status rollup),非 phase plan、非 ADR。
> **作用**:把「由 W43 觸發、橫跨 W43–W58 共 16 個 phase」的可調配置平台工作流,整合成單一視圖,
> 方便記錄全貌 + 跟進剩餘項。
> **與既有文件關係**:
> - 總藍圖(設計層)= [`docs/02-architecture/per-document-config-platform-design.md`](../02-architecture/per-document-config-platform-design.md)
> - 結構性 deferred-debt 登記冊 = [`DEFERRED_REGISTER.md`](./DEFERRED_REGISTER.md)
> - 產品 vision(原話)= memory `project_per_kb_tunable_config_vision`
> - 本文件 = 上述三者的**跨 phase 進度盤點層**(不重複設計細節,只記「做咗乜 / 剩低乜 / 點跟進」)
>
> **建立**:2026-06-10(整合兩個獨立 session 的盤點分析 + code 核實)
> **更新**:2026-06-10 — 新增 §4「圖片 recall 可行性深入分析」(回應用戶「真的可行嗎?真的有可能實現嗎?」
> 提問;基於 `backend/ingestion/orchestrator.py` + `backend/api/routes/query.py` code 核實),
> 原 §4–§6 順延為 §5–§7,§5 優先順序加入「圖片召回指標」候選項。

---

## 0. 緣起(點解會有這條工作流)

W43 之前做實際效果測試時發現:**不論文字內容的返回準確度 / 完整度,還是文字 + 圖片的處理,效果都不夠理想**。
根因是**不同文件內容格式需要不同配置**才有合適效果。當時的做法是**一直在後台改 code 或改配置**——
但這套做法**不適用於真實 end user 場景**。

由此確立 foundational vision(用戶 2026-06-01 原話節錄):

> 「希望本系統不論功能架構和 UI 頁面操作的部分,都可以提供讓用戶自行設置和調整,令不同 KB 的文件
> 都可以運用不同的度身訂做配置……當用戶能通過平台上去找出最理想的配置和測試了效果之後,這配置就會
> 應用在該 KB 的那份文件中。」

用戶視此為「RAG 必經的流程」。產品核心價值 = **對不同 input query,回答的文件內容準確度 + 完整度
(加上本項目一併提供的圖片返回處理)**。

藍圖把 vision 收斂為 **3 個正交層 + 一個配置生命週期 loop**:

| 層 | 目標 | 對應原始痛點 |
|---|---|---|
| **Gap A** | 配置粒度由 per-KB 落到 **per-document** | 「不同文件要不同配置」的核心 |
| **Gap B** | query 意圖 gate(列舉型 vs 具體型) | 同一文件、不同問法要不同完整度傾向 |
| **Gap C** | per-image 位置 + 相關性揀圖 | 圖片順序錯亂 + 圖片返回不齊 |
| **Loop** | 設定 → 平台試跑 → 驗證 → 持久化 | 把「後台改 config」搬上 UI 給 end user |

---

## 1. 結論先講

由 W43 觸發的整條工作流(W43–W58 共 16 個 phase)**已全部 close**。
用戶 vision 的核心 ——「配置在前端 UI 操作、設定、試跑驗證,且分 per-KB 與 per-document 兩個粒度」——
**已端到端落地**(藍圖 §0 於 2026-06-09 確認)。

對照藍圖的 3 個 gap,**真正未進行的主線只剩 1 個:Gap B(query 意圖 gate)**,
而且它的必要性在證偽實驗中未獲證實,屬最低優先、甚至可能 drop。
另有 3 個收尾細項掛在 `DEFERRED_REGISTER.md`,以及一批 W43 當初**主動 scope-out**(非欠債)的操作性增強。

**但 2026-06-10 深入分析(§4)發現一個藍圖 3-gap 以外的新缺口:圖片側完全沒有召回指標。**
文字側可系統性收斂(R@5 / faithfulness / `distinct_sections`),圖片側的「成功」至今全靠用戶肉眼
在 UI 驗證 ——「文字 + 相關圖片一併齊腳」這個產品核心目標**無法量度,因此無法系統性改善**。
這是收尾規劃中價值最高的新候選項(詳見 §4.5,優先順序見 §5)。

---

## 2. 已完成的部分(對照原始痛點)

| 原始痛點 | 落地 phase | 交付 |
|---|---|---|
| 不同文件格式要不同配置,不可後台改 code | **W43**(ADR-0040) | per-KB 配置模型 + `EffectiveConfig` 解析鏈(per-query > per-KB > 全域)+ 全 pipeline 試跑 harness(`POST /kb/{kb_id}/config-test`)+ KB Settings UI 配置面 + 儲存 loop |
| 圖洪水(圖密文件一個 chunk 帶 ~27 圖) | **W44–W47**(ADR-0041/0042) | chunker 圖數上限深層修 + per-KB ingestion 配置 + 重索引流程 + live 驗證 |
| 試跑信號可否信賴(單次試跑 variance ~20%) | **W48–W56** | faithfulness 質素軸 + length-bias 警告 + 完整性 proxy(`distinct_sections`)+ synthetic QA recall harness + chunk 策略受控 A/B + 大語料驗證 |
| 圖片返回不齊 + 順序錯亂 | **Gap C** = CH-011 / CH-012(ADR-0048/0049) | `doc_order` 全鏈 propagate → 圖片按真文件位置排序 + section-fair 揀圖(尾段 section 由 0 圖 → 5/6 圖,用戶 live 驗證 PASS) |
| 按文件(不只按 KB)設定 | **Gap A** = W57 + W58(ADR-0050/0051) | per-doc 配置後端(`document_configs` 表 + per-DOC 解析層 + dominant-doc 規則)+ doc-detail 頁「Per-doc 配置」tab UI(先擴 mockup → 用戶 review → 才砌 frontend,守 H7) |

**配置生命週期 loop 現況**:`設定 → 試跑預覽(N-run band + A/B + faithfulness)→ 驗證 → 持久化`
**per-KB 與 per-document 兩個粒度都有 UI**。vision「每文件 UI 操作配置管理」端到端打通。

git 對照:`79bc216`(W58 closeout,Gap A complete)、`e1713b2`(W57 backend),均已 merged。

---

## 3. 未進行 / 未收尾的部分

### 3.1 主線層 — 只剩 Gap B / P3(且建議可能不做)

**query 意圖 gate**:輕量啟發式分「列舉型(list every step…)vs 具體型」query,影響 completeness 傾向。

- **必要性未證實**:2026-06-01 證偽實驗(藍圖 §1.2 ②)在 AR 圖密手冊上**找不到**「保守 config 失敗、
  但激進 config 成功」的 query —— 列舉型 query 被 overview chunk 滿足了。即 query-adaptivity 必要性是
  **doc-dependent**,Gap A 做完後可能已足夠覆蓋。
- **建議**(藍圖 §3.2,per Karpathy §1.2 不做投機 feature):**擺到最後**,等 Gap A/C 實跑一段時間後
  實測再決定要不要做,甚至直接 drop。
- **H4 紅線**:若做,必須**輕量啟發式**,不可做 LLM-router / multi-agent orchestration(Tier 2 L4)。
- **判據來源**:§4.5 提議的圖片召回指標一旦建立,「列舉型 query 的圖片齊腳率是否系統性偏低」
  會有實數,Gap B 做不做可由數據拍板,不必再靠主觀體感。

### 3.2 三個 deferred 收尾細項(`DEFERRED_REGISTER.md`)

| ID | 項目 | 現況 | Close 條件 |
|---|---|---|---|
| **DD-3** | per-doc 配置 UI 的 **live 全 stack 視覺驗證** | W58 = fidelity-by-construction(逐元素對齊 approved mockup + tsc/eslint/prettier/vitest 綠 + KB test 零回歸),**但未實際起 frontend 在 browser 行過 upsert + 試跑** | 下次 session frontend 起得 + Azure key 在 + 機器 load 容許 |
| **DD-4** | chat RAG 質素 fix 的 **production default flip**(`ENABLE_PARENT_DOC_RETRIEVAL=true` + `CITATION_EXPANSION_MAX_AUX=10` + `CITATION_EXPANSION_SECTION_PATH_PREFIX_DEPTH=1`) | **eval 已 PASS 背書**(單檔 13-query + 跨檔 30-query,recall 1.0 / 0 regression / +413ms p95);default 未 flip,現靠 `.env` 輕量持久化 | 用戶決定是否升為 production default(純決策) |
| **DD-5** | `answer_detail` 旋鈕**不在試跑預覽內**(經「儲存」後 real query 才生效) | 細 follow-up:`DraftRetrievalConfig` + `ConfigTestRequest` 加 `answer_detail` field(後端 `PerQueryOverrides` 已有此 field) | 細 follow-up 排期 |

### 3.3 W43 當初主動 scope-out 的操作性增強(**非欠債,從未排期**)

> **性質澄清**:以下是 W43 plan §Non-goals **明文 defer** 的 nice-to-have,沒人答應過要做。
> **不算 W43 工作流的未完成尾巴** —— 要做需重新 kickoff。
> 證據:`docs/01-planning/W43-per-kb-tunable-retrieval-config/plan.md` L46–47。

- **config version history**(配置版本歷史)
- **配置 profile 自動建議**
- **批量 sweep**(一次掃多組配置)
- **per-query 旋鈕完整 expose** —— 現況:`PerQueryOverrides`(`backend/generation/effective_config.py:34`)
  整個 dataclass 是 **seam-only,W43 MVP 完全沒 wire**(docstring L38:`Unused by the W43 MVP wiring (seam only)`)。
  它列了 16 個 field(`default_top_k` / `enable_parent_doc_retrieval` / `citation_expansion_*` /
  `max_images_per_answer` / `answer_detail` 等)全部留空。
  > **修正一個常見誤述**:不是「只 wire 了 `top_k_*`、其餘留 seam」。整個 class 都未 wire;
  > W43「reuse 既有 `top_k_*`」指的是 `QueryRequest` 本身舊有的 top_k 參數,不是這個新 class。

---

## 4. 圖片 recall 可行性深入分析(2026-06-10 補充)

> **觸發**:用戶提問 ——「文字內容的 recall 質素(完整度 + 準確度)已大致符合預期,但加入圖片部分的
> recall 後,一直不能達到一次完全成功(成功定義 = recall 了文字內容,而這些文字內容**相關**的圖片
> 也能夠一併 recall)。這個目標真的可行嗎?真的有可能實現嗎?」
> 以下分析基於對 `backend/ingestion/orchestrator.py` + `backend/api/routes/query.py` 的 code 核實,
> 非單憑文件印象。

### 4.1 結論

**可行,但有一個前提:要重新定義「成功」。**「一次完全成功」(任何 query、任何文件、一次過文字 +
相關圖片齊腳)在**任何** RAG 系統 —— 包括商用方案 —— 都是**概率事件,不是可保證的性質**。
可實現的目標應是:

> **在特定文件類型上,把「文字 + 圖片齊腳」的成功率推到可量度的高水平(例如 ≥90%),
> 並提供工具令用戶可針對失敗案例自行調整。**

per-KB / per-doc 配置方向是對的,但它只是三塊拼圖之一(**配置 / 指標 / 語義綁定** — 見 §4.4–§4.6)。
對 Drive manuals 這類「圖片緊跟步驟文字」的結構化手冊,現架構 + per-doc 配置可以達到很高的實際
成功率(Gap C live 驗證已示範:尾段 section 由 0 圖 → 5/6 圖)。

### 4.2 結構性事實:圖片相關性 = 位置繼承,不是語義判斷

整條 pipeline 由頭到尾,**沒有任何一步在語義上判斷「這張圖跟這條 query 相關」**。
圖片的「相關性」是靠位置繼承回來的:

1. **Ingestion**(`backend/ingestion/orchestrator.py` L188–249):圖片按 `img@<doc_order>` 物理位置
   綁定到所在 chunk(`embedded_image_positions` → `ImageRef`,stamp `source_section` + `doc_order`)
   —— 即「這張圖在這段文字附近」,**不是**「這張圖在解釋這段文字」。
2. **檢索**:hybrid search + rerank 完全只看文字,圖片零參與。
3. **回答**(`backend/api/routes/query.py`):被 cite 的 chunk 自帶圖 + 鄰居 chunk 補圖(ADR-0034)
   + 章節 overview pin(ADR-0047)+ section-fair 揀圖(ADR-0049)+ 圖數 cap(per-KB / per-doc)
   + frontend checksum dedup。

### 4.3 「一次完全成功」的數學根源

圖片齊腳是幾個近乎獨立的概率相乘:

> P(圖片齊腳)= P(文字 chunk 被檢索)× P(捱過 rerank top_k)× P(被 synthesizer cite)
> × P(圖片 ingestion 時綁對了 chunk)× P(捱過 cap / dedup / 揀圖)

每級就算 95%,五級相乘 ≈ 77%。**不同文件斷在不同一級 —— 這正是「一套配置不行」的數學根源,
per-doc 方向的正確性由此再次印證。**「文字對了但圖不齊」之所以特別頑固,是因為即使文字側完美,
圖片側仍有獨立的失敗概率(綁定 + 揀圖兩級)。

### 4.4 per-doc 配置的能力邊界

| 判定 | 失敗模式 | 原因層 |
|---|---|---|
| ✅ 醫得到 | 容量不夠(top_k / expansion)、圖洪水(cap)、揀圖不公平(nearest-first 餓死頭尾 section)、綁定深度 | **管道層損耗** — W43–W58 已證明配置可解 |
| ❌ 醫不到 | 圖片在排版上遠離它解釋的文字(跨頁 / 圖排在段落後 / 「見圖 3」遠距離引用)→ ingestion 綁錯 chunk | **語義層缺失** — 再多配置都改不了錯誤綁定 |
| ❌ 醫不到 | 被 cite 的 section 有 10 張圖但只有 3 張跟 query 相關 → 沒有機制知道是哪 3 張 | 同上 |
| ❌ 醫不到 | 相關圖片在一個沒被 cite 的 section 內 → 永遠不會出現 | 同上 |

### 4.5 最大缺口:圖片側完全沒有召回指標 ⭐

文字側有 Gate 1 R@5、RAGAs faithfulness、`distinct_sections` completeness proxy —— 所以文字側
可以系統性收斂。**圖片側的「成功」至今全靠用戶肉眼在 UI 驗證**:

- Eval set(`docs/eval-set-v0.yaml` 35 條 + W25 supplement + 跨檔 30 條)**沒有標注
  「每條 query 預期應返回哪幾張圖」**。
- 沒有 ground truth → 沒有 image-recall / image-precision → per-doc 調配置變回「試一下看一下」,
  跟當初想擺脫的「後台改配置」本質相同,只是搬上了 UI。
- 「一直不能一次完全成功」無法系統性改善,因為**連「離目標有多遠」都看不到**。

**提議(候選 phase「圖片召回指標」,工作量小、不動架構)**:

1. 揀 1–2 份代表性文件(圖密步驟手冊 + prose 型各一),為每條 eval query 標注 `expected_images`
   (用 `(doc_id, doc_order)` 或 checksum 引用)。
2. Eval harness 加兩個指標:**image-recall**(預期圖片中返回了多少)+ **image-precision**
   (返回圖片中多少是預期的)。
3. 跑 per-config 對比 → 得出實數,例如:「Drive manuals 類文件調好配置後圖片齊腳率 87%,
   失敗的 13% 全部是跨頁圖」——「真的可行嗎」由哲學問題變成實證問題。

約束核對:加 eval / 指標**不屬 H1**(per CLAUDE.md §5.1「加 test」例外),不動 index schema、
不動 pipeline;標注成本集中在 ground truth(每文件約 13–30 條 query)。
**附帶價值**:同一份指標同時是 **Gap B 必要性**(§3.1)和 **§4.6 結構性路線必要性**的判據。

### 4.6 結構性根治路線(僅記錄,不屬現階段)

要打破「位置繼承」天花板,出路是令圖片本身有語義信號。兩條路:

| 路線 | 內容 | 約束 |
|---|---|---|
| **圖片 caption 文字化** | ingestion 時用 vision 模型為每張圖生成 caption,索引成文字 → 檢索可在語義上「找到」圖片;cite 時也可判斷 section 內哪幾張圖真正相關 | **H1**(改 index schema + ingestion 加 LLM 調用,須 STOP+ask + ADR)。另有 H4 邊界問題:藍圖 §3.3 紅線「相關性 signal 限文字 / section / `doc_order`」— caption 生成用視覺模型,但檢索層仍是文字;是否踩線留 ADR 拍板 |
| **多模態檢索**(image embedding / 純圖搜索) | 圖片直接入向量空間 | **Tier 2,H4 明文禁**(architecture.md §11) |

**判斷次序**:先建 §4.5 指標 → 用實數看清位置繼承天花板實際在哪(可能 87% 已夠用)→
才決定要不要走 caption 的 H1 路。沒有指標之前,任何結構性投資都是盲目的。

---

## 5. 建議優先順序(若要收尾)

1. **DD-3 live 視覺驗證** —— 成本最低,亦是驗證 W57/W58 成果**真正可用**的最後一步(本專案反覆出現的
   smoke-user-deferred 模式,在當「完全交付」前值得親手走一次)。
2. **DD-4 production default flip** —— 純決策,eval 證據已齊,差一個用戶拍板。
3. **【新】圖片召回指標(§4.5)** —— 令產品核心價值(「文字 + 相關圖片齊腳」)首次可量度;
   亦是 Gap B 與 §4.6 結構性路線的共同判據。不動架構,工作量 = eval 標注 + harness 加兩個指標。
4. **DD-5 `answer_detail` 試跑預覽** —— 細改動,令試跑面板覆蓋齊全部 per-doc 旋鈕(可隨手併入
   任何 backend session)。
5. **Gap B** —— **不建議直接起**;等 per-doc 配置實測一輪 + §4.5 指標實數,有實證需要才 kickoff P3。

---

## 6. 兩個 session 分析的交叉驗證註記

本文件整合自兩個獨立 session 的盤點分析。兩者核心結論**完全一致**(W43–W58 主線已 close /
vision 端到端打通 / Gap B 是唯一未起主線層且必要性未證實 / DD-3/4/5 三個收尾項)—— 交叉驗證可信。
唯一實質差異 = §3.3「主動 scope-out」維度,已經 code 核實成立(W43 plan §Non-goals +
`PerQueryOverrides` docstring),補入本文件令「還有多少未進行」的全貌完整。

§4(圖片 recall 可行性)為 2026-06-10 第三輪補充:由用戶「真的可行嗎」提問觸發,
經 code 核實(orchestrator 圖片綁定機制 + query route 揀圖鏈)後沉澱,**非**前兩輪盤點內容。

---

## 7. 參考

- 總藍圖:[`docs/02-architecture/per-document-config-platform-design.md`](../02-architecture/per-document-config-platform-design.md)
- Deferred 登記冊:[`DEFERRED_REGISTER.md`](./DEFERRED_REGISTER.md)
- Vision(原話):memory `project_per_kb_tunable_config_vision`
- chat RAG 質素 follow-ups:memory `project_chat_demo_rag_quality_followups`
- 試跑兩面區分:memory `project_v4_retrieve_only_vs_query_pipeline`
- 關鍵 ADR:ADR-0040(per-KB config-scope)/ ADR-0041/0042(chunker cap)/ ADR-0048/0049(Gap C doc_order + section-fair)/ ADR-0050(Gap A per-doc backend)/ ADR-0051(Gap A per-doc UI)
- Phase folders:`docs/01-planning/W43-*` 至 `W58-*`(共 16 個)
- §4 圖片分析 code 依據:`backend/ingestion/orchestrator.py`(`img@<doc_order>` 位置綁定)/
  `backend/api/routes/query.py`(揀圖鏈:cite 自帶圖 → 鄰居補圖 → overview pin → cap → dedup)/
  `frontend/lib/chat/citation-images.ts`(排序 + dedup)
- Eval 基礎(§4.5 擴展對象):`docs/eval-set-v0.yaml` + `docs/eval-set-v0-w25-supplement.yaml` +
  `docs/eval-methodology.md`
