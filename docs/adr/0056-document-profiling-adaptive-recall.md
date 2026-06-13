# ADR-0056: 文件畫像驅動嘅自適應 recall 流程(rule-based profiling + routing,LLM 選用保險)

**Date**: 2026-06-13
**Status**: Proposed(待 Chris 技術審 + stakeholder scope 拍板 — 涉及產品方向,行 decision-form)
**Approver**: _pending_ — Chris(技術 Lead,H1/H4 架構)+ Stakeholder(scope / 業務,per `docs/decision-form.md`)

> **本 ADR 仍係 `Proposed`**:只 commit 文件 + 勘查 script,**未動任何 production code**。
> 三輪實證(`scripts/explore_doc_profiling.py` / `explore_doc_profiling_v2.py` /
> `explore_doc_content.py`)已跑,結論支撐方向;落地需 Accept 後另開 phase(rolling JIT)。

---

## Context

### 緣起:W71 末尾堆暴露嘅結構性張力

W71(ADR-0055)把帶 `[IMG#sha8]` 標記嘅圖交織入答案,但用戶 2026-06-13 實測一條多模組 query
(`add fixed asset ap invoice depreciation method create gl account`)發現:召回 80 張圖,只有
~44 張有 inline 標記被錨定,其餘 ~36 張(figure 33–77)落末尾「Referenced screenshots」堆、
冇對應文字。根因 = image-recall 弧(W59–W68,cap=80 / `citation_neighbour_max_aux_images`=40)
為追求 ~1.00 召回撈嘅 neighbour / aux 圖,係 **post-synthesis** 補撈,synthesizer prompt 根本
見唔到 → 永遠冇標記 → 必然落末尾(per ADR-0055 §結構性限制)。W71 plan §5 早已預留「aux /
neighbour 圖 section 級錨定(方案 A)」為非目標,留待評估。

### 用戶訴求:唔可以只服務一種文件類型

用戶 2026-06-13 明確:**EKP 作為 Tier 1 Foundation,唔可以淨係對 docx 結構化 SOP 做得好**。
真實企業場景有散文政策 / 簡報 / PDF manual / 掃描件 / 跨模組 query,每種都要對應處理流程。
用戶提議:**先判斷文件內容格式屬於什麼類型和場景,再判斷應該使用哪一種處理流程**(即「為不同
文件類型分類到最適合的 recall 流程」)。此訴求係用戶 2026-06-01 foundational vision(per memory
`project_per_kb_tunable_config_vision`:系統 + UI 讓用戶自行設置調整,不同 KB 文件度身訂做配置)
嘅自然進化 —— 由「人手 per-KB 揀配置」升級到「系統先檢測 → 自動揀流程 + 用戶 UI 可調 override」。

### 方案 A 嘅文件類型敏感性

評估 W71 方案 A(section 級錨定)時發現:其收益同文件結構質素成正比、錯位風險同結構鬆散成反比
——結構化 SOP 收益高風險低;散文 / 簡報 / scan PDF 收益遞減、錯位風險上升。即「一刀切全局開
方案 A」會喺非結構化文件反噬。**正確做法 = 條件式:識別文件 profile,只喺適合嘅 profile 開
對應流程。** 此判斷直接驅動本 ADR。

### 三輪實證勘查(2026-06-13)

用戶喺 `docs/06-reference/01-sample-doc/` 放咗 33 份真實企業文件(14 docx / 13 pptx / 3 pdf /
3 xlsx)。用 EKP 現有 parser(`select_parser` → DoclingDocx / DoclingPdf / Pptx)抽結構信號,
跑 rule-based 分類:

**輪 1(`explore_doc_profiling.py`,v1 規則)**:命中 ~70%。揭露:
- P1 結構化 SOP signature 極清晰(6 份 DRIVE manuals:`depth`=4 + `img_density` 0.25–0.61 +
  `list_ratio` 0.52–0.65,三重信號零誤判)。
- **PDF 嘅 `img_density` 永遠 = 0**(Docling PDF parser 唔抽 embedded image)→ 任何靠圖密度
  嘅 rule 對 PDF 全失效。系統性信號缺口。
- 純文字步驟型(procedure / runbook)因低圖被 v1 P1 條件(`img_d>=0.1`)拒,落 P5。
- form / xlsx 未涵蓋;pptx 一刀切掩蓋圖密 deck vs 文字 deck。

**輪 2(`explore_doc_profiling_v2.py`,v2 規則 — reuse v1 parse 信號,純 re-classify)**:命中
**90%**(扣噪音 88.9%)。四項修正全部生效:① P1 拆 `imgdense` / `text` 兩支(純文字 SOP 唔靠圖)
② per-format(pptx 一律 P3、PDF 唔靠圖密度)③ 加 `P5_form` 類別 ④ `too_small` 過濾噪音。
v2 剩 3 個 miss。

**輪 3(`explore_doc_content.py`,抽真內容驗 ground truth + PDF text-layer 探測)**:
- 5 份 ground truth **全部確認人判正確**(`AI demonstration.pdf` = 簡報 / `AI-Governance-
  Procedure.pdf` = procedure / 兩份 Virtual_Boss = 問卷 + 散文 / Registration = form)。
- **反轉發現:3 個 v2 miss 全部有 rule 信號可救,非 LLM 不可嘅 = 0 份(於此 sample)**:
  - PDF 簡報撞 SOP → **每頁文字密度**可分(簡報 ~300 chars/page vs procedure ~2000 chars/page)。
  - 問卷撞散文 → **tick-box / Q-marker 密度**(`□` `★` `Qn` `answer:`)可救。
  - 短文被噪音殺 → `too_small` 門檻 25→20 可救。
- **PDF text-layer 全部唔空 → sample 冇真掃描件 → P4 scan 類別 0 樣本驗證**(未閉合口)。

實證裁決:**rule-based 主幹站得住(v2 90% / v3 預估 ~95%),LLM 真正剩低需求趨近極小;
但 P4 scan 未驗 + sample 偏細,LLM 應保留做 scan / 真語義陷阱嘅選用保險。**

---

## Decision

採用 **rule-based 文件畫像(profiling)+ 流程路由(routing)為主幹,LLM 退為邊界選用保險(hybrid)**,
全程接駁 EKP 現有 config 平台(ADR-0040 / ADR-0050 / W69 preset),三層 UI 可調體現用戶
「最大限度自行調試」哲學。

### D1. Profile taxonomy(六類 + 信心度)

| Profile | 定義 | 主要偵測信號(rule)| 對應 recall / render 流程 |
|---|---|---|---|
| **P1_sop_imgdense** | 圖密結構化步驟手冊 | `depth≥3` + `img_density≥0.15` + `list_ratio≥0.3` | 高 image cap + **section 級錨定(方案 A)** + inline marker ON |
| **P1_sop_text** | 純文字步驟型(procedure / runbook)| `list_ratio≥0.12` + `headings≥10`(低圖)| 步驟錨定 + 低 image cap |
| **P2_prose** | 散文政策 / 報告 | `head_density≥0.05` + `list_ratio<0.12` | 中 cap + 末尾堆(唔做 section 錨定,避錯位)|
| **P3_slide** | 簡報 | `format=pptx`,或 PDF **每頁文字密度低**;按 `img_density` 細分 imgdense / text | slide 順序錨定 + imgdense 開圖流程 |
| **P4_scan_imgdense** | 掃描 / 純圖無 heading | PDF **text-layer 空比例高**(`pypdfium2` pre-OCR 探測)| 純 gallery + OCR 依賴(**偵測已驗證 2026-06-13 — 7/7 scan 空比例 1.0**)|
| **P5_form** | 表單 / 問卷 | `headings≤1`,或 **tick-box / Q-marker 密度**高,或 **table 密度**高 | table 為主 + 末尾堆 |

低信心度(信號矛盾 / 邊界)→ flag「待人手確認」,或選用 LLM tie-break(見 D5)。

### D2. Rule v3 偵測信號(現有 + 新增,全部 rule-based)

**現有(已喺 `ParserResult`)**:`headings` 數 / `heading_level` 最大深度 / `embedded_images` 數 /
`list_item` 比例 / `tables` 數 / `paragraphs` 總數 + 衍生密度。

**新增(實證驅動,v3)**:
- **每頁文字密度(chars/page)** — 分 PDF 簡報 vs PDF 文件;需 parser 出 page metadata(目前
  `ParserResult` 無,要加)。
- **PDF text-layer 空比例** — 分 text-PDF vs scan-PDF(P4);用 `pypdfium2`(Docling 自帶,零新 dep);**2026-06-13 驗 7/7 scan 空比例 1.0,且必須 pre-OCR 探測**(Docling OCR 後 `embedded_images`=0 + heading 誤判,parse 後信號失效 → 偵測要喺 OCR 之前)。
- **tick-box / Q-marker 密度**(`□` `★` `Qn` `Your answer:`)— 救問卷式 form。
- **table 密度** — 救 grid form。
- **`too_small` 門檻 25→20** — 救短真文件被誤殺。

### D3. 端到端功能流程

**A. Ingestion 時(自動)**:`Parse(現有)` → **【新】Profiler 抽信號 → 判 profile + 信心度** →
**【新】Routing:profile → recall / render preset** → 自動套 preset 落該文件(寫 per-doc config,
ADR-0050 層)→ 信心度低則 flag 待確認(或 LLM tie-break)。

**B. Query 時**:用該文件 / KB 已 resolve 嘅 config 跑 pipeline(per-doc overlay,W57 已有);
profile 決定 image 錨定策略(P1 section 錨定 / P3 slide 順序 / P2 末尾堆 / FORM table 為主)。

**C. 接駁點全部係現有組件**(延伸非重寫):Profiler = `backend/ingestion/` 新 module;
profile→preset = W69 preset 機制;套 preset = per-doc config(ADR-0050);query resolve =
per-doc overlay(W57);試跑驗證 = config-test harness(W48)。

### D4. 三層 UI 可調(體現「最大限度自行調試」)

| 層 | 用戶體驗 | UI 位置 |
|---|---|---|
| **L1 自動** | 偵測 + 自動套 preset,零操作 | ingestion 後台 |
| **L2 一鍵 override** | UI 睇 profile + 信心度,唔啱一鍵換 profile / 換 preset | KB Detail 文件列表 + Doc Detail |
| **L3 逐 knob 微調 + 試跑** | 逐旋鈕調 + config-test 即時試跑 | Per-doc 配置 tab(W58 已有)|

**具體 UI 改動**(全部喺現有頁面加,唔推倒):
1. **KB Detail 文件列表**(`/kb/{id}`)— 每文件加 profile badge + 信心度,低信心黃旗。
2. **Doc Detail / Per-doc 配置 tab**(W58)— 加「文件畫像」section:偵測信號透明展示 + 判定
   profile + 信心度 + **override 下拉** + profile 對應 preset knob(可調)。
3. **「文件分類規則」設定**(Settings 一個 tab)— admin 調 profile→preset 映射 / threshold /
   preset 內容 —— 自行調試嘅指揮中心。
4. **上載流程** — 上載後即顯示「偵測為 P1,已套 X preset」+ 可即時 override。
5. **config-test 試跑**(W48 已有)— profile / preset 改完即試跑驗證。

> ⚠️ **H7**:上述 UI 元素 `references/design-mockups/` **大概率冇對應 mockup**(profiling 係新
> concept)。實作前必須先設計 + 加 mockup,per §5.7 H7 STOP+ask 對齊。本 ADR 只定方向,唔定像素。

### D5. Hybrid:LLM 退為選用保險(H4 劃界)

LLM **唔做主力分類**,只喺兩種情況選用:① rule 信心度低(信號矛盾)② P4 scan / 真語義陷阱
(結構信號呃人)。**H4 邊界:LLM 只輸出 profile classification label(+ 信心度),絕不做 dynamic
pipeline assembly / multi-agent orchestration**(嗰啲係 Tier 2,§11)。vendor = Azure OpenAI
`gpt-5.4-mini`(judge-tier,per memory `feedback_judge_llm_cost_policy`,**不升 gpt-5.5**)。

### D6. per-KB / per-doc override(接 ADR-0040 / ADR-0050)

profile 偵測結果 + 套用 preset 全部寫入現有四層 config 解析(per-query > per-doc > per-KB >
global)。admin override 永遠優先於自動偵測 —— 保住可解釋 + 人可介入(用戶 vision 核心)。

### D7. Open / future scope(誠實標明未閉合)

- **P4 scan 類別 — 偵測已驗證(2026-06-13)**:用戶補 7 份真 scan(多幣種發票,clean /
  skewed / noisy_photocopy + 繁中 / 越南文)。`scripts/explore_scan_pdf.py` 探測 **7/7
  text-layer 空比例 = 1.0**(`pypdfium2` pre-OCR,零 chars)→ P4 核心信號成立、同 text-PDF
  一刀切分開。入庫可行:`scripts/explore_scan_parse.py` 跑 03_VND(5 頁)過 DoclingPdfParser
  **`parse_failed=False`**(唔 crash)、OCR 抽到 999 chars 越南文發票。**設計鎖定**:OCR 後
  `embedded_images`=0(page raster 非 embedded)+ headings=10 屬 OCR font heuristic 誤判 →
  **P4 偵測必須 pre-OCR text-layer 探測,唔可以靠 Docling parse 後信號**。**caveat**:OCR
  ~76s/頁(5 頁 382s)成本高;noisy / skewed 多頁可能觸 `std::bad_alloc`(per AI demonstration
  先例,未全驗)→ 落地要 ingestion robustness 處理。
- **xlsx 支援 — future(H2)**:`select_parser` 對 xlsx raise;3 份差旅 spreadsheet 證實企業有
  此需求。新 parser = 另一條 H2 vendor / dependency 決定,本 ADR 不含。
- **parser robustness**:PDF OCR `std::bad_alloc`(`AI demonstration.pdf`)+ docx 圖 Pillow load
  失敗(`AI-Governance-Guideline.docx`)會污染 profiling 信號質素 → 上游 ingestion 要修。

---

## Alternatives Considered

### A. 純 LLM classification(每文件 LLM 判 profile)
- **Reject 原因**:實證顯示 rule-based 已 cover 90%+,LLM 喺結構清晰文件 overkill 兼有 stochastic
  誤判風險;LLM 真正不可取代嘅喺此 sample 趨近 0。LLM 主力 = 黑盒、難 debug、recurring eval
  維護成本高、滑向 H4 Tier 邊界。純效果天花板雖略高,但 production 重可預測 / 可解釋 > 峰值準確度。

### B. 純 rule v1(format-only `chunk_strategy=auto` 式)
- **Reject 原因**:v1 只 70%,PDF 信號缺口 + 純文字 SOP 接唔到 + form 未涵蓋。太粗,唔夠 cover
  企業文件多樣性。

### C. 唔做 profiling(維持手動 per-KB config + 接受末尾堆)
- **Reject 原因**:違背用戶「多文件類型適應」+「最大限度自行調試」核心訴求;末尾堆問題喺多模組
  query 持續;每新 KB 都要人手調 config,唔 scalable。

### D. (採用)rule v3 主幹 + LLM 邊界選用保險(hybrid)
- **Accept 原因**:實證命中 ~95%(v3 預估);$0 主幹 + 微成本 LLM 保險;可解釋 + 可 override;
  Tier 1 安全;接駁現有 config 平台(延伸非重寫);三層 UI 完整體現用戶 vision。

---

## Consequences

**Positive**:
- 多文件類型自動適應,唔再只服務 docx SOP;末尾堆喺 P1 文件由 section 錨定大幅縮細。
- rule 主幹 deterministic / 可解釋 / $0;admin UI 可見可 override,人可介入。
- 接駁現有 config 平台,基建一半已有(routing / preset / per-doc overlay / config-test)。
- LLM 成本只落 ~5% 邊界,eval set 細,維護負擔收窄。

**Negative**:
- 新 profiler + routing 層 = 複雜度上升;偵測準確度本身係新 failure surface(分錯 → 路由錯)。
- 新增信號(頁密度 / text-layer)要 parser 出 page metadata,改動 `ParserResult` 契約。
- 新 UI 觸 H7(無 mockup),要先設計;LLM 保險觸 H4 邊界,要嚴守 label-only。
- P4 scan 未驗 + sample 偏細,真實命中率有不確定性。

**Neutral**:
- 全程 per-KB / per-doc override,admin 永遠可推翻自動結果 — 自動係 default 唔係強制。
- knob 沿用現有(cap / max_aux / chunk_strategy / inline marker),唔新增旋鈕種類,只係自動賦值。

---

## Open Questions

- ~~**OQ-A(P4 scan)**~~ **RESOLVED 2026-06-13**:用戶補 7 份真 scan;7/7 text-layer 空比例
  1.0 驗證 P4 偵測信號;Docling OCR 入庫可行(`parse_failed=False`,唔 crash)。衍生鎖定:P4
  偵測用 pre-OCR `pypdfium2` text-layer 探測。衍生 caveat:scan OCR 成本高(~76s/頁)+
  noisy / skewed robustness(`std::bad_alloc`)待落地 ingestion 處理。
- **OQ-B(新 UI mockup)**:profiling UI(badge / 文件畫像 section / 分類規則設定)需設計 + 加
  `design-mockups`,H7 對齊。
- **OQ-C(LLM 保險 eval)**:若採用 LLM tie-break,需細 eval set cover 邊界 case + drift 監控。
- **OQ-D(profile 數量)**:六類是否足夠?抑或 mixed / spec / 多語等要再加?(simplicity-first
  克制,先六類)。

---

## References

- 實證 script:`scripts/explore_doc_profiling.py`(v1)/ `explore_doc_profiling_v2.py`(v2,90%)/
  `explore_doc_content.py`(ground truth + PDF text-layer)/ `explore_scan_pdf.py`(P4 scan
  text-layer 探測 7/7)/ `explore_scan_parse.py`(scan OCR 入庫驗證)
- Sample corpus:`docs/06-reference/01-sample-doc/`(33 份真實企業文件)+ `scanned_pdf_sample/`
  (7 份真 scan 發票,多幣種 / 多語言 / clean·skewed·noisy)
- 接駁 ADR:ADR-0040(per-KB tunable config)/ ADR-0050(per-doc config scope)/ ADR-0055(inline
  image markers + 交織 render)/ ADR-0054(dedup-before-cap image budget)
- W71 plan §5(方案 A 非目標預留):`docs/01-planning/W71-inline-image-interleave/plan.md`
- Parser 契約:`backend/ingestion/parsers/base.py`(`ParserResult`)/ `chunker/strategies.py`
  (`chunk_strategy=auto` rule-based 先例)
- 約束:CLAUDE.md §5.1 H1(architectural)/ §5.4 H4(Tier 邊界)/ §5.7 H7(design fidelity)/
  §5.2 H2(vendor — xlsx parser)
- 用戶 vision:memory `project_per_kb_tunable_config_vision` + `project_inline_image_markers_w70`
- spec:`docs/architecture.md` §3.3(Multi-Format Strategy)/ §11(Tier 2 trigger matrix)
