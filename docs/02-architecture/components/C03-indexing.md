---
component: C03
name: Indexing Service
catalog_ref: ../COMPONENT_CATALOG.md#c03--indexing-service
spec_refs: [architecture.md §3.6, architecture.md §3.4]
status: v0-draft
last_updated: 2026-05-01
---

# C03 — Indexing Service Design Note

> **Status**:`v0-draft`(W2 D1 first-touch:F9 index 創建 `ekp-kb-drive-v1`;依賴 Q3 endpoint+key 已喺 .env per H5 commit `09138d4`)
>
> **Owner**:AI(SDK / REST script)+ Chris(Q3 tier+region confirmation)

---

## 1. Internal Architecture

```
backend/indexing/                ← W2 D1 create
├── __init__.py
├── schemas.py                   ← index schema dict (matches §3.6 JSON)
├── index_service.py             ← IndexService class:create / drop / get / version
├── azure_search_client.py       ← thin async wrapper(REST first;SDK optional after pip unblock)
└── (W3+) populate.py            ← bulk index loader(consumes C01 ChunkRecord output)

scripts/
└── create_index.py              ← CLI(argparse)— W2 D1 immediate use,Q3 wired

(catalog 提到 the 12-component view treats indexing 同 ingestion 分開:
 C03 owns index lifecycle;C01 owns parse/chunk/embed/emit。C03 提供 sink target;C01 push.)
```

### Per-KB index naming convention(per `architecture.md §3.4`)

```
ekp-kb-{kb_id}-v{version}

Examples:
  ekp-kb-drive_user_manuals-v1     ← first KB drive_user_manuals
  ekp-kb-drive_user_manuals-v2     ← (W4 if chunk strategy refined → re-index version bump)
  ekp-kb-medical_protocols-v1      ← (Tier 2 future KB)

Naming rules(Azure AI Search constraint):
- lowercase
- alphanumeric, hyphen, underscore
- 2-128 chars
- start with letter, end with letter or digit
- enforce in C02 KB Manager via Pydantic regex on kb_id field
```

---

## 2. Key Interfaces

### Inputs
- `KbConfig`(from C02)— embedding model / dimension(影響 vector field config)
- (W2+)`ChunkRecord`(from C01,per `§3.5` schema)— for population

### Outputs
- Created Azure AI Search index ready for query(C04 consumes)
- Index handle / endpoint URL for downstream(C04, C09 view 4)

### Side effects
- Azure AI Search REST API calls(`PUT /indexes/{name}`,`DELETE /indexes/{name}`,`POST /indexes/{name}/docs/index`)
- C12 Azure AI Search service consumes API quota(Standard S1:no per-second cap but daily quota considerations)

### REST API approach(W2 D1 immediate path,no pip required)

```python
# scripts/create_index.py(stdlib only — no Azure SDK dep,no pip required)
import json
import urllib.request
from urllib.parse import urlencode

ENDPOINT = os.environ["AZURE_SEARCH_ENDPOINT"]
KEY = os.environ["AZURE_SEARCH_ADMIN_KEY"]
API_VERSION = "2024-07-01"  # latest stable

with open("backend/indexing/schema.json") as f:
    schema = json.load(f)

req = urllib.request.Request(
    f"{ENDPOINT}/indexes/{schema['name']}?api-version={API_VERSION}",
    data=json.dumps(schema).encode(),
    headers={"Content-Type": "application/json", "api-key": KEY},
    method="PUT",
)
with urllib.request.urlopen(req) as resp:
    print(resp.status, resp.read().decode())
```

(Switch to `azure-search-documents` SDK W2 D5+ when corp proxy unblocks via R8 mitigation)

---

## 3. Critical Design Decisions

| Decision | Rationale |
|---|---|
| **REST API first(non SDK)for W2 D1** | corp proxy block PyPI(R8)→ stdlib `urllib.request` work today;`azure-search-documents` SDK install pending P1/P2;REST API stable + documented |
| **Versioned index naming `-v{n}`** | Schema migration safety:create v2 alongside v1,populate v2,switch query routing(C04),drop v1。Zero downtime |
| **Index schema 100% match `architecture.md §3.6` JSON** | Spec frozen,catalog reference only;`backend/indexing/schemas.py` 係 spec 嘅 Python representation,`schemas.json` 係 spec literal |
| **HNSW vectorSearch profile per spec**:m=4, efConstruction=400, efSearch=500, cosine | spec-dictated;HNSW 係 Azure AI Search default;parameters tuned for ~2000 chunk POC volume |
| **Semantic config `ekp-semantic-config`** | Per spec;Azure AI Search semantic ranker(non-Cohere)作為 R6 fallback(per `architecture.md §8.3`)|
| **No populate logic in C03**;population 屬 C01 ingestion pipeline owns | Single responsibility:C03 = index lifecycle,C01 = data feed |
| **Tier W2 D1 = Standard S1 default**(per spec §3.2,Q3 confirm pending)| Adequate for POC ~2K chunks + Beta ~50 user concurrent。Tier 2 multi-tenancy may upgrade to S2 |

---

## 4. Edge Cases & Error Handling

| Edge case | Handling |
|---|---|
| **Index already exists**(409 from Azure AI Search) | If kb_id 已 provisioned,C02 should pre-check via `GET /indexes/{name}`;若 race,return clear error to caller |
| **Schema mismatch on update**(Azure AI Search 唔支持 in-place schema change of vector dim / key) | New version `-v{n+1}` + populate + switch + drop old |
| **Network timeout / 5xx from Azure AI Search** | tenacity retry exponential backoff;if final fail → propagate as `IndexingError` to C02;C02 should rollback KB state(no orphan KB record without index) |
| **Quota exceeded**(Tier 2 multi-tenancy may hit) | Surface 429;alert via C07 Langfuse;propose tier upgrade |
| **Invalid kb_id format**(violates Azure naming rule) | C02 Pydantic validator catches before reach C03 |
| **Drop index that has documents**(W2+ delete KB)| Cascade delete:DELETE /indexes/{name} purges docs implicitly;Blob container drop 屬 C12 separate step |
| **Concurrent populate during index drop**(racy)| Acquire advisory lock(W2 D2 design)or accept partial fail with clear error |
| **Authentication fail**(admin key wrong / rotated)| 403;suggest .env update;point to docs/11-env-resources-detail/ |

---

## 5. Performance Characteristics

| Operation | Latency target | Notes |
|---|---|---|
| Create index(empty) | ~500-1000ms | Azure AI Search service-level call |
| Drop index | ~1-2s | Includes doc cleanup |
| Get index schema | ~100ms | Service-level read |
| Populate batch(1000 docs)| ~5-10s | Embedding upload via Azure SDK chunked |
| Query latency(C04 dependency) | ~50-200ms hybrid + ~100-300ms vector | Standard S1 |
| Populate throughput | ~1000 docs/min batch | Per Azure AI Search Standard S1 spec |

---

## 6. Test Strategy

| Test type | Scope | Status |
|---|---|---|
| **REST contract test**(create + get + drop) | Real Azure AI Search POC instance(Q3 wired)| W2 D1 |
| **Schema diff check**(detect spec drift) | Compare in-code schema vs `architecture.md §3.6` JSON literal | W2 D2 |
| **Versioning regression test**(create v1 → v2 → switch → drop v1) | Real instance | W4 末 |
| **Concurrent create race test**(2 parallel POST /kb same kb_id) | Mock Azure or real instance | W2 D2 |
| **Index quota probe** | List indexes count vs Standard S1 max(50)| W4 if approaching limit |
| **Coverage target** | ≥ 80% per CLAUDE.md H6(critical pipeline) | W4 |

---

## 7. Future Evolution / Tier 2 Hooks

| Tier 2 feature | C03 evolution |
|---|---|
| **Multi-tenancy** | Index naming `ekp-{tenant}-kb-{kb_id}-v{n}`;tenant-bound API key or RBAC via Managed Identity |
| **Multi-region replicas**(HA) | Azure AI Search service-level high-availability config;cross-region replica via Azure traffic manager |
| **Schema evolution automation** | Bicep / Terraform manages index schema diffs;auto trigger v{n+1} create + populate + switch |
| **Index sharding**(Tier 2 large KB)| Split single logical KB across multiple indexes by date range / category;C04 union query |
| **GraphRAG entity store**(Tier 2)| New separate index `ekp-kb-{kb_id}-entities-v1` for entity nodes;query layer joins via filter |
| **CMK encryption**(Q9 Sensitivity / CMK Open) | Azure AI Search supports customer-managed key;config at index create |

---

## 8. Open Items / TODO

- [ ] **Q3 outstanding minor**:tier confirm + region confirm(Standard S1 default per spec,eastus2 inferred)
- [ ] **W2 D1 `scripts/create_index.py`** REST CLI implementation
- [ ] **W2 D1 `backend/indexing/schemas.py`** match `architecture.md §3.6` JSON
- [ ] **W2 D2 `IndexService` class** wrap REST(future SDK swap)
- [ ] **W2 D2 schema diff check**(detect drift from spec)
- [ ] **W2+ Azure SDK swap** when R8 corp proxy unblocks pip install
- [ ] **Q9 CMK decision** before W7 production deploy

---

**Cross-refs**:
- Catalog: [`../COMPONENT_CATALOG.md#c03--indexing-service`](../COMPONENT_CATALOG.md#c03--indexing-service)
- Spec: `architecture.md §3.6`(index schema JSON literal)+ `§3.4`(per-KB naming)
- Risks: R3(corp DNS may affect Azure SDK calls — REST mitigates),R8(pip block delays SDK swap)
- Cross-component: consumed by C04 retrieval;populated by C01 ingestion;provisioned via C02 KB Manager
