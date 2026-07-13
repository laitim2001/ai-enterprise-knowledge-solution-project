# ADR-0075: Multi-language(en/zh)i18n — Tier 2 → Tier 1 Promote(評估)

**Date**: 2026-07-13
**Status**: Proposed
**Approver**: Chris(技術 Lead)— 架構(H1/H2);**+ Stakeholder**(scope/business via `decision-form.md`)— Tier 邊界(H4)

> **本 ADR 係 promote 評估,唔係已定案。** Multi-language 原為 Tier 2(architecture.md §11);把佢 promote 入 Tier 1 同時觸 **H4**(Tier 邊界)+ **H1**(i18n 架構)+ **H2**(新 dependency)。依 CLAUDE.md §5.4 H4,任何 Tier 2 feature 落 Tier 1 必須 STOP + ADR + approve。故本文攤開 driver / 方案 / 成本 / gate,**Status 保持 Proposed 直到 Chris(架構)+ Stakeholder(scope,via decision-form)雙 approve 先可實作**。B-25(BACKLOG)對應。

## Context

**Driver**:用戶 2026-07-13 確認有**真實 zh / APAC 需求**(要 zh 介面,非單純根治語言跳動)。此 driver **需 Stakeholder 經 `decision-form.md` 正式記錄**(scope/business decision owner),本 ADR 前置假設其成立。

**現狀(關鍵 — externalize 地基已備)**:
- 專案 UI 官方語言**本來就係英文**(`app/layout.tsx` `<html lang="en">`,mockup `references/design-mockups/` 全英文)。
- mockup 有一個 **present-but-disabled Language toggle**(coming-soon control,ADR-0014 disabled-affordance pattern;architecture.md §11 line 863)。
- **CH-023(2026-07-09,done)** 已把 7 個中文洩漏組件(ADR-0056 per-KB config / W72 profiler track)止血、統一英文 → 全站 source language = 英文 hardcode。**呢個正正係 i18n externalize 嘅第一步**(CH-023 §6):Step 2 只需把英文 hardcode 抽做 `en` dictionary + 補 `zh`。
- 專案**刻意冇起 i18n machinery**(無 `next-intl` / `react-i18next` / dictionary / `t()`;architecture.md §11 + CLAUDE.md §5.4 H4)。

**Tier 2 定性**:architecture.md §11 明列 `Multi-language(JP/ZH)`= Tier 2,promote trigger = **「業務側擴 APAC」**,工作量估 **1 個月**。

**三重 constraint**:H4(Tier 邊界移動)+ H1(全站 i18n 架構 + routing)+ H2(新 i18n dependency)。

## Decision(proposed — 等 approve)

Promote **Multi-language(en/zh)** 入 Tier 1,建 i18n 機制:

1. **i18n library**:`next-intl`(App Router 原生 + SSR-friendly + TS-first)。屬 H2 新 dependency。
2. **Dictionary**:`en`(由現有英文 hardcode 抽取,CH-023 地基)+ `zh`(繁中翻譯,**來源待定 — 見 Consequences**)。
3. **Locale 機制**:`next-intl` URL-based(`/[locale]/…` routing)或 cookie/header negotiation(方案細節留 phase plan)。屬 H1 routing/架構改動。
4. **全站 UI string externalize** → `t()` calls(chrome 層:label / button / nav / toast / placeholder / aria-label / 表頭 / 空狀態)。
5. **啟用 mockup 嘅 disabled Language toggle**(disabled → enabled)。屬 mockup 已預留嘅 coming-soon 實現(H7:啟用 + zh 文字長度對 layout 影響需 fidelity 驗證)。

**Scope 劃線(關鍵 — 防 scope creep)**:
- ✅ **UI chrome 雙語**(介面文字)。
- ❌ **NOT RAG answer / 文件 content 翻譯** —— 嗰個係 multi-language **retrieval**(architecture.md §11 另一條 Tier 2),唔喺本 ADR 範圍。答案 / 引用 / 圖 caption 維持原文檔語言。
- **範圍限 en / zh**;JP 暫不做(架構預留 locale,未來可加)。

## Alternatives Considered

- **不 promote(維持 Tier 2)** —— 若 APAC driver 未經 Stakeholder 正式確立 / 唔 sustained。CH-023 已解決「語言跳動」痛點,單為偏好唔值 Tier 2 成本。
- **i18n library 選型**:
  - `next-intl`(**proposed**)— App Router 原生 integration、TS-first、message 格式標準(ICU)。
  - `react-i18next` / `next-i18next` — 更通用 + 生態大,但 App Router(RSC)整合較手動、SSR 需額外 wiring。
  - **裁決留 phase plan**,但傾向 `next-intl`(App Router 對齊 §3.2 App Router-only)。
- **Browser 翻譯(Google Translate 等)** — REJECTED:質量不可控 + RAG technical term(`faithfulness` / `img_density` 等)會被亂譯 + 無 layout 控制。
- **只做 en(維持現狀)** — 即 driver 不成立時嘅 fallback。

## Consequences

- **Positive**:
  - APAC / zh 使用者可用性(driver 直接滿足)。
  - 全站 string externalize 改善可維護性(集中管理文案)。
  - 實現 mockup 已預留嘅 Language toggle。
  - CH-023 地基令 `en` dictionary 抽取低成本(唔使先統一語言)。
- **Negative / 成本**:
  - **H4 邊界移動** —— Tier 1 納入原 Tier 2 feature,**需 Stakeholder 經 decision-form 正式批**(唔係純技術決定)。
  - **H1 架構** —— i18n machinery + locale routing 改動,影響全站 route / layout。
  - **H2 新 dependency** —— `next-intl`(需確認 R8 corp-proxy 可裝,per ADR-0017 dependency-add discipline)。
  - **工作量 ~1 個月**(architecture.md §11 估):全站 string externalize + zh 翻譯 + locale routing + toggle + test + H7 fidelity 驗證。屬 multi-day phase,需 §10 phase plan。
  - **zh 翻譯來源 + 持續維護成本(最大隱憂)**:邊個提供 zh 翻譯(內部 / 專業譯者 / MT + 人手校)?RAG technical term 保留英文定譯?**每次新 UI string 要雙語同步維護**(drift 風險,類比 design token 4-layer drift — 需似 DESIGN_SYSTEM.md §7 嘅 sync 紀律)。
  - **H7 fidelity**:zh 文字長度 / 換行同 en 唔同,可能撐爆 mockup layout;啟用 toggle + 切換態需逐 view 對齊 mockup。
  - **scope creep 風險**:要嚴守「chrome 雙語 ≠ content 翻譯」界線,否則滑向 multi-language retrieval(另一 Tier 2)。
- **Neutral**:
  - JP 暫不做,locale 架構預留。
  - 若 approve,後續 multi-day phase(§10 plan)+ H7 design sub-gate(切換態 / zh layout mockup 對齊)。

## References

- architecture.md §11(Multi-language Tier 2 trigger matrix — 「業務側擴 APAC」/ 1 個月 / line 863 disabled toggle)
- CLAUDE.md §5.4 H4(Tier 邊界)+ §5.1 H1(架構)+ §5.2 H2(dependency)+ §5.7 H7(design fidelity)
- CH-023(`docs/03-implementation/changes/CH-023-…/spec.md` §6 — externalize 地基 / 兩步走 Step 2)
- ADR-0014(disabled-affordance coming-soon pattern — Language toggle)
- ADR-0017(R8 corp-proxy dependency-add discipline — `next-intl` 裝機驗證)
- `decision-form.md`(Stakeholder scope approval — APAC driver 正式記錄,**待補**)
- BACKLOG B-25

## Approval Gate(明確)

| 決定者 | 範圍 | 狀態 |
|---|---|---|
| **Stakeholder**(via decision-form) | H4 Tier 邊界移動 + APAC business driver | ⏳ 待 |
| **Chris**(技術 Lead) | H1 i18n 架構 + H2 `next-intl` dependency | ⏳ 待 |

**雙 approve 前 Status 保持 Proposed,不得實作 code。** approve 後 → 建 multi-day phase plan(§10 R1)+ H7 design sub-gate。
