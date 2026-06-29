---
bug_id: BUG-038
report_ref: ./report.md
checklist_ref: ./checklist.md
status: closed          # in-progress | closed
---

# BUG-038 — Progress

> Investigation → fix → verify timeline。每 commit 對應 Day-N entry(R2)。

---

## Day 1 — 2026-06-29(triage + 診斷,未動 code)

### Done
- 用戶報告:已登入但 loading 期間顯示「Sign in to continue」。
- Grep 定位 `frontend/components/auth/login-gate.tsx:50`;讀 `login-gate.tsx` + `auth-provider.tsx` 確認根因(見 report §4)。
- AskUserQuestion 收斂:修法範圍 = **範圍 A 只修 loading(最小)**;流程 = **開正式 BUG-NNN 文件**。
- 建 BUG-038 三件套(report status=triaged,未動 code)。

### Diagnosis update
- 根因確認:`login-gate.tsx` CTA(line 46-51)不分狀態永遠顯示;`loading`(正在還原,可能已登入)同 `idle`/`error`(確定未登入)共用同一 splash 分支 → 已登入用戶 hydration 期間被閃 CTA。

### Decisions
- **D1 範圍 A**(用戶揀):只修 `login-gate.tsx` loading 分支純 spinner;初始 idle 第一幀 micro 閃爍 out-of-scope。
- **D2 非 H7 trigger**:login-gate 係 auth infra splash 無 mockup 對應,修為 reverse-drift。
- **D3 spec approval gate**:report status=triaged,**STOP 等用戶 approve** 先 flip fixing 動 code。

### Blockers
- ~~**B1(blocked-on-user)**:等用戶 review + approve report → 先開始 Fix 階段。~~ **RESOLVED 2026-06-29**:用戶 approve 範圍 A,Fix 階段完成。

### Effort
- Planned:fix ~0.3h;Actual:~0.3h(fix 一檔 + regression test + 三項驗證);Variance:≈0。

### Commits
| Hash | Subject |
|---|---|
| _(待用戶自行 commit)_ | `fix(frontend): login-gate loading shows neutral spinner, not sign-in CTA (C11, BUG-038)` |

---

## Day 1(cont)— 2026-06-29(fix + verify + closeout)

### Done
- **Fix(範圍 A)landed**:`login-gate.tsx` 新增 `status === 'loading'` 分支(`:44-50`),只 render 置中純 spinner,**唔 render**「Sign in to continue」CTA;置於 `mock || authenticated` pass-through 之後、idle/error(spinner + CTA)分支之前。idle/error 分支(`:52-68`)維持不變。
- **git diff 核實 fix 真實落 disk**(非 Edit 回報 — 上個 session tool-result 污染教訓):working tree 對 HEAD diff 只新增 loading 分支 + 6 行 docstring comment,surgical 單檔。
- **Regression test**:`tests/unit/login-gate.test.tsx`,4 case 覆蓋全 `AuthStatus`(loading→無 CTA+有 spinner+children gated / idle→有 CTA / error→有 CTA+「Sign-in failed」/ authenticated→pass-through)。
- **三項驗證全綠**:`tsc --noEmit` exit 0;`eslint`(login-gate + test)exit 0;`vitest` **4/4 pass**(50.85s,今次冇撞 W87 worker 60s timeout)。

### Decisions
- **D4 manual browser smoke deferred**:W87 OneDrive 環境(next dev 首編 ~135s + Fast Refresh 唔可靠需重啟 frontend);渲染邏輯已由 vitest 4-case regression 覆蓋,manual 留待用戶按需 browser 確認(report §7 T5 / checklist Verification 末項)。

---

## Closeout

- **根因**:`login-gate.tsx` 把「Sign in to continue」CTA 同 spinner 綁喺同一個 `status !== 'authenticated'` 分支,令 cookie hydration(`status === 'loading'`,`GET /auth/me` in-flight)期間已登入用戶被閃 CTA。
- **修法**:範圍 A 最小 surgical — 抽出 `loading` 分支顯示純 spinner(無 CTA);`idle`/`error`(確定未登入)維持 CTA。語意上把「正在還原(可能已登入)」同「確定未登入」分流。
- **驗證**:vitest 4/4 + tsc/eslint exit 0;manual browser smoke deferred(W87)。
- **H7**:非 trigger — auth infra splash 無 mockup 對應,本修為 reverse-drift(令行為更正確)。
- **無 regression**:idle/error 路徑 CTA 不變;authenticated pass-through 不變。
- **Sev4 → 無 postmortem**(per PROCESS.md §4.5)。
- **待用戶自行 commit**(本 session 不 commit)。

---

**End of BUG-038 progress — CLOSED 2026-06-29(fix landed + 驗證全綠;manual browser smoke deferred per W87;待用戶 commit)**
