# W94 P5 設計 — Checklist

> 對應 [`plan.md`](./plan.md) §2 F1-F3 + §3 Decision Gates。完成 → `[x]` + progress Day-N 記錄。
> 未完項**不可刪**(per CLAUDE.md §10 sacred rule),只 `→ [x]` 或標 🚧 + 理由。
> **約束**:P5 = 設計 phase,**不寫 production code**(`RoleKey` / permission matrix / guard / store / 端點不動)。

## F1 威脅模型 / 治理缺口(`threat-model-p5.md`)
- [ ] G8 職責分立缺口:`admin` 單層全權(`acl.py:112` 無條件 bypass)、permission matrix 無唯讀 auditor column(`rbac_storage.py:80-131`)+ 攻擊/合規情景(admin 改自己權限無監察 / 管理者兼監察者)+ codebase 證據
- [ ] G9 存取覆核缺口:權限永久有效無覆核、無 review/recert 任何 scaffold(grep 0 命中)+ 情景(privilege creep 無察覺 / 離職權限遺留)+ codebase 證據
- [ ] 與企業 SoD + access-review 標準對標(現狀 vs 合規要求差距表)
- [ ] 釐清 Explore 小結誤判:治理層 ≠「Tier 2 上線先決」(上線安全先決已 P2 達成),P5 = post-launch Tier 1.5 增強

## F2 目標治理模型(P5)(`target-architecture-p5.md`)
- [ ] ① auditor role 設計:加 `RoleKey` 第 5 值 + permission matrix 唯讀 column(`cfg.view_audit_log` + 新 `cfg.view_access_review` granted,所有寫 permission denied)+ guard 復用 `require_role("auditor", ...)`(DG-P5-A 選項 + 推薦)
- [ ] ① super-admin/owner 分層分析:**含 push-back** —— `admin` + `kb_acl.manage` 是否已覆蓋 owner;super-admin 委派真實需求論證(DG-P5-B 選項 + trade-off + 推薦)
- [ ] ② access-review report 設計:per-user/group snapshot(workspace role + KB ACL grants 匯總,建喺既有 `users`/`rbac`/`kb_acl` store + `GET /admin/audit-log` 之上,非新 data plane)
- [ ] ② re-certify 機制:標記「已覆核 + 時間戳 + 覆核人」store 設計(**無審批 workflow** — 延後 JIT)(DG-P5-C 選項 + 推薦)
- [ ] 每 fork 列選項 + trade-off + 推薦(對齊 ADR-0066/0067 選項分析風格)
- [ ] re-stamp / 索引影響確認:**零**(P5 不動 retrieval,north-star §15 by construction no-op)

## F3 ADR-0068 草擬 + Accept
- [ ] `docs/adr/0068-admin-tiering-and-access-governance.md` 撰寫(Context / Decision / Alternatives / Consequences / References)→ **Status: Proposed** + README index 加 0068 + next NNNN → 0069
- [ ] DG-P5-A/B/C/D resolution 寫入 ADR Decision(用戶 AskUserQuestion 拍板)
- [ ] decision owner review → **Accept**(用戶以 decision owner 身份)→ ADR Status Proposed→Accepted + README 更新(次序鐵律 5 satisfied,P5-impl 解鎖)

## Phase Gate(收尾)
- [ ] F1+F2+F3 完成 + **ADR-0068 Accepted**
- [ ] P5-impl 次序鐵律 5 satisfied(ADR Accept)→ 可 kickoff P5 implementation
- [ ] **零 production code**(設計 phase 純文檔,`RoleKey`/matrix/guard/store/端點一律未動)
- [ ] 更新 `enterprise-rbac/TRACKER.md`(P5 狀態 + M5 里程碑進展)+ progress retro
