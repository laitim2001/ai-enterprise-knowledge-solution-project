"""Evaluation Pydantic schemas (per architecture.md §4.5)."""

from pydantic import BaseModel


class FailedQueryDetail(BaseModel):
    query_id: str
    query: str
    expected: str
    got: str
    metric_failed: list[str]


class EvalReport(BaseModel):
    recall_at_5: float
    faithfulness: float
    correctness: float | None
    image_association: float
    p95_latency_ms: int
    failed_queries: list[FailedQueryDetail]
    crag_trigger_rate: float
    avg_cost_per_query_usd: float


class RerankerShootoutEntry(BaseModel):
    """One reranker's eval entry in shootout comparison (W16 F5.4 CO_W15_F1)."""

    reranker: str  # "cohere-v4.0-pro" / "cohere-v3.5" / "azure-semantic" / "off"
    skipped: bool  # True if reranker env config missing (per W4 shootout pattern)
    skip_reason: str  # populated when skipped=True
    report: EvalReport | None  # None when skipped


class ShootoutReport(BaseModel):
    """Multi-reranker shootout comparison (W16 F5.4 CO_W15_F1).

    Tier 1 baseline iterates supplied reranker labels; per Decision C.1 returns
    full ShootoutReport schema. Real reranker swap requires per-reranker engine
    reconstruction (see endpoint impl). Hybrid-only baseline (reranker="off")
    always evaluable as comparison anchor.
    """

    eval_set_id: str
    started_at: str
    finished_at: str
    rerankers: list[RerankerShootoutEntry]
    winner: str | None  # max recall_at_5 among non-skipped entries; None if all skipped
