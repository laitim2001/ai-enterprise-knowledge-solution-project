# ADR-0066: Enterprise Retrieval-Layer Document ACL(檢索層文件級存取控制架構)

**Date**: 2026-06-24
**Status**: Proposed
**Approver**: Chris(pending — DG5,H1 + H4 硬閘)

> Enterprise RBAC track P1 產出。整體目標授權架構拍板。**Proposed** 待 Chris Accept;**P2+ 任何 implementation 喺本 ADR Accepted 之前不可開工**(ROADMAP §3 次序鐵律 5)。
> 技術基礎:[`../01-planning/W89-rbac-p1-threat-model-arch/threat-model.md`](../01-planning/W89-rbac-p1-threat-model-arch/threat-model.md)(F1)+ [`target-architecture.md`](../01-planning/W89-rbac-p1-threat-model-arch/target-architecture.md)(F2)。

## Context

P0(W88)令 RBAC 地基活 —— KB 層寫端點全受 `require_kb_acl` / `require_role` 守衛。但 P1 威脅模型(F1)確認 RAG 檢索/查詢/合成路徑有 5 個授權缺口:

- **G1** `/query` + `/query/stream` 無任何守衛(連 KB 層 `require_kb_acl` 都無)
- **G2** 檢索層 filter 只 `kb_id eq '...'`,無文件級 trimming
- **G3** 索引 schema 無 ACL / classification 欄位
- **G4** synthesizer 直接餵全部 chunks 入 LLM,無授權過濾 → **confused deputy 洩漏**
- **G5** KB 層 `kb_acl` 存在但查詢路徑未採納

企業 KM RAG 嘅核心安全原則:LLM 係 confused deputy,授權必須喺**檢索之前 / 之中**執行(content 一旦入 prompt = 已洩漏,post-filter 無效)。檢索層文件級安全 = enterprise 上線必備。

**DG resolution(用戶 2026-06-24,plan §3)**:DG1 = 2 級 `internal / restricted`;DG2 = 單租戶 Ricoh internal(唔撞 H4 multi-tenancy);DG4 = **P2 檢索層安全 = Tier 1 上線先決**(非 Tier 2 後續)。

**次序鐵律 1(ROADMAP §3)**:影響索引結構嘅決定必須最先定(P1 拍板 → P2 動索引),否則重建成本翻倍 —— 故本 ADR 核心 = 索引 ACL 結構拍板。

## Decision

採目標授權模型(F2),拍板以下架構:

1. **索引 schema 擴 2 欄位**(G3):
   - `allowed_principals: Collection(Edm.String)`(filterable)— 每 chunk 存允許嘅 principal(user oid + group key)
   - `classification: Edm.String`(filterable)— `internal` / `restricted`(DG1)
2. **檢索層 security trimming**(G2/G4):query filter 注入
   `allowed_principals/any(p: search.in(p, '{user principals}', ',')) and (classification eq 'internal' or '{clearance}' eq 'restricted')`
   → Azure AI Search 喺檢索階段剔除無權 chunk,synthesizer 永遠睇唔到。
3. **query 端點補 KB 層守衛**(G1):`require_kb_acl("query")` 作基礎門檻(兩層防禦:KB 層 + 文件層)。
4. **文件 ACL 來源**:P2 用 **5.1 KB 繼承**(stamp 時由 `kb_acl` 推導 principals)→ P3 加 **5.2 文件級 `doc_acl` 表** override。
5. **ingestion stamp**:每 chunk stamp `allowed_principals` + `classification`(復用現有 `ChunkRecord` stamp 點,唔動 chunking/embedding)。
6. **單租戶**(DG2):索引**無** tenant 維度。
7. **Tier 定位**:P2 = **Tier 1 上線先決**(DG4)。
8. **P2 分段落地**:P2.0 query 守衛(G1 快補)→ P2.1 schema + stamp → P2.2 檢索 filter + 重建索引一次 → P2.3 classification clearance。

## Alternatives Considered

- **選項 B(只 `classification`,無 principal list)**:索引最簡,但無 principal 級 → 唔解 G2 分層存取(員工/經理同密級但唔同文件權限)→ **reject**。
- **選項 C(外部 ACL 服務 + post-filter)**:索引零改,但違反「檢索之前 / 之中」原則(content 已 round-trip + 易漏)+ 效能差 → **reject**。
- **全 ABAC 政策引擎(OPA / Cedar)**:過度 —— 2 級分類 + ACL list 已足夠;政策引擎留 P6 規模化(角色爆炸)才上,屬 H4 Tier 2 方向 → **defer P6**。
- **chunk 級獨立授權**:過度細粒度,索引膨脹 + 維護地獄;文件係自然授權邊界(同文件 chunks 同密級)→ **用文件繼承**。

## Consequences

- **Positive**:檢索層真 security trimming,根治 confused deputy(G2/G4);Azure AI Search S1 原生 `Collection` + `any()` filter,唔加 vendor(H2);P2.0-P2.3 分段降風險;5.1 KB 繼承令 P2 唔需新授權表。
- **Negative**:P2 需重建現有索引一次(現有 KB re-index);文件 ACL 改動需 re-stamp 該文件全部 chunks;P2.2 動檢索主路徑 → 必須驗 W43-85 圖文還原 + 問答品質不退。
- **Neutral**:P2 = Tier 1 上線先決(範圍擴大,但確認非 Tier 2 — DG4);單租戶簡化(未來多租戶需新 ADR + H4 review);G1(query 端點 KB 層守衛)可喺 P2.0 即時快補,獨立於文件級工程。

## References

- [`threat-model.md`](../01-planning/W89-rbac-p1-threat-model-arch/threat-model.md)(F1 威脅模型 G1-G5)
- [`target-architecture.md`](../01-planning/W89-rbac-p1-threat-model-arch/target-architecture.md)(F2 目標授權模型 + 選項 trade-off)
- [`FINDINGS.md` §4](../01-planning/enterprise-rbac/FINDINGS.md)(缺口分析,單一事實來源)
- [`ROADMAP.md` §2-§3](../01-planning/enterprise-rbac/ROADMAP.md)(P0-P6 路線 + 次序鐵律)
- ADR-0027(W24c RBAC,本 ADR 擴充其授權層)
- DG resolution(W89 plan §3,用戶 2026-06-24 拍板 DG1/DG2/DG4)
