# W88 P0 — Checklist

> 對應 [`plan.md`](./plan.md) §2 F1–F6 + §3 Phase Gate。完成 → `[x]` + progress Day-N 記錄。
> 未完項**不可刪**(per CLAUDE.md §10 sacred rule),只 `→ [x]` 或標 🚧 + 理由。

## F1 環境基準確認 + 帳號角色理順
- [x] `git show HEAD:backend/api/schemas/rbac.py` vs disk vs running backend 三層比對 → 全一致乾淨四級(自愈)
- [x] running backend `/auth/me` 實測 → 回乾淨 `{role:admin,is_mock:true}`,無幻欄位,唔 stale
- [ ] `admin@example.com` DB role + 解析角色對齊正確值 → 現狀查清(role=user / verified=f);理順動作併入 F2
- [x] 三層實測截錄入 progress

## F2 首位用戶自動管理員 bootstrap
- [x] 定位 bootstrap 邏輯 → `register()` 從未有,確認係「未實作」非「未生效」
- [x] 修正令空 DB 第一個用戶 role=admin → `register()` first-user bootstrap + `ensure_admin_bootstrap()` self-heal
- [x] DB role 值域對齊 RoleKey 四級 → bootstrap 只寫 admin/user,既有 admin@example.com(user)四級內
- [x] 單元測試覆蓋 → 5 個新測試,廣測 224 passed 零 regression
- [x] 端到端:重啟後 startup reconcile 觸發,`admin@example.com` 升 admin + verified=t(DB 確認 + startup log)

## F3 前端硬編 badge → 讀真角色
- [x] 定位 → user-menu.tsx:107 + app-shell.tsx:547(mockup ekp-shell.jsx:208/336 同樣寫死)
- [x] 改讀真角色 → useRole() + 複用 RoleBadge(H7 用戶拍板,mockup-grounded);role null 隱藏
- [x] H7 對齊 mockup → RoleBadge(ekp-page-users.jsx 四級);ESLint + tsc clean + browser 兩處 badge 驗證渲染

## F4 /users 寫操作接通
- [ ] 改角色接通
- [ ] 邀請接通
- [ ] 停用接通
- [ ] 前端錯誤態處理

## F5 KB 端點補接 require_kb_acl
- [ ] 盤點 KB 寫端點守衛覆蓋
- [ ] 補缺口
- [ ] 無權帳號被擋(測試)

## F6 Phase Gate + 端到端驗證
- [ ] G1–G5 逐項驗
- [ ] RBAC / auth pytest 全綠(≥ 160)
- [ ] 端到端 smoke 走通
- [ ] ruff clean
- [ ] P0 closeout + 更新 TRACKER + FINDINGS 基準
