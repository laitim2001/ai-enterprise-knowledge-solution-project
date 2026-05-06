// EKP backend ACA networking — Private Endpoint to Azure AI Search +
// VNet integration (W8 D3 F2.5).
// Per W08-beta-deploy-sprint2 plan §2 F2.5 + components/C12-devops.md.
//
// Declarative spec only. Chris infra apply gated on:
//   - Resource group `rg-ekp-beta-eastus2` exists
//   - Azure AI Search service `srch-ekp-beta` exists (per Q3 Resolved)
//   - Pre-provisioned VNet `vnet-ekp-beta` with /23 address space
//   - ACA Managed Environment `cae-ekp-beta` already vnet-injected at create
//
// CLAUDE.md §5.5 H5 — Private Endpoint forces Search traffic onto the VNet,
// no public-internet hop; Search public access disabled separately by Chris
// after PE provisioned + verified working.

@description('Resource prefix; defaults to ekp-{environmentTag}')
param name string = 'ekp-${environmentTag}'

@description('Azure region')
param location string = 'eastus2'

@description('Environment tag — beta | staging | production')
@allowed([
  'beta'
  'staging'
  'production'
])
param environmentTag string = 'beta'

@description('VNet resource ID — must be pre-provisioned by Chris infra session')
param vnetId string

@description('Subnet name within the VNet for Private Endpoints')
param peSubnetName string = 'snet-private-endpoints'

@description('Azure AI Search service resource ID — target of the PE')
param searchServiceId string

@description('Private DNS zone resource ID — privatelink.search.windows.net')
param privateDnsZoneId string

// ----------------------------------------------------------------------------
// Private Endpoint to Azure AI Search
// ----------------------------------------------------------------------------
//
// Front Door + Auth gate sit upstream of ACA; Search PE means the backend
// container's outbound retrieval traffic stays on the VNet without traversing
// the internet. Beta+ compliance + reduced data-egress cost.
resource searchPe 'Microsoft.Network/privateEndpoints@2024-01-01' = {
  name: '${name}-search-pe'
  location: location
  properties: {
    subnet: {
      id: '${vnetId}/subnets/${peSubnetName}'
    }
    privateLinkServiceConnections: [
      {
        name: '${name}-search-plsc'
        properties: {
          privateLinkServiceId: searchServiceId
          groupIds: [
            'searchService'
          ]
        }
      }
    ]
  }
}

// ----------------------------------------------------------------------------
// Private DNS zone group — auto-register the PE NIC into
// `privatelink.search.windows.net` so backend's `azure_search_endpoint`
// resolves to the private IP from inside the ACA VNet.
// ----------------------------------------------------------------------------
resource searchPeDnsGroup 'Microsoft.Network/privateEndpoints/privateDnsZoneGroups@2024-01-01' = {
  parent: searchPe
  name: 'default'
  properties: {
    privateDnsZoneConfigs: [
      {
        name: 'search-windows-net'
        properties: {
          privateDnsZoneId: privateDnsZoneId
        }
      }
    ]
  }
}

// ----------------------------------------------------------------------------
// Output — referenced by `backend.bicep` for FQDN / NIC verification
// ----------------------------------------------------------------------------
output searchPrivateEndpointId string = searchPe.id
output searchPrivateEndpointName string = searchPe.name
