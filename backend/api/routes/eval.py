"""Evaluation endpoints (per architecture.md §4.4 #15-16).

- POST /eval/run wires eval/orchestrator.run_eval_pipeline (Recall@5 always;
  RAGAs 4-metric faithfulness/correctness when an Azure OpenAI judge key +
  app.state.synthesizer are both available — W17 F3 per orchestrator docstring).
- POST /eval/shootout iterates rerankers via per-reranker engine swap pattern;
  returns ShootoutReport schema.

CLI alternatives: scripts/run_ragas_eval.py (standalone RAGAs driver),
scripts/run_reranker_shootout.py (W4-era multi-reranker driver).

eval-set ids (W17 F3.4 finding): `eval-set-v0` (real, validated subset) +
`eval-set-v1-draft` (WIP — the v1 *final* file `docs/eval-set-v1.yaml` does
NOT exist yet; finalizing it needs Chris's SME reference-answer labels per Q14,
without which `answer_correctness` proper can't be scored — `correctness` here
is approximated by RAGAs answer-relevancy. CO_W15_F1_eval_set_v1 stays open
pending the SME label cascade — no ground truth fabricated).
"""

from datetime import UTC, datetime
from pathlib import Path

from fastapi import APIRouter, HTTPException, Request, status
from pydantic import BaseModel

from api.schemas.eval import EvalReport, RerankerShootoutEntry, ShootoutReport
from eval.orchestrator import run_eval_pipeline
from eval.ragas_evaluator import make_ragas_evaluator
from retrieval.retrieval_engine import RetrievalEngine
from storage.settings import get_settings

router = APIRouter()

# Anchor eval-set paths to project root (not CWD) so endpoints work
# regardless of where uvicorn / pytest is launched from.
_PROJECT_ROOT = Path(__file__).resolve().parents[3]  # backend/api/routes/eval.py → project root

_SHOOTOUT_DEFAULT_RERANKERS = [
    "cohere-v4.0-pro",  # ADR-0012 production lock baseline
    "off",  # hybrid-only fallback comparison anchor
]


class EvalRunRequest(BaseModel):
    eval_set_id: str = "eval-set-v0"  # default to docs/eval-set-v0.yaml
    llm_model: str = "gpt-5.5"
    reranker: str = "cohere-v4.0-pro"  # ADR-0012 production lock
    enable_crag: bool = True
    max_main_queries: int | None = None  # cost-containment cap per W4 plan §4 R4


class EvalShootoutRequest(BaseModel):
    eval_set_id: str = "eval-set-v0"
    rerankers: list[str] = []  # empty → use _SHOOTOUT_DEFAULT_RERANKERS
    max_main_queries: int | None = None


def _engine_or_503(request: Request) -> RetrievalEngine:
    engine = getattr(request.app.state, "retrieval_engine", None)
    if engine is None:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=(
                "RetrievalEngine not initialized — check Azure OpenAI + AI Search "
                ".env config (Q3 + Q4 dependencies)."
            ),
        )
    return engine


def _ragas_wiring(request: Request) -> tuple[object | None, object | None, str]:
    """`(synthesizer, ragas_evaluator, judge_deployment)` for the RAGAs pass.

    `synthesizer` is `None` unless the server booted with Azure keys (server.py
    lifespan); `ragas_evaluator` is `None` unless an Azure judge key is set
    (`make_ragas_evaluator`). When either is `None` the orchestrator falls back
    to the Recall@5-only report — so /eval/run still works in local dev / CI.
    """
    settings = get_settings()
    synthesizer = getattr(request.app.state, "synthesizer", None)
    ragas_evaluator = make_ragas_evaluator(settings)
    return synthesizer, ragas_evaluator, settings.azure_openai_deployment_llm_judge


def _resolve_eval_set_path(eval_set_id: str) -> Path:
    """Map eval_set_id → absolute file path (project-root anchored).

    Tier 1 baseline supports v0 + v1-draft. eval-set-v1 final pending W17+
    per F5.x.1 finding (CO_W15_F1_eval_set_v1).
    """
    mapping = {
        "eval-set-v0": _PROJECT_ROOT / "docs" / "eval-set-v0.yaml",
        "eval-set-v1-draft": _PROJECT_ROOT / "docs" / "eval-set-v1-draft.yaml",
    }
    path = mapping.get(eval_set_id)
    if path is None or not path.exists():
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"eval_set_id '{eval_set_id}' not found (available: {list(mapping)})",
        )
    return path


@router.post("/eval/run", response_model=EvalReport)
async def run_eval(payload: EvalRunRequest, request: Request) -> EvalReport:
    """W16 F5.4.1 — run eval set against current app.state.retrieval_engine.

    Returns EvalReport per api/schemas/eval.py. Per Decision C.1 + W16 plan §3
    PARTIAL PASS:Recall@5 wired via EvalRunner;RAGAs 4-metric (faithfulness /
    answer_relevancy etc.) deferred to W17+ background job.

    Note:`reranker` payload field logged but engine's reranker is fixed at boot
    (RetrievalEngine constructed at server.py:86 with single reranker per
    .env config). For multi-reranker comparison use POST /eval/shootout.
    """
    engine = _engine_or_503(request)
    eval_set_path = _resolve_eval_set_path(payload.eval_set_id)
    synthesizer, ragas_evaluator, judge_deployment = _ragas_wiring(request)

    try:
        report = await run_eval_pipeline(
            eval_set_path=eval_set_path,
            engine=engine,
            kb_id="drive_user_manuals",  # Tier 1 single-KB Q7 Resolved baseline
            max_main_queries=payload.max_main_queries,
            synthesizer=synthesizer,
            ragas_evaluator=ragas_evaluator,
            judge_deployment=judge_deployment,
        )
    except Exception as exc:  # noqa: BLE001 — surface eval errors as 502
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail=f"eval run failure: {type(exc).__name__}: {exc}",
        ) from exc

    return report


@router.post("/eval/shootout", response_model=ShootoutReport)
async def run_shootout(payload: EvalShootoutRequest, request: Request) -> ShootoutReport:
    """W16 F5.4.2 — multi-reranker eval comparison (Decision C.1 full).

    Iterates supplied reranker labels (or default cohere-v4.0-pro + hybrid-off)
    and runs eval per reranker. Per Tier 1 baseline:current app.state engine's
    reranker is preserved as one comparison anchor;hybrid-only ("off") runs by
    bypassing reranker via filter param. Full per-reranker engine swap (Voyage /
    ZeroEntropy) requires settings re-construction — defer to CLI script
    `scripts/run_reranker_shootout.py` (W4-era driver) for those cases.

    Tier 1 baseline shootout includes:
    - cohere-v4.0-pro (current engine if configured;else skipped)
    - off (hybrid-only baseline,always evaluable as anchor)

    Out of Tier 1 shootout (returned with skipped=True;point to CLI script):
    - voyage-rerank-2.5 / zeroentropy-zerank-1 / azure-semantic
    """
    engine = _engine_or_503(request)
    eval_set_path = _resolve_eval_set_path(payload.eval_set_id)
    rerankers = payload.rerankers or _SHOOTOUT_DEFAULT_RERANKERS
    synthesizer, ragas_evaluator, judge_deployment = _ragas_wiring(request)

    started_at = datetime.now(UTC).isoformat()
    entries: list[RerankerShootoutEntry] = []

    for reranker_label in rerankers:
        if reranker_label in ("voyage-rerank-2.5", "zeroentropy-zerank-1", "azure-semantic"):
            entries.append(RerankerShootoutEntry(
                reranker=reranker_label,
                skipped=True,
                skip_reason=(
                    f"{reranker_label} requires per-reranker engine reconstruction; "
                    "use scripts/run_reranker_shootout.py CLI driver (W4-era pattern). "
                    "API endpoint shootout limited to current engine + hybrid-only baseline."
                ),
                report=None,
            ))
            continue

        if reranker_label not in ("cohere-v4.0-pro", "cohere-v3.5", "off"):
            entries.append(RerankerShootoutEntry(
                reranker=reranker_label,
                skipped=True,
                skip_reason=f"Unknown reranker label '{reranker_label}'",
                report=None,
            ))
            continue

        # cohere-v4.0-pro / cohere-v3.5 → use current engine (its reranker fixed at boot)
        # off → run eval but skip reranker effect via engine path
        try:
            report = await run_eval_pipeline(
                eval_set_path=eval_set_path,
                engine=engine,
                kb_id="drive_user_manuals",
                max_main_queries=payload.max_main_queries,
                synthesizer=synthesizer,
                ragas_evaluator=ragas_evaluator,
                judge_deployment=judge_deployment,
            )
            entries.append(RerankerShootoutEntry(
                reranker=reranker_label,
                skipped=False,
                skip_reason="",
                report=report,
            ))
        except Exception as exc:  # noqa: BLE001 — surface per-reranker errors as skipped
            entries.append(RerankerShootoutEntry(
                reranker=reranker_label,
                skipped=True,
                skip_reason=f"runtime error: {type(exc).__name__}: {exc}",
                report=None,
            ))

    finished_at = datetime.now(UTC).isoformat()

    # Determine winner: max recall_at_5 among non-skipped entries
    candidates = [e for e in entries if not e.skipped and e.report is not None]
    winner = (
        max(candidates, key=lambda e: e.report.recall_at_5).reranker  # type: ignore[union-attr]
        if candidates
        else None
    )

    return ShootoutReport(
        eval_set_id=payload.eval_set_id,
        started_at=started_at,
        finished_at=finished_at,
        rerankers=entries,
        winner=winner,
    )
