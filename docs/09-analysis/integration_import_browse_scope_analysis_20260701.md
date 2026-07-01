# 整合層匯入 browse scope 設計分析 — user-scoped(Copilot 式)vs app-only(現狀)

> **日期**:2026-07-01
> **作者**:Claude(EKP AI）· **決策擁有者**:Chris
> **狀態**:分析(analysis）— **未落 code**,供決策用
> **觸發**:2026-07-01 測試期間用戶提問(問題3)—「連 SharePoint 時,匯入 wizard 嘅 browse 係咪應該只列登入用戶睇得到嘅 site,好似 Copilot Studio 咁?」
> **範圍**:只討論**匯入時 browse / 選文件**嗰步嘅權限範圍取捨;**唔**改查詢層 security trimming(嗰層已定案,見 ADR-0070 / 藍圖 §2.2)。
> **關聯**:[`unified_integration_layer_architecture_20260628.md`](./unified_integration_layer_architecture_20260628.md) · [`integration_layer_phase1_sharepoint_solution.md`](./integration_layer_phase1_sharepoint_solution.md)(下稱「藍圖」)· ADR-0070(Accepted)· ADR-0071 · enterprise RBAC track(ADR-0066/0067/0068)

---

## 1. 問題陳述

現狀:匯入 wizard 嘅 **Step 2 Select**(`browse` + `list_documents`)用 **app-only 服務帳號**(`Sites.Selected`)列 site / library / 文件。做匯入嘅 admin / editor 見到嘅係「**app 被 IT 授權嘅全部 site**」,**唔係**按佢個人 SharePoint 權限過濾。

用戶觀察(準確):Copilot Studio 連 SharePoint 係 **delegated(per-user)**模型 —— 每個用戶只見到**自己**訪問得到嘅 site,睇唔到嘅來源永遠唔會出現喺列表。

**核心問題**:EKP 匯入 browse 應唔應該改成 user-scoped(delegated),定係維持 app-only?呢份分析拆解**真正嘅取捨**、四個選項、技術交互,同一個 right-sized 建議。

---

## 2. 現狀模型(雙層)精確描述

EKP 用**兩個獨立層**處理權限(藍圖 §2.1 雙模式分工):

| 層 | 時機 | 認證 | 見到 / 保護乜 |
|---|---|---|---|
| **A. Ingestion browse + 抽 ACL** | 匯入時 | **application** `Sites.Selected`(app-only,client credentials) | admin 見到 **app 被授權嘅 site superset**;每份文件抽 SharePoint ACL → 映射成 `allowed_principals`(`get_principals`) |
| **B. Query-time trimming** | 查詢時 | **delegated / OBO**(per-user token) | 用登入用戶嘅 Entra group ∩ 文件 `allowed_principals` 做 GA 字串比對 filter → 用戶**只**收到佢有權睇嘅 chunk |

實作錨點:
- 層 A:`backend/integration/sharepoint/connector.py`(`browse` / `list_documents` 用 app-only handle)+ `permissions.py`(`resolve_principals` 展 `transitiveMembers` 到 group 級)。
- 層 B:藍圖 §2.2 / §7,收斂點 `allowed_principals`,複用 RBAC track(ADR-0066/0067)。

---

## 3. 關鍵釐清 — 呢個係**治理 / UX** 問題,唔係**資料外洩**問題

呢節係成份分析嘅 headline,因為佢決定 effort 應該有幾大。

### 3.1 end-user 資料外洩風險 = 已受控(唔係缺口)

無論邊個 admin 喺 browse 見到咩、匯入咗咩,**end-user 睇到嘅內容永遠受層 B query-time trimming 約束**,而且:

- trimming 用**文件級** `allowed_principals`(每份文件保留自己嘅 SharePoint ACL),**唔係 KB 級**。所以即使一份文件被匯入到一個受眾較闊嘅 KB,佢嘅 SharePoint 原始 ACL 仍然主導 —— 冇權嘅用戶查唔到。
- 映射**故意 fail-closed**:抽唔到 principal(空)= 拒絕當公開索引(藍圖 §6 risk / `permissions.py` docstring);Anyone-link 預設 `drop`。所以 trimming 偏保守(寧縮唔放)。

**結論**:admin 就算匯入咗一個佢個人睇唔到嘅 site 嘅文件,亦**唔會**令未授權 end-user 睇到嗰啲文件。資料外洩呢個維度,現狀已安全。

### 3.2 咁真正嘅開放問題係咩?

三個 **治理 / UX** 維度(唔涉 end-user 外洩):

1. **選取層過度曝露(over-selection)**:admin 喺 browse 見到 IT 授權俾 app 嘅全部 site,包括佢個人唔相關 / 唔應該策展嘅 site → 較易誤匯入。
2. **策展治理(curation governance)**:「邊個 admin 有權將邊個來源嘅內容放入邊個 KB」目前只靠 IT 嘅 per-site grant 做粗粒度閘,冇 per-admin 收斂。
3. **可追溯性(auditability)**:目前冇一個「邊個 admin、幾時、由邊個 site、匯入咗咩」嘅審計記錄。

### 3.3 一個重要嘅既有護欄:per-site grant 本身就係 IT 策展閘

`Sites.Selected` 係「同意 ≠ 有權」模型 —— app 對**每個** site 都要 IT / SharePoint admin **逐個** grant(藍圖 §1.3,`POST /sites/{site-id}/permissions`)。即係 **browse 能見到嘅 site 範圍,已經係 IT 明示批准嘅白名單**,唔係整個 tenant。呢點大幅收窄「over-selection」嘅實際風險面:admin 唔會見到全公司嘅 site,只會見到 IT 特登開俾 EKP 匯入嘅嗰幾個。

---

## 4. Copilot Studio 模型對比(點解佢哋 delegated)

| 維度 | Copilot Studio(delegated) | EKP(現狀 app-only + query trim) |
|---|---|---|
| browse 範圍 | per-user,只列用戶自己嘅 site | app-granted site 白名單(IT 策展) |
| 索引時機 | 傾向即時 / 依賴用戶自身訪問 | **一次匯入**,經 Docling 核心入庫 |
| end-user 保護點 | browse 層(用戶連唔到就見唔到) | **query 層**(trimming) |
| 適用形態 | 個人 / 自助 copilot | **企業 RAG 集中匯入**(admin 策展) |

**要點**:Copilot 喺 browse 層做保護,係因為佢傾向 per-user 即時模型;EKP 係「集中匯入一次、查詢時 trim」嘅企業 RAG 標準形態,保護點自然落喺 query 層。兩者都達到「用戶睇唔到冇權內容」,只係機制唔同層。所以 **EKP 唔採 delegated browse ≠ 有安全缺口**,只係少咗 Copilot 嗰種選取層對稱性。

---

## 5. 選項

### Option A — 維持 app-only(現狀)

admin 用服務帳號 browse + 匯入;end-user 靠 query-time trimming。

- **優**:最簡單;對齊企業 RAG 常態;ingest 認證模型單一(app-only client credentials,穩定、唔靠用戶 token);零新工作。
- **缺**:browse 唔按 admin 個人權限收斂(§3.2 三項治理 / UX 維度未處理)。
- **Effort**:0 · **Tier**:1 · **ADR**:不需要。

### Option B — delegated user-scoped browse(Copilot 式)

browse 改用 admin 嘅 delegated / OBO token,只列 admin 個人訪問得到嘅 site / 文件。

- **優**:選取層對稱(同 Copilot 一致);符合部分用戶直覺;自助式匯入基礎。
- **缺**:
  - **同 ingest 認證模型衝突**(見 §6):browse 用 delegated、fetch 仍用 app-only `Sites.Selected` → 兩套權限集唔一致,產生「admin 見到但 app 未 grant → 匯入失敗」/「app grant 咗但 admin 見唔到 → 隱藏」嘅混亂。
  - 若連 fetch 都改 delegated:ingestion 變成依賴用戶 live token(會過期、要用戶有下載權)→ 削弱批次可靠性,推翻藍圖 §2.1 雙模式分工。
  - 傾向自助 / per-department 匯入 → 靠近 **Tier 2 邊界**(H4)。
- **Effort**:大 · **Tier**:1.5→2 · **ADR**:需要(改認證模型 = H1)。

### Option C — 混合:app-only ingest + delegated browse 過濾(顯示層)

browse 仍枚舉 app-granted site,但**額外**用 admin 嘅 delegated 檢查交叉比對,將 admin 個人訪問唔到嘅 site **灰掉 / 隱藏**;匯入照舊 app-only。

- **優**:選取層 defense-in-depth(admin 唔會見到自己都睇唔到嘅 site),但**唔郁 ingest 認證模型**(fetch 仍 app-only,穩定)。
- **缺**:要 admin 有 delegated 讀權 + 多一輪 Graph 呼叫;仍有「app grant 但 admin 冇權」→ 該 site 對呢個 admin 隱藏(可能係想要嘅,亦可能阻到合法策展)。
- **Effort**:中 · **Tier**:1.5 · **ADR**:建議(browse 加 delegated 交互 = 認證行為變更)。

### Option D — 治理護欄(唔郁認證模型)

維持 app-only,但補:(1) **匯入審計記錄**(邊個 admin / 幾時 / 邊個 site / 邊啲文件);(2) 明文化「browse 白名單 = IT per-site grant」呢個既有閘(§3.3)做產品文件;(3) 可選 pre-check「匯入嗰位 admin 需對該 site 有 delegated 讀權」先俾佢匯入。

- **優**:直接對症 §3.2 嘅治理 / 可追溯性維度;最平;(1) 審計係任何審計 driver 出現時都需要嘅基礎。
- **缺**:唔改變 browse 見到嘅 site 範圍(over-selection 靠 §3.3 既有 IT 閘,唔係 per-admin)。
- **Effort**:細–中 · **Tier**:1 · **ADR**:(1)(2) 不需要;(3) pre-check 建議寫。

---

## 6. 技術交互:點解 delegated browse 唔係 drop-in

Option B / C 都要留意 browse 認證同 ingest 認證嘅**權限集錯配**:

```
現狀:  browse(app-only Sites.Selected)  ─┐
        fetch (app-only Sites.Selected)  ─┴─ 同一權限集,一致

Option B: browse(delegated 用戶權限)  ← 用戶睇到嘅 site
          fetch (app-only Sites.Selected) ← app 被 grant 嘅 site
          → 兩集合唔一定相等:
             · 用戶睇到但 app 未 grant → browse 見到、匯入 fetch 失敗
             · app grant 但用戶睇唔到 → browse 隱藏、但內容其實可匯入
```

- delegated `Sites.Selected` **僅 Microsoft Graph API 實作**(藍圖 §2.1 caveat / deep-research §3.4)—— 對 EKP(本身行 Graph)技術上可行,但唔改變上面嘅集合錯配問題。
- 若要完全消除錯配 → browse + fetch 都用 delegated → ingest 靠用戶 token → 過期 / 下載權 / 批次可靠性問題浮現,等於重做藍圖 §2.1。呢個係 Option B「大 effort」嘅根源。
- Option C 用「app-only 枚舉 + delegated 過濾」避開 fetch 錯配(fetch 仍 app-only),代價係接受「app grant 但 admin 個人冇權」嗰啲 site 對該 admin 隱藏。

---

## 7. 建議

**Tier 1:採 Option A + Option D 嘅審計切片(D-1),暫緩 Option B/C。**

理據:
1. **資料外洩維度已受控**(§3.1)—— user-scoped browse 主要係治理 / UX / defense-in-depth,唔係安全缺口。唔應該用「補安全洞」嘅急迫性去 justify 大 effort。
2. **over-selection 已有既有 IT 閘**(§3.3)—— browse 白名單 = IT per-site grant,唔係全 tenant;實際過度曝露面細。
3. **審計(D-1)係無悔投資** —— 任何審計 / 治理 driver 出現(同 RBAC P5 一樣,ADR-0068)都會需要「邊個匯入咗咩」記錄;成本細,建議喺階段 1 live 驗證後補。
4. **Option B/C 靠近 Tier 2 邊界 + 需 ADR + 改 / 加認證模型交互**(§6)—— 冇明確 driver 之前建 = 過度工程(對齊 `feedback_confirm_value_before_enterprise_build`:企業 / 治理擴充開工前先確認實際用處)。

**明確 revisit trigger**(命中任一就重新評估 Option C / B):
- 出現**自助 / per-department 匯入**需求(唔再係中央 admin 集中策展)。
- 審計 / 合規方明確要求「匯入 browse 必須按操作者個人權限收斂」。
- 有 non-IT-managed 嘅 site grant 流程,令 §3.3 既有閘失效。

同步:產品文件應**明示**現狀係「集中匯入 + 查詢時 trimming」,唔係 Copilot 式 per-user 自助,以免 stakeholder 誤期望(呼應用戶今次提問)。

---

## 8. 對 spec / ADR / BACKLOG 影響

- **架構 spec / ADR-0070**:現狀模型無需改;ADR-0070 §2.1 雙模式分工維持。
- **新 ADR**:只有揀 Option B / C 先需要(改認證模型 = H1)。Option A + D-1 審計唔需要新 ADR(審計係 observability,唔改架構)。
- **BACKLOG**:登記一個 `候選` 項 —— 「整合層匯入 browse user-scoped 取捨」,狀態 = 分析完成、建議 defer(Option A + D-1),link 本文件 + revisit trigger。
- **live 驗證 runbook**:可加一句 D-1 審計期望(匯入操作留痕),歸入階段 1 live 驗證後 follow-up。

---

## 附:一頁速覽

```
問題:匯入 browse 要唔要 user-scoped(Copilot 式)?
釐清:end-user 外洩 = 已受控(query-time 文件級 trimming, fail-closed)
      真問題 = 治理 / UX / 審計(§3.2),over-selection 已有 IT per-site grant 閘(§3.3)
選項:A 維持 app-only(0)| B delegated browse(大, Tier1.5-2, ADR)
      C app-only+delegated 過濾(中, Tier1.5, ADR)| D 治理護欄+審計(細-中, Tier1)
建議:A + D-1 審計切片;暫緩 B/C(冇 driver = 過度工程);設 revisit trigger
```
