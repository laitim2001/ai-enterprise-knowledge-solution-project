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
- **F4 批 4 完成**(F4.2 users):`app/(app)/users/page.tsx`(1476 行)全 externalize —— page shell + gate(role null loading / non-admin banner)+ header + subtitle(rich `<mono>`)+ 4 stat card + 4 tab(Members/Roles/Groups/Audit)+ 3 dialog(Invite/RowAction/Suspend)+ RolesTab 權限矩陣 + GroupsTab + AuditTab;`formatRelative` 改簽名傳入 `t`(Groups + Audit 共用);TABS / SEG_FILTERS 由 `label` 改 i18n `labelKey`;ICU plural(role card 成員數)+ rich(`<mono>` / `<b>`)。加 Users namespace(en 完整 + zh **draft 初稿待校對**)。**保留英文**:role 專有名(Workspace Admin / Knowledge Editor / End User / Power User + RoleBadge column Admin/Editor/User/Power)、status badge(ACTIVE / PENDING EMAIL / INVITED / SUSPENDED)、TIER 2 / T2 badge、vendor(Entra ID / Postgres)、technical(ADR-0024 / RBAC / Tier 1/2)、API 路徑(`/users` / `/groups` / `/admin/audit-log`)、範例 email(`name@ricoh.com`)、`system` fallback、`EKP_ROLE_LABELS`(backend)。**tsc EXIT=0 + eslint clean**。**browser 驗證**(port 3002 mock auth,backend down):en↔zh 雙向切換 —— 頁首(Users & access ↔ 使用者與存取權限)+ gate loading(Loading… ↔ 載入中…)+ shell / breadcrumb 雙向正確,layout 無爆版。**環境限制**:`useRole()` fetch `/auth/me`(backend down → role 恆 null),頁面卡 gate loading,role-gated 深層(stat / 4 tab / 3 dialog / error 態)frontend-only 驗不到 → 留「整批做完一次過測」開 backend 涵蓋;深層正確性由 tsc / eslint clean + 逐 component 對照 mockup 結構 externalize 保證。
- **F4 批 5 完成**(F4.2 login):`app/login/page.tsx` + `components/auth/auth-frame.tsx`(login/register 共用 frame)externalize —— 表單(welcome / subtitle / SSO / divider / work email / password / forgot / submit / sign-up link)+ toast(creds required / welcome / SSO / `handleAuthError` 三態:invalid creds / email not verified / fallback)+ 左 brand panel(brand full name / headline / subtitle / 3 metric sub 描述)+ 頂欄 theme toggle(複用 ThemeToggle namespace)+ language toggle(**保持 disabled**,F6 login-page 正式化待處理)。`handleAuthError` 加 `t` 參數;metric chips 移除 `as const`。加 Login + AuthFrame namespace(en 完整 + zh draft)。**保留英文**:vendor(Microsoft / Ricoh / Cohere v4.0-pro / Langfuse / Dify / D365 F&O ERP)、metric 值(R@5 = 97.2% / P95 latency 4.2s / 100% oklch tokens)、corpus 名(Drive Manuals)、範例 email(`you@ricoh.com`)、`••••••••`、Tier 2 badge、auth-modes (Tier 1) mono block、MSAL / build footer(technical mono,同 user-menu footer 一致保留)。**tsc EXIT=0 + eslint clean**。**browser 完整驗證**(login 頁唔靠 backend data,mock 下無 redirect):en↔zh 雙向 —— brand「企業知識平台」/ headline「植根於您真實文件的知識檢索。」/ 表單全中文 / metric 值 + auth-modes + footer 保留,layout 無爆版。register 頁共用 AuthFrame 同步雙語(表單本體待後續)。**note**:login 頁無 shell LanguageToggle(disabled Globe 屬 F6),驗 zh 需先在 dashboard 切 cookie 再進。
- **F4 批 6 完成**(F4.2 register):`app/register/page.tsx`(888 行,3-step)externalize —— Step1(account info:heading / subtitle rich signin link / full name / work email + hint rich mono / password + hint / terms rich 雙 link / submit / sign-in link)+ Step2(email verify:heading / subtitle rich b+email / code label / digit aria ICU / what-happens-next 清單 rich mono+b / verify / resend ICU / back)+ Step3(welcome:name ICU + friend fallback / account ready / default KB / multi-KB title+hint / dashboard btn)+ `validateAccountInfo`(6 errors,ICU errMinChars)+ 3 個 module-level error handler(register / verify / resend,全傳入 `t`)+ toast。加 Register namespace(en 完整 + zh draft,~55 key)。**保留英文**:範例(`Chris Lai` / `you@ricoh.com`)、`@ricoh.com`(mono)、Scrypt / ADR-0022 / Langfuse / Ricoh · RAPO(嵌句)、KB id `drive_user_manuals`、Tier badge、**ACS footer**(Azure Communication Services / C13 / architecture.md v6 §3.7 / ConsoleEmailProvider,technical mono dashed block,同 auth-modes / MSAL 一致)。**tsc EXIT=0 + eslint clean**。**browser 驗證**(cookie zh):`get_page_text` 讀到 Step1 + AuthFrame 完整 zh —— 表單全中文、rich(signin / terms / privacy link + mono)render 正常、validation error(必填。/ 請接受…)中文化、保留項一致;Step2/3 需提交走 backend(down 進不到),code-level 由 tsc + 與 login 相同 pattern 保證。**note**:register render 時截圖 CDP timeout(backend ECONNREFUSED 洗版令 renderer 卡,已知現象),改用 `get_page_text` 繞過成功。
- **F4 批 7 完成**(F4.2 chat):`app/(app)/chat/page.tsx`(3190 行,全 phase 最大單頁)分 7a/7b/7c 三子批 externalize,Chat namespace 一次定義(en 完整 + zh **draft 待校對**,~64 key)—— 7a=ConversationHistoryPanel / ConversationItem / ChatHeader / EmptyState;7b=MessageRow / InlineImageCard / ImageGallery / FootnoteList;7c=SourcesStrip / SourceDocCard / CitationPanel / PanelSourceCard / FeedbackBar / ScreenshotModal / ChatComposer。ICU plural(citation / chunk / iteration / conversation count)+ rich;`formatRelative` / module-level handler 傳入 `t` pattern 延續。**保留英文**:vendor(Cohere v4.0-pro / GPT-5.5 / CRAG L2 / D365 F&O ERP)、schema field mono(section_path / chunk_id / chunk #{n})、corpus 域(AR / AP / FA / CB / GL / BM)、ADR-0031、relevance 數值。**tsc EXIT=0 + eslint clean**(只餘 pre-existing `<img>` line 1990 warning)。**chat 為全 phase 最大單頁,核心大頁完成**。
- **F4 批 8 完成**(F4.2 剩餘 view + F4.3 CH-023)—— **並行 subagent × 5 一次過**(用戶 2026-07-14 揀「一次過」策略):每 agent externalize 一個 cluster + 回報 en/zh keys,主 session 統一 merge namespace 入 en.json/zh.json(避免多 agent 爭寫 json)。5 cluster:**A settings**(page + 6 tab 組件 → 7 namespace `Settings`/`SettingsApiKeys`/`SettingsTabError`/`SettingsAudit`/`SettingsIdentity`/`SettingsConnections`/`SettingsDocProfiling`)/ **B kb-detail + doc-detail**(kb/[id]/page 8 tab + docs/[docId] + doc-config-tab → `KbDetail`/`DocDetail`/`DocConfig`)/ **C kb-new + upload**(`KbNew`/`KbUpload`)/ **D integrations**(landing + SharePoint 4 步 wizard,H7 敏感 → `Integrations`)/ **E observability**(traces×2 + eval → `Traces`/`Eval`)。共 **15 namespace** merge(A/C/D/E 12 + B 3)。**Agent B 中途 API error(response stalled mid-stream)** → SendMessage resume 續完成 + 修 tsc(`formatRelative` call site 少 `t` 參數)+ 補回報 keys。**Agent B 經 SendMessage/notification 雙層傳輸令 rich tag 被 HTML-escape 成 `&lt;b&gt;`**,merge 時用 node 統一 un-escape(零殘留驗證)。**驗證**:全 project `tsc` EXIT=0 + `eslint` EXIT=0 + **en/zh 完全 parity**(各 1511 keys / 31 namespace,零 missing/extra)+ **ICU rich-text parse 全 pass**(1511×2 條 IntlMessageFormat parse 零 fail,`<b>`/`<mono>`/`<bWarn>` tag valid,唔會 runtime crash)。root(`app/page.tsx`)純 redirect 無字串 → skip。**carry-over**:Settings「Language」toggle 描述「JP/ZH is Tier 2 disabled」F1 promote 後 stale(同 shell/Labs disabled toggle),externalize 照 verbatim,修正歸 F6。**H7 STOP 項(agent 交主決定)**:① kb-detail ImagesTab「How chunks reference images」explainer 含大量 literal 花括號 token(`EmbeddedImage{sha256,…}`)入 ICU 會當 placeholder → body 保留原 JSX 只抽標題;② Eval/Traces module-level const taxonomy(`PIPELINE_STAGES`/`METRIC_LABELS` 等)未抽(需 key-lookup restructure,超 externalize scope)—— 兩者留後續決定。
- **F4.4 完成**(無 en hardcode 殘留走查)—— grep 硬 attribute(aria/placeholder/title/alt) + 差集(全 .tsx − useTranslations)揭示 **6 個漏網 shared component**(page-level agent scope 未 cover 嘅獨立組件):`global-search`(Cmd/K palette)/ `tab-kb-access`(KB Access tab ~40 條)/ `api-key-input` / `deployments-table` / `error-boundary`(只 `ErrorBoundaryView`,class 唔動)/ `login-gate`。開 1 subagent externalize(6 namespace `GlobalSearch`/`KbAccess`/`ApiKeyInput`/`DeploymentsTable`/`ErrorBoundary`/`LoginGate`)主 session merge。**確認唔使動**:`disabled-affordance`(文字全 props + `TIER 2` 保留)/ `service-card`(status badge `HEALTHY/DEGRADED` 保留)/ `role-badge`(role 專有名保留)/ 2 error page(只傳 `scope` identifier)/ layout(純 wrapper)/ `breadcrumb`(`aria-label="breadcrumb"` ARIA landmark 慣用值)。**修正**:`ApiKeyInput.notProvisioned = <not provisioned>` 因 `<>` 被 ICU 當 tag(INVALID_TAG)→ revert 成 code literal(data sentinel 保留,不 externalize)。**驗證**:tsc EXIT=0 · eslint EXIT=0 · **en/zh parity**(各 1588 keys / 37 namespace,零 missing/extra)· **ICU parse 0 fail**。**至此 F4 全部 sub-item(F4.1–F4.4)完成。**

**Decision / deviation(R3)**:
- **F1.2 採 inline-tagged + doc-version-held convention,非 plan 原寫「version bump」** —— 對齊 architecture.md 既有 amendment 慣例(§3.4 ADR-0023 / §3.7 ADR-0022 / §5 ADR-0024),更接近既有 pattern(§13);doc version held v6,唔 bump v7。architecture.md line 17 歷史 note 保留(審計軌跡)。
- Language toggle 實際 disabled→enabled = F6,非 F1(F1 只確立文件層 Tier 邊界,頁面暫未有雙語切換功能)。
- **D-2 locale 機制拍板 = 甲 cookie-based**(2026-07-14 用戶 AskUserQuestion)—— next-intl「without i18n routing」,locale 存 `NEXT_LOCALE` cookie,URL 不變(對齊 W18 flat URL);route 零搬遷。副作用:所有 route 因 `cookies()` 讀取變 dynamic(SSR on demand)—— 對 EKP authenticated app 無實質影響(本來多數 dynamic)。
- **F3.4 CJK font fallback → 🚧 defer F7**(plan deviation R3):font stack 改動觸 design token 4-layer sync(DESIGN_SYSTEM.md §7)+ H7 fidelity;瀏覽器預設已 fallback 顯示 CJK,明確 CJK font stack 歸 F7 逐 view 走查一齊處理。
- **Build 環境發現(pre-existing,非 W103 引入)**:`next build` 因 `next/font/google` 抓 Google Fonts 撞 Ricoh MITM(`SELF_SIGNED_CERT_IN_CHAIN`)fail;設 `NODE_TLS_REJECT_UNAUTHORIZED=0`(dev-only,同 next.config backend proxy `rejectUnauthorized=false` pattern)繞過後 build 成功。frontend 喺 Ricoh 網絡 build 需此 workaround —— 屬 infra 議題(font import pre-existing,非 i18n),候選記 BACKLOG。

**下一步**:**F4 全部完成**(F4.1–F4.4;21 view/組件 + CH-023 7 檔全部 `t()` wiring,en 定稿 + zh draft,37 namespace / 1588 keys)。餘:**F5.3** zh 全 draft 待用戶校對(1588 keys)/ **F6** language toggle 正式化 + Labs & Settings「Language」stale 釐清 / **F7** H7 逐 view en+zh 走查(含 F3.4 CJK font + browser 抽驗 rich-text render)/ **F8** closeout。test env(port 3002)可 refresh 睇;role-gated 深層頁需開 backend 驗完整視覺。

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
- `67ac72d` — W103 F4 批 3 topbar 3 組件 externalize。
- `550f42b` — W103 F4 批 4 users(1476 行)externalize + Users namespace。
- `813b84a` — W103 F4 批 5 login + AuthFrame externalize + Login/AuthFrame namespace。
- `b4ebd38` — W103 F4 批 6 register(888 行 3-step)externalize + Register namespace。
- `8f2e0da` — W103 F4 批 7a chat 左 panel + header + empty externalize + Chat namespace 骨架。
- `a5ec9d2` — W103 F4 批 7bc chat 餘下全 externalize(message / image / sources / citation / feedback / screenshot / composer),chat 整頁完成。
- `900bb39` — W103 F4 批 8 剩餘 view 並行 subagent × 5 externalize + 15 namespace merge(settings 7 / kb-detail 3 / kb-new+upload 2 / integrations 1 / observability 2;F4.2 剩餘 + F4.3 CH-023 全 ✅)。
- (本批 commit)W103 F4.4 補漏 — 6 個漏網 shared component externalize + 6 namespace merge(GlobalSearch / KbAccess / ApiKeyInput / DeploymentsTable / ErrorBoundary / LoginGate);notProvisioned ICU 修正。F4 全部完成。
- _註:批 5–8(pre-rebase `813b84a`…`8c15e1c`)經 PR #16 rebase-merge,main 實際 hash 已重寫(`a49ec75` / `0b48b8a` / `900bb39` 等);上列 pre-rebase hash 保留作 audit,不逐一回填。_

## Day 2(2026-07-20)— F7.1 / F7.2 走查 + stale 修正 + 標點正規化

**Context**:F4 全部完成後,用戶揀先做 **(甲)F7.1/F7.2 browser 逐 view 走查**(捉爆版 / 漏譯 / render 問題),再按走查結果修甲類 stale + 丙類標點。

**已做**:
- **F7.1 + F7.2 走查完成**(Playwright,1440px + 390px 雙寬度,9 view):
  - **en 零回歸**:零 raw key 洩漏、文案與 i18n 前一致、breadcrumb + kb-detail 8 tab 結構未變。
  - **zh 零爆版回歸**:1440px 九 view 程式化溢出檢查**全部零溢出**;390px 有 5 處溢出,但 **en 態同樣 5 處且溢出量更大**(topbar 356 vs 267 / stat-grid 404 vs 265 / content-wide 950 vs 789)→ 屬 pre-existing responsive 行為,中文較短反而更緊湊。
  - 語言切換機制實測正常:cookie 寫入 → `<html lang>` 翻轉 → SSR 重讀。
  - **方法論**:browser 走查捉爆版有效但捉漏譯不全 → 補 **靜態全量掃描**(1588 條逐條驗)。兩者互補,單靠 browser 會漏。
- **甲類 stale 修正**(2 處):`app-shell.tsx` Labs reason 改「Japanese UI + content translation — Tier 2 (en / zh UI shipped per ADR-0075)」;`AuthFrame` 語言鈕去掉 Tier 2 錯誤歸類(保持 disabled 等 F6 接線)+ comment 同步。**Labs 8 項未 externalize**(技術名譯法屬 F6 決定,不單方面做)。
- **丙類標點全量正規化**(62 條):寫試跑腳本 → 逐條審差異 → 寫入。規則**保守**:只轉緊鄰中文的標點,ICU 佔位符 / rich tag / URL 全程哨兵保護。審差異時補兩條規則:全形括號自帶留白(清左括號前殘留空格)、佔位符後的結尾 `!` / `?`。另補修 3 處規則漏網:`KbList` 拼接句(左右括號分散兩條 key,配對規則捉不到)、`rbacBannerDesc` 的 `Tier 1:` / `Tier 2:`(冒號前是數字)。
- **順手清理 W103 自身製造的 lint 警告**:`settings-audit-log.tsx` 兩個 `t` 缺 dependency —— 用註解 + 停用該規則(零行為改變;若加入 deps,translator identity 一變會整份稽核日誌重抓)。
- **驗證**:1588/1588 鍵 · 零缺漏零多餘 · ICU 解析 0 失敗 · **佔位符對稱 ✅ · rich tag 對稱 ✅**(新增兩項檢查,防批次改寫破壞 ICU)· `tsc` EXIT=0 · `next lint` EXIT=0(剩一個 `<img>` 警告屬 pre-existing)· browser 抽驗拼接句正確 render。

**Decision / deviation(R3)**:
- **括號風格拍板 = 保持半形 + 空格**(2026-07-20 用戶 AskUserQuestion)—— 殘留掃描發現 27 條「中文標籤 + 空格 + 半形括號包純西文」(`應用程式 (client) ID` / `圖片密度 (img_density)`),**本身已一致**,不屬「同句混用」;純西文用半形括號是通行中英混排慣例,可讀性較好且與 mono 技術詞視覺一致。故正規化**不涵蓋**此 pattern。
- **Settings 語言鍵組(第 3 處 stale)→ 留 F6**(2026-07-20 用戶拍板):`languageDesc` / `languageReason` / `languageTier2` 仍寫 Tier 2,且控制項是 disabled Tier 2 樣式。單改文案會與「頂欄已有可用切換」矛盾 —— 接線與否同屬 F6 正式化決定,分開做會改兩次。
- **F7.1 驗證方式說明**:非逐 view 肉眼對 mockup。i18n 只換文字來源、不動 DOM / CSS,故以「程式化溢出檢查 + 文案一致性 + 結構未變」覆蓋零回歸;真正的 mockup fidelity 基線由 W22 UI sprint 建立,本 phase 無 layout 改動。

**下一步**:F7 餘 **F7.3**(Vitest 切換態)+ **F7.4**(`next build` clean,含 B-26 font MITM workaround)+ **F3.4**(CJK font stack,🚧 defer 到此)。之後 **F5.2 glossary**(乙類術語不一致:chunk 譯「區塊」vs 保留「Chunks」/ `Settings.tabIdentity` 疑似漏譯 / 86 條純英文值逐條定去留)→ **F5.3 用戶校對** → **F6**(toggle 正式化 + Labs & Settings 語言組 stale)→ **F8** closeout。

**Commits**:
- `7dba27e`(PR #18 rebase-merge → main `babd8c9`)W103 F7.1/F7.2 走查 + 甲類 stale 修正(Labs reason / AuthFrame 語言鈕)+ 丙類標點全量正規化 62 條 + audit-log lint 清理。
- (本批 commit)W103 F7.3 Vitest i18n 修復 + 16 條新測試 + F7.4 build clean。

---

### Day 2 續 — F7.3 / F7.4(收齊 F7)

**F7.3 揭出並修好 W103 引入的重大回歸**:
- **症狀**:`vitest run` → **24 檔 / 95 test 失敗**,全部同一句 `Failed to call useTranslations because the context from NextIntlClientProvider was not found`。externalize 令幾乎每個組件依賴 i18n context,但 unit test 直接 render、冇 provider。
- **點解拖到而家先爆**:前面每批只跑 `tsc` + `eslint`;而 `frontend-deploy.yml` 的 `lint-and-build` **從來冇跑 vitest** → 零 CI 覆蓋。
- **修法**:`tests/unit/setup.ts` 全域 `vi.mock('next-intl')`,用 **next-intl 官方 `createTranslator`** 接管 `useTranslations` / `useLocale`。特意**唔手寫假 translator** —— 官方實作保證 `t()` / `t.rich()` / `t.has()` 同 ICU 格式化行為一致,避免「測試綠但真實 render 爆」的假綠。字典預設 en → **既有 24 個測試檔零改動**。
- **效能**:初版每次 `useTranslations()` 都重建 translator,ICU 初始化疊加令全套慢 15 倍(chat-meta-row 908ms → 13.5s)。加 (locale, namespace) 快取後 **112s → 62s,比 i18n 之前仲快**。
- **新增 16 條測試(2 檔,全綠)**:`i18n-dictionaries.test.ts`(零組件依賴的字典守門:key / ICU 參數 / rich tag 對稱 + 無空值 + **中文排版回歸**〔守住丙類正規化,按拍板豁免括號〕+ 保留清單抽樣)/ `i18n-locale-switch.test.tsx`(切換態:組件跟 locale 走、zh 態唔再 match 英文、ICU 參數兩態都代入)。新建 `i18n-locale.ts` 提供 `setTestLocale()`,setup 每個 test 後自動 reset。

**餘 18 條失敗 —— 逐條查證全屬 pre-existing,非 W103**:

| 失敗檔 | 條數 | 根因 | 時序證據 |
|---|---|---|---|
| kb-settings-tuning / doc-config-tab / kb-settings-reindex | 16 | 測試斷言中文文案,但 **CH-023 已把 UI 改英文** | CH-023 `3221d38` = 2026-07-09;三個測試檔最後改動 = 06-05 / 06-09 / 06-12。W103 kickoff = 07-14 |
| kb-detail | 1 | `IMAGE_DENSE_PRESET` mock 缺 export → 組件 throw、body 空 | 引入 commit `7075526` 距今 **177 個 commit** |
| chat-meta-row | 1 | W83 section badge 令 `querySelector('.badge.badge-muted')` 攞到第一個(capped 8)而非 gallery 總數(10) | 引入 commit `25ef5ad`(W83 ADR-0064)距今 **191 個 commit** |

**F7.4 build clean**:`tsc --noEmit` EXIT=0 · `next lint` EXIT=0 · **`next build` EXIT=0(17 route 全生成)**。過程要先停 frontend dev server(避免同 `.next` 相爭,memory 有記錄呢種損壞),build 前後各 wipe 一次 `.next`,完成後以 WMI detached 重啟(parent = WmiPrvSE)。**build 的 type-check 捉到兩個我新寫 `setup.ts` 的型別問題**(`createTranslator` 由 messages 推導的型別 vs `useTranslations` 的全域 `IntlMessages`;namespace 要 literal union)—— 用單一 loose 簽名把 cast 收斂喺一點。

**Decision / deviation(R3)**:
- **pre-existing 測試失敗唔喺 W103 修**:18 條全部有時序證據證明早於本 phase(最遠 191 個 commit)。按 Karpathy §1.3「只清自己製造的 mess」,W103 只負責修 provider 回歸;呢 18 條應另開 Bug-fix / Change instance,並記入 BACKLOG。
- **`frontend-deploy.yml` 冇跑 vitest = 制度性缺口**:呢個先係「積咗一個月冇人發現」的根因(W103 自己嗰 95 條、pre-existing 嗰 18 條,都係同一個窿漏出去)。補 CI 步驟屬 workflow 改動(非 W103 scope)→ 已記 **BACKLOG B-27**。
- **BACKLOG 舊條目升級**:W101 早已記錄「14 個既有 frontend test fail…疑 kb config schema 演進後 test stale」。今次以 commit 時序逐條查實根因(CH-023 中文→英文 / `IMAGE_DENSE_PRESET` mock / W83 badge),數字校正為 **18 條 5 檔**,由「疑」升級為「確認 + 修法明確」。W101 用 `git diff` 證、W103 用 commit 時序證 —— 兩條獨立證據鏈結論一致。
- **測試 flakiness(新觀察)**:機器負載高時 `chat-bug034` / `chat-inline-image-interleave` 各有 1 條會因 async 等待逾時假紅 —— 全套 133 秒嗰次紅,單獨跑 33 秒嗰次 **6/6 全綠**。故**穩定基線 = 5 檔 / 18 條**,唔係 7 檔 / 20 條。入 CI 之前宜先調 `testTimeout`(已記入 B-27)。

---

## Day 3(2026-07-21)— F3.4 CJK font fallback(F7 真正收乾淨)

**Context**:F7.1–F7.4 已收,F3.4(kickoff 時 🚧 defer 到 F7)係 F7 弧最後一項。

**已做(跟足 DESIGN_SYSTEM.md §7.1 四層同步程序)**:
- **設計決定**:系統 CJK 字體 fallback,**唔自 host** —— 自 host Noto Sans TC 要 build-time 下載(撞 B-26 MITM)+ 幾 MB 字檔 + H2 新依賴考量;系統字體零依賴零下載(Karpathy §1.2)。TC 選序:`PingFang TC`(macOS)→ `Microsoft JhengHei`(Windows)→ `Noto Sans TC`(Linux / Android)。
- **關鍵機制**:CJK 字體放喺**所有 Latin 字體之後**、generic keyword 之前 —— fallback 只喺 Inter / JetBrains Mono 缺 glyph(即中文字符)時先引用,**en 版面零影響 by construction**(呢個係 H7 零回歸的機制保證,唔靠肉眼)。
- 四層改動:①`references/design-mockups/styles.css`(canonical,`--font-sans` / `--font-mono` + 註解)②`frontend/app/styles-mockup.css`(同步,保留 next/font `var()` 前綴 adaptation)③`globals.css` **不動**(§7 圖明寫 layer 3 只 carry color tokens)④`tokens.ts` fontFamily mirror。⑤連帶 DESIGN_SYSTEM.md §1.5 font 表 + CJK fallback 說明。
- **驗證**:`tsc` EXIT=0 · `next lint` EXIT=0 · `[oklch` grep 零 hit(§7.1 step 5)· **§7.3 diff 證零新增 drift**(diff 有 79 行,但 HEAD 版已有一模一樣的 79 行 —— 全屬 W22 F1-pivot documented adaptation:layer 2 有意剝走 color tokens 移去 globals.css,header comment 講明)· dark mode 步驟不適用(font 無 dark 分支)。
- **Browser 實證**(dashboard):computed `font-family` 已帶新 stack;**新舊 stack render 中文有實差**(bitmap 對比 —— 證明 fallback 有實效,唔係 no-op);本機裝有 Microsoft JhengHei + Noto Sans TC(bitmap 存在性探測);zh 態中文以黑體一致 render(無襯線混雜 / 缺字方格);**en 態截圖對比零回歸**。
- **測量方法教訓**:①canvas **寬度比較**法對 CJK 無效 —— 中文字喺任何字體都係全形 1em 闊 → false negative;②`document.fonts.check` 對唔存在嘅字體有 false positive(Chromium 已知);③跨 stack bitmap 全等比較太嚴 —— stack 版嘅 font metrics 由 primary font(Inter)決定,同單 family 版有 sub-pixel 位移。可靠組合 = 「family, monospace」vs「monospace」bitmap **存在性**探測 + 新舊 stack **實差**探測;「精確邊隻 render」留畀 CSS fallback 標準行為保證,唔值得再挖(Karpathy §1.1 唔 rabbit hole)。

**下一步**:F7 弧全收(F7.1–F7.4 + F3.4)。餘 **F5.2** glossary(乙類術語)→ **F5.3 用戶校對 zh(卡用戶)** → **F6** toggle 正式化 + Labs / Settings 語言組 stale → **F8** closeout 五項。

**Commits**:
- `8aa4cfa`(PR #20 rebase-merge)W103 F3.4 CJK font fallback — §7.1 四層同步。

---

### Day 3 續 — F5.2 glossary 定案 + 批次術語統一

**方法**:唔憑感覺寫 glossary —— 先寫 26 術語全量掃描 script(en 含該詞 → en / zh 並排 + 保留 / 譯 / 混三分類),基於實據歸納。掃出**分裂比預期多**:除已知 chunk 外,仲有 profile 文件域**四譯**(profile / 畫像 / 設定檔 / 個人檔案)、pipeline **三譯**(pipeline / 管線 / 流程)、chunk strategy 三譯、preset / 配方、rerank / 重排、extract 抽取 / 擷取、connection 連線 / 連接、deployment / overlap 各半、`Settings.tabIdentity` 漏譯。

**拍板(2026-07-21 AskUserQuestion,4 項全跟建議)**:
1. **chunk 系統一保留 chunk**(71/78 已保留;區塊→chunk 改 ~15 條;chunk strategy →「Chunk 策略」)
2. **文件 profile 域統一「畫像」**(W78 UI 已立「畫像」係最大存量;user profile「個人檔案」不動)
3. **preset 統一保留**(profile→preset 對應係核心域,同 ADR-0056 對齊)
4. **rerank / pipeline / overlap / deployment 保留英文**;品牌句「Cohere v4.0-pro 重排」例外保持;Chat 用戶面 citation 譯「引用」、調校面保留

**產出**:
- **`frontend/messages/GLOSSARY.md`**(術語權威):A 保留英文(vendor / metric / badge / role 專名 / schema mono / RAG 核心術語 / Azure Portal 對照欄位 / pipeline stage 短標)/ B 統一中文定譯(~30 詞)/ C 分域例外(citation 分域 / profile 分域 / embedding vs embedded / 品牌句例外 / 表頭一致)/ D 排版規則(2026-07-20 拍板收錄)/ E 拍板記錄。
- **批次修正 54 條**(43 全值 + 11 substring):精準 per-key map(dry-run 報告逐條審後先寫入,任何 key 缺失 / substring 對唔上即 ABORT);豁免 11 條(動詞 connect 容許「連接」/ procedure「流程手冊」/ `profiler` 組件名)。
- 順帶解決乙類清單第 4 項:`Settings.tabIdentity`「Identity & Auth」→「身分與驗證」(對齊 UserMenu 既有譯法)。

**驗證**:parity 1588/1588 · ICU 0 fail · placeholder / tag 對稱 · 殘留掃描零真殘留(11 條全豁免項)· i18n 守門測試 16/16。

**F5.3 前置就緒**:glossary 已定 + 術語已統一 → 用戶校對時有一致基準,唔使逐條糾結譯法。

---

### Day 3 續 2 — F6.2 language toggle 正式化 + Settings 語言組清 stale

**H7 前提修正(重要)**:F4 批 1a 記錄嘅「mockup 只有 disabled Globe,冇 enabled 互動設計」係**錯**—— `ekp-shell.jsx:104-134` 一直有完整 `LanguageMenu`:Globe = PopMenu trigger,菜單 260px(mono code 欄 + native 語言名 + active 剔號 accent + disabled 行 opacity .5 + Tier 2 badge + footer)。教訓:**當初斷言「mockup 冇」之前應該 grep 埋 `ekp-shell.jsx`,唔止睇 page-level jsx**(同 R6 pre-active-flip grep 精神一致)。所以 F6.2 形態唔使二選一 —— H7 正解就係跟 mockup。

**用戶拍板(2026-07-21 AskUserQuestion,3 項)**:①topbar 形態跟 mockup PopMenu ②mockup footer「Preview JP / ZH support (Labs) →」導向 prototype-only route → 保留結構、內容改 disabled 提示(日文 UI — Tier 2)③Settings 外觀分頁語言 select enable 接 locale(唔係指向 topbar)。

**Design-stage 內容修正(唔使問,per ADR-0075 明顯正解)**:mockup zh label「简体中文」→「繁體中文」(promote 嘅係繁體 UI chrome);en / zh enabled(剔號隨 locale)、ja 保持 Tier 2 disabled;header 副題「Per ADR-0024 · JP/ZH disabled in Tier 1」stale → 「Per ADR-0075 · en / zh Tier 1 · JP is Tier 2」。

**實作**:
- `language-toggle.tsx` 重寫:portal PopMenu(pattern 同 `notifications-menu.tsx` 完全一致 —— createPortal + click-outside `[data-popmenu-trigger]` `.closest()` 檢查 + `position: fixed` viewport 錨定;Radix DropdownMenu 係 anti-pattern per DESIGN_SYSTEM.md §4);mockup 參數 width=260 / right=138;`menuTop` / `menuRight` props 供登入頁錨點覆寫。
- `auth-frame.tsx`:登入頁 disabled Globe → `<LanguageToggle menuTop="74px" menuRight={48} />` 正式接線(F4 批 5 嘅「等 F6」carry-over 清咗)。
- `settings/page.tsx` AppearanceTab:語言 select 拿走 `DisabledAffordance`,enable + `value={locale}` + onChange 寫 cookie + `router.refresh()`(同 topbar 同源);option en / zh / ja(disabled)。
- **字典清理(+6 −6,總數 1588 不變)**:LanguageToggle 加 menuTitle / menuSubtitle / tier2Badge / footerJapanese、刪 english / chinese(cycle 版 orphan);Settings 刪 languageReason / languageTier2(DisabledAffordance orphan)+ languageDesc 改寫 + 加 languageOptionChinese / languageOptionJapanese;AuthFrame 刪 langToggleTitle / langToggleAria(orphan)。語言 native name(English / 繁體中文 / 日本語)按慣例兩 locale 同值。
- **踩坑**:Edit 刪 JSON 尾 key 留低懸掛逗號 → 兩檔 parse error;修好後統一 `JSON.stringify(,null,2)` re-format。教訓:批次刪 JSON key 後**即刻** parse 驗,唔好等到 verify 套件先發現。

**驗證**:parity 1588 / 1588 · ICU 0 fail · placeholder / tag 對稱 · `tsc` EXIT=0 · `next lint` EXIT=0 · vitest 相關 5 檔(i18n×2 + app-shell + login + settings-6tab)**30/30**。

**🚧 deferred**:browser 視覺走查(PopMenu 開合 / 剔號 / 切換 / 登入頁錨點 74px·48px 係估算值)—— playwright MCP session 中途斷線 + claude-in-chrome 對 localhost 導航失敗 ×2(按 rabbit-hole 規則即停)。服務跑緊(3002),用戶手動可即驗;或工具恢復後補。登入頁 PopMenu 錨點若有偏移屬 polish 級(唔阻 merge)。

---

### Day 3 續 3 — F8.1–F8.4 doc-sync(F8.5 retro 留 phase 閂門)

- **F8.1 ADR-0075 impl note**:§Implementation Notes 補「2026-07-21 主體實作落地」條目 —— 逐項對照 ADR spec 嘅裁決結果(F2 `next-intl` 4.13.2 落地、H2 傾向成立 / F3 locale 機制兩選項拍板 cookie-based / F4 規模 37 ns 1588 keys / F5.2 對 §Consequences「翻譯來源 + 維護」隱憂嘅回應 = GLOSSARY / F6 mockup 原有 PopMenu 設計 / F7 「zh 撐爆 layout」預警**實測未發生** + drift 機制回應 = 守門測試)。
- **F8.2 dict 維護規則**:**GLOSSARY.md §F(binding,類比 DESIGN_SYSTEM.md §7)** —— F.1 加 string 五步(核心 = machine gate `i18n-dictionaries.test.ts`,缺一邊 key 係 runtime throw 唔係 fallback)/ F.2 改譯文(術語變更先改表)/ F.3 刪 key(JSON parse 即驗,F6.2 踩坑)/ F.4 新術語爭議(唔可以靜靜引入第三種譯法 —— profile 四譯就係咁積出嚟)/ F.5 drift 三掃描(browser 走查捉唔齊漏譯嘅教訓)/ F.6 測試層慣例。**CLAUDE.md §2 routing 加 row**(§14 微調)。
- **F8.3 user-guide**:`01-platform-overview.md` 新增 §6 介面語言 —— 面向平台操作者:兩個切換入口 / 「介面譯、內容唔譯」嘅刻意設計 / 保留英文清單唔係漏譯 / 譯文問題回報路徑。
- **F8.4 BACKLOG B-25**:狀態「進行中(W103 主體完成,剩用戶校對 + retro)」+ 落地清單同步;**「完成」唔提早改** —— F5.3 + F8.5 齊先閂。
- **F8.5 留待**:closeout retro 同 phase 閂門等 F5.3 用戶校對完成一齊做(R2 phase gate 慣例)。
