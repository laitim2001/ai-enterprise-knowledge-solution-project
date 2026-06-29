---
bug_id: BUG-038
title: "已登入用戶喺 cookie session hydration 期間,login-gate 仍顯示「Sign in to continue」CTA"
severity: Sev4          # cosmetic / UX — 無功能損壞、無 console error、無資料風險
status: done            # triaged → fixing → verifying → done(用戶 2026-06-29 approve 範圍 A → fix landed + 驗證全綠)
reported: 2026-06-29
reporter: "用戶(chat 2026-06-29 — 「頁面在 loading 時顯示的文字不太正確,現在是顯示 sign in to continue,但是明明已經是登入了」)"
affects_components: [C11]      # auth state context + login-gate(app route group gate)
spec_refs:
  - architecture.md §5.0       # Application Shell + auth gate(W18 F2)
  - CLAUDE.md §5.7 H7          # non-trigger — infra splash 無 mockup 對應 + reverse-drift fix
related: [BUG-032]             # 另一宗 C11 login/auth surface 顯示 bug;CH-013 cookie session 模式
---

# BUG-038 — login-gate loading 期間顯示多餘 sign-in CTA

> **Report version**:1.1(2026-06-29 fix landed → `done`;v1.0 = initial triage)
> **Triage**:AI self-triaged **Sev4**,修法範圍由用戶 2026-06-29 AskUserQuestion 揀「範圍 A 只修 loading(最小)」+ approve(per `feedback_change_spec_approval_gate` + PROCESS.md §4)。**Fix 已 landed + 驗證全綠**(見 §7 + §8 changelog)。

## 1. Symptom

已登入用戶**刷新 / 直接進入**任何 (app) 內頁時,頁面 loading 期間左中央轉圈,**同時**顯示一條「Sign in to continue」連結 —— 但用戶其實已經登入,唔應該見到要求登入嘅 CTA。

## 2. Reproduction Steps

1. 確保 authMode = `cookie`(CH-013,mock off + SSO off — 即當前 `feat/auth-cookie-session-wire` branch 預設)
2. 以 valid 帳號登入(httpOnly `ekp_session` cookie 已存在)
3. 喺任何 (app) 內頁(如 `/dashboard`)按 **F5 刷新**(或直接 deep-link 該 URL)
4. **觀察**:頁面還原身份期間,中央 spinner **連同**「Sign in to continue」link 一齊出現,直到 `GET /auth/me` 回應、`status` 轉 `authenticated` 先消失

**Reproduction reliability**:Always(每次刷新已登入頁面皆重現;hydration 越慢越明顯)

**Environment**:local dev,cookie session 模式(authMode=`cookie`)。real MSAL 模式同樣受影響(init 期間 status=loading)。mock 模式不受影響(gate 直接 pass-through)。

## 3. Expected vs Actual

- **Expected**:身份還原(hydration)期間係「未知結果」狀態 —— 用戶可能已登入,gate 應只顯示中性 loading(spinner),**唔應該**顯示「Sign in to continue」CTA。確定未登入(hydration 後 401)先顯示 sign-in link。
- **Actual**:`login-gate.tsx:46-51` 嘅「Sign in to continue」link **不分狀態永遠顯示**(只要 `status !== 'authenticated'`),連 `loading` 期間都出。

## 4. Root Cause

`LoginGate`(`frontend/components/auth/login-gate.tsx`)只分兩路:

```tsx
if (authMode === 'mock' || status === 'authenticated') return <>{children}</>;
// 否則(idle / loading / error)→ 同一個 splash:
//   error → 錯誤文字;else → spinner
//   + 永遠 render <Link href="/login">Sign in to continue</Link>   ← 不分狀態
```

而 `auth-provider.tsx` 嘅狀態機(cookie 模式,line 80-90):mount → `status: 'loading'` → `GET /auth/me` 從 cookie 還原 → 成功 `authenticated` / 失敗(401)`idle`。

問題核心:**`loading`(正在還原,可能已登入)同 `idle`/`error`(確定未登入)共用同一個 UI 分支**,所以已登入用戶喺 hydration in-flight 期間被閃 sign-in CTA。`status` 嘅 `loading` 同 `idle` 語意冇喺 gate 區分。

> 次要:`status` 初始值係 `idle`,`AuthProvider` 嘅 effect 喺首次 paint 之後先設 `loading`,故第一幀會 paint 一下 CTA(極短 micro 閃爍)。用戶 2026-06-29 揀範圍 A(只修 loading),此 micro 閃爍**不在本 BUG scope**(若需要徹底消除,屬另一決定 — 加 hydrated flag,記 §7)。

## 5. Scope(範圍 A — 用戶 2026-06-29 揀「只修 loading,最小」)

- ✅ `frontend/components/auth/login-gate.tsx` — 新增 `status === 'loading'` 分支:純 spinner,**唔 render** 「Sign in to continue」link
- ✅ `idle` / `error` 維持原顯示(error 文字 / spinner + sign-in link)— 確定未登入仍見 CTA,無 regression
- ✅ Visual:`authenticated` pass-through 不變;真正未登入路徑不變;只係 loading 期間由「spinner + CTA」變「純 spinner」
- ❎ Out of scope:初始 idle 第一幀 micro 閃爍(需動 `auth-provider` 加 hydrated flag — 用戶揀範圍 A 不做)
- ❎ Out of scope:docstring TODO(W16)`router.replace('/login')` auto-redirect(等 MSAL cred Track A)

**H7 註**:`login-gate` 係 (app) route group 嘅 auth infra splash,**無對應 design-mockup 頁面**;本修為 reverse-drift(令行為更正確,loading 純 spinner 不偏離任何 mockup)→ **非 H7 trigger**(per §5.7「修正 visual drift bug → reverse direction」例外)。

## 6. Severity Justification

**Sev4** per PROCESS.md §4.5 —

- 純 cosmetic / UX:登入功能完全正常(hydration 成功就入頁),**無**功能損壞、**無** auth bypass、**無** console error、**無**效能 cost、**無**資料風險 → 唔係 Sev1/Sev2/Sev3
- 影響面:已登入用戶每次刷新內頁短暫見到誤導 CTA(觀感問題)→ 屬 cosmetic Sev4
- (對比 BUG-032 評 Sev3:嗰宗有 11 個 console error + hydration full client-render 效能 cost;本宗純多餘 link 顯示,故低一級)

## 7. Acceptance for Fix(checklist preview)

- [x] **T1** — `login-gate.tsx` 加 `status === 'loading'` 純 spinner 分支(無 CTA)— landed(`login-gate.tsx:44-50`,git diff 核實)
- [x] **T2** — `idle` / `error` 維持顯示 sign-in link(確定未登入無 regression)— 不變(`login-gate.tsx:52-68`)
- [x] **T3** — Regression test(vitest):`useAuthStatus` 回 `loading` → 無「Sign in to continue」;回 `idle`/`error` → 有;`authenticated` → pass-through。**4/4 pass**(`tests/unit/login-gate.test.tsx`,50.85s)
- [x] **T4** — `tsc --noEmit` exit 0 ✓ + `eslint`(login-gate.tsx + test)exit 0 ✓
- [ ] **T5**(user-facing manual)— **deferred**:browser smoke 受 W87 OneDrive 環境制約(next dev 首編 ~135s + Fast Refresh 唔可靠需重啟 frontend)。渲染邏輯已由 T3 vitest 4-case regression 覆蓋(loading 純 spinner 無 CTA / idle / error / authenticated);留待用戶按需 browser 確認

## 8. Report Changelog

| Date | Change | Reason | Approver |
|---|---|---|---|
| 2026-06-29 | Initial triage(Sev4,範圍 A,status=triaged 未動 code) | 用戶報告 + AskUserQuestion 揀範圍 A + 開正式 BUG 文件 | 用戶(2026-06-29) |
| 2026-06-29 | 用戶 approve 範圍 A → fix landed(`login-gate.tsx` loading 純 spinner 分支)+ regression test 4/4 pass + tsc/eslint exit 0 → status `triaged`→`done` | 修法已批准,實作完成且驗證全綠(manual browser smoke 因 W87 OneDrive 環境 deferred,vitest 覆蓋核心邏輯) | 用戶(2026-06-29) |

---

**Lifecycle reminder**:Sev4 → 無 postmortem 需求(per PROCESS.md §4.5,只 Sev1/Sev2 mandatory)。
