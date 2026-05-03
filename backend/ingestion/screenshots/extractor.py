"""Screenshot extractor (per architecture.md §4.6 + components/C01-ingestion.md §1).

F1 parser already extracts embedded images from .docx via Docling, normalizes them
to PNG bytes, and computes SHA256. The extractor's job here is to augment each
EmbeddedImage with KB/document context and a deterministic blob_path for the
F3 uploader to push into Azure Blob.

Path convention: `{sha256}.{ext}` — flat per-KB-container layout to enable
cross-document SHA256 dedup (architecture.md §3 design decision: "Same logo /
diagram across docs: upload once, reference many"). The architecture.md §4.6
template `{kb_id}/{doc_id}/{img_id}.{ext}` is directional; we collapse {doc_id}
out of the path to honor the dedup semantic. Chunk record stores the resolved
blob_url; the {doc_id} association is preserved at the chunk record level, not
the blob layer.
"""

from __future__ import annotations

from collections.abc import Iterable
from dataclasses import dataclass

from ingestion.parsers.base import EmbeddedImage


@dataclass(slots=True, frozen=True)
class ScreenshotRecord:
    """An embedded image augmented with KB/doc context + deterministic blob_path.

    Fields:
    - image_bytes: PNG-encoded by F1 parser
    - sha256: content hash; identifies the blob uniquely within container
    - blob_path: `{sha256}.{ext}` — flat layout, cross-doc dedup
    - content_type: MIME type for Blob upload metadata
    - alt_text: from Docling caption if any (else "")
    - doc_order: parser doc_order, used by F2 chunker to associate with sections
    - kb_id / doc_id: context for downstream chunk record citations
    """

    image_bytes: bytes
    sha256: str
    blob_path: str
    content_type: str
    alt_text: str
    doc_order: int
    kb_id: str
    doc_id: str
    width: int | None = None  # populated post-upload if probed
    height: int | None = None


class ScreenshotExtractor:
    """Stateless mapper: EmbeddedImage[] + (kb_id, doc_id) -> ScreenshotRecord[]."""

    @staticmethod
    def extract(
        embedded_images: Iterable[EmbeddedImage],
        kb_id: str,
        doc_id: str,
    ) -> list[ScreenshotRecord]:
        records: list[ScreenshotRecord] = []
        for img in embedded_images:
            content_type = _content_type_for_ext(img.ext)
            records.append(
                ScreenshotRecord(
                    image_bytes=img.image_bytes,
                    sha256=img.sha256,
                    blob_path=f"{img.sha256}.{img.ext}",
                    content_type=content_type,
                    alt_text=img.alt_text,
                    doc_order=img.doc_order,
                    kb_id=kb_id,
                    doc_id=doc_id,
                ),
            )
        return records


def _content_type_for_ext(ext: str) -> str:
    """Map ext -> MIME. F1 parser normalizes to PNG; future formats handled here."""
    return {
        "png": "image/png",
        "jpg": "image/jpeg",
        "jpeg": "image/jpeg",
        "gif": "image/gif",
        "webp": "image/webp",
        "svg": "image/svg+xml",
    }.get(ext.lower(), "application/octet-stream")
