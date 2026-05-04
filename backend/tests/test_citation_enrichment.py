"""Citation enrichment + embedded image parsing tests (W3 D2 F3)."""

from __future__ import annotations

import json

from generation.citation_enrichment import build_citations, parse_embedded_images
from retrieval.retrieval_engine import RetrievedChunk


def _chunk(cid: str, **fields_overrides) -> RetrievedChunk:
    fields: dict = {
        "chunk_id": cid,
        "doc_id": "doc-1",
        "doc_title": "Doc One",
        "chunk_title": "Section",
        "chunk_index": 0,
        "section_path": ["A", "B"],
        "embedded_images_json": "[]",
    }
    fields.update(fields_overrides)
    return RetrievedChunk(score=0.42, fields=fields)


# ----- parse_embedded_images -----


def test_parse_empty_string_returns_empty() -> None:
    assert parse_embedded_images("") == []


def test_parse_empty_array_returns_empty() -> None:
    assert parse_embedded_images("[]") == []


def test_parse_valid_array_returns_imagerefs() -> None:
    payload = json.dumps([
        {
            "blob_url": "https://x/blob/a.png",
            "alt_text": "Diagram",
            "checksum_sha256": "deadbeef",
            "width": 800,
            "height": 600,
        }
    ])
    images = parse_embedded_images(payload)
    assert len(images) == 1
    assert images[0].blob_url == "https://x/blob/a.png"
    assert images[0].width == 800


def test_parse_malformed_json_returns_empty_no_raise() -> None:
    assert parse_embedded_images("not-json") == []


def test_parse_non_array_top_level_returns_empty() -> None:
    assert parse_embedded_images('{"a": 1}') == []


# ----- build_citations -----


def test_build_citations_preserves_order_from_citation_ids() -> None:
    chunks = [_chunk("c1"), _chunk("c2"), _chunk("c3")]
    out = build_citations(["c2", "c3", "c1"], chunks)
    assert [c.chunk_id for c in out] == ["c2", "c3", "c1"]


def test_build_citations_skips_unknown_chunk_ids() -> None:
    chunks = [_chunk("c1")]
    out = build_citations(["c1", "ghost-id"], chunks)
    assert [c.chunk_id for c in out] == ["c1"]


def test_build_citations_populates_fields_from_retrieved() -> None:
    chunks = [_chunk("c1", doc_id="d-9", doc_title="Manual 9", section_path=["X"])]
    out = build_citations(["c1"], chunks)
    assert out[0].doc_id == "d-9"
    assert out[0].doc_title == "Manual 9"
    assert out[0].section_path == ["X"]
    assert out[0].relevance_score == 0.42


def test_build_citations_empty_list_returns_empty() -> None:
    assert build_citations([], [_chunk("c1")]) == []


def test_build_citations_with_real_image_json() -> None:
    img_json = json.dumps([
        {
            "blob_url": "https://b/img.png",
            "alt_text": "fig 1",
            "checksum_sha256": "abc",
            "width": 100,
            "height": 50,
        }
    ])
    chunks = [_chunk("c1", embedded_images_json=img_json)]
    out = build_citations(["c1"], chunks)
    assert len(out[0].embedded_images) == 1
    assert out[0].embedded_images[0].blob_url == "https://b/img.png"
