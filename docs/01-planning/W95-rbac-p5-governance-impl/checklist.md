# W95 P5-impl — Checklist

> 對應 [`plan.md`](./plan.md) §2 F1-F5 + §3 Phase Gate。完成 → `[x]` + progress Day-N。
> 未完項**不可刪**,只 `→ [x]` 或標 🚧 + 理由。
> **約束**:受 ADR-0068 約束;純 additive;**零檢索改動**(north-star §15 no-op);現有 4 role byte-identical。

## F1 auditor role
- [ ] `api/schemas/rbac.py`:`RoleKey` 加 `"auditor"` + `_DEFAULT_ROLES` 加 auditor Role(tier=1, active=True, 唯讀 label)
- [ ] `storage/rbac_storage.py`:`_ROLE_ORDER` 加 `"auditor"` + `_DEFAULT_ROLES` 加 + `_PERMISSION_MATRIX` 每行加第 5 bool(auditor column)+ 新 permission `cfg.view_access_review`(admin+auditor True)
- [ ] auditor 唯讀:只 `kb.view_assigned` + `cfg.view_audit_log` + `cfg.view_access_review` granted,所有寫 denied
- [ ] `routes/users.py`:`_TIER1_ROLES` 加 auditor(令可指派)
- [ ] `routes/admin/audit_log.py`:`GET /admin/audit-log` guard `require_role("admin")` → `require_role("admin","auditor")`
- [ ] test:auditor 出現 list_roles / 115 cell / auditor 過 audit-log / auditor 不過寫端點 / **BC 現有 4 role grant byte-identical**

## F2 access-review report
- [ ] schema `AccessReviewRow` / `AccessReviewResponse`(`api/schemas/access_review.py`)
- [ ] `GET /admin/access-review`(`require_role("admin","auditor")`)匯總 per-user role + KB ACL grants + group + verified(建喺既有 store 純讀組裝)
- [ ] test:匯總正確 + admin/auditor 過 + 非 admin/auditor 403

## F3 re-certify 標記
- [ ] `kb_management/access_review_store.py`(Protocol + InMemory + Postgres `access_reviews` 表 + factory,mirror `doc_classification_store`)
- [ ] `POST /admin/access-review/{principal_id}/certify`(`require_role("admin")`)+ 新 audit action `access.reviewed`
- [ ] report row 帶 last-reviewed 標記(reviewed_at / reviewed_by)
- [ ] server.py wire `access_review_store` + test(certify CRUD + audit + report 帶標記)

## F4 前端治理 UI(🚧 H7 — 無 mockup,STOP+ask)
- [ ] RolesTab auditor column + access-review view + certify 按鈕 → **STOP+ask**(design-stage expansion / 復用既有 primitive / 寫 vanilla,用戶定)

## F5 Gate(收尾)
- [ ] RBAC/auth pytest 全綠 + ruff + mypy(改動檔自身 0 error)
- [ ] **north-star §15 no-op**(零檢索改動論證)+ **BC**(現有 4 role byte-identical)
- [ ] 更新 progress retro + `enterprise-rbac/TRACKER.md`(P5 impl 進展 + M5)
