# W95 — Enterprise RBAC P5 implementation:管理治理(auditor role + access review)

| 項目 | 值 |
|---|---|
| Phase | W95-rbac-p5-governance-impl(enterprise RBAC track 第 8 期,P5 implementation) |
| Status | **active**(2026-06-25 用戶批准「繼續執行 P5 實作」) |
| Tier | Tier 1.5(per ADR-0068) |
| 依賴 | **ADR-0068 Accepted**(2026-06-25)・ ADR-0027(role / permission matrix / audit log 基建)・ W94 設計(threat-model-p5 / target-architecture-p5) |
| 錨點 | **ADR-0068** §Decision(auditor role 唯讀 + access-review report + re-certify)・ §Decision 6 分段 F1-F5 |
| 下一期 | P5 完成;後續 = P6 / SSO(Tier 2)/ 3 小手尾 / Production launch 待 Track A IT cred |

> **受 ADR-0068(Accepted)約束**。**核心保證**:純 **additive** —— 加 `auditor` 角色 + access-review 報告 + re-certify 標記;**零檢索改動**(不動 `allowed_principals` / filter / chunk / `principals_for_user`)→ north-star §15 by construction no-op;**現有 4 role 行為 byte-identical**。

---

## §1 目標(Why)

實作 ADR-0068 兩個治理能力:**G8 職責分立**(auditor 唯讀稽核角色,解決 admin 單層全權 = 被監察者兼監察者)+ **G9 存取覆核**(access-review report + re-certify,解決權限永久無覆核 / privilege creep)。

## §2 Deliverables(F1–F5,per ADR-0068 §Decision 6)

| # | Deliverable | Acceptance |
|---|---|---|
| **F1** | auditor role | `RoleKey` 加 `"auditor"`(第 5 值)+ `_DEFAULT_ROLES` + permission matrix 第 5 column(92→115 cell)+ 新 permission `cfg.view_access_review`(admin + auditor granted);auditor 唯讀(只 `kb.view_assigned` + `cfg.view_audit_log` + `cfg.view_access_review`,所有寫 denied)+ `users.py _TIER1_ROLES` 加 auditor + `GET /admin/audit-log` guard 改 `require_role("admin","auditor")`;**BC**:現有 4 role grant byte-identical;test(auditor 出現 / 115 cell / auditor 過 audit-log / 不過寫端點 / 現有 role 不變) |
| **F2** | access-review report | `GET /admin/access-review`(`require_role("admin","auditor")`)匯總每 user:workspace role + KB ACL grants(逐 KB)+ group 成員 + verified;schema `AccessReviewRow` / `AccessReviewResponse`;建喺既有 `users` / `rbac` store,純讀組裝;test |
| **F3** | re-certify 標記 | `access_review_store`(Protocol + InMemory + Postgres `access_reviews(id, principal_id, reviewed_by, reviewed_at, note)`)+ factory;`POST /admin/access-review/{principal_id}/certify`(`require_role("admin")`)+ 新 audit action `access.reviewed`;report row 帶 last-reviewed 標記;**無審批 workflow**;test |
| **F4** | 前端治理 UI | RolesTab auditor column + access-review view + certify 按鈕。**H7(無 mockup)→ STOP+ask**(design-stage expansion / 復用既有 primitive / 寫 vanilla,用戶定)|
| **F5** | Gate | RBAC/auth pytest 全綠 + ruff + mypy(改動檔自身 0 error)+ **north-star §15 no-op**(零檢索改動)+ **BC**(現有 4 role byte-identical) |

## §3 Phase Gate
- **G-F1** auditor role + 115-cell matrix + guard + BC
- **G-F2** access-review report 匯總正確
- **G-F3** re-certify store + 標記端點 + audit action
- **G-全** pytest 全綠 + ruff + mypy + north-star §15 no-op + BC

## §4 Risks
- 🟡 **permission matrix 92→115 cell**(F1):`_PERMISSION_MATRIX` 每行加第 5 bool + `_ROLE_ORDER` 加 auditor(`zip strict=True` 要對齊)→ test 守 cell count + 現有 4 role grant 不變。
- 🟢 **零檢索影響**:F1-F5 純授權 + 報告層,不動 retrieval → north-star §15 by construction no-op,**無需重跑 eval**。
- 🟢 **BC**:auditor 係新增第 5 role,現有 admin/editor/user/power 行為 byte-identical;auditor 唔加入 admin bypass(`acl.py:112` 維持只 admin);`principals_for_user(auditor)` = `[oid]`(非 admin path 已有)。
- 🟡 **H7 前端**(F4):無 access-review mockup → STOP+ask(per §5.7);backend F1-F3 + F5 可先做。
- 🟢 **backend reload=False**:live 驗證前確認 backend 啟動時間,否則 pytest 為準(per memory `project_stale_backend_no_reload`)。

## §5 Out of scope(留後期 / Tier 2)
super-admin / KB owner 分層(DG-P5-B push-back,無 driver)/ JIT 臨時提權 + 審批 workflow / break-glass / 自動回收 deprovisioning / 真實 SCIM 成員同步(全 Tier 2)/ ABAC 政策引擎(P6)/ access-review 自動過期提醒(DG-P5-C C3 defer)。

## §6 Changelog
| 日期 | 變動 | 由 |
|---|---|---|
| 2026-06-25 | P5-impl kickoff — W94 設計 + ADR-0068 Accepted 後,用戶批准「繼續執行 P5 實作」;rolling JIT 建三件套;scope = ADR-0068 §Decision 6 F1-F5(backend F1-F3+F5,前端 F4 H7 gate)| 開工 |
