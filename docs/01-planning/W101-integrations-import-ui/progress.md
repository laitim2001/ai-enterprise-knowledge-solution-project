# W101 progress — Integrations 前端匯入 wizard + browse 端點

> Daily 進度 + 決策 + commits + 結尾 retro。對應 `checklist.md` F1–F7。

---

## Day 0 — 2026-06-30(plan proposed)

### 前情(本 phase 點嚟)
- ADR-0070(統一整合層 connector framework)backend 階段 1 已喺 W100 完成(G-W100 PASS,49 測試,ingestion 核心零改動)。
- 用戶 2026-06-30 review IA 後,連續決定:
  1. 前端 wizard 應做**獨立頂層 Integrations 模組**(非掛 Knowledge 下)→ AskUserQuestion 揀 **landing + wizard 形態** + 命名 **Integrations**。
  2. → **ADR-0071** 寫成 Proposed → 用戶**Accept**(行使 decision owner)。
  3. mockup Step 1 已配套改:新增 `10-integrations-landing.html` + 4 surface(`20`–`23`)shell 由 Knowledge 歸屬改 Integrations(sidebar active / breadcrumb /「‹ Integrations」返回)。
  4. Step 2「Select」backend gap AskUserQuestion → 用戶揀 **B — 補 browse 端點 + 串真接口**。

### 開 plan 前查證(R6 think-before)
- **Explore agent** map frontend 現狀:route group `(app)` + 每 route 一 folder/`page.tsx`;sidebar `components/nav/app-shell.tsx` `WORKSPACE_NAV` array(行 98-107,`/kb` 行 104)+ `computeBreadcrumbs`(行 145-172);**無 `<Stepper>` primitive**(2 個 wizard inline + `useState`);API `lib/api/*.ts` `xxxApi` + `/api/backend/[...path]` proxy;**無 i18n**(hardcode 英文);無既有 integration frontend code。
- **First-hand 讀 backend**:`SharePointConnector` 已實作 `resolve_site` / `browse`(site→library→folder)/ `list_documents` / `fetch_document` / `get_principals`,**只欠 HTTP expose**;`POST /import` 現收 `container_ids`(整 container,`import_documents`)。

### 識別 3 處 mockup-vs-backend 張力(§4 處理)
1. **#1 個別文件粒度**:mockup step2 個別 checkbox vs backend container 級 import → F1 補 `import_selected_documents`(保留 container 級,production-preserve)。
2. **#2 credential H5**:mockup step1 輸入 Tenant/App ID/credential vs backend `.env` server-side(H5)→ **credential fields 改唯讀狀態展示**(H7 deviation,backend/H5 wins per §13,**待用戶 approve plan 確認**)。
3. **#3 browse 端點**:未 expose → F1 補 `resolve-site`/`browse`/`documents`(用戶選 B)。

### 決定(Day 0)
- 自決(已對齊 mockup + Karpathy):D-1 sidebar 加 `WORKSPACE_NAV` `/kb` 後(仍 Workspace section)/ D-2 Stepper inline 不抽 primitive / D-5 browse stateless / D-6 server-side cap。
- **待用戶確認**:#2 D-4 credential 唯讀(H7 deviation due to H5)。
- mockup sidebar 同實際 `app-shell.tsx` 有既有 drift(Eval/Traces 歸屬)— 非本 phase 引入,impl 以實際 app-shell 為準,只加一項(surgical)。

### plan 三件套
- `plan.md`(7 deliverable F1–F7 + Gate G-W101 + §4 六決定 + risks + changelog)/ `checklist.md`(F1.1–F7.4 atomic)/ 本 `progress.md`。
- **Status proposed** — 守 R1,F1 code 未開。

### Approve(2026-06-30 同日)
- 用戶 AskUserQuestion 揀「確認唯讀 + approve,開 F1(推薦)」→ #2 D-4 credential 唯讀**確認**,plan status proposed→**active**。
- BACKLOG B-01 R7 同步(plan active)。
- 開 **F1**(backend 端點,最底層先)。

### F1 完成(2026-06-30)
- backend browse/list/resolve 端點 + import 個別 ref path。
- `import_service.import_selected_documents`(復用 `_import_one`,個別文件路徑;container 級 `import_documents` 不變 = production-preserve)。
- `integration.py`:3 新端點(`POST /resolve-site` / `GET /browse` / `GET /documents`)+ `POST /import` 擴 `documents` ref 欄(both-empty → 422)+ schema(`SourceContainerOut` / `SourceDocumentRefOut` / `SourceDocumentRefIn`)+ RBAC `require_role(admin,editor)` + D-6 `_collect_capped` cap 2000(no silent cap,log warning)。
- credential 仍 server-side(`_new_connector` 由 .env / Key Vault,H5);#2 credential 唯讀屬前端 F5。
- 驗:pytest **24 passed**(既有 + 新端點 happy / RBAC user 403 / 個別 ref path / both-empty 422 / invalid URL 422)/ ruff clean / `mypy --strict`(integration package + route module module-mode)clean。

### F2-F4 完成(2026-06-30)
- F2 sidebar nav + breadcrumb + 2 route 骨架 / F3 API client `integrationApi`(`resolveSite` / `browse` / `listDocuments` / `importSelected`,對齊 F1 schema)/ F4 landing H7 重現 `10-integrations-landing.html`(SharePoint connector card +「Import documents →」+ disabled「connect another source」affordance;inline-style const 對齊 mockup `conn-card` verbatim 值,跟 `kb/new` stepper inline-style pattern)。
- F4 連接狀態靜態「Not connected」(D4 — live 探測需真 tenant);`integrationApi` F5/F6 wizard 先消費。
- 驗:tsc + eslint clean。**H7 browser visual smoke 留 phase 末 / 用戶**(同 BUG-038 pattern — W87 OneDrive dev server 首編 ~135s + Fast Refresh 唔可靠)。

### F5 完成(2026-06-30)
- wizard step1 Connect(KB select `kbApi.list` + site URL +「Test connection」call `resolveSite` + credential 唯讀 banner #2 + Sites.Selected prerequisite banner + Continue gate)+ step2 Select(lazy browse tree `TreeNode` + `listDocuments` 文件 table + 個別 checkbox + selected count)。
- stepper inline 28px circle(`kb/new` pattern,D-2 不抽 primitive);tree-row hover/active 用 scoped `<style>`(`.sp-import` 前綴鏡像 mockup `21` inline style,唔污染全域)。step3/4 placeholder 留 F6。
- 驗:tsc + eslint clean。

### F6 完成(2026-06-30)
- step3 Import:重現 mockup `22` layout(RUNNING badge + banner + progress bar + 揀文件 doc-row 列表),`importSelected` mount auto-run,per-doc 統一「Importing…」→ 完成 `onDone(summary)`。**step3 streaming = 整體 progress 過場**(用戶揀方案 A — backend 同步無 SSE,plan §4 #step3 記);Cancel 按鈕 disabled(同步無得 cancel)。
- step4 Summary:重現 mockup `23`(banner-success + mini-stats + per-doc READY/FAILED table + View KB link)。**第 3 mini-stat 由「Chunks added」改「Documents」**(backend `ImportSummary` 無 chunk count,H7 minor deviation 標明);Retry disabled(階段 1b,功能留 follow-up)。
- doc-row / mini-stat surface class 加入 scoped `<style>`(`.sp-import`,鏡像 mockup `22`/`23` inline style)。
- 驗:tsc + eslint clean。

### Commits
- `docs(adr):` ADR-0071 Accepted + landing mockup(`d84cbf8`)
- `docs(planning):` W101 plan 三件套(`babccd8`)
- `feat(integration):` F1 backend browse/list 端點 + import 個別 ref(`9f2818e`)
- `feat(frontend):` F2 sidebar nav + breadcrumb + route 骨架(`d5dcfc7`)
- `feat(frontend):` F3 API client + F4 landing H7 重現(`5611f2e`)
- `feat(frontend):` F5 wizard step1 Connect + step2 Select(`9972a18`)
- `feat(frontend):` F6 wizard step3 Import + step4 Summary(本 commit)
- (F7 收尾)
