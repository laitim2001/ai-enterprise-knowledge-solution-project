# EKP — 工作 Backlog(中央 dashboard 入口)

> **用途**:本項目**所有** pending 工作 / next-candidate 的**單一一覽入口**。AI 助手或用戶想知「而家有咩工作 pending、可以揀邊個去做」→ 第一站睇呢度。
>
> **定位 = index 層,唔複製細節**:每行只記「任務 / 狀態 / 前置·阻塞 / 來源連結」,細節一律 link 去 source-of-truth(`adr/README.md` / `DEFERRED_REGISTER.md` / `enterprise-rbac/TRACKER.md` / 對應 phase folder),避免雙重維護變 stale。
>
> **同步 = binding(CLAUDE.md §10 R7)**:phase kickoff / closeout、ADR Accept、defer/blocked 決定、新 candidate 被識別 → 必須同步本表,**唔可以 silent drift**。維護規則見文末。

**最後更新**:2026-07-14(**W103 i18n phase active — F1-F3 done + B-26 新增**:ADR-0075 **Accepted**〔2026-07-14 Chris 架構 + Stakeholder scope 雙 approve〕→ 開 `W103-i18n-en-zh` phase〔B-25 → `進行中`〕。**F1** Tier 邊界 amendment(en/zh UI chrome 由 Tier 2 移出 → Tier 1;採 inline-tagged + doc-version-held,非 version bump)+ **F2** next-intl 4.13.2 裝機(R8 corp-proxy 通過)+ **F3** i18n 機制(D-2 = **甲 cookie-based** `NEXT_LOCALE`;build 17 routes SSR 驗證);**F3.4** CJK font → defer F7。新增 **B-26**(frontend `next build` 撞 Ricoh MITM Google Fonts → E 區)。下一步 **F4** en externalize 增量策略(pattern + AppShell + dashboard + 臨時通 toggle 驗 end-to-end);翻譯 = Claude draft 初稿 + 用戶校對。commits `bac279b`/`2096811`/`2cc7cdc`/`f9ee7d0`。)｜2026-07-13(**B-25 雙語 i18n → ADR-0075 draft(Proposed)** — 用戶確認真實 zh/APAC driver;Multi-language 係 Tier 2(arch §11),promote 觸 **H4+H1+H2** → 依 §5.4 STOP,draft [ADR-0075](../adr/0075-multi-language-i18n-tier2-promote.md) 做 promote 評估(scope 限 **UI chrome 雙語 en/zh**,非 RAG content 翻譯、非 JP;`next-intl` + `en`/`zh` dictionary + locale routing + 啟用 mockup disabled Language toggle;工作量 arch §11 估 1 個月;**zh 翻譯來源 + 雙語同步維護 = 最大成本**),**待 Chris(架構)+ Stakeholder(scope via decision-form)雙 approve 先實作**,零 code。**同日** **B-19 KB reindex 非原子 → defer 併 B-06** — 讀 code 定案:完整原子解(v1→v2 zero-downtime)= ADR-0043 明確 defer Track A(卡 IT cred B-04);半途失敗止血已備(`failed` 回報 + counter 平衡 + 502 actionable hint,CH-001/ADR-0043 intentional);「reindexing 狀態標記」邊際止血深入 = 觸 H1(Postgres KB column mirror ADR-0025)+ H7(mockup 無「重建中」狀態)+ 價值綁 async reindex/多 user 並發(同步單機觸發者自 block 用不上)→ 連狀態標記一起 defer 等 Track A/Tier 2。**同日** **B-18 預設雙重 rerank 冗餘 close** — ADR-0039 早已 Accepted(BACKLOG/pipeline-review 標「Proposed」stale → 已更正)+ §Amendment default flip `hybrid_use_semantic_ranker` `True→False`。原定 Gate 1 R@5 re-verify 因無 validated text GT(`eval-set-v0` 係 synthetic placeholder、chunk_id 非真實 index = B-07 卡用戶)不可行 → 改 **retrieval-overlap A/B**(`drive-images-1` 9 真實 query,`POST /kb/{id}/retrieval-test` retrieve-only):**rerank-ON 兩臂 top-10 byte-identical**(overlap 1.00 / 9-9 exact order)、rerank-OFF 對照發散(0.50)→ 決定性證 semantic ranker 被 Cohere 完全 override、移除零 regression;僅改 `settings.py` 1 行 default(H1-adjacent 但在 ADR-0039 已 Accepted 框架內,2 個 W42 單元測試測參數行為不受影響),A/B 用進程 env var 覆蓋不動 `.env`。**前期** 2026-07-09(**CH-023 前端 UI 語言統一 + 雙語 Step 2 立案** — 頁面測試發現 en/zh 混雜 → sweep 審計(62 檔)證實前端**無 i18n 機制**,症狀真因 = 後期 per-KB config / W72 profiler track 組件把 UI 顯示字串寫死中文,與 core flow 英文 UI 不一致(**非瀏覽器翻譯**)。用戶採「兩步走」:Step 1 **CH-023 止血**(7 檔約 210 條 UI string 中文→英文,統一 source language 為英文;`tsc` + `next lint` clean;grep 全 7 檔 UI string 0 中文殘留;commit `9de3892`)✅ → **B-24**;Step 2 **雙語 en/zh 切換** = Multi-language Tier 2(H4/H1/H2),需 draft ADR + Chris approve → **B-25 候選**。**前期**同日 **B-22/B-23 完成** — [BUG-045](../03-implementation/bugs/BUG-045-pytest-blob-network-hang/report.md):full `pytest -q` 在 blob 不可達時 hang 根因 = endpoint 測試經 app 觸真 `azure.storage.blob.aio` 未 mock;修法 `conftest.py` 全域 autouse fixture 攔咽喉點 `from_connection_string`(方案 A)+ CI `pytest-timeout` 安全網(方案 B);dead-blob 全套驗證 **1738 passed / 0 timeout / exit 0**。解鎖 **B-22**(併入同 PR 宣告 `aiohttp>=3.10` base-dep)。**前期同日** housekeeping — BUG-039 stale 條目修正 + 殘留 branch 清理:「進行中」區 BUG-039 標「待 commit」實際已 merged 入 main〔`33a5c58`〕→ 更正為空區 + 完成註記;連帶 prune/刪除 7 條已 merged 殘留 branch〔PR #4/#5/#6/#7/#8 + 2 條舊 merged branch〕,遠端+本地淨返 `main`。**前期** 2026-07-08(**B-20 CI-green 完成 + B-22/B-23 衍生技術債立案** — PR #4/#5/#6 全部 rebase-merge 入 main:B-20 ruff 68 項清 + 揭出並修 pytest 兩項被遮蔽失敗(sharepoint 斷言 stale + CI 無 aiohttp → `ScreenshotUploader` stub)+ 清兩個 workflow 的 `cache:pip` post-step bug(`backend-ci` commit `2c4eee4` / `backend-deploy` PR #7 `d9937ca`);main 程式碼全綠(`backend-ci` + `backend-deploy` 的 `validate` gate),剩 `deploy` job 卡 Azure login 屬**未配 Azure OIDC 憑證**的已知狀態〔用戶接受,Track A〕。衍生 **B-22**〔`aiohttp` base-dep 未宣告,runtime 真需要〕+ **B-23**〔full `pytest -q` 網絡測試 hang〕入 E 區,兩者綁定需一齊處理。**前期** 2026-07-08(**B-15/CH-020 完成** — Cohere reranker 故障熱切換 fallback 落地:ADR-0074 Accepted(選項 A 自動熱降級 `FallbackReranker`,primary Cohere → Azure semantic,`server.py`/`retrieve()` 零改動),9 新 test 綠 + ruff/mypy clean,生效需重啟 backend;連帶 ⚑ 表 B-11~B-14/B-16/B-17 stale 標籤(PR #2 已 merged 但仍標 `立案 proposed`)同步回填 `完成`。**前期** 2026-07-07(**B-20 新增** — backend `ruff` lint 債 68 項入 E 區:對齊 **PR #1** 令 CI 首次當 gate 浮現,**非 W87 遷移造成**,獨立 PR 處理。**W87 路徑遷移執行** — B-05 `遷移執行中`(commit `b6dcb0d` 已推,首個對齊 **PR #1** branch→main 已開,待 rebase merge)。**前期** 2026-07-06(**pipeline review candidate** — [`pipeline_review_20260706.md`](../09-analysis/pipeline_review_20260706.md) 識別高+中風險 **9 項 candidate 入 B-11~B-19**,立案中〔用戶同意立案處理,先備 proposed 文件等指示才 code〕。**前期** 2026-07-04(**B-10 新增** — PR 流程正式化:solo self-merge SOP 已建([`PR_WORKFLOW.md`](./PR_WORKFLOW.md)),階段 1 `完成` / 階段 2 `main` branch protection `候選`;連帶本次 git 衛生 — 3 份 docs + PR SOP + gitignore commit、4 條 merge 殘留 branch 清理、docs branch push、首個對齊 PR〔83 commit → `main`〕待用戶開。**前期** 2026-07-01:B-01 **live 驗證 runbook 可執行版已備**(`docs/09-analysis/integration_layer_phase1_live_verification_runbook.md` — 確切 `.env` key / curl 連通冒煙 / UI 走查 / 故障對照 / 撤權測試,等真 tenant 拎住做)+ 前端 **step2-4 layout browser mock demo 對齊驗證** — landing + 4 步 wizard H7 對齊 mockup,純前端 mock 假 data 走完流程,demo 完 `integration.ts` code 已還原;真 live smoke 仍待真 tenant。CLAUDE.md §9/§0 已同步 W100-W101 進度(`5cc3b54`)。2026-06-30:階段 1b **W101 closed G-W101 PASS** — F1-F7 全落,backend 3 端點 + import 個別 ref + 前端 5 surface H7;ingestion diff=零 + pytest 80 passed + tsc/eslint clean;剩 live 驗證 blocked 真 tenant;14 pre-existing frontend test 債入 E 區;初版 2026-06-28 — 全項目 pending 盤點固化做 v0)

---

## 狀態 lifecycle

`候選`(已識別未規劃)→ `已規劃`(plan 建咗)→ `進行中` → `完成` / `defer`(實證或決定暫不做)/ `blocked`(卡外部·用戶決定)

分類 A–F 按「可開工性」:**A 可立即開工** / **B 已設計·暫緩** / **C blocked on 外部** / **D 已實證 defer** / **E 持續技術債** / **F Tier 2 out-of-scope**。

---

## 進行中(Active — 當前處理中)

_(空 — 目前無 in-progress 的 code 工作在飛。)_

> 最近一項 **BUG-039**(login-gate 初始 idle 第一幀 + 登出過渡閃「Sign in to continue」CTA)已 `完成` 並 merged 入 main(commit `33a5c58`,2026-07-08;範圍 B fix:auth-provider `hydrated` flag + gate 只喺確定未登入出 CTA + signOut hold loading + 登出先 navigate;vitest 8/8 + tsc/eslint clean)。source:`docs/03-implementation/bugs/BUG-039-login-gate-idle-flash-signin-cta/`

---

## A — 可立即開工(已 Accepted、等開工)

| ID | 任務 | 狀態 | 前置 / 下一步 | 來源 |
|---|---|---|---|---|
| **B-01** | 統一整合層階段 1 — SharePoint 按需匯入(`SourceConnector` interface + `Sites.Selected` 認證 + `allowed_principals` 權限收斂 + nested group 展平 + token refresh + per-doc 錯誤模型;Tier 1.5) | `進行中`(backend ✅ / 前端 5 surface ✅ / live blocked 真 tenant) | ①–③ spec amendment + 方案藍圖 + UI mockup ✅(見來源);④ ✅ **階段 1 backend 落地(`W100` closed,G-W100 PASS)**:F1 interface+capability / F2 Graph client(azure-identity+httpx,無新 dep)/ F3 connect·browse·list·fetch / F4 get_principals(transitiveMembers group 級+Anyone-drop+防爆量)/ F5 import service(per-doc 錯誤模型)/ F6 API route+RBAC+production adapter(doc ACL→既有 pipeline,**ingestion 核心零改動**)。**49 新測試 + RBAC 回歸綠**,ruff/mypy clean。commits `67f4f14`/`abfaf1e`/`bfa1d34`/`0499f2d`/`08ce773`/`ff87652`;⑤ **階段 1b 前端 IA 決定 ✅**(2026-06-30):ADR-0071(**Proposed** — 獨立頂層 Integrations 模組;用戶 AskUserQuestion 揀 landing+wizard 形態 + 命名 Integrations)+ mockup 配套改(加 `10-integrations-landing.html` + 4 surface shell 由 Knowledge 改 Integrations 歸屬);⑥ **階段 1b plan active**(`W101-integrations-import-ui`,2026-06-30 approve):ADR-0071 **Accepted** + 7 deliverable(F1 backend browse/list/resolve 端點 + import 個別 ref path / F2-F7 前端 5 surface H7 重現 + nav + API client);#2 credential 唯讀(H5 deviation 用戶確認);⑦ **W101 closed(G-W101 PASS,2026-06-30)**:F1-F7 全落 — backend 3 端點(`resolve-site`/`browse`/`documents`)+ import 個別 ref(`9f2818e`)+ 前端 5 surface H7(`d5dcfc7`/`5611f2e`/`9972a18`/`7545bde`);ingestion diff=零 + pytest 80 passed + tsc/eslint clean;**carry-over**:**live 驗證**(**runbook 可執行版已備** `docs/09-analysis/integration_layer_phase1_live_verification_runbook.md`,等真 tenant + `Sites.Selected`,blocked 外部)+ follow-up principal(org/public/external_group)+ H7 browser smoke(前端 step2-4 layout **已 mock demo 對齊驗證** 2026-07-01,真 live smoke 仍待真 tenant)+ 14 pre-existing frontend test 債(E 區) | ADR-0070(Accepted)/ `W100-integration-sharepoint-phase1/`(plan+progress)/ `docs/09-analysis/` 藍圖+deep-research ×2 / C17 / `integration-import/` mockup |
| **B-24** | 前端 UI 顯示語言統一為英文(CH-023 止血)— 7 個後期組件(`doc-config-tab` / kb settings-tuning / `doc-profiling` / upload scan-banner / kb-new preset / settings tab / doc-detail tab)約 210 條中文 UI string → 英文 | `完成`(commit `9de3892`) | sweep 審計識別 → 用戶「兩步走」拍板 Step 1 → 落地:只改顯示文字(class/邏輯零改)+ 中文註解保留 + technical term 保留 + `tsc`/`next lint` clean + 全 7 檔 UI string 0 中文殘留 | [CH-023](../03-implementation/changes/CH-023-unify-frontend-ui-language-english/spec.md) |

---

## ⚑ Pipeline 生產健壯性技術債(2026-07-06 pipeline review 識別 · B-11~B-18 + B-21 已完成,B-19 defer 併 B-06 — 全部有結論)

> 來源:[`../09-analysis/pipeline_review_20260706.md`](../09-analysis/pipeline_review_20260706.md)(RAG 查詢 + ingestion 代碼核對)。用戶 2026-07-06 同意立案處理**高(🔴)+ 中(🟠)級**風險(先備 `status: proposed` 文件,等指示才 code);低(🟡)級不在此批。
>
> **2026-07-06 已按推薦框架立案**(①只 Tier 1 緩解 `asyncio.to_thread`,完整佇列另作 Tier 2 候選 ②重疊項指向現有機制 ③每項獨立 folder;用戶立案框架問卷 3 題未答 → 用預設推進,**可調整**)。**B-11~B-17 已備 7 份立案文件**(4 BUG + 3 CH);B-18/B-19 指向現有機制不另開 folder。**B-11~B-17 已全部完成**(B-11~B-14/B-16/B-17 隨 PR #2 merged;B-15/CH-020 於 2026-07-08 完成 + ADR-0074 Accepted);**B-18 已完成**(2026-07-13,ADR-0039 §Amendment default flip `True→False` + retrieval-overlap A/B 背書);**B-19 已 defer**(2026-07-13 讀 code 定案,併 B-06 / Track A — 完整原子解 = ADR-0043 明確 defer + 半途失敗止血已備 + 「reindexing 狀態標記」觸 H1/H7 且價值綁 async/多 user)。**至此 ⚑ pipeline 技術債全部有結論**(B-11~B-18 + B-21 完成、B-19 defer)。

| ID | 風險(review 編號) | 級 | 狀態 | 立案 / 路徑 |
|---|---|---|---|---|
| **B-11** | ingest parse/chunk 同步阻塞事件迴圈(I-R1/I-R2,`asyncio.to_thread` 緩解) | 🔴 | `完成`(PR #2 merged) | [BUG-040](../03-implementation/bugs/BUG-040-ingest-sync-blocks-event-loop/report.md)(完整佇列=Tier 2 候選,另議) |
| **B-12** | 鄰居圖/概覽圖漏 ACL trim → 圖片洩漏(Q-R1) | 🔴 | `完成`(PR #2 merged) | [BUG-041](../03-implementation/bugs/BUG-041-neighbour-image-acl-trim-gap/report.md)(安全) |
| **B-13** | embedding 一次過整 doc 無分批 → 大 doc abort(I-R3) | 🟠 | `完成`(PR #2 merged) | [BUG-042](../03-implementation/bugs/BUG-042-embedding-no-subbatch-large-doc/report.md) |
| **B-14** | <1000 chunks/doc 假設 → delete/restamp 靜默漏尾(I-R7) | 🟠 | `完成`(PR #2 merged) | [BUG-043](../03-implementation/bugs/BUG-043-chunk-pagination-1000-cap/report.md) |
| **B-15** | Cohere 故障無熱切換 → 直接 502(Q-R3) | 🟠 | `完成`(2026-07-08) | [CH-020](../03-implementation/changes/CH-020-cohere-reranker-hot-fallback/spec.md) — ADR-0074 Accepted;`FallbackReranker` 自動熱降級 Azure semantic(選項 A);9 test 綠;生效需重啟 backend |
| **B-16** | ingest ACL fail-open 無告警(I-R4) | 🟠 | `完成`(PR #2 merged) | [CH-021](../03-implementation/changes/CH-021-ingest-acl-fail-open-alert/spec.md) |
| **B-17** | 串流路徑(chat 主路徑)無 CRAG(Q-R2) | 🟠 | `完成`(PR #2 merged,ADR-0073) | [CH-022](../03-implementation/changes/CH-022-streaming-crag-parity/spec.md)(方案 B 純後端信號) |
| **B-18** | 預設雙重 rerank 冗餘(Q-R4) | 🟠 | `完成`(2026-07-13) | ADR-0039 **早已 Accepted**(非「Proposed」— 標籤 stale)+ [§Amendment](../adr/0039-hybrid-semantic-ranker-toggle.md) default flip `True→False`;retrieval-overlap A/B(drive-images-1 9 真實 query)證 rerank-ON 兩臂 top-10 **byte-identical**(overlap 1.00 / 9-9 exact order)、rerank-OFF 發散(0.50)→ no-regression 決定性;僅改 `settings.py` 1 行 default(2 單元測試測參數行為不受影響) |
| **B-19** | KB reindex 非原子(I-R8) | 🟠 | `defer`(併 B-06 / Track A) | 2026-07-13 讀 code 定案:**完整原子解**(v1→v2 zero-downtime)= ADR-0043 明確 defer Track A(需 alias infra + Standard S1 + IT cred,卡 B-04);**半途失敗止血已備**(KB-level `run_kb_reindex` 單 doc 失敗不 abort + `failed` 回報 + counter 平衡;單檔 `reindex_document` 502 `reindex.partial_failure` + actionable hint,CH-001/ADR-0043 intentional);**「reindexing 狀態標記」邊際止血深入 = 觸 H1**(加 Postgres KB metadata column,mirror `archived`/ADR-0025)**+ H7**(mockup `ekp-page-kb.jsx` 有 reindex trigger/summary 但無「重建中」進行中狀態)**+ 價值綁 async reindex + 多 user 並發**(同步單機模型下觸發者自 block 用不上,async task queue 已 ADR-0043 defer)→ 連狀態標記一起 defer,等 Track A / Tier 2 一併做 |
| **B-21** | born-digital PDF 白行 Docling OCR → parse 慢 ~3x(+~60s 零得着;**2026-07-08 頁面測試發現**,非 2026-07-06 review) | 🟠 | `完成` | [BUG-044](../03-implementation/bugs/BUG-044-pdf-parser-redundant-ocr/report.md)(`do_ocr=False` 預設 + force_scan 保留 OCR;實測 87s→27s) |

---

## B — 已設計 / Accepted,用戶主動暫緩(等 driver,非技術阻塞)

| ID | 任務 | 狀態 | 解封條件 | 來源 |
|---|---|---|---|---|
| **B-02** | RBAC P5 implementation — auditor 唯讀稽核角色 + access-review report + re-certify | `defer` | 出現真實審計 / 合規 driver(Tier 1.5);用戶另批(2026-06-25 暫緩,F1 已還原) | ADR-0068(Accepted)/ `enterprise-rbac/TRACKER.md` M5 |
| **B-03** | `section_anchor_nearest` 全域 default flip — leaf 級圖步驟錨點由 preset-only 升全域 default | `defer` | 單獨拍板(類 ADR-0052)+ eval 背書;現只 preset(`P1_sop_imgdense`=nearest+cap8)+ UI,全域仍 OFF | ADR-0056 §Amendment / W98 / W99 |
| **B-08** | 整合層匯入 browse user-scoped 取捨(Copilot 式 delegated browse vs 現狀 app-only) | `defer` | 分析完成,建議 Option A(維持 app-only)+ D-1 審計切片;revisit trigger = 出現自助 / per-department 匯入需求,或審計方要求 browse 按操作者權限收斂(Option B/C 需 ADR + 改認證模型) | [`integration_import_browse_scope_analysis_20260701.md`](../09-analysis/integration_import_browse_scope_analysis_20260701.md) |
| **B-09** | SharePoint 連接改 UI 配置(credential 搬 `.env` → admin UI + Key Vault) | `完成` | 方向甲落地 **G-W102 gate PASS**(2026-07-01):ADR-0072 Accepted + `ProviderConfig.settings` generic 欄 + 新 `set-secret` 端點(用戶輸入→Key Vault,H5 不 log/回傳)+ 整合層 credential **managed > `.env` fallback**(零回歸)+ 前端 Settings→Connections SharePoint 卡。backend 65 passed / tsc+eslint+mypy(淨新增 0)clean。**carry-over**:live smoke 需重啟 backend + blocked 真 tenant(D4,同 B-01);多 named connection + cert 上載 = follow-up。per-site grant 仍 IT 步驟 | [ADR-0072](../adr/0072-sharepoint-managed-connection.md) · [W102](./W102-sharepoint-connection-config/) |
| **B-10** | PR 流程正式化 — solo self-merge SOP(階段 1)+ 分階段 `main` branch protection(階段 2)+ CODEOWNERS / PR template(階段 3,有協作者時) | 階段 1 `完成`(SOP 已建)/ 階段 2 `候選` | 階段 2 解封 = PR 流程跑順幾個 cycle 後,GitHub 開 `main` branch protection(禁直推 + require `backend-ci` pass + require PR);階段 3 = 有協作者時加 CODEOWNERS / required reviewers / `.github/PULL_REQUEST_TEMPLATE.md` | [`PR_WORKFLOW.md`](./PR_WORKFLOW.md) §7 |

---

## C — Blocked on 外部(企業 IT / 用戶決定)

| ID | 任務 | 狀態 | Blocker | 來源 |
|---|---|---|---|---|
| **B-04** | Production launch / Beta 25% rollout 啟動(Tier 1 上線最大關卡) | `blocked` | **Track A IT credential 落地**(Production launch gate ⏳) | DD-6 / `DEFERRED_REGISTER.md` / W16 F1-F4 |
| **B-05** | W87 OneDrive → 本地路徑遷移(2026-07-07 pivot 執行路徑 B;新路徑 `C:\Users\CLai03\ai-enterprise-knowledge-solution-project`,已逃出 OneDrive) | `進行中(F5 觀察)` | **F4 全棧 gate PASS 10/10**(2026-07-07 新 session:8 KB/3 conv/6 msg + azurite 827 圖 volume 無縫 + `/query` 引用+圖端到端 + 最長路徑 219 + api/venv 指新路徑);待 **F5 觀察 ≥3 天退役 OneDrive**(未過前保留舊副本) | `W87-onedrive-path-migration/progress.md` Day 2 |
| **B-06** | production 索引 v1→v2 原子切換 | `候選` | 等 production 需求 / 真實切換場景 | CLAUDE.md §9 W100+ candidate |
| **B-07** | prose 型 human ground truth 標註(解 DD-14/DD-15 多個品質量度 blocker) | `blocked` | 卡用戶(需人手標註) | DD-14 / DD-15 |
| **B-25** | 雙語 i18n(en/zh UI 切換)— Multi-language Tier 2 promote 評估(建 dictionary + locale state + 全站 UI string externalize + 切換 UI + 新 i18n dependency 如 next-intl) | `進行中(W103)` | **[ADR-0075](../adr/0075-multi-language-i18n-tier2-promote.md) Accepted(2026-07-14)** + decision-form Q23 Resolved:用戶 as Stakeholder scope + Chris 架構**雙 approve**,APAC driver = 內部+外部 both;scope 限 **UI chrome 雙語** en/zh(非 RAG content/JP)。**[W103-i18n-en-zh](./W103-i18n-en-zh/plan.md) phase `active`(2026-07-14 plan approved)**;F1 = Tier 邊界 amendment(architecture.md §11 + CLAUDE.md §5.4 H4);翻譯 = Claude draft 初稿 + 用戶校對((a));D-2 locale 機制留 F3 前拍板。最大成本 = zh 翻譯 + 雙語同步維護 | [ADR-0075](../adr/0075-multi-language-i18n-tier2-promote.md) / architecture.md §11 / CLAUDE.md §5.4 H4 / [CH-023 §6](../03-implementation/changes/CH-023-unify-frontend-ui-language-english/spec.md) |

---

## D — 已實證 defer(不重開,除非新 driver;close 條件見 DEFERRED_REGISTER)

> 細節 + 恢復條件**全部喺** [`DEFERRED_REGISTER.md`](./DEFERRED_REGISTER.md),本表只做指標。

| DD | 類別 | 狀態 |
|---|---|---|
| DD-9 | Scan PDF OCR 慢(robustness + ingest hang 已 close,剩 OCR 慢本身 = Tier 2) | `defer` |
| DD-10 | 層 B 查詢意圖 gate(leaf 錨已由 W98 解,核心仍 doc-dependent 無痛點) | `defer` |
| DD-12 | 層 C 圖片按相關性揀(實證無圖可砍,confirm defer) | `defer` |
| DD-13 | 缺口① profile-差異化 ingest chunking(兩路實證否決) | `defer` |
| DD-14 | 缺口② preset 出廠中值預校準(cap 維度已 close,品質維度 blocked on 真實 KB) | `defer` |
| DD-15 | 完整度 gate hardening(解析度 ±0.15,細 delta 需 fixed-answer,blocked on `gpt-5.5` H2) | `defer` |
| DD-16 | 乙類緩解 prompt 路(兩輪 A/B 反證 → code REVERT) | ✅ `完成`(CLOSED) |

---

## E — 持續性技術債(對應 view / 模組再動時順帶補)

| DD | 類別 | 解封條件 |
|---|---|---|
| DD-1 | Smoke-user-deferred — 9-view 互動 browser walkthrough + Playwright E2E run + dark mode 視覺 | `npx playwright install chromium` 解封(R8 corp-proxy 阻)或用戶 pre-Beta 親手 smoke |
| DD-2 | Frontend component test scaffold(多個 Vitest deferred) | 對應 view 再動時順帶補 / F8.4 batch |
| (W101 發現 · **W103 F7.3 複核定案**) | **18 條**既有 frontend test fail,5 檔:`kb-settings-tuning`(9)/ `doc-config-tab`(4)/ `kb-settings-reindex`(3)/ `kb-detail`(1)/ `chat-meta-row`(1)。**非 W101 亦非 W103 引入**(W101 以 `git diff babccd8 HEAD` 證零 touch;W103 F7.3 另以 commit 時序證,兩條獨立證據鏈一致) | **根因 W103 已查實**(由「疑 schema stale」升級為確認):**①16 條** = 測試斷言中文文案,但 CH-023 `3221d38`(2026-07-09)已把 UI 改英文,測試冇同步(三檔最後改動 06-05 / 06-09 / 06-12);**②1 條** `kb-detail` = `IMAGE_DENSE_PRESET` 未在 `@/lib/api/kb` mock 宣告 → 組件 throw、body 空(引入 commit `7075526` 距今 177 個);**③1 條** `chat-meta-row` = W83 `25ef5ad`(ADR-0064)加咗 section badge,令 `querySelector('.badge.badge-muted')` 攞到第一個(capped 8)而非 gallery 總數(10)(距今 191 個)。修法已明確 → 可開獨立 Bug-fix instance 清理 |
| **B-20** ✅ | backend `ruff` lint 債 **68 項**(35 `E402` / 12 `UP017` / 7 `F401` / 6 `I001` / 4 `UP037` / 4 `B00x`;2026-07-07 對齊 **PR #1** 令 CI `Ruff lint` 首次真正當 gate 才浮現,**非本次 W87 遷移造成** — 遷移 commit `b6dcb0d` 純 docs)| **✅ 2026-07-08 完成**(PR #6 rebase-merge 入 main `2c4eee4`;68 項全清 CI ruff gate 綠)。連帶揭出 pytest 兩項被遮蔽失敗(sharepoint 斷言 stale + CI 無 aiohttp)已修 + 兩個 workflow 的 `cache:pip` post-step bug 已清(`backend-ci` `2c4eee4` / `backend-deploy` PR #7 `d9937ca`)→ 衍生 **B-22 / B-23** |
| **B-22** ✅ | `aiohttp` 未在 `backend/pyproject.toml` base deps 宣告 — `azure.storage.blob.aio` runtime 真需要,曾只靠 `eval` extras transitive 意外滿足 | **✅ 2026-07-09 完成**(隨 B-23 併入同一 PR):宣告 `aiohttp>=3.10` base-dep;先修 B-23 hang 令加 aiohttp 安全 → CI 綠。見 [BUG-045](../03-implementation/bugs/BUG-045-pytest-blob-network-hang/report.md) |
| **B-23** ✅ | full `pytest -q` 在 blob 不可達時 hang — endpoint 測試(upload/reindex/eval)經 app 觸真 `azure.storage.blob.aio` 未 mock,best-effort try/except 接唔住阻塞 socket | **✅ 2026-07-09 完成**:[BUG-045](../03-implementation/bugs/BUG-045-pytest-blob-network-hang/report.md) — `conftest.py` 全域 autouse fixture 攔咽喉點 `from_connection_string`(方案 A)+ CI `pytest-timeout` 安全網(方案 B);dead-blob 全套驗證 **1738 passed / 0 timeout**。解鎖 B-22 |
| **B-26** | frontend `next build` 撞 Ricoh MITM — `next/font/google` build-time 抓 Google Fonts(Inter / JetBrains Mono)`SELF_SIGNED_CERT_IN_CHAIN` fail;**font import pre-existing**(`app/layout.tsx`),W103 F3 首跑 full build 才暴露,**非 i18n 引入** | dev workaround = `NODE_TLS_REJECT_UNAUTHORIZED=0`(同 `next.config.mjs` backend proxy `rejectUnauthorized=false` dev pattern)繞過即 build 成功(W103 F3 已驗);根治候選 = self-host fonts(`next/font/local`)/ CI 加 Ricoh CA / build 環境豁免 `fonts.googleapis.com`;W103 F7 需 build 驗證時沿用 workaround |
| **B-27** | **`frontend-deploy.yml` 從來冇跑 vitest** — `lint-and-build` job 只做 lint + type-check + `next build`,單元測試零 CI 覆蓋。後果實證:W103 externalize 打爛 24 檔 / 95 test(缺 `NextIntlClientProvider`)一路無人知,要到 W103 F7.3 手動跑先發現;上列 18 條 pre-existing 失敗亦同樣積咗一個月。**W103 F7.3 2026-07-20 識別** | 候選修法 = `lint-and-build` 加一步 `pnpm test:unit`(先清完 18 條 pre-existing 否則即刻紅);屬 workflow 改動非 W103 scope。**留意 flakiness**:機器負載高時 `chat-bug034` / `chat-inline-image-interleave` 會因 async 等待逾時假紅(全套 133s 時紅、單獨跑 33s 時 6/6 綠)→ 入 CI 前宜先調 `testTimeout` |

---

## F — Tier 2 明確 out-of-scope(H4 邊界,非 pending,記錄防混入)

RBAC P6(政策引擎)/ SSO / SCIM / 整合層多 provider + auto-sync / GraphRAG / multi-agent / multi-tenancy / 圖片 multimodal embedding。

> 詳見 `CLAUDE.md §5.4 H4` + `architecture.md §11` trigger matrix。任何要把以上落 Tier 1 → STOP+ask + ADR。

---

## 維護規則(對應 CLAUDE.md §10 R7)

1. **新 candidate 被識別**(分析 / 討論 / ADR Accept / phase retro carry-over / 用戶提出)→ 加一行,狀態 `候選`,填來源連結。
2. **phase kickoff**(plan 建)→ 對應項改 `進行中`(或新增該項做 `已規劃`)。
3. **phase closeout** → 對應項改 `完成`;若產生**反覆 / 結構性** deferral → 同步 `DEFERRED_REGISTER.md` 加 DD-N,本表 D/E 區加指標行。
4. **defer / blocked 決定** → 改對應狀態 + link DD-N 或阻塞源(IT cred / 用戶 go 等)。
5. **single source 原則** — 本表唔複製細節,只 link;細節改去 source-of-truth(ADR / DEFERRED_REGISTER / TRACKER / phase folder),本表只更新「狀態 + 一句摘要」。
6. **更新即改「最後更新」日期** + 必要時喺對應 phase `progress.md` Day-N entry mention(per R2)。

> **與 `DEFERRED_REGISTER.md` 分工**:BACKLOG = **全部** pending 的 dashboard(含可開工 / 候選 / blocked);DEFERRED_REGISTER = **recurring deferred-debt** 的 close 條件細節庫。BACKLOG 的 D/E 區只指向 DEFERRED_REGISTER,唔重複內容。
