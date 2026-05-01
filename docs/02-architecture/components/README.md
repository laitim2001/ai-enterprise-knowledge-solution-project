# Per-Component Design Notes

> **Purpose**:此 folder hold 每個 component 嘅 deep design note(`Cn-{kebab-name}.md`),作為 [`../COMPONENT_CATALOG.md`](../COMPONENT_CATALOG.md) 中對應 row 嘅 expansion。

## Naming convention

```
C01-ingestion.md
C02-kb-manager.md
C03-indexing.md
C04-retrieval.md
C05-generation.md
C06-eval.md
C07-observability.md
C08-api-gateway.md
C09-admin-ui.md
C10-chat-ui.md
C11-identity.md
C12-devops.md
```

## Rolling JIT 原則(per CC-5)

**唔可以 speculative pre-write**。每份 design note 喺對應 component 嘅 **first heavy-touch phase kickoff** 寫 stub,implementation 過程 enrich,phase 結束 stable。

| Component | First heavy-touch | Design note write trigger |
|---|---|---|
| C02 KB Manager | W1 D2(F7) | ✅ already implemented;design note 可 W2 D1 補(時序 retroactive)|
| C12 DevOps & Infra | W1 D1 | ✅ already in setup.md;design note 可選 |
| C06 Eval Framework | W1 D1(F5)| Cite eval-methodology.md;design note 可 W2 補 |
| C07 Observability | W1 D1 | Lightweight,可 W3 stage tracing 時補 |
| C08 API Gateway | W1 D1 | Lightweight,可 W2 wire 時補 |
| C09 Admin UI | W1 D1 | Lightweight,可 W2 KB views 時補 |
| C03 Indexing | W2 D1 | **W2 kickoff 寫** |
| C01 Ingestion | W2 D2 | **W2 kickoff 寫**(Q2 sample 到位後)|
| C04 Retrieval | W2 D5 | **W2 kickoff 寫**(prep Gate 1) |
| C05 Generation | W3 D1 | **W3 kickoff 寫** |
| C10 Chat UI | W3 D2 | **W3 kickoff 寫** |
| C11 Identity | W7 D1 | **W7 kickoff(Beta phase)寫** |

## Template

每份 design note 建議結構:

```markdown
---
component: Cn
name: <Component Name>
catalog_ref: ../COMPONENT_CATALOG.md#cn--<anchor>
spec_refs: [architecture.md §X.Y, ...]
status: stub | active | stable
last_updated: YYYY-MM-DD
---

# Cn — <Component Name> Design Note

## 1. Internal Architecture
(Layered diagram OR module decomposition within this component)

## 2. Key Interfaces
(Input / Output / Side effects, with type signatures)

## 3. Critical Design Decisions
(Why this approach over alternatives, link ADRs if any)

## 4. Edge Cases & Error Handling
(What can go wrong, how to recover)

## 5. Performance Characteristics
(Latency budget, throughput, cost-per-call)

## 6. Test Strategy
(Unit + integration coverage approach)

## 7. Future Evolution / Tier 2 Hooks
(Where Tier 2 features would plug in)
```

---

**呢份 README 會喺第一個 design note 落地時更新**(W1 retro 或 W2 kickoff)。
