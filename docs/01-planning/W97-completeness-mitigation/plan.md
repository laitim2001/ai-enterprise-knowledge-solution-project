# W97 — 乙類緩解:coverage-oriented synthesis(條件式變體 / 分支還原)

| 項目 | 值 |
|---|---|
| Phase | W97-completeness-mitigation(source-fidelity §15 北極星線 · 接 W96 gate + DD-16) |
| Status | **active**(2026-06-25 ADR-0069 已 Accept → 轉 active,per §5.1 H1 + §10 R1) |
| Tier | Tier 1(改 synthesizer prompt 策略,gated default OFF) |
| 依賴 | **ADR-0069(Proposed → 待 Accept)**・ W96 完整度 gate(`4bca795`)+ DD-15 hardening(`2102eed`) |
| 錨點 | **ADR-0069**・ CLAUDE.md §15・`docs/09-analysis/text_image_fidelity_recall_analysis_20260620.md` §5.3・`source_fidelity_recall_external_research_20260625.md` 方向 A |
| 粗估 | 中(F1-F5;prompt + config knob + A/B 驗證) |
| 下一期 | production default flip(另一決定,類 ADR-0052;需 gate 正向證據 + 再確認) |

> **H1 gating**:本 plan 受 ADR-0069 約束,**ADR Accept 前唔可以 implement**(§5.1 H1 + §10 R1)。草案先定 scope + acceptance,等批。

## §1 目標(Why)

乙類精準根因(ADR-0069 Context):現有 `SYSTEM_PROMPT_DETAILED` 捉到主線步驟,但掉**條件式變體 / 替代分支 / scenario 子流程**(W96 F8 C003 掉嘅 9 條 nugget 全屬此類;GL案掉 RMS/RSP 變體 + Overview)。緩解 = 加 coverage rule 令變體分支都還原 → 嗰啲段嘅圖自然重得文字錨(§15)。

## §2 Deliverables(F1–F5)

| # | Deliverable | Acceptance |
|---|---|---|
| **F1** | 新 config knob(四層 resolve per ADR-0040)+ schema + `effective_config` + default **OFF** | knob 加入 `Settings` / KB / per-doc / per-query;resolve 正確;default OFF;單元測試;**production-preserve**(off = 行為不變) |
| **F2** | `prompt_builder.py` additive coverage rule(append 到 detailed prompt 當 knob ON,mirror `_MARKER_RULE` Rule 9 pattern)+ 變體/分支 enumerate 指令 + DEDUP 校準 | knob OFF → system prompt **byte-identical** pre-ADR(substring + byte test);knob ON → 含變體覆蓋規則;concise mode no-op |
| **F3** | Wire knob 經 pipeline → `build_prompt`(synthesizer / query route) | effective config → build_prompt 正確帶 knob;單元/route 測試;off bit-identical |
| **F4** | **A/B 驗證(W96 gate)** — knob OFF(A)vs ON(B)paired delta + faithfulness + timeout | `run_completeness_ab.py` 用 `--config-a/-b`(或 per-KB config 切換)跑 GL/write-off 變體案;**完整度 paired delta 清楚正向 + 大過 gate ±0.15 解析度**(變體 nugget 被還原);RAGAs faithfulness 唔崩(length-bias 留意);**無 synth-timeout regression**(DD-7,mega-procedure) |
| **F5** | Doc-sync + ADR-0069 Accept(Chris 後)+ DEFERRED DD-16 close + memory | ADR Status Proposed→Accepted;DD-16 close;eval-methodology / memory 同步;**default flip 列另一決定(out-of-scope)** |

## §3 Phase Gate

- **G-W97**:F1-F3 knob OFF byte-identical(production-preserve)+ F4 **A/B 完整度 delta 清楚正向**(變體 nugget 還原,大過 gate 解析度)+ faithfulness 唔崩 + 無 timeout regression + ADR-0069 Accepted。
- A/B 若 delta < ±0.15(gate 解唔到)→ 先做 DD-15 殘餘 fixed-answer 模式(temperature=0 量準)再判,**唔可以**憑感覺話「prompt 有效」(研究反證「prompt 消除位置偏置」0-3)。

## §4 Risks

- 🔴 **length-bias + synth-timeout(DD-7)**:更長答案 → faithfulness length-bias + 撞 120s `synthesizer_request_timeout_s`(ADR-0053)。F4 必驗 mega-procedure(如 GL post-journal)唔 timeout + faithfulness 唔崩。
- 🟡 **過度 extractive**:逐句抄失 synthesis 價值(analysis §5.3)→ 規則保「分支標題 + 步驟」結構化;A/B 同睇 faithfulness。
- 🟡 **效果 < gate 解析度**:若 prompt 只得細效果(< ±0.15)→ gate 量唔到 → 先補 DD-15 fixed-answer(temp=0)再驗。
- 🔴 **backend reload=False**:改 backend prompt code 後重啟驗(per `project_stale_backend_no_reload`;pytest 綠 ≠ running server 有該 code)。
- 🟡 **H1**:本 plan ADR-0069 gating;Accept 前唔 implement。

## §5 Out of scope(留後續)

- **Production default flip**(knob OFF→ON 全域)= 另一決定(類 ADR-0052),需 gate 正向證據 + 再確認。本 phase 只 land knob + 規則 + A/B 驗證。
- **DD-15 殘餘 fixed-answer 模式**(temperature=0 直呼 synthesizer)= 只喺 F4 delta < gate 解析度時先做。
- 甲類圖→步驟級錨定(階梯 ① runtime `doc_order`)= 另一條腿,本 phase 不碰。

## §6 Changelog

| 日期 | 變動 | 由 |
|---|---|---|
| 2026-06-25 | Phase draft kickoff — DD-16 解鎖(W96 gate 對大 delta 可信)。ADR-0069 Proposed。F1-F5 分段;gated default OFF + W96 gate A/B 驗。**待 ADR Accept 轉 active** | 草案 |
| 2026-06-25 | **ADR-0069 Accept(decision owner 拍板)→ plan draft→active**。H1 解鎖,F1 開工。checklist + progress 補齊 | Accept |
