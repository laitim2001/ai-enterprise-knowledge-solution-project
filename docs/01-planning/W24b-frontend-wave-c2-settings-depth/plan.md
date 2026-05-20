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

---

**End of W24b-wave-c2 plan(version 1.0 kickoff)**
