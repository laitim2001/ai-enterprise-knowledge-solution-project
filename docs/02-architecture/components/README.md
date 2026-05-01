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

## Design-first with v0-draft marker(per CC-5 v1.1)

**W1 D3-D5 batch 寫齊 11 個 v0-draft note**(C11 Beta+ defer)作為 implementation 嘅 reference contract。Implementation 過程中發現 design 偏差 → update note + bump `status` field。

### Status semantics

| Status | Meaning |
|---|---|
| `v0-draft` | Pre-implementation,may evolve when impl hits reality |
| `v1-active` | Implementation in progress,design validated by partial impl |
| `v2-stable` | Implementation 完成,design final |

### Write schedule

| Component | First heavy-touch | v0-draft write |
|---|---|---|
| C12 DevOps & Infra | W1 D1 ✅ implemented | W1 D3(this batch) |
| C02 KB Manager | W1 D2 ✅ implemented | W1 D3(this batch) |
| C08 API Gateway | W1 D1 ✅ scaffold | W1 D3(this batch) |
| C06 Eval Framework | W1 D1 ✅ validator scaffold | W1 D3(this batch) |
| C07 Observability | W1 D1 ✅ init | W1 D3(this batch) |
| C09 Admin UI | W1 D1 ✅ 6 routes scaffold | W1 D4 |
| C10 Chat UI | W3 D2(future) | W1 D4 |
| C03 Indexing | W2 D1(future) | W1 D4 |
| C01 Ingestion | W2 D2(future,blocked Q2) | W1 D5 |
| C04 Retrieval | W2 D5(future) | W1 D5 |
| C05 Generation | W3 D1(future) | W1 D5 |
| C11 Identity | W7 D1(Beta+) | **DEFER to W6 末 / W7 kickoff** |

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
