# W103 — Multi-language(en/zh)i18n(UI chrome 雙語)

> **狀態**:**`active` — 2026-07-14 用戶 approve(D-2 locale 機制留 F3 前拍板;F1 amendment 不受影響先行)**
> **分類**:新功能 / Tier 邊界 promote(phase 級,跨前端 + i18n 基建 + 文件/架構 amendment + 翻譯 + 測試)
> **方向**:ADR-0075 **Accepted**(2026-07-14 — Stakeholder scope + Chris 架構雙 approve;driver = 內部 + 外部 APAC both,per decision-form Q23 Resolved)
> **Owner**:Chris(架構決策 H1/H2 + Tier 邊界 H4)
> **關聯**:ADR-0075 · decision-form Q23 · CH-023(externalize 地基,done)· ADR-0017(R8 corp-proxy dependency-add)· ADR-0014(disabled-affordance Language toggle)· BACKLOG B-25

---

## §1 Scope + 目標

把 **Multi-language(en/zh)UI chrome 雙語**由 Tier 2 promote 落 Tier 1 實作:建 i18n 機制,全站 UI chrome string externalize → `en` + `zh` dictionary,啟用 mockup 預留嘅 disabled Language toggle。

**目標(成功定義)**:使用者可喺 UI 切換 en / zh,全站 chrome(label / button / nav / toast / placeholder / aria-label / 表頭 / 空狀態 / tab 名)雙語顯示;切換持久化;zh 態逐 view 對齊 mockup layout(H7);RAG technical term 保留英文定譯。

**Scope 劃線**(承 ADR-0075,關鍵防 scope creep):
- ✅ **UI chrome 雙語**(介面文字)。
- ❌ **NOT RAG 答案 / 文件 content 翻譯** —— 嗰個係 multi-language **retrieval**(architecture.md §11 另一條 Tier 2)。答案 / 引用 / 圖 caption 維持原文檔語言。
- 範圍限 **en / zh**;JP 架構預留 locale 但**唔實作**。

---

## §2 Deliverables

| # | Deliverable | 層 |
|---|---|---|
| **F1(首)** | **Tier 邊界 amendment** —— architecture.md §11 把 `Multi-language(en/zh)` 移出 Tier 2 list(§1-§14 content-lock,version bump + 謹慎)+ CLAUDE.md §5.4 H4 list 同步移除 en/zh(JP retrieval / content 翻譯**留 Tier 2**)。**promote 已 approve 先可動** | 文件 / 架構 |
| **F2** | `next-intl` 裝機 + **R8 corp-proxy 驗證**(ADR-0017 dependency-add 紀律)—— 裝唔到 → **STOP + fallback 議**(唔硬闖) | 基建(H2) |
| **F3** | i18n 機制搭建 —— `next-intl` config + provider + locale 機制(見 §4 D-2)+ `app/layout.tsx` `lang` 動態化 + **CJK font fallback**(`next/font` 現只 latin subset) | 前端基建(H1) |
| **F4** | `en` dictionary externalize —— 全站 chrome string 抽 `t()` + `en` messages(**範圍 = 全站 chrome,唔止 CH-023 嗰 7 檔**;core flow 55 檔英文 hardcode 一併抽) | 前端 |
| **F5** | `zh` dictionary —— **我 draft 繁中初稿 → 用戶校對**(2026-07-14 拍板 (a));RAG technical term 保留英文定譯(glossary) | 前端 / 翻譯 |
| **F6** | 啟用 mockup disabled Language toggle(disabled → enabled)+ 切換持久化(cookie / localStorage) | 前端(H7 + ADR-0014) |
| **F7** | **H7 design sub-gate** —— en + zh 兩態逐 view 對齊 mockup;zh 文字長度對 layout 影響走查 + Vitest;ruff(若碰 backend)/ tsc / eslint / build clean | 測試 / H7 |
| **F8** | 文件同步 —— ADR-0075 impl note + user-guide language 章節(optional)+ dict 維護規則(en/zh sync 紀律,類比 DESIGN_SYSTEM.md §7)+ BACKLOG B-25 → `完成` + closeout retro | 文件 |

---

## §3 Acceptance Criteria(Gate G-W103)

- [ ] **AC1**:全站 chrome string externalize;`en` locale 顯示同 CH-023 後現狀**零視覺回歸**(逐 view 對齊)。
- [ ] **AC2**:切換 `zh` → 全 chrome 顯示繁中,**RAG technical term 保留英文定譯**;grep 無 en chrome 殘留(externalize 漏網為 fail)。
- [ ] **AC3**:Language toggle enabled + 切換**持久化**(reload / 重進保持選擇)。
- [ ] **AC4**:locale 機制 **SSR-safe**(無 hydration mismatch;`suppressHydrationWarning` 已在 `layout.tsx`)。
- [ ] **AC5**:**H7** —— en + zh 兩態逐 view 對齊 mockup;zh 文字長度**無撐爆 layout**(逐 view 走查,唔啱 → STOP+ask per §5.7 或 🚧 defer + reason)。
- [ ] **AC6**:全 Vitest 綠 + tsc / eslint / build clean(碰 backend 則 ruff / mypy strict clean)。
- [ ] **AC7**:**Tier 邊界 amendment 完成**(architecture.md §11 + CLAUDE.md §5.4 H4 移除 en/zh)+ ADR-0075 impl note。
- [ ] **AC8**:`next-intl` R8 corp-proxy 裝機驗證通過(ADR-0017);裝唔到已 surface + 有 fallback 決定。

---

## §4 設計決定(implementation 前 lock — 待 review 拍板)

- **D-1 i18n library = `next-intl`**(ADR-0075 傾向;App Router 原生 + SSR-friendly + TS-first + ICU)。phase 內 F2 最終確認 App Router 整合。
- **D-2(關鍵)locale 機制** —— **兩條路要 Chris 拍板**:
  - **(甲)cookie / header negotiation(URL 不變)** —— `next-intl` "without i18n routing";**傾向此路**:對齊 W18 已做嘅 flat URL(唔想 `/[locale]/` 重構全站 route)+ 改動面細。
  - **(乙)`/[locale]/` URL routing** —— `next-intl` 官方主推;需 `app/[locale]/` 包所有 route(全 route 重構)+ 影響所有 URL / bookmark / API proxy path。
  - **裁決留 plan review**;傾向 (甲) 以最小架構擾動。
- **D-3 externalize 範圍** —— chrome only(label / button / nav / toast / placeholder / aria-label / 表頭 / 空狀態 / tab);答案 / 引用 / 圖 caption / RAG technical term 保留原文。
- **D-4 zh 翻譯來源** —— **Claude draft 初稿 + 用戶校對**(2026-07-14 拍板 (a));technical term glossary(`faithfulness` / `img_density` / `nearest` / `completeness` 等)保留英文定譯。
- **D-5 font** —— zh CJK font fallback(`Inter` / `JetBrains Mono` latin subset 唔含 CJK 字形)—— 加 CJK web font 或系統 fallback stack,屬 H7 考量(字形影響 layout)。

---

## §5 Out of Scope(明確唔做)

- **RAG 答案 / 文件 content 翻譯**(multi-language retrieval,另一 Tier 2,H4)。
- **JP locale**(架構預留 locale,唔實作)。
- 多 locale lazy-split / 動態載入(YAGNI —— en + zh 兩個 static dict 足夠)。
- 瀏覽器機器翻譯整合(ADR-0075 REJECTED — 質量不可控 + technical term 亂譯)。

---

## §6 H-constraint / ADR 影響

- **H4**:promote **已 approve**(ADR-0075 雙 approve);F1 amendment 正式移邊界(en/zh 出 Tier 2;JP / content 翻譯留 Tier 2)。
- **H1**:i18n machinery + locale 機制 = 架構改動,喺 **ADR-0075 框架內**(已 Accepted;D-2 locale 機制裁決記 progress + 如涉重大偏離補 ADR)。
- **H2**:`next-intl` 新 dependency —— ADR-0075 已記錄;**F2 必須先 R8 corp-proxy 驗證**(ADR-0017),裝唔到唔硬闖。
- **H7**:**F7 逐 view 雙態對齊 mockup**(en 零回歸 + zh 唔撐爆 layout)—— design sub-gate。
- **H5**:N/A(無 secret / PII)。
- **H6**:前端為主(test nice-to-have),但 **H7 gate 要 Vitest 覆蓋切換態 + 關鍵 view**。

---

## §7 Risks

| Risk | 緩解 |
|---|---|
| `next-intl` R8 corp-proxy 裝唔到(Ricoh MITM) | **F2 首驗**;裝唔到 → STOP + fallback(改 library / 延後);memory `project_document_skills_toolchain` 有 proxy 繞法參考 |
| locale routing 全 route 重構風險(D-2 乙) | 傾向 D-2 (甲) cookie-based 避免;若選 (乙) 需獨立評估 route / API proxy 影響 |
| zh 文字長度撐爆 mockup layout(H7) | F7 逐 view 走查;撐爆 → STOP+ask(縮字 / 調 layout 需 mockup 對齊)/ 🚧 defer + reason |
| externalize 漏字串(動態拼接 / template literal grep 唔到) | AC1/AC2 grep + 逐 view 走查雙驗;分批 tick 每 view 確認 |
| en/zh dict drift(新 UI string 要雙語同步) | F8 立維護規則(類比 DESIGN_SYSTEM.md §7 sync 紀律);closeout 記入 |
| SSR hydration mismatch(locale 初值) | AC4 專驗;`suppressHydrationWarning` 已在 layout;cookie 初值 server 讀 |
| 工程量大(~1 個月,全站 chrome) | F4 分批 tick(逐 view / cluster);gate 要求全站覆蓋,但可增量推進 |

---

## §8 Changelog

- 2026-07-14:plan 建立(`proposed`)—— ADR-0075 Accepted 後 kickoff;翻譯來源 = Claude draft 初稿 + 用戶校對(拍板 (a));**等 approve 先 implement**。
- 2026-07-14:用戶 approve → phase `active`;建 checklist + progress kickoff。**D-2 locale 機制(甲 cookie / 乙 `/[locale]/` routing)留 F3 前 Chris 拍板**(F1 amendment 不受影響,先行)。
- 2026-07-14:F1 Tier 邊界 amendment 落地(採 inline-tagged + doc-version-held,非「version bump」— R3 deviation)。F2 next-intl 4.13.2 裝機(R8 通過)。
- 2026-07-14:**D-2 拍板 = 甲 cookie-based**(用戶 AskUserQuestion;next-intl without i18n routing,URL 不變)。F3 機制搭建完成。**F3.4 CJK font fallback deviation(R3):defer → F7**(觸 design token 4-layer sync + H7 fidelity)。**Build 環境**:frontend `next build` 需 `NODE_TLS_REJECT_UNAUTHORIZED=0` 繞 Ricoh MITM(Google Fonts fetch)— pre-existing infra 議題,非 i18n。

---

> **下一步**:用戶 review 本 plan → approve(或調 scope / D-2 locale 機制拍板)→ 我建 `checklist.md` + `progress.md` + kickoff → **F1 先做 Tier 邊界 amendment**(謹慎動 architecture.md §11 content-lock)→ 逐 F implement。**未 approve 前唔 code。**
