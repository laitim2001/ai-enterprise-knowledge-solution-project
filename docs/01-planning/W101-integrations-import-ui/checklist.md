# W101 checklist — Integrations 前端匯入 wizard + browse 端點

> 對應 `plan.md` §2 Deliverables F1–F7。Atomic checkbox,逐項 tick。**未 tick 項唔可刪**(只 `[x]` 或加 🚧 + reason)。

## F1 — backend browse/list/resolve 端點 + import 個別 ref path
- [x] F1.1 `import_service.import_selected_documents(connector, handle, kb_id, refs, ingest)` — 收選定 `SourceDocumentRef` list,逐個 fetch + get_principals + ingest(per-doc 錯誤模型同 `import_documents`)
- [x] F1.2 既有 `import_documents`(container 級)**不變**(production-preserve 驗證)
- [x] F1.3 `POST /resolve-site` — body `{ site_url }` → parse hostname+site_path → `connector.resolve_site` → `SourceContainerOut`(兼做 step1「Test connection」)
- [x] F1.4 `GET /browse?container_id=` — optional container_id(None=top)→ collect `connector.browse` → `{ containers: SourceContainerOut[] }`(D-6 server-side cap)
- [x] F1.5 `GET /documents?container_id=` — required → collect `connector.list_documents` → `{ documents: SourceDocumentRefOut[] }`(D-6 cap)
- [x] F1.6 `POST /import` 擴 `documents: list[SourceDocumentRefIn]`(個別 ref path,#1 D-3);`container_ids` 保留向後相容
- [x] F1.7 Pydantic schema `SourceContainerOut` / `SourceDocumentRefOut` / `SourceDocumentRefIn`(鏡像 `integration/models.py` dataclass)
- [x] F1.8 RBAC:browse/list/resolve = `require_role(admin,editor)`;import = + per-KB edit(既有);not-configured 503(既有 helper)
- [x] F1.9 mock connector 單元測(`tests/api/test_integration_route.py` + `tests/integration/`):resolve/browse/list/import-selected happy + RBAC + 503;既有 `import_documents` 測試零 regression
- [x] F1.10 `ruff` + `mypy --strict`(integration package + route module)clean

## F2 — sidebar nav + breadcrumb + route scaffold
- [ ] F2.1 `app-shell.tsx` `WORKSPACE_NAV` `/kb`(行 104)之後加 `{ href:'/integrations', label:'Integrations', Icon: <lucide> }`(icon 對 mockup `10-integrations-landing.html` chain-link)
- [ ] F2.2 `computeBreadcrumbs` 加 `integrations` 分支(`/integrations`→`['Integrations']`;`/integrations/sharepoint/import`→`['Integrations','Import from SharePoint']`)
- [ ] F2.3 `app/(app)/integrations/page.tsx` 骨架(`'use client'`)
- [ ] F2.4 `app/(app)/integrations/sharepoint/import/page.tsx` 骨架(`'use client'`)
- [ ] F2.5 sidebar active 高亮驗證(`usePathname` `isActiveRoute`)+ **唔郁其他 nav 項歸屬**(surgical,D-1)
- [ ] F2.6 `tsc` + `eslint` clean

## F3 — API client + types
- [ ] F3.1 `lib/api/integration.ts` `new ApiClient()` + `integrationApi` object
- [ ] F3.2 `resolveSite(siteUrl)` → `SourceContainer`(POST `/integration/sharepoint/resolve-site`)
- [ ] F3.3 `browse(containerId?)` → `SourceContainer[]`(GET `/integration/sharepoint/browse`)
- [ ] F3.4 `listDocuments(containerId)` → `SourceDocumentRef[]`(GET `/integration/sharepoint/documents`)
- [ ] F3.5 `importSelected(kbId, refs)` → `ImportSummary`(POST `/integration/sharepoint/import`)
- [ ] F3.6 TS types 鏡像 backend schema;URL 無 trailing slash;`tsc` clean

## F4 — Integrations landing(H7 重現 `10-integrations-landing.html`)
- [ ] F4.1 page-header(title「Integrations」+ subtitle)+ banner-info(pipeline/allowed_principals 說明)
- [ ] F4.2 SharePoint connector card(chain-link logo + 名 + desc + 狀態 badge +「Import documents →」link 去 wizard)
- [ ] F4.3 disabled「connect another source」affordance card(Tier 2 badge,opacity .6)
- [ ] F4.4 design-system class(`.content`/`.content-narrow`/`.page-header`/`.card`/`.badge`/`.btn`)+ 連接狀態(可選:call resolveSite 探測或靜態「Not connected」)
- [ ] F4.5 **H7 fidelity check**:逐 section 對齊 mockup(layout/spacing/typography/color token/interaction/responsive)

## F5 — Wizard Step 1 Connect + Step 2 Select(H7 重現 `20`+`21`)
- [ ] F5.1 inline stepper(4 step,28px circle DESIGN_SYSTEM §4.2,done/current/upcoming 態)+ `useState` step state
- [ ] F5.2 Step 1:目標 KB select + site URL input + **credential 唯讀狀態展示(#2 D-4)**(已配置/未配置 banner,非可輸入 fields)
- [ ] F5.3 Step 1「Test connection」→ `resolveSite` → 成功 enable Continue + 狀態 badge
- [ ] F5.4 Step 2:browse 樹(site→library→folder)`browse` lazy load + tree-row active
- [ ] F5.5 Step 2:文件 table + checkbox `listDocuments`;個別文件揀選 state + selected count
- [ ] F5.6 Step 1/2 導航(Continue / Back)+ breadcrumb「Integrations / Import from SharePoint」
- [ ] F5.7 **H7 fidelity check** `20`+`21`(含 credential 唯讀屬 H5 deviation,其餘 100% 對齊)

## F6 — Wizard Step 3 Import + Step 4 Summary(H7 重現 `22`+`23`)
- [ ] F6.1 Step 3:progress bar + per-doc 即時狀態列(ready/processing/queued status-dot)`importSelected`
- [ ] F6.2 Step 3:失敗唔 abort batch(per-doc 狀態獨立)+「runs in background」hint
- [ ] F6.3 Step 4:summary(2 of 3 imported banner + mini-stats imported/failed/chunks)
- [ ] F6.4 Step 4:per-doc table(READY/FAILED badge + detail + scan-PDF guard 例 ADR-0065)+「Retry failed」+「View knowledge base →」
- [ ] F6.5 **H7 fidelity check** `22`+`23`

## F7 — 收尾 + Gate
- [ ] F7.1 `kb/[id]/upload/page.tsx` `SourceKind='sharepoint'` placeholder 改指向 `/integrations/sharepoint/import` link(避免兩入口 drift)
- [ ] F7.2 component test scaffold(視 sprint;至少 landing + wizard smoke)
- [ ] F7.3 Gate G-W101:`tsc`/`eslint` clean + 既有 frontend 測試零 regression + backend mock 測試綠 + `ruff`/`mypy --strict` clean + `test_integration_route`/`test_kb_route_acl` 零 regression + `backend/ingestion/` diff = 零
- [ ] F7.4 doc-sync:BACKLOG B-01(R7)+ WIP memory + progress.md retro
