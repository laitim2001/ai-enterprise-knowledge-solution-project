// EKP backend — Azure Container Apps Bicep spec (W8 D1 F2.2).
// Per architecture.md §6.1 W8 deploy + components/C12-devops.md.
//
// Declarative spec only — actual `az deployment group create` lives in the
// W8 D2 GHA pipeline (F2.3). Reviewed by Chris before any infra apply.
//
// CLAUDE.md §5.5 H5 — secrets only via Key Vault references; never plain text.

@description('Resource prefix; defaults to ekp-{environmentTag}')
param name string = 'ekp-${environmentTag}'

@description('Azure region — eastus2 per Q3 Resolved 2026-05-02')
param location string = 'eastus2'

@description('Environment tag — beta | staging | production')
@allowed([
  'beta'
  'staging'
  'production'
])
param environmentTag string = 'beta'

@description('Container Apps Managed Environment resource ID (pre-provisioned)')
param managedEnvironmentId string

@description('Container image full ref — set by GHA pipeline (F2.3)')
param image string

@description('Azure Key Vault URI for secret references — F2.4 Managed Identity')
param keyVaultUri string

@description('User-assigned Managed Identity resource ID (read access to Key Vault)')
param userAssignedIdentityId string

resource backend 'Microsoft.App/containerApps@2024-03-01' = {
  name: '${name}-backend'
  location: location
  identity: {
    type: 'UserAssigned'
    userAssignedIdentities: {
      '${userAssignedIdentityId}': {}
    }
  }
  properties: {
    managedEnvironmentId: managedEnvironmentId
    configuration: {
      activeRevisionsMode: 'Single'
      // Internal ingress: Front Door + Auth gate sit upstream; only /health
      // probe runs on the public 8000 port locally for liveness.
      ingress: {
        external: false
        targetPort: 8000
        transport: 'http'
        traffic: [
          {
            latestRevision: true
            weight: 100
          }
        ]
      }
      secrets: [
        // CLAUDE.md §5.5 H5 — every secret 走 Key Vault reference; no plain
        // value bake-in. Identity above must have `Key Vault Secrets User` role.
        {
          name: 'azure-openai-api-key'
          keyVaultUrl: '${keyVaultUri}secrets/azure-openai-api-key'
          identity: userAssignedIdentityId
        }
        {
          name: 'azure-search-admin-key'
          keyVaultUrl: '${keyVaultUri}secrets/azure-search-admin-key'
          identity: userAssignedIdentityId
        }
        {
          name: 'cohere-api-key'
          keyVaultUrl: '${keyVaultUri}secrets/cohere-api-key'
          identity: userAssignedIdentityId
        }
        {
          name: 'azure-tenant-id'
          keyVaultUrl: '${keyVaultUri}secrets/azure-tenant-id'
          identity: userAssignedIdentityId
        }
        {
          name: 'azure-client-id'
          keyVaultUrl: '${keyVaultUri}secrets/azure-client-id'
          identity: userAssignedIdentityId
        }
        {
          name: 'azure-client-secret'
          keyVaultUrl: '${keyVaultUri}secrets/azure-client-secret'
          identity: userAssignedIdentityId
        }
      ]
    }
    template: {
      containers: [
        {
          name: 'backend'
          image: image
          resources: {
            cpu: json('1.0')
            memory: '2Gi'
          }
          env: [
            // Non-secret config — public + safe to bake into env vars.
            { name: 'ENVIRONMENT', value: environmentTag }
            { name: 'LOG_LEVEL', value: 'INFO' }
            { name: 'AZURE_SEARCH_DEFAULT_INDEX', value: 'ekp-kb-drive-v1' }
            // W8 D4 LIVE switch — feature_auth_mock=false from beta onward.
            { name: 'FEATURE_AUTH_MOCK', value: environmentTag == 'beta' ? 'false' : 'false' }
            { name: 'RATE_LIMIT_ENABLED', value: 'true' }
            { name: 'RATE_LIMIT_PER_MINUTE', value: '50' }
            { name: 'RATE_LIMIT_CONCURRENT', value: '5' }

            // Secret env vars — resolved from secrets[] above; values never
            // appear in Bicep / GHA logs.
            { name: 'AZURE_OPENAI_API_KEY', secretRef: 'azure-openai-api-key' }
            { name: 'AZURE_SEARCH_ADMIN_KEY', secretRef: 'azure-search-admin-key' }
            { name: 'COHERE_API_KEY', secretRef: 'cohere-api-key' }
            { name: 'AZURE_TENANT_ID', secretRef: 'azure-tenant-id' }
            { name: 'AZURE_CLIENT_ID', secretRef: 'azure-client-id' }
            { name: 'AZURE_CLIENT_SECRET', secretRef: 'azure-client-secret' }
          ]
          probes: [
            // Liveness — `curl /health` matches the Dockerfile HEALTHCHECK; ACA
            // restarts the replica if 3 consecutive failures.
            {
              type: 'Liveness'
              httpGet: {
                path: '/health'
                port: 8000
              }
              initialDelaySeconds: 15
              periodSeconds: 30
              timeoutSeconds: 5
              failureThreshold: 3
            }
            // Readiness — separate from liveness so a slow lifespan init
            // (Azure SDK clients warm-up) doesn't kill the replica.
            {
              type: 'Readiness'
              httpGet: {
                path: '/health'
                port: 8000
              }
              initialDelaySeconds: 5
              periodSeconds: 10
              timeoutSeconds: 5
              failureThreshold: 3
            }
          ]
        }
      ]
      scale: {
        // Architecture.md §8.1 R5 — autoscale 1-5 replicas to absorb burst
        // without exceeding Azure OpenAI quota; rule = HTTP concurrent
        // requests target 30 (paired with rate_limit_concurrent=5/user).
        minReplicas: 1
        maxReplicas: 5
        rules: [
          {
            name: 'http-concurrency'
            http: {
              metadata: {
                concurrentRequests: '30'
              }
            }
          }
        ]
      }
    }
  }
}

output backendFqdn string = backend.properties.configuration.ingress.fqdn
output backendName string = backend.name
