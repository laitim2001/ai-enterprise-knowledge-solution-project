---
component: C08
name: API Gateway
catalog_ref: ../COMPONENT_CATALOG.md#c08--api-gateway
spec_refs: [architecture.md §4.1, architecture.md §4.4, architecture.md §4.5]
status: v0-draft
last_updated: 2026-05-01
---

# C08 — API Gateway Design Note

> **Status**:`v0-draft`(scaffold:18 stubs ✅;wiring 進行中:C02 already wired W1 D2;C03/C04/C05/C06 wire W2-W4)
>
> **Owner**:AI

---

## 1. Internal Architecture

```
backend/api/
├── server.py                   ← FastAPI app + lifespan + 8 router includes
├── routes/                     ← 8 routers,共 18 endpoints
│   ├── query.py                ← /query (1) ── wires C04 + C05 (W2-W3)
│   ├── feedback.py             ← /feedback (1) ── wires C06 (W4+)
│   ├── kb.py                   ← /kb 5 endpoints ── wires C02 ✅ (W1 D2)
│   ├── documents.py            ← /kb/{id}/documents 4 endpoints ── wires C01 (W2)
│   ├── chunks.py               ← /kb/{id}/.../chunks 2 endpoints ── wires C01+C03 (W3)
│   ├── eval.py                 ← /eval (1) ── wires C06 (W4)
│   ├── debug.py                ← /debug/{trace_id} (1) ── wires C07 (W3-W4)
│   └── screenshots.py          ← /screenshots/{path} (1) ── wires C12 Blob (W2)
├── schemas/                    ← Pydantic v2 models per §4.5
│   ├── query.py
│   ├── feedback.py
│   ├── kb.py                   ← KbCreate + KbStatus + KbConfig + FailureRecord
│   └── eval.py
└── (future) middleware/        ← W7+ MSAL auth + rate limit
```

**Layered request flow**:

```
HTTP request
    │
    ▼
FastAPI middleware stack
    ├─ CORS (POC)
    ├─ (W7+) MSAL auth — C11
    ├─ (W7+) Rate limit
    └─ Structlog request log — C07
    │
    ▼
Router handler (api/routes/*.py)
    │
    ├─ Pydantic validation (input)
    ├─ Annotated[Service, Depends(get_*_service)] DI
    │
    ▼
Service / Domain layer (e.g. C02 KBService, C04 RetrievalEngine)
    │
    ▼
Storage / External (Azure AI Search / Azure OpenAI / Blob)
    │
    ▼
Pydantic serialization (output)
    │
    ▼
HTTP response
```

---

## 2. Key Interfaces

### 18 endpoints(per `architecture.md §4.4`)

| # | Path | Method | Wires C | First impl phase |
|---|---|---|---|---|
| 1 | `/health` | GET | (meta) | W1 D1 ✅ |
| 2 | `/query` | POST | C04 + C05 + C07 | W2-W3 |
| 3 | `/feedback` | POST | C06 | W4 |
| 4-8 | `/kb` × 5 | GET / POST / GET / DELETE / PATCH | C02 ✅ | W1 D2 ✅ |
| 9-12 | `/kb/{id}/documents` × 4 | GET / POST / DELETE / POST(reindex)| C01 + C03 | W2 |
| 13-14 | `/kb/{id}/.../chunks` × 2 | GET / PATCH | C01 + C03 | W3 |
| 15 | `/eval` | POST | C06 | W4 |
| 16 | `/debug/{trace_id}` | GET | C07 | W3-W4 |
| 17 | `/screenshots/{path}` | GET | C12 Blob | W2 |
| 18 | (extra reserved) | TBD | — | TBD |

(實際 17 + 1 reserved per spec §4.4 18-row table)

### Schema conventions(per `architecture.md §4.5`)

- **All schemas Pydantic v2**(`from pydantic import BaseModel`)
- **snake_case** field names(per CLAUDE.md §3.3)
- **Datetime fields use `datetime` type**(timezone-aware UTC where possible)
- **Lists use `list[T]` syntax**(Python 3.9+ native generic)
- **Optional fields use `T | None = None`**(PEP 604 union)

### Error response shape

```json
{
  "detail": "Human-readable error message"
}
```

(FastAPI default;may add `error_code` field W7+ for client UX)

---

## 3. Critical Design Decisions

| Decision | Rationale |
|---|---|
| **FastAPI lifespan() for service init**(non `@app.on_event`)| `@app.on_event` deprecated FastAPI 0.110+;lifespan context manager 係 modern pattern。Init `init_tracer(settings)` once,inject into app state |
| **`Annotated[Service, Depends(...)]` over default-arg DI** | Modern FastAPI style;ruff B008 clean;reusable type alias `KbServiceDep = Annotated[KBService, Depends(get_kb_service)]` per route file |
| **Service singleton via `@lru_cache`**(non module-global mutable)| Test-friendly(`app.dependency_overrides[get_kb_service]` works);immutable from caller perspective |
| **Stub endpoints raise `HTTPException(501, "...spec ref")`** | Document not-yet-impl with traceable spec reference;callers see clear "implement per architecture.md §X.Y" message |
| **Pydantic Settings 從 `.env` 讀,`extra="ignore"`** | Forward-compatible:新加 .env field 唔 break existing settings load |
| **No global error handler middleware POC**(rely on per-route try/except)| Simpler;errors mostly domain-specific(KBNotFound / 404 vs ValidationError / 422)。W7+ may add for cross-cutting (e.g. rate limit 429)|
| **Streaming endpoint(`/query`)用 `StreamingResponse` + SSE**(W3) | Compatible with Vercel AI SDK `useChat`(C10);simpler than WebSocket |

---

## 4. Edge Cases & Error Handling

| Edge case | Handling |
|---|---|
| Pydantic validation fail | Auto 422 with field-level error(FastAPI default)|
| Domain `*NotFoundError` | Per-route try/except → 404 |
| Domain `*AlreadyExistsError` | 409 Conflict |
| External service timeout(Azure OpenAI / Cohere)| `tenacity` retry with exponential backoff;若 final fail → 503 Service Unavailable + Langfuse trace |
| 大文件 upload(`POST /kb/{id}/documents`)| FastAPI `UploadFile` streaming;limit 100MB per spec(W2 implement)|
| Streaming connection drop(`/query`)| Server-side cleanup of in-flight CRAG iterations;Langfuse trace marks `aborted` |
| `/health` during service init | Returns `{"status": "ok"}` even if downstream(Azure)not reachable — health = liveness only,not readiness。W7+ separate `/ready` for readiness |
| (W7+) MSAL token expired | 401 with `WWW-Authenticate: Bearer` header;C10 chat UI silent refresh |
| (W7+) Rate limit exceeded | 429 with `Retry-After` header;C10 chat UI 顯示 "請稍候 X 秒" |

---

## 5. Performance Characteristics

| Endpoint | Latency budget(P95)| Notes |
|---|---|---|
| `/health` | < 10ms | Liveness only |
| `/kb` (list) | < 100ms W1;< 200ms W2 | In-memory vs Azure call |
| `/kb` (POST create) | < 200ms W1;< 1500ms W2 | W2 includes index + container provision |
| `/query` (full RAG) | **< 5s P95**(per `architecture.md §1.7` business metric) | Includes retrieval + rerank + LLM synthesis |
| `/query` time-to-first-token(stream)| **< 2s P95** | Critical UX metric for C10 chat |
| `/feedback` | < 100ms | Async write to Langfuse |
| `/eval` (full eval run) | ~5min(30 queries × 4 metrics)| Async background task,return job_id immediately |

**Concurrency**:uvicorn 1 worker dev / W7+ Azure CA scale 2-10 instances;async I/O throughout(no sync blocking).

**Memory**:< 200MB per worker(FastAPI + Pydantic + httpx + structlog,no heavy ML in-process).

---

## 6. Test Strategy

| Layer | Test type | Status |
|---|---|---|
| **Smoke tests**(8 routers exist + 18 endpoints registered)| `tests/test_api_skeleton.py` | ✅ written W1 D1;⏳ pytest run deferred R8 |
| **Per-endpoint contract tests**(input → output) | FastAPI TestClient,parametrized happy path + error cases | Per Cn wire phase(W2-W4) |
| **Integration tests**(end-to-end with real Azurite + mocked Azure)| TestClient + Azurite running | W4-W5 |
| **Streaming endpoint test**(`/query` SSE)| TestClient `stream=True` | W3 |
| (W7+) **Auth middleware test** | MSAL test tokens | W7 |
| **Coverage target** | ≥ 80% for `api/routes/query.py`(per CLAUDE.md H6) | W4 |

---

## 7. Future Evolution / Tier 2 Hooks

| Tier 2 feature | C08 evolution |
|---|---|
| **Multi-tenancy** | Middleware extracts `tenant_id` from auth token,injects into request state;all services receive tenant_id via Depends |
| **GraphQL endpoint** | Add `/graphql` route alongside REST;Strawberry or Ariadne lib;same service layer underneath |
| **Workflow / plugin builder** | Add `/workflows` router(new component C13)+ workflow execution endpoint |
| **gRPC alternative**(internal service-to-service)| FastAPI 仍對 web client;internal C04/C05 calls 可改 gRPC for perf |
| **OpenAPI export to Postman / SDK gen** | FastAPI auto-generates OpenAPI spec;W7+ wire to Stoplight / Postman for stakeholder API exploration |
| **Webhook callback registration**(eval done,doc indexed)| Add `/webhooks` router |

---

## 8. Open Items / TODO

- [ ] **F2 pytest verification**(8 smoke tests)— deferred R8
- [ ] **W2 documents router wiring**(C01 ingestion endpoints)
- [ ] **W2 query router skeleton**(C04 retrieval call,no rerank yet)
- [ ] **W3 query streaming**(SSE for C10 chat)
- [ ] **W4 eval router wiring**(C06)
- [ ] **W4 debug router wiring**(C07 Langfuse trace lookup)
- [ ] **W7+ MSAL middleware**(C11)
- [ ] **W7+ Rate limit middleware** + Redis backing
- [ ] **API contract doc**(`docs/api-contract.md` per CLAUDE.md §2 routing)— W2 末 deliverable

---

**Cross-refs**:
- Catalog: [`../COMPONENT_CATALOG.md#c08--api-gateway`](../COMPONENT_CATALOG.md#c08--api-gateway)
- Spec: `architecture.md §4.1`(stack)+ `§4.4`(18 endpoint table)+ `§4.5`(schema)
- Skeleton commit: `b21a0a2`(W1 D1)
- KB router wired commit: `c6ca6e3`(W1 D2)
- Wired components: C02 ✅ ;upcoming C01 / C03 / C04 / C05 / C06 / C07
