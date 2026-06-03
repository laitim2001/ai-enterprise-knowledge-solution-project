---
bug_id: BUG-032
title: "/login(及 AppShell)theme-toggle icon SSR/client hydration mismatch — server `<Layers>` vs client `<Sparkles>` 令 React 丟棄整棵 server tree(11 console errors)"
severity: Sev3
status: done
reported: 2026-06-03
reporter: "用戶(chat 2026-06-03 — 「http://localhost:3001/login 一直登錄不了,幫我調查原因和處理它」)"
affects_components: [C11, C09]    # C11 auth/login UI(auth-frame)+ C09 AppShell(nav/theme-toggle)
spec_refs:
  - CLAUDE.md §5.7 H7        # Design fidelity — fix 不改 visual output(非 trigger)
  - CLAUDE.md §1.3           # Surgical changes
  - architecture.md §5.0     # Auth views + AppShell
related: [BUG-023]           # 另一宗 hydration bug(CitationPill `<div>` in `<p>`)
---

# BUG-032 — /login theme-toggle icon hydration mismatch

> **Report version**:1.0(initial)
> **Triage approver**:AI self-triaged **Sev3** — `/login` 首次 SSR 載入時 console emit 11 個 React error(根源係單一 theme-toggle icon hydration mismatch),令 React 丟棄整棵 server HTML 改用 client render。登錄兩條路徑(SSO + email/password)functionally 仍 work,但首次互動喺重繪完成前唔穩定 + console noise persistent。用戶感知為「一直登錄唔到」。

## 1. Symptom

```
[Frontend Console — http://localhost:3001/login 首次 full-load]
Warning: Prop `d` did not match.
  Server: "M12.83 2.18a2 2 0 0 0-1.66 0L2.6 6.08...z"   ← lucide <Layers> path
  Client: "M9.937 15.5A2 2 0 0 0 8.5 14.063...z"        ← lucide <Sparkles> path
    at path
    at svg (lucide-react Icon)
    at button
    at AuthFrame (components/auth/auth-frame.tsx)
    at LoginPage (app/login/page.tsx)
...
Error: Hydration failed because the initial UI does not match what was rendered on the server.
Error: There was an error while hydrating. Because the error happened outside of a Suspense
       boundary, the entire root will switch to client rendering.
```

打開 `/login` console 共 11 個 error,全部源自同一個根:theme-toggle 按鈕嘅 lucide icon 喺 server 同 client 渲染唔同 SVG path,觸發 hydration mismatch → React 丟棄 server tree。用戶體驗:頁面首次載入閃爍重繪,首次撳「Sign in」喺重繪完成前可能無反應。

## 2. Reproduction Steps

1. 確保 system / 瀏覽器偏好係 **dark mode**(令 client resolvedTheme=`dark`,與 server 預設 `light` 不一致)
2. 瀏覽器 full-load `http://localhost:3001/login`(非 client-side navigation)
3. 打開 DevTools console
4. **觀察**:11 個 hydration error,第一個係 `Prop d did not match`(Layers vs Sparkles SVG path)
5. **觀察**:頁面右上角 theme-toggle icon 短暫閃爍(server `<Layers>` → client `<Sparkles>`)

## 3. Root Cause

`AuthFrame`(`frontend/components/auth/auth-frame.tsx`)同 `ThemeToggle`(`frontend/components/nav/theme-toggle.tsx`)用同一個 pattern 選擇 theme-toggle icon:

```jsx
const isDark = resolvedTheme === 'dark';   // resolvedTheme 來自 next-themes useTheme()
...
{isDark ? <Sparkles size={14} /> : <Layers size={14} />}
```

`next-themes` 嘅 `resolvedTheme` **只喺 client 解析**(讀 localStorage `theme` key + 系統 `prefers-color-scheme`),SSR 階段一律係 `undefined`。於是:

- **Server render**:`isDark = (undefined === 'dark') = false` → `<Layers>`(server HTML `d="M12.83 2.18...z"`)
- **Client hydrate**:若用戶係 dark mode → `resolvedTheme = 'dark'` → `isDark = true` → `<Sparkles>`(client `d="M9.937 15.5...z"`)
- SVG `d` 對唔上 → React hydration mismatch → 因為發生喺 Suspense boundary 外,整棵 root 切換 client render(其餘 10 個 error 係呢個串聯失敗)

`/login` 直接 SSR full-load 所以暴露;dashboard 嘅 `ThemeToggle` 多數經 client-side navigation 進入(mock auto-sign-in → router.push),未必每次 hydrate,但同樣帶住潛在 bug。

**為何唔係「真係登錄唔到」**:實測 SSO(`loginMock`)+ email/password(`POST /auth/login` 正確回 401 invalid_credentials)兩條路徑 functionally 都正常。Hydration 只影響首次互動穩定性 + console noise,並非永久 block 登錄。

## 4. Scope

- ✅ Frontend `components/auth/auth-frame.tsx` — 加 mounted guard(`useState(false)` + `useEffect(()=>setMounted(true),[])`),`isDark = mounted && resolvedTheme === 'dark'`
- ✅ Frontend `components/nav/theme-toggle.tsx` — 同一 guard(用戶 explicit 要求一併修同 pattern)
- ✅ Visual fidelity preserve(per CLAUDE.md §5.7 H7)— icon 最終顯示完全一樣,只係首次 client render 對齊 server(`<Layers>`),mounted 後切換正確 icon
- ✅ Toggle 行為 preserve(`setTheme` onClick / title / aria-label unchanged)
- ❎ Out of scope:其他用 `resolvedTheme` 嘅組件(`sonner.tsx` 用 `theme` 而非條件渲染 icon,無 mismatch 風險)

## 5. Severity Rationale

**Sev3** per PROCESS.md §4.5 —

- 兩條登錄路徑 functionally OK,無 data loss / 無 auth bypass → 唔係 Sev1/Sev2
- 但 login 係 critical surface + console 11 errors persistent + 首次互動穩定性受影響 + hydration full client-render 有效能 cost → 唔係 Sev4 cosmetic
- Hydration mismatch 屬 **recurring pattern**(cf. BUG-023 `<div>` in `<p>`)— postmortem per §4.5 Sev3「encouraged if pattern recurring」;本次 root cause trivial + surgical fix,先 skip postmortem,pattern 已記入本 report §3 + RISK 觀察(下方 §7）

## 6. Acceptance for Fix

- [x] **T1** — `auth-frame.tsx` theme-toggle icon mounted-guarded,首次 client render = server(`<Layers>`)
- [x] **T2** — `nav/theme-toggle.tsx` 同一 guard
- [x] **T3** — `/login` full-load console hydration error **11 → 0**(Playwright 實測)
- [x] **T4** — SSO 登錄修復後仍成功跳 `/dashboard`(Playwright 實測,zero regression)
- [x] **T5** — Visual zero regression(右上角 theme icon mounted 後正確顯示 Sparkles@dark — 截圖確認)
- [x] **T6** — `tsc --noEmit` exit 0 + `eslint`(兩檔)exit 0(已 run）

## 7. Related

- BUG-023(另一宗 hydration bug,CitationPill popover `<div>` in `<p>`)— 同屬 SSR/hydration correctness pattern
- `notifications-menu.tsx:145` — 既有 mounted-guard pattern,本 fix 沿用
- CLAUDE.md §5.7 H7(no visual change — mounted guard 不改最終 icon)
- CLAUDE.md §1.3 surgical(2 檔 × 3 行,zero 架構變化)
- **Pattern watch**:任何「條件渲染依賴 `next-themes` resolvedTheme / localStorage / 系統偏好」嘅組件,SSR 都會 mismatch — 必須 mounted guard
