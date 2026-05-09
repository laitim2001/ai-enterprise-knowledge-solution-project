"""Evaluation endpoints (per architecture.md §4.4 #15-16)."""

from fastapi import APIRouter, HTTPException, status
from pydantic import BaseModel

from api.schemas.eval import EvalReport

router = APIRouter()


class EvalRunRequest(BaseModel):
    eval_set_id: str
    llm_model: str = "gpt-5.5"
    reranker: str = "cohere-v4.0-pro"  # ADR-0012 production lock; v3.5 W3 baseline → v4.0-pro upgrade
    enable_crag: bool = True


@router.post("/eval/run", response_model=EvalReport)
async def run_eval(payload: EvalRunRequest) -> EvalReport:
    """Run eval set (W4 implementation per docs/eval-methodology.md)."""
    _ = payload
    raise HTTPException(
        status_code=status.HTTP_501_NOT_IMPLEMENTED,
        detail="W4 implementation per docs/eval-methodology.md",
    )


@router.post("/eval/shootout")
async def run_shootout() -> dict:
    """W4 4-way reranker comparison (Cohere / Voyage / ZeroEntropy / Azure)."""
    raise HTTPException(
        status_code=status.HTTP_501_NOT_IMPLEMENTED,
        detail="W4 reranker shootout per architecture.md §6.1 W4",
    )
