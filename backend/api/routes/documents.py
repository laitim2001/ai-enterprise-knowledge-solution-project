"""Document management endpoints (per architecture.md §4.4 #9-12 + §3.3).

W16 F5.1.1 closure (CO_F3a):
    GET /kb/{kb_id}/documents — replaced 501 stub with Azure AI Search
    aggregation via RetrievalEngine.list_documents (kb_id-scoped chunks
    grouped by doc_id; returns list[DocumentSummary]).

Other endpoints remain 501 stub pending W2 multi-format ingestion +
re-index W17+ scope (out of W16 F5 batch per Path A scope decision).
"""

from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Request, UploadFile, status

from api.schemas.listing import DocumentSummary
from kb_management import KBNotFoundError, KBService, get_kb_service
from retrieval.retrieval_engine import RetrievalEngine

router = APIRouter()

KbServiceDep = Annotated[KBService, Depends(get_kb_service)]


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


async def _verify_kb_or_404(kb_id: str, service: KBService) -> None:
    try:
        await service.get(kb_id)
    except KBNotFoundError as exc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(exc),
        ) from exc


@router.get("/kb/{kb_id}/documents", response_model=list[DocumentSummary])
async def list_documents(
    kb_id: str, request: Request, service: KbServiceDep,
) -> list[DocumentSummary]:
    """W16 F5.1.1 — list docs in KB via Azure AI Search aggregation.

    Verifies kb_id exists via KBService (404 if missing); then aggregates
    chunks in the kb_id-scoped index by doc_id, returning doc-level metadata.
    Empty index → empty list (kb exists but no chunks ingested).
    """
    await _verify_kb_or_404(kb_id, service)

    engine = _engine_or_503(request)
    try:
        rows = await engine.list_documents(kb_id)
    except Exception as exc:  # noqa: BLE001 — surface downstream Azure errors as 502
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail=f"document listing failure: {type(exc).__name__}: {exc}",
        ) from exc

    return [DocumentSummary(**row) for row in rows]


@router.post("/kb/{kb_id}/documents", status_code=status.HTTP_202_ACCEPTED)
async def upload_document(kb_id: str, file: UploadFile) -> dict:
    """Upload + ingest doc (W1 .docx Docling parser; W2 PDF + PPT per OQ-Q1).

    Per OQ-Q1 resolved: format ratio 40% Word + 30% PPT + 30% PDF — all 3 needed by W2.
    """
    _ = kb_id, file
    raise HTTPException(
        status_code=status.HTTP_501_NOT_IMPLEMENTED,
        detail="W1-W2 implementation per architecture.md §3.3 (multi-format ingestion)",
    )


@router.delete("/kb/{kb_id}/documents/{doc_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_document(kb_id: str, doc_id: str) -> None:
    """Delete doc + cleanup chunks/blob (W2 implementation)."""
    _ = kb_id, doc_id
    raise HTTPException(
        status_code=status.HTTP_501_NOT_IMPLEMENTED,
        detail="W2 implementation per architecture.md §3.4",
    )


@router.post("/kb/{kb_id}/documents/{doc_id}/reindex", status_code=status.HTTP_202_ACCEPTED)
async def reindex_document(kb_id: str, doc_id: str) -> dict:
    """Re-index single doc (W2 implementation)."""
    _ = kb_id, doc_id
    raise HTTPException(
        status_code=status.HTTP_501_NOT_IMPLEMENTED,
        detail="W2 implementation per architecture.md §3.4",
    )
