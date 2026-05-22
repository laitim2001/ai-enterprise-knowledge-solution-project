"""BUG-010 — `api/routes/query.py` `_proxy_citation_images`.

The chat citation path carries `embedded_images[].blob_url` straight from the
index — a raw private-blob URL the browser can't render. `_proxy_citation_images`
rewrites every URL to the `GET /kb/{kb_id}/screenshots/{blob}` proxy route so
chat referenced-screenshots render through the API.
"""

from __future__ import annotations

from unittest.mock import MagicMock

from api.routes.query import _proxy_citation_images
from api.schemas.query import Citation, ImageRef


def _request(base: str = "http://testserver/") -> MagicMock:
    request = MagicMock()
    request.base_url = base
    return request


def _citation(blob_urls: list[str]) -> Citation:
    return Citation(
        chunk_id="c1",
        doc_id="d1.docx",
        doc_title="Doc 1",
        chunk_title="Section 1",
        chunk_index=0,
        section_path=[],
        relevance_score=0.9,
        embedded_images=[
            ImageRef(
                blob_url=url,
                alt_text="",
                checksum_sha256=f"sha{i}",
                width=0,
                height=0,
            )
            for i, url in enumerate(blob_urls)
        ],
    )


def test_proxy_citation_images_rewrites_blob_url() -> None:
    citations = [_citation(["http://127.0.0.1:10000/devstoreaccount1/cont/abc.png"])]

    out = _proxy_citation_images(citations, _request(), "kb-1")

    assert out[0].embedded_images[0].blob_url == (
        "http://testserver/kb/kb-1/screenshots/abc.png"
    )
    # The non-URL ImageRef fields survive the rewrite untouched.
    assert out[0].embedded_images[0].checksum_sha256 == "sha0"


def test_proxy_citation_images_handles_multiple_images() -> None:
    citations = [
        _citation([
            "http://blob/cont/one.png",
            "http://blob/cont/two.png",
        ]),
    ]

    out = _proxy_citation_images(citations, _request("http://api.example/"), "kbX")

    urls = [img.blob_url for img in out[0].embedded_images]
    assert urls == [
        "http://api.example/kb/kbX/screenshots/one.png",
        "http://api.example/kb/kbX/screenshots/two.png",
    ]


def test_proxy_citation_images_no_images_is_noop() -> None:
    citations = [_citation([])]

    out = _proxy_citation_images(citations, _request(), "kb-1")

    assert out[0].embedded_images == []
    assert out[0].chunk_id == "c1"
