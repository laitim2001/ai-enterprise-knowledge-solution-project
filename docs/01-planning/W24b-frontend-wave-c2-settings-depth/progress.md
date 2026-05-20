---
phase: W24b-frontend-wave-c2-settings-depth
plan_ref: ./plan.md
checklist_ref: ./checklist.md
status: closed                      # active | closed — closed 2026-05-20 Gate PASS WITH SMOKE-USER-DEFERRED CAVEAT
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
| F4 | 0.5 | ~0.3 | -0.2 | ErrorBoundary class NEW(F0 audit 誤判)+ 6-tab wrap + 3-test suite |
| F5 | 1.0 | ~0.6 | -0.4 | settings-identity rewrite — 4 form cards;最大 deliverable |
| F6-F8 | _TBD per active flip_ | _TBD_ | _TBD_ | Rolling JIT per CLAUDE.md §10 R1 |

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

## Day 1 cont — 2026-05-20 — F4 ErrorBoundary per tab

### Done

- **F4 pre-active-flip 5-step grep audit recursive**(per CLAUDE.md §10 R6):
  - **(2) grep** — 讀 `components/error/error-boundary.tsx` 發現只 export `ErrorBoundaryView`(presentational error card,Tailwind-token style,畀 Next `error.tsx` route convention 用)— **冇 React class error boundary**;F0 audit「85-line class component」誤判
  - **(3) surface** — React error boundary 必須係 class component(`getDerivedStateFromError` / `componentDidCatch` — 冇 hook 版本)→ F4 必須創建真 `ErrorBoundary` class
  - **(4) document** — plan §7 Day 1 cont F4 row landed
  - **(5) adjust** — F4.2 acceptance = 創建 `ErrorBoundary` class(非「wrap existing」);`fallback` render-prop form;F4.3 = 自動化 test
- **F4.1** `frontend/components/settings/tab-error-state.tsx` NEW(48 lines)— `<TabErrorState tabName onRetry>` — CSS-first `.banner banner-destructive`(對齊 4 settings/* 既有 fetch-fail inline error)+ AlertTriangle + Retry button
- **F4.2** `ErrorBoundary` class 加入 `components/error/error-boundary.tsx`(~45 lines,append after `ErrorBoundaryView`)— `getDerivedStateFromError` 設 error state、`componentDidCatch` console.error、`reset` 清 error 令 children re-mount;`fallback: (reset) => ReactNode` render-prop;`settings/page.tsx` 加 `TabBoundary` local helper(`<ErrorBoundary fallback={(reset) => <TabErrorState onRetry={reset}/>}>`)+ 6 個 tab body 各 wrap(Profile / Appearance / Connections / Identity & Auth / API Keys & Quotas / Account)
- **F4.3** `frontend/tests/unit/error-boundary.test.tsx` NEW(78 lines / 3 tests)— healthy child passthrough / fallback-on-throw / reset re-mount recovers(controllable `MaybeBoom` + `console.error` spy silence);**3/3 pass in 32s**
- **F4.4** Verify gates — `pnpm exec tsc --noEmit` **REAL exit 0**、`next lint` **✔ No ESLint warnings or errors**、`Grep '\[oklch'`=0、`settings-6tab.test.tsx` **9/9 regression-clean**

### Decisions

- **D4.1 — `ErrorBoundary` class 加入 既有 `error-boundary.tsx`** — 該檔已有 `ErrorBoundaryView`(presentational fallback);`ErrorBoundary`(boundary class)係佢自然 sibling,同檔。React error boundary 只可以係 class component — 冇 hook 版本,亦唔需要 `react-error-boundary` new dep(H2 避免)。
- **D4.2 — `fallback` render-prop `(reset) => ReactNode`** — plan-text 寫 `fallback={<TabErrorState/>}` ReactNode form;但 `<TabErrorState>` 嘅 Retry button 要 reset boundary 就需要攞到 `reset` callback。render-prop form `(reset) => <TabErrorState onRetry={reset}/>` 先做到 retry wire。`reset()` 清 error state → children re-mount → 失敗嘅 fetch 重跑(transient error 可復原)。
- **D4.3 — `TabBoundary` local helper** — 6 個 tab 各 wrap 同一 `<ErrorBoundary fallback={(reset)=>...}>` pattern;`TabBoundary({tabName, children})` local helper DRY 6 call sites(用 6× → 非 single-use,Karpathy §1.2 abstraction 合理)。
- **D4.4 — F4.3 自動化 test 取代「dev throw test」** — plan F4.3 寫「dev throw test → fallback renders」係非正式 manual verify;`error-boundary.test.tsx` 3-test(passthrough / catch / reset-recover)係更紮實 + repeatable 嘅 verification,亦 feed F7 test count。
- **D4.5 — `npx tsc` decoy package 教訓** — `npx tsc` 喺 npx cache miss 時會去 fetch npm 上嘅 decoy package `tsc@2.0.4`(故意提示「This is not the tsc command you are looking for」),非 TypeScript compiler。正解 = `pnpm exec tsc`(只行 local `node_modules/.bin`,永不 fetch)。F5-F8 tsc verify 一律 `pnpm exec tsc`。
- **D4.6 — Bash cwd 飄移** — Bash tool cwd 喺 call 之間唔穩定(時 root 時 frontend);F5+ 一律用 absolute path `cd "C:/...一/frontend"` 確保。

### Acceptance(plan §3 + checklist F4)

- [x] F4.1 tab-error-state.tsx NEW(CSS-first banner-destructive)
- [x] F4.2 ErrorBoundary class NEW + TabBoundary helper + 6-tab wrap
- [x] F4.3 error-boundary.test.tsx 3/3 pass
- [x] F4.4 tsc REAL exit 0 + lint clean + [oklch=0 + settings-6tab 9/9

**Day 1 cont F4 Verdict**:F4 complete — `ErrorBoundary` class(F0 audit 誤判已 R6-corrected)+ `<TabErrorState>` CSS-first fallback + `TabBoundary` helper + 6-tab wrap;一個壞 tab 退化成可復原 error state,其餘 5 個照常。F5 Identity inline edit activation next。Real-calendar:F4 ~0.3 day vs 0.5 plan estimate。

---

## Day 1 cont — 2026-05-20 — F5 Identity inline edit activation(最大 deliverable)

### Done

- **F5 pre-active-flip 5-step grep audit recursive**(per CLAUDE.md §10 R6):
  - **(2) grep** — 讀 mockup `ekp-page-settings-tabs.jsx:528-723 SettingsIdentity`:role card 編輯 = per-row「⋯」menu + 「Add mapping」按鈕(individual CRUD)/ scopes = plain `badge badge-muted` 無 ×/Add(display-only)/ redirect_uris + allowed_email_domains = editable list with X + Add;`QueryProvider` confirmed `(app)/layout.tsx`(F3 audit)
  - **(3) surface** — role 編輯 = individual CRUD → plan F5.5 defer Wave C+ → F5 = 4 editable cards;scopes display-only;Identity cards form-based → optimistic pattern ≠ Connections
  - **(5) adjust** — F5 acceptance F5.1-F5.7 重寫 per 4-card reality;plan §7 Day 1 cont F5 row landed
- **F5.0** `lib/schemas/admin/identity.ts` 加 4 inferred type exports(`EntraTenantInput` / `AppRegistrationInput` / `MsalInput` / `SignInPolicyInput`)— `useForm<T>` generic 要 form type = `z.infer<schema>` 對齊 `zodResolver`
- **F5.1-F5.6** `settings-identity.tsx` 完整 rewrite(425 read-only → 559 行 / 4 form cards + 1 display card)：
  - `<TenantCard>` — tenant_id / tenant_domain(GUID + domain regex zod)/ cloud_instance select editable;authority_url `watch()` controlled read-only
  - `<AppRegistrationCard>` — client_id editable;redirect_uris editable list(`watch` + `setValue` add/remove + X button per row);scopes display badges;sign_in_audience select(multi_disabled `<option>` disabled);client_secret ApiKeyInput rotateDisabled(Wave C2)
  - `<MsalCard>` — token_cache_strategy select(distributed_disabled disabled)/ session_ttl / refresh / csrf(duration regex zod)editable;cookie_settings_preview `watch()` read-only div
  - `<RoleMappingCard>` — read-only display(W24-c1 role table 保留;individual CRUD defer Wave C+)
  - `<SignInPolicyCard>` — allowed_email_domains editable list / require_mfa_workspace_admin switch button / auto_disable_after_days switch+number;require_mfa_all_roles_tier2 DisabledAffordance
  - shared `<CardSaveRow>`(Save footer + mutation feedback)+ `<FieldError>`(zod error hint)helpers
  - 每 card `useMutation` patch endpoint + `onSuccess reset(saved)` re-baseline
- **F5.7** Verify gates — `pnpm exec tsc --noEmit` **REAL exit 0**(首 pass)、`next lint` **✔ No ESLint warnings or errors**、`Grep '\[oklch'`=0、`settings-6tab.test.tsx` **9/9**
- **settings-6tab.test.tsx QueryClientProvider wrapper** — F5 令 Identity tab(`getIdentity` mock 返完整 config → 4 form cards render → `useMutation`)需要 QueryClientProvider;預判 → 實測 2 identity test fail → 加 `renderSettings()` helper(`QueryClient` + `QueryClientProvider` wrap,pattern 對齊 `dashboard.test.tsx:77`)+ 9 處 `render(<SettingsPage/>)` → `renderSettings()`;**9/9 restored**

### Decisions

- **D5.1 — F5 = 4 editable cards 非 5**(role card display)— mockup role 編輯 affordance(per-row「⋯」menu + 「Add mapping」)= individual mapping CRUD,plan F5.5 明文 defer Wave C+;`<RoleMappingCard>` 保持 W24-c1 read-only display table。F5.2 plan-text「5 cards Save」R6-adjusted。
- **D5.2 — Identity cards form-based:onSuccess re-baseline,onError keep-and-show(非 onMutate rollback)** — Connections(F3)有獨立 `detail` display object → optimistic = onMutate setDetail / onError rollback。Identity cards 係**全卡表單**(所有 field 都係 form input)— form 本身就持住用戶 edits,冇獨立 display 要 optimistically update。save 失敗時 rollback 會**棄用戶輸入** = 壞 UX。正確 pattern:`useMutation` + `onSuccess reset(saved)` re-baseline(form 顯示 saved values + clean)+ `onError` 保留 form dirty + `<CardSaveRow>` 顯示 error。plan §3 Gate criterion 4「onMutate/onError rollback」對 form-based card 應讀作此 pattern — F8 closeout reconcile。
- **D5.3 — primitive `string[]` list 用 `watch`+`setValue` 非 `useFieldArray`** — redirect_uris / allowed_email_domains 係 `string[]`;RHF `useFieldArray` 對 primitive array 要 `{value:string}[]` object wrapper + form-specific type + submit-time map-back。`watch('redirect_uris')` render + `setValue('redirect_uris', newArr, {shouldDirty:true})` add/remove + `register('redirect_uris.${i}')` — 單一 isDirty / 單一 submit source / form type = backend config type,更 surgical per Karpathy §1.3。
- **D5.4 — mutationFn 顯式構造 backend payload** — form type = `z.infer<schema>`(authority_url / secret fields optional),backend config type required → `mutationFn` 顯式列 `{...edited from data, ...passed-through from initial}`(e.g. TenantCard authority_url 送 `null` server re-derive;AppReg secret fields 由 `initial` pass-through)— 比 `??` coercion chain 清楚。
- **D5.5 — `<CardSaveRow>` Save footer 係 functional 必需** — mockup `SettingsIdentity` 係 static prototype,inputs 有 defaultValue 但無 Save 按鈕。「inline edit」per ADR-0026 Option B 需要 Save 機制 → 加 card footer Save button(同 F2 ApiKeys / F3 Connections 加 Save button 一致 precedent;mockup static-prototype 限制,非 H7 deviation)。
- **D5.6 — settings-6tab QueryClientProvider 預判正確** — F3 嗰陣預判 settings-6tab 會 break(Connections useMutation)but 證實多餘(empty mock 無 ProviderRow)。F5 同樣預判 → 今次**證實成立**(Identity `getIdentity` mock 返完整 config → 4 form cards mount → useMutation reach)→ 加 wrapper。差別:Connections empty-mockable / Identity 唔 empty-mockable(consolidated config GET)。

### Acceptance(plan §3 + checklist F5)

- [x] F5.1 settings-identity rewrite — 7 readOnly removed + 1 (authority_url) preserved
- [x] F5.2 4 form cards useForm + zodResolver + CardSaveRow
- [x] F5.3 useMutation PATCH + onSuccess reset + 422 boundary
- [x] F5.4 authority_url read-only watch-controlled
- [x] F5.5 RoleMappingCard display(list-replace / individual CRUD defer Wave C+)
- [x] F5.6 H7 4-card layout 對齊 mockup
- [x] F5.7 tsc REAL exit 0 + lint clean + [oklch=0 + settings-6tab 9/9

**Day 1 cont F5 Verdict**:F5 complete — `settings-identity.tsx` 由 read-only display 變 4 editable form cards(Tenant / App Registration / MSAL / Sign-in Policy)+ role card display;每 card useForm + zod + useMutation + Save。最大 deliverable done。F6 audit log filter + pagination next。Real-calendar:F5 ~0.6 day vs 1.0 plan estimate。

---

## Day 1 cont — 2026-05-20 — F6 Audit log filter + cursor pagination

### Done

- **F6 pre-active-flip 5-step grep audit recursive**(per CLAUDE.md §10 R6)— 讀 `audit_log_storage.py` + `audit_log_postgres.py` + `audit_log.py` route + `audit_log.py` schema + `test_admin_audit_log.py` + `test_audit_log.py`(storage)+ `admin.ts` + `settings-audit-log.tsx` + mockup `ekp-page-settings-tabs.jsx:842-870 SettingsAccount`:
  - **(2) grep** — endpoint test 實際 = flat `backend/tests/api/test_admin_audit_log.py`(6 tests);`backend/tests/api/admin/` 子目錄**不存在**;mockup `SettingsAccount` 只有 Session + Danger zone card,**完全無 audit log surface**(`<SettingsAuditLog>` 本身係 W24-c1 functional promote);`settings-audit-log.tsx` 現用 `useEffect + useState`(無 TanStack)
  - **(3) surface** — 6 處 deviation/fork(plan §7 Day 1 cont F6 row)
  - **(4) document** — plan §7 changelog F6 row landed
  - **(5) adjust** — checklist F6.1-F6.7 重寫 per reality;F6.6 test path 改 flat file + 加 storage cases
- **F6.1** `audit_log_storage.py` `AuditLogBackend.list_recent` Protocol 加 keyword-only `action_type: AuditAction | None` + `since: datetime | None` + `cursor: int | None`(default None — backward-compat;return type 保持 `list[AuditLogEntry]`)
- **F6.2** filter 實作 — `InMemoryAuditLogBackend.list_recent` in-pass filter loop(`limit` counts post-filter rows,`cursor` exclusive `id <` 上界);`PostgresAuditLogBackend.list_recent` `WHERE` 由 fixed column predicate set 砌,每個 user value `%s` placeholder(無 string interpolation — SQL-injection-safe)+ `ORDER BY id DESC LIMIT %s`
- **F6.3** NEW `AuditLogPage` schema(`entries: list[AuditLogEntry]` + `next_cursor: int | None`);`GET /admin/audit-log` 加 `action_type`(AuditAction Literal → 422 on unknown)+ `since`(datetime)+ `cursor`(ge=1)query params;`since` tz-naive → endpoint UTC-normalize;over-fetch `limit+1` rows → `has_more` → `next_cursor = page[-1].id`;`response_model` bare-list → `AuditLogPage`
- **F6.4** `apiClient.admin.listAuditLog` signature `(limit=10)` → `(opts: AuditLogQuery = {})` → `Promise<AuditLogPage>`;NEW `AuditLogPage` + `AuditLogQuery` interfaces;`URLSearchParams` query build
- **F6.5** `settings-audit-log.tsx` filter UI — action_type `.select`(6 options:All + 5 AuditAction)+ since `type="date"` `.input` + "Load more" `.btn` cursor button;local-state extend(`useEffect` fresh-fetch on filter change + `useCallback` loadMore append)per D3.1 Wave C2 settings-cluster pattern;CSS-first primitives(無 mockup — net-new functional UI per R6 finding)
- **F6.6** tests — `test_admin_audit_log.py` rewrite 3 existing for `AuditLogPage` wrapper shape + **7 NEW**(action_type filter / unknown-action 422 / since filter / next_cursor present / next_cursor none on last page / cursor walks older / cursor=0 422)= 13 endpoint tests;`test_audit_log.py`(storage)**4 NEW**(action_type / cursor / since backdated / combined)= 10 storage tests;`settings-audit-log.test.tsx` NEW 3(mount render / filter re-fetch / Load more append);`settings-6tab.test.tsx` mock line 132 `listAuditLog` → `{entries:[],next_cursor:null}`
- **F6.7** Verify gates — backend `pytest` **816 passed + 11 skipped + 0 failed**(W24-c1 baseline 805 → +11 net);mypy strict route+schema **clean** + `audit_log_storage.py` clean;`pnpm exec tsc --noEmit` **REAL exit 0** + `next lint` **✔ No ESLint warnings or errors** + `Grep '\[oklch'`=**0** + Vitest `settings-audit-log` **3/3** + `settings-6tab` **9/9 regression-clean**

### Decisions

- **D6.1 — F6.6 test path corrected** — plan-text「`backend/tests/api/admin/test_audit_log.py`」嘅 `admin/` 子目錄不存在;actual endpoint test = flat `backend/tests/api/test_admin_audit_log.py`。R6 adjust:extend 既有 flat file。另外 Protocol/impl change(F6.1/F6.2)應有 storage 覆蓋 → 加 4 cases 入 `backend/tests/storage/test_audit_log.py`(plan §2 F6.6 原只提 endpoint test)。
- **D6.2 — `next_cursor` = breaking shape change,bare-list → `AuditLogPage` wrapper** — 現 endpoint `response_model=list[AuditLogEntry]`;加 `next_cursor` 唯一乾淨做法 = wrapper object `{entries, next_cursor}`。plan F6.6「6+ NEW cases」遺漏咗 **3 existing endpoint tests**(`returns_empty` / `returns_newest_first` / `respects_limit` 全部 assert bare list)+ `settings-6tab.test.tsx` mock + `settings-audit-log.tsx` consumer 都要 update 新 shape。R6 adjust:F6.6 包含 existing-test + mock 改寫。內部 consumer only,無 external API contract — 直接轉 wrapper(per CLAUDE.md §13 backend wins on field shape)。
- **D6.3 — `since` UTC-normalize 喺 endpoint** — HTML `type="date"` input 出 `YYYY-MM-DD` → FastAPI/Pydantic parse 為 **tz-naive** datetime → 同 tz-aware `created_at`(`datetime.now(timezone.utc)`)比較會 raise `TypeError: can't compare offset-naive and offset-aware`。Fix:endpoint 收到 `since` 後 `if since.tzinfo is None: since = since.replace(tzinfo=timezone.utc)`,單一 funnel normalize,backend 收到永遠 tz-aware。
- **D6.4 — `next_cursor` 計算 = `limit+1` over-fetch,`list_recent` return type 不變** — plan F6.1 只 extend params,唔改 `list_recent` return(保持 `list[AuditLogEntry]`)。endpoint 請求 `limit+1` rows:`has_more = len(rows) > limit` → `page = rows[:limit]` → `next_cursor = page[-1].id if has_more else None`。`next_cursor` 邏輯留喺 endpoint,storage 純 query — 唔需要 storage 返 page object。
- **D6.5 — filter UI 無 mockup,net-new functional UI,非 H7 violation** — mockup `SettingsAccount` 842-870 只有 Session + Danger zone card,**完全無 audit log surface**。`<SettingsAuditLog>` 本身係 W24-c1 functional promote(component header + endpoint docstring 明文 pre-commit「Wave C2 adds filter + pagination」);F6 filter dropdown + since input + Load more 係**無 mockup element 可偏離**嘅 net-new functional UI → 非 H7 trigger(ADR-0026 §Consequences Wave C2 expansion sanction)。處理:用既有 CSS-first primitive(`.select` / `.input` / `.btn` / `.field` / `.label`)保持 Settings cluster 視覺一致,而非 redesign。
- **D6.6 — frontend pattern = local-state extend,非 `useInfiniteQuery`** — `settings-audit-log.tsx` 現用 `useEffect + useState`(無 TanStack),cursor pagination「Load more append」嘅 TanStack-idiomatic 做法係 `useInfiniteQuery`,但轉換要連帶引入 QueryClient 依賴 + 重寫整個 fetch path = scope creep per Karpathy §1.3。跟 Wave C2 settings-cluster local-state 一致(D3.1 / D3.4 / D5.6):extend `useEffect`(filter-change fresh fetch)+ `useState` accumulator + `useCallback` loadMore append handler。

### Acceptance(plan §3 + checklist F6)

- [x] F6.1 list_recent Protocol +action_type/since/cursor keyword-only
- [x] F6.2 InMemory in-pass filter + Postgres parameterized WHERE
- [x] F6.3 AuditLogPage schema + endpoint 3 params + since UTC-normalize + next_cursor
- [x] F6.4 listAuditLog (opts: AuditLogQuery) → Promise<AuditLogPage>
- [x] F6.5 filter select + since date input + Load more button(local-state)
- [x] F6.6 13 endpoint + 10 storage + 3 frontend tests + 6tab mock update
- [x] F6.7 pytest 816 + mypy clean + tsc 0 + lint clean + [oklch=0 + Vitest 12/12

**Day 1 cont F6 Verdict**:F6 complete — audit log 由 W24-c1 read-only last-10 table 提升至 `action_type` + `since` filter + cursor「Load more」pagination;backend Protocol/InMemory/Postgres + `AuditLogPage` wrapper + endpoint 3 additive params,frontend filter UI local-state extend。Breaking response shape change(bare-list → wrapper)consumer + 3 existing test + mock 全部 R6-surfaced 並 update。F7 tests(Vitest + Playwright)next。Real-calendar:F6 ~0.5 day vs 1.0 plan estimate。

---

## Day 1 cont — 2026-05-20 — F7 Tests(Vitest + Playwright)

### Done

- **F7 pre-active-flip 5-step grep audit recursive**(per CLAUDE.md §10 R6)— 讀 `settings-identity.tsx` + `identity.ts` schema + `app-shell-path.spec.ts` + `visual-baseline.spec.ts` + F6-created `settings-audit-log.test.tsx`:
  - **(2) grep** — F7.2 內容(action_type filter + cursor pagination)已由 F6.6 `settings-audit-log.test.tsx` 3 cases 交付;`app-shell-path.spec.ts` 已有 `/settings?tab=identity` test(line 225-235);`visual-baseline.spec.ts` 只有 `settings-connections.png` baseline,**無 identity baseline**
  - **(3) surface** — 3 plan-text deviations + 2 precedent-bound defers(plan §7 Day 1 cont F7 row)
  - **(4) document** — plan §7 changelog F7 row landed
  - **(5) adjust** — F7.2 = extend F6 file;F7.3 = extend 既有 test;F7.4 = first-capture(非 re-capture);Playwright run + capture user-deferred
- **F7.1** `frontend/tests/unit/settings-identity-form.test.tsx` NEW(4 cases)— render `<SettingsIdentity>`(mocked `adminApi`,`QueryClientProvider`),TenantCard RHF + `zodResolver(entraTenantConfigSchema)`:malformed `not-a-guid` submit → `findByText('Must be a valid GUID')` + `patchTenant` not called / 改 valid GUID → reValidateMode onChange → error 清 / malformed `tenant_domain`(`'bad domain!'`)submit → domain regex error / valid edit submit → `patchTenant` called with `authority_url:null`(v4-shaped GUID 兩個避開 zod `.uuid()` strict regex)
- **F7.2** `settings-audit-log.test.tsx` extend +2 NEW(F6 baseline 3 → **5 cases**)— since date input `fireEvent.change` → `listAuditLog` called with `since:'2026-05-01'` / action filter change at empty result → `findByText(/no audit entries match the current filter/i)`
- **F7.3** `app-shell-path.spec.ts` 既有 `/settings?tab=identity` test extend — `<CardSaveRow>` Save button render-smoke(`saveButton.or(banner).or(errorBanner)` 3-state OR per BUG-004 dev-cold-start tolerance);test 改名反映 F7.3 scope
- **F7.4** `visual-baseline.spec.ts` 加 `Settings ?tab=identity baseline` 新 test spec(`toHaveScreenshot('settings-identity.png')` + mask `.mono`);PNG first-capture user-deferred
- **F7.5** Vitest — settings-area 6-file deterministic batch **41/41 pass**(settings-6tab 9 + settings-audit-log 5 + settings-identity-form 4 + zod-toolchain 4 + admin-schemas 16 + error-boundary 3);`error-boundary.test.tsx` 嘅「transient boom」stack trace 係故意 throw 嘅 expected console noise(ErrorBoundary catch test)
- **F7.6** `app-shell-path.spec.ts` + `visual-baseline.spec.ts` spec 改動已 land + tsc/lint clean;**🚧 `PW_CHANNEL=chrome` execution + `settings-identity.png` PNG first-capture = user pre-Beta smoke**
- **F7.7** F7 無 backend change → backend pytest **816 preserved from F6**(唔重跑);`pnpm exec tsc --noEmit` **REAL exit 0** + `next lint` **✔ clean**

### Decisions

- **D7.1 — F7.2 = extend F6 file,非 duplicate `-filter` 新檔** — plan-text F7.2 描述「`settings-audit-log-filter.test.tsx` NEW or extend — action_type filter + cursor pagination,3+ cases」;但 F6.6 已交付 `settings-audit-log.test.tsx` 3 cases(mount / filter re-fetch / Load more)= F7.2 描述內容。開 `settings-audit-log-filter.test.tsx` 新檔 = near-duplicate filename + 分散同一 component 嘅 test。R6 adjust:extend F6 嗰個 file 加 since-filter + filtered-empty-state 2 cases(F6 唔 cover 嗰兩個 surface),總 5 cases。
- **D7.2 — F7.3 = extend 既有 test,Save button render-smoke OR-tolerant** — `app-shell-path.spec.ts` 已有 `/settings?tab=identity deep link selects Identity tab`(W23 F2 landed)。F7.3 唔加 duplicate test,extend 既有嗰個。Save button(`<CardSaveRow>`)render-smoke 用 `saveButton.or(banner).or(errorBanner)` 3-state OR — dev cold-start 時 backend 可能未 resolve,per BUG-004 render-smoke philosophy(loading / happy / graceful-error 任一)。strict「type input → Save button enables」interactive 流程屬 user pre-Beta smoke(同 BUG-004 `/traces/[traceId]` + `/kb/[id]` deep-interactive defer 一致)。
- **D7.3 — F7.4 = first-capture 非 re-capture** — plan-text 寫「baseline re-capture」,但 `visual-baseline.spec.ts` 只有 `settings-connections.png`,**冇 `settings-identity` baseline**(W24-c1 settings tab 係 read-only,冇 identity-specific baseline)。所以 F7.4 係 first-capture。加 `Settings ?tab=identity` 新 test spec;PNG 實際 capture user-deferred(per W24-c1「visual baseline first-capture user-deferred」+ W20 F8.5 + W23 F2.3 precedent)。
- **D7.4 — F7.6 Playwright execution user-deferred** — `PW_CHANNEL=chrome pnpm exec playwright test` 需要 frontend dev server + backend server + system Chrome 同時起(multi-process)。W24-wave-c1 closeout precedent 明確 defer Playwright run(「Playwright +2 NEW... user-deferred」)+ visual baseline first-capture。F7 ship spec **file** 改動(可 tsc/lint verify),execution 留 user pre-Beta smoke。F7.6「24/24 pass」唔自我宣稱 — 冇跑就唔 claim。標 🚧 + reason per CLAUDE.md sacred rule。
- **D7.5 — F7.7 唔重跑 backend pytest** — F7 全部 frontend test 檔改動(`settings-identity-form.test.tsx` / `settings-audit-log.test.tsx` / 2 e2e spec),**零 backend source 改動**。F6 已 verify backend pytest 816 passed。重跑 4.5-min suite 攞同一個 816 = busywork per Karpathy §1.2。F7.7 = 816 preserved from F6。
- **D7.6 — Vitest full-suite worker-pool timeout = OneDrive infra,非 regression** — `pnpm exec vitest run tests/unit/` 全 15 檔一齊跑會命中 `Failed to start threads worker` / `Timeout waiting for worker to respond`(OneDrive I/O contention,W23 D2 已 documented + setup.md §8.7 記錄)。可靠量度法 = 跑細 batch(settings-area 6 檔 → 41/41 deterministic pass)。full-suite 綠燈係 CI 嘅 concern(W23 retro:CI 應用 production build + 適當 pool config),非 W24b code regression。

### Acceptance(plan §3 + checklist F7)

- [x] F7.1 settings-identity-form.test.tsx NEW 4 cases
- [x] F7.2 settings-audit-log.test.tsx extend +2(3 → 5 cases)
- [x] F7.3 app-shell-path.spec.ts /settings?tab=identity test extend(Save button render-smoke)
- [x] F7.4 visual-baseline.spec.ts Settings ?tab=identity test spec NEW
- [x] F7.5 Vitest settings-area 41/41 deterministic batch
- [🚧] F7.6 spec landed;Playwright execution + PNG capture user-deferred per W24-c1 precedent
- [x] F7.7 backend pytest 816 preserved + tsc exit 0 + lint clean

**Day 1 cont F7 Verdict**:F7 complete — `settings-identity-form.test.tsx` NEW 4-case RHF+zod validation suite + `settings-audit-log.test.tsx` extend(3→5)+ 2 e2e spec 改動(`app-shell-path` identity test extend + `visual-baseline` identity test NEW)。Vitest settings-area 41/41 deterministic。Playwright execution + visual PNG capture 標 🚧 user pre-Beta smoke per W24-c1 precedent。F8 closeout cascade next。Real-calendar:F7 ~0.4 day vs 0.75 plan estimate。

---

## Day 1 cont — 2026-05-20 — F8 Closeout cascade

### Done

- **F8 pre-active-flip 5-step grep audit recursive**(per CLAUDE.md §10 R6)— 讀 `ADR-0026` + `COMPONENT_CATALOG.md` C08/C09/C11 + `PAGE_INVENTORY.md` table + `session-start.md` §3/§10/§11/§12:
  - **(3) surface** — 1 R6 finding:`PAGE_INVENTORY.md` **row 6 `/doc-detail` 亦 stale**(W22 F6 `093ff89` 已 land `/kb/[id]/docs/[docId]`,row 仍標「⏳ Wave B candidate (W21+)」)— 但 plan F8.9 + Chris kickoff 明確 scope「row 8/9/10」→ **唔擅自擴 scope**,row 6 surface 入下方 Carry-overs 留下一個 doc-sync 處理(per Karpathy §1.3 — 見到無關 stale → mention 唔 fix)
  - **(5) adjust** — F8.9 = rows 8/9/10 only(per stated scope);row 6 carry-over noted
- **F8.1** Phase Gate verdict **PASS WITH SMOKE-USER-DEFERRED CAVEAT**(下方 Retrospective)
- **F8.2** 7-section retro landed(下方)
- **F8.3** plan + checklist + progress frontmatter `active → closed`
- **F8.4** W24c+ candidates 入 Retrospective Carry-overs,**NOT pre-created** per CLAUDE.md §10 R1
- **F8.5** `session-start.md` 6 處 sync(§3 C08+C09+C11 W24b notes + §10 W24b row + §11 NEW W24b CLOSED block + §12 milestones row + 累計 23→24 + Update history)
- **F8.6** `COMPONENT_CATALOG.md` C08 + C09 + C11 W24b status amendments
- **F8.7** `PAGE_INVENTORY.md` row 11 `/settings` Wave C1+C2 amendment
- **F8.8** `ADR-0026` Status line + NEW Wave C2 Implementation Status section
- **F8.9** `PAGE_INVENTORY.md` rows 8/9/10 staleness fix(observability cluster W22 F7 rebuilt — Wave B candidate → Implemented W22 F7)

### Decisions

- **D8.1 — Phase Gate = PASS WITH SMOKE-USER-DEFERRED CAVEAT** — plan §3 全 10 criteria 滿足:3 NEW deps landed(F1)/ form validation(F2+F5)/ optimistic UI(F3 Connections local-state + F5 Identity form-based per D5.2 reconcile)/ ErrorBoundary(F4)/ Identity inline edit(F5)/ audit log filter+pagination(F6)/ H7 preserved / backend pytest 816 no regression / verify gates green。唯一 caveat:F7.6 Playwright `PW_CHANNEL=chrome` execution + `settings-identity.png` PNG first-capture = user pre-Beta smoke(spec file 改動已 land + tsc/lint verified)— 同 W18/W20/W24-c1 smoke-user-deferred pattern 一致。
- **D8.2 — plan §3 Gate criterion 4 reconcile(per D5.2 carry-over)** — criterion 4 寫「4 settings/* components 用 useMutation + onMutate/onError rollback」。實際:**Connections(F3)** = local-state optimistic(`onMutate` setDetail + `onError` rollback,fork D3.1);**Identity 4 cards(F5)** = form-based(`onSuccess reset(saved)` re-baseline + `onError` keep-edits,D5.2 — onMutate-rollback 對全卡表單會棄用戶輸入,壞 UX)。兩種都 satisfy「optimistic / snappy edit」intent;criterion 4 字面「rollback」對 form-based card 讀作「onError 保留 edits + 顯示 error」。reconciled,Gate criterion 4 PASS。
- **D8.3 — F8.9 scope = rows 8/9/10 only,row 6 surface 唔 fix** — R6 audit 發現 `PAGE_INVENTORY` row 6 `/doc-detail` 亦 W22-stale。plan F8.9 + Chris kickoff 明確 scope「8/9/10」。Karpathy §1.3 surgical + §13 when-in-doubt-stick-to-stated-scope → row 6 唔擅自 fix,入 Carry-overs flag 下一 doc-sync。

### Acceptance(plan §3 + checklist F8)

- [x] F8.1 Phase Gate verdict published
- [x] F8.2 7-section retro
- [x] F8.3 frontmatter active → closed
- [x] F8.4 W24c+ candidates NOT pre-created
- [x] F8.5 session-start.md 6 places synced
- [x] F8.6 COMPONENT_CATALOG.md C08+C09+C11
- [x] F8.7 PAGE_INVENTORY.md /settings row
- [x] F8.8 ADR-0026 Implementation Status Wave C1+C2
- [x] F8.9 PAGE_INVENTORY.md rows 8/9/10 staleness fix

**Day 1 cont F8 Verdict**:F8 complete — closeout cascade landed across `session-start.md` / `COMPONENT_CATALOG.md` / `PAGE_INVENTORY.md` / `ADR-0026` / 3 phase docs frontmatter。W24b-wave-c2 phase **CLOSED**。

---

## Retrospective — W24b-frontend-wave-c2-settings-depth

**Phase Gate verdict**:✅ **PASS WITH SMOKE-USER-DEFERRED CAVEAT**

Wave C2 promotes the Settings 6-tab Hub from W24-c1 read-mostly 到 inline-editable depth:form validation(react-hook-form + zod)+ optimistic UI + ErrorBoundary per tab + Identity 4-card inline edit + audit log filter/pagination。F0-F8 全部交付,F7.6 Playwright execution + visual PNG first-capture = user pre-Beta smoke(spec file 改動 + tsc/lint verified)。

### 1. What worked

- **Feature-slice 重組(D2.1)** — F2/F3/F5 原 plan 嘅 aspect-slice 切法(F2 wire structural / F5 activate)會令 component 經歷 inert 中間態。R6 audit 上 surface,改 feature-slice(F2=schemas,F3=Connections-edit-complete,F5=Identity-edit-complete),每個 component 一個 coherent pass — codebase 全程 shippable。
- **Pre-active-flip 5-step R6 audit 每 F-deliverable 都 catch 到嘢** — F1(2 plan-text deviation)/ F2(3 boundary + 1 pre-existing defect)/ F3(fork resolved)/ F4(F0-audit 誤判 class-vs-presentational)/ F5(role-card 4-vs-5)/ F6(test path + breaking shape)/ F7(F7.2 already-done + F7.3/F7.4 既有)/ F8(row 6 stale)。R6 recursive(plan-text + code)持續產出 value。
- **Karpathy §1.2 avoid-busywork 多次生效** — F1.4 空 folder 唔整 throwaway file;F7.7 唔重跑 zero-delta backend suite;F8.9 唔擴 scope 去 row 6。
- **Local-state optimistic pattern 內部一致** — F3 Connections + F5 Identity + F6 audit log 全部 local-state(`useState` + `useMutation`/`useEffect` callbacks),Wave C2 settings cluster 無引入 useQuery cache 轉換 — surgical。

### 2. Friction

- **Broken `tsc | tail` pipe exit-code(D2.6)** — `npx tsc | tail; echo $?` 攞 `tail` 嘅 exit 唔係 `tsc` 嘅;W24-c1 + F1/F2 第一次量度都中招。正解 `tsc > file 2>&1; echo $?`,F3-F8 沿用。
- **`npx tsc` decoy package(D4.5)** — `npx tsc` cache miss fetch npm decoy `tsc@2.0.4`;改 `pnpm exec tsc` local binary。
- **Vitest full-suite OneDrive worker-pool timeout(D7.6)** — 15 檔一齊跑命中 `Failed to start threads worker`;細 batch(settings-area 6 檔)係可靠 workaround,W23 setup.md §8.7 已 documented。
- **Bash cwd 飄移(D4.6)** — Bash tool cwd call 之間唔穩定;一律 absolute path `cd`。

### 3. Surprises

- **F2.4/F2.6 wire defer 而非 F2 做** — plan 原意 F2 wire useForm structural;實際 component 全 readOnly(Identity)/ 冇 form(Connections)→ wire 入去 = inert code。feature-slice 重組後 wire 各歸 F5/F3。
- **`error-boundary.tsx` 只 export presentational `ErrorBoundaryView`** — F0 audit 誤寫「85-line class component」;F4 active-flip 實讀發現冇 React error-boundary class → F4 創建真 class(first-party,無 H2)。
- **F6 `next_cursor` = breaking response shape** — bare-list → `AuditLogPage` wrapper;3 existing endpoint test + 6tab mock + consumer 全部要 update(R6 上 surface)。
- **F7.2 內容已由 F6.6 交付** — F6.6 `settings-audit-log.test.tsx` 3 cases = F7.2 描述;F7.2 改為 extend(+2)而非開 `-filter` duplicate 檔。
- **mockup `SettingsAccount` 完全無 audit log surface** — `<SettingsAuditLog>` 本身係 W24-c1 functional promote;F6 filter UI 係 net-new functional(非 H7 violation — 無 mockup element 可偏離)。

### 4. Decisions(完整清單見各 Day entry)

D2.1-D2.6(feature-slice / ApiKeys-keep / zod-strict / valueAsNumber / trivial-fix-commit / tsc-pipe)· D3.1-D3.5(local-state optimistic / ConnectionEdit type / no-refetch / test-breakage / ServiceCard endpoint)· D4.1-D4.6(ErrorBoundary class / render-prop / TabBoundary / auto-test / npx-decoy / cwd)· D5.1-D5.6(4-cards / onSuccess-rebaseline / watch-setValue / payload-construct / CardSaveRow / QueryClientProvider)· D6.1-D6.6(test path / breaking shape / since-tz / next_cursor / filter-no-mockup / local-state)· D7.1-D7.6(extend-F6-file / extend-existing-test / first-capture / Playwright-defer / no-backend-rerun / vitest-infra)· D8.1-D8.3(Gate verdict / criterion-4 reconcile / F8.9 scope)。

### 5. Carry-overs(→ W24c+,NOT pre-created per R1)

- **F7.6 Playwright execution + `settings-identity.png` PNG first-capture** — `PW_CHANNEL=chrome pnpm exec playwright test` 需 dev server + backend + system Chrome;= user pre-Beta smoke(同 W12-W24 smoke-deferred backlog roll forward)
- **PAGE_INVENTORY row 6 `/doc-detail` staleness**(NEW R6 finding,F8.9 stated scope 外)— W22 F6 `093ff89` 已 land `/kb/[id]/docs/[docId]`,row 仍標「⏳ Wave B candidate」→ 下一 doc-sync 修
- **ADR-0027 Option A `/users` Tier 1.5 RBAC**(~20 backend days + 6 NEW Postgres tables + Entra Graph SDK + ACL middleware)— W24c+ wave candidate
- **ADR-0025 `/kb/[id]` Access tab activation** — 依賴 ADR-0027 RBAC backend
- **Connections deployment cap edit**(TPM/RPM)— Wave B+ Azure portal authoritative
- **Real-MSAL feature flag verification + Track A IT cred consumption** — W16 parallel track,Q11 operational early June 2026
- **Connections / Identity secret rotation full wire** — F5 AppRegistration client_secret `ApiKeyInput` rotateDisabled「Wave C2 — rotation requires Entra Graph SDK」;真 rotation = Entra Graph SDK wave
- **CO17 R8 umbrella** — F1.5b psycopg + F3.5b RAGAs live-verify 仍 external-blocked

### 6. Time tracking

| F | Plan estimate | Real-calendar | Note |
|---|---|---|---|
| F0 | 0.25 day | ~0.2 day | kickoff cascade |
| F1 | 0.5 day | ~0.3 day | 3 deps clean install zero R8 |
| F2 | 1 day | ~0.4 day | feature-slice 重組,pure validation layer |
| F3 | 1 day | ~0.4 day | Connections inline edit + optimistic |
| F4 | 0.5 day | ~0.3 day | ErrorBoundary class |
| F5 | 1 day | ~0.6 day | 最大 deliverable — Identity 4-card rewrite |
| F6 | 1 day | ~0.5 day | audit log filter + cursor pagination |
| F7 | 0.75 day | ~0.4 day | tests |
| F8 | 0.5 day | ~0.4 day | closeout cascade |
| **總計** | **~6.5 plan-day** | **~3.5 real-calendar day** | ~1.9× collapse(W19 ~1.8× pattern;single-session 多-commit run)|

### 7. Spec-ref alignment

- **ADR-0026** Status `Accepted + Wave C1 implemented` → `Accepted + Wave C1+C2 implemented`(F8.8);Wave C2 promote items(form validation / optimistic UI / ErrorBoundary / Identity inline edit / audit log filter)全部 landed
- **CLAUDE.md §5.2 H2** — react-hook-form + zod + @hookform/resolvers 3 NEW deps:F1 Plan B (a) `pnpm add` clean,zero R8,**no ADR-0017 amendment needed**(npm-registry non-binary per W17 F6 precedent)
- **CLAUDE.md §5.7 H7** — F5 Identity 4-card 對齊 mockup line 542-721;F6 filter UI 無 mockup(net-new functional,非 H7 trigger per D6.5);無 fidelity drift
- **CLAUDE.md §10 R6** — pre-active-flip 5-step recursive audit 每 F-deliverable 執行,8 個 F 共 surface 14+ deviation/fork,全 log 入 plan §7 changelog
- **architecture.md v6** — 無 amendment(Wave C2 = depth promotion within ADR-0026 既存 6-tab spec,no Cn structural change — per F0.3)
- **CLAUDE.md §13** — Connections F3 `useMutation` mockup-vs-backend 無 contract 衝突;F6 audit log 無 OQ deps

**累計 phase**:**24 closed**(W01-W24-wave-c1 23 + W24b-wave-c2 1)。
