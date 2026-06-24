# W89 P1 — Progress

> 每日進展 + 決策 + commits + 結尾 retro。對應 [`checklist.md`](./checklist.md)。

## Day 1 — 2026-06-24(P1 kickoff)

### 開工背景
- P0 完全完成(2026-06-24,M1「地基活」達成 + 寫操作受守衛;F1-F6 + F5b + F6b)。
- 用戶 2026-06-24「而家開 P1」→ rolling JIT 建 W89 三件套(per R1,P0 收尾後才建)。
- **P1 性質 ≠ P0**:P0 純技術校正可自主推進;P1 = **設計 phase**,產出 ADR-0066,涉及 **Tier 邊界拍板**(H1/H4 需 Chris)+ 威脅模型需 **stakeholder 輸入**(資料分類/合規/租戶數)。

### P1 scope 定調(per ROADMAP §2-§3)
- P1 = 威脅模型 + 目標授權模型 + ADR-0066,**唔 implement**(implementation = P2+)。
- 次序鐵律 1:影響索引結構嘅決定最先定(P1 拍板 → P2 動索引)。
- 次序鐵律 5:P2+ 開工前 = ADR-0066 Accepted + Chris approve(H1+H4 硬閘)。

### Decision gates 識別(plan §3)
- DG1 資料分類 / DG2 用戶類型+租戶數 / DG3 合規 → 可用 default 假設推進 F1/F2 技術分析。
- **DG4 Tier 邊界拍板**(P2 = Tier 1 上線先決 vs Tier 2)+ **DG5 ADR-0066 Accept** → Chris 硬拍板,P2 開工前必須 resolve。
- AI 自主範圍 = F1 威脅模型技術分析 + F2 目標架構技術選項 + F3 草擬 ADR-0066(Proposed);**Tier 邊界 + ADR Accept 唔自行定**(H1+H4)。

### DG resolution(用戶 2026-06-24 拍板 DG1/DG2/DG4)
- **DG1 = 2 級 internal / restricted**(索引加 1 個 `classification` 欄位)。
- **DG2 = 單租戶 Ricoh internal**(純 Tier 1,索引無 tenant 維度,唔撞 H4)。
- **DG4 = P2 檢索層 = Tier 1 上線先決**(confused deputy 洩漏 = 上線阻塞)。
- → **F2 索引 ACL 方向確定**:文件級 ACL(principal + access_role)+ `classification` 欄位,單租戶,Azure AI Search `filter`。
- DG3 用 default(無特定合規);**DG5 ADR-0066 Accept 仍待 Chris**(H1+H4)。

### F1 威脅模型 + 需求(2026-06-24 ✅ 完成)→ `threat-model.md`
- Explore agent 調查檢索/查詢/合成路徑 ACL 現狀 → **5 缺口確認**(file:line):
  - **G1 query 端點無授權守衛**(`query.py:203-218`、`:530-534` 連 KB 層 `require_kb_acl` 都無)= 獨立 P0-style 缺口,可快補
  - G2 檢索層無文件 filter(`hybrid.py:354-355` 只 `kb_id`)/ G3 索引 schema 無 ACL 欄位(`schema.json`)/ G4 合成層無授權過濾(`synthesizer.py:127-235`,confused deputy 成立)/ G5 KB 層 ACL 存在但 query 未用
- 攻擊情景(員工/經理分層)+ 需求表(DG-derived)+ P2 設計含義(索引加 `allowed_principals` + `classification`,檢索 filter 注入,單租戶簡化)。
- **結論**:檢索層文件級安全完全未實現;G1 即時可補,G2-G4 = P2 主體(索引重建,次序鐵律 1)。

### F2 目標授權模型(2026-06-24 ✅ 完成)→ `target-architecture.md`
- 資源層級:KB → 文件 → chunk 繼承(P1 到文件級,單租戶無 tenant 維度)。
- RBAC+ABAC 邊界:RBAC 粗(role+kb_acl)/ 文件 ACL+classification 細(檢索層 trimming);唔用全政策引擎(P6)。
- **索引 ACL 結構(核心,3 選項)**:A `allowed_principals` Collection + classification = **推薦**(Azure `any()` filter,檢索層真 trimming,單次解決)/ B 只 classification 唔夠(無 principal 級)/ C 外部 post-filter 違「檢索之前/之中」原則。
- 檢索 filter 機制 + 文件 ACL 來源(5.1 KB 繼承=P2 起點 / 5.2 文件級表=P3)+ ingestion stamp + **P2.0-P2.3 落地分段**。
- **次序鐵律 1**:索引加 2 欄位 = ADR-0066 核心拍板;H2 唔撞(Azure 原生)。

### F3 ADR-0066 草擬(2026-06-24 ✅ Proposed)→ `docs/adr/0066-enterprise-retrieval-layer-document-acl.md`
- 撰寫 ADR-0066(Context F1 G1-G5 + Decision 選項 A 索引擴 `allowed_principals`+`classification` + 檢索 filter security trimming + 5.1 KB 繼承 + query `require_kb_acl("query")` + P2.0-P2.3 分段 + Tier 定位;Alternatives B/C/政策引擎/chunk級;Consequences;References)。
- 更新 `docs/adr/README.md` index(0066 Proposed + next 0067)。
- **Status: Proposed** — DG5 ADR Accept 待 Chris(H1+H4 硬閘);**P2+ implementation 喺 Accept 前不可開工**(次序鐵律 5)。

### P1 核心完成(F1-F3 + DG closeout)
- F1 威脅模型 + F2 目標架構 + F3 ADR-0066(Proposed)全完成。DG1/DG2/DG4 用戶定,DG3 default,**DG5 ADR Accept 待 Chris**。
- **P2 kickoff 前置條件 = DG5 ADR-0066 Accept(Chris)**。Accept 後 P2.0(query 守衛快補)→ P2.1(schema+stamp)→ P2.2(filter+重建索引)→ P2.3(classification)。

### 下一步
- **待 Chris review + Accept ADR-0066**(DG5)。Accept 後 kickoff P2(檢索層文件級 ACL implementation)。
- 期間可選:G1 query 端點 KB 層守衛快補(P2.0,獨立於文件級工程)。

### Commits
- (kickoff)docs(planning): kickoff W89 P1 phase artifacts(`284e9f0`)
- docs(planning): record P1 DG1/DG2/DG4 resolution(`2d3138b`)
- docs(planning): W89 P1 F1 threat model(`294080f`)
- docs(planning): W89 P1 F2 target architecture(`fc704a0`)
- (本 entry)docs(planning): W89 P1 F3 ADR-0066 Proposed + P1 closeout
