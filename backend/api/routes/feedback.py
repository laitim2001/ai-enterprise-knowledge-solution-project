"""Feedback endpoint (per architecture.md §4.4 #3 + §7.4 user feedback loop).

W8 D5 F5.3 implementation: thumbs_up / thumbs_down + comment for a given
trace_id. When the Langfuse client is wired (F5.1), the feedback is forwarded
as a Langfuse `score()` call so it lands on the corresponding trace in the
Langfuse dashboard. When Langfuse is not configured (local dev / CI), the
feedback is still accepted (HTTP 202) and emitted as a structured audit log
event so it is captured for downstream processing — Karpathy §1.2 simplicity-
first: feedback is never silently dropped.
"""

from __future__ import annotations

import uuid

import structlog
from fastapi import APIRouter, status

from api.schemas.feedback import FeedbackRequest, FeedbackResponse
from observability.langfuse_tracer import get_langfuse_client

router = APIRouter()

_logger = structlog.get_logger("ekp.feedback")


@router.post("/feedback", response_model=FeedbackResponse, status_code=status.HTTP_202_ACCEPTED)
async def submit_feedback(payload: FeedbackRequest) -> FeedbackResponse:
    """Submit per-answer thumbs / comment feedback against a trace_id.

    Mapping:
      - rating=thumbs_up  → Langfuse score name="user_feedback" value=1
      - rating=thumbs_down → Langfuse score name="user_feedback" value=-1
    Comment lands in the optional `comment` field of the score record.

    The accepted feedback_id is a fresh uuid4 so the caller can correlate the
    response with downstream Langfuse trace lookups (the Langfuse score id is
    not deterministically returned by the SDK across versions).
    """
    feedback_id = str(uuid.uuid4())
    rating_value = 1 if payload.rating == "thumbs_up" else -1

    client = get_langfuse_client()
    forwarded = False
    if client is not None:
        score = getattr(client, "score", None)
        if callable(score):
            try:
                score(
                    trace_id=payload.trace_id,
                    name="user_feedback",
                    value=rating_value,
                    comment=payload.comment,
                )
                forwarded = True
            except Exception as exc:  # noqa: BLE001 — feedback must never 5xx
                _logger.warning(
                    "feedback_forward_failed",
                    feedback_id=feedback_id,
                    trace_id=payload.trace_id,
                    error=str(exc),
                )

    _logger.info(
        "feedback_received",
        feedback_id=feedback_id,
        trace_id=payload.trace_id,
        rating=payload.rating,
        has_comment=payload.comment is not None,
        forwarded_to_langfuse=forwarded,
    )

    return FeedbackResponse(accepted=True, feedback_id=feedback_id)
