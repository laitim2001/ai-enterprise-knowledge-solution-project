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
- [x] F2.1 `app-shell.tsx` `WORKSPACE_NAV` `/kb`(行 104)之後加 `{ href:'/integrations', label:'Integrations', Icon: <lucide> }`(icon 對 mockup `10-integrations-landing.html` chain-link)
- [x] F2.2 `computeBreadcrumbs` 加 `integrations` 分支(`/integrations`→`['Integrations']`;`/integrations/sharepoint/import`→`['Integrations','Import from SharePoint']`)
- [x] F2.3 `app/(app)/integrations/page.tsx` 骨架(`'use client'`)
- [x] F2.4 `app/(app)/integrations/sharepoint/import/page.tsx` 骨架(`'use client'`)
- [x] F2.5 sidebar active 高亮驗證(`usePathname` `isActiveRoute`)+ **唔郁其他 nav 項歸屬**(surgical,D-1)
- [x] F2.6 `tsc` + `eslint` clean

## F3 — API client + types
- [x] F3.1 `lib/api/integration.ts` `new ApiClient()` + `integrationApi` object
- [x] F3.2 `resolveSite(siteUrl)` → `SourceContainer`(POST `/integration/sharepoint/resolve-site`)
- [x] F3.3 `browse(containerId?)` → `SourceContainer[]`(GET `/integration/sharepoint/browse`)
- [x] F3.4 `listDocuments(containerId)` → `SourceDocumentRef[]`(GET `/integration/sharepoint/documents`)
- [x] F3.5 `importSelected(kbId, refs)` → `ImportSummary`(POST `/integration/sharepoint/import`)
- [x] F3.6 TS types 鏡像 backend schema;URL 無 trailing slash;`tsc` clean

## F4 — Integrations landing(H7 重現 `10-integrations-landing.html`)
- [x] F4.1 page-header(title「Integrations」+ subtitle)+ banner-info(pipeline/allowed_principals 說明)
- [x] F4.2 SharePoint connector card(chain-link logo + 名 + desc + 狀態 badge +「Import documents →」link 去 wizard)
- [x] F4.3 disabled「connect another source」affordance card(Tier 2 badge,opacity .6)
- [x] F4.4 design-system class(`.content`/`.content-narrow`/`.page-header`/`.card`/`.badge`/`.btn`)+ 連接狀態(可選:call resolveSite 探測或靜態「Not connected」)
- [x] F4.5 **H7 fidelity check**:逐 section 對齊 mockup(layout/spacing/typography/color token/interaction/responsive)

## F5 — Wizard Step 1 Connect + Step 2 Select(H7 重現 `20`+`21`)
- [x] F5.1 inline stepper(4 step,28px circle DESIGN_SYSTEM §4.2,done/current/upcoming 態)+ `useState` step state
- [x] F5.2 Step 1:目標 KB select + site URL input + **credential 唯讀狀態展示(#2 D-4)**(已配置/未配置 banner,非可輸入 fields)
- [x] F5.3 Step 1「Test connection」→ `resolveSite` → 成功 enable Continue + 狀態 badge
- [x] F5.4 Step 2:browse 樹(site→library→folder)`browse` lazy load + tree-row active
- [x] F5.5 Step 2:文件 table + checkbox `listDocuments`;個別文件揀選 state + selected count
- [x] F5.6 Step 1/2 導航(Continue / Back)+ breadcrumb「Integrations / Import from SharePoint」
- [x] F5.7 **H7 fidelity check** `20`+`21`(含 credential 唯讀屬 H5 deviation,其餘 100% 對齊)

## F6 — Wizard Step 3 Import + Step 4 Summary(H7 重現 `22`+`23`)
- [x] F6.1 Step 3:progress bar + per-doc 即時狀態列(ready/processing/queued status-dot)`importSelected`
- [x] F6.2 Step 3:失敗唔 abort batch(per-doc 狀態獨立)+「runs in background」hint
- [x] F6.3 Step 4:summary(2 of 3 imported banner + mini-stats imported/failed/chunks)
- [x] F6.4 Step 4:per-doc table(READY/FAILED badge + detail + scan-PDF guard 例 ADR-0065)+「Retry failed」+「View knowledge base →」
- [x] F6.5 **H7 fidelity check** `22`+`23`

## F7 — 收尾 + Gate
- [x] F7.1 ~~upload placeholder 改指向~~ → **不改 upload**(用戶 2026-06-30 揀:改 `kb/[id]/upload` sharepoint placeholder 會偏離其 mockup `ekp-page-misc.jsx` 觸 H7;disabled「Wave C+」placeholder non-functional 唔構成真 drift。plan changelog R3)
- [ ] F7.2 🚧 **deferred** component test scaffold — per DD-2(frontend test deferred pattern);階段 1b 純前端 UI(H6 UI test nice-to-have);target = 對應 view 再動 / F8 batch 補
- [x] F7.3 Gate G-W101 **PASS(caveat)**:tsc+eslint clean / backend pytest **80 passed**(integration+RBAC) / ruff+mypy clean / **ingestion diff=零** / 5 surface H7 對齊 mockup。⚠️ **vitest 14 fail = pre-existing**(kb config view test;git diff 證 W101 零 touch → 0 regression;單跑穩定 fail;`app-shell.test` pass);live 留 runbook(D4)
- [x] F7.4 doc-sync:plan close + progress retro + BACKLOG B-01(R7,前端 impl done)+ E 區 14 pre-existing test 債 + WIP memory
