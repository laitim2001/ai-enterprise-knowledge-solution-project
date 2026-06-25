# W94 P5 — 目標治理模型(target-architecture-p5.md)

> 對應 [`threat-model-p5.md`](./threat-model-p5.md) G8(職責分立)+ G9(存取覆核)。每 fork 列選項 + trade-off + 推薦,decision owner 拍板後寫入 ADR-0068。
> **約束**:Tier 1.5、**零索引 / 零檢索影響**、建喺既有 role / permission / audit store 之上、**additive 唔推倒**。

---

## §1 設計原則

- **Additive**:加 role + 加報告端點,**唔改**現有 4 role 行為 / guard / 檢索路徑。
- **復用既有**:auditor 用 `require_role`;report 建喺 `users` / `rbac` / `kb_acl` store + `GET /admin/audit-log` 之上,非新 data plane。
- **唔 over-engineer**(Karpathy §1.2):只加真正解 G8/G9 嘅嘢;JIT / ABAC / 自動過期屬後期。

## §2 ① auditor role(解 G8 職責分立)

### 2.1 DG-P5-A:auditor 實作方式

| 選項 | 做法 | Trade-off |
|---|---|---|
| **A. 加 `RoleKey` 第 5 值**(推薦) | `RoleKey=[...,"auditor"]` + permission matrix 第 5 column | 對齊既有 role-based 模型;少新概念;前端 RolesTab 自動渲染。改 92→115 cell |
| B. 獨立 permission flag | user 加 `is_auditor` bool | 唔郁 `RoleKey`,但引入 role 以外第二授權維度,複雜化 guard |
| C. 用 group | auditor = 特殊 group | group 係 ACL principal 唔係 workspace role,語義錯位 |

**推薦 A** —— 最少新概念,對齊 ADR-0027 role 模型。

### 2.2 auditor permission(唯讀)

permission matrix 第 5 column,**只 grant 唯讀**:
- granted:`kb.view_assigned`(睇 KB 列表)+ `cfg.view_audit_log` + **新 `cfg.view_access_review`**
- 所有寫 permission(kb.create / kb.delete、doc.upload、cfg.manage_* 等)= **denied**
- 新增 permission key:`cfg.view_access_review`(auditor + admin granted)

### 2.3 guard 整合
- auditor **唔加入** admin bypass(`acl.py:112` 維持只 admin)。
- audit log 讀端點 `GET /admin/audit-log` 由 `require_role("admin")` 改 `require_role("admin","auditor")`。
- access-review report 端點 `require_role("admin","auditor")`。

### 2.4 DG-P5-B:管理權分層深度(含 push-back)

| 選項 | 做法 | 評估 |
|---|---|---|
| **B1. 只加 auditor**(推薦) | admin 維持單層 + auditor 唯讀 | 解 G8 SoD 核心;最少改動 |
| B2. + KB owner | kb_acl 加 owner 級 | **push-back**:`kb_acl.manage` 已係 per-KB 最高權(可改 ACL),近似 owner。再加 owner 語義重疊,收益低 |
| B3. + super-admin | admin 分 super-admin(管 admin)vs 日常 admin | **push-back**:單一 workspace 通常一個 admin tier 夠;super-admin 委派係 multi-team 大組織需求,**未有真實 driver = speculative**(Karpathy §1.2) |

**推薦 B1** —— auditor 解 SoD 核心痛點;owner / super-admin 無真實 driver,留後期(出現明確需求先加,避免 role 爆炸 → 同 P6 ABAC 政策引擎邊界互通)。

> **Why push-back**:用戶範圍揀「核心 + 存取覆核」原意 = SoD + 合規可視。auditor 直接解;owner / super-admin 係「企業級」三字嘅自然聯想但未必有真實痛點。設計 phase 應 surface 呢點俾 decision owner 揀,**唔好默默加 role**(Karpathy §1.1 + §1.2)。

## §3 ② access-review report + re-certify(解 G9 存取覆核)

### 3.1 report snapshot

新端點 `GET /admin/access-review`(`require_role("admin","auditor")`):
- 匯總每個 user:workspace role(`users` store)+ KB ACL grants(`kb_acl` 逐 KB)+ group 成員(`group_members`)+ last login / verified。
- 建喺既有 store,**唔新增 data plane**,純讀 + 組裝。
- 回傳 per-principal 一行,前端渲染「邊個有咩權限」表。

### 3.2 DG-P5-C:re-certify 範圍

| 選項 | 做法 | Trade-off |
|---|---|---|
| C1. 純唯讀報告 | 只 snapshot,唔記覆核狀態 | 最簡;但「覆核咗冇」靠人手記 |
| **C2. 報告 + re-certify 標記**(推薦) | 加 `access_reviews` 表記「principal X 由 admin Y 喺 T 覆核」+ audit action `access.reviewed` | snapshot + 可追溯覆核歷史;無 workflow 開銷 |
| C3. + 自動過期提醒 | C2 + grant 超期未覆核標紅 | 引入時間政策 + 背景 job,接近 JIT(延後範圍) |

**推薦 C2** —— 報告 + 覆核標記 + 時間戳 + 覆核人,新 audit action `access.reviewed`。**無審批 workflow**(審批屬延後 JIT)。

### 3.3 re-certify store
- 新 `access_review_store`(Protocol + InMemory + Postgres `access_reviews` 表),mirror 既有 store pattern(如 `doc_classification_store`)。
- 純記錄「覆核事件」,**唔改** user / kb_acl 本身(覆核 = 確認現狀適當;要改權限走既有 `/users` / `/kb/{id}/acl` 端點)。

## §4 影響評估

- **零索引 / 零檢索**:唔掂 `allowed_principals` / filter / chunk / `principals_for_user` → north-star §15 by construction no-op。
- **Additive**:加 1 role + 2 permission key + 1 report 端點 + 1 re-certify 端點 / 表;**現有 4 role 行為 byte-identical**。
- **前端**:RolesTab 多一 column(auditor);admin / Settings 多一個 access-review view(H7,等 mockup 或 design-stage expansion)。
- **測試**:auditor guard + report 組裝 + re-certify CRUD;BC(現有 role 不變)。

## §5 DG 總表(待 decision owner 拍板)

| Gate | 推薦 |
|---|---|
| DG-P5-A auditor 實作 | **A. 加 `RoleKey` 第 5 值** |
| DG-P5-B 分層深度 | **B1. 只加 auditor**(owner / super-admin push-back 留後期) |
| DG-P5-C re-certify 範圍 | **C2. 報告 + 覆核標記**(無 workflow) |
| DG-P5-D Tier / 時序 | **Tier 1.5 post-launch**;implementation 視排程 |

## §6 P5-impl 預覽(ADR Accept 後,非本期)

F1 auditor role(`RoleKey` + matrix column + guard)/ F2 access-review report 端點 / F3 re-certify store + 端點 / F4 前端治理 UI(H7)/ F5 Gate(BC + 零檢索影響驗證)。**本設計 phase 唔做以上任何一項** —— 純設計 + ADR,implementation 待 ADR-0068 Accept + 用戶另批。
