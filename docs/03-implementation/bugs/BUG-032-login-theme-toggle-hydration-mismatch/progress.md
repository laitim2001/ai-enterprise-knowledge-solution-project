---
bug_id: BUG-032
report_ref: ./report.md
checklist_ref: ./checklist.md
status: closed
---

# BUG-032 — Progress

> Investigation → fix → verify timeline。

---

## Day 1 — 2026-06-03

### Done
- 用戶報「`http://localhost:3001/login` 一直登錄唔到」→ 起步先排查基礎設施(端口 / backend health / proxy / env)
- 釐清 3001 係正確前端(Next.js dev,3000 被 Docker `com.docker.backend` + `wslrelay` 佔用 → 自動 fallback),非問題本身
- Backend(8000)`/health` 200 全綠;proxy `/api/backend → localhost:8000` + mock 模式(`NEXT_PUBLIC_AUTH_MOCK=true`)配置正確
- Playwright full-load `/login` → 重現 **11 console errors**
- 兩條登錄路徑實測:SSO(`loginMock`)成功跳 `/dashboard`;email/password 經 proxy 正確送後端,回 `401 auth.invalid_credentials`(無效測試帳號 → 預期行為,非 bug)
- Fix:`auth-frame.tsx` + `nav/theme-toggle.tsx` 加 mounted guard
- Verify:console error 11 → 0;SSO 登錄仍 work;視覺零 regression(截圖)

### Diagnosis update
- 初始假設:基礎設施 / backend down → **反證**(全綠)
- 第二假設:登錄系統 functionally broken → **反證**(SSO 成功、email path 正確回 401)
- 確認 root cause:單一 theme-toggle icon hydration mismatch(`next-themes` resolvedTheme @ SSR undefined → server `<Layers>` vs client `<Sparkles>`)令 React 丟棄整棵 server tree;11 errors 全部源自呢一個根

### Decisions
- 修法揀 mounted guard(對齊 codebase 既有 `notifications-menu.tsx:145` pattern,per CLAUDE.md §1.3 surgical + §13「揀更接近既有 pattern」)
- 非 H7 trigger:fix 不改 visual 最終輸出(icon 一樣),屬「修正 hydration bug / visual output identical」
- 一併修 `nav/theme-toggle.tsx`(同 pattern,用戶 explicit 要求);按 surgical 原則初次只報告未主動改

### Blockers
- 無

### Effort
- Planned:1.0h;Actual:~1.0h;Variance:0

### Commits
| Hash | Subject |
|---|---|
| (本次)| `fix(frontend): guard theme-toggle icon against SSR hydration mismatch (C11, C09) [BUG-032]` |

---

## Closeout

### Root Cause(final)
`auth-frame.tsx` 同 `nav/theme-toggle.tsx` 用 `isDark = resolvedTheme === 'dark'` 條件渲染 lucide icon。`next-themes` 嘅 `resolvedTheme` 只喺 client 解析(localStorage + 系統偏好),SSR 時係 `undefined`,令 server 渲染 `<Layers>` 但 dark-mode client hydrate 成 `<Sparkles>` → SVG `d` mismatch → React 丟棄 server tree 全 client render(11 errors)。`/login` 直接 SSR full-load 所以暴露。

### Fix Summary
兩個 client component 加 mounted guard:`const [mounted,setMounted]=useState(false); useEffect(()=>setMounted(true),[]); const isDark = mounted && resolvedTheme==='dark';`。首次 client render `mounted=false` → `<Layers>`,與 server byte-identical,消除 mismatch;mounted 後 `useEffect` 觸發 re-render 切換正確 icon。視覺最終輸出不變。影響檔案:`frontend/components/auth/auth-frame.tsx`、`frontend/components/nav/theme-toggle.tsx`。

### Regression Test
未自動化 hydration-error assertion(記為 follow-up)。手動 regression:Playwright full-load `/login` → console error 11→0;SSO 登錄→`/dashboard` 成功。既有 `frontend/tests/e2e/visual-baseline.spec.ts` v8-login snapshot 覆蓋 visual 不變。若日後要自動化,可喺 e2e 加「load /login 後 console 無 error」assertion — 原本即能捕捉本 bug。

### Lessons
- **有效**:從基礎設施往上排查 + Playwright 直接 reproduce console + 逐條讀 hydration error stack → 精確定位單一根因,避免盲改
- **教訓**:「登錄唔到」嘅用戶感知 ≠ 登錄系統壞 — 實測證明兩條 auth 路徑 functionally OK,真兇係 hydration 重繪影響首次互動穩定性。先驗證 functional path 再歸因,避免修錯方向
- **Pattern to watch**:任何條件渲染依賴 `next-themes` resolvedTheme / localStorage / 系統偏好嘅組件,SSR 必 mismatch → 一律 mounted guard(cf. BUG-023 亦屬 hydration class)

### Component design note status updates
- 無(純 hydration correctness fix,C11 / C09 design note 不變)

---

**End of BUG-032 progress**
