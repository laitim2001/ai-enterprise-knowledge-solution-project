"""Document management endpoints (per architecture.md §4.4 #9-12 + §3.3)."""

from fastapi import APIRouter, HTTPException, UploadFile, status

router = APIRouter()


@router.get("/kb/{kb_id}/documents")
async def list_documents(kb_id: str) -> list[dict]:
    """List docs in KB (W2 implementation)."""
    _ = kb_id
    raise HTTPException(
        status_code=status.HTTP_501_NOT_IMPLEMENTED,
        detail="W2 implementation per architecture.md §3.3",
    )


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
