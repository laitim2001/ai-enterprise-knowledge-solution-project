# W97 Progress — 乙類緩解:coverage-oriented synthesis

> 接 W96 完整度 gate + DD-16。北極星 §15:答案忠實還原原文段落 → 嗰段圖自然得文字錨。

## Day 1 — 2026-06-25

### ADR-0069 Accept + phase kickoff

- **ADR-0069 由 decision owner 拍板 Accept**(Proposed → Accepted)→ §5.1 H1 解鎖,W97 plan draft → active。
- 補齊 phase 三件套:`plan.md`(active)+ `checklist.md`(F1-F5 atomic)+ 本 `progress.md`。
- F5.1 ADR Accept 先 tick(其餘 F5 phase 收尾做)。

### 範圍提醒(承 ADR-0069)

- 緩解 = additive coverage rule **閘新 config knob default OFF**(mirror `_MARKER_RULE` Rule 9),只喺 `answer_detail=detailed` 之上 compose 變體 / 替代分支 / scenario 子流程 enumerate。
- **驗收靠 W96 gate A/B**(`run_completeness_ab.py`),唔憑感覺;研究反證「prompt 消除位置偏置」(0-3)→ 效果未保證,要量到清楚正向 delta(大過 gate ±0.15 解析度)先考慮 flip default。
- production default flip = 另一決定(out-of-scope)。

### 風險載入(plan §4)

- 🔴 length-bias + synth-timeout(DD-7,120s `synthesizer_request_timeout_s`)→ F4 必驗 mega-procedure。
- 🔴 backend reload=False → 改 prompt code 後重啟驗(`project_stale_backend_no_reload`)。
- 🟡 過度 extractive / 效果 < gate 解析度 → 後者觸發先補 DD-15 fixed-answer。

### F1-F3 落地(code + 測試)

- **F1 config knob 四層**:`enable_complete_coverage` 加入 `Settings`(default OFF)/ `KbConfig` / `DocConfig` / `PerQueryOverrides` + `EffectiveConfig` + `resolve_effective_config`(mirror `enable_inline_image_markers` `_resolve`+`_layer`)。
- **F2 prompt rule**:`prompt_builder.py` 加 `_COVERAGE_RULE`(labelled,非 digit-numbered → compose 喺 optional Rule 9 marker 之後無 collision)+ `build_prompt(complete_coverage=...)`;gate = `complete_coverage and detail_level=="detailed"`(concise no-op);OFF byte-identical pre-W97。
- **F3 wire**:`synthesizer.py` synthesize + synthesize_stream `getattr` 讀 knob → `build_prompt`;**query.py 零改動**(knob 經 `EffectiveConfig` 自動流通,per-query seam 預設 None fall-through)。
- **驗證**:新 `test_complete_coverage_w97.py` 16 測試 + 既有 affected(answer_detail / effective_config / inline_image_markers)= **75 passed**。ruff clean(import 排序 auto-fix)。mypy:`effective_config` / `prompt_builder` 自身 clean;`synthesizer.py` 嘅 `create()` overload error 喺 **HEAD pre-W97 已有 3 個**(grep 確認),W97 零新 error。
- production-preserve:全部 OFF path byte-identical;default OFF → 未跑 A/B 前 production 行為不變。

### 下一步

- **F4 A/B 驗證**(W96 gate,需 backend 重啟 + live LLM run):knob OFF(A)vs ON(B)paired delta + faithfulness + timeout(DD-7)。**待 commit F1-F3 + 用戶確認跑 F4**。
