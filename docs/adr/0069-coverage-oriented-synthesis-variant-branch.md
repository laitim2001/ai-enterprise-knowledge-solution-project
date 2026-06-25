# ADR-0069: Coverage-oriented synthesis — 條件式變體 / 替代分支完整還原(乙類緩解)

**Date**: 2026-06-25
**Status**: Accepted(2026-06-25 由 decision owner 拍板,Proposed → Accepted)
**Approver**: Chris(技術 Lead)

> **本 ADR 已 Accept**(2026-06-25)→ W97 implementation 解鎖(per CLAUDE.md §5.1 H1 + §6 + §10 R1)。觸 H1:改 synthesizer(architecture.md §3 RAG core)合成行為,gated default OFF(production-preserve)。

## Context

**北極星(§15)**:答案要忠實還原原文段落 → 嗰段嘅圖自然有文字錨。乙類 = synthesizer 把原文段落濃縮掉 → 嗰段圖失錨(`docs/09-analysis/text_image_fidelity_recall_analysis_20260620.md` §5.3 + 2026-06-25 研究方向 A)。

**已有但不足**:`prompt_builder.py` 嘅 `SYSTEM_PROMPT_DETAILED`(`answer_detail=detailed`)Rule 3 已寫「reproduce the FULL procedure... enumerate EVERY DISTINCT step... do NOT summarize or omit any step」+ DEDUP 規則(BUG-036)。**但實證仍掉內容**:
- GL「post journal entry」案(effective config = detailed)仍掉 `[RMS/RSP] Petty cash` 變體段 + §3.1.1 Overview 段(analysis §4.1)。
- W96 gate F8 C003「write off a receivable」掉嘅 9 條 nugget **全部係條件式變體分支**(「for a single customer…」/「for multiple customers…」/「for RMS only…」/「for approval workflow…」)。

**精準根因**:現有 detailed prompt 捉到**主線程序步驟**,但捉唔到**條件式變體 / 替代分支 / scenario 子流程**(呢啲唔係「下一步」而係平行分支);加上 DEDUP 規則可能把 Overview/summary 段誤掃。

**前置就緒**:W96 完整度 gate(commit `4bca795`)+ DD-15 hardening(`2102eed`,paired A/B + 固定 nugget)已就緒,**對大 delta 可信**(解析度 ~±0.15)。coverage prompt 預期係大 + 系統性改動 → gate 量得到。

## Decision

加一條 **additive coverage rule** 到 synthesis system prompt,**閘喺一個新 per-KB/per-doc config knob 後**(default **OFF**,mirror 現有 `_MARKER_RULE` Rule 9 append pattern),只喺 `answer_detail=detailed` 之上 compose:

- **規則內容(實作時定字)**:除咗 enumerate 主線步驟,**亦必須 enumerate 原文 context 入面每個條件式變體 / 替代分支 / scenario 子流程**(例:「for single customer X / for multiple customers Y / for RMS only Z / for approval workflow W」),即使佢哋係 optional / 平行 / 例外路徑;以分支標題 + 其步驟呈現,不可當「重複」掃走。**校準 DEDUP 規則**令 summary/outline dedup 唔誤刪真實變體分支。
- **Default OFF → production-preserve**(knob off = system prompt byte-identical pre-ADR;現有 detailed/concise 行為不變)。
- **驗收靠 W96 gate A/B**:`scripts/run_completeness_ab.py` 比 knob-OFF(A)vs knob-ON(B)嘅 paired delta;**唔可以**憑感覺判好。研究明證「prompt 能消除位置偏置」**被反證 0-3** → 效果**未保證**,必須 A/B 量到清楚正向 delta(大過 gate ±0.15 解析度)先考慮 flip default。
- **Default flip = 另一決定**:本 ADR 只 land「knob + 規則 + A/B 驗證」;flip production default 需 gate 正向證據 + 再確認(類 ADR-0052 flip 流程)。

## Alternatives Considered

1. **就地改 `SYSTEM_PROMPT_DETAILED`**(非 gated)→ reject:即時改全部 production detailed 答案,無 A/B 安全網,撞 production-preserve 紀律。
2. **RL inserter / fine-tune synthesizer**(M2IO-R1 類)→ reject:觸 H4(禁 fine-tuning)+ 成本高。
3. **Extractive-then-abstractive 兩段式**(arXiv 2304.04193)→ reject:2026-06-25 研究**對抗驗證反證(1-2)**,且易變逐句複製失 synthesis 價值(analysis §5.3 警告)。
4. **U-形位置 prompt(明示覆蓋中段)** → 部分納入規則措辭考慮,但**唔當主力**:研究反證「prompt 能消除位置偏置」(0-3),只可作輔助 + A/B 驗。
5. **唔做** → reject:乙類係 §15 北極星核心缺口,且連帶失圖錨。

## Consequences

- **Positive**:條件式變體 / 分支段被還原 → 嗰啲段嘅圖自然重得文字錨(§15);完整度 gate 預期見正向 delta;opt-in 可逐 KB/doc 啟。
- **Negative**:
  - 答案更長 → faithfulness **length-bias**(eval 要留意)+ 撞 synth-timeout(DD-7,現 120s `synthesizer_request_timeout_s`,ADR-0053)→ 需驗 mega-procedure 唔 timeout。
  - 風險變**過度 extractive**(逐句抄)→ 規則要保「分支標題 + 步驟」結構化,非全文照搬;A/B 同時睇 faithfulness 唔崩。
  - gate 只解大 delta;若 prompt 只得細效果(< ±0.15),需先做 DD-15 殘餘 fixed-answer 模式先量得準。
- **Neutral**:default OFF;config 多一個 knob(四層 resolve per ADR-0040);concise mode 下 no-op。

## References

- CLAUDE.md §15 North-Star Principle + `docs/09-analysis/text_image_fidelity_recall_analysis_20260620.md` §5.3(乙類)+ `source_fidelity_recall_external_research_20260625.md`(方向 A,FineSurE/AutoNuggetizer/CRUX;extractive-then-abstractive 反證)
- W96 完整度 gate(`4bca795`)+ DD-15 hardening(`2102eed`)+ `docs/eval-methodology.md` §2.5
- `backend/generation/prompt_builder.py`(`SYSTEM_PROMPT_DETAILED` Rule 3 + `_MARKER_RULE` Rule 9 append pattern)
- ADR-0040(四層 config resolve)・ ADR-0052(default flip 流程 precedent)・ ADR-0053(synth timeout)・ DD-7(mega-section timeout)
- W97 phase plan(`docs/01-planning/W97-completeness-mitigation/plan.md`)
