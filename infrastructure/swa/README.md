# Azure Static Web Apps custom domain SOP — F3.2(W8 D4)

> Per W08-beta-deploy-sprint2 plan §2 F3.2 + components/C12-devops.md。
> **Owner**:Chris(DNS + Azure portal apply)+ AI(SOP authoring)。
> **Status**:SOP only — actual DNS + portal apply lives in Chris infra session(W8 D4-D5 cascade)。

## Overview

Frontend deploys to Azure Static Web Apps(SWA)per `.github/workflows/frontend-deploy.yml`(W8 D3 F3.1)。Default SWA URL is `<random>.azurestaticapps.net`。Beta phase needs friendly custom domain(`ekp.ricoh.com`)+ HTTPS via SWA managed cert。

## Naming + scope

| Environment | Custom domain | SWA slot |
|---|---|---|
| Beta(W8-W10)| `ekp-beta.ricoh.com` | production slot |
| Staging | `staging-ekp.ricoh.com` | staging slot |
| Production(W11+)| `ekp.ricoh.com` | production slot post-rollout |

**Q owner**(per W7 carry-over):**Chris confirm with Stakeholder W8 D1**(Q owner choice tracked in `decision-form.md`)。Default = subdomain of `ricoh.com` corp domain。

## Pre-requisites(Chris infra setup)

1. **SWA resource exists** — created automatically by first GHA `frontend-deploy.yml` run W8 D3
2. **DNS authority** — Ricoh corp DNS team(or `ricoh.com` registrar)access for CNAME / TXT record creation
3. **Azure portal access** — Chris with `Web Plan Contributor` or `Contributor` on SWA resource

## Step-by-step

### 1. Add custom domain in Azure portal

```
Azure Portal → Static Web Apps → ekp-beta-frontend → Custom domains → + Add
Type:   Custom domain on other DNS
Domain: ekp-beta.ricoh.com
```

Azure responds with **two pieces of info**:
- **CNAME target value**(e.g. `delightful-pebble-1234.4.azurestaticapps.net`)
- **TXT validation token**(format `_dnsauth.ekp-beta.ricoh.com TXT <random>`)

### 2. Create DNS records(Ricoh corp DNS team)

| Record | Name | Type | Value | TTL |
|---|---|---|---|---|
| Validation | `_dnsauth.ekp-beta.ricoh.com` | TXT | `<random>` from step 1 | 300s |
| Routing | `ekp-beta.ricoh.com` | CNAME | `<swa-name>.azurestaticapps.net` from step 1 | 300s |

DNS propagation:5 min - 48h depending on Ricoh corp DNS cache。Verify via:
```bash
dig +short TXT _dnsauth.ekp-beta.ricoh.com
dig +short CNAME ekp-beta.ricoh.com
```

### 3. Validate domain in Azure portal

```
Azure Portal → Static Web Apps → ekp-beta-frontend → Custom domains → ekp-beta.ricoh.com → Validate
```

Status flips:`Validating` → `Adding` → `Ready` once DNS propagation complete。SSL cert auto-provisioned via SWA managed cert(LetsEncrypt-backed)≈ 5-10 min after validation。

### 4. Update Entra ID app registration redirect URIs

Per `infrastructure/entra-id/README.md` step 2,add the custom domain as redirect URI + post-logout URI:
- `https://ekp-beta.ricoh.com/`
- `https://staging-ekp.ricoh.com/`

Without this,login redirect from Entra ID lands on the wrong host → AADSTS50011 error。

### 5. Update GHA `frontend-deploy.yml` env vars

```
GHA repo settings → Variables → NEXT_PUBLIC_API_URL = https://api-ekp-beta.ricoh.com
```

(API URL is the corresponding backend custom domain — separate Front Door / API Management setup,W8+ scope)。

## Apex domain caveat

If Stakeholder picks `ekp.ricoh.com`(apex / root subdomain),CNAME records aren't allowed at apex per RFC。Two options:

- **Option A**(recommended):use ALIAS record(if Ricoh corp DNS supports it — Azure DNS / Cloudflare yes;internal BIND no)
- **Option B**:use SWA's TXT-validated A record method:
  ```
  Type:   Custom domain on other DNS(A record - apex)
  Domain: ekp.ricoh.com
  ```
  Azure responds with IP + TXT;create A record(IP)+ TXT(validation)at Ricoh corp DNS。

## Post-validation security headers verification

`staticwebapp.config.json`(W8 D3 F3.4)bakes security headers including HSTS。Confirm response headers include:

```bash
curl -I https://ekp-beta.ricoh.com/
# Expected:
#   strict-transport-security: max-age=31536000; includeSubDomains
#   x-frame-options: DENY
#   x-content-type-options: nosniff
```

## Rollback

- **Cert issue**:SWA auto-provisions new cert on next deploy;manual `Reset cert` button in portal if stuck
- **Wrong CNAME target**:update DNS record;5-min TTL means recovery quick
- **Domain conflict with another SWA**:remove from this SWA(`Custom domains → ... → Delete`),add to correct one;DNS records stay valid

## Cross-component dependencies

| Component | Wired |
|---|---|
| **C09 + C10 UI** | Custom domain serves frontend SPA |
| **C11 Identity** | Entra ID app registration redirect URIs MUST include custom domain(per `entra-id/README.md` step 2)|
| **C12 DevOps** | DNS records managed by Ricoh corp DNS team — out of EKP team scope |

## Tier 2(out-of-scope)

- Front Door / WAF in front of SWA — Tier 2 advanced perimeter
- Multi-region SWA failover — Tier 2 production geo-redundancy
- Custom cert(non-SWA managed)— Tier 2 enterprise PKI integration

## Update history

| Date | Change | Reason |
|---|---|---|
| 2026-05-22 | Initial SOP(W8 D4 F3.2)| First-time SWA custom domain workflow;documents Chris cascade gating on DNS authority |
