"""Feedback endpoint (per architecture.md §4.4 #3)."""

from fastapi import APIRouter, HTTPException, status

from api.schemas.feedback import FeedbackRequest, FeedbackResponse

router = APIRouter()


@router.post("/feedback", response_model=FeedbackResponse)
async def submit_feedback(payload: FeedbackRequest) -> FeedbackResponse:
    """Submit per-answer thumbs / comment feedback.

    W3+ implementation per architecture.md §4.4 + Langfuse correlation.
    """
    _ = payload
    raise HTTPException(
        status_code=status.HTTP_501_NOT_IMPLEMENTED,
        detail="W3 implementation per architecture.md §4.4",
    )
