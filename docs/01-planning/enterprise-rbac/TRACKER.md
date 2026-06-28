# Enterprise RBAC — 項目工作追蹤清單(TRACKER)

> **用途**:呢個獨立項目嘅**跨階段持續追蹤入口**。每次有進展 → 勾選對應項 + 更新狀態 + 補變更日誌。
> **最後更新**:2026-06-25 ・ **Owner**:Chris(技術 Lead)
> **狀態圖例**:🔲 未開始 ・ 🟡 進行中 ・ ✅ 完成 ・ ⏸️ 待批准 ・ 🚫 阻塞 ・ ⏭️ 延後
> **現狀 / 實測 / 缺口詳情**:見 [`FINDINGS.md`](./FINDINGS.md)(本檔只追蹤狀態,事實不複製)

---

## 一、狀態總覽

| 階段 | 內容 | 狀態 | 備註 |
|---|---|---|---|
| 規劃 | 路線圖 + P0 計劃 + 報告 + 紀錄 + 文件整合 | ✅ 完成 | 已 commit + push |
| **P0** | 基礎校正 + W24c 收尾 | ✅ **完成** | 2026-06-24 F1-F6 + F5b + F6b 全綠(209 pytest + live smoke);2 待決均 resolve |
| **P1** | 威脅模型 + 目標架構 + ADR-0066 | ✅ **完成** | 2026-06-24 F1-F3 + ADR-0066 **Accepted**(用戶 decision owner 拍板);M2 達成 |
| **P2** | 檢索層文件級存取控制 | ✅ **完成** | 2026-06-24 P2.0-P2.3 全完成(W90,檢索層 KB + classification trimming 上線就緒,DG4 達成;commit `5fca451`/`0d4fb20`)|
| **P3** | 文件/資料夾級細粒度授權 | ✅ **完成** | 2026-06-24 W92 P3a doc_acl override(G6,commit `041813b`)|
| **P4** | 群組存取(成員 + 繼承) | ✅ **完成** | 2026-06-24 W93 P3b group 繼承(G7,commit `433ab74`,併入 P3-impl;真 SCIM 同步仍 Tier 2 延後)|
| **P5** | 管理權分級 + 存取治理 | 🟡 **設計完成** | 2026-06-25 W94 設計 + **ADR-0068 Accepted**(auditor role + access review,範圍核心 + 存取覆核);implementation 待用戶另批(Tier 1.5)|
| P6(選) | 屬性式權限 / 政策引擎 | ⏭️ 延後 | 規模化才需 |
| SSO/SCIM | 真實 SSO + 自動供應 | ⏭️ 延後 | 用戶決定後加 |

**整體定調(2026-06-25 更新)**:**P0-P4 全完成 + P5 設計拍板**。安全核心已就緒 —— 檢索層文件級 security trimming(P2)+ 文件級 doc_acl override(P3 / G6)+ 群組繼承(P4 / G7)上線就緒,**Tier 1 上線安全先決(DG4)達成**。P5 治理層(auditor 職責分立 + 存取覆核)設計拍板(ADR-0068 Accepted),依 Tier 1.5 **暫不 implement**。**剩餘:P5-impl(等用戶另批)/ P6 + SSO/SCIM(Tier 2 延後)/ Production launch 待 Track A IT cred。**

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
- [x] **F5b** documents.py 4 寫端點補 `require_kb_acl("edit")`(用戶選 P0-extend,commit `a333884`,74 pass)
- [x] F6 Phase Gate 驗證 — G1-G6 綠(209 passed / 8 skipped)+ ruff + mypy
- [x] **F6b** 端到端 live smoke(用戶選重啟,重啟 backend READY ~56s + 7 case 驗守衛 live 生效)
- [x] P0 closeout + 更新本 TRACKER + `FINDINGS.md` 基準
- **2 待決均 resolve(2026-06-24)**:① documents.py 守衛已補(F5b)② live smoke 已做(F6b)

### P1 — 威脅模型 + 目標架構 + ADR-0066(🟡 進行中 2026-06-24 → 細項見 [`../W89-rbac-p1-threat-model-arch/checklist.md`](../W89-rbac-p1-threat-model-arch/checklist.md))
- [x] 建立 W89 P1 phase folder(三件套,rolling JIT)
- [x] F1 威脅模型 + 需求(`threat-model.md`,5 缺口 G1-G5 + confused deputy + DG-derived 需求)
- [x] F2 目標授權模型(`target-architecture.md`,選項 A 索引 ACL 推薦 + 檢索 filter + 5.1 KB 繼承 + P2.0-P2.3 分段)
- [x] F3 撰寫 ADR-0066(**Proposed**,`docs/adr/0066-enterprise-retrieval-layer-document-acl.md`)+ DG4 用戶定方向
- [x] **DG5 ADR-0066 Accept**(用戶 2026-06-24 decision owner 拍板)→ Status **Accepted**,P2 解鎖(次序鐵律 5 satisfied)

### P2 — 檢索層文件級存取控制(✅ 完成 2026-06-24,W90 P2.0-P2.3,commit `5fca451`/`0d4fb20`)
- [x] 索引結構加 ACL / 密級欄位(`allowed_principals` Collection + `classification`)
- [x] ingestion stamp 文件 ACL
- [x] 查詢時注入 Azure AI Search filter(security trimming;query 端點補 KB 層守衛 G1)
- [x] 答案 / 引用層確認唔洩漏
- [x] 重建索引 + 驗證唔影響問答品質(north-star §15)

### P3 — 文件/資料夾級細粒度授權(✅ 完成 2026-06-24,W92 P3a doc_acl override G6,commit `041813b`)
- [x] 授權表擴資源層級維度 + 繼承 + 覆寫(`doc_acl` replace 語義,沿用 `allowed_principals` 零新索引欄位)
- [ ] 細粒度授權管理介面(UI — Tier 1.5,等真實 doc-level driver,per ADR-0067 DG-P3-C)

### P4 — 群組存取(✅ 完成 2026-06-24,W93 P3b group 繼承 G7,commit `433ab74`)
- [x] 群組成員模型 + 繼承解析(query 側 `principals_for_user` 展開,group member 改動零 re-stamp)
- [x] 手動成員(復用 `group_members` 表,per ADR-0067 DG-P3-B;真 SCIM 自動同步仍 Tier 2 延後)

### P5 — 管理權分級 + 治理(🟡 設計完成 — W94 + ADR-0068 Accepted 2026-06-25;impl 待用戶另批)
- [x] **設計 + ADR-0068 Accepted**(W94:F1 威脅模型 G8 職責分立 / G9 存取覆核 + F2 目標架構 + ADR)
- [ ] 角色分立(超管 / 管理 / 稽核員 / 擁有者)→ **設計收窄:只加 auditor 唯讀稽核**(super-admin/owner push-back 成立留後期,per DG-P5-B);P5-impl 等用戶另批
- [ ] 存取覆核 + 生命週期(JIT / 回收 / break-glass)→ **設計收窄:access-review report + re-certify 標記**(JIT/回收/break-glass 延後 Tier 2,per DG-P5-C/D);P5-impl 等用戶另批

### P6(選)/ SSO(⏭️ 延後)
- [ ] P6 評估角色是否爆炸 → 決定政策引擎
- [ ] SSO 真實接駁 + SCIM 供應 + 群組真實同步

---

## 三、里程碑

- [x] **M1** P0 核心完成 — 地基活(登入正常 / 角色正確 / 寫操作可用且受守衛)✅ 2026-06-24(live smoke + documents 守衛 2 項 surface 待決)
- [x] **M2** ADR-0066 Accepted — 目標架構 + Tier scope 拍板 ✅ 2026-06-24(用戶 decision owner 拍板)
- [x] **M3** P2 完成 — 檢索層文件級安全(企業安全先決達成)✅ 2026-06-24(P2.0-P2.3,DG4 達成)
- [x] **M4** 細粒度授權 + 群組(P3+P4)可用 ✅ 2026-06-24(P3a doc_acl G6 + P3b group G7)
- [ ] **M5** 治理層(P5)可用 — 達企業級營運水平(設計 ADR-0068 Accepted 2026-06-25;**impl 待用戶另批**)

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
| 2026-06-24 | **P0 完全完成** — F5b documents.py 4 寫端點補 `require_kb_acl("edit")`(commit `a333884`)+ F6b 重啟 backend 端到端 live smoke(7 case 驗守衛 live 生效);2 待決均 resolve | P0 完成 |
| 2026-06-24 | **P1 核心完成** — kickoff(`284e9f0`)+ DG1/DG2/DG4 resolution(`2d3138b`)+ F1 威脅模型(`294080f`)+ F2 目標架構(`fc704a0`)+ F3 **ADR-0066 Proposed**;DG5 Accept 待 Chris(P2 前置,次序鐵律 5) | P1 核心完成 |
| 2026-06-24 | **P1 完全完成 + P2 解鎖** — 用戶 decision owner 拍板 **Accept ADR-0066**(Proposed→Accepted),DG5 resolved + M2 達成;P0+P1 15 commits push origin/main;**W90 P2 kickoff**(檢索層文件級 ACL,P2.0-P2.3) | P1 完成 / P2 開工 |
| 2026-06-25 | **P2-P4 完成 sync + P5 設計拍板** — TRACKER stale 更新(P2.0-P2.3 / P3a G6 / P3b G7 全完成,M3 + M4 達成);W94 P5 設計 phase + **ADR-0068 Accepted**(auditor role 職責分立 + access review,範圍核心 + 存取覆核,JIT/break-glass 延後 Tier 2);P5-impl 待用戶另批(Tier 1.5) | P5 設計完成 |
| 2026-06-28 | **第二節工作清單 checkbox 補勾**(P2/P3/P4 section 標題仍 🔲 + 子項全 `[ ]`,與「一、狀態總覽」+「三、里程碑」矛盾;對齊狀態總覽勾選已完成子項,P3 管理介面 UI + P4 SCIM 保留未勾並加 Tier 1.5/Tier 2 註)| BACKLOG 機制啟動 stale 修正 |

---

> **使用說明**:呢份係項目入口 + 持續追蹤點。完成任何項 → 勾選 + 改狀態 + 補變更日誌;各 phase kickoff 喺對應 W{NN} folder 建詳細清單,本 TRACKER 同步展開該階段細項。事實 / 數據統一改 [`FINDINGS.md`](./FINDINGS.md)。
