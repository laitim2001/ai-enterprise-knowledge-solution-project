# W94 P5 設計 — Progress

> 每日進展 + 決策 + commits + 結尾 retro。對應 [`checklist.md`](./checklist.md)。

## Day 1 — 2026-06-25(P5 設計 kickoff)

### 開工背景
- P3 完整收束(W92 P3a doc_acl override G6 + W93 P3b group 繼承 G7,已 push)。用戶問「總共幾多 RBAC 要做 + RBAC 以外仲有咩 pending」→ 答畢後用戶指示「先繼續完成 P5」。
- P5「管理權分級 + 存取治理」觸發 H1(加 `auditor` role = role model 演進 + 新治理機制)→ STOP + 跟 P1/P3 既定模式:**先設計 phase + ADR-0068,Accept 後先 implement**(次序鐵律 5)。
- **範圍 AskUserQuestion 拍板 = 「核心 + 存取覆核」**:① 角色分立 + 管理權分級 ② 存取覆核唯讀報告 + re-certify;JIT/break-glass/自動回收延後(Tier 2)。

### 現狀盤點(Explore agent + 自讀 `rbac.py`/`rbac_storage.py`)
- **Role model**:`RoleKey=["admin","editor","user","power"]`,3 active + power(Tier 2 reserved active=False)。**單層 admin,無 super-admin/owner/auditor 分化**。
- **Permission matrix**(`rbac_storage.py:80-131`):5 area × 23 permission × 4 role = 92 cell,硬編 static。`cfg.view_audit_log` + `cfg.manage_users` 皆 admin-only。
- **Guard**(`acl.py:47-126`):`require_role`/`require_kb_acl`/`assert_kb_access`,**admin `:112` 無條件 bypass**。
- **Audit log**:**已有讀端點** `GET /admin/audit-log`(`routes/admin/audit_log.py:34-54`,游標分頁 + action_type/since 過濾)→ access-review 可建喺其上。
- **存取覆核 / re-certify**:**完全 net-new**(grep 0 命中)。
- **Groups**:P3b 已備 member 方法 + 端點。
- **Explore 小結誤判更正**:佢判治理層係「Tier 2 上線先決」**唔啱** —— 上線安全先決已由 P2 達成(DG4);P5 = post-launch Tier 1.5 治理增強(同 P3)。

### kickoff(R1)
- rolling JIT 建 W94 三件套。F1-F3 = 設計 + ADR,**不 implement**。

### 待續(本 phase)
- F1 威脅模型(G8 SoD + G9 access review)→ F2 目標架構(auditor role + 分層 push-back + review report)→ F3 ADR-0068 Proposed → DG 拍板 → Accept。

### Commits
- (kickoff)docs(planning): kickoff W94 P5 governance-design phase artifacts
