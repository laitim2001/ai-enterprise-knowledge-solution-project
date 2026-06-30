# W101 — 統一整合層階段 1b:Integrations 前端匯入 wizard + browse 端點

| 項目 | 值 |
|---|---|
| Phase | W101-integrations-import-ui(ADR-0070 階段 1b 前端 + ADR-0071 頂層 Integrations IA)|
| Status | **active**(用戶 2026-06-30 approve plan + 確認 #2 credential 唯讀;F1 進行中)|
| Tier | Tier 1.5(NET NEW 前端 surface + 薄 backend browse 端點;全喺 ADR-0070 / ADR-0071 Accepted 授權範圍,非新架構決定)|
| 依賴 | **已清**:① backend connector(W100)`browse`/`list_documents`/`resolve_site`/`fetch_document`/`get_principals` 全實作 ② ADR-0071 Accepted(頂層 Integrations IA)③ mockup 已備(`integration-import/` 5 surface,本 phase Step 1 已加 landing + 改歸屬)④ H2 無新 dep(前端用既有 TanStack Query / lucide-react;backend 用既有 connector,無新 vendor)|
| 錨點 | mockup `references/design-mockups/integration-import/`(5 surface)· ADR-0071(IA)· ADR-0070(connector framework)· W100 backend(`backend/integration/`)· 方案藍圖 `docs/09-analysis/integration_layer_phase1_sharepoint_solution.md` · BACKLOG B-01 |
| 粗估 | 大(7 deliverable;F1 backend 補端點 + import 個別 ref path;F2–F7 前端 5 surface H7 重現 + nav + API client)|

> **H1 / H7 / H5 gating**:
> - **H1**:sidebar 頂層 Integrations 項已喺 ADR-0071 Accepted(用戶 2026-06-30 拍板);backend browse 端點係 expose 既有 connector(ADR-0070 範圍),import 個別 ref path 係 extend 既有端點(非新架構)→ H1 唔再 trigger,plan changelog 記 contract extend。
> - **H7**:5 surface 前端 impl **必須 100% 重現 mockup**。3 處 mockup-vs-backend 張力喺 §4 處理:#1 個別文件(backend 補 path,視覺保留)/ #3 browse(backend 補端點,視覺保留)/ **#2 credential 輸入 → 唯讀狀態(H5 hard constraint wins,屬 H7 deviation,待用戶 approve plan 時確認)**。
> - **H5**:SharePoint credential **絕不經前端明文傳**(只 .env / Key Vault server-side)→ 決定 #2 step1 credential fields 改唯讀狀態展示。
> - **D4 reframe**(沿 W100):SharePoint/Graph 端到端要真 tenant + `Sites.Selected`,**本機造唔到** → 本 phase 前端串真接口 + backend 端點 mock 測試;**端到端 live 驗證留藍圖 §10 階段 C/D runbook**,唔計入 Gate。

## §1 目標(Why)

把 ADR-0070 統一整合層由 backend-only(W100)補上**用戶可見入口**:獨立頂層 **Integrations** 模組(ADR-0071)→ landing 來源列表 → 4 步 SharePoint import wizard(connect → select → import → done),100% 重現 mockup(H7),串真 backend 接口(browse / list / import),令公司真 tenant 一接上就能用。

**北極星(§15)**:connector-sourced 文件行同一條 Docling pipeline,圖文還原度同人手上傳一致(live 驗證 D1,留 runbook)。

## §2 Deliverables(F1–F7)

| # | Deliverable | 檔案 | Acceptance |
|---|---|---|---|
| **F1** | backend browse/list/resolve 端點 + import 個別文件 ref path | `backend/api/routes/integration.py`(加 `POST /resolve-site` · `GET /browse?container_id=` · `GET /documents?container_id=` · `POST /import` 擴 `documents` ref 欄)· `backend/integration/import_service.py`(加 `import_selected_documents` 收選定 refs;保留既有 container 級 path)· Pydantic out schema(`SourceContainerOut` / `SourceDocumentRefOut`)| 4 端點 callable + RBAC `require_role(admin,editor)` + per-KB edit(import)+ not-configured 503;個別 ref path 逐個 fetch+ingest;**既有 container 級 `import_documents` 不變**(production-preserve);mock connector 測試綠;ruff + `mypy --strict` clean |
| **F2** | sidebar nav + breadcrumb + route scaffold | `frontend/components/nav/app-shell.tsx`(`WORKSPACE_NAV` `/kb` 後加 Integrations + lucide icon + `computeBreadcrumbs` integrations 分支)· `frontend/app/(app)/integrations/page.tsx` + `.../sharepoint/import/page.tsx`(骨架)| sidebar 出現 Integrations 項(Knowledge 後、仍 Workspace section,per ADR-0071)+ active 高亮 + breadcrumb 正確;`/integrations` + `/integrations/sharepoint/import` route ready;`tsc`/`eslint` clean;**唔郁其他 nav 項歸屬**(surgical) |
| **F3** | API client `lib/api/integration.ts` + types | `frontend/lib/api/integration.ts`(`resolveSite` / `browse` / `listDocuments` / `importSelected` 跟 `xxxApi` pattern)+ TS types 鏡像 backend schema | 4 method typed;經 `/api/backend/[...path]` proxy;URL 無 trailing slash;`tsc` clean |
| **F4** | Integrations landing | `frontend/app/(app)/integrations/page.tsx` | **H7 100% 重現 `10-integrations-landing.html`**:SharePoint connector card(狀態 badge +「Import documents →」)+ disabled「connect another source」affordance(Tier 2);`.content`/`.content-narrow`/`.page-header`/`.card`/`.badge`/`.btn` design-system class;`'use client'` |
| **F5** | Wizard Step 1 Connect + Step 2 Select | `frontend/app/(app)/integrations/sharepoint/import/page.tsx`(inline stepper + step state useState)| **H7 重現 `20`+`21`**:stepper(28px circle DESIGN_SYSTEM §4.2)+ connect form(**credential 唯讀狀態 per #2**)+ 「Test connection」call `resolveSite` + browse 樹(site→library→folder)call `browse` + 文件 table checkbox call `listDocuments`;個別文件揀選 state |
| **F6** | Wizard Step 3 Import + Step 4 Summary | (同上 page)| **H7 重現 `22`+`23`**:progress + per-doc 即時狀態(失敗唔 abort)call `importSelected` + summary(READY/FAILED + scan-PDF guard 例 + retry);完成 →「View knowledge base」link |
| **F7** | 收尾 — upload placeholder 改指向 + 測試 + Gate | `frontend/app/(app)/kb/[id]/upload/page.tsx`(`SourceKind='sharepoint'` placeholder 改指向 `/integrations/sharepoint/import` link,避免兩入口 drift)· component test scaffold(`'use client'` 頁 Vitest 視 sprint)| upload placeholder 收斂;Gate G-W101(見 §3)|

## §3 Phase Gate

- **G-W101**:F1–F7 全完成 + **H7 fidelity**(5 surface 逐個對齊 mockup,§12 fidelity check)+ frontend `tsc`/`eslint` clean + 既有 frontend 測試零 regression + backend 新端點 mock 測試綠 + `ruff`/`mypy --strict` clean + 既有 backend 測試(`test_integration_route` + `test_kb_route_acl`)零 regression + `backend/ingestion/` git diff = 零(§7.2 鐵律)。
- **Live 端到端驗證(D1–D4,藍圖 §10 階段 C/D)= 留 runbook 畀公司真 tenant + `Sites.Selected` 執行**,**唔計入 G-W101**(D4 reframe)。Gate 只認 H7 fidelity + mock/單元測 + 靜態檢查。

## §4 設計決定(proposed default,approve plan 時確認 / 覆寫)

| # | 決定 | proposed default | 理由 / 性質 |
|---|---|---|---|
| **D-1** | sidebar Integrations 位置 | `WORKSPACE_NAV` `/kb` 之後(Knowledge 後、Eval 前,仍 Workspace section)| 對齊 mockup README + ADR-0071;**mockup sidebar 同實際 `app-shell.tsx` 有既有 drift**(mockup 把 Eval/Traces 當 Tools,實際 Workspace)— 非本 phase 引入,impl **以實際 app-shell 為準**,只加一項(surgical) |
| **D-2** | Stepper primitive | **inline copy**(跟現有 2 wizard pattern + H7 逐頁對齊),**唔抽 `<Stepper>`** | rule-of-3 技術達標,但抽 primitive 要動兩個既有 working wizard = 獨立 refactor scope,違 Karpathy surgical;如要抽另開 task |
| **#1 D-3** | import 揀選粒度 | **個別文件 ref**(F1 補 `import_selected_documents`,前端傳選定 refs;保留 container 級 path)| mockup step2 明確個別 checkbox;backend extend 既有端點非新架構;production-preserve |
| **#2 D-4** | step1 credential 輸入 | **唯讀狀態展示**(顯示 server 已配置 / 未配置,用戶只填 site URL + 揀 KB)| **H5 hard constraint** — credential 絕不經前端明文傳(.env / Key Vault server-side)→ mockup 可輸入 credential fields 改唯讀;**屬 H7 deviation(backend/H5 wins per §13),要用戶 approve plan 時確認** |
| **D-5** | browse session | **stateless**(每個 browse/list/resolve 端點自己 `connect`+`aclose`,同 `/import` pattern)| 無 session 狀態管理,簡單;app-only token cheap;live 慢可後優化(留 runbook 觀察) |
| **D-6** | browse 大 library 分頁 | 階段 1b **server-side collect + cap**(合理上限,超額標明),前端唔做 infinite scroll | connector async generator 已分頁;HTTP 透傳 continuation 複雜度留階段 2;mock 環境量小;cap 防爆(log) |

## §5 Out of scope(留後續 / 別滑入)

- **Live tenant 端到端驗證**(藍圖 §10 階段 C/D)= runbook 畀公司執行(D4)。
- **follow-up principal**:org-link / Anyone-public / external_group 端到端(需 query 側 inject org/public token;default drop 唔行此路)= live 後 follow-up。
- **auto-sync / delta / 多 provider / 統一管理 console** = 階段 2-3(Tier 2,H4)。landing「connect another source」係 disabled affordance,**唔可以**做到真。
- **抽 `<Stepper>` primitive** = 獨立 refactor(D-2)。
- **credential write/config 端點** = 唔做(H5,credential server-side 配置)。

> **🔴 Tier 邊界**:landing 只係「單 connector card + disabled affordance」,順手做多 provider 卡片真 / sync 狀態監控 → STOP per H4。

## §6 Risks

- 🟡 **H7 fidelity 5 surface**:逐個對齊 mockup(layout/spacing/typography/color token/interaction/responsive/a11y),唔啱 STOP+ask 或標 🚧 deferred。inline stepper 跟 DESIGN_SYSTEM §4.2 28px circle 規格。
- 🟡 **#2 credential H7 deviation(D-4)**:mockup credential 輸入 → 唯讀狀態,屬 H5-driven deviation,**plan approve 時向用戶確認**;impl 時唯讀狀態仍要 design-system 視覺(banner/field 既有 primitive,零發明)。
- 🟡 **Live 不可本機驗(D4)**:browse/import 串真接口但無真 tenant,mock connector 測試 + 前端餵 mock data 跑通 UI flow;端到端留 runbook。
- 🟡 **backend import contract extend(#1)**:`POST /import` 加 `documents` 欄 — 保留 `container_ids` 既有路徑(W100 測試 `test_integration_route` 零 regression 驗證)。
- 🟢 **ingestion 核心零改動**(§7.2 鐵律,Gate diff 驗證)→ blast radius 限新前端 + `integration.py`/`import_service.py` 局部 extend。
- 🟢 **H2 無新 dep**(前端 TanStack Query / lucide-react 既有;backend 既有 connector)。

## §7 Changelog

| 日期 | 變動 | 由 |
|---|---|---|
| 2026-06-30 | **Plan proposed**:接 ADR-0071 Accept(用戶 2026-06-30 拍板獨立頂層 Integrations IA)+ Step 2 範圍 AskUserQuestion(用戶揀 **B — 補 browse 端點 + 串真接口**)。Explore agent map frontend 現狀(route group `(app)` / `app-shell.tsx` `WORKSPACE_NAV` / 無 `<Stepper>` primitive / `lib/api` `xxxApi` pattern / 無 i18n)+ first-hand 讀 backend connector 確認 `browse`/`list_documents`/`resolve_site` 已實作只欠 HTTP expose。識別 3 處 mockup-vs-backend 張力(#1 個別文件粒度 / #2 credential H5 / #3 browse 端點)→ §4 處理。7 deliverable F1(backend 端點)→ F2(nav scaffold)→ F3(API client)→ F4(landing)→ F5(step1+2)→ F6(step3+4)→ F7(收尾 Gate)。**STOP — 等用戶 approve plan + 確認 #2 D-4 credential H7 deviation,先開 F1。** | proposed |
