# W89 — Enterprise RBAC P1:威脅模型 + 目標授權架構 + ADR-0066

| 項目 | 值 |
|---|---|
| Phase | W89-rbac-p1-threat-model-arch(enterprise RBAC track 第 2 期) |
| Status | **active**(2026-06-24 用戶批准開工) |
| Tier | ⚖️ **Tier 邊界拍板點**(P1 = 設計 + ADR,**唔 implement**;ADR-0066 Accept 需 Chris approve per H1 + H4) |
| 依賴 | P0(✅ 完成 2026-06-24,M1 達成) |
| 錨點 | ADR-0027(W24c)・ 事實基準 [`../enterprise-rbac/FINDINGS.md`](../enterprise-rbac/FINDINGS.md) ・ 路線 [`../enterprise-rbac/ROADMAP.md` §2-§3](../enterprise-rbac/ROADMAP.md) |
| 粗估 | 5–8 日 |
| 下一期 | P2 檢索層文件級存取控制(**ADR-0066 Accepted + Chris approve 後**才 kickoff) |

> **本 plan 受 FINDINGS + ROADMAP 約束**:現狀 / 缺口以 [`../enterprise-rbac/FINDINGS.md`](../enterprise-rbac/FINDINGS.md) 為準,次序鐵律以 ROADMAP §3 為準。本檔只定 scope + deliverables + acceptance + decision gate。

---

## §1 目標(Why)

P0 令地基活起來(登入 / 角色 / 寫操作受守衛)。但企業核心仍 0%(檢索層安全 / 群組 / 治理)。P1 = **設計 phase**:產出企業級**目標授權架構**,拍板 **ADR-0066**,為 P2 檢索層安全鋪路。

**次序鐵律 1(ROADMAP §3)**:影響索引結構嘅決定要**最先定**(P1 拍板 → P2 動索引),否則做錯方向 + 重建成本翻倍。

**P1 唔 implement** —— 唔改 retrieval 主路徑、唔動索引、唔改 schema。implementation = P2+。P1 產出 = 文檔(威脅模型 + 目標架構)+ ADR-0066(Proposed → Chris Accept)。

## §2 Deliverables(F1–F3)

| # | Deliverable | Acceptance(可驗證成功標準) |
|---|---|---|
| F1 | 威脅模型 + 需求 | 攻擊面 + confused deputy + 檢索層洩漏路徑技術分析完成;需求(資料分類 / 用戶類型 / 合規 / 租戶數)收集 — stakeholder 輸入部分標 decision gate + default 假設 |
| F2 | 目標授權模型 | 資源層級設計(KB → 資料夾 → 文件 → chunk)/ RBAC+ABAC 邊界 / **索引 ACL 結構選項**(次序鐵律 1 核心,Azure AI Search `filter` 落地方式)— 技術選項 + 推薦 + trade-off 寫清 |
| F3 | ADR-0066 草擬 + Accept | `docs/adr/0066-*.md` 撰寫(Context / Decision / Alternatives / Consequences)→ **Status: Proposed** → Chris review → Accept(H1 + H4 硬閘) |

## §3 Decision Gates(需 stakeholder / Chris 拍板,P1 阻塞點)

| Gate | 內容 | default 假設(若無輸入) | 阻塞 |
|---|---|---|---|
| **DG1** | 資料分類體系(密級層級數 + 名稱) | Drive Project 假設無 PII(H5);enterprise 預設 2 級(internal / restricted) | F2 索引 ACL 欄位設計 |
| **DG2** | 用戶類型 + 租戶數 | 單租戶(Ricoh internal);**多租戶撞 H4 Tier 2** | F2 + Tier 邊界 |
| **DG3** | 合規要求(GDPR / 行業) | 無特定合規(internal manual) | F1 需求 |
| **DG4** | **Tier 邊界拍板** — P2 檢索層安全 = Tier 1 上線先決 vs Tier 2 後續 | FINDINGS §4 建議「上線先決」 | P2 kickoff |
| **DG5** | **ADR-0066 Accept** | — | P2+ 全部(鐵律 5) |

> DG1-DG3 可用 default 推進 F1/F2 技術分析(標 default 假設 + commit note);DG4/DG5 = Chris 硬拍板,P2 開工前必須 resolve。

## §4 Risks

- 🔴 **Tier 邊界誤判**(active):P2 檢索層若判 Tier 2 → Tier 1 無法安全上線;若判 Tier 1 先決 → 範圍擴大。**DG4 必須 Chris 拍板,AI 唔自行定**(H1 + H4)。
- 🟡 **索引結構選錯**(次序鐵律 1):F2 索引 ACL 設計若選錯,P2 重建成本翻倍 → F2 必須列多選項 + trade-off,唔急 commit 單一方案。
- 🟡 **OneDrive 同步吞文件**(active per P0):Write 後 `git ls-files` 驗入庫。
- 🟢 **唔影響 W43-85 問答品質**:P1 純設計唔 implement,零 retrieval 改動。

## §5 Out of scope(留 P2+)

索引 ACL 欄位**實作** + ingestion stamp + 查詢 `filter` 注入 + 索引重建(全 P2)/ 文件夾級細粒度(P3)/ 群組同步(P4)/ 治理(P5)/ 真實 SSO。P1 **只**設計 + 拍板,不寫 production code(retrieval / schema / index 一律不動)。

## §6 Changelog

| 日期 | 變動 | 由 |
|---|---|---|
| 2026-06-24 | P1 kickoff — P0 收尾後 rolling JIT 建三件套;用戶批准開工;scope = 設計 + ADR-0066,不 implement | 開工 |
