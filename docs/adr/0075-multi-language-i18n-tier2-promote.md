# ADR-0075: Multi-language(en/zh)i18n — Tier 2 → Tier 1 Promote(評估)

**Date**: 2026-07-13
**Status**: Accepted(2026-07-14 — 用戶 as Stakeholder scope + Chris 架構雙 approve;APAC driver = 內部 + 外部 both,per decision-form Q23 Resolved)
**Approver**: Chris(技術 Lead)— 架構(H1/H2);**+ Stakeholder**(scope/business via `decision-form.md`)— Tier 邊界(H4)

> **本 ADR 係 promote 評估,唔係已定案。** Multi-language 原為 Tier 2(architecture.md §11);把佢 promote 入 Tier 1 同時觸 **H4**(Tier 邊界)+ **H1**(i18n 架構)+ **H2**(新 dependency)。依 CLAUDE.md §5.4 H4,任何 Tier 2 feature 落 Tier 1 必須 STOP + ADR + approve。故本文攤開 driver / 方案 / 成本 / gate。**2026-07-14 → Accepted**(用戶 as Stakeholder scope + Chris 架構雙 approve;APAC driver = 內部 + 外部 both,per decision-form Q23 Resolved)。**下一步 = 開 i18n multi-day phase plan(§10 R1),implement code 前需 plan committed**;architecture.md §11 + CLAUDE.md §5.4 H4 的 Tier 邊界 amendment(Multi-language en/zh 移出 Tier 2)為 phase 首個 deliverable。B-25(BACKLOG)對應。

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
| **Stakeholder**(via decision-form Q23) | H4 Tier 邊界移動 + APAC business driver | ✅ Approved 2026-07-14(driver = 內部 + 外部 both)|
| **Chris**(技術 Lead) | H1 i18n 架構 + H2 `next-intl` dependency | ✅ Approved 2026-07-14 |

**雙 approve 完成(2026-07-14)。** 下一步 → 建 i18n multi-day phase plan(§10 R1)+ H7 design sub-gate;**implement code 前需 phase plan committed**。Tier 邊界 amendment(architecture.md §11 Multi-language 移出 Tier 2 + CLAUDE.md §5.4 H4)為 phase 首個 deliverable。

## Implementation Notes

- **2026-07-14 — W103 kickoff**:i18n multi-day phase plan `docs/01-planning/W103-i18n-en-zh/plan.md` committed(§10 R1 gate 過)+ 用戶 approve → phase `active`。翻譯來源 = Claude draft 初稿 + 用戶校對(decision-form Q23 (a))。
- **2026-07-14 — W103 F1 Tier 邊界 amendment 落地**:採 EKP **inline-tagged + doc-version-held** convention(同 §3.4 ADR-0023 / §3.7 ADR-0022 / §5 ADR-0024,**非** version bump v6→v7)——
  - architecture.md §2.2(Tier 1 Out of Scope)+ §5.0(Language toggle 說明)+ §11.1(Tier 2 Backlog)+ line 8 最後更新註:en/zh UI chrome i18n 由 Tier 2 移出 → Tier 1;**JP UI + content/RAG 翻譯(multi-language retrieval)留 Tier 2**。
  - CLAUDE.md §5.4 H4 list 同步(en/zh 移出;JP + content 翻譯留低)。
  - architecture.md line 17 歷史 amendment note(ADR-0024 W18 描述)**保留不動**(audit trail);當前 Tier 邊界權威以 §2.2 / §5.0 / §11.1 body 為準。
  - Language toggle 實際啟用(disabled→enabled)= W103 F6,非本 amendment。
- **2026-07-21 — W103 主體實作落地(F2–F7 + F5.1/F5.2 + F6)**,關鍵裁決同 spec 對照:
  - **F2 dependency(H2)**:`next-intl` **4.13.2** 落地(R8 corp-proxy 驗證通過,Ricoh MITM 未阻 npmjs;peerDeps 同 Next 14 / React 18 相容,無需降版)。ADR 傾向 `next-intl` 成立。
  - **F3 locale 機制(H1)**:拍板 **cookie-based(D-2 甲)** —— `next-intl` without i18n routing,locale 存 `NEXT_LOCALE` cookie,URL 不變(對齊 W18 flat URL;ADR §Decision 3 兩選項中揀後者)。副作用:全 route 因 `cookies()` 變 dynamic SSR —— 對 authenticated app 無實質影響。
  - **F4 externalize**:全站 UI chrome 21 view / 組件 + 6 shared component + CH-023 7 檔 → **37 namespace / 1588 keys**(en 定稿 + zh Claude draft)。
  - **F5.2 術語治理(§Consequences「zh 翻譯來源 + 維護」隱憂嘅回應)**:`frontend/messages/GLOSSARY.md` 落地(保留英文 / 統一中文 / 分域例外 / 排版規則 / 拍板記錄)+ 批次統一 54 條;RAG technical term 保留英文定譯正式定案(chunk / preset / rerank / pipeline 等)。
  - **F6 toggle(H7)**:mockup 原有完整 `LanguageMenu` PopMenu 設計(`ekp-shell.jsx:104-134`)—— 依 mockup 落地 + 3 處 design-stage 內容修正(zh label「简体中文」→「繁體中文」/ en+zh enabled / 副題 ADR-0024→0075);登入頁接線;Settings select enable。
  - **F7 H7 design sub-gate**:en 零回歸 + zh 零爆版(1440px 九 view 零溢出;390px 溢出 en 態同樣存在且更大 = pre-existing)+ CJK font fallback(styles.css 四層同步,PingFang TC / Microsoft JhengHei / Noto Sans TC 系統字體,唔自 host)+ Vitest i18n 守門 16 條 + `next build` 17 route clean。**§Consequences 預警嘅「zh 撐爆 layout」實測未發生**(中文較短反而更緊湊)。
  - **維護 drift 風險嘅機制回應**(§Consequences 類比 DESIGN_SYSTEM.md §7 嘅預警):`tests/unit/i18n-dictionaries.test.ts` 機器守門(key parity / ICU / rich tag 對稱 / 中文排版)+ GLOSSARY.md 維護規則(W103 F8.2)。
  - **剩餘**:F5.3 zh 全量用戶校對(卡用戶)+ F8.5 closeout retro。scope 劃線守住:零 content / RAG 翻譯滲入,JP 保持 Tier 2(Labs affordance + toggle ja disabled)。
