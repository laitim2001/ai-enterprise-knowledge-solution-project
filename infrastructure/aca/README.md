# Azure Container Apps spec(W8 D1 F2.2)

> Per W08-beta-deploy-sprint2 plan §2 F2 + components/C12-devops.md。
> **Owner**:Chris(infra apply)+ AI(spec authoring)。
> **Status**:declarative spec only;actual `az deployment group create` lives in W8 D2 GHA pipeline(F2.3)。

## Files

| File | Purpose |
|---|---|
| `backend.bicep` | EKP backend Container App spec — image / env / secrets(Key Vault refs)/ probes / autoscale 1-5 |
| `networking.bicep`(W8 D3)| Private Endpoint to Azure AI Search + Private DNS zone group;forces backend retrieval traffic onto VNet(no internet hop)|
| `parameters.beta.json`(W8 D2)| Per-environment parameter file populated by GHA pipeline pre-deploy |

## Pre-requisites(Chris infra setup,outside W8 D1 AI scope)

1. **Azure resource group** — `rg-ekp-beta-eastus2`(per Q3 Resolved 2026-05-02)
2. **Container Apps Managed Environment** — `cae-ekp-beta`(must exist before backend.bicep deploy)
3. **Azure Container Registry** — `acrekpbeta`(GHA pipeline pushes here per F2.3)
4. **Azure Key Vault** — `kv-ekp-beta`(secrets created W8 D1+D2 cascade per F2.4)
5. **User-assigned Managed Identity** — `id-ekp-beta-backend`(role `Key Vault Secrets User` on `kv-ekp-beta`;assigned to backend Container App)
6. **Pre-populated secrets in Key Vault**:`azure-openai-api-key` / `azure-search-admin-key` / `cohere-api-key` / `azure-tenant-id` / `azure-client-id` / `azure-client-secret`

## Deploy(W8 D2 GHA pipeline reference — informational)

```bash
# Manual ad-hoc deploy(non-CI usage). Production goes via GHA per F2.3.
az deployment group create \
  --resource-group rg-ekp-beta-eastus2 \
  --template-file infrastructure/aca/backend.bicep \
  --parameters \
    managedEnvironmentId="/subscriptions/{SUB}/resourceGroups/rg-ekp-beta-eastus2/providers/Microsoft.App/managedEnvironments/cae-ekp-beta" \
    image="acrekpbeta.azurecr.io/ekp-backend:{GIT_SHA}" \
    keyVaultUri="https://kv-ekp-beta.vault.azure.net/" \
    userAssignedIdentityId="/subscriptions/{SUB}/resourceGroups/rg-ekp-beta-eastus2/providers/Microsoft.ManagedIdentity/userAssignedIdentities/id-ekp-beta-backend"
```

## Spec highlights

- **Ingress**:internal(`external: false`)— Front Door + Auth gate sit upstream;`/health` 8000 internal probe target only
- **Resources**:1 vCPU + 2 GiB memory per replica(architecture.md §9 cost row;~$45/month for 2 replicas)
- **Autoscale**:1-5 replicas;HTTP concurrency rule target 30 paired with app-level rate limit `rate_limit_concurrent=5/user`(architecture.md §8.1 R5)
- **Probes**:Liveness `/health` 30s interval;Readiness `/health` 10s interval — separate so slow lifespan(Azure SDK warm-up)doesn't kill replica
- **Identity**:User-assigned MI for Key Vault Secrets User role(F2.4 secrets management;CLAUDE.md §5.5 H5 — no plain-text bake-in)
- **Env vars(non-secret)**:`ENVIRONMENT` / `LOG_LEVEL` / `AZURE_SEARCH_DEFAULT_INDEX` / `FEATURE_AUTH_MOCK=false`(W8 D4 LIVE switch)/ `RATE_LIMIT_*`
- **Env vars(secret refs)**:6 secrets all `secretRef:` resolved at runtime;values never in Bicep / GHA logs

## W8 D2 cascade

- F2.3 GHA pipeline:`test → ruff → docker build → ACR push → ACA deploy revision → smoke`(landed `.github/workflows/backend-deploy.yml` W8 D2)
- F2.4 Key Vault populate:Chris pre-stages secrets;Managed Identity grant via `az role assignment create`(SOP `infrastructure/keyvault/README.md` W8 D2)

## W8 D3 cascade

- F2.5 networking:`networking.bicep` Private Endpoint to Azure AI Search;auto-DNS via `privatelink.search.windows.net` zone group;**Chris infra apply** sequence:
  1. Pre-provision VNet `vnet-ekp-beta`(/23)+ subnet `snet-private-endpoints`(`/27` for PE NICs)+ subnet `snet-aca`(`/24` for ACA env)
  2. Create ACA Managed Environment with `--infrastructure-subnet-resource-id <snet-aca>`(VNet integration must be set at env create — non-mutable post-create)
  3. Create Private DNS zone `privatelink.search.windows.net` linked to VNet
  4. `az deployment group create --template-file infrastructure/aca/networking.bicep --parameters ...`
  5. Disable Azure AI Search public access via `az search service update --public-network-access disabled`(only AFTER PE verified working — irreversible without re-enabling)
- Networking deploy command(W8 D3 reference):

```bash
az deployment group create \
  --resource-group rg-ekp-beta-eastus2 \
  --template-file infrastructure/aca/networking.bicep \
  --parameters \
    environmentTag=beta \
    vnetId="/subscriptions/{SUB}/resourceGroups/rg-ekp-beta-eastus2/providers/Microsoft.Network/virtualNetworks/vnet-ekp-beta" \
    peSubnetName=snet-private-endpoints \
    searchServiceId="/subscriptions/{SUB}/resourceGroups/rg-ekp-beta-eastus2/providers/Microsoft.Search/searchServices/srch-ekp-beta" \
    privateDnsZoneId="/subscriptions/{SUB}/resourceGroups/rg-ekp-beta-eastus2/providers/Microsoft.Network/privateDnsZones/privatelink.search.windows.net"
```
