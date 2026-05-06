# Microsoft Entra ID app registration — F1.1 + F3.3 cascade SOP(W8 D4)

> Per W08-beta-deploy-sprint2 plan §2 F1.1 + F3.3 + components/C11-identity.md。
> **Owner**:Chris(IT engagement + portal apply)+ AI(SOP authoring)。
> **Status**:SOP only — actual portal apply lives in Chris IT session(F1.1 W8 D1+ trigger)。

## Overview

Beta authentication uses Microsoft Entra ID(architecture.md §6.1 W7)。EKP Tier 1 single-tenant pattern means one Entra ID tenant per environment(beta / staging / production)with one(or two — see §3)app registration per environment。

## App registration topology

EKP supports two minimal patterns;Chris picks one with Stakeholder per Q11 alignment 2026-05-05 W6 D5 stakeholder approval cycle:

### Pattern A — single combined app(simplest;recommended)
- **One** app registration with **two** redirect URIs(SPA + web-API)
- Frontend SPA + backend resource-server share the same client id
- `azure_client_id` Settings == `NEXT_PUBLIC_AZURE_CLIENT_ID` env

### Pattern B — separate SPA + API apps(Microsoft sample default)
- **Two** app registrations:`ekp-spa-beta`(SPA platform)+ `ekp-api-beta`(web API platform)
- SPA holds `NEXT_PUBLIC_AZURE_CLIENT_ID`;API exposes scope consumed by SPA
- `azure_client_id` Settings = API app's client id;frontend uses SPA client id
- Slightly higher operational overhead but cleaner separation

**Default for Beta**:Pattern A unless audit / compliance pushes Pattern B。

## Pattern A — step-by-step(Beta example)

### 1. Create app registration

```
Azure Portal → Microsoft Entra ID → App registrations → New registration

Name:            ekp-beta
Supported types: Accounts in this organizational directory only (Single tenant)
Redirect URI:    leave blank for now(set in step 2)
```

After create:
- **Application (client) ID** → store as `azure-client-id` in Key Vault(per `infrastructure/keyvault/README.md`)
- **Directory (tenant) ID** → store as `azure-tenant-id`

### 2. Configure Single-Page Application platform(F3.3 redirect URIs)

```
App registration → Authentication → + Add a platform → Single-page application
```

Add redirect URIs(both production + staging):
- `https://ekp.ricoh.com/`(production)
- `https://staging-ekp.ricoh.com/`(staging slot)
- `http://localhost:3001/`(W7 dev mode local)
- `http://localhost:3000/`(legacy dev port,if used)

**Front-channel logout URL**:
- `https://ekp.ricoh.com/`(post-logout redirect lands user on home)
- `https://staging-ekp.ricoh.com/`

**Implicit grant**:**leave both checkboxes unchecked**(msal-react 5.x uses Authorization Code with PKCE — implicit deprecated per Microsoft 2024 guidance)。

### 3. Expose an API(audience for backend JWT validation)

```
App registration → Expose an API → + Add a scope
```

- **Application ID URI**(auto-suggested):`api://<client-id>` — accept default
- **Scope name**:`access`
- **Who can consent**:Admins + users
- **Display + description**:"Access EKP Beta API"

Resulting scope = `api://<client-id>/access`

Set `NEXT_PUBLIC_AZURE_API_SCOPE=api://<client-id>/access` env value。

### 4. Configure API permissions(SPA → API self-grant)

```
App registration → API permissions → + Add a permission → My APIs → ekp-beta → access
```

Add the `access` scope you just exposed → **Grant admin consent for {tenant}** button(Chris admin role required)。

Optional Microsoft Graph permissions:
- `User.Read`(default delegated;safe;already granted on app create)

### 5. Generate client secret(only if Pattern B back-end uses confidential client flow)

Pattern A SPA + token-validating backend = **NO client secret needed**;backend validates JWT signature via JWKS,doesn't acquire tokens itself。

If Pattern B(API confidential client flow):
```
App registration → Certificates & secrets → + New client secret
Name:        ekp-api-beta-rotation-{YYYYMM}
Expires:     6 months
```
Copy the value(visible once)→ store in Key Vault as `azure-client-secret`。Rotation cycle 6-month per Microsoft default(per `infrastructure/keyvault/README.md` rotation SOP)。

### 6. Token configuration(optional but recommended)

```
App registration → Token configuration → + Add optional claim → ID
```

Add:
- `email`(falls back when `preferred_username` absent — covers B2B / guest)
- `upn`(redundant safety;backend already falls back to upn per `msal_provider.py:_toUser`)

### 7. Verify F1.1 cred ready

After steps 1-6,Chris populates Key Vault per `infrastructure/keyvault/README.md`:
- `azure-tenant-id` ← step 1 Directory ID
- `azure-client-id` ← step 1 Application ID
- `azure-client-secret` ← step 5(only Pattern B)

GHA secrets sync(for `frontend-deploy.yml`):
- `AZURE_TENANT_ID` repo secret = same value
- `AZURE_FRONTEND_CLIENT_ID` repo secret = step 1 Application ID
- `AZURE_API_SCOPE` repo variable = `api://<client-id>/access`

### 8. F1.5 LIVE smoke(W8 D4 trigger after steps 1-7)

```bash
# Backend with .env populated:
#   AZURE_TENANT_ID=<step 1>
#   AZURE_CLIENT_ID=<step 1>
#   FEATURE_AUTH_MOCK=false
cd backend && .venv/Scripts/python.exe -m uvicorn api.server:app --host 127.0.0.1 --port 8000

# Frontend with .env.local populated:
#   NEXT_PUBLIC_AZURE_TENANT_ID=<step 1>
#   NEXT_PUBLIC_AZURE_CLIENT_ID=<step 1>
#   NEXT_PUBLIC_AZURE_API_SCOPE=api://<client-id>/access
#   NEXT_PUBLIC_AUTH_MOCK=false
cd frontend && pnpm dev
```

Smoke flow:
1. Visit `http://localhost:3001/admin` → AuthProvider mounts → calls `initMsal()` → no cached account → user remains unauthenticated
2. Click "Sign in" CTA(W8 D4 cascade — UserMenu adds login button when `authMode === 'msal'`)→ `loginRedirect` redirects to `https://login.microsoftonline.com/...`
3. Authenticate with Ricoh Entra ID account → Entra ID redirects back to `http://localhost:3001/` with auth code
4. `handleRedirectPromise` resolves → access_token cached → `_DEV_USER` shape replaced with real `oid` + `tid` + `preferred_username`
5. Subsequent `/query` requests carry real Bearer JWT → backend `authenticate_msal` validates against JWKS → returns real `AuthenticatedUser`
6. Verify Langfuse trace tag `user_id=<real oid>` + audit log row with real `tenant_id`

Pass criterion:full redirect round-trip + `/query` 200 with real identity propagated through audit pipeline。

## F1.7 LIVE smoke acceptance(W8 D4 = G1 from W7 plan §3 deferred)

Per W7 plan §3 G1 + W8 plan §3 G1 — F1.7 LIVE = "F1 Entra ID auth LIVE smoke pass on dev tenant"。Step 8 above 滿足 acceptance。

## Tier 2(out-of-scope)

- Multi-tenant dispatcher(`/common` authority)— Tier 2 multi-tenancy
- Conditional Access policies / MFA enforcement — Beta+ Stakeholder cycle
- B2B guest invitation flow — Tier 2 cross-tenant
- Custom claims via claims mapping policy — Tier 2 advanced governance

## Cross-component dependencies

| Component | Wired |
|---|---|
| **C11 Identity & Access** | Real `msal_provider.py`(backend)+ `lib/auth/msal_provider.ts`(frontend)cred values from this app registration |
| **C12 DevOps & Infra** | Key Vault stores all 3 cred values;ACA Bicep references via `secretRef:`;GHA `frontend-deploy.yml` reads `AZURE_FRONTEND_CLIENT_ID` from repo secret |
| **C09 + C10 UI** | Login flow UI redirects to / from `https://login.microsoftonline.com/<tenant>` |

## Rollback / recovery

- **Soft delete**:Entra ID app registrations soft-delete on portal delete;recoverable 30 days via `Deleted apps` panel
- **Cred rotation**:rotate client secret without breaking app — old secret stays valid until expiry;new secret deploys via Key Vault `secret set`(per `keyvault/README.md` rotation SOP)
- **Redirect URI change**:non-breaking add(append-only);removal triggers immediate auth fail for any user mid-flow

## Update history

| Date | Change | Reason |
|---|---|---|
| 2026-05-22 | Initial SOP(W8 D4 F3.3)| F1.1 W8 D1 IT engagement cascade trigger;documented authoring complete pending Chris portal apply |
