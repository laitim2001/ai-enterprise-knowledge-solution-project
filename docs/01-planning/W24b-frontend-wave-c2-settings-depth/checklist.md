---
phase: W24b-frontend-wave-c2-settings-depth
plan_ref: ./plan.md
status: active
last_updated: 2026-05-20  # F7 active-flip → F7.1-F7.7 complete (Vitest + Playwright tests)
---

# W24b-wave-c2 — Checklist

> Derived from `plan.md §2 F0-F8 deliverables`。延後項標 🚧 + reason(per CLAUDE.md sacred rule — 唔可以刪未勾 `[ ]`)。

## F0 — Kickoff cascade

- [x] **F0.1** W24b folder `plan.md`(this folder)+ `checklist.md` + `progress.md` created `status: active` 2026-05-20
- [x] **F0.2** NO `frontend/` or `backend/` code change at kickoff(per W19-W24 F0 precedent — F0 governance only)
- [x] **F0.3** NO `architecture.md v6` amendment(Wave C2 = depth promotion within ADR-0026 既存 spec — no Cn structural change;Wave C1 had architecture.md amendment because 6-tab scope expansion;Wave C2 仍喺 same 6-tab scope inline-edit)
- [x] **F0.4** Pre-active-flip 5-step grep audit recursive(per CLAUDE.md §10 R6)completed at kickoff prep,documented in `progress.md` Day 0 + plan §7:Wave C1 4 components exist / `error-boundary.tsx` 85 lines exist / `@tanstack/react-query@5.59.0` installed / `react-hook-form` + `zod` + `@hookform/resolvers` NOT installed → F1 H2 trigger / `settings-identity.tsx` 8 處 `readOnly` confirmed / `audit_log.py` 36 lines limit-only no filter
- [x] **F0.5** W24b kickoff cascade committed `(this commit)`

## F1 — react-hook-form + zod install(H2 ADR-0017 mitigation)

- [x] **F1.1** `pnpm add react-hook-form@^7 zod@^3 @hookform/resolvers@^3` — **Plan B (a) clean install in 40.6s,zero R8**;resolved `react-hook-form@^7.76.0` + `zod@^3.25.76` + `@hookform/resolvers@^3.10.0`
- [x] **F1.2** N/A — F1.1 Plan B (a) `pnpm add` succeeded clean;no R8 hit → no ADR-0017 amendment + no Plan B (c) mobile hotspot fallback needed(npm-registry metadata non-binary,per W17 F6 Vitest precedent — confirmed low R8 risk)
- [x] **F1.3** `package.json` 3 new deps confirmed(lines per `grep`);`tsc --noEmit` **exit 0**
- [🚧] **F1.4 DEFERRED to F2.1** — `frontend/lib/schemas/admin/` 空 folder 對 git 無意義(空目錄唔被 tracked);folder 喺 F2.1 首個真 schema `identity.ts` 落地時自然 materialize(per CLAUDE.md §10 R6 adjust-acceptance-to-reality + Karpathy §1.2 avoid-busywork;plan §7 changelog Day 1 row documented)
- [x] **F1.5** Sanity Vitest:`frontend/tests/unit/zod-toolchain.test.ts` NEW(renamed from plan-text `lib-schemas-admin.test.ts` — F1.4 folder deferred so toolchain-level name 更準;R6 deviation logged)— **4/4 pass in 11.9s**:zod parse + safeParse field-error surfacing + zodResolver bridge + useForm export;inline `sampleSchema` mirrors 2 real Wave C1 constraints(tenant_id UUID + alert_threshold_pct 50-95)

## F2 — Zod schemas + form validation wire

- [x] **F2.1** `frontend/lib/schemas/admin/identity.ts` NEW(106 lines)— 5 object schemas(`entraTenantConfigSchema` + `appRegistrationConfigSchema` + `msalConfigSchema` + `roleMappingConfigSchema` + `signInPolicyConfigSchema`)+ 4 enum schemas(cloud / audience / token-cache / ekp-role)mirror backend `admin_identity.py` Pydantic Literals + Field bounds;GUID / duration / domain regex 比 backend `str` 嚴(form-validation 層意義 — value 仍係 `str`,wire contract 不變)
- [x] **F2.2** `frontend/lib/schemas/admin/api_keys.ts` NEW(20 lines)— `alertThresholdSchema`(int 50-95)+ `AlertThresholdInput` z.infer type;mirror backend `AlertThresholdPatch`
- [x] **F2.3** `frontend/lib/schemas/admin/connections.ts` NEW(24 lines)— `providerPatchSchema`(endpoint_url URL-or-empty union + region + display_name min-1)+ `ProviderPatchInput` type;mirror backend `ProviderPatch`
- [🚧] **F2.4 DEFERRED to F5** — `settings-identity.tsx` useForm wire:wiring `useForm` 入全 `readOnly` inputs = inert code;F5 一個 surgical pass 做 remove-readOnly + form + zod + mutation(per CLAUDE.md §10 R6 adjust-to-reality + Karpathy §1.3 surgical;plan §7 Day 1 F2 row documented)。F2 對 Identity 嘅貢獻 = `identity.ts` 5 schemas(F2.1)
- [x] **F2.5** `settings-api-keys.tsx` `OutgoingQuotaRowItem` — `useState`+`handleSave` → `useForm` + `zodResolver(alertThresholdSchema)` + `register('alert_threshold_pct', {valueAsNumber:true})`;`<form onSubmit>` + `reset()` re-baseline;`!isDirty || isSubmitting` disable;inline `errors.alert_threshold_pct.message` 紅字。既有 await save pattern 保留(optimistic 入 F3)
- [🚧] **F2.6 DEFERRED to F3** — `settings-connections.tsx` ProviderRow form:form scaffold 冇 submit mutation = 唔可以 submit 的死表單;F3 一個 pass 做 form + zod + mutation。F2 對 Connections 嘅貢獻 = `connections.ts` schema(F2.3)
- [x] **F2.7** `tsc --noEmit` **REAL exit 0**(用 `> file 2>&1; echo $?` 量度,非 broken `tsc | tail` pipe)+ `next lint` **✔ No ESLint warnings or errors** + `Grep '\[oklch'` across `app`+`components`+`lib` = **0 preserved**;9 NEW/edited 行全部 CSS-first
- [x] **F2.8** NEW(per plan §7 Day 1 F2 changelog)`frontend/tests/unit/admin-schemas.test.ts`(150 lines)— **16/16 pass**:entraTenant(valid + non-GUID + bad enum)+ alertThreshold(in-band + <50 + >95 + non-int)+ signInPolicy(valid domains + missing-@ + tier2-true-reject)+ msal(duration-shape + free-text-reject)+ providerPatch(valid URL + empty + malformed + empty display_name)

## F3 — Connections inline edit + optimistic mutation

> Scope per F2 R6 reshape(aspect-slice → feature-slice,plan §7 Day 1 cont F2)— F3 = Connections inline edit complete unit(form + zod + optimistic mutation),absorbs deferred F2.6。原 aspect-sliced F3.1-F3.5 acceptance(「4 components retrofit」/「queryClient.setQueryData」/「invalidateQueries」)→ feature-slice 重寫,per plan §7 Day 1 cont F3 row。

- [x] **F3.1** `settings-connections.tsx` ProviderRow inline edit form — `useForm<ProviderPatchInput>` + `zodResolver(providerPatchSchema)` + `values` synced to `detail`(handles async-load + optimistic mutation);3 fields(display_name / region / endpoint_url)`.field` 2-col grid + Save changes button(`!isDirty || patchMutation.isPending` disabled)+ inline zod field errors
- [x] **F3.2** `patchMutation` `useMutation` **local-state optimistic**(fork decision D3.1)— `onMutate` snapshot `detail` + `setDetail({...detail,...patch})`;`onError` rollback to snapshot;`onSuccess` server-truth `setDetail(updated)`。`ProviderRow.detail` 係 component-local state → `queryClient.setQueryData` 唔需要;轉 useQuery = scope creep(要重寫 lazy-fetch interaction)per Karpathy §1.3 surgical。narrower `ConnectionEdit` type(display_name 永遠 concrete)令 `{...detail,...patch}` type-check against `ProviderConfig`
- [x] **F3.3** `testMutation` + `rotateMutation` retrofit — `handleTest`/`handleRotate` async fns → `useMutation`;`isPending` 取代 `testing`/`rotating` useState;`onSuccess` setDetail from result(`last_test_status` / `last_test_detail` / `last_rotated_at` / `secret_masked_preview`)— 唔再 in-onSuccess refetch(result 已含 fresh fields)
- [x] **F3.4** Error surfacing — `patchMutation.isError` inline destructive text(`patchMutation.error?.message`)+ per-field zod `errors.{display_name,endpoint_url}.message` 紅字
- [x] **F3.5** Verify gates — `tsc --noEmit` **REAL exit 0**(ConnectionEdit type fix 後)+ `next lint` **✔ clean** + `Grep '\[oklch'`=0 + `settings-6tab.test.tsx` **9/9 regression-clean**(empty `listConnections` mock → 冇 ProviderRow mount → `useMutation` 唔 reach → F3 唔 break test,**唔需加 QueryClientProvider wrapper** — 預判 breakage 證實多餘)

## F4 — ErrorBoundary per tab

> R6 finding(plan §7 Day 1 cont F4):F0 audit 誤判「`error-boundary.tsx` 係 85-line class component」— 實際只 export `ErrorBoundaryView`(presentational error card,畀 Next `error.tsx` route convention 用)。React error boundary 必須係 class component(冇 hook 版本)→ F4 創建真 `ErrorBoundary` class(first-party code,非 new dep,無 H2)。

- [x] **F4.1** `frontend/components/settings/tab-error-state.tsx` NEW(48 lines)— `<TabErrorState tabName onRetry>` fallback;CSS-first `.banner banner-destructive`(對齊 4 settings/* components 既有 fetch-fail inline error 風格)+ AlertTriangle icon + Retry button
- [x] **F4.2** `ErrorBoundary` class NEW(加入 `components/error/error-boundary.tsx`,~45 lines)— `getDerivedStateFromError` + `componentDidCatch`(console.error)+ `reset` re-mount;`fallback: (reset) => ReactNode` render-prop(原 plan-text `fallback={<TabErrorState/>}` ReactNode form → render-prop 先做到 retry wire,R6 adjust)。`settings/page.tsx` 加 `TabBoundary` local helper(DRY for 6 wrap)+ 6 個 tab body 各 wrap(Profile / Appearance / Connections / Identity & Auth / API Keys & Quotas / Account)
- [x] **F4.3** `frontend/tests/unit/error-boundary.test.tsx` NEW(3 tests pass)— healthy child passthrough / fallback on throw / reset re-mount recovers(controllable `MaybeBoom`)— 比 plan「dev throw test」更紮實嘅自動化 verification
- [x] **F4.4** Verify gates — `pnpm exec tsc --noEmit` **REAL exit 0**(`npx tsc` 攞錯 decoy package → 改用 `pnpm exec` local binary)+ `next lint` **✔ clean** + `Grep '\[oklch'`=0 + `settings-6tab.test.tsx` **9/9 regression-clean**(ErrorBoundary 無 error 時 passthrough children → 6-tab render 不變)

## F5 — Identity inline edit activation

> R6 finding(plan §7 Day 1 cont F5):mockup `SettingsIdentity` 嘅 role 編輯 = per-row「⋯」menu + 「Add mapping」(individual CRUD)→ plan F5.5 明文 defer Wave C+ → **F5 = 4 editable cards 非 5**(Tenant / App Registration / MSAL / Sign-in Policy);role card 保持 W24-c1 display。

- [x] **F5.1** `settings-identity.tsx` 完整 rewrite(read-only display → 4 editable form cards)— 8 處 `readOnly` 入面 **7 個移除**(tenant_id / tenant_domain → register editable;client_id → register;redirect_uris → register list;session_ttl / refresh / csrf → register);**1 個保留** = `authority_url`(per F5.4 server-derived);3 個 `disabled` select(cloud_instance / sign_in_audience / token_cache_strategy)→ `register` editable(Tier 2 `<option>` 保持 disabled)
- [x] **F5.2** **4 sub-resource card**(非 5 — role card display per F5.5)各 `useForm<XInput>` + `zodResolver` + `<CardSaveRow>` footer Save button(`!isDirty || isPending` disabled)+ `formState.isDirty` dirty-state;redirect_uris + allowed_email_domains editable list 用 `watch` + `setValue(...,{shouldDirty:true})` add/remove(非 useFieldArray — primitive string array)
- [x] **F5.3** Save → `useMutation` PATCH(`patchTenant`/`patchAppRegistration`/`patchMsal`/`patchPolicy`)→ `onSuccess` `reset(saved)` re-baseline(form-based card:form 本身持 edits,onSuccess re-baseline,onError 保留 edits + 顯示 error — 比 onMutate-rollback 啱,rollback 會棄用戶輸入,per D5.2)+ 422 boundary 透過 disabled Tier 2 `<option>` preserve + `CardSaveRow` inline destructive error 顯示任何 422
- [x] **F5.4** `authority_url` read-only disabled preserved — `watch('authority_url')` controlled display(save 後 server re-derive 會更新);唔 register,唔 edit
- [x] **F5.5** RoleMappingConfig list-replace semantic preserved — `<RoleMappingCard>` 保持 W24-c1 read-only display(individual mapping CRUD = mockup「⋯」menu + 「Add mapping」= Wave C+);Power User row `opacity:0.5` Tier 2 disabled affordance preserved
- [x] **F5.6** H7 per-tab fidelity — 4 cards layout 對齊 mockup line 542-721(grid 1fr/1fr field layout / redirect_uris list with X + Add per mockup line 589-600 / allowed_email_domains list per mockup line 700-705 / switch toggles);`<CardSaveRow>` Save footer 係 functional 必需(mockup static prototype 無 save wiring,同 F2 ApiKeys / F3 Connections Save button precedent 一致)
- [x] **F5.7** `pnpm exec tsc --noEmit` **REAL exit 0** + `next lint` **✔ clean** + `Grep '\[oklch'`=0 + `settings-6tab.test.tsx` **9/9**(F5 令 Identity tab 用 `useMutation` → 預判並修復 settings-6tab 缺 QueryClientProvider:加 `renderSettings()` helper wrap — F5 自己整出嚟嘅 breakage 自己清 per Karpathy §1.3)

## F6 — Audit log filter + pagination

> R6 finding(plan §7 Day 1 cont F6):**(a)** F6.6 plan-text test path「`backend/tests/api/admin/test_audit_log.py`」→ `admin/` 子目錄不存在,實際 = flat `backend/tests/api/test_admin_audit_log.py`;**(b)** F6.3 `next_cursor` = breaking shape change,bare-list → wrapper `AuditLogPage{entries,next_cursor}`,3 existing endpoint tests + `settings-6tab.test.tsx` mock + consumer 全部要 update。

- [x] **F6.1** `backend/storage/audit_log_storage.py` `AuditLogBackend.list_recent` Protocol extended keyword-only `action_type` + `since` + `cursor`(backward-compat default None;return type 保持 `list[AuditLogEntry]`)
- [x] **F6.2** InMemory(in-pass filter loop,`limit` counts post-filter rows)+ Postgres(`WHERE` parameterized conditions — 每個 user value `%s` placeholder,no string interpolation + `ORDER BY id DESC LIMIT %s`)impl filter logic
- [x] **F6.3** NEW `AuditLogPage` schema(`entries` + `next_cursor`);`audit_log.py` `GET /admin/audit-log` add `action_type`(AuditAction Literal)+ `since` + `cursor`(ge=1)query params + `since` UTC-normalize + `limit+1` over-fetch + `next_cursor` compute;`response_model` bare-list → `AuditLogPage`
- [x] **F6.4** `apiClient.admin.listAuditLog` extended signature `(opts: AuditLogQuery = {})` → `Promise<AuditLogPage>` + NEW `AuditLogPage` + `AuditLogQuery` interfaces;`URLSearchParams` query build
- [x] **F6.5** `settings-audit-log.tsx` filter dropdown(action_type `.select` 6 options)+ since `type="date"` input + "Load more" cursor button(local-state extend `useEffect`/`useState`/`useCallback` per D3.1;CSS-first primitives — no mockup, net-new functional UI per R6 finding 5)
- [x] **F6.6** Tests:`backend/tests/api/test_admin_audit_log.py` rewrite 3 existing for wrapper shape + **7 NEW** filter/pagination cases(13 total)+ `backend/tests/storage/test_audit_log.py` **4 NEW** storage filter cases(10 total)+ `frontend/tests/unit/settings-audit-log.test.tsx` **NEW 3** filter interaction + `settings-6tab.test.tsx` mock(line 132)updated 新 shape
- [x] **F6.7** mypy strict route+schema **clean** + `audit_log_storage.py` clean(`audit_log_postgres.py` 只 pre-existing psycopg import-not-found per R8/F1.5b 環境)+ `tsc --noEmit` **exit 0** + `next lint` **✔ clean** + `Grep '\[oklch'`=**0** + backend pytest **816 passed + 11 skipped + 0 failed**(805 baseline +11)+ Vitest settings-audit-log 3/3 + settings-6tab 9/9 regression

## F7 — Tests(Vitest + Playwright)

> R6 finding(plan §7 Day 1 cont F7):**(a)** F7.2 content(action_type filter + cursor pagination)已由 F6.6 `settings-audit-log.test.tsx` 3 cases 交付 → F7.2 = extend 嗰個 file(非 `-filter` 新檔);**(b)** F7.3 `/settings?tab=identity` test 既有 → extend;**(c)** F7.4 無 identity baseline(只 connections)→ first-capture 非 re-capture;**(d)** Playwright run + PNG capture = user pre-Beta smoke per W24-c1 precedent;**(e)** F7 無 backend change → pytest 816 from F6 preserved。

- [x] **F7.1** `frontend/tests/unit/settings-identity-form.test.tsx` NEW(4 cases)— `<SettingsIdentity>` TenantCard RHF + zod:malformed tenant_id → "Must be a valid GUID" on submit + `patchTenant` not called / valid value clears error / malformed tenant_domain → domain regex error / valid edit → `patchTenant` called with `authority_url:null`
- [x] **F7.2** `frontend/tests/unit/settings-audit-log.test.tsx`(F6.6-created)**extended** +2 NEW — since date filter re-fetch(`listAuditLog` called with `since`)+ filtered empty-state message(F6 baseline 3 → **5 cases**)
- [x] **F7.3** `frontend/tests/e2e/app-shell-path.spec.ts` 既有 `/settings?tab=identity` test **extended** — dirty-state `<CardSaveRow>` Save button render-smoke(`saveButton.or(banner).or(errorBanner)` 3-state per BUG-004;strict type→enable interactive = user pre-Beta smoke)
- [x] **F7.4** `frontend/tests/e2e/visual-baseline.spec.ts` 加 `Settings ?tab=identity` 新 test spec(mask `.mono`);PNG first-capture user-deferred per W24-c1/W20 F8.5/W23 F2.3 precedent
- [x] **F7.5** Vitest — settings-area 6-file deterministic batch **41/41 pass**(settings-6tab 9 + settings-audit-log 5 + settings-identity-form 4 + zod-toolchain 4 + admin-schemas 16 + error-boundary 3);full-suite run 15 files green 但命中 OneDrive worker-pool start-timeout(W23-documented infra flakiness per setup.md §8.7 — 非 regression;smaller-batch 係 workaround)
- [🚧] **F7.6 spec landed,execution user-deferred** — `app-shell-path.spec.ts` + `visual-baseline.spec.ts` spec 改動已 land + `tsc`/`lint` clean;`PW_CHANNEL=chrome pnpm exec playwright test` execution + `settings-identity.png` PNG first-capture = **user pre-Beta smoke**(needs dev server + backend + system Chrome 同時起,per W24-c1「Playwright +2 user-deferred」+ W20 F8.5 + W23 F2.3 precedent)
- [x] **F7.7** Backend pytest — F7 全 frontend test 改動,**無 backend change** → **816 passed preserved from F6**(per Karpathy §1.2 唔重跑 zero-delta 4.5-min suite);`tsc --noEmit` exit 0 + `next lint` ✔ clean

## F8 — Closeout cascade

- [ ] **F8.1** Phase Gate verdict published per `progress.md` retro
- [ ] **F8.2** 7-section retro per F-deliverable
- [ ] **F8.3** plan/checklist/progress frontmatter `active → closed`
- [ ] **F8.4** W24c+ candidates noted in retro **NOT pre-created** per CLAUDE.md §10 R1 rolling JIT
- [ ] **F8.5** `session-start.md` 6 places synced
- [ ] **F8.6** `COMPONENT_CATALOG.md` C08 + C09 + C11 W24b status amendments
- [ ] **F8.7** `PAGE_INVENTORY.md` `/settings` row Wave C1+C2 hybrid amendment
- [ ] **F8.8** ADR-0026 Implementation Status section amendment(Wave C1 → Wave C1+C2 implemented)
- [ ] **F8.9** `PAGE_INVENTORY.md` row 8/9/10 staleness drift fix(observability cluster W22 F7 already-rebuilt update)

---

**Lifecycle reminder**:新加 acceptance item 必先入 `plan.md §2 F-deliverables`,然後再加 checklist。延後項標 🚧 + reason,唔可以刪。
