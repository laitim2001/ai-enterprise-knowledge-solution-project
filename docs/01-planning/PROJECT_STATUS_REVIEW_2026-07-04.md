# EKP 項目進度全面盤點 —— 2026-07-04 時點快照

> **本文用途**:應用戶要求,對 Enterprise Knowledge Platform(EKP)Tier 1 走到今日的**完整狀態盤點**。回答四個問題:
> **① 哪些已規劃 + 實作 · ② 哪些 pending · ③ 哪些 carry-over(反覆延後) · ④ 哪些屬未來 Tier(規劃都未開始)**。
>
> **定位 = 時點快照(snapshot),非 living 文件**。living 的 pending 狀態一律以 [`BACKLOG.md`](./BACKLOG.md) 為單一入口;本文只做「2026-07-04 這一刻的橫切面 + 判斷」,供用戶**了解走到多遠、決定下一步方向**。細節一律 link 去 source-of-truth(ADR / DEFERRED_REGISTER / TRACKER / phase folder),不重複維護。
>
> **權威來源**:`docs/adr/README.md`(72 ADR)· `BACKLOG.md`(中央 dashboard)· `DEFERRED_REGISTER.md`(DD-1~16)· `enterprise-rbac/TRACKER.md`(P0–P6)· `COMPONENT_CATALOG.md`(component spine)· 104 個 `W{NN}-*/` phase folder。
>
> **配套圖表**:[`docs/09-analysis/ekp_architecture_diagrams_20260704.html`](../09-analysis/ekp_architecture_diagrams_20260704.html) — 同日快照七圖(① 整體五層架構 · ② RAG 查詢十步流程 · ③ ingestion 十步流程 · ④ 圖文還原 §15 四層機制 · ⑤ RBAC 權限模型 · ⑥ SharePoint 整合層 · ⑦ 三層可調配置 resolve),瀏覽器直接開。

---

## 1. 執行摘要 —— 一頁看走到多遠

### 1.1 一句話結論

**Tier 1 的「功能開發」已實質完成,且大幅超出原 12 週 spec 範圍。項目目前的狀態是「功能完備、等待三件外部驅動的關卡」:① Production 上線(卡企業 IT credential)· ② 統一整合層 live 驗證(卡真 tenant + `Sites.Selected` 授權)· ③ 安全 + 治理團隊審查(2026-07-01 剛啟動的新 track)。核心 RAG 品質、前端、權限、整合層架構本身都已落地並經大量實證調優。**

### 1.2 規模概覽(截至 2026-07-04)

| 維度 | 數量 | 備註 |
|---|---|---|
| Phase(sprint week) | **104** | W01–W102(含 W24b/W24c 等子階段);原 spec 只規劃 12 週 |
| ADR(架構決定) | **72 編號** | 有效 landed 約 66(扣 0013 reserved / 0030+0032 skipped / 0062 reverted;0069 Accepted 但 code revert) |
| Change(CH) | **19** | CH-001~019(CH-014/015 為 align-then-revert 一對) |
| Bug(BUG) | **38** | BUG-001~039(缺 BUG-018) |
| Component | **13+** | C01–C12 core spine + 新增 C16 Users Service / C17 Integration |
| Hard Gate | Gate 1 ✅ / Gate 2 PARTIAL ✅ / Gate 3 ✅ / UI FINAL ✅ | **Production launch gate ⏳ 待 IT cred** |

### 1.3 原 spec 12 週 vs 實際 trajectory

原架構 spec 規劃 Tier 1 = 12 週(POC 6w → Beta 4w → Rollout 2w)。實際走了 **W1–W102(約 3–4 倍時間)**,原因是在 base pipeline 完成後,做了五條主線的深度擴充,每一條都遠超原 scope:

1. **W12–W18 UI sprint cycle** —— 6 view → 9 view + 統一 AppShell + 完整前端重建(ADR-0014/0015/0024)
2. **W19–W58 前端進階 surface + per-KB/per-doc 可調配置 vision**(ADR-0025~0051,per-KB config platform)
3. **W59–W85 圖文還原度北極星主線**(image-recall 0.574→~1.0 + inline markers + 文件畫像 profiling,ADR-0054/0055/0056)
4. **W88–W95 企業級 RBAC track**(檢索層文件級 security trimming,ADR-0066/0067/0068)
5. **W100–W102 統一整合層階段 1**(SharePoint 按需匯入,ADR-0070/0071/0072)

---

## 2. 里程碑時間線(W1–W102)

| 區段 | Weeks | 主題 | 狀態 |
|---|---|---|---|
| **地基** | W1–W6 | FastAPI + Next.js skeleton · 多格式 ingestion · hybrid retrieval · Cohere rerank · CRAG L2 · RAGAs eval | ✅ 全 closed;**Gate 1 R@5=0.9722 · Gate 2 PARTIAL PASS** |
| **Beta 準備 + auth** | W7–W11 | Entra ID auth(mock bridge)· rate limiting · mobile responsive · cost dashboard · staged rollout 準備 · **UI sprint pivot 觸發** | ✅ closed |
| **UI sprint cycle** | W12–W18 | 前端 9-view foundation · user-facing views · admin views · polish · **統一 AppShell IA**(ADR-0024) | ✅ 全 closed(UI FINAL gate PASS,smoke-user-deferred caveat) |
| **前端進階 + per-KB config** | W19–W58 | KB Detail 8-tab / Settings 6-tab / `/users` RBAC / Chat 進階 surface · **per-KB → per-doc 可調配置平台**(ADR-0040~0051) | ✅ closed |
| **retrieval 調優長弧** | W25–W56 | parent-doc retrieval · query expansion · section-path filter · chunk strategy · 完整度 proxy · synthetic QA harness | ✅ closed |
| **圖文還原度北極星** | W59–W85 | image-recall 弧(0.574→~1.0)· inline image markers · **文件畫像 profiling**(6 類 taxonomy + 三層 UI)· PDF picture ingestion · P4 scan guard | ✅ closed |
| **企業 RBAC** | W88–W95 | P0 地基 → P1 威脅模型 → P2 檢索層文件 ACL → P3 文件級 override → P4 群組繼承 → P5 治理設計 | ✅ P0–P4 完成 + P5 設計完成(impl 暫緩) |
| **完整度 eval gate** | W96–W97 | 造完整度尺(乙類)+ prompt 緩解 | ✅ closed(**gate 造成但 per-answer 不可靠;prompt 路實證 exhausted**) |
| **圖錨 amendment** | W98–W99 | leaf 級 `section_anchor_nearest` 圖步驟錨點 + 融入自動配對 preset + UI | ✅ closed |
| **統一整合層階段 1** | W100–W102 | SharePoint 按需匯入 backend + 前端 5 surface + 連接改 UI 配置(Key Vault) | ✅ 全 closed(**live 驗證 blocked 真 tenant**) |

> 詳細逐 phase timeline 見 `docs/12-ai-assistant/01-prompts/01-session-start.md §10`。W16 為唯一 partial(Beta deploy,卡 Track A IT cred)。

---

## 3. 系統組成與實作狀態(Component 維度)

> 來源 `COMPONENT_CATALOG.md`(v1.1,2026-06-29)。原 status 欄為 2026-05-01 快照,下表為 2026-07-04 實際落地狀態。

| ID | Component | 2026-07-04 實際狀態 | 說明 |
|---|---|---|---|
| **C01** | Ingestion Pipeline | ✅ 完整 | Docling + python-pptx + PDF picture(ADR-0057)+ 文件畫像 profiling(ADR-0056)+ P4 scan guard(ADR-0065) |
| **C02** | Knowledge Base Manager | ✅ 完整 | Postgres-backed(ADR-0023),in-memory fallback |
| **C03** | Indexing Service | ✅ 完整 | Azure AI Search + HNSW + **`allowed_principals`/`classification` security 欄位**(ADR-0066) |
| **C04** | Retrieval Engine | ✅ 完整 | Hybrid + Cohere v4.0-pro + contextual retrieval(ADR-0045)+ **檢索層 security trimming**(P2) |
| **C05** | Generation Pipeline | ✅ 完整 | GPT-5.5 synthesizer + CRAG L2 + citation expansion + inline image markers |
| **C06** | Eval Framework | ✅ 完整 | RAGAs 4-metric + image-recall metric + 完整度 gate(per-answer 不可靠,只可 aggregate) |
| **C07** | Observability | ✅ 完整 | Langfuse self-host + structlog |
| **C08** | API Gateway | ✅ 完整 | FastAPI,多 router(KB / query / config / RBAC / integration…) |
| **C09** | Admin Console UI | ✅ 完整 | Next.js 9-view + 統一 AppShell + per-doc config surface + H7 fidelity |
| **C10** | Chat Interface UI | ✅ 完整 | streaming + citation + inline image + conversation history(server-side) |
| **C11** | Identity & Access | 🟡 部分 | hybrid auth(SSO mock bridge + self-register)+ **enterprise RBAC P0–P4**;真 SSO/SCIM = Tier 2 |
| **C12** | DevOps & Infra | 🟡 部分 | local stack ✅;**production deploy blocked Track A IT cred** |
| **C16** | Users Service(NEW) | ✅ 落地 | ADR-0027 Tier 1.5 RBAC(Members / Roles / Groups / Audit log) |
| **C17** | Integration(NEW) | 🟡 backend+前端完成 | ADR-0070 SourceConnector framework + SharePoint connector;**live 驗證 blocked 真 tenant** |

---

## 4. 已交付功能總覽(① 已規劃 + 實作)

### 4.1 核心 RAG pipeline(Gate 驗證)

- **多格式 ingestion**(Word / PDF / PPT,layout-aware chunking)· **hybrid retrieval**(BM25 + vector + RRF + Cohere rerank)· **CRAG L2** · **citation** · **streaming chat** —— 全部 landed 並經 Gate 1/2/3 驗證。
- **retrieval 調優長弧**(W25–W56):parent-document retrieval(ADR-0037)· query expansion + RAG-Fusion(ADR-0034)· section-path prefix filter(W37)· contextual retrieval(ADR-0045)· heading-aware chunk strategy(ADR-0044)。

### 4.2 圖文還原度北極星(§15 專章見第 5 節)

image-recall 0.574→~1.0(ADR-0054)· inline image markers 交織顯示(ADR-0055)· 文件畫像自適應 recall(ADR-0056)· 末尾無錨圖章節分組(ADR-0064)。

### 4.3 per-KB / per-doc 可調配置平台(EKP 產品方向核心)

- **三層可調配置**:全域 Settings → per-KB `KbConfig`(ADR-0040)→ per-doc `DocConfig`(ADR-0050)→ per-query override。
- **文件畫像驅動**:6 類 taxonomy 自動分類 → profile→preset 路由 → 三層 UI(L1 自動 / L2 一鍵 override / L3 逐旋鈕 + 試跑)(ADR-0056/0058/0059/0060/0063)。
- **原始檔儲存 + KB-level reindex**(ADR-0043)· per-KB image cap(ADR-0042)。

### 4.4 前端 9-view + 進階 surface(H7 fidelity)

統一 AppShell(ADR-0024)· KB Detail 8-tab(ADR-0025)· Settings 6-tab(ADR-0026)· `/users` RBAC(ADR-0027)· `/kb/new` 5-step wizard(ADR-0028)· doc-detail 3-pane(ADR-0029)· Chat 進階(對話歷史 + 3 citation 模式 + InlineImageCard,ADR-0031)。

### 4.5 企業級權限 RBAC(P0–P4 完成)

- 檢索層**文件級 security trimming**(`allowed_principals` filter,ADR-0066/P2)· 文件級 `doc_acl` override(ADR-0067/P3)· 群組繼承(P4,group member 改動零 re-stamp)。
- **北極星 §15 by-construction no-op**:安全層改動不影響問答品質(P2.2 eval 驗證)。

### 4.6 統一整合層階段 1(Tier 1.5)

- `SourceConnector` provider-agnostic framework(ADR-0070)+ SharePoint connector + `Sites.Selected` 認證 + `allowed_principals` 權限收斂 + nested group 展平。**設計鐵律:connector 唔掂 ingestion 核心**(ingestion diff = 零)。
- 前端獨立頂層 Integrations 模組(ADR-0071):landing + 4 步 wizard 共 5 surface,H7 重現。
- SharePoint 連接改 UI 配置 + Key Vault(ADR-0072,方向甲 G-W102 PASS)。

### 4.7 生產化基建 + 用戶手冊

- production default flip 已做(ADR-0052,2026-06-11)· synth timeout 30→120s(ADR-0053)。
- **8 份用戶操作手冊** `docs/08-user-guide/`(出廠值已核對 code)。
- 本機 dev 工具鏈(slash commands + hook + skill,gitignore 只經 OneDrive 同步)。

---

## 5. 圖文還原度北極星主線(§15)—— 專章

> 這是用戶 2026-06-20 確立的 RAG 最根本目的準則,也是投入最多的一條主線,值得單獨盤點其收束狀態。

| 面向 | 現狀 | 收束狀態 |
|---|---|---|
| **文字 recall** | ≈0.97 | ✅ 穩定 |
| **圖片召回** | ≈1.0(全圖召回) | ✅ ADR-0054 dedup-before-cap 達成(0.574→~1.0 全弧) |
| **圖-文關係還原** | inline marker(W70/71)+ section-anchor(W75)+ leaf-nearest(W98) | ✅ 主線收束;末尾堆 28-85%→0% |
| **層 A per-doc profile** | 6 類 taxonomy + 路由 + 三層 UI + write surface | ✅ 落地(W72–W84) |
| **層 B 查詢意圖 gate** | doc-dependent,無 production 痛點 | 🅳 defer(DD-10,leaf 錨已由 W98 解) |
| **層 C 圖片按相關性揀** | 實證無圖可砍(召回圖全相關) | 🅳 defer(DD-12) |
| **缺口① ingest chunking 差異化** | 現有通用 layout_aware 已足夠 | 🅳 defer(DD-13,兩路實證否決) |
| **缺口② preset 中值預校準** | cap 維度 close;品質維度 blocked 真實 KB | 🅳 defer(DD-14) |
| **完整度尺(乙類)** | generation-ceiling ~0.77,prompt 路 exhausted | 🅳 defer(DD-15/16) |

**判斷**:北極星主線的**可做部分已全部落地**;剩餘全部收斂到「blocked on production reality / 卡用戶標註 / 卡 `gpt-5.5` H2」,不重開除非新 driver。

---

## 6. 進行中 + 可立即開工(② pending — 可動)

| ID | 任務 | 狀態 | 說明 |
|---|---|---|---|
| **BUG-039** | login-gate 初始 idle 閃 sign-in CTA | 已 fix(commit `a781b72`)| 範圍 B fix landed,vitest 8/8 綠 |
| **B-01** | 統一整合層階段 1 SharePoint 按需匯入 | `進行中` | backend ✅ + 前端 5 surface ✅ + **live runbook 已備**(`docs/09-analysis/integration_layer_phase1_live_verification_runbook.md`);**live smoke blocked 真 tenant** |
| **安全 + 治理審查 track** | 為交 security / risk & governance 團隊審查準備 | 🟡 剛啟動(2026-07-01)| 兩輪 deep-research 完成 + framework 草案 `docs/09-analysis/security_governance_review_framework_20260701.md`;下一步待決:正式開 phase track + RISK_REGISTER security cluster |

> `A` 區(BACKLOG)目前只有 B-01 在 active。其餘可開工項多已完成或轉 blocked。

---

## 7. Carry-over / 已實證 defer(③ 反覆延後)

### 7.1 已實證 defer(不重開,除非新 driver)—— DEFERRED_REGISTER 結構性債

| DD | 類別 | 狀態 | close 條件 |
|---|---|---|---|
| DD-9 | Scan PDF OCR 慢(robustness + ingest hang 已 close,剩 OCR 慢本身) | `defer` | 需 Tier 2 async ingest + 真實 scan KB 需求 |
| DD-10 | 層 B 查詢意圖 gate | `defer` | leaf 錨已 W98 解,核心 doc-dependent 無痛點 |
| DD-12 | 層 C 圖片按相關性揀 | `defer` | 實證無圖可砍 |
| DD-13 | 缺口① profile 差異化 ingest chunking | `defer` | 兩路實證否決 |
| DD-14 | 缺口② preset 出廠中值預校準 | `defer` | cap 維度 close;品質維度 blocked 真實 KB + GT |
| DD-15 | 完整度 gate hardening(解析度 ±0.15) | `defer` | 細 delta 需 fixed-answer,blocked `gpt-5.5`(H2) |
| DD-16 | 乙類緩解 prompt 路 | ✅ CLOSED | 兩輪 A/B 反證 → code REVERT(ADR-0069 §Outcome 記錄) |

### 7.2 持續性技術債(view / 模組再動時順帶補)

| DD | 類別 | 解封條件 |
|---|---|---|
| DD-1 | Smoke-user-deferred — 9-view browser walkthrough + Playwright E2E run + dark mode 視覺 | `npx playwright install chromium`(R8 corp-proxy 阻)或用戶 pre-Beta 親手 smoke |
| DD-2 | Frontend component test scaffold(多個 Vitest deferred) | 對應 view 再動時補 |
| (W101 發現) | 14 個**既有** frontend test fail(kb config view;非 W101 引入) | 對應 view 再動時修 / 獨立 debt 清理 |

---

## 8. Blocked on 外部(② pending — 卡外部,不能自行動)

| ID | 任務 | Blocker | 影響 |
|---|---|---|---|
| **B-04** | Production launch / Beta 25% rollout 啟動 | **Track A IT credential 落地** | **Tier 1 上線最大關卡**(Production launch gate ⏳) |
| **B-01 live** | 整合層階段 1 live 端到端驗證 | 真 tenant + `Sites.Selected` 授權(IT 動作) | runbook 已備,等 IT |
| **B-05** | W87 OneDrive → 本地路徑遷移 | 企業 IT 政策確認 + 用戶 go | 純 infra,規劃 + 設計已完成未執行 |
| **B-07** | prose 型 human ground truth 標註 | 卡用戶(需人手標註) | 解 DD-14/DD-15 多個品質量度 blocker |
| **B-06** | production 索引 v1→v2 原子切換 | 等 production 需求 / 真實切換場景 | `候選` |
| **B-02** | RBAC P5 implementation(auditor + access review) | 真實審計 / 合規 driver(用戶 2026-06-25 暫緩) | 設計 + ADR-0068 已完成,F1 已還原 |
| **B-03** | `section_anchor_nearest` 全域 default flip | 單獨拍板 + eval 背書 | 現只 preset + UI,全域仍 OFF |

---

## 9. Tier 2 / 尚未開始(④ 規劃都未 start)

> 明確 out-of-scope(H4 邊界)。列出防混入,**任何要落 Tier 1 → STOP + ask + ADR**。

| 類別 | 說明 | 觸發 Tier 2 的條件 |
|---|---|---|
| **整合層多 provider + auto-sync** | 階段 2-3(OneDrive / Google Drive / S3 + 增量自動同步) | ADR-0070 已定分階段;需 H4 ADR + 用戶決定 |
| **RBAC P6(政策引擎)+ SSO / SCIM** | 屬性式權限 / 真實 SSO 接駁 / 自動供應 | 規模化 driver;用戶決定 |
| **GraphRAG / Knowledge Graph** | `architecture.md §11` trigger matrix | 多跳推理需求明確化 |
| **L4+ multi-agent orchestration** | workflow / plugin builder | — |
| **Multi-tenancy** | 跨租戶隔離 | — |
| **圖片 multimodal embedding** | 純圖片語意搜索(B 類) | 現全部只用文字信號(H4 硬邊界) |
| **Multi-language(JP / ZH)** | 多語 retrieval | — |
| **xlsx parser / structured form extraction** | 新 doc 類型 | 需 H2 vendor ADR |

---

## 10. 下一步方向候選(供用戶決策)

盤點顯示:**Tier 1 功能已完備,項目卡在三個外部驅動的關卡上**。下一步方向可歸為五條路線,前三條是「推動已完成的東西上線 / 過審」,後兩條是「開新戰線」:

| # | 路線 | 性質 | 可立即動? | 關鍵前置 |
|---|---|---|---|---|
| **1** | 推 **Production 上線**(Beta 25% rollout) | 交付 | ⛔ 卡 IT | Track A IT credential —— 需推動企業 IT |
| **2** | 完成**整合層 live 驗證**(SharePoint 端到端) | 交付 | ⛔ 卡 IT | 真 tenant + `Sites.Selected` —— runbook 已備,需推動 IT |
| **3** | 推進**安全 + 治理審查 track** | 過審 | ✅ 可動 | 已啟動(2026-07-01),framework 草案已備;下一步正式開 phase + RISK_REGISTER security cluster |
| **4** | 啟動 **Tier 2**(整合層多 provider / RBAC P6 / GraphRAG) | 開新戰線 | ⚠️ 需決定 | H4 ADR + 用戶拍板 scope |
| **5** | 繼續深挖**品質**(完整度 gate / prose GT) | 打磨 | ⛔ 多 blocked | 卡用戶標註或 `gpt-5.5`(H2);多數已實證 defer |

**AI 觀察(非決定,供參考)**:
- **路線 1、2 是價值最高但不受我方控制**的關卡 —— 建議把「推動 IT 提供 credential + tenant 授權」當成**當前第一優先的對外行動**,因為它同時解封 production 上線 + 整合層驗證兩件事。
- **路線 3(安全治理審查)是唯一可立即自行推進且與企業推廣強相關**的 track,2026-07-01 剛啟動,適合作為等待 IT 期間的主線工作。
- **路線 5(品質深挖)基本已到 Tier 1 天花板** —— 剩餘量度全 blocked on 用戶標註或 vendor 限制,ROI 低,不建議作為主線,除非出現真實 production 品質痛點。

---

## 附錄 A：ADR 狀態速查(0001–0072)

| 狀態 | ADR | 說明 |
|---|---|---|
| **Accepted 有效** | 0001–0012, 0014–0028, 0029, 0031, 0033–0061, 0063–0068, 0070–0072 | 約 66 份,構成 Tier 1 架構決定全集 |
| **Proposed(未升 Accepted)** | 0039(hybrid semantic ranker toggle) | W42 實作了 Option ①;index 仍標 Proposed |
| **Accepted 但 code REVERT** | 0069(coverage synthesis) | 兩輪 A/B 反證,knob 未採用,§Outcome 保留記錄 |
| **Reverted** | 0062(app content max-width) | 同日走錯方向 revert |
| **Skipped(未寫)** | 0030, 0032 | W19 F2 absorb-vs-promote 決定吸收入 Wave A |
| **Reserved(從未寫)** | 0013 | AF3 lifespan gate split fix,defer |

> 完整每 ADR 標題 + source 見 `docs/adr/README.md`。

## 附錄 B：Change / Bug 清單

**Change(CH,19 份)**:CH-001 upload/delete/reindex · CH-003 image association · CH-005 overview aggregate · CH-006 per-KB answer detail · CH-007 per-KB top-k/rerank · CH-008 contextual retrieval · CH-009 image relevance · CH-010 chapter overview lead · CH-011 per-image doc-order · CH-012 section-fair distribution · CH-013 auth cookie session · CH-014/015 KB selector align→revert · CH-016 sidebar KB badge · CH-017 dashboard active KB · CH-018 chat KB active-only · CH-019 chat header toggles(最新,commit `8fcd211`)。

**Bug(BUG,38 份,缺 018)**:BUG-001~039。近期主要集中在 chat / 圖片顯示 / login-gate;最新 BUG-039(login-gate idle flash,已 fix)。完整清單見 `docs/03-implementation/bugs/`。

---

**盤點人**:Claude Code · **快照日期**:2026-07-04 · **下次更新**:重大 phase closeout 或方向決策後
