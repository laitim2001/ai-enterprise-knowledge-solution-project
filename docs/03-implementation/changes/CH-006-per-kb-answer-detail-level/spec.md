---
change_id: CH-006
title: "Per-KB answer detail level (concise | detailed) for synthesis"
status: approved        # draft | proposed | approved | active | done | cancelled
created: 2026-06-06
target_completion: 2026-06-07
affects_components: [C05, C02]      # C05 Generation (prompt) + C02 KB Manager (KbConfig)
spec_refs:
  - architecture.md §3.1 §3.2 (Generation Pipeline / Synthesizer)
  - architecture.md §4.4 (per-KB tunable config, ADR-0040)
  - backend/generation/prompt_builder.py SYSTEM_PROMPT Rule 3
  - ADR-0040 (per-KB tunable config resolution → EffectiveConfig)
  - ROADMAP-per-kb-tunable-config.md
---

# CH-006 — Per-KB answer detail level (concise | detailed)

> **Spec version**:1.0(initial)
> **Owner**:AI(實作)/ Chris(approve)
> **Approved by**:Chris(2026-06-06 — chat「Approve」)

## 1. Context (Why)

W56 後續實測(2026-06-06,KB `w56-drive-ab-1` 6-doc DRIVE)揭示:procedural 問題(例「How do I post a journal entry in General Ledger?」)就算 **recall 已完整**(parent_doc 開咗 → 14/14 GL03 chunks 撈到、含 Excel 上載分支),chat 答案**仍然係 6 步摘要、缺逐個 sub-step**。

**根因 = synthesis,非 retrieval**:`prompt_builder.py` SYSTEM_PROMPT **Rule 3** 寫死「target <= 150 words total」→ LLM 手上有齊 14 塊都被逼壓縮。Scratch 證實:同樣 14 塊內容、用無字數上限 + 要求逐步鋪開嘅 prompt 餵 gpt-5.5 → 即刻吐返完整逐 sub-step 程序(Path 1 Excel 14 步 / Path 2 直接 / Validate / Approve / Post),granularity 對齊 manual。

**用戶要求**(2026-06-06 AskUserQuestion):答案要「逐步鋪開每個細節步驟」;且揀咗 **per-KB「答案詳細度」config** 作為設計方向(最貼合 per-KB 可調配置願景:manual KB 要 detailed、FAQ KB 要 concise)。

## 2. Scope (What)

### 2.1 Behavior Change
- **Before**:synthesizer 一律用單一 SYSTEM_PROMPT,Rule 3 硬性「target <= 150 words」→ 所有 KB 所有問題都係簡潔摘要。
- **After**:每個 KB 可設 `answer_detail`(`concise` | `detailed`)。`concise`(預設,= 現行 150-字 Rule 3,**零行為改變**);`detailed` = 換用放寬 Rule 3 變體(無字數上限、要求逐個 sub-step 鋪開、nested 編號列、唔好壓縮/省略),令 procedural 答案完整重現程序。

### 2.2 In Scope
- **C02**:`KbConfig.answer_detail: Literal["concise","detailed"] | None = None`(nullable,沿用 `enable_parent_doc_retrieval: bool | None` 模式;`None` → 跌返全域預設)。
- **C02**:`Settings.synthesis_answer_detail: str = "concise"` 全域預設(env override 用,保留現行行為)。
- **C02**:EffectiveConfig 加 `answer_detail` + `_resolve_effective_config` resolve(KB 值 → 全域 → "concise")。
- **C05**:`prompt_builder.py` —— `SYSTEM_PROMPT_CONCISE`(= 現行 SYSTEM_PROMPT,改名保留)+ NEW `SYSTEM_PROMPT_DETAILED`(放寬 Rule 3 變體;其餘 Rule 1/2/4-8 citation/refusal/language 不變);`build_prompt(..., detail_level="concise")` 新增參數揀 system prompt。為 backward-compat 保留 `SYSTEM_PROMPT` 別名指向 concise(現有 import/test 不破)。
- **C05**:`synthesizer.synthesize(...)` + stream 變體新增 `detail_level` 參數 → 傳入 `build_prompt`。
- **query.py**:`execute_query_pipeline` 把 `effective.answer_detail` 傳落 synthesizer(`/query` + `/query/stream` 兩路)。
- **Frontend C02 SettingsTab**(`kb/[id]/page.tsx`):喺現有 W43 advanced-tuning panel 加一個 `answer_detail` 選擇控件(concise / detailed),沿用該 panel 既有 OptionRow / select 視覺語言。
- **Tests**:prompt_builder detail-variant 選擇(concise 含「150」cap 字眼、detailed 不含 + 含「do not summarize」類指令);KbConfig 欄位 round-trip;effective resolution(KB→global→default);synthesizer 傳遞 detail_level;frontend vitest 控件 render + 預設值。

### 2.3 Out of Scope(explicit)
- ❌ 改任何 retrieval / recall 行為(parent_doc / top_k / rerank 不郁 — recall 已足夠)。
- ❌ intent-based 自動判斷問題類型(用戶明確揀 per-KB config 路線,非 intent 路線)。
- ❌ 全域強制 detailed(預設維持 concise,零行為改變)。
- ❌ `default_rerank_k` → chat 嘅 wiring gap(獨立議題,另開 CH/Bug,本 CH 不處理)。
- ❌ 把 `w56-drive-ab-1` flip 做 detailed(實作完由用戶自行喺 UI 撥)。

## 3. Acceptance Criteria

- [ ] `KbConfig` 有 `answer_detail` 欄位,POST/GET/PATCH `/kb` round-trip 正常(預設 `None`)。
- [ ] `answer_detail=None` 或 `"concise"` → synthesizer 用現行 150-字 prompt;**現有答案/測試零行為改變**(non-regression)。
- [ ] `answer_detail="detailed"` → synthesizer 用放寬 prompt;對 GL03 問題答案完整鋪開 sub-step(含 Excel 上載分支逐步)。
- [ ] EffectiveConfig resolve 次序:KB 值 > 全域 `synthesis_answer_detail` > `"concise"`。
- [ ] `/query` + `/query/stream` 兩路都採用 effective `answer_detail`(chat 路徑生效)。
- [ ] Frontend SettingsTab 有 concise/detailed 控件,撥後 save→PATCH 持久化;視覺對齊既有 tuning panel(H7)。
- [ ] 驗證指令:`backend/.venv/Scripts/python.exe -m pytest backend/tests/test_prompt_builder.py backend/tests/test_synthesizer*.py -q`(新/現有 test 全綠)+ frontend `pnpm vitest run` 相關檔綠 + ruff/tsc/lint clean。
- [ ] 手動 live 驗:`w56-drive-ab-1` 設 detailed → chat 問 GL03 → 答案逐 sub-step;設返 concise → 6 步摘要(對照)。

## 4. Risks

| # | Risk | Likelihood | Impact | Mitigation |
|---|---|---|---|---|
| R1 | 改 SYSTEM_PROMPT 牽連現有 synthesizer/citation 測試 | Med | Med | 保留 `SYSTEM_PROMPT` 別名 = concise variant;concise 內容逐字不變 → 現有 test 不破;新增 detail-variant test |
| R2 | detailed 模式答案變長 → RAGAs **faithfulness length-bias**(W49-W50 已知:長答案 faithfulness 易跌)| Med | Low | 文件標明此為已知互動(非 bug);detailed 為 opt-in per-KB,非預設;eval 解讀沿用 W50 length-bias caveat |
| R3 | detailed 模式 token/成本↑(完整鋪開 = 更長 output)| High | Low | opt-in per-KB;只 manual 類 KB 開;成本知情記 spec |
| R4 | Frontend 控件 H7 design fidelity(advanced-tuning panel 可能無對應 mockup)| Med | Low | 沿用該 panel 既有 OptionRow/select 視覺;若有 mockup gap → STOP per H7;否則屬 W43 tuning-panel design-stage expansion 一致延伸 |
| R5 | 跨 `/query` + `/query/stream` 兩路 wiring 遺漏一路 | Low | Med | acceptance 明列兩路;test 覆蓋 |

## 5. Effort Estimate

~0.5–1 day(backend prompt + config + wiring + tests ~半日;frontend 控件 + vitest ~數小時;live 驗)。

## 6. Dependencies

- 無外部 / OQ 阻塞。判 LLM 維 `gpt-5.5`(synthesizer,H2 lock)不變。
- 跨 component C05 + C02(per CC-1)。
- 無新 vendor / dep(純 prompt + schema + UI 控件)。
- 非 H1(無加/刪 §3/§4 component,無 vendor swap,無 storage layout 改動;synthesizer prompt 行為調整 + KbConfig additive 欄位)。

## 7. Spec Changelog(deviation log)

| Date | Change | Reason | Approver |
|---|---|---|---|
| 2026-06-06 | Initial draft | W56 後續 live 揭 synthesis 150-字 cap 係 procedural 答案殘缺根因;用戶揀 per-KB「答案詳細度」config 路線 | (待 approve) |
| 2026-06-06 | status draft → approved | Chris chat「Approve」;scope/acceptance/risks 確認,`default_rerank_k` wiring gap 明確另案 | Chris |

---

**Lifecycle reminder**:呢份 spec locked after status=approved。重大 deviation → §7 changelog。**未 approve 前不 implement(R1.change)。**
