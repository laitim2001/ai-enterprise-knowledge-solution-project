# ADR-0051: Doc-Detail Per-Document 配置 surface(design-stage expansion)

**Date**: 2026-06-09
**Status**: Accepted
**Approver**: Chris(2026-06-09 — mockup review PASS)

## Context

ADR-0050(W57 / P2a)落地 per-document 配置**後端**(`DocConfigStore` + EffectiveConfig per-DOC layer +
dominant-doc 解析 + CRUD API + config-test doc-scope)。用戶 vision 要求配置可「喺 UI 頁面上操作、配置、
管理」——即 P2b UI 層。

**H7 缺口**:per-doc 配置 UI 喺 design-mockup **完全冇對應 surface** ——
`references/design-mockups/ekp-page-doc-detail.jsx` 係純唯讀 chunk inspector(outline / chunk list /
inspector 三欄 + pipeline strip + image strip),無任何 config / settings 面;mockup 入面 config UI **只
存在於 KB 層**(`ekp-page-kb.jsx` `TabKbSettings`)。按 §5.7 H7,呢個係 STOP+ask trigger,**唔可以自行
approximate** 一個新 UI。

用戶 2026-06-09(AskUserQuestion)揀**路徑 A —— 先擴 doc-detail mockup**(over 路徑 B 沿用 KB
SettingsTab pattern 但無 mockup backing):先喺 mockup 加 per-doc config 面、design 確認,**然後先**砌
frontend。屬 DESIGN_README 標明嘅 design-stage expansion ADR-route precedent(KB Detail 5→8 tabs /
Settings v1→6 tabs / `/users` Tier 1.5)。

## Decision

**doc-detail 頁(`/kb/[id]/docs/[docId]`)加 per-document 配置 surface,為 design-stage expansion:**

1. **Tab strip**:doc-detail 由單一 3-pane view 改為 tabbed —— **[Chunk inspector]**(現有 pipeline strip +
   image strip + outline/chunk-list/inspector 三欄,視覺不變)+ **[Per-doc 配置]**(新)。Mirror KB detail
   頁既有 tab pattern,design-system consistent。

2. **Per-doc 配置面只暴露 post-retrieval 旋鈕**(per ADR-0050):`answer_detail`(concise/detailed seg)+
   Citation post-hoc expansion group + Citation neighbour images + 圖片上限 group(`enable_*` toggle +
   numeric knobs)。**檢索入口旋鈕**(`default_top_k` / `default_rerank_k` / `parent_doc_*`)**不暴露**喺
   per-doc 面 —— 用 explanatory affordance 指引去 KB 設定(per ADR-0050:呢類旋鈕喺引文未知前已消耗,
   維持 per-KB)。

3. **繼承語意**:per-doc 旋鈕 None = **繼承 KB**(再全域)。Badge =「繼承 KB」/「已覆寫(此文件)」;
   每旋鈕有「還原至 KB」affordance;scope 註明「per-query > **per-DOC(此文件)** > per-KB > 全域 ·
   ADR-0050」。視覺忠實 mirror KB `KbTuneKnob`/`KbTuneGroup` pattern(繼承來源由「全域」→「KB」)。

4. **Per-doc config-test 面**:reuse KB config-test 嘅 N-run band + A/B + faithfulness + 完整性 proxy 視覺
   (`KbTestResultCard`/`KbTestMetric`),scope 到此文件(`POST /kb/{kb}/config-test` body `doc_id`)。

5. **H7 gate**:本 ADR Status = Proposed;mockup(`ekp-page-doc-detail.jsx` 擴展)design 確認 + 用戶 review
   後 → Accepted。frontend build(W58 F2-F4)**gated on** mockup approve;build 完成後 visual fidelity 仍
   受 H7 約束(逐元素對齊 approved mockup)。

## Alternatives Considered

- **路徑 B — 沿用 KB SettingsTab pattern,無新 mockup**:重用 `KbTuneGroup`/`KbTuneKnob`/`ConfigTestPanel`
  喺 doc-detail 加 config 區。較快,但「放喺 doc-detail」嘅 placement 無 mockup backing = H7-adjacent。
  reject —— 用戶揀路徑 A(最守 H7,有 mockup backing 先 implement)。
- **獨立 per-doc 配置頁**(`/kb/[id]/docs/[docId]/config`):reject —— doc-detail 已係文件 context 中心,
  tab 比另開頁更貼 vision「喺文件上操作配置」。
- **暴露全部旋鈕(含檢索入口)per-doc**:reject —— per ADR-0050 檢索入口旋鈕維持 per-KB(雞同蛋),UI 暴露
  會誤導(set 咗都唔生效)。

## Consequences

- **Positive**:per-doc 配置可喺 UI 操作(完成 vision UI 層);視覺 design-system consistent(reuse KB
  tuning pattern);H7-faithful(mockup backing 先 build);消費 W57 已 merge API,零後端改動。
- **Negative**:doc-detail 頁由單 view 變 tabbed(layout 改動,mockup + ADR backing 緩解);tuning 元件需
  抽出共用(KB + doc;限抽出 refactor,既有 KB test 守不回歸)。
- **Neutral**:檢索入口旋鈕仍 KB-level(future per-doc 檢索 = 另一 ADR);per-doc config-test 共用 KB 試跑
  harness 視覺。

## References

- ADR-0050(W57 per-doc config backend;本 ADR = 其 UI 實現)
- 平台藍圖:`docs/02-architecture/per-document-config-platform-design.md` §3.1 Layer A + §7 P2b
- Mockup(擴展對象):`references/design-mockups/ekp-page-doc-detail.jsx`
- Mockup pattern source:`references/design-mockups/ekp-page-kb.jsx` `TabKbSettings`(L744-1177)
- DESIGN_README design-stage expansion ADR-route precedent(KB Detail 5→8 / Settings v1→6 / `/users`)
- Phase plan:`docs/01-planning/W58-per-doc-config-ui/plan.md`
- 用戶決策:2026-06-09 AskUserQuestion(路徑 A 先擴 mockup over 路徑 B 沿用 pattern)
