# Enterprise RBAC — 策略路線圖(ROADMAP)

> **性質**:候選路線圖(candidate)。**唔係** pre-created phase plans —— 每期 kickoff 先正式建 `W{NN}-*/plan.md`(守 CLAUDE.md §10 rolling JIT R1)。
> **建立**:2026-06-23 ・ **Owner**:Chris(技術 Lead)
> **錨點**:ADR-0027(W24c RBAC,Accepted)・ 整體拍板 = **ADR-0066**(P1 產出)
> **現狀 / 缺口 / 改造性質**:見 [`FINDINGS.md`](./FINDINGS.md)(單一事實來源,本檔不複製)
>
> **⚠️ Tier 邊界**:**P0 = 純 Tier 1**(W24c 收尾);**P1 = Tier 邊界拍板點**;**P2–P6 = 擴充,部分摸 Tier 2**。寫本檔唔等於 commit Tier 2;P2+ 開工前必須 ADR-0066 Accepted + Chris approve(H1 + H4)。

---

## §1 Vision

用戶 2026-06-23 framing:呢個係**企業級 KM RAG 系統**,需要**完善、安全、設置精細**嘅權限管理。SSO 可後加,其餘缺口先備齊。
落到工程,核心係喺現有 W24c RBAC 上補齊企業級能力,當中**最關鍵 = 檢索層文件級存取控制**(詳見 [`FINDINGS.md` §4](./FINDINGS.md))。

## §2 路線:6 個必做階段 + 1 選做(SSO 另計)

| 階段 | 內容 | Tier 定位 | 需 ADR | 依賴 | 粗估 |
|---|---|---|---|---|---|
| **P0** | 基礎校正 + W24c 收尾 | ✅ 純 Tier 1 | 否 | 無 | 3–5 日 |
| **P1** | 威脅模型 + 目標架構 + ADR-0066 | ⚖️ 拍板點 | **是** | P0 | 5–8 日 |
| **P2** | 檢索層文件級存取控制 | 🟡 擴充 / 上線先決 | 是 | P1 | 大(可分 2 段) |
| **P3** | 文件 / 資料夾級細粒度授權 | 🟡 擴充 | 是 | P2 | 中–大 |
| **P4** | 群組存取(成員 + 繼承) | 🟡 擴充 | 是 | P3 | 中 |
| **P5** | 管理權分級 + 存取治理 | 🟡 擴充 | 是 | P3 | 中 |
| **P6**(選) | 屬性式權限 / 政策引擎 | 🔴 Tier 2 方向 | 是 | P5 | 大 |
| (延後) | 真實 SSO + SCIM + 群組真實同步 | — | 是 | — | 中–大 |

### 階段摘要
- **P0** — 後端跑返 HEAD + 驗證真實能力 + 帳號 role 理順;修首位管理員 bootstrap;前端硬編 badge → 讀真 role;`/users` 寫操作接通;KB endpoints 補接 `require_kb_acl`。詳見 [`../W88-rbac-p0-foundation/plan.md`](../W88-rbac-p0-foundation/plan.md)。
- **P1** — 威脅模型 + 需求 + 目標授權模型(資源層級 / RBAC+ABAC 邊界 / 索引結構)+ 產出 ADR-0066。
- **P2** — 索引結構加 ACL / 密級欄位;ingestion stamp 文件 ACL;查詢時注入 Azure AI Search `filter`;重建索引一次。
- **P3** — KB 層 ACL 擴到資料夾 / 文件級(grant + 繼承 + 覆寫)+ 管理介面。
- **P4** — 群組成員模型 + 繼承解析(真實 Entra 同步隨 SSO)。
- **P5** — 角色分立 + 存取覆核 + 生命週期(JIT / 回收 / break-glass)。
- **P6(選)** — 角色爆炸先上集中政策引擎(OPA / Cedar)。

## §3 次序鐵律

1. **影響索引結構嘅決定要最先定**(P1 拍板 → P2 動索引),否則做錯方向 + 重建成本翻倍。
2. **保命嘅先做**(P2 檢索層授權 = 最大資料外洩風險)。
3. **修現有債 vs 新建分開**(P0 收尾 ≠ 新架構)。
4. **rolling JIT**(本表係建議切法,逐個 phase kickoff 先建詳細文件)。
5. **P2+ 開工前 = ADR-0066 Accepted + Chris approve**(H1 + H4 硬閘)。

---

## §4 Changelog

| 日期 | 變動 | 原因 |
|---|---|---|
| 2026-06-23 | 初版(原 `ROADMAP-enterprise-rbac.md`) | enterprise 授權需求 framing |
| 2026-06-23 | 移入 `enterprise-rbac/` + 抽走現狀 / 缺口 / 改造性質到 `FINDINGS.md`(去重) | 方案 A 文件整合 |
