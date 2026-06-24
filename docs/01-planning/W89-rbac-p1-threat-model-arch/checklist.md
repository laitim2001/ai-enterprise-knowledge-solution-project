# W89 P1 — Checklist

> 對應 [`plan.md`](./plan.md) §2 F1-F3 + §3 Decision Gates。完成 → `[x]` + progress Day-N 記錄。
> 未完項**不可刪**(per CLAUDE.md §10 sacred rule),只 `→ [x]` 或標 🚧 + 理由。

## F1 威脅模型 + 需求
- [ ] 攻擊面分析(認證 / 授權 / 檢索 / 注入 / 越權路徑)
- [ ] confused deputy 分析(LLM 喺檢索階段撈無權內容 → 摘要洩漏)
- [ ] 檢索層洩漏路徑(現 KB 層守衛 vs 文件/chunk 層缺口,對標 FINDINGS §4)
- [ ] 需求收集 + DG1-DG3 default 假設(資料分類 / 用戶類型 / 合規 / 租戶數)

## F2 目標授權模型
- [ ] 資源層級設計(KB → 資料夾 → 文件 → chunk 授權維度)
- [ ] RBAC + ABAC 邊界(角色 vs 屬性,邊個層用邊個)
- [ ] 索引 ACL 結構選項(Azure AI Search `filter` 落地方式 + 多選項 trade-off,次序鐵律 1)
- [ ] 對齊 H2 vendor lock(Azure AI Search S1 原生 `filter`,唔撞)

## F3 ADR-0066 草擬 + Accept
- [ ] 撰寫 `docs/adr/0066-*.md`(Context / Decision / Alternatives / Consequences,Status: Proposed)
- [ ] 更新 `docs/adr/README.md` index
- [ ] **DG4 Tier 邊界拍板**(P2 檢索層 = Tier 1 上線先決 vs Tier 2)→ Chris
- [ ] **DG5 ADR-0066 Accept**(Chris approve,H1 + H4 硬閘)→ Status: Accepted

## Phase Gate(收尾)
- [ ] F1-F3 文檔完成 + decision gate 狀態明確
- [ ] ADR-0066 至少 Proposed(Accept 視 Chris)
- [ ] 更新 TRACKER P1 + FINDINGS(若需)
- [ ] P1 closeout + P2 kickoff 前置條件清單(DG4/DG5 gate)
