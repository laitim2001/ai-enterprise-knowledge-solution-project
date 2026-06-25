# W94 P5 — 威脅模型 / 治理缺口(threat-model-p5.md)

> 延續 W89 P1(G1-G5 檢索層)+ W91 P3(G6-G7 細粒度)。本檔補 **G8 職責分立** + **G9 存取覆核** 兩個**治理層**缺口。
> **性質定位**:治理 = 合規層,**非上線安全先決**(上線安全已 P2 達成 DG4)。P5 = post-launch Tier 1.5 增強。
> **錨點**:現狀盤點 2026-06-25(Explore agent + 自讀 `rbac.py` / `rbac_storage.py` / `acl.py`)。

---

## §1 範圍與定位

- 上線安全先決(檢索層唔洩漏文件)= **P2 已達成**(DG4)。本檔**唔係**講資料外洩(嗰個 P2/P3 解咗),而係講**治理 / 合規**:邊個可以做咩、由邊個監察、權限有冇定期清。
- **對標**:企業 IAM 嘅 Separation of Duties(SoD,職責分立)+ Access Certification / Recertification(存取覆核,如 SOX / ISO 27001 access review 要求)。
- **本檔唔掂 retrieval**:G8/G9 純授權 + 報告層,零索引 / 零檢索改動 → north-star §15 by construction no-op。

## §2 現狀基準(codebase 證據)

| 項目 | 現狀 | file:line |
|---|---|---|
| Role model | `RoleKey=["admin","editor","user","power"]`,3 active + power(Tier 2 reserved) | `rbac.py:22` |
| admin bypass | admin 無條件通過所有 KB guard;`principals_for_user` admin → None(檢索全放行) | `acl.py:112` / `acl.py:175-196` |
| Permission matrix | 5 area × 23 permission × 4 role = 92 cell,硬編 static | `rbac_storage.py:80-131` |
| audit log 讀 | **已有讀端點** `GET /admin/audit-log`(游標分頁 + action_type/since 過濾) | `routes/admin/audit_log.py:34-54` |
| audit log 寫 | user.invited / suspended / role.changed / kb.access.granted / kb.config.changed / doc.access.granted | `schemas/audit_log.py:16-36` |
| access review | **0 scaffold**(grep review/certif 0 命中) | — |

## §3 G8 — 職責分立缺口(Separation of Duties)

### 缺口
- `admin` 一個 role 集齊:改用戶角色(`cfg.manage_users`)、管 KB、管 provider / API key、**睇 audit log**(`cfg.view_audit_log`)。即係**被監察者 = 監察者**。
- 冇唯讀稽核角色:想俾合規 / 審計人員睇 audit log + 權限現狀,但**唔俾佢改嘢** → 做唔到(要俾 audit log 存取就要俾 admin,admin 就乜都改得)。
- 冇 admin 委派分層(super-admin vs 日常 admin)。

### 攻擊 / 合規情景
- **情景 A(監察盲點)**:admin 改自己 / 同謀權限、刪走唔想俾人見嘅操作,audit log 有記錄但**只有 admin 自己睇得到** → 無獨立稽核。違反 SoD。
- **情景 B(過度授權)**:要俾審計部門睇 audit log,被迫 grant admin → 審計員獲得完整改寫權,擴大攻擊面。

### 影響
合規審計(SOX / ISO 27001)通常要求「獨立稽核角色」+「管理操作有第三方可見」。現狀過唔到。

## §4 G9 — 存取覆核缺口(Access Review)

### 缺口
- 權限一旦 grant **永久有效**。冇機制 generate「邊個 user/group 有咩 workspace role + KB ACL」snapshot。
- 冇 re-certify 流程(定期確認權限仍適當)。
- 冇遺留權限清理流程(離職 / 轉崗)。

### 情景
- **情景 C(privilege creep)**:用戶轉崗多次,累積一堆 KB ACL grant,冇人 review → 過度權限長期潛伏。
- **情景 D(離職遺留)**:用戶離職,但 workspace role + KB grant 冇收回(現狀有 suspend,但冇主動 review 揾出邊啲該收)。

### 影響
Access certification 係企業合規基本要求。現狀靠 admin 記性,無系統支援。

## §5 與企業標準對標(差距表)

| 企業治理要求 | 現狀 | 缺口 | P5 對應 |
|---|---|---|---|
| 職責分立(唯讀稽核角色) | admin 單層全權 | G8 | auditor role |
| 管理操作獨立可見 | audit log 只 admin 睇 | G8 | auditor 可讀 audit log |
| 存取覆核 snapshot | 無 | G9 | access-review report |
| 定期 re-certify | 無 | G9 | re-certify 標記 |
| 自動過期 / JIT | 無 | (延後 Tier 2) | — |
| break-glass | 無 | (延後 Tier 2) | — |

## §6 非缺口 / 已澄清

- **Explore 小結誤判更正**:現狀盤點時 Explore agent 把治理層判為「Tier 2 上線先決條件」**唔啱**。上線安全先決(檢索層唔洩漏)已由 **P2 達成**(DG4)。P5 治理 = **post-launch Tier 1.5 合規增強**,**非上線 blocker**。
- **零索引 / 零檢索影響**:G8/G9 純授權 + 報告層,完全唔掂 `allowed_principals` / filter / chunk / `principals_for_user` → north-star §15 圖文還原 by construction no-op。

## §7 結論

P5 implement 兩件:① **auditor role**(解 G8 職責分立)② **access-review report + re-certify**(解 G9 存取覆核)。範圍收窄(用戶 2026-06-25 拍板):JIT / break-glass / 自動回收 = Tier 2 延後。目標架構 + 選項分析見 [`target-architecture-p5.md`](./target-architecture-p5.md)。
