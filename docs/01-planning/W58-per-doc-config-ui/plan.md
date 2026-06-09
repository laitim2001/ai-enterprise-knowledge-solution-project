---
phase: W58
name: per-doc-config-ui
status: active        # draft | active | closed
created: 2026-06-09
owner: "Claude (AI) — 技術 Lead Chris 審閱"
gap: "Gap A / P2b (per-document config platform — UI layer)"
adr: ADR-0051
spec_refs:
  - docs/02-architecture/per-document-config-platform-design.md §3.1 (Layer A UI)
  - ADR-0050  # W57 per-doc config backend (本 phase 消費其 CRUD API + config-test doc-scope)
  - references/design-mockups/ekp-page-doc-detail.jsx  # H7 — 擴此 mockup
  - references/design-mockups/ekp-page-kb.jsx          # KB SettingsTab tuning pattern (mirror source)
---

# W58 — Per-Document 配置 UI(P2b)

> **緣起**:W57 / P2a 落地 per-doc 配置後端(`DocConfigStore` + EffectiveConfig per-DOC layer +
> dominant-doc 解析 + CRUD API + config-test doc-scope,已 merged)。本 phase 起 **P2b — UI 層**,
> 完成用戶 vision 嘅「喺 UI 頁面上操作、配置、管理 per-document 配置」。
>
> **H7 前置(用戶 2026-06-09 決策)**:doc-detail mockup(`ekp-page-doc-detail.jsx`)係純唯讀 chunk
> inspector,**完全冇 config 面**。用戶揀**路徑 A —— 先擴 mockup**(最守 H7):先喺 mockup 加 per-doc
> config 面、design 確認,**然後先**砌 frontend。

## 1. 範圍(Scope)

喺 **doc-detail 頁**(`/kb/[id]/docs/[docId]`)加 per-doc 配置 surface,消費 W57 已 merge 嘅:
- CRUD API:`GET/PUT/DELETE /kb/{kb}/docs/{doc}/config` + `GET /kb/{kb}/doc-configs`
- config-test doc-scope:`POST /kb/{kb}/config-test` body `doc_id`

**只暴露 post-retrieval 旋鈕**(per ADR-0050 — `answer_detail` / citation expansion / neighbour images /
max_images / overview_pin);**檢索入口旋鈕**(top_k/rerank/parent_doc)維持 KB-level only,UI 用
explanatory affordance 講明「呢類旋鈕喺 KB 設定」。

**繼承語意**:per-doc 旋鈕 None = **繼承 KB**(再全域)。UI badge 用「繼承 KB」/「已覆寫(此文件)」
(對比 KB SettingsTab 嘅「繼承全域」)。

## 2. 交付物(Deliverables)

| # | 交付 | Component | Gate |
|---|---|---|---|
| **F1** | 擴 `ekp-page-doc-detail.jsx` mockup:tab strip([Chunk inspector] 現有 3-pane + [Per-doc 配置] 新)+ per-doc config 面(忠實 mirror KB tuning pattern,只 post-retrieval 旋鈕,繼承 KB 語意)+ per-doc config-test 面 | mockup | **用戶 review(mockup gate)** |
| **ADR** | ADR-0051 doc-detail per-doc config surface(design-stage expansion,§5.1/§5.7 route)| doc | — |
| **F2** | `frontend/lib/api/doc-config.ts` API client(get/put/delete/list)+ config-test `doc_id` 透傳 | C10 | **gated on F1 approve** |
| **F3** | 砌 doc-detail config tab(`frontend/app/(app)/kb/[id]/docs/[docId]/page.tsx`)100% match approved mockup;抽出/重用 tuning 元件 | C09/C10 | **gated on F1 approve** |
| **F4** | Frontend test(Vitest + RTL)+ §12 H7 fidelity self-check(逐元素對齊 approved mockup)| test | **gated on F3** |

## 3. Acceptance Criteria

- **AC1**(F1 mockup):doc-detail mockup 加 per-doc config tab,視覺忠於既有 design system(reuse
  `.seg` / `KbTuneGroup`-style toggle-group / `.field`/`.input`/`.hint` / config-test result card);只列
  post-retrieval 旋鈕;繼承 KB / 已覆寫 badge;scope 註明「per-query > per-DOC(此文件)> per-KB > 全域 ·
  ADR-0050」。
- **AC2**(H7):F3 frontend **逐元素 100% match** F1 approved mockup(layout / spacing / typography /
  color tokens / interaction states / responsive / a11y)— 唔對齊即 STOP+ask 或 🚧 deferred + reason。
- **AC3**(消費 W57 API):UI get/put/delete per-doc config + scoped config-test 全部行 W57 endpoint;
  無新 backend 改動(若發現需要 = STOP,可能要 W57 後續)。
- **AC4**(繼承語意):per-doc 旋鈕留空 = 繼承 KB;UI 正確顯示繼承來源 + 「還原至 KB」affordance。
- **AC5**(H1/H4):純前端 + 既有 API;無架構改動;無 Tier 2 滲入。
- **AC6**(test):F3 frontend component test;F4 fidelity self-check pass。

## 4. 風險

- **R1 🟡 H7 fidelity**:mockup 擴展係新設計,F3 必須逐元素對齊。緩解:F1 用既有 design-system primitive
  (唔發明新視覺);F1 user-review gate 鎖視覺;F3 self-check per §12。
- **R2 🟡 tuning 元件未抽出**:`KbTuneGroup`/`KbTuneKnob`/`ConfigTestPanel` inline 喺 `kb/[id]/page.tsx`,
  非共用元件。F3 需抽出做共用(KB + doc 共用)或謹慎複製。傾向**抽出共用**(DRY,但屬 refactor — 限抽出,
  唔改 KB 行為,既有 KB test 全綠守)。
- **R3 🟡 doc-detail 頁加 tab = layout 改動**:現有頁無 tab。加 tab strip 改頁面結構(H7 — 屬 design-stage
  expansion,F1 mockup + ADR-0051 backing)。
- **R4 🟢 production-preserve**:per-doc 旋鈕全空 = 行為同 W57(後端 doc_config 空 → 繼承 KB)。

## 5. 非目標(Non-goals)

- ❌ 後端改動(W57 已足;F3 純消費 API)。
- ❌ 檢索入口旋鈕 per-doc UI(top_k/rerank/parent_doc 維持 KB-level,per ADR-0050)。
- ❌ Gap B query 意圖 gate。
- ❌ 一次過砌 frontend —— F2-F4 **gated on F1 mockup user-review**(守 H7,唔 approximate)。

## 6. ADR 觸發(H1 + H7)

doc-detail 頁加 config tab = view layout design-stage expansion(§5.1 H1「8-view layout philosophy」+
§5.7 H7 mockup 缺口)→ **ADR-0051**(Proposed;mockup review 後 Accepted)。對齊 DESIGN_README 標明嘅
design-stage expansion ADR-route precedent(KB Detail 5→8 tabs / Settings v1→6 tabs / `/users`)。

## 7. Changelog

| Date | Change | Reason |
|---|---|---|
| 2026-06-09 | Initial plan(P2b UI;路徑 A 先擴 mockup;F2-F4 gated on F1 review)| W57 後端完成 + 用戶揀 kickoff P2b + 路徑 A |
| 2026-06-09 | **Deviation R2**:F3 建 self-contained `doc-config-tab.tsx` 而非抽 KB 頁 tuning 元件 | §1.3 唔掂 3174 行 KB 頁(零回歸)+ mockup 本身分開 Doc*/Kb* helpers + 「繼承 KB」vs「繼承全域」framing 不同 |
| 2026-06-09 | **Config-test 機制**:用 `draft_config` 預覽(proposed-doc vs 繼承 KB A/B)而非 mockup 暗示嘅 `doc_id` scope;`answer_detail` 不在試跑預覽(經儲存 real-query 生效)| 免 W58 backend 改動(plan non-goal)+ 預覽未存編輯更貼 vision loop;mockup 2 句文字已對齊 frontend |
