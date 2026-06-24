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
| **P0** | 基礎校正 + W24c 收尾 | ✅ **核心完成** | 2026-06-24 F1-F6 全綠(209 pytest);2 項 surface 待決(documents 守衛 / live smoke) |
| P1 | 威脅模型 + 目標架構 + ADR-0066 | 🔲 未開始 | 依賴 P0 |
| P2 | 檢索層文件級存取控制 | 🔲 未開始 | 依賴 P1;可能係上線先決 |
| P3 | 文件/資料夾級細粒度授權 | 🔲 未開始 | 依賴 P2 |
| P4 | 群組存取(成員 + 繼承) | 🔲 未開始 | 真實同步隨 SSO 延後 |
| P5 | 管理權分級 + 存取治理 | 🔲 未開始 | 依賴 P3 |
| P6(選) | 屬性式權限 / 政策引擎 | ⏭️ 延後 | 規模化才需 |
| SSO/SCIM | 真實 SSO + 自動供應 | ⏭️ 延後 | 用戶決定後加 |

**整體定調(2026-06-24 更新)**:規劃完成;**P0 核心完成 — 地基已活**(首位管理員 bootstrap 生效 / 角色正確解析 / `/users` + KB 寫操作可用且受 RBAC 守衛,209 pytest 為證)。企業核心(檢索層安全 / 群組 / SSO)仍 0%,待 P1 拍板。**下一步:用戶決 2 待決 + P1 威脅模型 + ADR-0066。**

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

### P0 — 基礎校正 + W24c 收尾(✅ 核心完成 2026-06-24,2 項 surface 待決 → 細項見 [`../W88-rbac-p0-foundation/checklist.md`](../W88-rbac-p0-foundation/checklist.md))
- [x] **批准開工**(2026-06-24 用戶批准 flip active)
- [x] F1 基準確認 — HEAD=disk=running backend 三層乾淨四級**已自愈**;幻欄位 0 match;剩真實債=帳號 role+verified(移交 F2)
- [x] F2 修首位用戶自動管理員(bootstrap)+ role 值一致性 — `register()` first-user→admin + `ensure_admin_bootstrap()` self-heal(commit `e3809e1`);端到端重啟驗 `admin@example.com` user→admin + verified f→t
- [x] F3 前端硬編「Workspace Admin」badge → 讀真 role — `useRole()` + 複用 `RoleBadge`(commit `b4cfceb`);playwright 兩處驗
- [x] F4 `/users` 寫操作接通(改 role / 邀請 / 停用)— InviteDialog/RowActionMenu/SuspendDialog 接 `usersApi`(commit `7ff7588`);①讀 ②設計 ③mockup ④前端對齊 + H7 verify
- [x] F5 KB endpoints 補接 `require_kb_acl` — kb.py 7 寫端點守衛(映射 permission matrix)+ 18 新測試 + 4 整合測試 wire admin;209 RBAC/auth pytest 全綠
- [x] F6 Phase Gate 驗證 — G1-G6 綠(209 passed / 8 skipped)+ ruff + mypy;🚧 端到端 live smoke deferred(pytest 已充分,重啟大動作 surface)
- [x] P0 closeout + 更新本 TRACKER + `FINDINGS.md` 基準
- **待決(surface)**:① documents.py 4 寫端點守衛(相鄰缺口,納 P0 補完 vs 留 P1)② 端到端 live smoke 是否重啟 backend 做

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

- [x] **M1** P0 核心完成 — 地基活(登入正常 / 角色正確 / 寫操作可用且受守衛)✅ 2026-06-24(live smoke + documents 守衛 2 項 surface 待決)
- [ ] **M2** ADR-0066 Accepted — 目標架構 + Tier scope 拍板
- [ ] **M3** P2 完成 — 檢索層文件級安全(企業安全先決達成)
- [ ] **M4** 細粒度授權 + 群組(P3+P4)可用
- [ ] **M5** 治理層(P5)可用 — 達企業級營運水平

---

## 四、待決事項(需管理層 / Chris 拍板)

- [x] **D1** 批准 P0 開工 → ✅ 2026-06-24 用戶批准 flip active
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
| [`COLLABORATION-SOP.md`](./COLLABORATION-SOP.md) | **協作 SOP**(開工收工 / 溝通 / 護欄 / 決策把關 / 環境應對) |
| `TRACKER.md`(本檔) | **持續追蹤入口** |
| [`../W88-rbac-p0-foundation/`](../W88-rbac-p0-foundation/) | **P0 phase 執行**(plan / checklist / progress) |
| `../../adr/0027-users-tier-1-5-rbac.md` | W24c RBAC 架構決策(已實作) |

---

## 六、變更日誌

| 日期 | 變動 | 由 |
|---|---|---|
| 2026-06-23 | 建立 TRACKER | 初版 |
| 2026-06-23 | 方案 A 整合:抽 `FINDINGS.md` 單一來源、狀態總覽去重引用、文件索引更新為 enterprise-rbac/ 新結構 | 文件整合 |
| 2026-06-24 | P0 flip active(用戶批准)+ 重建 W88 三件套(OneDrive 吞文件後)+ 修 broken reference;F1 環境基準實測(disk `rbac.py` 已自愈追上 HEAD) | P0 開工 |
| 2026-06-24 | **P0 F1-F6 核心完成** — F5 KB 寫端點補 RBAC 守衛(映射 permission matrix)+ F6 Phase Gate(209 RBAC/auth pytest 全綠 + ruff + mypy)+ closeout;M1 達成。2 待決 surface(documents 守衛擴充 / 端到端 live smoke) | P0 核心完成 |

---

> **使用說明**:呢份係項目入口 + 持續追蹤點。完成任何項 → 勾選 + 改狀態 + 補變更日誌;各 phase kickoff 喺對應 W{NN} folder 建詳細清單,本 TRACKER 同步展開該階段細項。事實 / 數據統一改 [`FINDINGS.md`](./FINDINGS.md)。
