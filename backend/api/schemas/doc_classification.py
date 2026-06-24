"""Per-document classification API schemas (W90 P2.3 / ADR-0066 DG1).

Request + response shape for the admin-only
``PATCH /kb/{kb_id}/docs/{doc_id}/classification`` endpoint that tags a document
`internal` / `restricted` (DG1 2-level) and merge-restamps its chunks in the live index.
"""

from __future__ import annotations

from typing import Literal

from pydantic import BaseModel

# DG1 — 2-level classification. A Literal so an invalid value is rejected 422 at the
# API boundary (the index `classification` field itself is a free-form Edm.String).
Classification = Literal["internal", "restricted"]


class ClassificationUpdateRequest(BaseModel):
    """Request body for `PATCH /kb/{kb_id}/docs/{doc_id}/classification`."""

    classification: Classification


class DocClassificationInfo(BaseModel):
    """Response shape — the doc's new classification + how many chunks were restamped."""

    kb_id: str
    doc_id: str
    classification: Classification
    chunks_restamped: int
