# EKP Architecture Decision Records (ADRs)

> Format per `CLAUDE.md` §6。Filename pattern:`NNNN-short-kebab-title.md`(NNNN = 4-digit zero-padded sequential)。

## Index

| ADR | Title | Status | Source |
|---|---|---|---|
| [0001](./0001-build-vs-buy-self-build-ekp.md) | Build vs Buy — Self-build EKP based on D1/D2/D3 differentiators | Accepted | `architecture.md` §13.0 |
| [0002](./0002-project-rename-to-ekp.md) | Project rename to EKP(Enterprise Knowledge Platform) | Accepted | `architecture.md` §13.1 |
| [0003](./0003-multi-format-ingestion.md) | Multi-format ingestion(Word + PDF + PPT) | Accepted | `architecture.md` §13.2 |
| [0004](./0004-layout-aware-chunking.md) | Layout-aware chunking — not character-based | Accepted | `architecture.md` §13.3 |
| [0005](./0005-multi-kb-architecture-day1.md) | Multi-KB architecture from Day 1 | Accepted | `architecture.md` §13.4 |
| [0006](./0006-nextjs-shadcn-day1.md) | Next.js 14 + shadcn/ui from Day 1(replace Streamlit) | Accepted | `architecture.md` §13.5 |
| [0007](./0007-l2-crag-not-l0-l4.md) | L2 CRAG(not L0 / L4+)for Tier 1 | Accepted | `architecture.md` §13.6 |
| [0008](./0008-graphrag-trigger-matrix.md) | GraphRAG via Trigger Matrix(not "Plan B added on") | Accepted | `architecture.md` §13.7 |
| [0009](./0009-frontend-backend-separated.md) | Frontend / Backend separated(not Next.js full-stack) | Accepted | `architecture.md` §13.8 |
| [0010](./0010-dify-read-only-reference.md) | Dify as read-only reference(no fork, no copy) | Accepted | `architecture.md` §13.9 |
| [0011](./0011-custom-crag-vs-langgraph.md) | Custom CRAG vs LangGraph framework — Tier 1 path | Accepted | `architecture.md` §13.11 |
| [0012](./0012-cohere-v4-pro-upgrade-and-gate2-partial-pass.md) | Cohere Rerank v3.5 → v4.0-pro same-vendor model upgrade + Gate 2 PARTIAL PASS verdict landed | Accepted | W6 D5 stakeholder approval cycle 2026-05-05(`architecture.md` v5 → v5.1 amendment) |
| [0014](./0014-hybrid-auth-sso-plus-self-register.md) | Hybrid auth model — Microsoft Entra ID SSO + self-service email register | Accepted | W11 D2 cont stakeholder approval cycle 2026-06-10(`architecture.md` v5.1 → v6 amendment;sister ADR with 0015) |
| [0015](./0015-ui-tier-1-expansion-dify-leaning.md) | UI Tier 1 expansion — 6 views → 9 views + shadcn/ui foundation commit + Dify-leaning aesthetic | Accepted | W11 D2 cont stakeholder approval cycle 2026-06-10(`architecture.md` v5.1 → v6 amendment;sister ADR with 0014) |

> §13.10 ("Other v3 inherits") 屬 meta-rollup,不單獨 promote。
> ADR-0013 reserved for AF3 lifespan gate split fix(W11 D5 retro carry-over #1;defer per R5)。

## Adding a new ADR

Per `CLAUDE.md` §6 — 任何違反 §5.1 H1 / §5.2 H2 嘅變動必須 ADR(approval 後)。Format:

```markdown
# ADR-NNNN: <Title>

**Date**: YYYY-MM-DD
**Status**: Proposed | Accepted | Superseded by ADR-MMMM
**Approver**: <Name>

## Context
## Decision
## Alternatives Considered
## Consequences
## References
```

**Next NNNN**:`0013` reserved for AF3 fix(W11 D5 retro);next available `0016`(per CLAUDE.md §6 sequential)。
