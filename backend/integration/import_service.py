"""Import orchestration (§7 / §8) — provider-agnostic glue between a `SourceConnector`
and EKP's existing ingestion, with the per-doc error model (⑦ / §8.1).

Design rules:
- provider-agnostic: depends only on the `SourceConnector` Protocol + models — no
  SharePoint / Graph import here (so 階段 2 providers reuse it unchanged).
- ingestion core stays untouched (§7.2 鐵律): ingestion is an injected callable
  (`IngestCallable`). The production wiring (F6) adapts it to the existing
  `_run_ingest_pipeline` by writing source ACL as doc-level rows, so the pipeline
  resolves `allowed_principals` via its normal path — zero change to the core.
- per-doc failure does NOT abort the batch (⑦); a failed listing of one container
  does not abort the others. Output is a per-doc summary (§8.2, ADR-0043 shape).
- security: an empty principal set on a document-ACL connector is NOT public
  (§6 risk / F4.5) — such a doc is recorded as failed, never indexed.
"""

from __future__ import annotations

import re
from collections.abc import Callable
from dataclasses import dataclass, field
from typing import Literal, Protocol

import structlog

from integration.connector import ConnectionHandle, SourceConnector
from integration.models import SourceDocumentRef

logger = structlog.get_logger(__name__)

DocStatus = Literal["success", "failed"]

_UNSAFE_DOC_ID = re.compile(r"[^A-Za-z0-9_-]")


def default_doc_id(ref: SourceDocumentRef) -> str:
    """Stable doc id from the source item id → re-import of the same item is a
    replace-in-place (§8.3). Sanitised to the Azure Search key charset."""
    return "sp-" + _UNSAFE_DOC_ID.sub("_", ref.id)


class IngestCallable(Protocol):
    """The ingestion seam. Production wraps EKP's existing pipeline; tests inject a
    fake. Raising signals a per-doc ingest failure."""

    async def __call__(
        self,
        *,
        content_path: object,  # pathlib.Path at runtime; object keeps this Protocol light
        name: str,
        kb_id: str,
        doc_id: str,
        allowed_principals: list[str],
        source_url: str,
    ) -> None: ...


@dataclass(slots=True, frozen=True)
class DocImportResult:
    doc_id: str
    name: str
    status: DocStatus
    error: str | None = None


@dataclass(slots=True)
class ImportSummary:
    """Per-doc import outcome (§8.2). Not all-or-nothing."""

    results: list[DocImportResult] = field(default_factory=list)

    @property
    def total(self) -> int:
        return len(self.results)

    @property
    def succeeded(self) -> int:
        return sum(1 for r in self.results if r.status == "success")

    @property
    def failed(self) -> int:
        return sum(1 for r in self.results if r.status == "failed")


async def import_documents(
    connector: SourceConnector,
    handle: ConnectionHandle,
    *,
    kb_id: str,
    container_ids: list[str],
    ingest: IngestCallable,
    make_doc_id: Callable[[SourceDocumentRef], str] = default_doc_id,
) -> ImportSummary:
    """Import every document in `container_ids` into `kb_id` (§8.3 initial import).

    Per-doc resilience (⑦): a single document's ACL / fetch / ingest failure is
    recorded and skipped; the batch continues. A container whose listing fails is
    recorded and the next container proceeds. Auth / connect failures are fatal and
    surface from `connector.connect()` BEFORE this call (the caller aborts).
    """
    summary = ImportSummary()
    doc_acl = connector.capabilities.acl_granularity == "document"

    for container_id in container_ids:
        try:
            async for ref in connector.list_documents(handle, container_id):
                await _import_one(
                    connector,
                    handle,
                    ref,
                    kb_id=kb_id,
                    doc_acl=doc_acl,
                    ingest=ingest,
                    make_doc_id=make_doc_id,
                    summary=summary,
                )
        except Exception as exc:  # noqa: BLE001 — a container listing failure is per-container
            logger.warning("import_list_failed", container_id=container_id, error=str(exc))
            summary.results.append(
                DocImportResult(container_id, container_id, "failed", f"list_failed: {exc}")
            )

    logger.info(
        "import_complete",
        kb_id=kb_id,
        total=summary.total,
        succeeded=summary.succeeded,
        failed=summary.failed,
    )
    return summary


async def _import_one(
    connector: SourceConnector,
    handle: ConnectionHandle,
    ref: SourceDocumentRef,
    *,
    kb_id: str,
    doc_acl: bool,
    ingest: IngestCallable,
    make_doc_id: Callable[[SourceDocumentRef], str],
    summary: ImportSummary,
) -> None:
    """Import a single document; never raises (per-doc errors are recorded, ⑦)."""
    doc_id = make_doc_id(ref)
    try:
        principals = await connector.get_principals(handle, ref)
        allowed = [p.id for p in principals]
        # §6 / F4.5 — an empty ACL on a document-ACL source is NOT public. Refuse to
        # index it (an empty stamp would fail open to public via the P2.2 filter).
        if doc_acl and not allowed:
            summary.results.append(
                DocImportResult(
                    doc_id,
                    ref.name,
                    "failed",
                    "acl_empty: no resolvable principal — refusing to index as public",
                )
            )
            return

        doc = await connector.fetch_document(handle, ref)
        try:
            await ingest(
                content_path=doc.content_path,
                name=ref.name,
                kb_id=kb_id,
                doc_id=doc_id,
                allowed_principals=allowed,
                source_url=ref.path,
            )
        finally:
            # Always clean up the temp file the connector streamed to (§4.5 / §8.5).
            _cleanup(doc.content_path)
        summary.results.append(DocImportResult(doc_id, ref.name, "success"))
    except Exception as exc:  # noqa: BLE001 — per-doc, don't abort the batch (⑦ / §8.1)
        logger.warning("import_doc_failed", doc_id=doc_id, name=ref.name, error=str(exc))
        summary.results.append(
            DocImportResult(doc_id, ref.name, "failed", f"{type(exc).__name__}: {exc}")
        )


def _cleanup(content_path: object) -> None:
    # content_path is a pathlib.Path; guard defensively (the Protocol types it loosely).
    unlink = getattr(content_path, "unlink", None)
    if callable(unlink):
        try:
            unlink(missing_ok=True)
        except Exception:  # noqa: BLE001 — best-effort temp cleanup
            logger.warning("import_temp_cleanup_failed", path=str(content_path))
