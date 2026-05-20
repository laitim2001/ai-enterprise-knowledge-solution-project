---
phase: W24b-frontend-wave-c2-settings-depth
plan_ref: ./plan.md
checklist_ref: ./checklist.md
status: active                      # active | closed
---

# W24b-wave-c2 — Progress

## Day 0 — 2026-05-20 — Kickoff cascade(F0)

### Done

- **Sprint pivot trigger** — Chris initial directive 2026-05-20「confirm scope kickoff W24b-wave-b plan」→ pre-active-flip R6 audit surfaced **W22 F7.1/F7.2/F7.3 已 strict-fidelity rebuild 3 observability routes**(`/eval` + `/traces` + `/traces/[traceId]` page.tsx 989/383/1522 lines all carry「W22 F7.x (2026-05-18 D5) — complete rewrite for mockup fidelity per CLAUDE.md §5.7 H7」 docstring header)→ wave-b-observability scope redundant → AskUserQuestion 2026-05-20「W22 F7 已 rebuild 3 routes,W24b scope 邊個方向?」 → Chris pick **「Pivot to W24b-wave-c2-settings-depth(推薦)」**
- **Pre-active-flip 5-step grep audit recursive**(per CLAUDE.md §10 R6 W23 v1.9 amendment):
  - **(1) read plan literal acceptance criteria** — Wave C2 promote items per W24-wave-c1 retro Day 1 cont(F6.3 form validation + F6.4 optimistic UI + F6.5 ErrorBoundary + Identity inline edit + Connections deployment cap edit + Audit log filter/pagination + real-MSAL feature flag concurrent ship + ADR-0027 RBAC)
  - **(2) grep code base for referenced files**:
    - `frontend/components/settings/` confirmed 4 components exist(connections.tsx 279 / identity.tsx 425 / api-keys.tsx 376 / audit-log.tsx 104 = 1184 lines total Wave C1)
    - `frontend/components/error/error-boundary.tsx` 85 lines exists(class component)
    - `frontend/components/ui/api-key-input.tsx` + `deployments-table.tsx` + `service-card.tsx` + `disabled-affordance.tsx` 3 NEW Wave C1 primitives + W19 F5 shared affordance exist
    - `frontend/package.json` line 31 `@tanstack/react-query@5.59.0` installed;**`react-hook-form` + `zod` + `@hookform/resolvers` NOT installed** → F1 H2 trigger confirmed
    - `frontend/lib/api/admin.ts` 264 lines existing(13 methods);`listAuditLog(limit=10)` already wired
    - `settings-identity.tsx` 8 處 `readOnly` confirmed(line 96/106/115/163/190/256/265/274 — 5 sub-resource card 全部 disabled-input Wave C1 read-mostly)
    - `settings-api-keys.tsx` line 225 `useState(row.alert_threshold_pct)` + line 308 Save button — Wave C1 既有 inline-edit pattern;F2 upgrade to react-hook-form + zod
    - `frontend/lib/auth/index.ts` line 34 `isMockMode = process.env.NEXT_PUBLIC_AUTH_MOCK === "true"` switch already wired;`msal_provider.ts` 110+ lines exists → real-MSAL feature flag **already concurrent-shipped** Wave C1 era,Wave C2 work = verify path live(依賴 Q11 IT cred)→ **OUT OF SCOPE Wave C2,Track A parallel**
    - `backend/api/routes/admin/audit_log.py` 36 lines `limit=Query(default=10, ge=1, le=200)` only — no `action_type` / `since` / `cursor` filters → F6 trigger
  - **(3) surface mismatches via Karpathy §1.1 think-before-coding**:
    - **Critical finding**: `PAGE_INVENTORY.md` row 8/9/10 仍 mark observability cluster `/eval` + `/traces` + `/traces/[traceId]` 為「⏳ Wave B candidate (W21+)」— 但 W22 F7 deliverable row(line 19)已標 `ad3ec90` + `4f1eadd` landed strict-fidelity rebuild;**inventory documentation drift** but not implementation drift → F8.9 surgical fix during W24b closeout
    - **Scope cuts surfaced upfront**: Connections deployment cap edit per W24-c1 F4 plan §7 deviation = Azure portal authoritative,non-Wave-Cn stream → OUT;real-MSAL feature flag = Track A IT cred parallel(Q11 operational early June 2026)→ OUT
  - **(4) document deviations in plan §7 changelog** — Day 0 row landed
  - **(5) adjust acceptance criteria per actual reality** — F0-F8 acceptance criteria reflect lean Wave C2 scope(7 deliverables + governance bookends;exclude Connections cap + real-MSAL)
- W24b folder + 3 docs landed `docs/01-planning/W24b-frontend-wave-c2-settings-depth/{plan,checklist,progress}.md` `status: active`
- **F0.1** + **F0.2** + **F0.3** + **F0.4** + **F0.5** acceptance criteria met at kickoff cascade

### Decisions

- **D0.1 — Wave C2 scope = 7 deliverables(F1-F7)+ F0/F8 governance** per Chris AskUserQuestion 2026-05-20 pick「Pivot to W24b-wave-c2-settings-depth(推薦)」 over「Keep wave-b backend connect verify」+「Pivot to users-rbac-tier-1-5」+「STOP — fix inventory drift first」。Rationale:Wave C1 retro 7 Wave C2 promote items 入面 5 個適合 W24b(form validation + optimistic UI + ErrorBoundary + Identity inline edit + Audit log filter);Connections deployment cap + real-MSAL feature flag 2 個係 parallel track non-Wave-Cn stream
- **D0.2 — NO architecture.md amendment at F0** per W24-wave-c1 precedent — Wave C1 ship 之前 Settings v1 thin → 6-tab hub 屬 ADR-0024 §5.0 amendment;Wave C2 仍喺 same 6-tab scope inline-edit depth,**no Cn structural change**,純粹 component-level behavior promotion
- **D0.3 — F1 H2 mitigation Plan B (a) `pnpm add` 首輪**(react-hook-form + zod 屬 npm-registry metadata,non-binary)— precedent W17 F6 Vitest + RTL `pnpm add -D` 成功,W20 F4 wizard 若有 react-hook-form prior install 應已 verified;Plan B (c) mobile hotspot 留 fallback。Per ADR-0017 Decision-rule #5 sequencing
- **D0.4 — F0 governance only**(per W19-W24 F0 precedent)— NO `frontend/` or `backend/` code change at kickoff;F0 純粹 plan + checklist + progress + commit
- **D0.5 — Karpathy §1.3 surgical**:Wave C2 components extend not rewrite — 4 settings/* + page.tsx 既有 W22 F8.1 + W24-c1 F5 嘅 structure 保留,只係:
  - Replace `useState + try/catch` with `useMutation`
  - Remove `readOnly` props in `settings-identity.tsx`
  - Wrap tab content in `<ErrorBoundary>`
  - 加 zod schemas + form validation hooks
  - 加 audit log filter UI(dropdown + date input + Load more)
- **D0.6 — F4 ErrorBoundary 用 既有 `frontend/components/error/error-boundary.tsx`**(85 lines class component)而非 寫 NEW — W14 CO_F4 carry-over 嘅 existing implementation 已 ready;Wave C2 只需 wire fallback prop + wrap-points
- **D0.7 — F6 audit log filter pagination cursor design = `id` SERIAL DESC cursor**(per W24-c1 `audit_log_postgres.py` ORDER BY id DESC 已用);`next_cursor: int | None` response field;无 `since: datetime` 同 `cursor` 衝突 — `since` 過濾 created_at,cursor 過濾 id,兩者 AND
- **D0.8 — Real-calendar estimate ~0.5-1 actual days**(per W22-W24 real-calendar collapse pattern;C09 frontend mid scope + 1 NEW dep)— budget ~3-5 plan day window

### Decisions Log per CLAUDE.md §10 R5

- ADR-0026 既存 → Wave C2 = `Accepted + Wave C1 implemented` 升 `Accepted + Wave C1+C2 implemented` at F8.8(amendment-only,no NEW ADR)
- ADR-0017 既存 → 若 F1.1 Plan B (a) fail → ADR-0017 amendment occurrence #9 row + Plan B (c) hotspot 詳細;若 F1.1 success → ADR-0017 unchanged
- ADR-0027 既存 → Wave C2 Identity inline edit 必須 preserve Power User 422 boundary(不會 break ADR-0027 Option B fallback)
- W24b H1 trigger = **none**(no architecture change)
- W24b H2 trigger = react-hook-form + zod NEW deps → F1.1 Plan B (a) attempt + F1.2 fallback path

### Acceptance(plan §3 + checklist F0)

- [x] F0.1 W24b 3 docs created `status: active`
- [x] F0.2 NO code change at kickoff
- [x] F0.3 NO architecture.md amendment(depth promotion within ADR-0026 既存 spec)
- [x] F0.4 Pre-active-flip 5-step grep audit recursive completed
- [x] F0.5 kickoff cascade commit `(this commit)`

**Day 0 Verdict**:W24b-wave-c2 **active**;F0 kickoff cascade 100% complete in single commit。F1-F8 detailed at per-deliverable active flip per rolling JIT。Real-calendar:Day 0 = same-session as W24-wave-c1 closeout + 24h cooling period + W24b pivot kickoff(Wave C1 closeout 2026-05-19 + W24b pivot 2026-05-20)。

### Actual vs Planned Effort

| F# | Planned days | Actual days | Variance | Notes |
|---|---|---|---|---|
| F0 | 0.25 | 0.25 | 0 | Single-commit kickoff per W19-W24 F0 precedent |
| F1 | 0.5 | ~0.15 | -0.35 | Plan B (a) clean install no R8 friction;F1.4 folder defer F2.1 |
| F2 | 1.0 | ~0.4 | -0.6 | 3 schemas + ApiKeys upgrade + 16-test suite;F2.4→F5 + F2.6→F3 deferred |
| F3 | 1.0 | ~0.4 | -0.6 | Connections inline edit + 3 useMutation;1 tsc type-fix(ConnectionEdit) |
| F4-F8 | _TBD per active flip_ | _TBD_ | _TBD_ | Rolling JIT per CLAUDE.md §10 R1 |

---

## Day 1 — 2026-05-20 — F1 react-hook-form + zod install + sanity test

### Done

- **F1 pre-active-flip 5-step grep audit recursive**(per CLAUDE.md §10 R6):
  - **(1)** read F1 plan literal acceptance criteria — F1.1-F1.5
  - **(2)** grep code base — `react-hook-form` / `zod` / `@hookform` 完全唔喺 `frontend/app` + `frontend/components` + `frontend/lib`(greenfield);`docs/adr/` 確認 ADRs 去到 0031(0030 + 0032 skipped per session-start)— next available NNNN ≥ 0033 但 W24b 無 NEW ADR;`frontend/app/(app)/kb/new/page.tsx`(W20 F4 5-step wizard)用 plain `useState`(line 104-105)— **無 react-hook-form precedent**,F2 zod 整合 fully greenfield
  - **(3)** surface mismatches via Karpathy §1.1 — 2 deviations(F1.4 空 folder git-meaningless / F1.5 test 檔名隨 folder defer 而 rename)
  - **(4)** document deviations in plan §7 changelog — Day 1 row landed
  - **(5)** adjust acceptance criteria — F1.4 → F2.1 / F1.5 → `zod-toolchain.test.ts`
- **F1.1** `pnpm add react-hook-form@^7 zod@^3 @hookform/resolvers@^3` — **Plan B (a) clean install in 40.6s,zero R8**(npm-registry metadata non-binary;`+8 -58` packages,resolved 620);landed `react-hook-form@^7.76.0` + `zod@^3.25.76` + `@hookform/resolvers@^3.10.0`
- **F1.2** N/A — F1.1 Plan B (a) succeeded clean,no R8 hit → no ADR-0017 amendment + no Plan B (c) mobile hotspot fallback;confirms W17 F6 Vitest npm-registry precedent(R8 blocks binary-CDN / image-layer downloads,not npm/PyPI metadata)
- **F1.3** `package.json` 3 new deps confirmed;`pnpm-lock.yaml` updated;`npx tsc --noEmit` **exit 0**(types resolve)
- **F1.4** DEFERRED to F2.1 — `frontend/lib/schemas/admin/` folder materialize 喺首個真 schema 落地時
- **F1.5** `frontend/tests/unit/zod-toolchain.test.ts` NEW(60 lines)— toolchain sanity:zod `.parse()` valid path + `.safeParse()` field-error surfacing(`tenant_id` + `alert_threshold_pct`)+ `zodResolver` bridge typeof function + `useForm` export typeof function;**4/4 pass in 11.9s**;inline `sampleSchema` mirror 2 real Wave C1 constraint(Entra `tenant_id` UUID + `alert_threshold_pct` int 50-95)

### Decisions

- **D1.1 — F1.4 空 folder defer F2.1** per Karpathy §1.2 simplicity — git 唔 track 空目錄;為滿足「folder NEW」字面去整 throwaway placeholder file 屬 busywork;folder 喺 F2.1 `identity.ts` 落地時自然 materialize。R6 adjust-acceptance-to-reality。
- **D1.2 — F1.5 test 改名 `zod-toolchain.test.ts`** — plan-text `lib-schemas-admin.test.ts` 隱含 import `lib/schemas/admin/`;F1.4 folder 既 defer,toolchain-level 命名更準確反映 test 實際驗證內容(3-dep 整合 sanity,非 schema collection coverage)。
- **D1.3 — react-hook-form + zod H2 = NO NEW ADR** per W24-wave-c1 F1 Key Vault SDK precedent — NEW dep within an approved parent ADR scope(ADR-0026 Option B「fully editable」→ form validation inherent)= parent ADR covers + ADR-0017 amendment only IF Plan B fallback 用到;F1.1 Plan B (a) succeeded → ADR-0017 unchanged。
- **D1.4 — zod v3 not v4** per plan §1 spec(`zod@^3`)— zod v3 rock-solid + `@hookform/resolvers@^3` 對齊 zod 3;zod 4 / resolvers v5 屬 future migration,Wave C2 唔 scope-creep。

### Acceptance(plan §3 + checklist F1)

- [x] F1.1 pnpm add 3 deps — Plan B (a) clean
- [x] F1.2 N/A — no R8 fallback needed
- [x] F1.3 package.json + tsc exit 0
- [🚧] F1.4 deferred F2.1(R6 adjust)
- [x] F1.5 sanity test 4/4 pass

**Day 1 F1 Verdict**:F1 complete — 3 form-validation deps landed clean(Plan B (a),zero R8 friction)+ toolchain sanity 4/4 green。F2 zod schemas + form validation wire next。Real-calendar:F1 ~0.15 day vs 0.5 plan estimate(-0.35 — `pnpm add` 無 R8 friction collapse)。

---

## Day 1 cont — 2026-05-20 — F2 zod schemas + form validation wire

### Done

- **F2 pre-active-flip 5-step grep audit recursive**(per CLAUDE.md §10 R6)— 讀 `admin.py` + `admin_identity.py` + `admin_api_keys.py` backend Pydantic + `lib/api/admin.ts` TS mirror + `settings-{identity,api-keys,connections}.tsx` 3 components:
  - **(3) surface mismatches** — F2/F3/F5 原 aspect-slice 切法令 component 處於 incoherent intermediate state:F2.4 wire useForm 入全 readOnly Identity = inert / F2.6 Connections form scaffold 冇 mutation = 死表單。**Adjust** aspect-slice → feature-slice:F2 = pure validation layer + ApiKeys 既有 edit 硬化;F2.4 wire → F5、F2.6 wire → F3(各自一個 surgical pass)
  - **(4) document** — plan §7 Day 1 cont F2 row landed
  - **(5) adjust** — F2 ship 3 schemas + ApiKeys upgrade + 16-test suite;F2.8 schema test added(plan §2 F2 原無)
- **F2.1** `frontend/lib/schemas/admin/identity.ts` NEW(106 lines)— 5 object schemas + 4 enum schemas mirror `admin_identity.py` Literals(`CloudInstance` / `SignInAudience` / `TokenCacheStrategy` / `EkpRoleKey`)+ Field bounds(`auto_disable_after_days >= 0` / `require_mfa_all_roles_tier2` z.literal(false));GUID(`.uuid()`)+ duration(`/^\d+[smhd]$/`)+ domain(`/^@.../`)regex 比 backend plain `str` 嚴 — form-validation 層意義,value 仍 `str`,wire contract 不變。F1.4-deferred `lib/schemas/admin/` folder 喺此 materialize
- **F2.2** `frontend/lib/schemas/admin/api_keys.ts` NEW(20 lines)— `alertThresholdSchema`(int 50-95)mirror `AlertThresholdPatch`
- **F2.3** `frontend/lib/schemas/admin/connections.ts` NEW(24 lines)— `providerPatchSchema`(endpoint_url URL-or-empty `z.union`)mirror `ProviderPatch`
- **F2.4** DEFERRED to F5 — Identity useForm wire(全 readOnly,F5 一個 pass)
- **F2.5** `settings-api-keys.tsx` `OutgoingQuotaRowItem` 升級 — `useState`+`handleSave` → `useForm<AlertThresholdInput>` + `zodResolver` + `register(...,{valueAsNumber:true})`;`<form onSubmit>` + `handleSubmit` + `reset()` re-baseline post-save;`!isDirty || isSubmitting` disable;inline zod error 紅字。既有 await save pattern 保留(optimistic 入 F3)
- **F2.6** DEFERRED to F3 — Connections ProviderRow form wire(冇 mutation = 死表單,F3 一個 pass)
- **F2.7** Verify gates:`tsc --noEmit` **REAL exit 0**、`next lint` **✔ No ESLint warnings or errors**、`Grep '\[oklch'` across `app`+`components`+`lib` = **0 preserved**
- **F2.8** `frontend/tests/unit/admin-schemas.test.ts` NEW(150 lines)— **16/16 pass in 49s**:5 schema × happy + sad path
- **Pre-existing defect caught + fixed** — 量度 tsc REAL exit 時發現 `settings-6tab.test.tsx:138` `beforeEach` 漏 import(W24-c1 F7 `1a3784c` latent;該 phase「tsc exit 0」用 broken `tsc | tail` pipe 量度 — 我 F2 第一次量度都犯同樣 pipe 錯,即時更正)→ 獨立 Trivial-class `fix(frontend): add missing beforeEach import` commit **`d10bf2c`**(per PROCESS.md §1 typo-class,F2 commit 前 land)
- **Regression check** — `settings-6tab.test.tsx`(9)+ `zod-toolchain.test.ts`(4)= **13/13 pass**;`settings-api-keys.tsx` RHF 改動冇 break API Keys tab render-smoke

### Decisions

- **D2.1 — F2/F3/F5 aspect-slice → feature-slice** per Karpathy §1.1 + §1.3 — 每個 F-deliverable 要留 codebase 喺 coherent state。原 plan F2「wire useForm structural,F5 activate」會令 Identity component 經歷 inert-useForm 中間態 + 3-pass;feature-slice(F2=schemas,F3=Connections-edit-complete,F5=Identity-edit-complete)每個 component 一個 coherent pass。總 scope / components / outcome 不變,只 regroup。
- **D2.2 — F2 ApiKeys upgrade keep,Identity/Connections wire defer** — ApiKeys `OutgoingQuotaRowItem` 本身已有 self-contained alert-threshold edit(Wave C1 shipped),F2「加 zod validation」係 coherent shippable change(component 全程 functional)。Identity(全 readOnly)+ Connections(冇 form)冇既有 edit,wire 入去無 mutation 唔 functional → defer 去佢哋各自 feature slice。
- **D2.3 — zod regex 比 backend `str` 嚴** — backend `tenant_id` / `session_ttl` / email domain 全部 plain `str`;zod 加 GUID / duration / `@`-prefix regex。Rationale:form-validation 層嘅意義就係喺 submit 前 catch malformed input(malformed tenant GUID → MSAL auth silently break)。Value 通過 regex 後仍係 `str`,wire contract 不變 — 唔 violate CLAUDE.md §13 backend-wins(嗰條係 field-shape contract,呢度 field shape 仍 `str`)。
- **D2.4 — `valueAsNumber:true` on alert-threshold input** — RHF number input 預設返 string;`valueAsNumber` 令 zod `.number()` resolver 直接收到 number。Empty input → `NaN`(typeof number)→ `.int()`/`.min(50)` fail → inline error,acceptable behavior。
- **D2.5 — Trivial-class fix 獨立 commit `d10bf2c`** — `beforeEach` 漏 import 屬 PROCESS.md §1 typo-class(< 30 min,無需 BUG folder);獨立 `fix(frontend):` commit 喺 F2 commit 之前 land,令 F2「tsc REAL exit 0」gate 誠實 + 唔將 W24-c1 defect fix 混入 F2 feature commit(Karpathy §1.3 surgical separation)。
- **D2.6 — broken `tsc | tail` pipe exit-code 教訓** — `npx tsc | tail; echo $?` 嘅 `$?` 係 `tail` 嘅 exit,唔係 `tsc` 嘅;W24-c1(+ 我 F1 + F2 第一次量度)都中招。正確量度 = `npx tsc --noEmit > file 2>&1; echo $?`。後續 F3-F8 tsc verify 一律用正確法。

### Acceptance(plan §3 + checklist F2)

- [x] F2.1 identity.ts 5 schemas + 4 enums
- [x] F2.2 api_keys.ts alertThresholdSchema
- [x] F2.3 connections.ts providerPatchSchema
- [🚧] F2.4 deferred F5(Identity all-readOnly)
- [x] F2.5 ApiKeys OutgoingQuotaRowItem RHF + zod upgrade
- [🚧] F2.6 deferred F3(Connections no existing form)
- [x] F2.7 tsc REAL exit 0 + lint clean + [oklch=0
- [x] F2.8 admin-schemas.test.ts 16/16

**Day 1 cont F2 Verdict**:F2 complete — pure validation layer(3 zod schema files mirror backend Pydantic)+ ApiKeys alert-threshold RHF+zod 硬化 + 16-test schema suite green。1 pre-existing W24-c1 tsc defect 順帶 caught + Trivial-fixed(`d10bf2c`)。F3 Connections inline edit(form + zod + optimistic mutation)next。Real-calendar:F2 ~0.4 day vs 1.0 plan estimate。

---

## Day 1 cont — 2026-05-20 — F3 Connections inline edit + optimistic mutation

### Done

- **F3 pre-active-flip 5-step grep audit recursive**(per CLAUDE.md §10 R6):
  - **(2) grep** — `QueryClientProvider` confirmed mounted via `(app)/layout.tsx` → `<QueryProvider>`(`lib/providers/query-provider.tsx`,staleTime 30s / retry 1);settings 喺其下,`useMutation` 可用。`service-card.tsx` API confirmed(`endpoint?` prop optional → 唔傳就唔 render endpoint strip)。mockup `ekp-page-settings-tabs.jsx:383-457 ServiceCard` 確認 expanded body 用 editable `.input mono` grid
  - **(3) surface** — optimistic UI fork(useQuery cache 轉換 vs local-state);ProviderRow `detail` 係 component-local state → local-state optimistic,無需 useQuery 轉換
  - **(5) adjust** — F3 acceptance feature-slice 重寫(原 aspect-slice);plan §7 Day 1 cont F3 row landed
- **F3.1** `settings-connections.tsx` ProviderRow inline edit form — `useForm<ProviderPatchInput>` + `zodResolver(providerPatchSchema)` + `values` prop(sync to `detail`,handle async-load + optimistic);3-field `.field` 2-col grid(display_name / region / endpoint_url full-width mono)+ Save changes button + inline zod errors
- **F3.2** `patchMutation` `useMutation` local-state optimistic — `onMutate` snapshot `detail` + `setDetail({...detail,...patch})`;`onError` rollback;`onSuccess` `setDetail(updated)` server-truth。narrower `ConnectionEdit` type(`endpoint_url: string|null` + `region: string|null` + `display_name: string`)— form 永遠送 concrete display_name,令 `{...detail,...patch}` type-check against `ProviderConfig`
- **F3.3** `testMutation` + `rotateMutation` — `handleTest`/`handleRotate` async fns → `useMutation`;`isPending` 取代 `testing`/`rotating` useState(刪 2 個 useState);`onSuccess` setDetail from result(test → `last_test_status`/`last_test_detail`;rotate → `last_rotated_at`/`secret_masked_preview`)— 取消原 in-onSuccess `getConnection` refetch(result payload 已含 fresh fields)
- **F3.4** Error surfacing — `patchMutation.isError` → inline `oklch(var(--destructive))` text(`patchMutation.error?.message ?? 'Update failed'`);per-field zod errors `errors.display_name`/`errors.endpoint_url` 紅字 hint
- **F3.5** Verify gates — `tsc --noEmit` **REAL exit 0**、`next lint` **✔ No ESLint warnings or errors**、`Grep '\[oklch'` across `app`+`components`+`lib` = **0**、`settings-6tab.test.tsx` **9/9 pass**(regression-clean)
- **ServiceCard `endpoint` prop dropped** — F3 唔再傳 `endpoint` 俾 ServiceCard(原本顯示 read-only endpoint strip);endpoint 而家由 edit form 擁有(editable)— 避免 endpoint 顯示兩次 redundancy,更貼 mockup「endpoint 喺 expanded body editable」

### Decisions

- **D3.1 — Optimistic UI fork = local-state(非 useQuery cache 轉換)** — `ProviderRow.detail` 係 component-local `useState`(一張展開卡嘅 lazy-fetched config),唔係 cross-component shared data。`useMutation` 嘅 `onMutate`/`onError`/`onSuccess` callback 直接操作 local `setDetail` 就可以做 optimistic + rollback;`queryClient.setQueryData` 只喺 data 住喺 query cache(`useQuery`)時先需要。轉 useQuery 要連帶重寫 ProviderRow 嘅 lazy「Load configuration」button interaction = scope creep per Karpathy §1.3 surgical。plan §3 Gate criterion 4「useMutation + onMutate/onError rollback」— local-state 完全 satisfy(criterion 冇 mandate query cache)。F5 Identity 亦會跟同一 local-state pattern(`config` useState)— Wave C2 settings cluster 內部一致。
- **D3.2 — `ConnectionEdit` narrower type** — `ProviderPatch.display_name` 係 `string|null`(backend PATCH 容許 omit),但 `ProviderConfig.display_name` 係 `string`(stored config 必有)。`{...detail,...patch}` optimistic merge 用 `ProviderPatch` 會 widen display_name 至 `string|null` → tsc reject。Fix:`ConnectionEdit = {endpoint_url: string|null; region: string|null; display_name: string}` — form 永遠送 concrete display_name(`.min(1)` zod 已 enforce non-empty),narrower type assignable to `ProviderPatch` for `updateConnection` call。
- **D3.3 — test/rotate `onSuccess` 唔再 refetch** — 原 Wave C1 `handleTest`/`handleRotate` 喺 await 後再 `getConnection` refetch「so the badge updates」。`testConnection` 返 `{status,latency_ms,detail}`、`rotateSecret` 返 `{last_rotated_at,secret_masked_preview}` — 兩個 result payload 已含需要更新嘅 fields,`onSuccess` 直接 `setDetail` partial merge 即可,慳一個 round-trip。
- **D3.4 — 預判 test breakage 證實多餘** — F3 加 `useMutation` 入 ProviderRow,本以為會 break `settings-6tab.test.tsx`(該 test 冇 QueryClientProvider wrapper)。但實測 9/9 pass:test mock `listConnections` 返 `[]` → `grouped` 空 → **ProviderRow 完全唔 mount** → `useMutation` 永遠唔 reach。**唔加 wrapper**(Karpathy §1.2 — 唔加唔需要嘅嘢)。F7 若加實 data render test 先需要 wrapper。
- **D3.5 — ServiceCard `endpoint` prop 唔再傳** — 避免 endpoint read-only strip + edit form 兩處顯示;endpoint 由 edit form 擁有。region 仍傳 ServiceCard(collapsed header summary)+ edit form 亦有(editable)— 同 mockup「header desc summary + body editable input」一致。

### Acceptance(plan §3 + checklist F3)

- [x] F3.1 ProviderRow inline edit form(useForm + zodResolver + values sync)
- [x] F3.2 patchMutation local-state optimistic(onMutate/onError/onSuccess)
- [x] F3.3 testMutation + rotateMutation retrofit(isPending,刪 2 useState)
- [x] F3.4 error surfacing(isError text + per-field zod errors)
- [x] F3.5 tsc REAL exit 0 + lint clean + [oklch=0 + settings-6tab 9/9

**Day 1 cont F3 Verdict**:F3 complete — Connections inline edit 完整 unit(form + zod + 3 optimistic useMutation),absorbs F2.6 deferred wire。Optimistic UI fork resolved = local-state per D3.1。F4 ErrorBoundary per tab next。Real-calendar:F3 ~0.4 day vs 1.0 plan estimate。

---

<!-- Day 1+ F4 entries land at F4 active flip per CLAUDE.md §10 R2 -->
