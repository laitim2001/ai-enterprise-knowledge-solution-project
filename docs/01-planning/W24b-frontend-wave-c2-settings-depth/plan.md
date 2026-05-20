---
phase: W24b-frontend-wave-c2-settings-depth
name: "Settings depth — form validation + optimistic UI + ErrorBoundary + Identity inline edit + Audit log filter/pagination (Wave C2 promote items per ADR-0026)"
sprint_week: W24b
start_date: 2026-05-20              # real-calendar — Chris directive 2026-05-20 「kickoff(plan + checklist + progress + commit F0 cascade)」
end_date: 2026-05-24                # ~3-5 plan day window;real-calendar collapse ~0.5-1 days per W22-W24 pattern(C09 frontend mid scope + 1 NEW dep)
status: active
spec_refs:
  - CLAUDE.md §10 R1-R6             # rolling JIT + plan-before-code + R6 pre-active-flip recursive (plan-text grep audit)
  - CLAUDE.md §5.2 H2               # react-hook-form + zod NEW deps (npm registry, low R8 risk per ADR-0017)
  - CLAUDE.md §5.7 H7               # mockup-fidelity preserved during inline-edit promotion
  - CLAUDE.md §13 surgical          # extend Wave C1 components, no page-level rewrite
  - ADR-0026                        # Wave C1 ship read-mostly → Wave C2 promotes inline-edit per §Consequences
  - ADR-0017                        # R8 mitigation pattern (react-hook-form + zod npm-registry; low risk per W17 F6 precedent)
  - ADR-0027                        # Power User Tier 2 boundary preserved during roles list-replace edit
prior_phase: W24-frontend-wave-c1   # closed 2026-05-19 PASS WITH WAVE-C2-PROMOTE-DEFERS CAVEAT
related_artifacts:
  - docs/adr/0026-settings-6-tab-hub-and-connections-backend.md  # primary ADR — Wave C2 promote
  - docs/adr/0017-r8-corp-proxy-mitigation-pattern.md             # R8 dep-add discipline
  - references/design-mockups/ekp-page-settings-tabs.jsx          # canonical visual spec
  - frontend/components/settings/                                 # 4 components touch (Connections + Identity + ApiKeys + AuditLog)
  - frontend/components/error/error-boundary.tsx                  # 85 lines existing class component
  - frontend/lib/api/admin.ts                                     # 264 lines existing — extend with audit-log filter params
  - backend/api/routes/admin/audit_log.py                         # 36 lines existing — extend with filter + pagination params (additive)
---

# Phase W24b — Settings depth (Wave C2 promote items) Plan

> **Authorization**:Chris explicit directive 2026-05-20 「**kickoff(plan + checklist + progress + commit F0 cascade)**」 after W24b-wave-b-observability pivoted to Wave C2 per pre-active-flip R6 audit finding(W22 F7 已 rebuild 3 observability routes — original wave-b scope substantially landed,redundant)。
>
> **R6 audit lean-scope decision**:
> - **EXCLUDE** Connections deployment cap edit(Wave B+ Azure portal authoritative)
> - **EXCLUDE** Real-MSAL feature flag verification(W16 Track A IT cred parallel track,Q11 operational pending)
> - **INCLUDE** form validation + optimistic UI + ErrorBoundary + Identity inline edit + Audit log filter/pagination(Wave C1 read-mostly → Wave C2 editable depth promotion)
>
> Wave C2 = **Beta-operator self-service milestone**:Settings 6-tab Hub 由 read-mostly 提升至 inline editable,configure operations 唔再需 `.env` rotation rituals 或 Azure Portal trips。

---

## §0 Phase identity

**Trigger**:W24-wave-c1 closeout 2026-05-19 Wave C2 promote items + Chris kickoff directive 2026-05-20 + R6 pre-active-flip audit lean-scope per inventory drift finding。

**Decision authority**:Chris W19 F6 ADR-0026 Accepted Option B(fully editable;Wave C1 ship structural / Wave C2 promote depth)+ R6 audit 2026-05-20 pivot to Wave C2 over wave-b-observability redundant rebuild。

**Scope**:
- F0 Kickoff cascade(plan + checklist + progress)
- F1 react-hook-form + zod install + H2 ADR-0017 mitigation(npm registry,low R8 risk per W17 F6 precedent)
- F2 Zod schema per Wave C1 sub-resource + form validation wire(Identity tenant + app_reg + msal + roles + policy + ApiKeys alert_threshold + Connections endpoint_url/region)
- F3 Optimistic UI per PATCH(TanStack `useMutation` retrofit + rollback on error;current Wave C1 用 `useState + try/catch` pessimistic)
- F4 ErrorBoundary per tab(wrap 4 settings/* components via existing `frontend/components/error/error-boundary.tsx`)
- F5 Identity inline edit activation(remove 8 處 `readOnly` props + wire 5 PATCH mutations + Power User Tier 2 boundary preserved per ADR-0027 fallback)
- F6 Audit log filter + pagination(backend `audit_log.py` 加 `action_type` + `since` + `cursor`/`offset` query params additive;UI 加 filter dropdown + pagination controls)
- F7 Tests(Vitest form validation cases + Playwright optimistic UI + ErrorBoundary fallback + visual baseline re-capture)
- F8 Closeout cascade(retro + Gate verdict + session-start sync + ADR-0026 Implementation Status amendment for Wave C2)

**Out of scope**:
- Connections deployment cap edit(Wave B+ Azure portal authoritative;ADR-0026 §Consequences Wave B+ note)
- Real-MSAL feature flag verification(W16 Track A IT cred parallel track;Q11 operational early June 2026)
- ADR-0027 Option A `/users` Tier 1.5 RBAC(separate W24c+ wave,~20 backend days + 6 NEW Postgres tables + Entra Graph SDK)
- ADR-0025 Access tab activation(依賴 W24c RBAC backend)
- New backend endpoints beyond F6 audit log filter param additions(additive only — no new routes)
- Tier 2 expansion(Power User role activation / Density toggle / Distributed token cache)

**Authorities**:
- **CLAUDE.md §10 R1-R6** — rolling JIT + plan-before-code + R6 pre-active-flip 5-step recursive grep audit(plan-text + code-at-active-flip)
- **CLAUDE.md §5.2 H2** — react-hook-form + zod NEW deps(npm registry,low R8 risk per W17 F6 + Vitest precedent;ADR-0017 amendment row added at F1 if Plan B (a) PyPI/npm direct fails)
- **CLAUDE.md §5.7 H7** — mockup-fidelity preserved per H7 self-verify(inline-edit promotion 唔可以改 mockup visual;只 unlock 既有 disabled inputs)
- **CLAUDE.md §13 surgical** — Wave C1 components extend not rewrite(Karpathy §1.3)
- **ADR-0026** Status `Accepted + Wave C1 implemented` → Wave C2 closeout amend to `Accepted + Wave C1+C2 implemented`

---

## §1 Authorization + spec refs

| F-deliverable | Authorization | Spec ref |
|---|---|---|
| F0 Kickoff | this plan + Chris kickoff directive 2026-05-20 | CLAUDE.md §10 R1 + R5 + §1 + ADR-0026 §References |
| F1 react-hook-form + zod install | CLAUDE.md §5.2 H2 + ADR-0017 mitigation pattern | `frontend/package.json` add `react-hook-form@^7` + `zod@^3` + `@hookform/resolvers@^3` |
| F2 Zod schemas + form validation | ADR-0026 §Decision Option B inline-edit | `frontend/lib/schemas/admin/` NEW + Wave C1 components wire `useForm` + `zodResolver` |
| F3 Optimistic UI per PATCH | ADR-0026 §Decision Option B UX + W20 F3 TanStack precedent | `useMutation` retrofit per 4 settings/* + `onMutate` optimistic + `onError` rollback |
| F4 ErrorBoundary per tab | W14 CO_F4_error_boundary carry-over + W24-c1 F6.5 promote | wrap 4 settings/* in `<ErrorBoundary fallback={<TabErrorState />}>` |
| F5 Identity inline edit | ADR-0026 §Decision Option B + ADR-0027 Power User boundary | `settings-identity.tsx` 8 處 `readOnly` removal + 5 PATCH mutation wire |
| F6 Audit log filter + pagination | ADR-0026 §Consequences Wave C2 expansion | `backend/api/routes/admin/audit_log.py` additive params + `settings-audit-log.tsx` filter UI |
| F7 Tests | CLAUDE.md §5.6 H6 + W23 Playwright pattern | Vitest form validation cases + Playwright optimistic UI E2E + visual baseline re-capture |
| F8 Closeout | CLAUDE.md §10 R3 + W19-W24 closeout pattern | retro + Gate criteria + ADR-0026 Implementation Status section amendment(Wave C1+C2) |

---

## §2 F0-F8 deliverables

**Rolling JIT discipline**:F0 + F1 detailed at kickoff;F2-F8 sketched;detail refines per-deliverable at kickoff per W12-W24 pattern。Per CLAUDE.md §10 R6 — pre-active-flip 5-step grep audit applied **recursively** to plan-text **and** code-at-active-flip-time。

### F0 — Kickoff cascade(landed at phase open — `(this commit)`)

- **Component(s)**:governance(no Cn touched at F0)
- **Spec ref**:CLAUDE.md §10 R1 + this plan §0
- **OQ deps**:none
- **Acceptance criteria**:
  - F0.1 W24b folder `plan.md`(this file)+ `checklist.md` + `progress.md` created `status: active` 2026-05-20
  - F0.2 NO `frontend/` or `backend/` code change at kickoff(per W19-W24 F0 precedent — F0 governance only)
  - F0.3 NO `architecture.md v6` amendment(Wave C2 is depth promotion within ADR-0026 既存 spec — no Cn structural change;same precedent as ADR-0026 Wave C1 shipped within `architecture.md v6 §5.0` 6-tab amendment landed at W24-wave-c1 F0)
  - F0.4 Pre-active-flip 5-step grep audit recursive(per R6)已 completed at kickoff prep(documented in `progress.md` Day 0 entry + plan §7 changelog):
    - Wave C1 components 4 個 confirmed `frontend/components/settings/{connections,identity,api-keys,audit-log}.tsx` 全部 exist
    - `frontend/components/error/error-boundary.tsx` 85 lines exists
    - `@tanstack/react-query@5.59.0` installed in `package.json` line 31
    - `react-hook-form` + `zod` + `@hookform/resolvers` NOT installed → F1 H2 trigger
    - `settings-identity.tsx` 8 處 `readOnly` confirmed line 96/106/115/163/190/256/265/274
    - `audit_log.py` backend 36 lines `limit` param only — no filter / since / cursor
  - F0.5 W24b kickoff cascade committed `(this commit)`
- **Effort estimate**:0.25 day(this commit)

### F1 — react-hook-form + zod install(H2 ADR-0017 mitigation)

- **Component(s)**:**C12** DevOps & Infra(npm dep install)+ **C09** Admin Console UI(dep usage)
- **Spec ref**:
  - CLAUDE.md §5.2 H2 NEW dep
  - ADR-0017 §Decision-rule #5 Plan B sequencing(react-hook-form + zod 屬 npm registry,Plan B (a) `pnpm add` 直接 attempt — Langfuse/Playwright/Azure SDK 屬 binary CDN 嚴重 R8 不同)
  - W17 F6 Vitest + RTL `pnpm add -D` `@testing-library/*` 成功 precedent(non-binary npm-registry deps R8 通常 OK)
- **OQ deps**:none
- **Acceptance criteria**:
  - F1.1 `pnpm add react-hook-form@^7 zod@^3 @hookform/resolvers@^3` 透過 IT-managed pnpm registry(無需 Plan B (c) mobile hotspot — npm-registry metadata 通常 R8 通過)
  - F1.2 若 F1.1 fails per R8 → ADR-0017 amendment occurrence #9 + retry via Plan B (c) mobile hotspot(precedent ready per Langfuse 2026-05-16 + Azure Key Vault 2026-05-19)
  - F1.3 `package.json` + `pnpm-lock.yaml` 確認 3 new deps landed;`tsc --noEmit` exit 0(types available)
  - F1.4 `frontend/lib/schemas/admin/` folder NEW(zod schema collection root)
  - F1.5 Sanity test:`frontend/tests/unit/lib-schemas-admin.test.ts` NEW — verify zod schema parse + validate path for 1 sample schema(e.g. `EntraTenantConfigSchema`);Vitest pass
- **Effort estimate**:0.5 day(0.25 install + 0.25 sanity test)

### F2 — Zod schemas + form validation wire

- **Component(s)**:**C09** Admin Console UI(form validation layer)
- **Spec ref**:
  - F1 deps available
  - `backend/api/schemas/admin*.py` Pydantic models = canonical shape(F2 mirror with zod)
  - W20 F4 5-step wizard react-hook-form + zod precedent(若有,grep verify at F2 active-flip)
- **OQ deps**:none
- **Acceptance criteria**:
  - F2.1 `frontend/lib/schemas/admin/identity.ts` NEW — 5 zod schemas(`EntraTenantConfigSchema` + `AppRegistrationConfigSchema` + `MsalConfigSchema` + `RoleMappingConfigSchema` + `SignInPolicyConfigSchema`)mirror backend Pydantic Literals + constraints
  - F2.2 `frontend/lib/schemas/admin/api_keys.ts` NEW — `AlertThresholdSchema`(50-95 range)
  - F2.3 `frontend/lib/schemas/admin/connections.ts` NEW — `ProviderPatchSchema`(endpoint_url URL validation + region string + display_name string)
  - F2.4 `settings-identity.tsx` wire `useForm({resolver: zodResolver(EntraTenantConfigSchema)})` per 5 sub-resource card(only activate when F5 inline-edit lands;F2 ship schemas + structural wire only,inline-edit final activation 入 F5)
  - F2.5 `settings-api-keys.tsx` `OutgoingQuotaRowItem` 既有 alert_threshold inline edit 升級 to react-hook-form zod-validated input(replaces existing `useState + onChange`)
  - F2.6 `settings-connections.tsx` ProviderRow expand panel `useForm` for endpoint_url + region + display_name(F2 ship form scaffold + zod validation;PATCH mutation wire 入 F3 optimistic UI deliverable)
  - F2.7 `tsc --noEmit` exit 0 + `next lint` clean + `Grep '\[oklch'` across `frontend/` = 0 preserved
- **Effort estimate**:1 day(0.5 schemas + 0.5 wire across 3 components)

### F3 — Optimistic UI per PATCH(TanStack useMutation retrofit)

- **Component(s)**:**C09** Admin Console UI(mutation layer)
- **Spec ref**:
  - W20 F3 advanced surfaces TanStack precedent
  - ADR-0026 §Decision Option B UX(snappy edit experience for Beta operator)
- **OQ deps**:none
- **Acceptance criteria**:
  - F3.1 4 settings/* components retrofit:replace `useState + try/await/catch` pessimistic with `useMutation({ onMutate, onError, onSuccess })`
  - F3.2 `onMutate` optimistic cache update via `queryClient.setQueryData(['admin','identity'], updater)`
  - F3.3 `onError` rollback via cached snapshot + inline banner-destructive error display(不彈 toast — 保留 Wave C1 inline banner pattern per Karpathy §1.3 surgical)
  - F3.4 `onSuccess` invalidate cache via `queryClient.invalidateQueries(['admin','identity'])`
  - F3.5 `tsc --noEmit` exit 0 + `next lint` clean
- **Effort estimate**:1 day

### F4 — ErrorBoundary per tab

- **Component(s)**:**C09** Admin Console UI(error layer)
- **Spec ref**:
  - W14 CO_F4_error_boundary carry-over
  - W24-c1 F6.5 promote
  - `frontend/components/error/error-boundary.tsx` 85 lines existing class component
- **OQ deps**:none
- **Acceptance criteria**:
  - F4.1 `frontend/components/settings/tab-error-state.tsx` NEW — `<TabErrorState tabName>` fallback UI(banner-destructive + retry button)
  - F4.2 `frontend/app/(app)/settings/page.tsx` wrap each tab content in `<ErrorBoundary fallback={<TabErrorState tabName={...} />}>` — 6 wrap points(Profile / Appearance / Connections / Identity / ApiKeys / Account)
  - F4.3 Verify ErrorBoundary catches React render errors per existing class component contract(throw test in dev → fallback renders)
  - F4.4 `tsc --noEmit` exit 0 + `next lint` clean
- **Effort estimate**:0.5 day

### F5 — Identity inline edit activation

- **Component(s)**:**C09** Admin Console UI(`settings-identity.tsx` inline edit)+ **C11** Identity & Access(consumer surface)
- **Spec ref**:
  - ADR-0026 §Decision Option B inline-edit
  - ADR-0027 Option B fallback(Power User Tier 2 boundary preserved — 422 reject if `power_user` ekp_role with `is_tier2_disabled=false`)
  - F2 zod schemas available
  - F3 useMutation available
  - mockup `ekp-page-settings-tabs.jsx:528-723 SettingsIdentity` inline-edit affordance
- **OQ deps**:Q11 operational(non-blocking — mock-auth default Wave C2 unchanged per W18+ pattern)
- **Acceptance criteria**:
  - F5.1 `settings-identity.tsx` 8 處 `readOnly` props 移除(line 96/106/115/163/190/256/265/274 per R6 audit)
  - F5.2 5 sub-resource card 各 wire 一個 Save 按鈕 + dirty-state detection(react-hook-form `formState.isDirty`)
  - F5.3 Save click → useMutation triggers PATCH endpoint(F3 deliverable already covers mutation pattern)→ optimistic update(F3)→ 422 boundary error(Power User / multi_disabled / distributed_disabled)inline banner-destructive
  - F5.4 client-supplied `authority_url` field disabled-display preserved(server-side derived per F3 backend `_derive_authority_url` — read-only 唔屬 inline-edit promote)
  - F5.5 RoleMappingConfig list-replace semantic preserved(individual mapping CRUD defer Wave C+,per W24-c1 F3 D3.1 deviation)
  - F5.6 H7 per-tab fidelity verify — inline-edit affordance match mockup line 528-723 visual(input/select unlock 唔可以改 visual structure)
  - F5.7 `tsc --noEmit` exit 0 + `next lint` clean
- **Effort estimate**:1 day

### F6 — Audit log filter + pagination

- **Component(s)**:**C08** API Gateway(`audit_log.py` additive expansion)+ **C09** Admin Console UI(filter UI)
- **Spec ref**:
  - ADR-0026 §Consequences Wave C2 expansion
  - `backend/api/routes/admin/audit_log.py` 36 lines existing
  - `backend/storage/audit_log_storage.py` Protocol(F2/F3/F4 audit row writes — Wave C1 write-only)
  - mockup `ekp-page-settings-tabs.jsx` SettingsAccount audit log surface(若有 filter affordance — grep verify at F6 active-flip)
- **OQ deps**:none
- **Acceptance criteria**:
  - F6.1 `backend/storage/audit_log_storage.py` `AuditLogBackend.list_recent` Protocol extended with `action_type: str | None = None` + `since: datetime | None = None` + `cursor: int | None = None`(SERIAL `id` PK cursor;backward-compat default None)
  - F6.2 InMemory + Postgres impl 各 implement filter logic(InMemory list comprehension + Postgres `WHERE action_type = %s AND created_at >= %s AND id < %s ORDER BY id DESC LIMIT %s`)
  - F6.3 `audit_log.py` `GET /admin/audit-log` add query params `action_type` + `since` + `cursor` + `limit`(既有);response shape extends with `next_cursor: int | None`(pagination signal)
  - F6.4 `apiClient.admin.listAuditLog` extended signature `(opts: {limit?, action_type?, since?, cursor?})` + response `{entries, next_cursor}`
  - F6.5 `settings-audit-log.tsx` 加 filter dropdown(action_type select)+ since picker(simple date input)+ "Load more" cursor pagination button
  - F6.6 Tests:`backend/tests/api/admin/test_audit_log.py` 加 filter + pagination 6+ NEW cases;`frontend/tests/unit/settings-audit-log.test.tsx` NEW or 加 filter interaction case
  - F6.7 mypy strict backend + tsc/lint frontend clean
- **Effort estimate**:1 day

### F7 — Tests(Vitest + Playwright)

- **Component(s)**:**C09** Admin Console UI(test layer)
- **Spec ref**:
  - CLAUDE.md §5.6 H6 test coverage
  - W23 F2 Playwright render-smoke pattern(3-state OR for data-dependent)
  - W22 F8.7 Vitest pattern(per-component)
- **OQ deps**:none
- **Acceptance criteria**:
  - F7.1 `frontend/tests/unit/settings-identity-form.test.tsx` NEW — react-hook-form + zod tenant card validation(invalid tenant_id format triggers error;valid value clears error);3+ cases
  - F7.2 `frontend/tests/unit/settings-audit-log-filter.test.tsx` NEW or extend — action_type filter select + cursor pagination interaction;3+ cases
  - F7.3 `frontend/tests/e2e/app-shell-path.spec.ts` `/settings?tab=identity` 加 dirty-state Save button visible-after-edit render-smoke
  - F7.4 `frontend/tests/e2e/visual-baseline.spec.ts` `/settings?tab=identity` baseline re-capture(post-inline-edit visual change → mask `.mono` + run `pnpm test:e2e:update-snapshots`)
  - F7.5 Vitest stats `pnpm exec vitest run tests/unit/` ≥ ~10 pass(W24-wave-c1 baseline 9 settings-6tab + F7.1+F7.2 NEW ~6 = ~15 settings-area pass)
  - F7.6 Playwright stats `PW_CHANNEL=chrome pnpm exec playwright test` ≥ 24/24 pass(W24-wave-c1 baseline 22+2 → 24 preserved + F7.3 expanded inline)
  - F7.7 Backend pytest preserved:W24-wave-c1 baseline 805 + F6 filter/pagination ~6 NEW = ~811 pass
- **Effort estimate**:0.75 day

### F8 — Closeout cascade

- **Component(s)**:governance(no Cn touched)
- **Spec ref**:CLAUDE.md §10 R3 + W19-W24 closeout pattern
- **OQ deps**:none
- **Acceptance criteria**:
  - F8.1 Phase Gate verdict published per `progress.md` retro
  - F8.2 7-section retro per F-deliverable(What worked / friction / Surprises / Decisions / Carry-overs / Time tracking / Spec-ref alignment)
  - F8.3 plan/checklist/progress frontmatter `active → closed`
  - F8.4 W24c+ candidates noted in retro **NOT pre-created** per CLAUDE.md §10 R1 rolling JIT
  - F8.5 `session-start.md` 6 places synced(§3 C08+C09+C11 W24b status notes + §10 W24b row closed + §11 NEW W24b CLOSED block + §12 milestones W24b row + 累計 23 → 24 phase closed + Last Updated + Update history row)
  - F8.6 `COMPONENT_CATALOG.md` C08 + C09 + C11 W24b status amendments
  - F8.7 `PAGE_INVENTORY.md` `/settings` row status amendment Wave C1+C2 hybrid(編 row 已 fully implemented W24-c1 F5,加 Wave C2 amendment row hint)
  - F8.8 `ADR-0026 Implementation Status` section amendment(Wave C1 implemented → **Wave C1+C2 implemented**)
  - F8.9 PAGE_INVENTORY.md row 8/9/10 staleness drift fix(W22 F7 已 rebuild observability cluster,inventory row update — Karpathy §1.3 surgical adjacent docs fix)
- **Effort estimate**:0.5 day

---

## §3 Success criteria + Gate criteria

Phase Gate **PASS** requires:

1. **All F0-F8 `[x]` complete**(~50+ atomic items)
2. **3 NEW frontend deps landed**:react-hook-form + zod + @hookform/resolvers(via Plan B (a) pnpm OR Plan B (c) mobile hotspot fallback)
3. **Form validation working**:Identity 5 sub-resource cards + Connections endpoint_url/region/display_name + ApiKeys alert_threshold 全部 zod-validated
4. **Optimistic UI working**:4 settings/* components 用 useMutation + onMutate/onError rollback pattern(no `useState + try/catch` pessimistic)
5. **ErrorBoundary working**:6 wrap points + `<TabErrorState>` fallback render verified
6. **Identity inline edit working**:8 處 `readOnly` removed + 5 PATCH mutations + 422 Tier 2 boundary inline banner
7. **Audit log filter + pagination working**:`action_type` + `since` + `cursor` backend params + filter UI + Load more
8. **H7 fidelity preserved**:inline-edit affordance 唔改 mockup visual structure(unlock-only,not redesign)
9. **No backend regression**:pytest 805 pre-W24b → +6 audit-log filter tests = ~811 pass
10. **Verify gates all green**:`tsc --noEmit` exit 0 + `next lint` clean + `Grep '\[oklch'` = 0 preserved + `mypy --strict backend/storage/audit_log_storage.py backend/api/routes/admin/audit_log.py` clean

**PARTIAL PASS allowance**:
- F1.1 `pnpm add` direct fail → Plan B (c) mobile hotspot fallback per ADR-0017(precedent ready;若 hotspot 都 fail → PARTIAL PASS + F1 defer next sprint + F2-F5 fallback to `useState + manual zod parse` non-RHF wire)
- F6 filter/pagination 若 backend pagination scope explodes → ship `action_type` only at Wave C2,`since` + `cursor` defer Wave C3(scope cut documented in plan §7 changelog)

---

## §4 Risks

| Risk | Mitigation | Status |
|---|---|---|
| **R-W24b-1** react-hook-form + zod R8 install fail | Plan B (c) mobile hotspot fallback ready;ADR-0017 amendment row #9 if used(precedent Langfuse + Azure Key Vault SDK)| 🟡 active |
| **R-W24b-2** Optimistic UI cache invalidation race | TanStack Query default invalidate-on-success pattern + W20 F3 chat-history precedent;若 cache race surfaces → fallback to pessimistic with cache refresh on success | 🟢 mitigated |
| **R-W24b-3** Identity 5 PATCH bulk activate cascading errors | F5 ship per-card Save not全-tab Save(card-level transaction granularity;1 card error 唔 affect others) | 🟢 mitigated |
| **R-W24b-4** F6 pagination cursor design wrong | `id` SERIAL DESC cursor 屬 standard pattern(W24-c1 `audit_log_postgres.py:ORDER BY id DESC` 已用);verified at F6 active-flip | 🟢 mitigated |
| **R-W24b-5** H7 fidelity drift during inline-edit | Per-tab visual diff comparison vs mockup(unlock-only semantic — input/select pre/post visually identical except focus state);per-tab user-eye self-verify F5.6 + F2.x | 🟡 active |
| **R8 corp-proxy** | Plan B (a) attempt + Plan B (c) hotspot fallback per ADR-0017 | 🟢 mitigated |

---

## §5 Component-Catalog references

| Cn | Touch | Scope |
|---|---|---|
| **C08** API Gateway | `audit_log.py` additive expansion | F6 backend `action_type` + `since` + `cursor` query params + `next_cursor` response field |
| **C09** Admin Console UI | 4 settings/* + page.tsx + NEW schemas + tab-error-state | F2 zod schemas + F3 useMutation retrofit + F4 ErrorBoundary wraps + F5 Identity inline-edit + F6 audit-log filter UI |
| **C11** Identity & Access | consumer surface | F5 Identity inline-edit activation(no new endpoints — Wave C1 5 PATCH endpoints already shipped W24-wave-c1 F3) |
| **C12** DevOps & Infra | NEW frontend deps | F1 react-hook-form + zod + @hookform/resolvers install |
| **C01-C07** / **C10** / **C13** | _no touch_ | preserved unchanged |

---

## §6 Carry-overs to W24c+ / rolling JIT

- **W24c+ candidates**(per W24b retro):
  - ADR-0027 Option A `/users` Tier 1.5 RBAC full(~20 backend days + 6 NEW Postgres tables + Entra Graph SDK + ACL middleware + audit_log writes)
  - ADR-0025 Access tab activation(`kb_acl` table + per-KB ACL CRUD;依賴 ADR-0027 RBAC backend)
  - Connections deployment cap edit(Wave B+ Azure portal authoritative;non-Wave-Cn stream)
  - Real-MSAL feature flag verification + Track A IT cred consumption(W16 parallel track,Q11 operational early June 2026)
  - F6 filter/pagination 若 scope cut to `action_type` only at Wave C2 → `since` + `cursor` carry forward W24c
- **W24c+ NOT pre-created** per CLAUDE.md §10 R1 rolling JIT
- **CO17 R8 umbrella** — F1.5b psycopg + F3.5b RAGAs live-verify 仍 external-blocked

---

## §7 Changelog

| Day | Change | Reason |
|---|---|---|
| Day 0 2026-05-20 | Plan kickoff cascade — frontmatter / §0-§7 全部 landed `status: active` + Chris kickoff directive + Wave C2 pivot from W24b-wave-b-observability per R6 audit finding(W22 F7 已 rebuild 3 observability routes;original wave-b scope redundant)| per CLAUDE.md §10 R1 + R6 + ADR-0026 §Consequences Wave C2 promote |
| Day 1 2026-05-20 | **F1 pre-active-flip 5-step grep audit recursive** surfaced **2 plan-text deviations**(per CLAUDE.md §10 R6):**(1)** F1.4 plan-text「`frontend/lib/schemas/admin/` folder NEW」→ 空 folder 對 git 無意義(空目錄唔被 tracked)→ **Adjust** — folder 延後至 **F2.1** 首個真 schema `identity.ts` 落地時自然 materialize(Karpathy §1.2 avoid-busywork — 唔為滿足「folder NEW」字面去整 throwaway file);**(2)** F1.5 plan-text test 檔名「`lib-schemas-admin.test.ts`」→ F1.4 folder 既然延後,test 唔再 import 該 folder → **Adjust** rename 為 `zod-toolchain.test.ts`(toolchain-level sanity 更準確反映 test 內容 — 驗證 zod + react-hook-form + @hookform/resolvers 3-dep 整合,inline `sampleSchema` mirror 2 real Wave C1 constraint)。**F1.1 Plan B (a) `pnpm add` clean install zero R8** — npm-registry metadata non-binary per W17 F6 Vitest precedent confirmed;**no ADR-0017 amendment needed**(Plan B fallback 未觸發)| Karpathy §1.1 think-before-coding surfaced upfront;F1 ship 3 deps + 1 sanity test(4/4 pass);tsc exit 0 |
| Day 1 cont 2026-05-20 | **F5 active-flip — role-card scope clarification**(per CLAUDE.md §10 R6):**(1)** 讀 mockup `ekp-page-settings-tabs.jsx:650-690 SettingsIdentity` role card 發現 role 編輯 affordance = per-row「⋯」(IcMore)menu + header「Add mapping」按鈕 = individual mapping CRUD → plan F5.5 明文 defer Wave C+ → **Adjust** F5.2「5 cards Save」→ **4 editable cards**(Tenant / App Registration / MSAL / Sign-in Policy);`<RoleMappingCard>` 保持 W24-c1 read-only display;**(2)** mockup scopes = plain `badge badge-muted`(無 × / Add)→ scopes display-only,唔 editable(只 redirect_uris + allowed_email_domains 係 editable list);**(3)** Identity cards 係 form-based(全卡係表單)→ optimistic「onMutate cache write + onError rollback」唔 apply — rollback 會棄用戶 edits;正確 pattern = form 持 edits、`onSuccess reset(saved)` re-baseline、`onError` 保留 form + 顯示 error(D5.2);**(4)** redirect_uris / allowed_email_domains primitive `string[]` list → 用 RHF `watch` + `setValue(...,{shouldDirty:true})` 而非 `useFieldArray`(primitive array useFieldArray 要 `{value}` object wrapper + form-specific type juggling — `watch`/`setValue` 更 surgical,單一 isDirty / submit source);**(5)** 預判 F5 令 Identity tab `useMutation` 會 break `settings-6tab.test.tsx`(缺 QueryClientProvider)→ 實測證實(2 identity test fail)→ 加 `renderSettings()` QueryClientProvider wrapper helper(F5 自己 breakage 自己清,per Karpathy §1.3)| Karpathy §1.1 think-before-coding;F5 ship `settings-identity.tsx` 完整 rewrite(4 form cards + role display card)+ `identity.ts` 加 4 inferred type exports;tsc REAL exit 0 + lint clean + `[oklch`=0 + settings-6tab 9/9 |
| Day 1 cont 2026-05-20 | **F4 active-flip — F0-audit correction**(per CLAUDE.md §10 R6):**(1)** F0 pre-active-flip audit 寫「`error-boundary.tsx` 85-line class component」→ 實際讀檔發現只 export `ErrorBoundaryView`(presentational error card,畀 Next `error.tsx` route convention 用),**冇 React `componentDidCatch` class** → React error boundary 必須係 class(冇 hook 版本)→ **Adjust** F4.2 = 創建真 `ErrorBoundary` class 加入 `error-boundary.tsx`(first-party code,非 new dep,**無 H2**);**(2)** F4.2 plan-text `fallback={<TabErrorState tabName={...}/>}` ReactNode form → retry button 要 reset boundary 需要攞 `reset` callback → **Adjust** `fallback: (reset) => ReactNode` render-prop form;`settings/page.tsx` 加 `TabBoundary` local helper DRY 6-wrap;**(3)** F4.3 plan「dev throw test」→ **Adjust** 為 `error-boundary.test.tsx` 3-test 自動化 verification(healthy passthrough / fallback-on-throw / reset-recovers)— 更紮實;**(4)** tooling — `npx tsc` 攞咗 npm decoy package `tsc@2.0.4`(非 TypeScript compiler)→ 改用 `pnpm exec tsc`(local binary,F5-F8 沿用)| Karpathy §1.1 think-before-coding;F4 ship `ErrorBoundary` class + `<TabErrorState>` + `TabBoundary` helper + 6-tab wrap + 3-test suite;tsc REAL exit 0 + lint clean + `[oklch`=0 + settings-6tab 9/9 |
| Day 1 cont 2026-05-20 | **F3 active-flip — fork resolved + 1 tsc type-fix**(per CLAUDE.md §10 R6):**(1)** plan §2 F3 acceptance criteria 寫嘅係 aspect-sliced「4 components retrofit」+「`queryClient.setQueryData`」+「`invalidateQueries`」→ 經 F2 R6 reshape(aspect→feature slice)後 F3 = Connections inline edit complete unit;**Adjust** F3 acceptance 重寫為 feature-slice(F3.1 inline edit form / F3.2 optimistic patch / F3.3 test+rotate retrofit / F3.4 error surfacing / F3.5 verify);**(2)** **optimistic UI fork resolved = local-state**(D3.1)— `ProviderRow.detail` 係 component-local `useState`,`useMutation` 嘅 `onMutate`/`onError` callback 直接操作 `setDetail` 即可,`queryClient.setQueryData` 只喺 data 喺 query cache 時需要;轉 useQuery 要重寫 lazy-fetch「Load configuration」interaction = scope creep per Karpathy §1.3;**(3)** tsc 發現 `{...detail,...patch}` 將 `display_name` widen 至 `string\|null`(因 `ProviderPatch.display_name` nullable)≠ `ProviderConfig.display_name: string` → **Adjust** 加 narrower `ConnectionEdit` type(form 永遠送 concrete display_name);**(4)** 預判 F3 useMutation 會 break `settings-6tab.test.tsx`(冇 QueryClientProvider wrapper)→ 實測證實多餘 — empty `listConnections` mock 令 ProviderRow 唔 mount,useMutation 永遠唔 reach,test 9/9 仍 green,**唔加 wrapper** | Karpathy §1.1 think-before-coding + §1.3 surgical;F3 ship Connections inline edit(ProviderRow + form + zod + 3 useMutation)；tsc REAL exit 0 + lint clean + `[oklch`=0 |
| Day 1 cont 2026-05-20 | **F2 pre-active-flip 5-step grep audit recursive** surfaced **3 plan-deliverable-boundary deviations + 1 pre-existing defect**(per CLAUDE.md §10 R6,讀 3 backend schemas + admin.ts + 3 components 後):**(1)** F2.4 plan-text「`settings-identity.tsx` wire useForm structural,activate 入 F5」→ component 全 `readOnly`(8 處),wire useForm 入 readOnly inputs = inert code,F5 再 remove-readOnly = 2-pass → **Adjust** — F2.4 整個 useForm wire **defer F5**(F5 一個 surgical pass 做 remove-readOnly + form + zod + mutation);**(2)** F2.6 plan-text「`settings-connections.tsx` form scaffold,PATCH wire 入 F3」→ ProviderRow 完全冇 edit form,form scaffold 冇 mutation = 死表單 → **Adjust** — F2.6 整個 form wire **defer F3**(F3 一個 pass 做 form + zod + mutation);F2 改為 aspect-slice→feature-slice — F2 ship pure validation layer(3 zod schemas)+ ApiKeys 既有 edit 硬化(唯一 coherent component work — component 本身已有 alert-threshold edit),總 scope 不變;**(3)** plan §2 F2 無 schema unit test item → **Add F2.8** `admin-schemas.test.ts`(16 tests — H6-class hygiene for pure validation layer);**(4)** 量度 tsc 時發現 `tests/unit/settings-6tab.test.tsx:138` `beforeEach` 漏 import(W24-c1 F7 `1a3784c` latent defect,該 phase「tsc exit 0」用咗 broken `tsc | tail` pipe 量度)→ **獨立 Trivial-class `fix(frontend):` commit `d10bf2c`** 修正(per PROCESS.md §1 typo-class,non-W24b-scope,F2 commit 之前 land 令 F2 tsc-clean gate 誠實)| Karpathy §1.1 think-before-coding + §1.3 surgical(coherent intermediate state per F-deliverable)surfaced upfront;F2 ship 3 zod schema files + ApiKeys RHF+zod upgrade + 16-test schema suite;tsc REAL exit 0(正確量度法)+ lint clean + `[oklch`=0 |
| Day 1 cont 2026-05-20 | **F6 pre-active-flip 5-step grep audit recursive** surfaced **2 plan-text path/scope deviations + 4 implementation forks**(per CLAUDE.md §10 R6,讀 `audit_log_storage.py` + `audit_log_postgres.py` + `audit_log.py` route + `audit_log.py` schema + `test_admin_audit_log.py` + `test_audit_log.py` + `admin.ts` + `settings-audit-log.tsx` + mockup `SettingsAccount` 842-870):**(1)** F6.6 plan-text test path「`backend/tests/api/admin/test_audit_log.py`」→ 該 `admin/` 子目錄不存在,實際 endpoint test = flat `backend/tests/api/test_admin_audit_log.py`(6 existing tests)→ **Adjust** — extend 既有 flat file,另加 storage-layer filter tests 入 `backend/tests/storage/test_audit_log.py`(Protocol change F6.1/F6.2 應有 storage 覆蓋);**(2)** F6.3「response 加 `next_cursor`」係 **breaking shape change** — 現 endpoint `response_model=list[AuditLogEntry]` bare list,加 `next_cursor` → 必須轉 wrapper object `{entries, next_cursor}` 經 NEW `AuditLogPage` schema;plan F6.6「6+ NEW cases」遺漏咗 **3 existing endpoint tests**(`returns_empty_list` / `returns_newest_first` / `respects_limit`)+ `settings-6tab.test.tsx` mock(line 132)+ `settings-audit-log.tsx` consumer 全部要 update 新 shape → **Adjust F6.6** 包含 existing-test + mock 改寫;**(3)** `since` tz fork — HTML date input 出 `YYYY-MM-DD` → FastAPI parse 為 naive datetime → 同 tz-aware `created_at` 比較會 `TypeError` → **endpoint 內 normalize** `since` 為 UTC-aware 先傳 backend;**(4)** `next_cursor` 計算 fork — `list_recent` return type 保持 `list[AuditLogEntry]`(plan F6.1 只 extend params,唔改 return)→ endpoint 請求 `limit+1` rows、`has_more = len > limit`、`next_cursor = page[-1].id`;**(5)** filter UI **無 mockup** — mockup `SettingsAccount` 842-870 只有 Session + Danger zone card,**完全無 audit log surface**(`<SettingsAuditLog>` 本身係 W24-c1 functional promote)→ F6 filter dropdown + since input + Load more 係 net-new functional UI;**非 H7 violation**(無 mockup element 可偏離;ADR-0026 §Consequences Wave C2 expansion sanction;W24-c1 component header + endpoint docstring 明文 pre-commit「Wave C2 adds filter + pagination」)→ 用既有 CSS-first primitive(`.select` / `.input` / `.btn`)保持 Settings cluster 視覺一致;**(6)** frontend pattern = local-state extend — `settings-audit-log.tsx` 現用 `useEffect + useState`(無 TanStack)→ 跟 Wave C2 settings-cluster local-state 一致(D3.1/D3.4/D5),extend useEffect/useState 加 filter state + loadMore append handler,轉 `useInfiniteQuery` = scope creep per Karpathy §1.3 | Karpathy §1.1 think-before-coding + §1.3 surgical;F6 ship Protocol + 2 impl filter/cursor + AuditLogPage schema + endpoint 3 params + apiClient opts signature + filter UI + ~13 NEW/rewritten tests;mypy strict + tsc/lint clean |

| Day 1 cont 2026-05-20 | **F7 pre-active-flip 5-step grep audit recursive** surfaced **3 plan-text deviations + 2 precedent-bound defers**(per CLAUDE.md §10 R6,讀 `settings-identity.tsx` + `identity.ts` schema + `app-shell-path.spec.ts` + `visual-baseline.spec.ts` + F6-created `settings-audit-log.test.tsx`):**(1)** F7.2 plan-text 描述「`settings-audit-log-filter.test.tsx` NEW or extend — action_type filter + cursor pagination interaction,3+ cases」→ **F6.6 已交付** `settings-audit-log.test.tsx`(3 cases:mount render / filter re-fetch / Load more append)= F7.2 描述內容 → **Adjust** — F7.2 = **extend** F6 嗰個 file(plan-text 檔名 `-filter` suffix 同 F6 實際檔名唔同 → 用 F6 檔名,避免 near-duplicate)加 2 NEW(since date filter re-fetch + filtered empty-state),唔開新檔;**(2)** F7.3 plan-text「`app-shell-path.spec.ts` `/settings?tab=identity` 加 dirty-state render-smoke」→ 該 spec **已有** `/settings?tab=identity deep link selects Identity tab` test(line 225-235)→ **Adjust** — F7.3 = **extend** 既有 test 加 Save button render-smoke,唔加 duplicate test;**(3)** F7.4 plan-text「baseline **re-capture**」→ `visual-baseline.spec.ts` 只有 `settings-connections.png` baseline,**無 identity baseline** → 實際係 **first-capture** 非 re-capture → **Adjust** — F7.4 = 加 `Settings ?tab=identity` 新 test spec;**(4)** F7.4 + F7.6 — Playwright `PW_CHANNEL=chrome` run + pixel baseline PNG first-capture **需要 dev server + backend + system Chrome 同時起**,per W24-wave-c1 closeout precedent(「Playwright +2 NEW... user-deferred」+「visual baseline first-capture user-deferred per W20 F8.5 + W23 F2.3」)→ F7 ship spec **file** 改動(F7.3 extend + F7.4 NEW test),`PW_CHANNEL=chrome` **execution + PNG capture = user pre-Beta smoke**(同 W12-W24 carry-over pattern;F7.6「24/24 pass」唔自我宣稱);**(5)** F7.7 — F7 **全部 frontend test 改動,無 backend change** → backend pytest 維持 F6 的 **816 passed**,唔重跑 4.5-min suite(per Karpathy §1.2 avoid-busywork — zero backend delta 重跑 = busywork)| Karpathy §1.1 think-before-coding + §1.2 avoid-busywork;F7 ship `settings-identity-form.test.tsx` NEW(4 cases)+ `settings-audit-log.test.tsx` extend(+2)+ `app-shell-path.spec.ts` identity test extend + `visual-baseline.spec.ts` identity test NEW;Vitest verified;Playwright run + visual capture user-deferred |

---

**End of W24b-wave-c2 plan(version 1.0 kickoff)**
