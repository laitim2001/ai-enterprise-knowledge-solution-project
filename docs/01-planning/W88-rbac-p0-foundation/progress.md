# W88 P0 — Progress

> 每日進展 + 決策 + commits + 結尾 retro。對應 [`checklist.md`](./checklist.md)。

## Day 1 — 2026-06-24(開工 + F1 起手)

### 開工背景
- 用戶 2026-06-24 批准 P0 flip active(原 status draft)。
- **發現:初版三件套(plan / checklist / progress)從未真正入庫** —— git 史 + disk 都冇 `W88-rbac-p0-foundation/`,只有 `enterprise-rbac/` 6 份在。OneDrive 同步吞文件 risk(🔴)實現。今日重建三件套,Write + `git ls-files` 驗入庫(若被吞則 PowerShell 直寫 fallback)。
- TRACKER / ROADMAP 對 `../W88-rbac-p0-foundation/plan.md` 嘅 broken reference 一併修復。

### F1 環境基準實測(2026-06-24)
- **HEAD vs disk rbac schema = 一致(乾淨四級)**:`git show HEAD:backend/api/schemas/rbac.py` 同 disk 都係 `RoleKey = Literal["admin","editor","user","power"]`。**根因「disk stale 三級」已自愈** —— OneDrive 同步追上 HEAD(對比 FINDINGS §3 基準日 2026-06-23 disk 仍 stale)。
- **backend `/health` = ok**(全 components 綠);進程 PID 12104+46164 啟動 2026-06-23 2:28 PM。
- **running backend 確認唔 stale**:啟動 6/23 2:28 PM **晚過**最後 backend commit `854f9a5`(6/18);實打 `/auth/me`(mock dev-token)回乾淨 `{role:"admin", is_mock:true}`,**無 role_source / viewer 幻欄位**;backend code 全域 grep `role_source`/`is_admin_hint`/`default_viewer` = 0 match。→ FINDINGS「running backend 回幻欄位」根因**已隨 disk 自愈消失**(嗰啲欄位嚟自 6/23 被污染嘅 disk 版,今已乾淨)。
- **DB `users` 表查清**:得 1 行 `admin@example.com` / role=`user` / verified=`f`(首位且唯一用戶)。

### F2 根因定位(2026-06-24)
- `users_repo.register()`(L80-99)**從未有 first-user-admin bootstrap** —— 建 `UserRecord` 唔設 role,用 DB default `'user'`。所以首位用戶 `admin@example.com` 係 `user` 而非 `admin`。FINDINGS「bootstrap 未生效」更準確 = **從未實作**。
- 連帶:`admin@example.com` verified=`f`(未驗證 → 登入撞 403,解釋 FINDINGS「登入失敗」)。

### F1 判決
- ✅ **環境三層一致(自愈)**:HEAD = disk = running backend 全乾淨四級,running backend 唔 stale。
- ❌ **既有債真實**:首位用戶 role + verified 待理順(移交 F2)。

### Decisions
- P0 status draft → **active**(用戶批准)。
- plan acceptance criteria 對齊最新實測(disk + backend code 已自愈)。
- F1 環境基準 = 通過(自愈);帳號角色理順併入 F2 一齊做。

### Commits
- d5c2006 docs(planning): rebuild W88 P0 phase artifacts + flip active

### F2 實作(2026-06-24)
- **用戶拍板方案 1**:加 bootstrap + 一次性升權既有帳號。
- **`users_repo.register()`** 加 first-user bootstrap:`role = "admin" if not _store.list_users() else "user"`。
- **新增 `users_repo.ensure_admin_bootstrap()`**:self-healing reconcile —— 無 admin 時把最早註冊用戶升 admin + `mark_verified`,經 repo layer(`set_user_role`/`mark_verified`)不裸改 DB(H5);idempotent;P1 Entra app-role 假設已標 NOTE。
- **`server.py` lifespan wire**(L154 RBAC seed 後):startup 呼叫 `ensure_admin_bootstrap()` + structlog log promotion;`import structlog` 加 `# noqa: E402`(server.py 既有 truststore E402 pattern,count 回 30 不增 debt)。
- **測試**:`test_auth_self_register.py` 加 5 個(首用戶→admin / 次用戶→user / 無 admin 升+verify / 有 admin no-op / 空 store no-op)。
- **驗證**:self-register 58 passed;廣測試(auth/users/rbac/acl/group)**224 passed / 8 skipped / 0 failed**,零 regression;`users_repo.py` ruff clean,`server.py` 回 30(既有 baseline)。

### F2 端到端驗證(2026-06-24 ✅ 完成)
- 重啟 backend(殺 dual-process 12104/46164 → venv python 啟新,READY ~104s,新 server 進程 27628)。
- **startup log 確認 `admin_bootstrap_promoted`**:`{oid:u-IQh-6IRLT-4tXfAS, email:admin@example.com}`。
- **DB `users` 驗證**:`admin@example.com` role `user`→**`admin`** + verified `f`→**`t`**。經 application layer(`set_user_role`/`mark_verified`),**不裸改 DB**(H5)。
- **F2 正式收尾** ✅(code + 單元測試 + 端到端三層全綠)。

### F3 前端 badge 讀真 role(2026-06-24 ✅ 完成)
- **H7 trigger + 用戶拍板**:mockup `ekp-shell.jsx` 兩處(line 208 UserMenu header / line 336 sidebar footer)寫死「Workspace Admin」,未定義非 admin role 視覺 → STOP+ask → 用戶選**複用 RoleBadge**。
- **改動**:`user-menu.tsx`(L107)+ `app-shell.tsx`(L547)兩處硬編 → `{role && <RoleBadge role={role} />}`;role 由 `useRole()`(canonical `/auth/me`)攞;role null(loading)隱藏。
- **驗證**:ESLint clean、`tsc --noEmit` F3 檔案 0 type error。
- **browser H7 fidelity check**(playwright,:3001 mock auto sign-in admin):
  - sidebar footer RoleBadge "Workspace Admin" ✅(snapshot ref=e276)
  - user-menu header dropdown RoleBadge "Workspace Admin" ✅(snapshot ref=e470)
  - console 3 errors 全係既有 `/api/backend/notifications` 404(非故障 per memory),同 F3 無關。
- **F3 正式收尾** ✅。

### F4 調查 + 路徑(2026-06-24)
- **調查**:backend 寫 endpoints 全已實作(`POST /users/invite`、`POST /users/{oid}/suspend`、`PATCH /users/{oid}/role`);前端 `/users` mockup 係 presentational(Invite button L88 + 每行 ⋯ More L183 有按鈕視覺,**交互未設計**)。F4 = 純前端接通。
- **H7 trigger**:寫操作交互(邀請 form / 改角色 menu / 停用確認)mockup 未設計 → STOP+ask → **用戶選「先補 mockup 設計再對齊」**(最正統 H7 路徑)。
- **F4 下一步(fresh turn,避免 context 緊下硬做 H7-sensitive 設計)**:
  ① 讀 mockup `ekp-page-users.jsx` 全結構 + `DESIGN_SYSTEM.md §4`(Modal / PopMenu / OptionRow)
  ② propose 三個交互佈局(邀請 form modal / 改角色 PopMenu / 停用確認)畀用戶確認
  ③ 寫入 mockup → ④ 前端 1:1 對齊實作 + H7 verify。

### 本輪(Day 1)收結
- **完成 F1 + F2 + F3**(3 commits:`d5c2006` / `e3809e1` / `b4cfceb`);重啟 backend 驗 F2 端到端;playwright 驗 F3 兩處 badge。
- **F4 路徑已定**(補 mockup 設計),fresh turn 開工。F5(KB ACL,純 backend)+ F6(Gate)未開始。

### F4 ①②③ — 補 mockup 設計(2026-06-24 續)
- **① 讀**:mockup `ekp-page-users.jsx` 全結構 + `DESIGN_SYSTEM.md §4`(§4.5 Modal / §4.1 PopMenu / §5 destructive color)+ backend contract(invite: email/role/display_name;role: PATCH role;suspend: 無 body;⚠️ 無 reactivate/resend endpoint)。
- **② propose + 用戶確認**:三個交互;用戶選改角色形式 = **row dropdown + inline 列三個 role**(當前 ✓ + Suspend destructive)。
- **③ 寫入 mockup**:`InviteModal`(§4.5,email/display_name/role,Power User Tier 2 disabled)+ `RowActionMenu`(row-anchored dropdown,CHANGE ROLE inline 三 role + Suspend)+ `SuspendModal`(§4.5 destructive)+ state wiring。121 insertions。
- **③ browser 驗證**(http.server + playwright):mockup users 頁 0 JS errors;三個交互全部渲染正確(邀請 form Power User T2 disabled / row menu admin ✓ + Suspend red / suspend confirm user 插值 + destructive)。
- **P0 scope**:Reactivate / Resend invite backend 無 endpoint → out of scope。

### Carry-over → F4 ④
- ④ 前端 1:1 對齊實作:`frontend/app/(app)/users/page.tsx` 接通三個交互(shadcn/Tailwind + 接 backend invite/role/suspend + 錯誤態)+ browser H7 verify。fresh turn。
