# W89 P1 — Checklist

> 對應 [`plan.md`](./plan.md) §2 F1-F3 + §3 Decision Gates。完成 → `[x]` + progress Day-N 記錄。
> 未完項**不可刪**(per CLAUDE.md §10 sacred rule),只 `→ [x]` 或標 🚧 + 理由。

## F1 威脅模型 + 需求 → [`threat-model.md`](./threat-model.md)
- [x] 攻擊面分析(6 面,query 端點 + 檢索層 + 合成層 = 🔴 最關鍵)
- [x] confused deputy 分析(LLM 檢索階段撈無權內容 → 摘要洩漏,§3)
- [x] 檢索層洩漏路徑(5 缺口 G1-G5 + file:line 證據;**G1 query 端點連 KB 層守衛都無** = 獨立 P0-style 缺口可快補,G2-G4 文件級 = P2 主體)
- [x] 需求收集 + DG1-DG3(§6 需求表;DG1/DG2 用戶定,DG3 default)

## F2 目標授權模型 → [`target-architecture.md`](./target-architecture.md)
- [x] 資源層級設計(KB → 文件 → chunk 繼承;P1 設計到文件級,單租戶無 tenant 維度)
- [x] RBAC + ABAC 邊界(RBAC 粗:role+kb_acl / 文件 ACL+classification 細:檢索層 trimming;唔用全 ABAC 政策引擎 = P6)
- [x] 索引 ACL 結構選項(A `allowed_principals` Collection + classification **推薦** / B 只 classification 唔夠 / C 外部 post-filter 違原則;Azure `any()` filter,次序鐵律 1)
- [x] 對齊 H2 vendor lock(Azure AI Search S1 原生 Collection + `any()` filter,唔加 vendor)
- [x] 文件 ACL 來源(5.1 KB 繼承=P2 起點 / 5.2 文件級表=P3)+ ingestion stamp 機制 + P2.0-P2.3 落地分段

## F3 ADR-0066 草擬 + Accept
- [x] 撰寫 `docs/adr/0066-enterprise-retrieval-layer-document-acl.md`(Context / Decision / Alternatives / Consequences / References,**Status: Proposed**)
- [x] 更新 `docs/adr/README.md` index(0066 Proposed + next → 0067)
- [x] **DG4 Tier 邊界**(P2 = Tier 1 上線先決)→ 用戶 2026-06-24 代定方向(正式 Tier 邊界拍板隨 DG5 ADR Accept)
- [ ] 🚧 **DG5 ADR-0066 Accept**(Chris approve,H1 + H4 硬閘)→ Status: Accepted。**待 Chris**:P2+ implementation 喺 Accept 前不可開工(次序鐵律 5)

## Phase Gate(收尾)
- [x] F1-F3 文檔完成 + decision gate 狀態明確(DG1/DG2/DG4 用戶定,DG3 default,DG5 待 Chris)
- [x] ADR-0066 至少 Proposed(Accept 視 Chris = DG5)
- [x] 更新 TRACKER P1 + FINDINGS(若需)
- [x] P1 closeout + P2 kickoff 前置條件 = DG5 ADR-0066 Accept(Chris)
