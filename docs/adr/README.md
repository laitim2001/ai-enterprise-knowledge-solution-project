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
| [0016](./0016-password-hash-scrypt-stdlib.md) | Password hashing — argon2-cffi → hashlib.scrypt(Python stdlib)| Accepted | W13 D5 F5 implementation 2026-06-10(R8 corp proxy `pip install argon2-cffi` blocker;user instruction option 1 stdlib path;H2 vendor decision change ADR per strict reading)|
| [0018](./0018-multi-kb-kb-id-propagation.md) | Multi-KB `kb_id` propagation — Tier 1 commit via dynamic `index_name` injection(reaffirm ADR-0005)| Accepted | W15 D5 closeout audit `audit-W15-d5-vs-spec.md` §CC-1 trigger 2026-05-09;P0.1 P0 batch decision(reaffirm not supersede ADR-0005;Option B b2 Dynamic injection chosen over Option A scope reversal + Option C hybrid + (b1) per-KB instance map);Phase 3 implementation W16+ active flip ~1.5-2 days |
| [0019](./0019-pdf-parser-tier-1-deliver.md) | PDF parser Tier 1 deliver via Docling DocLayNet(reaffirm ADR-0003 multi-format ingestion)| Accepted | W15 D5 closeout audit `audit-W15-d5-vs-spec.md` §1.2 C01 Major drift #1 trigger 2026-05-09;P0.2 P0 batch decision(reaffirm not supersede ADR-0003;Option A deliver chosen over Option B Tier 2 defer;Tier 1 scope = text-extractable PDF only,scanned/encrypted defer Tier 2);Phase 3 implementation W16+ active flip ~1 day |
| [0020](./0020-context-expander-tier-1-deliver.md) | Context Expander step Tier 1 deliver(reaffirm architecture.md §3.1 + V6 9-stage spec via code catch-up)| Accepted | W15 D5 closeout audit `audit-W15-d5-vs-spec.md` §1.5 C05 Major drift #3 + §CC-3 trigger 2026-05-09;P0.3 P0 batch decision(reaffirm not amend §3.1 + §5.7;Option A deliver chosen over Option B amend spec + Option C split delivery;internal-spec inconsistency resolved by code + V6 + C05 design note 5-source align);Phase 3 implementation W16+ active flip ~1.5 days(sequential dependency on ADR-0018 Multi-KB kb_id wiring)|

> §13.10 ("Other v3 inherits") 屬 meta-rollup,不單獨 promote。
> ADR-0013 reserved for AF3 lifespan gate split fix(W11 D5 retro carry-over #1;defer per R5)。
> ADR-0017 reserved for R8 corp proxy mitigation pattern formalization(currently 4 cumulative occurrences:Cohere W3 + argon2-cffi W13 + ACS SDK W13 + Playwright browser CDN W15 D5;trigger threshold 5th occurrence OR vendor-decision pivot needed per W15 plan §F4 risks)。

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

**Next NNNN**:`0013` reserved for AF3 fix(W11 D5 retro);`0017` reserved for R8 mitigation pattern;`0018`+`0019`+`0020` landed(P0 batch:Multi-KB kb_id propagation + PDF parser + Context Expander)— **P0 batch complete from `audit-W15-d5-vs-spec.md` §6 W16+ Remediation Prioritization**;next available `0021`(future ADR candidates per `audit-W15-d5-vs-spec.md` §7:0021 cookie migration W17+ / 0022 KB Manager persistent backing W17+)。
