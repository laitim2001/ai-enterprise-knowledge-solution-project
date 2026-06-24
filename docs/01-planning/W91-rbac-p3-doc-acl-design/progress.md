# W91 P3 設計 — Progress

> 每日進展 + 決策 + commits + 結尾 retro。對應 [`checklist.md`](./checklist.md)。

## Day 1 — 2026-06-24(P3 設計 phase kickoff)

### 開工背景
- P2 完全完成(W90,2026-06-24)→ 檢索層 KB 繼承 + classification clearance 上線就緒,DG4 達成。
- 用戶 AskUserQuestion 拍板:① **開 W91 設計 phase**(mirror W89 P1:設計 + ADR,不 implement)② 範圍 = **5.2 doc_acl + P4 群組繼承**。
- P3 = 跨 Tier 邊界(H1/H4)→ 設計 phase 出 ADR-0067 Proposed,implementation 待 decision owner Accept(次序鐵律 5)。寫設計 + 草擬 ADR 唔 trigger H1 實作閘(precedent:W89 P1 寫 ADR-0066 Proposed 在 Accept 前)。

### kickoff(R1)
- rolling JIT 建 W91 三件套(plan/checklist/progress)。
- plan §3 列 4 個 Decision Gate(DG-P3-A override 語義 / DG-P3-B group 來源 / DG-P3-C Tier 定位 / DG-P3-D ADR Accept),F2 分析後附推薦再由 decision owner 拍板。

### F1 威脅模型補充(✅ `threat-model-p3.md`)
- Explore agent 盤點 RBAC storage 基建(file:line 證據):`doc_acl` **全不存在** / `group_members` 表已存在但**無寫方法**(W24c F6 只同步 group list,member = P4 deferred) / `principal_type="group"` 已支援 / `resolve_kb_principals` 已返 group key / `principals_for_user` 只 `[oid]` / 4 個 per-doc store mirror 同一 pattern。
- **G6 文件級 override 缺口**:`allowed_principals` 唯一來源 = KB 繼承,全 KB 一個 ACL → 同 KB 內分文件權限 = 0(攻擊情景:staff_handbook 薪資對員工洩漏)。
- **G7 群組繼承缺口**:group key stamp 落 chunk OK,但 user 側無展開 → group grant 形同虛設。
- **think-before 修正(Karpathy §1.1)**:plan §4「group membership 改 → re-stamp 所有含該 group chunks」**過度估計**。chunk 存 group **key** 非 member oid → **群組成員加減 = 純 query 側 `principals_for_user` 展開 → 零 re-stamp**。令 P4 成本極低。

### F2 目標授權模型(✅ `target-architecture-p3.md`)
- **doc_acl 表**:`document_acls(kb_id, doc_id, principal_type, principal_id, access_role, …)` 多行,mirror 既有 per-doc store + `kb_acl` 路由(`/kb/{kb_id}/docs/{doc_id}/acl`),復用 `KbPrincipalType`/`KbAclRole`。沿用 P2 `allowed_principals` Collection,**唔加索引欄位**。
- **DG-P3-A override 語義**:三選項(additive / replace / allow+deny),**推薦 replace**(G6 主場景=KB 全員可見但某文件收窄 → replace 直接表達;additive 唔能收窄;allow+deny Tier 1 過度)。
- **DG-P3-B group 來源**:三選項,**推薦手動 admin 管理**(復用 `group_members` 表 + 加寫方法;真 SCIM/Entra = Tier 2)。
- **P4 `principals_for_user`**:改 async + rbac_backend 依賴([oid] → [oid] ∪ group_keys),**唔改下游 11 層 threading**(下游收 list[str] 不變)。
- **DG-P3-C Tier 定位**:**推薦 Tier 1.5 post-launch enhancement**(P2 已達 launch 安全 DG4;P3 等真實 doc-level driver 落 implementation)。
- **re-stamp**:doc_acl 改 → restamp 該文件(復用 P2.3 search-then-merge);group member 改 → 零 restamp;順帶補 P2 遺留(kb_acl ingest 後改未 restamp)。

### DG resolution(用戶 2026-06-24 AskUserQuestion,3 個全採推薦)
- **DG-P3-A = replace 取代**(doc 有 doc_acl → 只用之,無 → 繼承 KB)。
- **DG-P3-B = 手動 admin 管理**(復用 `group_members` 表,真 SCIM = Tier 2)。
- **DG-P3-C = Tier 1.5 post-launch enhancement**(設計即做,impl 等真實 doc-level driver)。

### F3 ADR-0067 草擬(✅ Proposed,`docs/adr/0067-document-level-acl-override-and-group-inheritance.md`)
- Context / Decision(7 點,反映 3 DG)/ Alternatives(additive / allow+deny / Entra-sync / member-oid-in-chunk / chunk 級全 reject 或 defer)/ Consequences / References 齊。
- README summary log 加 0067 Proposed + next NNNN → 0068。
- **Status: Proposed** —— 待用戶以 decision owner 身份 **Accept**(H1+H4 硬閘,次序鐵律 5)→ P3-impl 解鎖。Accept 前唔開任何 implementation。

### 待續(本 phase)
- **decision owner Accept ADR-0067**(用戶拍板)→ 更新 Status Proposed→Accepted → P3-impl(P3a doc_acl 表+API+restamp / P3b group 展開)另期 kickoff。

### Commits
- `f7758d1` docs(planning): W91 P3 kickoff + F1 威脅模型 + F2 目標架構
- (本 entry)docs(adr): ADR-0067 文件級 ACL override + 群組繼承(Proposed)
