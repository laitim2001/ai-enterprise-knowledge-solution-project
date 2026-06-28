---
change_id: CH-013
title: "前端通電真實登入 — 接入 cookie-session auth 第三模式（self-register 本地帳號）"
status: approved         # draft | proposed | approved | active | done | cancelled
created: 2026-06-28
target_completion: 2026-06-29
affects_components: [C11]      # C11 Auth（前端 auth state 機制；後端不動 code）
spec_refs:
  - architecture.md §5.0 (login gate / authenticated shell)
  - ADR-0014 (hybrid auth — Entra ID SSO + email self-register)
  - ADR-0022 (auth-transport hardening — httpOnly ekp_session cookie + CSRF double-submit)
  - ADR-0027 (RBAC role via GET /auth/me)
  - backend/api/auth/dependency.py get_current_user (cookie path 優先)
  - frontend/lib/auth/index.ts (authMode 單一切換點)
---

# CH-013 — 前端通電真實登入（cookie-session auth 第三模式）

> **Spec version**：1.0（initial）
> **Owner**：AI（實作）/ Chris（approve）
> **Approved by**：Chris（2026-06-28 — chat「approved spec，同意 §2.4 root redirect：改成已登入導 /dashboard」）

## 1. Context (Why)

使用者 2026-06-28 回報：用 `admin@example.com` 登入後，右上角帳號區卻顯示 `dev-user (dev-user@ekp.local [mock])`、按 logout 沒反應、重訪 `localhost:3001` 又被導回 `/login`。經調查確認登入流程目前跑的是 **mock 模式**，並選定方向「**通電啟用真實登入**」（email/password 本地帳號）。

**關鍵調查結論——「通電」不是改兩個 flag，而是補一條前端漏接的線：**

- **後端與帳號全部 ready**：
  - `admin@example.com` 存在、`verified=true`、有 `password_hash`、`role=admin`（查 `ekp` DB `users` 表）。
  - cookie session 登入整條已實作：`POST /auth/login`（設 httpOnly `ekp_session` + `ekp_csrf` cookie）、`GET /auth/me`（靠 cookie 回傳 `{oid, tid, preferred_username, role, is_mock}`，`auth.py:155`）、`POST /auth/logout`（`auth.py:168`，revoke session + 清 cookie）、`get_current_user` 的 cookie path 優先（`dependency.py:65`）。皆符合 ADR-0022 hybrid auth 設計。
  - 傳輸層已 ready：`api-client.ts` 全程 `credentials:'include'`（帶 cookie），`buildAuthHeader()` 有 try/catch fallback 到 `{}`（MSAL skeleton throw 時靠 cookie），非 GET 自動帶 `X-CSRF-Token`（`api-client.ts:53-75`）。

- **前端缺口 = auth store 只認兩條身份來源（mock / MSAL），漏了「cookie session」這條**：
  - `lib/auth/index.ts:40-46` 的 `getCurrentUser/login` 只在 mock 與 MSAL 之間二選一。
  - `app/login/page.tsx:59` 的 email/password 登入成功後只 `router.push('/dashboard')`，**從未把身份填進 auth store**。
  - `lib/providers/auth-provider.tsx:62` mock 模式 mount 即 auto sign-in，登出後 `status` 回 `idle` 又**自動重新登入** → 這就是「logout 沒反應」的根因。
  - **MSAL 完全沒配置**（`msal_provider.ts:23-24`，`NEXT_PUBLIC_AZURE_CLIENT_ID`/`TENANT_ID` 為空字串），`getMsalInstance()` 在沒 config 時 throw。所以**單純把 `NEXT_PUBLIC_AUTH_MOCK=false` 會讓 auth-provider 走 MSAL → initMsal throw → 進 error state，使用者卡在 splash 進不去**（`auth-provider.tsx:86-95` catch 設 error；`login-gate.tsx:35` 顯示 Sign-in failed）。

- **`FEATURE_AUTH_ENABLED` 是 informational，不 gate 任何端點**：grep 全 backend，它只在 `settings.py:448`（default False）定義 + `langfuse_tracer.py` 記錄，**沒有任何端點用它做 auth gate**。真正決定「未帶憑證的請求是否 fallback 成 mock user」的開關是 `feature_auth_mock`（`dependency.py:86`）。故通電的後端開關 = `feature_auth_mock=false`，`FEATURE_AUTH_ENABLED` 可不動。

- **既有現成可重用**：`useRole()`（`lib/hooks/use-role.ts`）已透過 `usersApi.getMe()`（`lib/api/users.ts:110`，`GET /auth/me`，回傳 `MeResponse`）取 role。故本 change **重用 `usersApi.getMe()`，不需新增 API**。

**淨結果**：後端 + 帳號 + 傳輸層皆 ready，缺的只是前端把 cookie-session 身份接進 auth store + 修 logout/hydration/gate。這是完成 ADR-0022 既定 hybrid auth 的前端缺口，非引入新架構或新 vendor。

## 2. Scope (What)

### 2.1 Behavior Change

- **Before**：前端 auth 只有 mock 與 MSAL 兩態。dev 跑 mock（`NEXT_PUBLIC_AUTH_MOCK=true`）→ 自動以硬編碼 `dev-user@ekp.local [mock]` 登入；email/password 登入只設 cookie、不更新 store（右上角永遠 dev-user）；logout 被 mock auto re-login 蓋掉（看似無反應）；改 `NEXT_PUBLIC_AUTH_MOCK=false` 會走未配置的 MSAL → 卡 error。
- **After**：新增 **cookie-session（第三模式）**。`feature_auth_mock=false` + 前端 cookie 模式下，使用者用 email/password 經 `POST /auth/login` 登入 → 前端以 `GET /auth/me` 取回真實身份填 store → 右上角正確顯示 `Chris Lai` + admin role chip（非 dev-user [mock]）；重新整理受保護頁面會以 cookie 還原 session；logout 真正 revoke session + 清 store + 導回 `/login`，且不再 auto re-login；未登入訪問受保護頁面會被 gate 擋下。SSO（MSAL）路徑維持為未來 opt-in，不受影響。

### 2.2 In Scope

採 **重用既有後端端點 + 既有 `usersApi.getMe()`** 的 surgical 做法，後端 **不動 code**：

- **C11 前端 authMode 三態化**（`lib/auth/index.ts`）：
  - `authMode: 'mock' | 'cookie' | 'msal'`。判定：`NEXT_PUBLIC_AUTH_MOCK==='true'` → `mock`；否則 `NEXT_PUBLIC_AUTH_SSO==='true'` → `msal`；否則 → `cookie`（新預設）。
  - 理由：保持向後相容（目前無人設 `NEXT_PUBLIC_AUTH_SSO`，故關掉 mock 後落 `cookie` 而非未配置的 `msal`，避免卡 error）；未來啟用 SSO 設 `NEXT_PUBLIC_AUTH_SSO=true` 即切回 MSAL。
  - `getCurrentUser/getBearer/login/logout/refresh` 各新增 cookie 分支。
- **C11 cookie-session provider**（新檔 `lib/auth/cookie_session.ts`）：
  - `loginCookie()`：以現有 cookie 呼叫 `usersApi.getMe()` 取回身份（登入動作本身仍由 login page 表單的 `authApi.login` 完成並設 cookie）；做形狀映射 `preferred_username → preferredUsername`、`is_mock → isMock`（對齊前端 `AuthenticatedUser` type）。
  - `logoutCookie()`：`POST /auth/logout`（經 `apiClient.post`，自動帶 cookie + CSRF）。
  - `getCookieBearer()` / `getCookieUser()`：throw（cookie 模式無 bearer；同步介面無法 fetch，store 由 hydration 填）→ `api-client.ts` 既有 try/catch fallback 接住，靠 cookie 認證。
  - `refreshCookie()`：no-op（session TTL 7d，dev 無需 silent refresh；如需可後續接 `/auth/refresh`）。
- **C11 auth-provider hydration**（`lib/providers/auth-provider.tsx`）：
  - 新增 cookie 分支：mount 時嘗試**一次** `signIn()`（= `loginCookie` = getMe）還原 session；成功 → `authenticated` + 填 store；失敗（401 / ApiError）→ `idle`（未登入，gate 接手）。
  - 以 `useRef` guard 確保只 hydration 一次，**不**像 mock 那樣依 `status==='idle'` 無條件 re-login（否則 logout 又被蓋）。
- **C11 login page**（`app/login/page.tsx`）：`handleSelfSubmit` 在 `authApi.login` 成功後加 `await signIn()`（cookie 模式填 store）再 `router.push('/dashboard')`。
- **C11 logout redirect**（`components/auth/user-menu.tsx:139`）：`signOut()` 後 `router.push('/login')`（修「沒反應」）。
- **C11 login-gate**（`components/auth/login-gate.tsx`）：cookie 模式比照 MSAL —— `status==='authenticated'` 放行；hydration 中（loading）顯示 splash；未登入顯示 splash + Sign-in link（gate 行為與既有 MSAL 分支一致，不新增 redirect 迴圈風險）。
- **環境開關**：
  - `backend/.env`：`FEATURE_AUTH_MOCK=false`。
  - `frontend/.env.local`：`NEXT_PUBLIC_AUTH_MOCK=false`。
- **Tests**：UI auth 為前端，H6 不強制（H6 清單為 backend pipeline；本 change 後端 0 code 改動）。新增 `lib/auth/cookie_session.ts` 的形狀映射單元測試（純函式，可測），auth-provider hydration 行為以手動 live 驗為主（前端無 Vitest harness，per W7 D4 deferred）。

### 2.3 Out of Scope（explicit）

- ❌ **MSAL / Entra ID SSO 實際配置與登入**：無 Entra cred（留 Track A IT cred，W16 DD-6）。「Sign in with Microsoft」按鈕維持不可用，本 change 不碰。
- ❌ **後端 auth 端點 / schema / dependency 任何 code 改動**：已 ready，只改 `backend/.env` 一個 flag。
- ❌ **register / verify-email 流程**：已 ready，不動。`feature_email_mock` 維持現狀（dev 驗證碼印 log）。
- ❌ **RBAC role-gated view 大改**：沿用既有 `useRole()` + `RoleBadge`；本 change 只確保 cookie 模式下 `useRole` 與 store user 都被填。
- ❌ **eval harness / dev script 的 auth 適配**：見 §4 R1 —— `feature_auth_mock=false` 後，靠 mock dev-token 的 script 會 401，需另以 session bearer 或臨時開 mock，本 change 不一併改造（測試體驗 tradeoff 已知情）。
- ❌ **其他三個回報問題（#2 dashboard mock 數據 / #3 sidebar badge / #4 chat KB 選擇器）**：分別另案。
- ❌ **改 `docs/architecture.md` §1-14 frozen 內容**：只記 drift note（如需），不動 content lock。

### 2.4 Scope 抉擇（需 approve 時確認）— root `/` 已登入時是否導 `/dashboard`

使用者問題 #1d：登入後重訪 `localhost:3001` 仍被導回 `/login`。根因 = `app/page.tsx:19` root `/` 無條件 `redirect('/login')`（ADR-0024：移除 landing page）。通電後若不改 root，登入後重訪 root 仍回 login，易誤解為「登入沒保持」。

- **推薦 = 改 root server component 讀 `ekp_session` cookie**：cookie 存在 → `redirect('/dashboard')`，否則 → `/login`。小改（server component 讀 cookie，無 client 邏輯），直接解決 #1d 困惑。
- **替代 = 不改 root**：維持 `/ → /login`，向使用者說明這是 ADR-0024 設計、改用 `/dashboard` 為入口即可。

> **Approve 抉擇**：☑ 改 root 已登入導 /dashboard（推薦，Chris 2026-06-28）/ ☐ 維持 `/ → /login`

## 3. Acceptance Criteria

- [ ] `authMode` 三態正確：`NEXT_PUBLIC_AUTH_MOCK=true` → mock；`=false` 且無 `NEXT_PUBLIC_AUTH_SSO` → cookie；`NEXT_PUBLIC_AUTH_SSO=true` → msal。
- [ ] cookie 模式下，`admin@example.com` + 正確密碼 email/password 登入 → 跳轉 `/dashboard`，右上角顯示 `chris.lai`（display name 的 local part）+ admin RoleBadge，**不再**出現 `dev-user` / `[mock]`。
- [ ] 登入後重新整理 `/dashboard`（或任何受保護頁）→ 維持登入（`GET /auth/me` 以 cookie 還原），不被踢回 `/login`。
- [ ] 按 Sign out → `POST /auth/logout` 成功、store 清空、導向 `/login`，且**不會**自動 re-login（停在 login 頁）。
- [ ] 登出後直接打 `/dashboard` → 被 login-gate 擋（splash + Sign-in link，或 §2.4 採用後 root 導向）。
- [ ] 未登入呼叫受保護端點（如 `/kb`）→ 401（`feature_auth_mock=false` 生效，不再 fallback mock user）。
- [ ] 錯誤密碼 → toast「Email or password is incorrect」（既有 `INVALID_CREDENTIALS` 分支不破）。
- [ ] （若採 §2.4 推薦）登入後訪問 `localhost:3001` → 導 `/dashboard`；未登入 → 導 `/login`。
- [ ] `lib/auth/cookie_session.ts` 形狀映射單元測試通過（snake→camel）。
- [ ] `ruff` 不涉（無 backend code 改）；前端 `eslint` + `tsc --noEmit`（改動檔）clean。
- [ ] 既有 mock 模式回歸：把 env 切回 `NEXT_PUBLIC_AUTH_MOCK=true` + `FEATURE_AUTH_MOCK=true` → 行為與今日一致（auto sign-in dev-user）。

## 4. Risks

| # | Risk | Likelihood | Impact | Mitigation |
|---|---|---|---|---|
| R1 | `feature_auth_mock=false` 後，靠 mock dev-token 的 eval / dev script（per memory chat-demo-followups 用 `Bearer dev-token`）一律 401 | High | Med | §2.3 明確 out of scope + 知情記錄；dev script 需改用真實 session bearer（`POST /auth/login` 取 `access_token`）或跑 eval 時臨時 `FEATURE_AUTH_MOCK=true`；本 change 聚焦 UI 登入體驗 |
| R2 | auth-provider hydration 迴圈（mount effect 反覆呼叫 getMe / 登出後又 hydration）| Med | High | `useRef` guard 只 hydration 一次；登出 = 明確 set idle + redirect 離開 (app) gate；不依 `status==='idle'` 觸發（與 mock 分支區隔）|
| R3 | user 形狀映射錯（snake/camel）→ 右上角空白 / `Signing in…` 卡住 | Low | Med | 明確 `mapMe()` 映射 + 單元測試；live 驗右上角顯示 |
| R4 | 登出後 mock-style auto re-login 殘留導致 logout 仍無效 | Med | High | cookie 分支**不**抄 mock auto sign-in；acceptance 明列「登出停在 login 頁」|
| R5 | logout 是 POST 需 CSRF；漏帶 `X-CSRF-Token` → 403 | Low | Med | 經 `apiClient.post` 自動帶 `getCsrfHeaders()`（既有機制）；live 驗 logout 200 |
| R6 | 切 env 後忘記重啟 backend / frontend，跑 stale flag（per memory stale-backend）| Med | Med | 實作後依 ekp-restart 重啟 backend（殺 dual-process）+ frontend（wipe `.next`），再 live 驗 |
| R7 | 其他既有測試帳號（`chris.lai@rapo.com.hk`, role=user）登入後 RBAC 行為差異 | Low | Low | 非本 change 引入；role-gated view 沿用既有 useRole；admin 帳號為主驗證對象 |

## 5. Effort Estimate

~0.5–1 day（前端：index.ts 三態 + cookie_session.ts 新檔 + auth-provider hydration + login page + user-menu redirect + login-gate + 可選 root；env 2 行；cookie_session 單元測試；ekp-restart + live 驗一輪）。後端 0 code（1 行 env）。

## 6. Dependencies

- 帳號 `admin@example.com`（verified + 密碼）已 ready；後端 `/auth/login` `/auth/me` `/auth/logout` + cookie path 已 ready；`usersApi.getMe()` 已存在。無外部 / OQ 阻塞。
- 無新 vendor / 無新 npm dep（重用既有 `@azure/msal-browser` 不啟用、TanStack Query / Zustand 既有）。
- 跨 component：僅 C11。
- **非 H1**：無加/刪 architecture.md §3/§4 component；無 vendor swap；無 storage layout 改動；無 multi-KB arch 改動；無 8-view layout philosophy 改動；無 Tier 2 feature。屬完成 ADR-0014/0022 既定 hybrid auth 之前端缺口（後端早已實作）。→ **無新 ADR**。
- **H7 評估**：UserMenu / login-gate 視覺維持 mockup（`ekp-shell.jsx` UserMenu / `ekp-page-auth.jsx`）；本 change 只把顯示資料由 mock 換成真實身份 + 加 logout redirect，**無 layout / spacing / typography / color 改動**，視覺輸出不變（甚至更貼近 mockup —— 顯示真實帳號而非 dev-user）。→ **非 H7 trigger**（屬資料正確化，非 redesign）。實作時仍逐項對齊 UserMenu mockup。
- **H5**：不 log 密碼 / session token 到 plaintext；session 經 httpOnly cookie（既有 ADR-0022）；env flag 非 secret。
- **H6**：後端 0 code 改動，不觸發強制覆蓋；前端 auth 為 nice-to-have test。

## 7. Spec Changelog（deviation log）

| Date | Change | Reason | Approver |
|---|---|---|---|
| 2026-06-28 | Initial draft（status proposed）| 使用者回報登入後顯示 dev-user [mock] / logout 無反應 / 重訪回 login，選定「通電啟用真實登入」；調查確認需補前端 cookie-session 缺口（非改 flag），後端 + 帳號已 ready | (待 approve) |
| 2026-06-28 | status proposed → approved；§2.4 = 改 root 已登入導 /dashboard | Chris chat「approved spec，同意 §2.4 root redirect：改成已登入導 /dashboard」 | Chris |

---

**Lifecycle reminder**：呢份 spec locked after status=approved。重大 deviation → §7 changelog。**未 approve 前不 implement（PROCESS.md R1.change）。**
