# ADR-0067: Document-Level ACL Override + Group Inheritance(文件級存取覆寫 + 群組繼承架構)

**Date**: 2026-06-24
**Status**: Proposed
**Approver**: Chris(decision owner;Accept 需 H1 + H4 硬閘 — 同 ADR-0066 一樣可由用戶 session 行使 decision owner 拍板)

> Enterprise RBAC track P3 產出。在 ADR-0066(P2,檢索層文件級 ACL,5.1 KB 繼承)之上設計 **5.2 文件級 `doc_acl` override** + **P4 群組繼承**。**Proposed → Accept 後解鎖 P3 implementation**(ROADMAP 次序鐵律 5)。
> 技術基礎:[`../01-planning/W91-rbac-p3-doc-acl-design/threat-model-p3.md`](../01-planning/W91-rbac-p3-doc-acl-design/threat-model-p3.md)(F1 G6/G7)+ [`target-architecture-p3.md`](../01-planning/W91-rbac-p3-doc-acl-design/target-architecture-p3.md)(F2)。

## Context

P2(W90,ADR-0066)令檢索層文件級 security trimming 上線就緒,但 `allowed_principals` 來源只係 **5.1 KB 繼承**(整個 KB 共用同一 ACL,principal 只 user oid)。F1 威脅模型(P3)確認兩個企業級缺口:

- **G6 文件級 override 缺**:同一 KB 內**唔同文件唔同權限做唔到**。`allowed_principals` 唯一來源 = `resolve_kb_principals(kb_id)`(KB 層),一個 KB 所有 doc stamp 同一 principal list。攻擊情景:`staff_handbook` KB grant 員工 query → 員工 oid 喺薪資文件 `allowed_principals` → query 薪資 → LLM 洩漏。**P2 解咗跨 KB 洩漏,但同 KB 內文件級洩漏未解。**
- **G7 群組繼承缺**:`kb_acl` / `doc_acl` 可 grant `principal_type="group"`,但 `principals_for_user` 只返 `[oid]` 無 group 展開 → group 授權對 user 無效。`group_members` 表已存在(W24c F6)但無寫方法。

**單租戶 + 2 級分類**(承 ADR-0066 DG2/DG1)。文件係授權邊界(chunk 級獨立授權已 ADR-0066 否決)。

**關鍵洞察(re-stamp 不對稱)**:chunk `allowed_principals` 存 group **key** 非 member oid → **群組成員加減 = 純 query 側 `principals_for_user` 展開 → 零索引 re-stamp**。只有 doc/kb 嘅 principal 集變動先需 restamp。令 P4 成本極低。

## Decision

採目標授權模型(F2),在 P2 `allowed_principals` Collection 之上設計,**唔加索引欄位、無索引重建**:

1. **5.2 `doc_acl` override 表**(G6):新建 `document_acls(kb_id, doc_id, principal_type, principal_id, access_role, granted_by, created_at, UNIQUE(kb_id, doc_id, principal_type, principal_id))`。Store mirror 既有 per-doc store pattern(Protocol + InMemory + Postgres + factory),但 per-doc 多行;復用 `KbPrincipalType` / `KbAclRole` enum。API mirror `kb_acl` 路由 → `/kb/{kb_id}/docs/{doc_id}/acl`(admin / KB-manage 守衛)。

2. **override 語義 = replace**(DG-P3-A,用戶 2026-06-24 拍板):ingest stamp 時,文件**有** `doc_acl` 行 → `allowed_principals` = doc_acl 嘅 principals;**無** → 繼承 KB(`resolve_kb_principals`,P2 現狀)。short-circuit,清晰;直接表達 G6 主場景(KB 全員可見但某文件收窄到子集)。

3. **P4 群組繼承**(G7):
   - **chunk 側**:`resolve_kb_principals` / `doc_acl` 已返 group key → stamp 落 chunk(已 work)。
   - **user 側**:`principals_for_user` 由純 sync 改 **async + rbac_backend 依賴** → 非 admin 返 `[oid] ∪ {user 所屬 group_key}`(查 `group_members`)。**唔改下游 11 層 `user_principals` threading 鏈**(下游收 `list[str]` 不變),只改其計算 + query handler call site await。
   - **group membership 來源 = 手動 admin 管理**(DG-P3-B,用戶拍板):復用 `group_members` 表 + 加寫方法(`add_member` / `remove_member` / `list_groups_for_user`)+ admin 指派 UI。真 SCIM/Entra 自動同步 = **Tier 2**(`source` / `synced_at` 欄位已預留)。

4. **re-stamp 機制**:doc_acl grant/revoke → restamp 該文件 chunks 嘅 `allowed_principals`(復用 P2.3 `IndexPopulator.update_doc_*` search-then-merge,無 re-ingest)→ 新 `update_doc_principals`。**group member 加減 → 零 re-stamp**(query 側解析)。順帶補 P2 遺留(kb_acl ingest 後改動未 restamp 現有 chunk)。

5. **principal 命名空間**:user oid(Azure AD object id GUID)vs group key;local group key 強制 `grp-` 前綴約定防碰撞,顯式 `principal_type` 區分。

6. **Tier 定位 = Tier 1.5 post-launch enhancement**(DG-P3-C,用戶拍板):P2 已達 launch 安全(DG4);P3 設計即做(本 ADR),**implementation 等真實 doc-level 需求 driver**(某 KB 確實要分文件權限)→ 避 speculative。

7. **P3 分段**(implementation,ADR Accept 後):P3a doc_acl 表 + Store + API + replace 解析 + restamp(G6)→ P3b(=P4)group_members 寫方法 + `principals_for_user` 展開(G7)。

## Alternatives Considered

- **override 語義 additive(UNION KB)**:doc principals = KB 繼承 ∪ doc_acl。只能加唔能減 → 解唔到「KB 全員 grant 但某文件收窄」(G6 主場景)→ **reject**。
- **override 語義 allow + deny**:doc_acl 可 allow 亦可 deny(扣減 KB 繼承)。最靈活但 filter 要 encode 排除(`not allowed_principals/any(p: p eq 'denied')`)+ 語義難解釋 + Tier 1 過度 → **defer Tier 2**。
- **group member 來源 = Entra/SCIM 自動同步**:零手動,但撞 H4 鄰近(真 SSO/SCIM)+ 需 Entra 整合(Track A 未 ready)→ **defer Tier 2**(`source='entra'` 預留)。
- **chunk 存 member oid(非 group key)**:group 改動就要 re-stamp 所有相關 chunk(跨文件跨 KB,牽連大)→ **reject**(group key + query 側展開 = 零 re-stamp,優越)。
- **chunk 級獨立 ACL**:ADR-0066 已否決(索引膨脹 + 文件係自然授權邊界)→ 沿用文件繼承。

## Consequences

- **Positive**:同 KB 內文件級分權(G6 confused deputy 根治);group 授權真正落地(G7);沿用 P2 `allowed_principals` Collection + Azure `any()` filter,**零新 vendor(H2)、零新索引欄位、無索引重建**;group member 改動零 re-stamp(query 側);replace 語義易解釋。
- **Negative**:doc_acl 改動需 restamp 該文件 chunks(P2.3 機制,可控);`principals_for_user` 變 async(threading call site 微調,但唔影響下游 11 層);admin 需手動維護 group member(Tier 1.5 取捨)。
- **Neutral**:P3 = Tier 1.5 post-launch(範圍明確非上線阻塞 — DG-P3-C);真 SCIM member 同步劃 Tier 2(需將來 ADR + H4 review);順帶補 P2 kb_acl-change-restamp 遺留缺口。

## References

- [`threat-model-p3.md`](../01-planning/W91-rbac-p3-doc-acl-design/threat-model-p3.md)(F1 G6/G7 + re-stamp 不對稱洞察)
- [`target-architecture-p3.md`](../01-planning/W91-rbac-p3-doc-acl-design/target-architecture-p3.md)(F2 設計 + DG 選項 trade-off)
- ADR-0066(P2 檢索層文件級 ACL,本 ADR 擴充其 5.1 KB 繼承 → 5.2 文件級 + group)
- ADR-0027(W24c RBAC,`kb_acl` / `groups` / `group_members` 基建來源)
- DG resolution(W91 plan §3 + AskUserQuestion,用戶 2026-06-24 拍板 DG-P3-A replace / DG-P3-B 手動 group / DG-P3-C Tier 1.5)
