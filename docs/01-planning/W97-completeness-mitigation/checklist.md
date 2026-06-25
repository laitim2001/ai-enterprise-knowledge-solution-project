# W97 Checklist — 乙類緩解:coverage-oriented synthesis

> Status active(2026-06-25 ADR-0069 Accept 後解鎖)。每項 atomic;daily tick。
> production-preserve 紀律:knob OFF 行為 byte-identical pre-ADR。

## F1 — Config knob(四層 resolve per ADR-0040,default OFF)

- [x] F1.1 schema:`enable_complete_coverage` 加入 `Settings`(`storage/settings.py`)/ `KbConfig`(`api/schemas/kb.py`)/ `DocConfig`(`api/schemas/doc_config.py`)/ `PerQueryOverrides` + `EffectiveConfig`(`generation/effective_config.py`)
- [x] F1.2 `Settings.enable_complete_coverage` default = **OFF**(production-preserve)
- [x] F1.3 四層 resolve 正確(per-query > per-doc > KB > Settings)— mirror `enable_inline_image_markers`(`_resolve` + `_layer`)
- [x] F1.4 `EffectiveConfig.enable_complete_coverage` 帶 knob 出去
- [x] F1.5 單元測試:resolve 優先序 4 case + default OFF + schema default None(`test_complete_coverage_w97.py` T4)

## F2 — `prompt_builder.py` additive coverage rule

- [x] F2.1 `_COVERAGE_RULE` 常數(mirror `_MARKER_RULE` append pattern,labelled 非 digit-numbered 避 collision)— 變體 / 替代分支 / scenario 子流程 enumerate 指令
- [x] F2.2 append 邏輯:`complete_coverage` ON **且** `detail_level=="detailed"` 先 compose;concise = no-op
- [x] F2.3 DEDUP 校準措辭(REFINES the DEDUP rule — 真實 conditional branch 永不當 duplicate)
- [x] F2.4 測試:knob OFF → system prompt **byte-identical** pre-ADR(concise + detailed,byte 比對);ON detailed → 含 COVERAGE;ON concise no-op;compose after marker(`test_complete_coverage_w97.py` T1-T3)

## F3 — Wire knob → build_prompt

- [x] F3.1 `synthesizer.py` synthesize + synthesize_stream 讀 `getattr(effective_config, "enable_complete_coverage")` → `build_prompt(complete_coverage=...)`;query.py 零改動(knob 經 `EffectiveConfig` 自動流通)
- [x] F3.2 測試:thread coverage into system prompt(ON 含 COVERAGE / OFF byte-identical detailed,`test_complete_coverage_w97.py` T5);75 既有 affected 測試全綠(零 regression)

## F4 — A/B 驗證(W96 gate)

- [ ] F4.1 `run_completeness_ab.py` 支援 config-A(OFF)vs config-B(ON)(`--config-a/-b` 或 per-KB 切換)
- [ ] F4.2 跑 GL / write-off 變體案(條件式分支被掉嗰啲)
- [ ] F4.3 完整度 paired delta **清楚正向 + 大過 gate ±0.15 解析度**(變體 nugget 被還原)
- [ ] F4.4 RAGAs faithfulness 唔崩(length-bias 留意)
- [ ] F4.5 **無 synth-timeout regression**(DD-7 mega-procedure,如 GL post-journal)

## F5 — Doc-sync + close

- [x] F5.1 ADR-0069 Status Proposed → **Accepted**(2026-06-25 decision owner 拍板)
- [ ] F5.2 DD-16 close(DEFERRED_REGISTER)
- [ ] F5.3 `docs/eval-methodology.md` §2.5 + memory `project_completeness_eval_gate_w96` 同步
- [ ] F5.4 production default flip 明列為**另一決定**(out-of-scope,類 ADR-0052)
