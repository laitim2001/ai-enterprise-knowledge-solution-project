# W91 P3 設計 — Checklist

> 對應 [`plan.md`](./plan.md) §2 F1-F3 + §3 Decision Gates。完成 → `[x]` + progress Day-N 記錄。
> 未完項**不可刪**(per CLAUDE.md §10 sacred rule),只 `→ [x]` 或標 🚧 + 理由。
> **約束**:P3 = 設計 phase,**不寫 production code**(retrieval / schema / 表 / `principals_for_user` 不動)。

## F1 威脅模型補充(doc-level + group)(✅ `threat-model-p3.md`)
- [x] G6 文件級 override 缺口:同 KB 內分文件權限做唔到(現 `allowed_principals` = KB 繼承,全 KB 一個 ACL)+ 攻擊情景(staff_handbook 薪資洩漏)+ codebase 證據(`doc_acl` 不存在 / `resolve_kb_principals` 只 KB 層)
- [x] G7 群組繼承缺口:`principals_for_user` 只返 `[oid]`(`acl.py:152-164`)、group key stamp 落 chunk 但無 member resolve(`group_members` 無寫方法)+ codebase 證據
- [x] re-stamp 牽連分析:**修正 plan §4 過度估計** —— doc_acl 改 → restamp 該文件 chunks;**group membership 改 → 零 re-stamp**(chunk 存 group key 非 member oid,純 query 側展開)

## F2 目標授權模型(P3)(✅ `target-architecture-p3.md`)
- [x] 5.2 `doc_acl` override 表設計:`document_acls(kb_id, doc_id, principal_type, principal_id, access_role, …)` 多行 + Store mirror per-doc pattern + API mirror `kb_acl` 路由 + override 語義(DG-P3-A 三選項,**推薦 replace**)+ ingest 解析(doc_acl 有行 → 用之,無 → KB 繼承 short-circuit)
- [x] P4 群組繼承設計:group membership 來源(DG-P3-B 三選項,**推薦手動 admin** 復用 `group_members`)+ `principals_for_user` 改 async + group 展開([oid] → [oid, grp…],不改下游 11 層 threading)+ principal 命名空間(group key 前綴約定防碰撞)
- [x] re-stamp 機制:doc_acl 改 → restamp 該文件(復用 P2.3 `update_doc_*` search-then-merge);**group member 改 → 零 re-stamp**(query 側);順帶補 P2 遺留(kb_acl ingest 後改未 restamp)
- [x] 每 fork 列選項 + trade-off + 推薦(對齊 ADR-0066 選項分析風格)

## F3 ADR-0067 草擬 + Accept
- [x] `docs/adr/0067-document-level-acl-override-and-group-inheritance.md` 撰寫(Context / Decision / Alternatives / Consequences / References)→ **Status: Proposed** + README summary log 加 0067 + next NNNN → 0068
- [x] DG-P3-A/B/C resolution 寫入 ADR Decision(用戶 2026-06-24 AskUserQuestion 拍板:replace / 手動 admin group / Tier 1.5 post-launch)
- [ ] 🚧 decision owner review → **Accept**(H1+H4 硬閘)→ 更新 ADR Status Proposed→Accepted + README — **待用戶以 decision owner 身份 Accept**(次序鐵律 5,P3-impl 解鎖前置)

## Phase Gate(收尾)
- [ ] F1+F2+F3 完成 + ADR-0067 Accepted
- [ ] P3-impl 次序鐵律 5 satisfied(ADR Accept)→ 可 kickoff P3 implementation
- [ ] **不寫任何 production code**(設計 phase 純文檔驗證)
