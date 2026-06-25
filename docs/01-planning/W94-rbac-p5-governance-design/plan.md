# W94 — Enterprise RBAC P5:管理權分級 + 存取治理 設計 + ADR-0068

| 項目 | 值 |
|---|---|
| Phase | W94-rbac-p5-governance-design(enterprise RBAC track 第 7 期,P5 設計) |
| Status | **active**(2026-06-25 用戶批准開 P5;範圍 AskUserQuestion 拍板 = 核心 + 存取覆核) |
| Tier | **Tier 1.5 post-launch 治理增強**(P5 = 設計 + ADR,**唔 implement**;ADR-0068 Accept 需 decision owner approve per H1 + H4) |
| 依賴 | P0–P3 全完成(W88–W93)・ audit log 讀端點已存在(`GET /admin/audit-log`,分頁 + action_type/since 過濾)・ permission matrix(`backend/storage/rbac_storage.py:80-131`,92 cell)・ groups + group_members(P3b 已備) |
| 錨點 | **ADR-0027**(W24c RBAC role model + permission matrix)・ ADR-0066(檢索層 ACL)・ ADR-0067(doc_acl + group)・ [`ROADMAP.md §2 P5`](../enterprise-rbac/ROADMAP.md) |
| 粗估 | 設計 3–5 日(implementation 另期 P5-impl) |
| 下一期 | P5 implementation(**ADR-0068 Accepted 後**才 kickoff,次序鐵律 5) |

> **範圍由用戶 2026-06-25 AskUserQuestion 拍板 = 「核心 + 存取覆核」**:① 角色分立 + 管理權分級(auditor 唯讀稽核 role + super-admin/owner 分層 + permission matrix 細化)② 存取覆核(access review)唯讀報告 + 定期 re-certify。**JIT 臨時提權 / break-glass 應急 / 自動回收(隨 SSO/SCIM)延後(Tier 2)**。本檔只定 scope + deliverables + acceptance + decision gate。**P5 建喺既有 4-role permission matrix(`ADR-0027`)+ audit log 讀端點之上,非推倒重來。**

---

## §1 目標(Why)

W24c(ADR-0027)落地咗**功能性**(能用)嘅 RBAC —— 授權邏輯正確、4 role 清晰、KB 隔離有效。但欠**治理性**(合規)能力:現時 `admin` 係**單層全權**(無條件 bypass 所有 guard,`acl.py:112`),冇職責分立,亦冇任何機制定期驗證「邊個有咩權限」。兩個企業級治理缺口:

- **缺口 G8(職責分立 / Separation of Duties)**:`admin` 一個 role 做晒所有嘢 —— 改用戶角色、管 KB、管 provider、睇 audit log 全部同一個 role。冇**唯讀稽核員**(auditor:可睇 audit log + 存取報告但唔可改任何嘢)→ 違反企業合規嘅 SoD 原則(管理者唔應該同時係自己嘅監察者)。亦冇 super-admin vs 日常 admin 嘅委派分層。
- **缺口 G9(存取覆核 / Access Review)**:權限一旦 grant 就**永久有效**,冇定期覆核。冇機制 generate「邊個 user/group 有咩 workspace role + KB ACL」嘅 snapshot 俾管理者 re-certify → **權限蔓延(privilege creep)無人察覺**,離職 / 轉崗用戶嘅遺留權限無流程清理。

P5 = **設計** 呢兩層治理能力嘅目標架構 + 拍板 **ADR-0068**,為 P5 implementation 鋪路。

**次序鐵律 1(ROADMAP §3)**:P5 **唔影響索引結構**(純授權 + 治理層,不動 `allowed_principals` / 檢索 filter / chunk schema)→ 與 P2/P3 正交,零重建。但 **auditor 加入 `RoleKey` Literal = role model 演進**(改 permission matrix 第 5 column),屬 architectural change(H1)→ 必須 ADR。

**P5 設計 phase 唔 implement** —— 唔改 `RoleKey` / permission matrix / guard / 不加 access-review 表或端點。implementation = P5-impl(ADR-0068 Accept 後)。產出 = 文檔(威脅模型 + 目標架構)+ ADR-0068(Proposed → decision owner Accept)。

## §2 Deliverables(F1–F3)

| # | Deliverable | Acceptance(可驗證成功標準) |
|---|---|---|
| F1 | 威脅模型 / 治理缺口(`threat-model-p5.md`) | 在 G1-G7 之上補 **G8 職責分立缺口** + **G9 存取覆核缺口**:攻擊 / 合規情景(admin 改自己權限無監察 / privilege creep 無人察覺 / 離職權限遺留)+ codebase 證據(`acl.py:112` admin bypass / permission matrix 無 auditor column / 無 review 任何 scaffold)+ 與企業 SoD + access-review 標準對標 |
| F2 | 目標治理模型(P5) | **① 角色分立**:auditor role 設計(加 `RoleKey` 第 5 值 + permission matrix 唯讀 column:`cfg.view_audit_log` + 新 `cfg.view_access_review` granted,所有寫 permission denied)+ super-admin/owner 分層分析(DG-P5-B 列選項 + trade-off,**含 push-back**:現有 `admin` + `kb_acl.manage` 是否已覆蓋 owner 概念)。**② 存取覆核**:report snapshot 設計(per-user/group:workspace role + KB ACL grants 匯總,建喺既有 store 之上)+ re-certify 機制(標記「已覆核 + 時間戳 + 覆核人」,**無審批 workflow** — 屬延後 JIT)。每 fork 列選項 + 推薦 + trade-off |
| F3 | ADR-0068 草擬 + Accept | `docs/adr/0068-*.md`(Context / Decision / Alternatives / Consequences / References)→ **Status: Proposed** → DG-P5-A~D resolution 寫入 → decision owner review → **Accept**(H1 + H4 硬閘)+ README index 加 0068 + next NNNN → 0069 |

## §3 Decision Gates(需 decision owner 拍板,P5 阻塞點)

> P5 範圍(核心 + 存取覆核)已由用戶 2026-06-25 拍板。以下係範圍內嘅設計 fork,F2 分析後附推薦,decision owner 拍板後寫入 ADR-0068。

| Gate | 內容 | 推薦 default(F2 grounded) | 阻塞 |
|---|---|---|---|
| **DG-P5-A** | auditor role 實作方式:加 `RoleKey` 第 5 個 active role / 用獨立 permission flag / 用 group | F2 後定;傾向 **加 `auditor` 第 5 個 active role**(對齊既有 role-based 模式 + permission matrix column,最少新概念) | F2 role 設計 |
| **DG-P5-B** | 管理權分層深度:只加 auditor(admin 維持單層)/ + KB owner 概念 / + super-admin vs admin 委派 | F2 後定;**含 push-back** —— auditor 係 clear win(SoD),但 super-admin/owner 可能 over-engineering(`kb_acl.manage` 已近似 owner)→ F2 分析真實需求後附推薦 | F2 分層設計 |
| **DG-P5-C** | 存取覆核範圍:純唯讀報告 / 報告 + re-certify 標記 / + 過期提醒 | 傾向 **報告 + re-certify 標記**(snapshot + admin 標「已覆核」+ 時間戳;審批 workflow + 自動過期屬延後 JIT) | F2 review 設計 |
| **DG-P5-D** | P5 Tier 定位 + implementation 時序 | **Tier 1.5 post-launch**(P2 已達 launch 安全 DG4;P5 治理增強,implementation 緊接設計或視排程) | P5-impl kickoff |
| **DG-P5-E** | ADR-0068 Accept | — | P5-impl 全部(鐵律 5) |

## §4 Risks

- 🟡 **role model 演進**(H1):加 `auditor` 入 `RoleKey` Literal + permission matrix 第 5 column → 改 92→115 cell(23 permission × 5 role)+ 影響 `users.py` `_TIER1_ROLES` 過濾 + 前端 RolesTab 渲染。屬 ADR-0027 嘅自然擴充(非推倒),但係 architectural change → **DG-P5-A 須 decision owner 拍板,AI 唔自行定**(H1)。
- 🟡 **over-engineering 風險**(Karpathy §1.2):super-admin / owner 分層可能 speculative —— 單一 workspace 通常一個 admin tier 足夠,`kb_acl.manage` 已提供 per-KB owner-like 委派。F2 須 **push-back + 真實需求論證**,唔可為「企業級」三字加未要求嘅 role 爆炸(同 P6 ABAC 政策引擎邊界互通)。
- 🟢 **零索引 / 零檢索影響**(次序鐵律 1):P5 純授權 + 治理層,**完全不動** `allowed_principals` / 檢索 filter / chunk schema / `principals_for_user` → north-star §15 圖文還原 by construction no-op(無 retrieval 路徑改動)。
- 🟢 **建喺既有之上**:access-review report 建喺既有 `users` / `rbac` / `kb_acl` store + `GET /admin/audit-log` 之上,非新 data plane;auditor 沿用既有 guard 機制(`require_role`)。
- 🟢 **P5 設計 phase 唔 implement**:零 production code(`RoleKey` / matrix / guard / 表 / 端點一律不動),implementation = P5-impl(ADR-0068 Accept 後)。

## §5 Out of scope(留 P5-impl / 後期)

auditor role + permission matrix column **實作** + access-review report 端點 + re-certify 標記 store + 前端治理 UI(全 P5-impl)/ **JIT 臨時提權 + 審批 workflow**(Tier 2,P5 範圍外,用戶 2026-06-25 拍板延後)/ **break-glass 應急存取**(Tier 2 延後)/ **自動回收 deprovisioning**(隨 SSO/SCIM,Tier 2)/ 真實 SCIM 成員同步(Tier 2)/ ABAC 政策引擎(P6)。P5 設計 phase **只**設計 + 拍板,不寫 production code(`RoleKey` / permission matrix / guard / store / 端點一律不動)。

## §6 Changelog

| 日期 | 變動 | 由 |
|---|---|---|
| 2026-06-25 | P5 kickoff — P3 收尾後 rolling JIT 建三件套;用戶批准開 P5 + AskUserQuestion 拍板範圍「核心 + 存取覆核」(JIT/break-glass/自動回收延後 Tier 2);scope = 設計 + ADR-0068,不 implement(H1/H4 gate,implementation 待 ADR Accept) | 開工 |
