"""Per-document config CRUD endpoints (W57 / ADR-0050 — platform P2a / Gap A).

Manages the per-DOCUMENT `DocConfig` overlay (post-retrieval knobs) keyed by
``(kb_id, doc_id)``, backed by the `DocConfigStore` wired on app.state. The query
pipeline reads these via the dominant-doc overlay (per ADR-0050); this surface lets
a KB owner set / inspect / clear them (the P2b UI consumes these endpoints).

    GET    /kb/{kb_id}/docs/{doc_id}/config   → stored DocConfig (empty if none)
    PUT    /kb/{kb_id}/docs/{doc_id}/config   → upsert, returns stored DocConfig
    DELETE /kb/{kb_id}/docs/{doc_id}/config   → 204 (idempotent)
    GET    /kb/{kb_id}/doc-configs            → {doc_id: DocConfig} for the KB

The list path is ``/kb/{kb_id}/doc-configs`` (not ``/kb/{kb_id}/docs/configs``)
deliberately — the latter would collide with the documents route
``GET /kb/{kb_id}/docs/{doc_id}`` (matching ``doc_id="configs"``).

``kb_id`` existence is validated (404). ``doc_id`` is a free-form key in the MVP
(no documents persistence table — per ADR-0050), so an orphan config (doc deleted)
is surfaced by the list endpoint, not blocked here.
"""

from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Request, status

from api.schemas.doc_config import DocConfig
from kb_management import KBNotFoundError, KBService, get_kb_service
from kb_management.doc_config_store import DocConfigStore

router = APIRouter()

KbServiceDep = Annotated[KBService, Depends(get_kb_service)]


async def _verify_kb(service: KBService, kb_id: str) -> None:
    """404 when the KB has no metadata row (per-doc config needs a real KB)."""
    try:
        await service.get(kb_id)
    except KBNotFoundError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc


def _store(request: Request) -> DocConfigStore:
    store: DocConfigStore | None = getattr(request.app.state, "doc_config_store", None)
    if store is None:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="per-document config store not initialized",
        )
    return store


@router.get("/kb/{kb_id}/docs/{doc_id}/config", response_model=DocConfig)
async def get_doc_config(
    kb_id: str,
    doc_id: str,
    request: Request,
    service: KbServiceDep,
) -> DocConfig:
    """Return the stored per-doc config, or an all-`None` `DocConfig` (= inherit
    per-KB) when none is set."""
    await _verify_kb(service, kb_id)
    config = await _store(request).get(kb_id, doc_id)
    return config or DocConfig()


@router.put("/kb/{kb_id}/docs/{doc_id}/config", response_model=DocConfig)
async def put_doc_config(
    kb_id: str,
    doc_id: str,
    config: DocConfig,
    request: Request,
    service: KbServiceDep,
) -> DocConfig:
    """Upsert the per-doc config for ``(kb_id, doc_id)``; returns the stored config."""
    await _verify_kb(service, kb_id)
    return await _store(request).upsert(kb_id, doc_id, config)


@router.delete("/kb/{kb_id}/docs/{doc_id}/config", status_code=status.HTTP_204_NO_CONTENT)
async def delete_doc_config(
    kb_id: str,
    doc_id: str,
    request: Request,
    service: KbServiceDep,
) -> None:
    """Delete the per-doc config (idempotent — 204 whether or not a row existed)."""
    await _verify_kb(service, kb_id)
    await _store(request).delete(kb_id, doc_id)


@router.get("/kb/{kb_id}/doc-configs", response_model=dict[str, DocConfig])
async def list_doc_configs(
    kb_id: str,
    request: Request,
    service: KbServiceDep,
) -> dict[str, DocConfig]:
    """Return ``{doc_id: DocConfig}`` for every per-doc config under the KB (P2b UI
    overview + orphan-config surfacing per ADR-0050)."""
    await _verify_kb(service, kb_id)
    return await _store(request).list_for_kb(kb_id)
