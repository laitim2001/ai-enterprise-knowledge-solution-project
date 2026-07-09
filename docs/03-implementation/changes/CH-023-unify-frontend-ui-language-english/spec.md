---
id: CH-023
title: 統一前端 UI 顯示語言為英文 — 止血 7 個中文洩漏組件（雙語 i18n 前的第一步）
class: Change
status: done              # 2026-07-09 用戶 approve + 落地（7 檔止血 · tsc + eslint clean）
created: 2026-07-09
author: sweep 審計（general-purpose agent，2026-07-09）→ 用戶「兩步走」拍板 Step 1
related:
  - Step 2 = 雙語 i18n ADR（待本 CH approve/落地後 draft，交 Chris approve；H1/H2/H4）
  - architecture.md §11（Multi-language = Tier 2 out-of-scope，H4）
  - CLAUDE.md §5.7 H7（design fidelity — 本 CH 屬「reverse drift」修正，非 H7 trigger）
  - ADR-0056 / W72-W99（per-KB config track — 洩漏 95% 集中處）
---

# CH-023 — 統一前端 UI 顯示語言為英文（止血）

## 1. Context / 問題

用戶 2026-07-09 在頁面測試發現「en/zh 版本語言跳動」。sweep 審計（62 檔）確認：

- **本項目前端無 i18n / locale / 翻譯層**（無 `next-intl` / `react-i18next` / dictionary / `t()`）。`app/layout.tsx` 設 `<html lang="en">`，UI 官方語言為英文，mockup（`references/design-mockups/`）亦為英文。
- 真因 = **UI 語言不一致的 code 洩漏**：後期新增組件（ADR-0056 per-KB config / W72 profiler track）的 UI 顯示字串**直接用繁體中文寫死**，而 core flow 55 檔全英文 → 同一 app 語言跳動。
- 「中文版有英文字」= 中文組件裡混雜的 RAG 領域術語（`faithfulness` / `DRAFT` / `img_density` 等）；統一英文後自然消失。可能疊加瀏覽器翻譯造成的觀感。

用戶最終目標是 **en/zh 雙語切換**，但那是 architecture.md §11 的 Multi-language = **Tier 2 out-of-scope（H4）**，需 ADR + Chris approve + phase plan。用戶採「兩步走」：**本 CH = Step 1 先在 Tier 1 內止血；Step 2 另立 ADR 評估雙語。**

## 2. Decision / 範圍

把以下 **7 個組件的 UI 顯示字串（B 類）由繁體中文改為英文**，統一全站 UI 語言。**只改使用者看得見的文字，不改任何邏輯 / 資料 / class / layout。**

| # | 檔案 | UI 中文洩漏處（估） | 型態 |
|---|---|---|---|
| 1 | `app/(app)/kb/[id]/docs/[docId]/doc-config-tab.tsx` | ~80 | 近乎整個 tab 全中文（toast / JSX / label / 空狀態） |
| 2 | `app/(app)/kb/[id]/page.tsx` | ~65 | Settings/Tuning 段全中文（knob title / metric label / 按鈕 / 空狀態） |
| 3 | `components/settings/settings-doc-profiling.tsx` | ~50 | 整個 tab 全中文（banner / 表頭 / Dialog / toast） |
| 4 | `app/(app)/kb/[id]/upload/page.tsx` | ~9 | scan-confirm banner + profiler 說明 + 狀態徽章 |
| 5 | `app/(app)/kb/new/page.tsx` | 3 | image-recall preset 卡（title / desc / badge） |
| 6 | `app/(app)/settings/page.tsx` | 2 | 1 個 tab label（`文件分類規則`）+ TabBoundary 名 |
| 7 | `app/(app)/kb/[id]/docs/[docId]/page.tsx` | 1 | 1 個 tab label（`Per-doc 配置`） |

**估計總量 ~210 條 UI 字串**（中型工程，約 1–2 日）。

**中文註解（A 類）保留不動** — 本項目慣用中文 comment，不影響 UI，改動它們違反 Karpathy §1.3 surgical（超出止血範圍）。

## 3. H7 design fidelity 對齊策略

本 CH 是把 implementation **更貼近** `<html lang="en">` + mockup 的方向（reverse drift），**非** §5.7 H7 trigger。但實作英文用詞仍受 H7 約束：

- **有 mockup 對應的字串** → 英文用詞以 mockup 原文為準（如 `ekp-page-doc-detail.jsx` / `ekp-page-kb-detail.jsx` settings tab / `ekp-page-settings.jsx` 若有對應 UI）。
- **post-date mockup 的字串**（comment 明載 section 錨定等功能 mockup 之後才加，無對應）→ 自擬簡潔英文；RAG technical term（`img_density` / `faithfulness` / `nearest` / `completeness proxy` 等）保留原文。
- **實作階段若遇 mockup 詮釋不清 / 無對應且英文用詞不確定 → 按 §5.7 H7 STOP+ask**，不自行 approximate 視覺，但文字翻譯本身可提 proposed 用詞待確認。

## 4. 明確不做（YAGNI / 範圍控制）

- **不建 i18n 機制**（無 dictionary / locale state / `t()`）— 那是 Step 2 ADR 的事（H4）。本 CH 只把中文 hardcode 換成英文 hardcode。
- **不改邏輯 / API / schema / class / layout / 資料流** — 純文字替換。
- **不動中文註解（A 類）**。
- **不碰 core flow 55 個已全英檔**（無洩漏）。
- **不譯 core flow 成中文**（那是被否決的反方向）。

## 5. 驗收準則

1. 7 檔的 UI 顯示字串（JSX text / toast / label / placeholder / aria-label / title / button / tab / 表頭 / 空狀態）**全部英文**；grep `[一-鿿]` 命中僅剩註解行（A 類），UI string 位置 0 命中。
2. 對應 view 在瀏覽器視覺 fidelity 對齊 mockup（有 mockup 者）；layout / spacing / class 零改動。
3. `tsc` + `eslint` clean；相關 Vitest（若有）不因文字改動而 fail。
4. 功能行為完全不變（只改顯示文字）。
5. 用戶在頁面走查確認語言不再跳動（全英文一致）。

## 6. 與 Step 2（雙語 i18n ADR）的關係

止血統一英文 **正是 i18n externalize 的第一步**：先把全站 source language 統一為英文，Step 2 建 i18n 時只需把英文 hardcode 抽成 `en` dictionary + 補 `zh` dictionary，中文以 `zh` locale 正式回來。故本 CH 不是白做，是雙語的地基。

## 7. Changelog

- 2026-07-09 — spec draft（proposed）建立，等用戶 approve。
- 2026-07-09 — 用戶 approve → 落地。7 檔止血(4 小檔手改 + 3 大檔 subagent 平行,共 ~210 UI string 中文→英文);修 JSX 引號轉義(`react/no-unescaped-entities` 9 處);`tsc --noEmit` + `next lint` clean;grep 全 7 檔 UI string 0 中文殘留(剩全註解 A 類)。status → done。
