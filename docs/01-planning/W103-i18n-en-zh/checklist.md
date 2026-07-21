# W103 — Checklist(i18n en/zh UI chrome 雙語)

> 對應 `plan.md` §2 Deliverables + §3 Acceptance Criteria。逐項 tick;🚧 defer 需 reason + target。

## F1 — Tier 邊界 amendment(首)✅
- [x] F1.1 讀 architecture.md 現狀(§2.2 / §5.0 / §11.1 / line 17 四處定位)
- [x] F1.2 architecture.md §2.2 + §5.0 + §11.1 + line 8 把 Multi-language(en/zh)移出 Tier 2(JP + content/RAG 翻譯留 Tier 2)—— **採 inline-tagged + doc-version-held convention,非 version bump**(R3 deviation,對齊 ADR-0022/0023/0024)
- [x] F1.3 CLAUDE.md §5.4 H4 list 同步移除 en/zh(JP / content 翻譯留低)
- [x] F1.4 ADR-0075 §Implementation Notes 記 amendment 落地
- [x] F1.5 surface diff 畀用戶確認(2026-07-14 用戶確認 diff OK)

## F2 — next-intl 裝機 + R8 驗證 ✅
- [x] F2.1 R8 corp-proxy 裝機探測 — registry 可達,`pnpm view` / `add` 無代理攔截(Ricoh MITM 未阻 npmjs)
- [x] F2.2 next-intl 4.13.2 裝入 frontend(peerDeps `next ^14` + `react ^18` 完全相容,無需降 v3)
- [x] F2.3 裝唔到 fallback — N/A(裝成功,無需 fallback)
- [x] F2.4 版本鎖定 package.json(`next-intl: ^4.13.2`)+ pnpm-lock.yaml + tsc baseline clean

## F3 — i18n 機制搭建 ✅
- [x] F3.1 D-2 locale 機制拍板 — **甲 cookie-based**(next-intl without i18n routing;URL 不變,對齊 W18 flat URL;2026-07-14 用戶 AskUserQuestion)
- [x] F3.2 next-intl config + provider — next.config.mjs `createNextIntlPlugin` + i18n/request.ts(cookie `NEXT_LOCALE`)+ layout `<NextIntlClientProvider>` + messages/en.json + zh.json 骨架
- [x] F3.3 layout.tsx lang 動態化 — RootLayout async + `<html lang={locale}>`(getLocale)
- [x] F3.4 CJK font fallback —(原 🚧 defer → F7,2026-07-21 F7 收尾時完成)`--font-sans` / `--font-mono` 尾部加 `"PingFang TC", "Microsoft JhengHei", "Noto Sans TC"`(Latin 字體之後、generic 之前 — 只喺 Inter / JetBrains Mono 缺 glyph 時引用,en 零影響 by construction)。**跟足 DESIGN_SYSTEM.md §7.1 四層同步**:styles.css(canonical)→ styles-mockup.css(保留 next/font var 前綴 adaptation)→ globals.css 不動(只 carry color)→ tokens.ts fontFamily mirror + DESIGN_SYSTEM.md §1.5 表同步。**唔自 host** Noto Sans TC(避 build-time 下載撞 B-26 + 幾 MB 字檔;系統字體零依賴,Karpathy §1.2)。驗證:tsc / lint / `[oklch` grep 全過;§7.3 diff 證零新增 drift(79 行差異 pre-existing = W22 documented adaptation);browser 實證 stack 生效 + 新舊 render 有實差 + 本機有 JhengHei / Noto Sans TC;en / zh 截圖對比零回歸
- [x] F3.5 SSR-safe 驗 — tsc clean + build 成功(17 routes SSR;繞 font MITM cert 後證實 i18n build OK,無 hydration error)

## F4 — en dictionary externalize(🚧 增量進行中)
- [x] F4.1 en messages 骨架 + t() wiring pattern 定(批 1a:Nav/Breadcrumb/Shell/TopBar/LanguageToggle namespace + `useTranslations` client pattern + `t.has()` breadcrumb guard)
- [ ] F4.2 core flow view externalize(分批:**app-shell ✅ 批 1a** / **dashboard ✅ 批 1b** / **kb-list ✅ 批 2** / **topbar 3 組件 ✅ 批 3**(theme-toggle/notifications-menu/user-menu)/ **users ✅ 批 4**(4 tab + 3 dialog + StatCard;role 專有名 / status badge / TIER 2 / T2 / vendor / ADR / API 路徑保留英文;role-gated 深層視覺待 backend 起驗)/ **chat ✅ 批 7**(3190 行分 7a/7b/7c 子批;左 panel/header/empty + message/image gallery/footnote + sources/citation/feedback/screenshot modal/composer 全 externalize;schema field section_path/chunk_id + vendor + relevance 值保留)/ **kb-detail ✅ 批 8**(8 tab)+ **doc-detail ✅ 批 8**(inspector + per-doc config)/ **settings ✅ 批 8**(6 tab)/ **integrations ✅ 批 8**(landing + SharePoint wizard,H7 敏感)/ **kb-new + upload ✅ 批 8** / **traces + eval ✅ 批 8**(並行 subagent × 5,主 session 統一 merge namespace)/ **login ✅ 批 5** + **register ✅ 批 6**(login/page.tsx + register/page.tsx 3-step + validation + 3 error handler + AuthFrame login/register 共用 frame;auth-modes / MSAL / build footer / ACS footer / metric 值 / vendor / 範例值 保留英文);**Labs Tier 2 items 待後續** — labels 多技術名 + "Multi-Language" reason F1 promote 後 stale,連 F6 一併釐清)
- [x] F4.3 CH-023 那 7 檔 externalize(已英文 hardcode → 抽 dict)—— 批 8 kb-detail/doc-detail/settings cluster 覆蓋(doc-config-tab / doc-detail page / kb-detail page / upload / kb-new / settings page / settings-doc-profiling)
- [x] F4.4 grep 無 en chrome hardcode 殘留(動態拼接走查)—— 揭示 6 個漏網 shared component(global-search / tab-kb-access / api-key-input / deployments-table / error-boundary / login-gate)已 externalize;其餘硬 attribute 全屬保留項(範例值 email/URL/KB id、ARIA landmark `breadcrumb`)

## F5 — zh dictionary
- [x] F5.1 Claude draft zh 初稿(全 en key 對應)—— 實質隨 F4 各批逐批產出(1588 keys / 37 namespace 全對應);正式 tick 於 F5.2 glossary 落地時(2026-07-21)
- [x] F5.2 technical term glossary(保留英文定譯)—— **`frontend/messages/GLOSSARY.md` 落地**(A 保留英文 / B 統一中文 / C 分域例外 / D 排版規則 / E 拍板記錄)。基於 26 術語全量掃描實據;4 項分裂由用戶 2026-07-21 AskUserQuestion 拍板(chunk 保留 / 文件 profile→畫像 / preset 保留 / 調校術語保留英文+品牌句例外);**連帶批次修正 54 條**(區塊 / 切塊→chunk 15、管線 / 流程→pipeline 6、配方→preset 5、抽取→擷取 7、連接狀態→連線 6、identity→身分 4、profile→畫像 8、overlap / deployment 3、pipeline stage 短標統一英文 3);豁免 11 條(動詞 connect / procedure 流程手冊 / profiler 組件名)。驗證:parity 1588/1588 · ICU 0 fail · 殘留掃描零真殘留 · i18n 守門測試 16/16
- [ ] F5.3 用戶校對 → 定稿(**卡用戶**;而家有 glossary 做基準)

## F6 — Language toggle 啟用
- [x] F6.1 定位 mockup disabled Language toggle 現實作位置(app-shell TopBar,原 DisabledAffordance 包 disabled Globe)
- [x] F6.2 disabled → enabled + 綁 locale 切換 —— **正式版落地(2026-07-21)**。**H7 前提修正**:mockup 原來有完整 enabled 設計(`ekp-shell.jsx:104-134` LanguageMenu PopMenu 260px:code 欄 + native 語言名 + active 剔號 + Tier 2 badge + footer),批 1a 嘅「mockup 只有 disabled 版」判斷係錯 → 形態唔使二選一,正解 = 跟 mockup PopMenu。用戶拍板 3 項(AskUserQuestion):①形態跟 mockup PopMenu ②footer(原導向 prototype-only labs route)保留結構改 disabled 提示 ③Settings select enable 接 locale。**Design-stage 內容修正(per ADR-0075)**:mockup zh label「简体中文」→「繁體中文」/ en+zh enabled 剔號隨 locale、ja 保持 Tier 2 disabled / header 副題 ADR-0024 stale → ADR-0075。實作:`language-toggle.tsx` 重寫(portal pattern 同 notifications-menu 一致,menuTop / menuRight props 供登入頁錨點)+ `auth-frame.tsx` 登入頁 disabled Globe → 正式接線 + `settings/page.tsx` 語言 select enable(en / zh / ja-disabled,同 topbar cookie 同源)+ **Settings 語言組 3 條 stale 鍵清刪**(languageReason / languageTier2 + languageDesc 改寫)+ orphan 鍵清理(LanguageToggle.english / chinese、AuthFrame.langToggle×2)。驗證:parity 1588/1588 · ICU 0 fail · tsc / lint EXIT=0 · vitest 相關 5 檔 30/30。**🚧 browser 視覺走查 deferred**(playwright MCP 斷線 + Chrome extension localhost 導航失敗 ×2 即停)—— 用戶手動或工具恢復後補
- [x] F6.3 切換持久化(`NEXT_LOCALE` cookie 1yr)— reload / 重進保持

## F7 — H7 design sub-gate + test
- [x] F7.1 en 態逐 view 對齊 mockup(零回歸)—— 走查 9 view(dashboard / chat / kb / kb-detail / settings / users / traces / integrations / eval):**零 raw key 洩漏**、文案與 i18n 前一致、breadcrumb(en 仍「Knowledge › Knowledge Base」)+ kb-detail 8 tab 結構未變;layout 用程式化溢出檢查(1440px 九頁零溢出)。**note**:非逐 view 肉眼對 mockup —— i18n 只換文字來源不動 DOM/CSS,visual 由溢出檢查 + 文案一致性覆蓋
- [x] F7.2 zh 態逐 view 走查(文字長度唔撐爆 layout)—— 1440px 九 view **全部零溢出**;390px 有 5 處溢出但 **en 態同樣 5 處且量更大**(topbar 356 vs 267 / stat-grid 404 vs 265 / content-wide 950 vs 789)→ pre-existing responsive 行為,中文較短反而更緊湊 = **zh 零爆版回歸**。捉到 4 類文案問題:甲 stale(已修 2 處 + 第 3 處 Settings 組留 F6)/ 乙 術語不一致(留 F5.2 glossary)/ 丙 標點(已全量正規化)/ 丁 譯文撞名致 breadcrumb 資訊丟失(留 F5.3)
- [x] F7.3 Vitest 切換態 + 關鍵 view —— **先修好 W103 引入的回歸**:externalize 令組件依賴 i18n context,但 unit test 冇 provider 包住 → **24 檔 / 95 test 全掛**。修法=全域 setup 用 next-intl 官方 `createTranslator` 接管 hook(同一實作,`t()` / `t.rich()` / `t.has()` / ICU 行為一致,避免假綠),字典預設餵 en,**零改既有 24 個測試檔**;加 translator 快取後全套 112s → 62s。**新增 16 條測試**:`i18n-dictionaries.test.ts`(key / ICU 參數 / rich tag 對稱、無空值、中文排版回歸守門、保留清單抽樣)+ `i18n-locale-switch.test.tsx`(組件跟 locale 走、zh 態唔再 match 英文、ICU 參數兩態代入)。**餘 18 條失敗全屬 pre-existing**(見 progress Day 2)
- [x] F7.4 tsc / eslint / build clean(碰 backend 則 ruff / mypy strict)—— `tsc --noEmit` EXIT=0 · `next lint` EXIT=0(剩一個 `<img>` 警告屬 pre-existing)· **`next build` EXIT=0,17 route 全生成**(需 `NODE_TLS_REJECT_UNAUTHORIZED=0` 繞 B-26 font MITM;build 前後 wipe `.next` 避免 dev / production 產物混雜)。build 的 type-check 捉到 `setup.ts` 兩個 mock 型別問題(`createTranslator` 推導型別 vs 全域 `IntlMessages`、namespace literal union),已用單一 loose 簽名收斂 cast

## F8 — 文件同步 + closeout
- [x] F8.1 ADR-0075 impl note —— §Implementation Notes 補 2026-07-21 主體實作條目(F2 next-intl 4.13.2 / F3 cookie-based D-2 甲 / F4 37 ns 1588 keys / F5.2 glossary / F6 mockup PopMenu / F7 sub-gate 結果 + 「zh 撐爆 layout」預警實測未發生 + drift 機制回應),逐項對照 ADR spec 裁決
- [x] F8.2 en/zh dict 維護規則 —— **GLOSSARY.md §F**(F.1 加 string 五步含 machine gate / F.2 改譯文 / F.3 刪 key 含 JSON parse 教訓 / F.4 新術語爭議唔可以靜靜引入第三譯法 / F.5 drift 偵測三掃描 / F.6 測試層慣例)+ **CLAUDE.md §2 routing 加 row**「加 / 改 UI 文案」→ GLOSSARY.md(§14 微調自行做)
- [x] F8.3 user-guide language 章節 —— `docs/08-user-guide/01-platform-overview.md` 新增 §6 介面語言(兩個切換入口 / 範圍 = 介面唔係 content / 刻意保留英文清單指向 GLOSSARY / 譯文問題回報路徑)
- [x] F8.4 BACKLOG B-25 同步 —— 狀態改「進行中(W103 主體完成,剩用戶校對 + retro)」+ 內容更新 F1-F8.4 落地清單;**「完成」留 F5.3 + F8.5 齊先改**(誠實反映,唔提早閂)
- [ ] F8.5 closeout retro(progress.md 結尾)—— 等 F5.3 用戶校對完成一齊(phase 閂門)
