# ADR-0018: Multi-KB `kb_id` propagation — Tier 1 commit via dynamic `index_name` injection(reaffirm ADR-0005)

**Date**: 2026-05-09
**Status**: Accepted
**Approver**: Chris(技術 Lead)
**Trigger**: `docs/02-architecture/audit-W15-d5-vs-spec.md` §CC-1 Multi-KB invariant gap surfaced(W15 D5 closeout audit verdict ⚠️ MINOR DRIFT,Major Drift #4)

---

## Context

### Spec promise(authoritative,frozen)

**ADR-0005**(`docs/adr/0005-multi-kb-architecture-day1.md`,Accepted):
> EKP 從 Day 1 已支援 multiple Knowledge Bases,with `kb_id` namespacing 跨:(a)search index — `ekp-kb-{kb_id}-v{version}`;(b)blob storage container — `ekp-kb-{kb_id}-screenshots`;(c)chunk_id format — `kb-{kb_id}_doc-{doc_id}_chunk-{idx:04d}`

**architecture.md §3.4 Multi-Knowledge-Base Architecture**(lines 268-292,frozen v6):
- 第一個 KB = `drive_user_manuals`(per W6 Q7 Resolved 2026-05-05 stakeholder approval cycle)
- W16+ Beta cohort 候選 KBs:RAPO 內部 + 1-2 友好部門

### Code reality(verified spot-check 2026-05-09 audit)

| Layer | Spec promise | Code reality | Status |
|---|---|---|---|
| Schema | `QueryRequest.kb_id` field | `backend/api/schemas/query.py:36` ✅ field exists | Aligned |
| Route handler | `/query` reads `payload.kb_id` | `backend/api/routes/query.py` grep `kb_id` = **0 hits** | ❌ Broken |
| Retrieval engine | `retrieve(query, top_k, kb_id)` | `backend/retrieval/retrieval_engine.py:87` signature 冇 `kb_id` parameter | ❌ Broken |
| Hybrid filter | `kb_id eq '{kb_id}'` AND clause | `backend/retrieval/hybrid.py:33 _DEFAULT_FILTER = "enabled eq true and low_value_flag eq false"` 冇 `kb_id` | ❌ Broken |
| App state | per-KB engine map | `app.state.retrieval_engine` single shared instance wired to `azure_search_default_index = "ekp-kb-drive-v1"` | ❌ Broken |
| Blob container | per-KB container | `azure_blob_container_screenshots = "ekp-kb-drive-screenshots"` single hardcoded;`backend/ingestion/screenshots/uploader.py:8` 註明 "single-KB Tier 1 baseline" | ❌ Broken(intentional comment)|

### Latent risk profile

- **Today**(W15 D5 closeout):Tier 1 single-KB(Drive only)— functionally OK,所有 query 自動 → `ekp-kb-drive-v1`
- **W16+ Beta cohort**(per Q7 Resolved):「RAPO 內部 + 1-2 友好部門」— **可能想 per-department KBs**(e.g. `rapo_internal` + `finance_dept` + `hr_dept`),documents 性質唔同,跨部門搜索可能有 access control concern
- **加 2nd KB without fix**:silent misroute — user 喺 V1 Chat select 「HR docs」KB query,system 全部 forward 去 Drive index,搵唔到 / 攞到 wrong context,**zero error surface**

### Decision driver

呢個 ADR 由 W15 D5 closeout 全項 audit(`audit-W15-d5-vs-spec.md`)4 個 parallel agent 嘅 cross-cutting finding(CC-1)觸發。Audit verdict ⚠️ MINOR DRIFT — 5 major drifts 入面 Multi-KB invariant 屬 latent bomb(Tier 1 OK,Tier 2 / W16+ multi-KB activation crit risk)。

---

## Decision

**1. 重申 ADR-0005**(reaffirm Day 1 multi-KB stance — **NOT supersede**)

**2. Wire `kb_id` dynamic injection through retrieval pipeline** for Tier 1 deliver:

### Implementation contract

- **`RetrievalEngine.retrieve()` signature 加 `kb_id` parameter**:
  ```python
  async def retrieve(
      self,
      query: str,
      top_k: int,
      kb_id: str,                    # NEW required parameter
      filter_clause: str | None = None,
  ) -> RetrievalResult:
      ...
  ```

- **Searcher dynamically constructs `index_name`**(NOT per-KB instance map):
  ```python
  index_name = f"ekp-kb-{kb_id}-v1"  # convention per ADR-0005
  ```

- **HybridSearcher filter prepends `kb_id eq` clause**:
  ```python
  filter = f"kb_id eq '{kb_id}' and enabled eq true and low_value_flag eq false"
  ```

- **`/query` route reads `payload.kb_id`**(with default backwards-compat):
  ```python
  kb_id = payload.kb_id or "drive_user_manuals"  # default for omitted field
  ```

- **Blob container dynamic construction**(parallel pattern to search index):
  - `extractor.py` + `uploader.py` 用 `f"ekp-kb-{kb_id}-screenshots"` runtime
  - Settings preserve `azure_blob_container_screenshots` 作為 single-KB POC fallback default

- **W16 F5 backend stub closure cascade align same `kb_id` awareness**:
  - `/eval/run` + `/debug/trace/{id}` + `/kb/{id}/documents` 全部 kb_id-scoped 設計
  - Eval set 結構 extend 支援 per-KB sub-set(W16+ cohort onboarding deliverable)

### Implementation timing

- **Phase 3 of P0 batch**(W16+ active flip post Track A IT cred populate event)
- **Estimated 1.5-2 days**(retrieval signature change + searcher index_name injection + hybrid filter clause + route handler + integration tests + KB-aware eval setup)
- **Spread over 2-3 sessions** allowed
- **Batch with W16 F5 backend stub closure refactor**(shared kb_id awareness scope economy)

---

## Alternatives Considered

### Option A — 降 scope(Tier 1 single-KB confirmation,ADR-0005 amendment)

**Action**:
- Amend ADR-0005:"Architecture multi-KB-ready,but **Tier 1 implementation single-KB only**(Drive);Tier 2 activation 觸發 multi-KB plumbing"
- `QueryRequest.kb_id` field 加 deprecation note "Tier 2 reserved field"
- architecture.md §3.4 加 note Tier 1 single-KB simplification
- W16+ Beta 唔 add 第 2 個 KB(blocking constraint)

**Pros**:
- Most truthful to current code reality
- Lowest immediate work(0.5 day spec-only)
- 0 risk of incomplete multi-KB plumbing causing W16+ Beta deploy bugs
- 符合 Karpathy §1.2 simplicity-first(Tier 1 真係只 launch Drive)

**Cons**:
- Reverses ADR-0005 Day 1 multi-KB stance — governance debt
- Beta narrative weakened(stakeholder pitch "1 platform 服務多部門" 講唔到)
- Tier 2 仍要做同樣嘅 kb_id wiring,只係 deferred,no net saving
- Q7 stakeholder context(RAPO + 1-2 departments)signal 多部門 KB 機率高 — 反向 lock 自己

**Rejected because**:Q7 stakeholder context expects per-department KBs;ADR-0005 promise reversal = governance debt > 1.5-2 days code work;Tier 2 not a saving。

### Option C — Hybrid(wire signature but Tier 1 launches single-KB only)

**Pros**:Type plumbing in place,2nd KB activation = config-driven(future)

**Cons**:
- 90% of Option B work + 80% of risk + 0 actual multi-KB validation
- Karpathy §1.2 — middle state delivers least value
- Defer 真實 multi-KB exercise 直到 Tier 2 多 KB user activates — bug surface rate higher

**Rejected because**:if 你 wire,就 wire 完整(deliver feature);唔 wire 就唔 wire(Option A)。Middle state = most cost,least value。

### (b1) Per-KB instance map(`app.state.retrieval_engines: dict[str, RetrievalEngine]`)

**Pros**:Type-safe per-KB encapsulation;avoid dynamic string construction at retrieve time

**Cons**:
- Each engine must be created at app startup(dynamic KB creation 需要 lifespan refresh)
- State mutation in lifespan 複雜;hard to add KB without app restart
- Dict membership check + KeyError handling overhead per call

**Rejected in favor of (b2) Dynamic injection** — per Karpathy §1.2 simplicity-first;single retrieval engine,dynamically scope per call;new KB activation = create index + populate + start querying(no app restart)。

---

## Consequences

### Positive

- **ADR-0005 honored**(no governance debt;reaffirm not supersede)
- **Tier 1 actually delivers multi-KB capability**(platform value proposition preserved)
- **Beta cohort 真可 per-department KBs**(Q7 stakeholder context alignment;RAPO + Finance + HR each own KB possible)
- **Stakeholder demo 可 include multi-KB scenario**(broader narrative)
- **Tier 2 activation no repeat work**(已 done at Tier 1)
- **Aligns with C02 Knowledge Base Manager scope**(per architecture.md §4.4 18-endpoint contract — KB CRUD already wired)
- **W16 F5 backend stub closure synergy**(stub endpoints 自然 kb_id-aware design)

### Negative

- **W16 schedule +15-20%**(1.5-2 days code work)— W16 已有 F1-F5 deliverables busy(Track A IT cred + R-B1 closure + 25% Beta cohort rollout + daily metric monitor + user smoke + backend stub closure)
- **New code = new risk surface for Beta launch** — mitigated via:
  - Backwards-compat default(omitted `kb_id` → fall back to `"drive_user_manuals"`)
  - Integration tests asserting cross-KB query 唔 leak
  - Default 值 preserve existing test pass rate
- **2nd KB eval-set creation needed** for cohort onboarding validation — W16+ deliverable extend `eval-set-v0.yaml` + 加 KB-2 placeholder 1-5 queries via `eval_set_augmentor.py` pipeline(minimum scope)

### Neutral

- **Phase 3 implementation**:可 batch with W16 F5 backend stub closure refactor(共用 kb_id awareness scope economy)
- **Frontend(V1 Chat KB selector dropdown)可 land later**:backend kb_id wiring sufficient for API contract;frontend 可 W17+ activate(spec §5.2 KB selector)
- **Default backwards-compat ensures existing tests pass**:0 baseline test breakage expected;new tests added for multi-KB invariant assertions

---

## References

- **Reaffirmed(NOT superseded)**:[ADR-0005 Multi-KB architecture from Day 1](./0005-multi-kb-architecture-day1.md)
- **Spec source**:`docs/architecture.md` §3.4 Multi-Knowledge-Base Architecture(lines 268-292,frozen v6)
- **Audit trigger**:`docs/02-architecture/audit-W15-d5-vs-spec.md` §CC-1(2026-05-09 W15 D5 closeout)
- **Stakeholder context**:Q7 Resolved 2026-05-05(`docs/decision-form.md`)— Beta cohort RAPO 內部 + 1-2 友好部門
- **Code citations**:
  - `backend/api/schemas/query.py:36`(QueryRequest.kb_id field exists)
  - `backend/api/routes/query.py`(kb_id 0 hits)
  - `backend/retrieval/retrieval_engine.py:87`(retrieve signature 冇 kb_id)
  - `backend/retrieval/hybrid.py:33`(filter 冇 kb_id eq)
  - `backend/ingestion/screenshots/uploader.py:8`(single-KB Tier 1 baseline comment)
- **Behavioral baseline**:Karpathy §1.2 simplicity-first(rejected (b1) per-KB instance map)+ §1.4 goal-driven(multi-KB = platform value proposition core)

---

## Implementation Deliverables(W16+ Phase 3)

### Code changes(retrieval pipeline)
- [ ] `backend/retrieval/retrieval_engine.py` — `retrieve()` signature add `kb_id: str` parameter
- [ ] `backend/retrieval/hybrid.py` — Searcher accept `kb_id` + dynamic `index_name = f"ekp-kb-{kb_id}-v1"` + filter prepend `kb_id eq '{kb_id}' and ...`
- [ ] `backend/retrieval/reranker/*.py` — pass-through `kb_id`(no behavior change but signature consistency)
- [ ] `backend/api/routes/query.py` — read `payload.kb_id` with default `"drive_user_manuals"` backwards-compat

### Code changes(blob storage)
- [ ] `backend/ingestion/screenshots/extractor.py` — dynamic blob container per `kb_id`
- [ ] `backend/ingestion/screenshots/uploader.py` — dynamic blob container per `kb_id`;remove single-KB baseline comment(line 8)post-implementation

### Settings + config
- [ ] `backend/storage/settings.py` — `kb_id_default = "drive_user_manuals"` constant for backwards-compat fallback;deprecate hardcoded `azure_search_default_index` + `azure_blob_container_screenshots` to dynamic

### Tests
- [ ] Integration tests:multi-KB query routing assertions(2 KB scenario,assert no cross-KB leakage)
- [ ] Unit tests:`hybrid.py` filter clause assertion(kb_id present in filter string)
- [ ] Backwards-compat test:`payload.kb_id = None` → defaults to `"drive_user_manuals"`,no regression
- [ ] `eval-set-v1` extension(W16+ cohort onboarding):1-5 KB-2 placeholder queries via `eval_set_augmentor.py`

### Documentation
- [ ] architecture.md §3.4 amendment(P1 Phase 4B):reaffirm Tier 1 multi-KB delivery + cross-ref ADR-0018
- [ ] components/C02-kb-manager.md update(P1 Phase 4C):reflect multi-KB live state
- [ ] components/C04-retrieval.md update:`retrieve()` signature change

### Eval / observability
- [ ] Per-KB eval reports(extend `backend/eval/runner.py` to support `kb_id` parameter)
- [ ] Langfuse trace tags `kb_id`(per-KB cost / latency attribution)
- [ ] Cost dashboard per-KB breakdown(`backend/observability/realtime_cost.py` extend)

---

**Implementation timing**:W16 active flip post Track A IT cred populate event trigger(rolling JIT per CLAUDE.md §10 R1)。Estimated 1.5-2 days work;may span 2-3 sessions。Batch with W16 F5 backend stub closure cascade for shared `kb_id` awareness refactor。

**Re-audit trigger**:Post-implementation audit re-run on §CC-1 specifically — verify multi-KB invariant restored(spec ↔ code aligned)。
