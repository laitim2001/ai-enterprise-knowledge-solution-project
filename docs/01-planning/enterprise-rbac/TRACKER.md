# Enterprise RBAC — 項目工作追蹤清單(TRACKER)

> **用途**:呢個獨立項目嘅**跨階段持續追蹤入口**。每次有進展 → 勾選對應項 + 更新狀態 + 補變更日誌。
> **最後更新**:2026-06-23 ・ **Owner**:Chris(技術 Lead)
> **狀態圖例**:🔲 未開始 ・ 🟡 進行中 ・ ✅ 完成 ・ ⏸️ 待批准 ・ 🚫 阻塞 ・ ⏭️ 延後
> **現狀 / 實測 / 缺口詳情**:見 [`FINDINGS.md`](./FINDINGS.md)(本檔只追蹤狀態,事實不複製)

---

## 一、狀態總覽

| 階段 | 內容 | 狀態 | 備註 |
|---|---|---|---|
| 規劃 | 路線圖 + P0 計劃 + 報告 + 紀錄 + 文件整合 | ✅ 完成 | 已 commit + push |
| **P0** | 基礎校正 + W24c 收尾 | ⏸️ **待批准** | 計劃 draft,等 Chris flip active |
| P1 | 威脅模型 + 目標架構 + ADR-0066 | 🔲 未開始 | 依賴 P0 |
| P2 | 檢索層文件級存取控制 | 🔲 未開始 | 依賴 P1;可能係上線先決 |
| P3 | 文件/資料夾級細粒度授權 | 🔲 未開始 | 依賴 P2 |
| P4 | 群組存取(成員 + 繼承) | 🔲 未開始 | 真實同步隨 SSO 延後 |
| P5 | 管理權分級 + 存取治理 | 🔲 未開始 | 依賴 P3 |
| P6(選) | 屬性式權限 / 政策引擎 | ⏭️ 延後 | 規模化才需 |
| SSO/SCIM | 真實 SSO + 自動供應 | ⏭️ 延後 | 用戶決定後加 |

**整體定調(2026-06-23)**:規劃完成;程式碼地基扎實但系統未活、企業核心 0%(實測依據見 [`FINDINGS.md`](./FINDINGS.md))。**等 P0 批准令地基活起來。**

---

## 二、工作清單(可勾選持續追蹤)

### 階段 0 — 規劃(✅ 完成 2026-06-23)
- [x] 現狀調查 + 根因分析 + 企業級評估 + 親自實測(→ `FINDINGS.md`)
- [x] 候選路線圖(→ `ROADMAP.md`)
- [x] W88 P0 詳細計劃(plan / checklist / progress)
- [x] 向上級匯報報告 v2(→ `REPORT.md`)
- [x] 對話紀錄(→ `RECORD.md`)
- [x] 文件整合方案 A(抽 FINDINGS 單一來源 + 歸入 enterprise-rbac/ 去重)
- [x] commit + push

### P0 — 基礎校正 + W24c 收尾(⏸️ 待批准 → 細項見 [`../W88-rbac-p0-foundation/checklist.md`](../W88-rbac-p0-foundation/checklist.md))
- [ ] **批准開工**(Chris flip W88 draft → active)← 當前阻塞點
- [ ] F1 基準確認(disk / HEAD / running backend 一致)+ 帳號 role 理順
- [ ] F2 修首位用戶自動管理員(bootstrap)+ role 值一致性
- [ ] F3 前端硬編「Workspace Admin」badge → 讀真 role
- [ ] F4 `/users` 寫操作接通(改 role / 邀請 / 停用)
- [ ] F5 KB endpoints 補接 `require_kb_acl`
- [ ] F6 Phase Gate 驗證 + smoke
- [ ] P0 closeout + 更新本 TRACKER + `FINDINGS.md` 基準

### P1 — 威脅模型 + 目標架構 + ADR-0066(🔲 未開始)
- [ ] 威脅模型 + 需求(資料分類 / 用戶類型 / 合規 / 租戶數)
- [ ] 目標授權模型(資源層級 / RBAC+ABAC 邊界 / 索引結構)
- [ ] 撰寫 ADR-0066 + Chris approve
- [ ] 建立 W{NN} P1 phase folder

### P2 — 檢索層文件級存取控制(🔲 未開始,最關鍵)
- [ ] 索引結構加 ACL / 密級欄位
- [ ] ingestion stamp 文件 ACL
- [ ] 查詢時注入 Azure AI Search filter
- [ ] 答案 / 引用層確認唔洩漏
- [ ] 重建索引 + 驗證唔影響問答品質

### P3 — 文件/資料夾級細粒度授權(🔲 未開始)
- [ ] 授權表擴資源層級維度 + 繼承 + 覆寫
- [ ] 細粒度授權管理介面

### P4 — 群組存取(🔲 未開始,真實同步隨 SSO)
- [ ] 群組成員模型 + 繼承解析
- [ ] 手動 / 匯入成員

### P5 — 管理權分級 + 治理(🔲 未開始)
- [ ] 角色分立(超管 / 管理 / 稽核員 / 擁有者)
- [ ] 存取覆核 + 生命週期(JIT / 回收 / break-glass)

### P6(選)/ SSO(⏭️ 延後)
- [ ] P6 評估角色是否爆炸 → 決定政策引擎
- [ ] SSO 真實接駁 + SCIM 供應 + 群組真實同步

---

## 三、里程碑

- [ ] **M1** P0 完成 — 地基活(登入正常 / 角色正確 / 寫操作可用)
- [ ] **M2** ADR-0066 Accepted — 目標架構 + Tier scope 拍板
- [ ] **M3** P2 完成 — 檢索層文件級安全(企業安全先決達成)
- [ ] **M4** 細粒度授權 + 群組(P3+P4)可用
- [ ] **M5** 治理層(P5)可用 — 達企業級營運水平

---

## 四、待決事項(需管理層 / Chris 拍板)

- [ ] **D1** 批准 P0 開工(flip W88 active)
- [ ] **D2** 策略排序:先推 Tier 1 上線 vs P0+P2 安全層併入上線準備(AI 建議後者)
- [ ] **D3** P1 之後階段是否納入正式排期
- [x] **D4** 規劃文件 push → ✅ 已 push 2026-06-23

---

## 五、文件索引(全部歸入 `enterprise-rbac/`)

| 文件 | 用途 |
|---|---|
| [`FINDINGS.md`](./FINDINGS.md) | **事實基準**(現狀 / 實測 / 根因 / 缺口 / 改造性質)— 單一真相來源 |
| [`ROADMAP.md`](./ROADMAP.md) | **策略路線** P0–P6 + Tier 邊界 + 次序 |
| [`REPORT.md`](./REPORT.md) | **對上匯報** 快照 v2 |
| [`RECORD.md`](./RECORD.md) | **調查紀錄** archive(歷程 / 糾正 / 決定) |
| `TRACKER.md`(本檔) | **持續追蹤入口** |
| [`../W88-rbac-p0-foundation/`](../W88-rbac-p0-foundation/) | **P0 phase 執行**(plan / checklist / progress) |
| `../../adr/0027-users-tier-1-5-rbac.md` | W24c RBAC 架構決策(已實作) |

---

## 六、變更日誌

| 日期 | 變動 | 由 |
|---|---|---|
| 2026-06-23 | 建立 TRACKER | 初版 |
| 2026-06-23 | 方案 A 整合:抽 `FINDINGS.md` 單一來源、狀態總覽去重引用、文件索引更新為 enterprise-rbac/ 新結構 | 文件整合 |

---

> **使用說明**:呢份係項目入口 + 持續追蹤點。完成任何項 → 勾選 + 改狀態 + 補變更日誌;各 phase kickoff 喺對應 W{NN} folder 建詳細清單,本 TRACKER 同步展開該階段細項。事實 / 數據統一改 [`FINDINGS.md`](./FINDINGS.md)。
