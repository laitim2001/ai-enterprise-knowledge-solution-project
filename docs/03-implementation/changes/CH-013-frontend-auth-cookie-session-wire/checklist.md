---
change_id: CH-013
spec_ref: ./spec.md
status: done     # in-progress | done
last_updated: 2026-06-28
---

# CH-013 — Checklist

> Atomic checkbox items derived from `spec.md` §3 acceptance criteria。每 item ≤ 1-2h effort。
> AI tick 完成嘅 item;唔可以 tick 嘅 item 喺 progress Day-N entry 寫原因。

## Implementation

- [x] I1 — `lib/auth/cookie_session.ts` 新檔：`mapMe()`（snake→camel）+ `loginCookie()`（重用 `usersApi.getMe()`）+ `logoutCookie()`（POST /auth/logout）+ `getCookieBearer()`/`getCookieUser()`（throw）+ `refreshCookie()`（no-op）。**循環 import 修正**：`usersApi`/`apiClient` 改函式內 dynamic import（top-level 只留 type import）
- [x] I2 — `lib/auth/index.ts`：`authMode` 三態（mock / cookie / msal）+ `getCurrentUser`/`getBearer`/`login`/`logout`/`refresh` 接 cookie 分支
- [x] I3 — `lib/providers/auth-provider.tsx`：cookie 分支 mount 一次 hydration（`useRef` guard，不依 `status==='idle'` re-login）；成功 authenticated / 401 idle
- [x] I4 — `app/login/page.tsx`：`handleSelfSubmit` 成功後 `await signIn()` 填 store 再 `router.push('/dashboard')`
- [x] I5 — `components/auth/user-menu.tsx`：`signOut()` 後 `router.push('/login')`
- [x] I6 — `components/auth/login-gate.tsx`：cookie 模式比照 MSAL（既有邏輯已 cover）→ 只更新 docstring
- [x] I7 — `app/page.tsx`（§2.4）：root 讀 `ekp_session` cookie → 有則 `redirect('/dashboard')`，否則 `/login`
- [x] I8 — env：`.env`（根目錄 line 105）`FEATURE_AUTH_MOCK=false` + `frontend/.env.local`（line 12）`NEXT_PUBLIC_AUTH_MOCK=false`（用戶授權只改這兩個 flag）
- [x] I9 — `cookie_session.ts` `mapMe()` 形狀映射單元測試（`tests/unit/auth/cookie-session.test.ts`，3 passed）

## Verification

- [x] V1 — authMode cookie 模式生效（/login 正常渲染，無走 MSAL error）
- [x] V2 — ekptest@example.com 登入 → /dashboard，右上角顯示 ekptest + End User RoleBadge，dropdown 顯示 ekptest@example.com，**無 dev-user / [mock]**
- [x] V3 — reload /dashboard → 維持登入（/auth/me cookie 還原，user menu 仍顯示 ekptest）
- [x] V4 — Sign out → 導 /login + 等 3s 不 auto re-login（修掉原 mock 「沒反應」）
- [x] V5 — 登出後打 /dashboard → 被 gate 擋（只顯示 splash「Sign in to continue」）
- [x] V6 — 未登入打 /kb → 401（feature_auth_mock=false 生效；舊 dev-token 也失效 503）
- [x] V7 — 錯誤密碼 → POST /auth/login 401 + 仍停 /login（INVALID_CREDENTIALS toast 分支）
- [x] V8 — root redirect：登入後 / → /dashboard；登出後 / → /login（雙向正確）
- [x] V9 — 前端 `tsc --noEmit`（exit 0）+ `eslint`（exit 0）改動檔 clean
- [ ] V10 — mock 模式回歸（env 切回 true）→ 未驗（code 保留 mock 分支不變，風險低；非通電目標，可選）

## Cross-Cutting

- [ ] Each commit references `progress.md` Day-N entry(R2) → 待用戶確認是否 commit
- [ ] Component tag in commit message per CC-1（`feat(frontend): ... (C11)`）→ 待 commit
- [x] 非 H1 → 無 ADR（per spec §6）；非 H7 → 無 mockup visual 改動（user-menu 只改 logout handler）
- [x] `progress.md` closeout summary written
- [ ] `progress.md` frontmatter status flipped to `closed` → 待 commit 後

---

**Lifecycle reminder**:呢份 checklist 隨 spec acceptance criteria 衍生。新加 item 必須先入 spec + changelog,然後再加 checklist。
