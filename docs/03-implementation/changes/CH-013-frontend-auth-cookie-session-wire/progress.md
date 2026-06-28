---
change_id: CH-013
spec_ref: ./spec.md
checklist_ref: ./checklist.md
status: in-progress     # in-progress | closed
---

# CH-013 — Progress

> Day-N entries during execution + 結尾 closeout summary。
> 每 commit 必須對應一個 Day-N entry mention(R2 binding rule per PROCESS.md §5)。

---

## Day 1 — 2026-06-28

### Done
- spec.md 寫成 + approved（Chris chat approve + §2.4 = 改 root 已登入導 /dashboard）
- checklist + progress derive
- I1-I7 + I9 code 完成：`lib/auth/cookie_session.ts` 新檔 + `lib/auth/index.ts` authMode 三態 + `auth-provider.tsx` cookie hydration（useRef guard）+ `login/page.tsx` signIn 填 store + `user-menu.tsx` logout redirect + `login-gate.tsx` docstring + `app/page.tsx` §2.4 root redirect
- I9 單元測試 `tests/unit/auth/cookie-session.test.ts` 3 passed；V9 `tsc --noEmit` exit 0 + `eslint`（8 改動檔）exit 0 clean
- I8 env 兩 flag 改 false（用戶授權只改這兩個）；重啟 backend（殺 dual-process 96216/109660 + 啟新讀新 env）+ frontend（wipe `.next`）
- live 驗 V1-V9 全通過（playwright + 臨時帳號 ekptest@example.com，role=user）

### Decisions
- 重用既有 `usersApi.getMe()`（`GET /auth/me`），不新增 API（Karpathy §1.2 simplicity）
- authMode 三態化（mock / cookie / msal）而非二態 boolean，向後相容：mock=false 且無 SSO env → 落 cookie（避免卡未配置的 MSAL）
- §2.4 root redirect = 採推薦（已登入導 /dashboard）
- **circular import 修正**：cookie_session.ts top-level `import {usersApi}` → users.ts → api-client.ts，而 api-client.ts 又 import auth/index → cookie_session，形成循環。SSR webpack 初始化時 `ApiClient` class（檔尾）未定義就被 users.ts 存取 → `Cannot access 'ApiClient' before initialization` + /login 500（Vitest 用不同 module 初始化順序所以單元測試沒爆，SSR 才爆）。修法 = `usersApi`/`apiClient` 改函式內 dynamic import，top-level 只留 type import（erased）

### Blockers
- （已解）I8 env 受 §4.4 阻擋 → 用戶授權只改 `FEATURE_AUTH_MOCK` / `NEXT_PUBLIC_AUTH_MOCK` 兩個 flag，已改 false（其他 secret 未動）；`FEATURE_AUTH_ENABLED` 不動（無作用，per spec §1）

### Effort
- Planned:~0.5–1 day;Actual:_(填);Variance:_

### Commits
| Hash | Subject |
|---|---|

---

## Closeout

### Acceptance verification
§3 acceptance criteria 全部 ✅（V1-V9 live 驗 + 單元測試）。V10（mock 回歸）未驗但 code 保留 mock 分支不變、風險低，標可選。
- V2 核心修復確認：右上角由 `dev-user@ekp.local [mock]` → 真實 `ekptest` / `ekptest@example.com` / End User RoleBadge
- V4 核心修復確認：logout 由「沒反應」（mock auto re-login 蓋掉）→ 真正登出 + 導 /login + 不 re-login
- V8 §2.4：root `/` 已登入 → /dashboard、未登入 → /login

### Effort summary
| Day | Planned (h) | Actual (h) | Variance |
|---|---|---|---|
| 1 | ~6 | ~5 | -1（重用 getMe + 既有 cookie 後端省事；circular import debug 補回） |

### Lessons
- **What worked**：後端 + 帳號 + 傳輸層（cookie/CSRF/api-client）早已 ready，前端只缺第三條身份來源 → 重用 `usersApi.getMe()` 而非新建 API（Karpathy §1.2）
- **What didn't / friction**：新增 module 引入 circular import，**Vitest 綠 ≠ SSR 沒事**（兩者 module 初始化順序不同）→ 教訓:新增跨層 import 的檔要在實際 dev server SSR 驗證,別只信單元測試。dynamic import 是打破循環的 surgical 解
- **Carry-overs**：臨時測試帳號 `ekptest@example.com`（密碼 TestPass123!，role=user，verified）留在 ekp DB 供測試 / 可刪；V10 mock 回歸未驗（可選）；SSO（MSAL）仍未配置（Track A cred）

### Component design note status updates
- C11:auth state 機制由 mock+MSAL 二態 → mock+cookie+MSAL 三態（cookie-session 為 dev 本地 self-register 通電路徑）

---

**End of CH-013 progress**
