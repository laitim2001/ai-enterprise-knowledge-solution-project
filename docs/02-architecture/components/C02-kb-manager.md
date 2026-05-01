---
component: C02
name: Knowledge Base Manager
catalog_ref: ../COMPONENT_CATALOG.md#c02--knowledge-base-manager
spec_refs: [architecture.md §3.4, architecture.md §4.4 #4-8]
status: v1-active
last_updated: 2026-05-01
---

# C02 — Knowledge Base Manager Design Note

> **Status**:`v1-active` — W1 D2 in-memory CRUD implemented(commit `c6ca6e3`)。W2 D1 swap to Azure-backed via FastAPI dependency override(zero call site change)。
>
> **Owner**:AI

---

## 1. Internal Architecture

```
backend/kb_management/
├── __init__.py             ← public re-exports
├── storage.py              ← Protocol + InMemoryKBBackend + Exceptions
└── service.py              ← KBService + lru_cache singleton

backend/api/
├── routes/kb.py            ← 5 endpoints,wire to KBService via Depends
└── schemas/kb.py           ← KbConfig + KbCreate + KbStatus + FailureRecord
```

**3-layer separation**:

| Layer | File | Responsibility |
|---|---|---|
| **Storage** | `storage.py` | Pure CRUD ops。W1 = `InMemoryKBBackend`(`dict[str, KbStatus]`)。W2+ = `AzureSearchKBBackend`(provisions index + Blob container)|
| **Service** | `service.py` | Translates request payloads to backend calls;sets defaults(stats=0,timestamps);singleton via `@lru_cache(maxsize=1)` |
| **API** | `api/routes/kb.py` | HTTP routing;`Annotated[KBService, Depends(get_kb_service)]` DI;maps domain exceptions to HTTP errors(404 / 409)|

**Why Protocol(non-ABC)**:duck-typed,no inheritance forced;backend impl 唔需 import storage.py,decoupled。

---

## 2. Key Interfaces

### Public API endpoints(per `architecture.md §4.4 #4-8`)

| Method | Path | Input | Output | Status codes |
|---|---|---|---|---|
| `GET` | `/kb` | — | `list[KbStatus]` | 200 |
| `POST` | `/kb` | `KbCreate` | `KbStatus` | 201 / 409 (kb_id 已存在) / 422 (validation)|
| `GET` | `/kb/{kb_id}` | path param | `KbStatus` | 200 / 404 |
| `DELETE` | `/kb/{kb_id}` | path param | — | 204 / 404 |
| `PATCH` | `/kb/{kb_id}/settings` | `KbConfig` | `KbConfig` | 200 / 404 |

### Storage backend Protocol

```python
class KBStorageBackend(Protocol):
    async def create(self, kb: KbStatus) -> KbStatus: ...
    async def list_all(self) -> list[KbStatus]: ...
    async def get(self, kb_id: str) -> KbStatus: ...      # raises KBNotFoundError
    async def delete(self, kb_id: str) -> None: ...        # raises KBNotFoundError
    async def update_config(self, kb_id: str, config: KbConfig) -> KbStatus: ...
```

### Side effects

| Backend | Side effect on `create()` |
|---|---|
| **InMemory(W1)** | `dict[kb_id] = kb`(in-process state,not durable)|
| **AzureSearch(W2)** | Provision per-KB index `ekp-kb-{kb_id}-v1`(via C03)+ provision Blob container `ekp-kb-{kb_id}-screenshots`(via C12)+ persist KB record(可選 cosmos / table storage)|

---

## 3. Critical Design Decisions

| Decision | Rationale |
|---|---|
| **Protocol-based storage abstraction(非 W1 寫死 in-memory)** | W2 D1 swap to Azure-backed需要 zero call-site change;Protocol 預留 swap point。Plan §2 F7 寫 `kb_service.py` 單檔,W1 D2 implementation 升級為 3-file package(per CC-1 component design override)|
| **`lru_cache(maxsize=1)` singleton via FastAPI Depends** | Cleaner than module-level mutable global;test override via `app.dependency_overrides[get_kb_service]` works regardless |
| **`Annotated[KBService, Depends(get_kb_service)]` instead of default-arg `Depends(...)`** | FastAPI modern style + ruff B008 clean(B008 = "no function call in arg defaults")|
| **kb_id 由 client 提供(non-generated)** | Per `§3.4`,kb_id forms index name `ekp-kb-{kb_id}-v1`;index name 有 Azure AI Search 命名約束(lowercase / hyphen-underscore only),client 應該明確控制 |
| **PATCH `/settings` 用 full-replace KbConfig**(非 partial PATCH semantic)| KbConfig 5 fields 全部 default,full-replace 等同 PUT semantic;true partial PATCH 需要 Optional fields schema = scope creep。W2+ 如需可加 KbConfigPatch |
| **Errors:return domain exception(KBNotFoundError / KBAlreadyExistsError)由 route layer map HTTP** | Domain logic 同 HTTP 解耦;backend 唔知 HTTP code |

---

## 4. Edge Cases & Error Handling

| Edge case | Behavior |
|---|---|
| `POST /kb` with duplicate `kb_id` | `KBAlreadyExistsError` → 409 Conflict |
| `GET /kb/{kb_id}` not found | `KBNotFoundError` → 404 |
| `DELETE /kb/{kb_id}` not found | 404(not 204 silent — caller should know)|
| `PATCH /kb/{kb_id}/settings` not found | 404 |
| Invalid `kb_id` format(uppercase / spaces / etc)| Pydantic validation 422(W2 加入 regex constraint per Azure AI Search index naming rule)|
| Server restart | W1 in-memory:全部 KB 遺失(`@lru_cache` 重建空 instance)。W2 Azure-backed:persist 到 storage(Cosmos / Table)|
| Concurrent `POST /kb` race(2 requests same kb_id)| W1 in-memory:Python GIL ensures atomic dict insert,but check-then-set race possible。W2:Azure-backed transaction handle |
| `DELETE /kb/{kb_id}` when KB has documents(W2+)| W1 in-memory:no-op（無 doc state）;W2 cascade delete index + Blob container per `§3.4` "cleanup" |

---

## 5. Performance Characteristics

| Operation | W1 in-memory | W2 Azure-backed |
|---|---|---|
| `GET /kb` (list) | O(1)(returns list of values)| ~50ms Azure Search service-level call |
| `POST /kb` (create) | O(1) + dict insert | ~500-1000ms(create index API + Blob container API + persist record)|
| `GET /kb/{kb_id}` | O(1) dict lookup | ~50ms |
| `DELETE /kb/{kb_id}` | O(1) | ~1-2s(delete index + delete container)|
| `PATCH /kb/{kb_id}/settings` | O(1) | ~100ms(update record);若 config change requires re-index,trigger separate workflow(W2+)|

**No bottleneck expected at POC scale**(< 10 KB total,Tier 2 multi-tenancy 才會撞 KB count 大規模)。

---

## 6. Test Strategy

| Test type | Scope | Status |
|---|---|---|
| **Unit tests for in-memory backend**(`storage.py`)| Each Protocol method,error paths | ⏳ Deferred to post-pip-install window(R8 active)|
| **Service-level tests**(`service.py`)| KBCreate → KbStatus mapping with default stats | ⏳ Deferred(同上)|
| **Integration tests via FastAPI TestClient**(`api/routes/kb.py`)| End-to-end:POST → GET → PATCH → DELETE happy path + error paths | ⏳ Deferred |
| **W2 swap regression test** | After AzureSearchKBBackend 落地,run same Protocol-level test against new backend | W2 D2 |
| **Concurrent create race test** | Two parallel `POST /kb` same kb_id → expect 1× 201 + 1× 409 | W2 D2 |

**Coverage target**:per CLAUDE.md §3.1:critical pipeline modules ≥ 80%。`backend/kb_management/` 屬 critical path supporting C03 / C04 / C06。

---

## 7. Future Evolution / Tier 2 Hooks

| Tier 2 feature | C02 evolution |
|---|---|
| **Multi-tenancy** | Add `tenant_id` field to KbCreate / KbStatus;index name becomes `ekp-{tenant_id}-{kb_id}-v1`;C11 middleware injects tenant_id from auth context |
| **KB clone / template** | Add `POST /kb/{kb_id}/clone` endpoint;copies config + creates new index without copying chunks |
| **KB versioning**(beyond v{n} index)| Add `POST /kb/{kb_id}/versions` lifecycle |
| **KB-level rate limit**(per-KB quota)| Add `quota` field to KbConfig,enforce via C08 middleware |
| **Cross-KB retrieval** | Storage-level transparent;query layer(C04)takes `list[kb_id]` instead of single kb_id |

---

## 8. Open Items / TODO

- [ ] **W2 D1 AzureSearchKBBackend impl** — implements `KBStorageBackend` Protocol,wire via `app.dependency_overrides[get_kb_service]` in lifespan
- [ ] **kb_id Pydantic regex validator** — enforce Azure Search naming rule
- [ ] **Persist KB metadata** beyond Azure Search index(option:Cosmos DB or Azure Table Storage)— W2 D2 decision
- [ ] **Unit test suite**(post-pip-install window)
- [ ] **W2 swap regression test**(Protocol-level)

---

**Cross-refs**:
- Catalog: [`../COMPONENT_CATALOG.md#c02--knowledge-base-manager`](../COMPONENT_CATALOG.md#c02--knowledge-base-manager)
- Spec: `architecture.md §3.4`(multi-KB)+ `§4.4 #4-8`(API)+ `§3.6`(index schema target for W2)
- Implementation commit: `c6ca6e3`(W1 D2)
- Dependent components: C03(Indexing)+ C12(Blob container provision)
