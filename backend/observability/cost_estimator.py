"""C07 — Cost projection table + per-day aggregator (W8 D5 F5.2).

Per architecture.md §7.4 Day-2 Readiness + §9 cost estimate table.

Two halves:
  1. **Static reference rates** — per-1k-token (Azure OpenAI) / per-1k-call
     (Cohere) / fixed-monthly (Blob + AI Search) drawn from the architecture.md
     §9 cost rows. These are projection inputs, not actuals — actual spend
     comes from Azure Cost Management + Cohere billing portal.
  2. **Per-day projection** — given the monthly Beta column from architecture.md
     §9, spread evenly across 30 days. The route layer (F5.2) merges these
     projections with audit_log volume so the admin UI can sanity-check
     projection vs realised request count.

Karpathy §1.2 simplicity-first: this module ships projections only. Real-time
LLM token attribution requires Langfuse generations API (W9+ progressive
instrumentation when query / synthesizer / crag stages emit `@observe` traces).
"""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class ServiceCostRow:
    """One row of the projected daily cost dashboard."""

    service: str
    component: str  # which architecture.md §3.2 component the service backs
    projected_daily_usd: float
    projected_monthly_usd: float
    source: str  # documentation / cost-tracking source

    def to_dict(self) -> dict[str, float | str]:
        return {
            "service": self.service,
            "component": self.component,
            "projected_daily_usd": round(self.projected_daily_usd, 2),
            "projected_monthly_usd": round(self.projected_monthly_usd, 2),
            "source": self.source,
        }


# Per architecture.md §9 cost-estimate Beta column (4-week Beta phase).
# Numbers projected forward to a steady-state monthly figure for projection
# clarity. Production column (W11+) usage 大概率 higher — re-baseline
# post-Beta real query distribution.
_BETA_MONTHLY_BASELINE: tuple[ServiceCostRow, ...] = (
    ServiceCostRow(
        service="Azure AI Search Standard S1",
        component="C03 Indexing Service",
        projected_monthly_usd=75.0,
        projected_daily_usd=75.0 / 30,
        source="architecture.md §9 row 1 (S1 multi-KB ready)",
    ),
    ServiceCostRow(
        service="Azure OpenAI text-embedding-3-large",
        component="C01 Ingestion Pipeline + C04 Retrieval",
        projected_monthly_usd=1.0,
        projected_daily_usd=1.0 / 30,
        source="architecture.md §9 row 2 (1024d MRL truncate)",
    ),
    ServiceCostRow(
        service="Azure OpenAI GPT-5.5 synthesis",
        component="C05 Generation Pipeline",
        projected_monthly_usd=120.0,
        projected_daily_usd=120.0 / 30,
        source="architecture.md §9 row 3 (Beta 50 user × 5 q/day)",
    ),
    ServiceCostRow(
        service="Azure OpenAI GPT-5.4-mini judge",
        component="C05 Generation (CRAG L2 grader)",
        projected_monthly_usd=15.0,
        projected_daily_usd=15.0 / 30,
        source="architecture.md §9 row 4 (CRAG trigger ~30%)",
    ),
    ServiceCostRow(
        service="Cohere Rerank v4.0-pro (Marketplace)",
        component="C04 Retrieval Engine",
        projected_monthly_usd=20.0,
        projected_daily_usd=20.0 / 30,
        source="architecture.md §9 row 5 (Path A Marketplace per Q5; v4.0-pro per ADR-0012)",
    ),
    ServiceCostRow(
        service="Azure Blob Storage (screenshots)",
        component="C12 DevOps + C03 Indexing",
        projected_monthly_usd=2.0,
        projected_daily_usd=2.0 / 30,
        source="architecture.md §9 row 6 (Hot tier 500 GB-month proxy)",
    ),
    ServiceCostRow(
        service="Azure Container Apps (backend)",
        component="C12 DevOps",
        projected_monthly_usd=45.0,
        projected_daily_usd=45.0 / 30,
        source="W8 plan §2 F2 (1 vCPU + 2GB autoscale 1-5)",
    ),
    ServiceCostRow(
        service="Azure Static Web Apps (frontend)",
        component="C12 DevOps",
        projected_monthly_usd=10.0,
        projected_daily_usd=10.0 / 30,
        source="W8 plan §2 F3 (Standard tier custom domain + auth)",
    ),
)


def projected_daily_rows() -> list[ServiceCostRow]:
    """Return the static Beta-baseline projection table.

    Stable order matches architecture.md §9 row order so the admin UI table
    presentation is reproducible across requests.
    """
    return list(_BETA_MONTHLY_BASELINE)


def total_projected_monthly_usd() -> float:
    return round(sum(row.projected_monthly_usd for row in _BETA_MONTHLY_BASELINE), 2)


def total_projected_daily_usd() -> float:
    return round(sum(row.projected_daily_usd for row in _BETA_MONTHLY_BASELINE), 2)
