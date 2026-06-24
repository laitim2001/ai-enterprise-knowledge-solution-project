# W89 P1 F2 — 目標授權模型

> P1 deliverable F2。純設計(唔 implement)。基於 [`threat-model.md`](./threat-model.md) F1 缺口 G1-G5 + DG resolution(DG1 2 級分類 / DG2 單租戶 / DG4 P2=Tier 1 上線先決)。本檔係 ADR-0066(F3)嘅技術基礎。

---

## 1. 資源層級

```
Workspace
 └─ KB                    ← 現有 kb_acl(manage/edit/query),P0 已守寫端點
     └─ 文件(doc_id)       ← P2/P3 新:文件級 ACL
         └─ chunk          ← 繼承文件 ACL(唔獨立授權,簡化)
```

**P1 設計範圍到文件級**(chunk 繼承文件 ACL)。理由:chunk 級獨立授權 = 過度細粒度,索引膨脹 + 維護地獄;文件係自然授權邊界(同一文件嘅 chunks 同密級)。DG2 單租戶 → **無 tenant 維度**(簡化)。

---

## 2. RBAC + ABAC 邊界

| 機制 | 用喺邊 | 例 | 狀態 |
|---|---|---|---|
| **RBAC**(角色) | workspace + KB 層 | admin / editor / user;kb_acl manage/edit/query | 🟢 現有(P0) |
| **文件 ACL**(principal grant) | 文件層 | doc-X allow [userA, grpB] | 🔴 P2 新 |
| **ABAC**(屬性) | classification 過濾 | restricted 文件需 user clearance | 🔴 P2 新(DG1) |

**邊界原則**:RBAC 管「邊個角色可做邊類操作」(粗);文件 ACL + ABAC classification 管「邊個 principal 可見邊份文件」(細,檢索層 trimming)。**唔用全 ABAC 政策引擎**(P6 才需,H4 Tier 2 方向)— P1/P2 用 ACL list + 1 個 classification 屬性即夠(DG1 2 級)。

---

## 3. 索引 ACL 結構(核心 — 多選項 + trade-off)

> 次序鐵律 1:索引結構決定最先定,ADR-0066 核心。Azure AI Search S1 原生 `filter` 支援(H2 唔撞)。

### 選項 A — `allowed_principals` Collection(每 chunk 存允許 principal list)

```json
{"name": "allowed_principals", "type": "Collection(Edm.String)", "filterable": true}
{"name": "classification", "type": "Edm.String", "filterable": true}
```
檢索 filter:`kb_id eq '{kb}' and allowed_principals/any(p: search.in(p, '{user_oid},{grp1},{grp2}', ','))`

- ✅ Azure 原生 `any()` filter,security trimming 喺檢索層發生(F1 G2/G4 根治)
- ✅ 單次 query 解決,無需 post-filter
- ❌ principal list 存喺每 chunk → 文件 ACL 改動需 re-stamp 該文件全部 chunks(更新成本)
- ❌ 大群組 → principal list 長(但 OData `search.in` 可接受)

### 選項 B — `classification` only + 查詢時 clearance 比對

只存 `classification`,user clearance 喺 app 層比對。
- ✅ 索引最簡(1 欄位)
- ❌ **唔解 F1 G2**(文件級 principal 仍無 filter,只密級)→ 唔夠(分層存取需 principal 級)

### 選項 C — 外部 ACL 服務 + chunk_id 雙查

檢索返 chunk_id → 外部查 ACL → post-filter。
- ✅ 索引零改
- ❌ **違反核心原則**(post-filter = content 已入記憶體,且 LLM prompt 構造前要 round-trip)+ 效能差 + 易漏

### 推薦:選項 A(+ classification 欄位)

**A 係唯一喺檢索層真正 trimming + 單次解決 + Azure 原生嘅方案**。B 唔夠細(只密級無 principal),C 違反「檢索之前/之中」原則。A 嘅更新成本(re-stamp)用 P2 ingestion + 文件 ACL 改動 hook 解決。

---

## 4. 檢索 filter 機制

```
query 時:
1. 攞 user 嘅 principals = {user_oid} ∪ {group_keys}(P4 群組繼承前先得 user_oid)
2. 攞 user clearance(DG1:internal user 見 internal;restricted user 見全部)
3. 注入 filter:
   kb_id eq '{kb}'
   and allowed_principals/any(p: search.in(p, '{principals}', ','))
   and (classification eq 'internal' or '{clearance}' eq 'restricted')
4. Azure AI Search 喺檢索階段已剔除無權 chunk → synthesizer 永遠睇唔到
```

**配合 G1 修復**:query 端點先加 `require_kb_acl("query")`(KB 層門檻)→ 再檢索層 filter(文件級 trimming)。兩層防禦。

---

## 5. 文件 ACL 來源(KB 繼承 vs 文件級表)

| 選項 | 機制 | Tier/Phase |
|---|---|---|
| **5.1 KB 繼承** | 文件 `allowed_principals` = 該 KB 全部 query+ grant 嘅 principals(stamp 時由 kb_acl 推導) | **P2 起點**(最簡,等同現 KB 層但落到索引) |
| **5.2 文件級表** | 新 `doc_acl` 表(doc_id → principal → access),override KB 繼承 | P3 細粒度 |

**P1 設計**:P2 先做 5.1(KB 繼承落索引,令檢索層 trimming 生效,等同把現有 KB ACL「下沉」到 chunk),P3 才加 5.2 文件級 override。呢個分段令 P2 唔需要新授權表(只 stamp),降低 P2 風險。

---

## 6. ingestion stamp 機制(P2)

ingestion / reindex 時,每 chunk stamp:
- `allowed_principals` = resolve_kb_principals(kb_id)(P2 5.1)或 doc_acl override(P3 5.2)
- `classification` = 文件級 metadata(預設 internal;restricted 由 profile/manual 標)

**現有 ingestion 已有 per-chunk stamp 點**(`ChunkRecord` 構造,`indexing/schemas.py`)→ P2 只加 2 欄位,唔動 chunking/embedding 邏輯(保 W43-85 問答品質,plan §4)。

---

## 7. 對齊 H2 + 次序鐵律 1

- **H2**:Azure AI Search S1 原生 `Collection(Edm.String)` + `any()` filter,唔加 vendor,唔撞 lock。
- **次序鐵律 1**:索引加 `allowed_principals` + `classification` = 結構決定,**ADR-0066 必須拍板**;一旦定 → P2 重建索引一次(現有 KB re-index)。
- **單租戶(DG2)**:無 tenant_id 欄位,簡化。

---

## 8. P2 落地路線(分段,供 ADR-0066 + P2 plan)

| 段 | 內容 | 風險 |
|---|---|---|
| **P2.0** | query 端點補 `require_kb_acl("query")`(G1 快補,KB 層門檻) | 🟢 低(類似 P0 F5) |
| **P2.1** | 索引 schema 加 `allowed_principals` + `classification`(G3)+ ingestion stamp(KB 繼承 5.1) | 🟡 中(改 schema) |
| **P2.2** | 檢索 filter 注入(G2)+ 重建現有索引一次 | 🔴 高(動檢索主路徑,需驗 W43-85 問答品質不退) |
| **P2.3** | classification clearance + restricted 文件流程(DG1) | 🟡 中 |

→ **F3 ADR-0066** 將拍板:選項 A 索引結構 + 5.1 KB 繼承起點 + P2.0-P2.3 分段 + Tier 定位(P2=Tier 1 上線先決 per DG4)。**ADR Accept = DG5 Chris**(H1+H4)。
