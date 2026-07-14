# W103 — Progress(i18n en/zh UI chrome 雙語)

> Daily progress + decisions + commits + 結尾 retro。對應 `plan.md` + `checklist.md`。

## Day 1(2026-07-14)— Kickoff

**Context**:ADR-0075 Accepted(2026-07-14 雙 approve)後開 W103 phase。承 CH-023 externalize 地基(7 檔中文洩漏止血 → 全站 source language 英文 hardcode)。翻譯來源 = Claude draft 初稿 + 用戶校對(拍板 (a))。

**已做**:
- plan.md draft → 用戶 approve → 狀態 `proposed` → `active`。
- 建 checklist.md(8 F 展開)+ progress.md kickoff。
- **F1 Tier 邊界 amendment 完成**(F1.1-F1.5 tick):architecture.md §2.2 + §5.0 + §11.1 + line 8 + CLAUDE.md §5.4 H4 —— en/zh UI chrome i18n 由 Tier 2 移出 → Tier 1;JP UI + content/RAG 翻譯留 Tier 2。ADR-0075 加 §Implementation Notes。用戶 2026-07-14 確認 diff OK。
- **F2 next-intl 裝機完成**(F2.1-F2.4 tick):R8 corp-proxy 探測通過(registry 可達,Ricoh MITM 未阻 npmjs — `pnpm view` / `add` 皆成功);next-intl **4.13.2** 裝入 frontend(peerDeps `next ^14` + `react ^18` 完全相容,無需降 v3);package.json `^4.13.2` + pnpm-lock 更新;**tsc baseline clean**(裝包無破壞 build)。
- **F3 i18n 機制搭建完成**(F3.1-F3.3 + F3.5;F3.4 🚧→F7):D-2 拍板 **甲 cookie-based**(next-intl without i18n routing,URL 不變);建 `i18n/request.ts`(cookie `NEXT_LOCALE`)+ next.config plugin + layout async `<html lang={locale}>` + `<NextIntlClientProvider>` + messages/en.json+zh.json 骨架;**tsc clean + build 成功 17 routes SSR**(繞 font MITM cert 後)。
- **F4 批 1a 完成**(F4.1 + F4.2 app-shell + F6 臨時通):增量策略先做 pattern + AppShell 核心 chrome。messages 加 Nav/Breadcrumb/Shell/TopBar namespace(en 完整 + zh **draft 初稿待校對**);app-shell.tsx externalize(nav labels/section/breadcrumb/topbar aria+search/brand/workspace/footer,用 `useTranslations` client + `t.has()` breadcrumb guard);**LanguageToggle 臨時通線**(`language-toggle.tsx`:Globe 點擊 en↔zh + cookie + router.refresh,替換原 DisabledAffordance disabled Globe)。**tsc + eslint + build 17 routes SSR 全 clean**。**Labs Tier 2 items 暫不 externalize**(技術名 + "Multi-Language" reason F1 後 stale,連 F6 釐清)。
- **F4 批 1b 完成**(F4.2 dashboard):`dashboard/page.tsx` 全 chrome 抽 `t()`(page header / 4 stat / KB summary + table / recent queries / latest eval / system health / quick actions / relative time,ICU param);加 Dashboard namespace(en 完整 + zh draft);**RAGAs metrics + vendor 元件名 + status badge word(READY/OK/DEGRADED)+ technical identifier(cohere-v4.0-pro/ADR/BM25)保留英文**。tsc + build 17 routes SSR clean。**批 1(app-shell + dashboard)完成 — pattern 驗證可複製**。
- **測試環境 browser 驗證(2026-07-14)**:frontend dev(port 3002 + `NEXT_PUBLIC_AUTH_MOCK=true` mock 登入,**唔使 backend**;`NODE_TLS_REJECT_UNAUTHORIZED=0` 繞 font MITM)+ Claude-in-Chrome 真實 toggle flow —— dashboard + nav **en↔zh 切換成功**(`html lang` 隨 `NEXT_LOCALE` cookie 切;技術詞/vendor/RAGAs metric 正確保留英文;**layout 冇爆**)。順帶實證 Labs「Multi-Language」item F1 後 stale(留 F6)+ theme-toggle/notifications-menu/user-menu 3 組件 aria 未 externalize(待補)。
- **F4 批 2 完成**(F4.2 kb-list):`app/(app)/kb/page.tsx` externalize(頁首/subtitle/seg grid-table/export/new KB/filter placeholder/status-cycle/tag/count meta/loading/KbCard/KbTable headers+row actions/KbEmpty/relative time,ICU param);加 KbList namespace(en + zh draft);**Azure AI Search/ADR-0018/R@5/MB/status badge(READY/EMPTY/ARCHIVED)/chunk strategy value 保留英文**。tsc clean + dev HMR 編譯成功。
- **F4 批 3 完成**(F4.2 topbar 3 組件):externalize `theme-toggle.tsx`(toggle theme / switch light-dark aria+title)+ `notifications-menu.tsx`(header/unread count/mark all read/empty/footer/trigger aria — **mock 通知 sample content 保留英文**)+ `user-menu.tsx`(signing in/open menu/profile/settings/API keys/identity/sign out — **MSAL · httpOnly cookie · 7d TTL + [mock] 保留英文**);加 ThemeToggle/Notifications/UserMenu namespace(en + zh draft)。tsc + eslint clean。**shell chrome 全站每頁可見部分 externalize 完成**。

**Decision / deviation(R3)**:
- **F1.2 採 inline-tagged + doc-version-held convention,非 plan 原寫「version bump」** —— 對齊 architecture.md 既有 amendment 慣例(§3.4 ADR-0023 / §3.7 ADR-0022 / §5 ADR-0024),更接近既有 pattern(§13);doc version held v6,唔 bump v7。architecture.md line 17 歷史 note 保留(審計軌跡)。
- Language toggle 實際 disabled→enabled = F6,非 F1(F1 只確立文件層 Tier 邊界,頁面暫未有雙語切換功能)。
- **D-2 locale 機制拍板 = 甲 cookie-based**(2026-07-14 用戶 AskUserQuestion)—— next-intl「without i18n routing」,locale 存 `NEXT_LOCALE` cookie,URL 不變(對齊 W18 flat URL);route 零搬遷。副作用:所有 route 因 `cookies()` 讀取變 dynamic(SSR on demand)—— 對 EKP authenticated app 無實質影響(本來多數 dynamic)。
- **F3.4 CJK font fallback → 🚧 defer F7**(plan deviation R3):font stack 改動觸 design token 4-layer sync(DESIGN_SYSTEM.md §7)+ H7 fidelity;瀏覽器預設已 fallback 顯示 CJK,明確 CJK font stack 歸 F7 逐 view 走查一齊處理。
- **Build 環境發現(pre-existing,非 W103 引入)**:`next build` 因 `next/font/google` 抓 Google Fonts 撞 Ricoh MITM(`SELF_SIGNED_CERT_IN_CHAIN`)fail;設 `NODE_TLS_REJECT_UNAUTHORIZED=0`(dev-only,同 next.config backend proxy `rejectUnauthorized=false` pattern)繞過後 build 成功。frontend 喺 Ricoh 網絡 build 需此 workaround —— 屬 infra 議題(font import pre-existing,非 i18n),候選記 BACKLOG。

**下一步**:繼續逐 view cluster externalize(kb-detail / chat / settings / integrations / users / login / CH-023 7 檔)+ 3 個 topbar 組件(theme-toggle/notifications-menu/user-menu)+ Labs 釐清(F6)。test env(port 3002)可一路 refresh 睇。

**Commits**:
- `29a0bdd` — W103 kickoff(plan approved + checklist + progress + BACKLOG B-25 進行中)。
- `2096811` — W103 F1 Tier 邊界 amendment(architecture.md §2.2/§5.0/§11.1/line 8 + CLAUDE.md §5.4 H4 + ADR-0075 impl note)。
- `2cc7cdc` — W103 F2 next-intl 4.13.2 裝機(package.json + pnpm-lock)。
- `f9ee7d0` — W103 F3 i18n 機制搭建(next-intl cookie-based,D-2 甲)。
- `ea05b77` — BACKLOG W103 F1-F3 同步 + B-26 font MITM。
- `808c218` — W103 F4 批 1a app-shell externalize + LanguageToggle 臨時通。
- `cbcdae0` — W103 F4 批 1b dashboard externalize。
- `21a875c` — W103 F4 批 1b phase docs 同步。
- `7126b0e` — W103 F4 批 2 kb-list externalize。
- (見下一 commit)W103 F4 批 3 — topbar 3 組件 externalize。
