# 統一整合層階段 1(SharePoint 按需匯入)— 方案藍圖 PROGRESS / Resume Tracker

**Date 起**: 2026-06-29
**對應 BACKLOG**: B-01
**對應 ADR**: ADR-0070(Accepted 2026-06-28)
**性質**: 防失憶 resume tracker。Context 斷片 / 新 session,**讀呢份 + ADR-0070 + 兩份 deep-research doc**(見 §7)就 resume 到。

> **紀律(上個 session 教訓)**:每寫完一塊 = **明寫檔案路徑 + 改咗邊節 + grep/git 驗證 + commit**。**絕不聲稱未建立嘅嘢已建立**。上個 session 喺最終 summary 聲稱建立咗藍圖 / progress / WIP memory + 改咗 architecture.md / COMPONENT_CATALOG,但實際一份都冇(grep 0 命中),只改咗 BACKLOG 一行(仲寫住假「✅ landed」)。本 tracker 嘅每個「✅」都要有 commit hash / grep 佐證。

---

## 0. TL;DR 現狀(2026-06-29)

| 交付物 | 狀態 | 佐證 |
|---|---|---|
| ADR-0070 本體 | ✅ 已 commit | `6cb00a3`(104 行 Accepted ADR) |
| deep-research:架構骨架 | ✅ 已 commit | `unified_integration_layer_architecture_20260628.md`(`51d8820`,196 行) |
| deep-research:SharePoint 權限 | ✅ 已 commit | `sharepoint_connector_permission_mapping_external_research_20260628.md`(193 行) |
| EKP spec amendment(architecture.md §3.3/§4.1 + COMPONENT_CATALOG C17 v1.1) | ✅ 已 commit | **`884b149`**(2026-06-29;grep architecture 0→7、catalog 0→8) |
| BACKLOG B-01 改誠實 | ✅ 已 commit | `884b149` |
| **進度 tracker(本檔)** | ✅ 已 commit | `0a06798` |
| **WIP memory** `project_adr0070_integration_phase1_wip.md` | ✅ 已建立 | `.claude/.../memory/`(非 git-tracked,經 OneDrive 同步) |
| **方案藍圖** `integration_layer_phase1_sharepoint_solution.md` | ✅ **§0–10 + 附錄 全部完成** | `26c5e74`→`14f3719`(grep 11 節 + 附錄)|
| **UI 設計 mockup**(SharePoint 匯入 4 surface + foundation + index)| ✅ **land 落 `references/design-mockups/integration-import/`** | `70e42df`(8 檔;雙擊 `index.html` 直接開,link canonical `../styles.css`;design-stage,H7 源頭)|
| **階段 1 backend 落地(W100 F1–F6)** | ✅ **G-W100 PASS(2026-06-30)** | plan 三件套 `796ea22`;F1 `67f4f14` / F2 `abfaf1e` / F3 `bfa1d34` / F4 `0499f2d` / F5 `08ce773` / F6 `ff87652`;`backend/integration/` + `api/routes/integration.py`;49 新測試 + RBAC 回歸綠;`backend/ingestion/` diff=零 |

**現狀(2026-06-30)**:藍圖正文 + UI mockup + **階段 1 backend(F1–F6)全部完成**。backend 詳情(deliverable / 測試 / 教訓 / Gate caveat / carry-over)= `docs/01-planning/W100-integration-sharepoint-phase1/`(plan + progress retro)。**H2 無新 dep**(`azure-identity`+`httpx` 已在,對齊 `api/auth/entra_graph.py`)+ B1(`allowed_principals`)W90 已 ship → **冇開新 ADR**(全喺 ADR-0070 範圍)。

**下一塊(carry-over)**:① **階段 1b 前端匯入 wizard**(H7 100% 重現 `integration-import/` 4 surface;等真 tenant 將近 / 用戶 kickoff)② **live 驗證**(本藍圖 §10 階段 C/D runbook,公司真 tenant + `Sites.Selected`,D4 本機造唔到)③ follow-up:org-link / Anyone-public / external_group principal 端到端(需 query 側 inject org/public token;default drop 唔行此路)。藍圖係**你帶去公司真實環境執行**嗰份(reframe,見 §1 D4)。

**UI 設計來歷注意**:用 claude design(`DesignSync`)植入 EKP design system 後設計;但該 design-system project 喺用戶互動 claude.ai 登入**唔可見**(`/design-login` 獨立授權 context,API `list_projects`/`list_files` 證實有檔但瀏覽器睇唔到)→ 改為 land 落本地 canonical。教訓:claude design design-system project ≠ 用戶 prototype project(`EKP Platform.html` 嗰個 `/p/` regular project,API 404 掂唔到);要畀用戶睇得到嘅交付,land 落本地 `references/design-mockups/` 最穩。

---

## 1. 已 confirm 嘅決定(鎖死,唔再 re-litigate)

| ID | 問題 | 決議 | 來源 |
|---|---|---|---|
| **DG-INT-1** | 第一個 concrete connector? | **SharePoint 先行**(公司主力) | ADR-0070 |
| **DG-INT-2** | 階段 1 範圍? | **鎖死 = SharePoint 按需手動匯入**;排除 auto-sync + 多 provider(守 H4) | ADR-0070 |
| **DG-INT-3** | interface 定案? | 採**修正後 interface**(5 點 ①–⑤,見 §4 D-IF);⑥⑦ 入階段 1 plan | ADR-0070 |
| **D4(reframe)** | 階段 1 點交付? | **方案交付給用戶喺公司真實環境執行**,唔喺 local repo 假裝 implement | 2026-06-29 reframe(BACKLOG B-01) |

---

## 2. 方案藍圖計劃大綱(`integration_layer_phase1_sharepoint_solution.md`,§0–§10)

> Ground 在架構 doc §4「7 正交關注點」+ §8 分階段 + SharePoint 權限 doc §5 修正版本。逐節寫,每節寫完即 commit。

| § | 標題 | 內容要點 | 狀態 |
|---|---|---|---|
| §0 | 總覽 | 目標 / 階段 1 鎖死範圍 / 交付-執行分工 / 設計鐵律一句 | ✅ |
| §1 | 前置條件(IT / tenant) | SharePoint tenant、Entra app registration、`Sites.Selected` per-site grant 三步、credential 儲存 | ✅ |
| §2 | 認證架構 | ingestion 用 application `Sites.Selected`(least-privilege)+ query-time delegated/OBO + token refresh(⑥) | ✅ |
| §3 | `SourceConnector` interface + capability model | 5 點修正 interface(§4 D-IF)+ `ConnectorCapabilities` 退化規則 | ✅ |
| §4 | SharePoint connector 實作 | browse site/library → list driveItems(分頁)→ fetch document(stream/temp)→ Graph endpoints | ✅ |
| §5 | 權限映射(ACL → `allowed_principals`) | `/permissions` 抽 → 正規化 Entra GUID → `transitiveMembers` 展 nested group 到 **group 級** → 填欄;Anyone-link 特殊處理;< 2,049/file cap | ✅ |
| §6 | 撤權 / stale permission | delta 對 library 層唔可靠 → 排程 full re-ingest + 有界延遲明示;唔承諾即時撤權 | ✅ |
| §7 | 與 EKP 核心銜接 | push chunks + `allowed_principals` 入 Azure AI Search;query-time GA 字串比對 security filter;ingestion 核心零改動鐵律 | ✅ |
| §8 | 錯誤模型 + 生命週期 | per-doc 失敗唔 abort batch(⑦)+ re-sync / 健康監控 | ✅ |
| §9 | 階段 1 範圍邊界 + 未答缺口 | 唔做 auto-sync / 多 provider(Tier 1.5);§6 4 缺口承接 | ✅ |
| §10 | 公司執行 checklist(runbook) | 你帶去公司逐步做嘅清單 | ✅ |
| 附錄 | Graph endpoints / scopes / 來源連結 | — | ✅ |

---

## 3. 關鍵技術決定(ground 在 ADR-0070 + 兩份 deep-research,寫藍圖直接引用)

1. **主路線 = push-model**(自跑 Docling ingestion + 自己注入權限 metadata),獲微軟官方明文背書,同 locked stack 全相容。**唔用** turnkey SharePoint indexer(會繞過 Docling / 圖文還原 / profile / 可調配置核心)。
2. **權限用 GA 字串比對 security filter**(= 現有 `allowed_principals` 做法),**唔押注** preview 嘅 Entra-native 自動 token-trim(全 `2026-05-01-preview`,無 SLA)。
3. **認證分工**:ingestion 服務帳號 = application `Sites.Selected`(逐 site least-privilege,security review 可辯護);query-time = delegated / on-behalf-of(per-user token)。
4. **nested group 展平到 group 級(非 user 級)**:用 Graph **`transitiveMembers`**(**非**被 0-3 反證嘅 `transitiveMemberOf`)展 nested group → flat group id + 直接 user id 即止,**唔展到每個 member user**(展到 user 級 = index 爆炸 + 改 membership 要 re-stamp 全部文件)。同 ADR-0067 group key 洞察一致:加 user 入 group **零 re-ingest**。展開設上限(< 2,049/file 防 group 爆量)。
5. **特殊 principal**:「Anyone」分享連結**無可解析 Entra object ID** → 明確規則(drop / 當 public / 拒絕索引)。「Specific people」帶可解析 `grantedToIdentitiesV2` user.id(可映射)。
6. **撤權 = 結構性 stale**:官方只給定性「timing lag」唔畀秒數;delta query 對 library/folder 層權限變更**唔可靠**(連 3 個 Prefer header 都唔得,會 `resyncRequired`)→ 用**排程 full re-ingest** 補,撤權延遲產品上明示為**有界延遲**,**唔承諾即時撤權**。
7. **chunk-level ACL 傳播**:文件切多 chunk,每 chunk 是否重複完整 `allowed_principals`(index 膨脹 + query 效能)— **無 production case,階段 1 plan 要解**(§6 缺口②)。

---

## 4. interface 修正 5 點(D-IF,per DG-INT-3,寫 §3 直接用)

- **① `get_principals` 展平到 group 級非 user 級**(零 re-ingest;同 ADR-0067 一致)
- **② `browse` / `list_documents` 分頁** → `AsyncIterator`(大 library 上萬文件唔可以一次 `list[...]`)
- **③ `SourceDocumentRef` 帶 change-detection 欄位**(`etag` / `version` / `last_modified` / `size`;Graph driveItem 原生 `eTag`/`cTag`)
- **④ `fetch_document` 用 stream / temp file path**,唔好全 bytes-in-memory(大掃描件頂唔順)
- **⑤ `delta` 保留但階段 1 唔實作**(`supports_delta=false` capability-gate)
- **⑥**(入 plan,唔改 interface)`ConnectionHandle` token refresh;credential 階段 1 配置 → Beta+ Azure Key Vault(H5)
- **⑦**(入 plan)per-doc 錯誤模型:單一文件失敗**唔 abort batch**(同 ADR-0043 reindex per-doc summary pattern 一致)

---

## 5. Kill list(5 個被反證 claim — 寫藍圖時唔好當定論)

1. ❌(0-3)「push 嘅 permission filter 欄被當 Entra 認證自動 token-trim」— GA 就係**純字串比對**。
2. ❌(0-3)「`transitiveMemberOf` v1.0 GA 跨所有 group type 展開」— 用 **`transitiveMembers`** 為準。
3. ❌(1-2)「Glean webhook 即時撤權」— vendor 自報,gated on `Sites.FullControl.All`,唔採信。
4. ❌(1-2)「Glean `Member.Read.Hidden` 補 hidden group」— vendor 自報未佐證。
5. ❌(0-3)「微軟員工確認 Graph 唔支援 track library permissions」— 過度簡化原 thread(但「library 層 delta 唔可靠」由另一 3-0 claim 確認)。

---

## 6. 未答缺口(寫藍圖 / 階段 1 plan 要補)

1. **GA 時間線** — Entra-native token-trim 幾時 GA(決定押注 GA 字串比對 vs 等 preview GA)。
2. **chunk-level ACL 傳播** 最佳實踐(每 chunk 重複 `allowed_principals`?膨脹 + 效能)。
3. **library/folder 層撤權補機制** — 排程 full re-ingest 頻率 vs 成本 + 實測延遲。
4. **分階段策略業界實證** — 「先手動匯入後自動同步」common pattern?incremental migration 經驗。

---

## 7. Resume 指引(新 session / context 斷片)

1. 讀**本檔**(現狀 + 大綱 + 已 confirm 決定)。
2. 讀 `docs/adr/0070-source-abstraction-framework.md`(Decision + scope decisions)。
3. 需要技術細節先讀兩份 deep-research:
   - `docs/09-analysis/unified_integration_layer_architecture_20260628.md`(7 正交關注點 + interface 草案 + 分階段)
   - `docs/09-analysis/sharepoint_connector_permission_mapping_external_research_20260628.md`(push-model 裁決 + 權限映射 + auth + stale)
4. 跟 §0「下一塊」+ §2 大綱「❌」最上一節繼續寫。**每塊寫完明寫路徑 + 節 + grep/git 驗 + commit。**

---

## 8. 變更記錄

| 日期 | commit | 內容 |
|---|---|---|
| 2026-06-29 | `884b149` | EKP spec amendment 真正落地(architecture.md §3.3/§4.1 + COMPONENT_CATALOG C17 v1.1)+ BACKLOG B-01 改誠實 |
| 2026-06-29 | `0a06798` | 建立本 progress tracker(防失憶)+ WIP memory |
| 2026-06-29 | `26c5e74` | 方案藍圖 `integration_layer_phase1_sharepoint_solution.md` §0–2(總覽 / 前置 / 認證)寫入 |
| 2026-06-29 | `45142f3` | 藍圖 §3(interface + capability model + 5 點修正 + 退化規則)+ §4(SharePoint connector 實作:browse / list 分頁 / fetch stream / get_principals / delta-gate / per-site grant)|
| 2026-06-29 | `d50f738` | 藍圖 §5(權限映射:transitiveMembers 展 group 級 / 特殊 principal / 防爆量 / chunk-ACL 缺口)+ §6(撤權:membership 變即時 vs 文件 ACL 變需 re-ingest / delta 反證 / 有界延遲)|
| 2026-06-29 | `b100945` | 藍圖 §7(與 EKP 核心銜接:component 全圖 / 零改動鐵律 / allowed_principals 注入 / query-time filter / 混合來源)+ §8(錯誤模型 fatal vs per-doc / 生命週期 / 健康監控 / idempotency)|
| 2026-06-29 | `14f3719` | 藍圖 §9(範圍邊界 + 4 缺口 + plan 要落實決定)+ §10(公司執行 checklist 階段 A–E)+ 附錄(Graph endpoints / scopes / 來源 / 配套)+ 頂部進度標完成 → **藍圖正文 §0–10 + 附錄齊** |
| 2026-06-30 | `70e42df` | **UI 設計 mockup land** 落 `references/design-mockups/integration-import/`(4 surface + tokens + primitives + index + README,8 檔);用 claude design 植入 EKP design system 後設計,因 design-system project 用戶睇唔到改 land 本地 canonical(H7 源頭,雙擊 index.html 直接開)|
| 2026-06-30 | (本 commit) | 同步 B-01 進度:本 tracker §0 加 UI mockup 行 + UI 設計來歷注意 + changelog;BACKLOG B-01 更新(per R7)|
