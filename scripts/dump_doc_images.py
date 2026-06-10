"""W59 F1 — dump a document's full image catalog for image-recall GT labeling.

Given a kb_id + doc_id, lists EVERY embedded image in the document — deduped by
content checksum, ordered by `doc_order` (true reading-flow position) — with the
stable identity a labeler needs to fill the eval-set `expected_images` ground truth:

- `checksum_sha256`  — the MATCH KEY (content hash, stable across re-index; what the
                       W59 F3 harness compares against the answer's returned images)
- `doc_order`        — human anchor ("which image, in reading order") to recognise
                       the figure against the source document
- `source_section`   — the section the image belongs to
- `alt_text`         — figure caption / alt text, helps identify the image
- `blob_url`         — open to eyeball the actual image

No embedder / retrieval — uses `HybridSearcher.list_chunks` (kb_id+doc_id filter) +
`parse_embedded_images` only, so Free-tier semantic is NOT consumed.

Without `--doc-id`, lists the KB's documents (doc_id / title / chunk count) so you
can pick the pilot doc first.

Live prerequisites:
- `.env` carries AZURE_SEARCH_ADMIN_KEY
- the target KB index is populated (images re-indexed)

Usage (from project root):
    backend/.venv/Scripts/python.exe -m scripts.dump_doc_images --kb-id <kb>
    backend/.venv/Scripts/python.exe -m scripts.dump_doc_images --kb-id <kb> --doc-id <doc>
"""

from __future__ import annotations

# Use OS trust store (Windows Cert Store) for TLS verification so Ricoh corp
# proxy SSL inspection is honoured. Must run before any ssl/urllib3/httpx import.
import truststore

truststore.inject_into_ssl()

import argparse  # noqa: E402
import asyncio  # noqa: E402
import sys  # noqa: E402
from pathlib import Path  # noqa: E402

# sys.path bootstrap (per W2 D2 convention)
_BACKEND_DIR = Path(__file__).resolve().parent.parent / "backend"
if str(_BACKEND_DIR) not in sys.path:
    sys.path.insert(0, str(_BACKEND_DIR))

import yaml  # noqa: E402  — after sys.path bootstrap

from generation.citation_enrichment import parse_embedded_images  # noqa: E402
from retrieval.hybrid import HybridSearcher  # noqa: E402
from storage.kb_naming import kb_id_to_index_name  # noqa: E402
from storage.settings import get_settings  # noqa: E402

_DEFAULT_TOP_CHUNKS = 5000  # generous cap; a single doc is far smaller


def _default_out(kb_id: str, doc_id: str) -> Path:
    # Filesystem-safe stem from the doc_id (which may contain path-ish chars).
    safe_doc = doc_id.replace("/", "_").replace("\\", "_").replace(":", "_")
    return Path("reports") / f"image_catalog_{kb_id}_{safe_doc}.yaml"


async def _list_documents(searcher: HybridSearcher, kb_id: str) -> int:
    """No --doc-id: print the KB's documents so the user can pick the pilot doc."""
    docs = await searcher.list_documents(kb_id)
    if not docs:
        print(f"No documents found in KB '{kb_id}' (empty / unpopulated index?).")
        return 1
    print(f"\nDocuments in KB '{kb_id}' ({len(docs)}):\n")
    print(f"{'doc_id':<48}  {'chunks':>6}  doc_title")
    print(f"{'-' * 48}  {'-' * 6}  {'-' * 40}")
    for d in sorted(docs, key=lambda x: str(x.get("doc_id", ""))):
        print(
            f"{str(d.get('doc_id', '')):<48}  "
            f"{int(d.get('total_chunks', 0) or 0):>6}  "
            f"{str(d.get('doc_title', ''))}"
        )
    print(
        "\nNext: re-run with --doc-id <doc_id> to dump that document's image catalog.",
    )
    return 0


async def _dump_images(
    searcher: HybridSearcher, kb_id: str, doc_id: str, out_path: Path
) -> int:
    """Dump the document's full image catalog (deduped by checksum, doc_order sorted)."""
    chunks = await searcher.list_chunks(kb_id, doc_id, top=_DEFAULT_TOP_CHUNKS)
    if not chunks:
        print(
            f"No chunks found for doc_id '{doc_id}' in KB '{kb_id}'. "
            "Check the doc_id (run without --doc-id to list documents).",
            file=sys.stderr,
        )
        return 1

    # Aggregate images by content checksum (the match key). One physical image may
    # appear under several chunks (e.g. repeated logo) — collapse to a single entity
    # but keep every position/owning chunk it was seen under for traceability.
    by_checksum: dict[str, dict] = {}
    total_instances = 0
    for ch in chunks:
        chunk_id = str(ch.get("chunk_id", ""))
        imgs = parse_embedded_images(str(ch.get("embedded_images_json", "") or ""))
        for img in imgs:
            total_instances += 1
            key = img.checksum_sha256 or img.blob_url
            rec = by_checksum.get(key)
            if rec is None:
                by_checksum[key] = {
                    "checksum_sha256": img.checksum_sha256,
                    "doc_order": img.doc_order,
                    "source_section": img.source_section,
                    "alt_text": img.alt_text,
                    "blob_url": img.blob_url,
                    "width": img.width,
                    "height": img.height,
                    "owning_chunk_ids": [chunk_id],
                    "all_doc_orders": [img.doc_order],
                }
            else:
                if chunk_id not in rec["owning_chunk_ids"]:
                    rec["owning_chunk_ids"].append(chunk_id)
                if img.doc_order not in rec["all_doc_orders"]:
                    rec["all_doc_orders"].append(img.doc_order)

    images = sorted(
        by_checksum.values(),
        key=lambda r: (r["doc_order"], r["checksum_sha256"]),
    )
    doc_title = str(chunks[0].get("doc_title", ""))

    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(
        yaml.safe_dump(
            {
                "metadata": {
                    "kb_id": kb_id,
                    "doc_id": doc_id,
                    "doc_title": doc_title,
                    "index_name": kb_id_to_index_name(kb_id),
                    "total_chunks": len(chunks),
                    "distinct_images": len(images),
                    "total_image_instances": total_instances,
                    "purpose": (
                        "W59 F1 image catalog for image-recall GT labeling. For each "
                        "eval-set query, fill `ground_truth.expected_images` with the "
                        "`checksum_sha256` values of the images that SHOULD accompany "
                        "the answer (use `doc_order` + `blob_url` + `alt_text` to "
                        "recognise each figure against the source document). The W59 "
                        "F3 harness matches the answer's returned images against these "
                        "checksums to compute image-recall / image-precision."
                    ),
                },
                "images": images,
            },
            sort_keys=False,
            allow_unicode=True,
        ),
        encoding="utf-8",
    )

    print(f"Image catalog written: {out_path}")
    print(
        f"Doc '{doc_id}' ({doc_title}): {len(chunks)} chunks, "
        f"{len(images)} distinct images ({total_instances} instances).",
    )
    print(
        "Next (F2): label each eval-set query's expected_images using these "
        "checksums (doc_order + blob_url to recognise figures).",
    )
    return 0


async def _amain(kb_id: str, doc_id: str | None, out_path: Path | None) -> int:
    settings = get_settings()
    if not settings.azure_search_admin_key:
        print(
            "AZURE_SEARCH_ADMIN_KEY missing in .env — cannot reach the index.",
            file=sys.stderr,
        )
        return 1

    async with HybridSearcher(
        endpoint=settings.azure_search_endpoint,
        admin_key=settings.azure_search_admin_key,
        index_name=kb_id_to_index_name(kb_id),
    ) as searcher:
        if not doc_id:
            return await _list_documents(searcher, kb_id)
        resolved_out = out_path if out_path is not None else _default_out(kb_id, doc_id)
        return await _dump_images(searcher, kb_id, doc_id, resolved_out)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--kb-id", required=True)
    parser.add_argument(
        "--doc-id",
        default=None,
        help="omit to list the KB's documents; provide to dump that doc's image catalog",
    )
    parser.add_argument(
        "--out",
        type=Path,
        default=None,
        help="default: reports/image_catalog_<kb>_<doc>.yaml",
    )
    args = parser.parse_args()
    return asyncio.run(_amain(args.kb_id, args.doc_id, args.out))


if __name__ == "__main__":
    raise SystemExit(main())
