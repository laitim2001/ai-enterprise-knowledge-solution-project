---
component: C07
name: Observability Stack
catalog_ref: ../COMPONENT_CATALOG.md#c07--observability-stack
spec_refs: [architecture.md §3.2, architecture.md §4.3]
status: v0-draft
last_updated: 2026-05-01
---

# C07 — Observability Stack Design Note

> **Status**:`v0-draft`(W1 D1 Langfuse healthy + structlog stub init ✅;per-pipeline-stage tracing W3 wire;cost / latency dashboards W4-W6)
>
> **Owner**:AI

---

## 1. Internal Architecture

```
backend/observability/
├── __init__.py
└── langfuse_tracer.py          ← Init stub (W1 ✅) → W3 enrich with @observe decorator wrappers

backend/(各 module 用 structlog directly):
backend.kb_management.service   ← structlog.get_logger().info("kb.created", kb_id=...)
backend.api.routes.query        ← @observe + structlog.bind(trace_id=...) per request
backend.eval.runner             ← @observe per eval iteration
... etc

infrastructure/docker-compose.yml(C12)
└── langfuse v2 service          ← UI on :3000,Postgres backing
└── postgres 16-alpine           ← Langfuse persistence layer
```

**Trace data flow**:

```
HTTP request
    │
    ├─► Structlog request log (JSON to stdout) ─► Container log → Azure Log Analytics (W7+)
    │
    ▼
Service layer code
    │
    ├─► @observe(name="retrieval.hybrid")     ─► Langfuse trace span
    │   @observe(name="generation.crag.iter") ─► nested span
    │   @observe(name="judge.gpt54mini")      ─► nested span
    │
    ▼
Async batched flush (Langfuse SDK)
    │
    ▼
Langfuse Postgres (local W1 / cloud W7+)
    │
    ▼
Langfuse UI (http://localhost:3000) → trace detail view
```

---

## 2. Key Interfaces

### Code-side(developer-facing)

```python
# Structured logging
from structlog import get_logger
log = get_logger(__name__)
log.info("kb.created", kb_id=kb.kb_id, chunk_count=0)

# Langfuse trace
from langfuse.decorators import observe
@observe(name="retrieval.hybrid")
async def retrieve(query: str, kb_id: str, top_k: int) -> list[ChunkRecord]:
    ...

# Manual trace span (when @observe insufficient)
from langfuse.client import Langfuse
langfuse = Langfuse()
with langfuse.trace(name="custom.operation") as trace:
    ...
```

### Outputs
- **Stdout JSON**:per-line structured log,scrapable by container log collector
- **Langfuse UI**:`http://localhost:3000` per-trace detail with hierarchy,timing,token usage
- **Langfuse API**(W4+)`/api/public/traces` for programmatic access(C06 eval framework reads traces for context-aware metric)

### Configuration
```python
# backend/observability/langfuse_tracer.py
def init_tracer(settings: Settings) -> None:
    if settings.langfuse_public_key and settings.langfuse_secret_key:
        # Wire Langfuse SDK
    structlog.configure(
        processors=[
            structlog.processors.TimeStamper(fmt="iso"),
            structlog.processors.JSONRenderer(),
        ],
    )
```

---

## 3. Critical Design Decisions

| Decision | Rationale |
|---|---|
| **Langfuse self-host(non SaaS)** | Data sovereignty(Ricoh internal data not leave corp)、cost control at scale、CLAUDE.md §5.5 H5 alignment |
| **Structlog over stdlib `logging`** | JSON-native output,key-value structured fields(better for Azure Log Analytics queries / Splunk),no string formatting bugs |
| **`@observe` decorator over manual span**(預設) | Less boilerplate;auto-captures function args + return + duration;manual span 留 for cross-function spans |
| **Async batched flush**(Langfuse SDK 預設)| Don't block request path on trace ingestion;batched POST to Langfuse |
| **No sampling W1-W6**(100% trace)| POC phase trace volume low;visibility > cost。W7+ enable sampling if cost concern |
| **Per-component trace name convention**:`{component}.{operation}`(e.g. `retrieval.hybrid`,`generation.crag.iter`)| Predictable filter in Langfuse UI;match catalog C-naming |
| **Sensitive data scrubbing**(per §5.5 H5)| Query payload OK trace(authorized internal data);**never** log full LLM prompts containing user PII to plaintext file。Langfuse encrypts at rest |

---

## 4. Edge Cases & Error Handling

| Edge case | Behavior |
|---|---|
| **Langfuse down**(Postgres connection lost)| Langfuse SDK 內部 buffer + retry;若 buffer full → drop trace,log warning to structlog;**never** block request path |
| **Langfuse Postgres disk full**(Beta+ load)| Alert via Langfuse自身 monitoring;evict oldest traces(retention policy)|
| **Trace volume burst**(load spike)| Async batch growing;若 SDK buffer overflow → drop oldest;alert |
| **Sensitive token / key accidentally in trace input**(developer mistake)| Code review catches;Langfuse提供 input/output redaction config W4+ enable |
| **Structlog renderer crash on non-serializable obj**(e.g. raw bytes)| Convert via `repr()` fallback;don't crash request |
| **`init_tracer()` fail**(Langfuse keys 未填)| Log warning,continue;structlog still works,Langfuse traces silently disabled |

---

## 5. Performance Characteristics

| Metric | Target | Notes |
|---|---|---|
| Per-request structlog overhead | < 1ms | Negligible |
| Per-request Langfuse `@observe` overhead | < 5ms | Async batched flush 不 block request |
| Trace flush latency(SDK → Langfuse server)| < 5s typical | Async batch interval default 5s |
| Langfuse UI trace lookup(by trace_id)| < 500ms | Postgres indexed lookup |
| Langfuse trace ingest throughput | ~100 traces/sec local;~10K traces/sec cluster mode(Tier 2) | |
| Storage growth(POC trace size) | ~1KB per simple trace,~5KB per CRAG iteration | 30 query/day × 5KB = 150KB/day,trivial |

---

## 6. Test Strategy

| Test type | Scope | Status |
|---|---|---|
| **Smoke check**:`curl http://localhost:3000/api/public/health` | Langfuse alive | ✅ W1 D1 manual |
| **Trace presence assertion**(integration)| Hit endpoint → assert trace appears in Langfuse via API query | W3 |
| **Structlog format assertion** | Assert log line is valid JSON with expected fields | W2 |
| **Sensitive scrubbing test**(W4+ with redaction config)| Inject "test_secret_value" into request → assert NOT present in Langfuse trace | W4+ |
| **Langfuse down resilience** | Stop Langfuse container → assert request still succeeds | W3 |

---

## 7. Future Evolution / Tier 2 Hooks

| Tier 2 feature | C07 evolution |
|---|---|
| **Cluster mode for Beta+ load** | Langfuse v2 cluster docker-compose + Postgres replica;or migrate to Langfuse Cloud(SaaS)if cost-effective |
| **Datadog / Splunk export**(enterprise SOC integration)| Langfuse → webhook → Datadog ingest;or structlog → Fluentd → Splunk |
| **Real-time alerting on metric anomaly** | Langfuse webhook on filter match(e.g. error rate > 5%);Slack / PagerDuty integration |
| **Cost optimization dashboard**(LLM token spend trend)| Aggregate Langfuse usage data → custom dashboard(C09 admin UI 加 view) |
| **A/B test framework**(W4 reranker shootout precursor)| Langfuse trace tags by variant;aggregation by tag for comparison |
| **Distributed tracing**(W7+ multi-service)| OpenTelemetry export from Langfuse traces;Azure Monitor integration |

---

## 8. Open Items / TODO

- [ ] **W3 D1 enrich `langfuse_tracer.py`**:wire `@observe` decorators on C04 / C05 critical paths
- [ ] **W3 D5 trace presence integration test**
- [ ] **W4 cost / latency dashboard query** in Langfuse UI(savable filter)
- [ ] **Sensitive data redaction config**(W4+,enable Langfuse server-side scrub)
- [ ] **Langfuse Public + Secret Key generation**(W1 D1 manual create-account flow per `setup.md`)→ Chris fill `.env` LANGFUSE_PUBLIC_KEY / LANGFUSE_SECRET_KEY when ready

---

**Cross-refs**:
- Catalog: [`../COMPONENT_CATALOG.md#c07--observability-stack`](../COMPONENT_CATALOG.md#c07--observability-stack)
- Spec: `architecture.md §3.2`(stack table — Langfuse)+ `§4.3`(local stack topology)
- Init commit: `b21a0a2`(W1 D1 stub)+ `f7ba973`(Langfuse image pin fix)
- Cross-component: traces produced by C04 / C05 / C06;consumed by C09 debug view (W4)
