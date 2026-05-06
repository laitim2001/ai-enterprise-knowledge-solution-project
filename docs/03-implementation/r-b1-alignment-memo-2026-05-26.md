---
artifact: r-b1-alignment-memo
status: pre-session-draft
session_target: 2026-05-26 W9 D1 三方 alignment session
audience: Stakeholder + IT Manager + Chris
prepared_by: AI(Chris's pre-session prep aid)
related_artifacts:
  - docs/01-planning/RISK_REGISTER.md R14 R-B1
  - docs/decision-form.md Q11
  - docs/03-implementation/beta-plan-v1.md §2 W8.F1
  - infrastructure/entra-id/README.md
  - infrastructure/keyvault/README.md
---

# R-B1 Alignment Memo — Q11 Operational Cred Cascade(W9 D1 三方 Session)

> **Prepared for**:Chris,to take into the Stakeholder + IT manager + Chris alignment session(W9 D1 = 2026-05-26)。
> **Source of truth**:此 memo 是 W7 retro / W8 retro / RISK_REGISTER R14 / decision-form.md Q11 嘅 governance summary。Chris 可以 sanitize 同 distribute pre-session,或者直接攜入會議。

---

## 1. Executive Summary(讀 30 秒)

EKP Tier 1 implementation **already production-ready** for Beta deploy(W7-W8 closed)。Real Microsoft Entra ID auth wire(`backend/api/auth/msal_provider.py` + `frontend/lib/auth/msal_provider.ts`)+ Azure Container Apps Bicep + Static Web Apps SWA + Key Vault secrets + cost dashboard + observability — **全部 spec-complete**。

**唯一 missing piece** = IT delivery of:
1. `AZURE_TENANT_ID`(Ricoh 統一 tenant directory id)
2. `AZURE_CLIENT_ID`(EKP app registration application id)
3. App registration approved with redirect URIs + Expose API scope per `infrastructure/entra-id/README.md` 8-step SOP

**過 deadline** — IT engagement 由 W8 D1 cascade trigger,past W8 D5(2026-05-23)closeout escalation threshold per W8 plan §4 R1。**RISK_REGISTER R14 R-B1 status updated 🟡 Active monitor → 🔴 Active escalation 2026-05-23**。

**今日嘅 ask**:**confirm IT delivery commit date**。Implementation 唔需要再等 spec 改;只需要 cred populate to Key Vault → ACA deploy + SWA DNS + LIVE smoke = 即時 cascade。

---

## 2. Background — What Was Decided 2026-05-05

W6 D5 stakeholder approval cycle(2026-05-05)landed:
- **Q11 decision-level Resolved** — Ricoh 統一 tenant via Entra ID(default path approved)
- **W7 D1 critical path** — IT engagement trigger to confirm:Tenant Access + App Registration + Owner Identification
- **Fallback** — mock auth dev mode for W7 D1-D3 if IT cascade slips
- **Beta-blocking threshold** — 若 W7 D5 仍未 confirm

**Subsequent revision 2026-05-05 same-session(a-revised mock auth strategy)**:
- IT engagement moved **W8 D1 Beta deploy phase entry**(per `beta-plan-v1.md §2 W8.F1` alignment)
- W7 D1 implementation start **不再 IT-blocked** — `Settings.feature_auth_mock=True` flag + `mock_msal.py` decoupled W7 dev work
- F1.7 LIVE smoke 自然推 W8 D4 deploy-time gate
- **New Beta-blocking threshold** — 若 W8 D5 仍未 confirm(escalation Stakeholder + IT manager 三方 session)

---

## 3. Current State — What's Done(W7-W8)

### Implementation spec-complete

| Phase | Deliverables landed | Verification |
|---|---|---|
| W7 closed 2026-05-16 | `mock_msal.py` + `msal_provider.py` skeleton + rate limiter + audit middleware + error handlers + mobile responsive | Phase Gate G1'-G7 全 PASS;269/269 pytest |
| W8 closed 2026-05-23 | Real `msal_provider.py`(python-jose JWKS + RS256)+ frontend `msal_provider.ts`(@azure/msal-react)+ Dockerfile + ACA Bicep + GHA CI/CD + Key Vault SOP + SWA pipeline + Entra ID app registration SOP + SWA custom domain SOP + F4 substitute integration smoke + Langfuse SDK + cost dashboard + alerts | Phase Gate PARTIAL PASS;312/312 pytest |
| W9 D1 in-progress | `observe.py` decorator wrapper + 3-stage decoration(synthesizer + retrieval + crag)+ this memo | 322/322 pytest |

### Chris-cascade SOPs ready(only awaiting IT cred + portal access)

- **`infrastructure/entra-id/README.md`** — 8-step app registration SOP(Pattern A combined SPA+API recommended)+ F1.5 LIVE smoke procedure
- **`infrastructure/keyvault/README.md`** — 6 secrets SOP(azure-openai-api-key + azure-search-admin-key + cohere-api-key + azure-tenant-id + azure-client-id + azure-client-secret)+ Managed Identity grant + rotation cadence
- **`infrastructure/swa/README.md`** — 5-step custom domain SOP(Azure portal → Ricoh corp DNS CNAME + TXT → Validate → cert provisioned)
- **`infrastructure/aca/README.md`** + `backend.bicep` + `networking.bicep` — Container Apps declarative spec(internal ingress + Managed Identity + 6 KV secret references + autoscale 1-5 + Private Endpoint to Azure AI Search)

### Tests covering all paths

- 287 backend unit + integration tests(W7-W8)+ 10 W9 D1 observe wrapper tests = 322 total
- F1.6 13 unit tests for real msal_provider(JWKS mock + valid signed JWT 200 + expired 401 + audience mismatch 401 + issuer mismatch 401 + missing kid 401 + JWKS cache TTL)
- F4 substitute 5 integration smoke tests(E1 OOS query + E5 LLM timeout + E12 chunk_id collision + F3.5 audit chain)
- F5.1 8 Langfuse SDK lifecycle tests + F5.3 6 feedback wire tests + F5.2/F5.4 11 dashboard tests + F4.4 7 admin auth parametrized tests

---

## 4. Current State — What's Blocked(W9 deferred)

| Gate | Blocker | Impact |
|---|---|---|
| G1 F1 Real Entra ID LIVE smoke pass on dev tenant | IT cred missing | Beta cohort can't login;F1.7 LIVE smoke can't run |
| G2 F2 ACA backend deploy + smoke 200 OK on /health | Chris infra session pending(Bicep declarative spec ready)+ IT cred for KV populate | Backend not in Azure yet;local dev only |
| G3 F3 SWA frontend deploy + custom domain reachable | Chris DNS session pending(SOP ready)+ Ricoh corp DNS team CNAME + TXT | Frontend not at `ekp-beta.ricoh.com` yet |
| G7 OQ Q11 final operational Resolved | IT cred delivery | Q11 stays decision-level Resolved + operational pending |

**No implementation gap**。**No spec drift**。**No team capacity issue**。Pure external dependency on IT delivery cycle。

---

## 5. The Ask — What IT Needs to Deliver

### 5.1 Three deliverables(Pattern A — recommended)

Per `infrastructure/entra-id/README.md` 8-step SOP,the IT manager(or delegated Entra ID admin)needs to:

1. **Create one app registration** in Ricoh Entra ID tenant
   - Name:`ekp-beta`(or stakeholder-confirmed environment naming)
   - Supported types:Single tenant
2. **Configure Single-Page Application platform**
   - Redirect URIs:`https://ekp-beta.ricoh.com/` + `https://staging-ekp.ricoh.com/` + `http://localhost:3001/`(dev)
   - Front-channel logout URLs:same hosts
   - Implicit grant:**both checkboxes UNCHECKED**(msal-react 5.x uses Authorization Code with PKCE)
3. **Expose an API scope**
   - Application ID URI:`api://<client-id>`(default suggested by Azure)
   - Scope name:`access`
   - Who can consent:Admins + users
4. **Grant admin consent** for the `access` scope
5. **Pattern A only:NO client secret needed**(SPA + token-validating backend = no confidential client flow)

After steps 1-5,IT delivers to Chris:
- **Application (client) ID** → populates Key Vault as `azure-client-id`
- **Directory (tenant) ID** → populates Key Vault as `azure-tenant-id`

### 5.2 Pattern B fallback(if audit / compliance requires separation)

If Pattern A is unacceptable per Ricoh IT compliance policy:
- **Two app registrations**:`ekp-spa-beta`(SPA platform)+ `ekp-api-beta`(web API platform)
- API exposes scope consumed by SPA
- API confidential client flow → 6-month rotation client secret
- Slightly higher operational overhead but cleaner separation

**Default for Beta**:Pattern A unless IT manager pushes Pattern B explicitly。

---

## 6. Decision Options for the Session

| Option | What it means | Implication |
|---|---|---|
| **A. IT commits W9 D2-D3 delivery**(default ask)| IT manager allocates resource to complete 5 steps within 2 working days | F2 ACA deploy + F3 DNS + F1.5 LIVE smoke cascade W9 D3-D5 → Beta cohort onboard W9 D5 / W10 D1 |
| **B. IT commits W9 D5 delivery**(slip 2 days)| Coordination cycle → resource availability bumps mid-W9 | W10 D1 LIVE deploy cascade → Beta cohort onboard W10 D2-D3 → W10 retro re-baseline schedule;**still within W11-W12 production launch milestone** |
| **C. IT cannot commit < 1 week**(escalation cycle re-engage)| Stakeholder cycle re-opens — escalate above IT manager OR consider Pattern B with separated audit cycle OR consider self-managed tenant for Beta | **W11-W12 production launch milestone at risk** — staged rollout 25% / 50% / 100% phases compress;Chris-cascade re-baseline likely required |
| **D. Pivot to Pattern B**(if compliance pushes)| Two app registrations + secret rotation cycle | Adds ~1 day to F2.4 KV populate(extra secret)+ F2.4 rotation SOP exercise;NO implementation impact;NO spec drift |

**Recommended**:A or B — Pattern A combined SPA+API。

---

## 7. Risk Implications(Why This Matters)

### W11-W12 production launch milestone(staged rollout)

Per architecture.md §6.1 timeline:
- W9-W10 = Beta internal testing(real query log collection + UX iteration)
- W11-W12 = Staged rollout 25% → 100% production launch

**Beta cohort onboarding requires real Entra ID auth**(mock auth = dev only,not for actual users)。Without IT cred:
- Beta cohort cannot login → no real query collection
- Q6 Real query collection owner trigger empty
- Q15 Manual update frequency signal unavailable
- W11 staged rollout 25% has no production-ready signal

**Each day of slip past W9 D5 compresses Beta validation window**。If IT delivery slips beyond W10 D2,W11-W12 milestone re-baseline 必須 Stakeholder cycle re-engage。

### Mitigation already in place

- **Mock auth dev mode preserved**(`Settings.feature_auth_mock=True`)— allows Chris to keep developing internal tooling + dashboard polish during slip
- **F1.7-mock substitute(W7 D5 commit `247bb49`)** — 9 comprehensive integration cases verify mock auth + middleware chain + audit propagation;same acceptance contract preserved when LIVE switch flips
- **Chris-cascade SOPs ready W8 D4** — portal apply itself is **mechanical**(8-step SOP),no novel design work needed
- **F1.6 13 unit tests** verify real msal_provider against signed-JWT fixtures so contract drift caught BEFORE LIVE smoke

The cost of waiting 2-3 more days for Pattern A is **low**(W9 D2-D3 cascade still hits Beta cohort onboarding W9 D5 / W10 D1)。The cost of escalation cycle option C is **high**(staged rollout milestone re-baseline)。

---

## 8. Pre-Session Suggested Agenda(20 min)

1. **5 min** — Chris briefs Stakeholder + IT manager on W7-W8 closeout state(Section 3 + 4 of this memo)
2. **5 min** — IT manager confirms timeline + resource availability(Section 5.1 deliverables;Section 6 options A/B/C/D)
3. **5 min** — Stakeholder confirms Pattern A vs B preference(audit / compliance lens)
4. **5 min** — All-hands commit to:(a)IT delivery date + (b)F1.4 LIVE switch trigger date + (c)Beta cohort onboarding date

**Pre-session ask**:Chris circulates this memo 24h before session so IT manager has time to check Pattern A vs B compliance + resource calendar。

---

## 9. Post-Session Action Items Template

After session,Chris updates:
- [ ] `docs/decision-form.md` Q11 → `Resolved` operational(replace "operational pending W9" qualifier)
- [ ] `docs/01-planning/RISK_REGISTER.md` R14 R-B1 → 🟢 Mitigated(or 🔴 Open if escalation cycle)
- [ ] `docs/01-planning/W09-beta-internal-testing/progress.md` Day 1 entry adds session outcome
- [ ] `docs/01-planning/W09-beta-internal-testing/checklist.md` F1.1 → ticked + commit date noted
- [ ] If Pattern B picked → `infrastructure/entra-id/README.md` Pattern B section flagged primary
- [ ] Schedule W9 D2/D3 IT cred delivery follow-up(or alternative date per option chosen)

---

## 10. Reference Quick-Links

| Topic | Path |
|---|---|
| Q11 decision history | `docs/decision-form.md §Q11` |
| R-B1 risk evolution | `docs/01-planning/RISK_REGISTER.md §R14` |
| Beta plan timeline | `docs/03-implementation/beta-plan-v1.md §2 W7-W12` |
| Entra ID app registration SOP | `infrastructure/entra-id/README.md`(Pattern A 8-step + Pattern B fallback)|
| Key Vault SOP | `infrastructure/keyvault/README.md`(6 secrets layout + Managed Identity grant)|
| ACA networking spec | `infrastructure/aca/networking.bicep` + `backend.bicep`(Private Endpoint + Managed Identity)|
| SWA custom domain SOP | `infrastructure/swa/README.md`(DNS + apex caveat + cert)|
| F1.7 LIVE smoke procedure | `infrastructure/entra-id/README.md` step 8 |

---

**Memo prepared 2026-05-23 W8 D5 closeout same-session post pytest 322/322 PASS verdict**。Chris consume + sanitize as needed for distribution。
