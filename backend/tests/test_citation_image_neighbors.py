"""Citation post-process neighbour-image attach tests (W25 F5 D1; CLAUDE.md §5.6 H6).

Coverage:
- attach_neighbour_images(empty) → empty (no engine call)
- attach_neighbour_images(citations with no doc_id) → unchanged
- happy path: cited intro chunk gets neighbour image attached
- batch fetch: citations from same doc → one engine.list_chunks call
- self-chunk excluded (chunk_index == citation.chunk_index)
- window boundary (±N): outside window excluded
- dedup: citation's own image not duplicated, neighbour dup checksum filtered
- cap at max_aux_per_citation
- empty checksum images skipped (defensive)
- per-doc fetch exception → graceful degradation (other docs continue)
- max_aux=0 / window=0 edge cases
- _find_neighbour_images pure unit (no IO)
"""

from __future__ import annotations

import json
from unittest.mock import AsyncMock, MagicMock

import pytest

from api.schemas.query import Citation, ImageRef
from generation.citation_image_neighbors import (
    _find_neighbour_images,
    attach_neighbour_images,
)


# ---------- helpers ----------------------------------------------------------


def _img(checksum: str = "abc123", blob_url: str = "https://blob/x.png") -> ImageRef:
    return ImageRef(
        blob_url=blob_url,
        alt_text="alt",
        checksum_sha256=checksum,
        width=800,
        height=600,
    )


def _citation(
    chunk_id: str = "c1",
    doc_id: str = "doc-A",
    chunk_index: int = 5,
    embedded_images: list[ImageRef] | None = None,
    section_path: list[str] | None = None,
) -> Citation:
    return Citation(
        chunk_id=chunk_id,
        doc_id=doc_id,
        doc_title="title",
        doc_format="docx",
        chunk_title="t",
        chunk_index=chunk_index,
        section_path=section_path or [],
        relevance_score=0.8,
        embedded_images=embedded_images or [],
    )


def _doc_chunk_dict(
    chunk_index: int,
    images: list[dict] | None = None,
    chunk_id: str | None = None,
) -> dict:
    """Build a dict matching `searcher.list_chunks` return shape."""
    return {
        "chunk_id": chunk_id or f"chunk-{chunk_index}",
        "chunk_index": chunk_index,
        "chunk_title": f"title-{chunk_index}",
        "section_path": [],
        "enabled": True,
        "low_value_flag": False,
        "embedded_images_json": json.dumps(images) if images else "",
    }


def _img_dict(
    checksum: str,
    blob_url: str = "https://blob/x.png",
) -> dict:
    return {
        "blob_url": blob_url,
        "alt_text": "alt",
        "checksum_sha256": checksum,
        "width": 800,
        "height": 600,
    }


def _mock_engine(per_doc_chunks: dict[str, list[dict]]) -> MagicMock:
    """Build a MagicMock RetrievalEngine where list_chunks(kb_id, doc_id)
    returns the per-doc list."""
    engine = MagicMock()

    async def _list(kb_id: str, doc_id: str, top: int = 1000) -> list[dict]:
        return per_doc_chunks.get(doc_id, [])

    engine.list_chunks = AsyncMock(side_effect=_list)
    return engine


# ---------- _find_neighbour_images pure unit --------------------------------


def test_find_neighbour_images_basic_one_window() -> None:
    citation = _citation(chunk_index=5)
    doc_chunks = [
        _doc_chunk_dict(4, images=[_img_dict("img-prev")]),
        _doc_chunk_dict(5, images=[_img_dict("img-self")]),  # self → skipped
        _doc_chunk_dict(6, images=[_img_dict("img-next")]),
    ]
    result = _find_neighbour_images(citation, doc_chunks, max_aux=2, window=3)
    checksums = [img.checksum_sha256 for img in result]
    assert checksums == ["img-prev", "img-next"]


def test_find_neighbour_images_skips_outside_window() -> None:
    citation = _citation(chunk_index=10)
    doc_chunks = [
        _doc_chunk_dict(7, images=[_img_dict("too-far-left")]),
        _doc_chunk_dict(11, images=[_img_dict("close-right")]),
        _doc_chunk_dict(14, images=[_img_dict("too-far-right")]),
    ]
    result = _find_neighbour_images(citation, doc_chunks, max_aux=5, window=2)
    checksums = [img.checksum_sha256 for img in result]
    assert checksums == ["close-right"]


def test_find_neighbour_images_caps_at_max_aux() -> None:
    citation = _citation(chunk_index=5)
    doc_chunks = [
        _doc_chunk_dict(4, images=[_img_dict("img-1"), _img_dict("img-2"), _img_dict("img-3")]),
    ]
    result = _find_neighbour_images(citation, doc_chunks, max_aux=2, window=3)
    assert len(result) == 2


def test_find_neighbour_images_dedup_against_own() -> None:
    own = _img(checksum="own-checksum")
    citation = _citation(chunk_index=5, embedded_images=[own])
    doc_chunks = [
        _doc_chunk_dict(6, images=[_img_dict("own-checksum"), _img_dict("new-image")]),
    ]
    result = _find_neighbour_images(citation, doc_chunks, max_aux=5, window=3)
    checksums = [img.checksum_sha256 for img in result]
    assert checksums == ["new-image"]


def test_find_neighbour_images_dedup_across_neighbours() -> None:
    citation = _citation(chunk_index=5)
    doc_chunks = [
        _doc_chunk_dict(4, images=[_img_dict("dup-cksum")]),
        _doc_chunk_dict(6, images=[_img_dict("dup-cksum")]),  # duplicate
    ]
    result = _find_neighbour_images(citation, doc_chunks, max_aux=5, window=3)
    assert len(result) == 1
    assert result[0].checksum_sha256 == "dup-cksum"


def test_find_neighbour_images_skips_empty_checksum() -> None:
    citation = _citation(chunk_index=5)
    doc_chunks = [
        _doc_chunk_dict(4, images=[_img_dict("")]),  # empty checksum
        _doc_chunk_dict(6, images=[_img_dict("valid")]),
    ]
    result = _find_neighbour_images(citation, doc_chunks, max_aux=5, window=3)
    checksums = [img.checksum_sha256 for img in result]
    assert checksums == ["valid"]


def test_find_neighbour_images_zero_max_aux_returns_empty() -> None:
    citation = _citation(chunk_index=5)
    doc_chunks = [_doc_chunk_dict(4, images=[_img_dict("img-1")])]
    assert _find_neighbour_images(citation, doc_chunks, max_aux=0, window=3) == []


def test_find_neighbour_images_zero_window_returns_empty() -> None:
    citation = _citation(chunk_index=5)
    doc_chunks = [_doc_chunk_dict(4, images=[_img_dict("img-1")])]
    assert _find_neighbour_images(citation, doc_chunks, max_aux=5, window=0) == []


def test_find_neighbour_images_handles_non_int_chunk_index() -> None:
    citation = _citation(chunk_index=5)
    doc_chunks = [
        {"chunk_index": "not-an-int", "embedded_images_json": json.dumps([_img_dict("x")])},
        _doc_chunk_dict(6, images=[_img_dict("valid")]),
    ]
    # Bad chunk_index should be skipped, not crash
    result = _find_neighbour_images(citation, doc_chunks, max_aux=5, window=3)
    checksums = [img.checksum_sha256 for img in result]
    assert checksums == ["valid"]


# ---------- attach_neighbour_images async ------------------------------------


@pytest.mark.asyncio
async def test_attach_empty_citations_returns_empty() -> None:
    engine = _mock_engine({})
    result = await attach_neighbour_images([], kb_id="kb1", engine=engine)
    assert result == []
    engine.list_chunks.assert_not_called()


@pytest.mark.asyncio
async def test_attach_citations_without_doc_id_returns_unchanged() -> None:
    cit = _citation(doc_id="")
    engine = _mock_engine({})
    result = await attach_neighbour_images([cit], kb_id="kb1", engine=engine)
    assert result == [cit]
    engine.list_chunks.assert_not_called()


@pytest.mark.asyncio
async def test_attach_happy_path_intro_citation_gets_neighbour_image() -> None:
    """Cited §8 intro chunk_index=44 has no images; §8.1 at chunk_index=45
    has a scenario diagram → image gets attached."""
    intro_cit = _citation(chunk_id="ch-44", doc_id="doc-A", chunk_index=44, embedded_images=[])
    doc_chunks = [
        _doc_chunk_dict(44),  # self (no images anyway)
        _doc_chunk_dict(45, images=[_img_dict("scenario-A-img")]),  # §8.1 Scenario A
        _doc_chunk_dict(47, images=[_img_dict("scenario-B-img")]),  # §8.2 Scenario B
    ]
    engine = _mock_engine({"doc-A": doc_chunks})

    result = await attach_neighbour_images(
        [intro_cit], kb_id="kb1", engine=engine, max_aux_per_citation=2,
    )

    assert len(result) == 1
    assert len(result[0].embedded_images) == 2
    checksums = [img.checksum_sha256 for img in result[0].embedded_images]
    assert checksums == ["scenario-A-img", "scenario-B-img"]


@pytest.mark.asyncio
async def test_attach_multiple_citations_same_doc_batches_fetch() -> None:
    """Two citations from same doc → one engine.list_chunks call, not two."""
    c1 = _citation(chunk_id="ch-1", doc_id="doc-A", chunk_index=5)
    c2 = _citation(chunk_id="ch-2", doc_id="doc-A", chunk_index=10)
    engine = _mock_engine({"doc-A": [_doc_chunk_dict(5)]})

    await attach_neighbour_images([c1, c2], kb_id="kb1", engine=engine)
    assert engine.list_chunks.call_count == 1


@pytest.mark.asyncio
async def test_attach_multiple_citations_different_docs_fetches_each() -> None:
    c1 = _citation(chunk_id="ch-1", doc_id="doc-A", chunk_index=5)
    c2 = _citation(chunk_id="ch-2", doc_id="doc-B", chunk_index=5)
    engine = _mock_engine({
        "doc-A": [_doc_chunk_dict(5)],
        "doc-B": [_doc_chunk_dict(5)],
    })

    await attach_neighbour_images([c1, c2], kb_id="kb1", engine=engine)
    assert engine.list_chunks.call_count == 2


@pytest.mark.asyncio
async def test_attach_citation_with_own_image_is_extended_not_replaced() -> None:
    """Citation's existing embedded_images preserved; neighbour image appended."""
    own_img = _img(checksum="own-cksum")
    cit = _citation(doc_id="doc-A", chunk_index=5, embedded_images=[own_img])
    doc_chunks = [
        _doc_chunk_dict(6, images=[_img_dict("neighbour-cksum")]),
    ]
    engine = _mock_engine({"doc-A": doc_chunks})

    result = await attach_neighbour_images([cit], kb_id="kb1", engine=engine)

    assert len(result) == 1
    assert len(result[0].embedded_images) == 2
    checksums = [img.checksum_sha256 for img in result[0].embedded_images]
    assert checksums == ["own-cksum", "neighbour-cksum"]


@pytest.mark.asyncio
async def test_attach_no_neighbours_returns_citation_unchanged() -> None:
    cit = _citation(doc_id="doc-A", chunk_index=5)
    # Only self chunk + far chunk (outside default window=3)
    doc_chunks = [
        _doc_chunk_dict(5),
        _doc_chunk_dict(50, images=[_img_dict("far-away")]),
    ]
    engine = _mock_engine({"doc-A": doc_chunks})

    result = await attach_neighbour_images([cit], kb_id="kb1", engine=engine)
    assert result == [cit]


@pytest.mark.asyncio
async def test_attach_doc_fetch_failure_falls_back_gracefully() -> None:
    """One doc fetch raises → citation from that doc passes through unchanged;
    other citations from successful docs still get augmented."""
    cit_a = _citation(chunk_id="ch-A", doc_id="doc-A", chunk_index=5)
    cit_b = _citation(chunk_id="ch-B", doc_id="doc-B", chunk_index=5)

    async def _list(kb_id: str, doc_id: str, top: int = 1000) -> list[dict]:
        if doc_id == "doc-A":
            raise RuntimeError("Azure Search timeout")
        return [_doc_chunk_dict(6, images=[_img_dict("b-img")])]

    engine = MagicMock()
    engine.list_chunks = AsyncMock(side_effect=_list)

    result = await attach_neighbour_images([cit_a, cit_b], kb_id="kb1", engine=engine)

    # doc-A citation passes through unchanged
    assert result[0].embedded_images == []
    # doc-B citation gets the neighbour image
    assert len(result[1].embedded_images) == 1
    assert result[1].embedded_images[0].checksum_sha256 == "b-img"


@pytest.mark.asyncio
async def test_attach_respects_max_aux_per_citation_setting() -> None:
    cit = _citation(doc_id="doc-A", chunk_index=5)
    doc_chunks = [
        _doc_chunk_dict(6, images=[_img_dict(f"img-{i}") for i in range(5)]),
    ]
    engine = _mock_engine({"doc-A": doc_chunks})

    result = await attach_neighbour_images(
        [cit], kb_id="kb1", engine=engine, max_aux_per_citation=1,
    )
    assert len(result[0].embedded_images) == 1


@pytest.mark.asyncio
async def test_attach_respects_neighbour_window_setting() -> None:
    cit = _citation(doc_id="doc-A", chunk_index=5)
    doc_chunks = [
        _doc_chunk_dict(6, images=[_img_dict("within-window")]),
        _doc_chunk_dict(15, images=[_img_dict("outside-tight-window")]),
    ]
    engine = _mock_engine({"doc-A": doc_chunks})

    result = await attach_neighbour_images(
        [cit], kb_id="kb1", engine=engine,
        max_aux_per_citation=5, neighbour_window=2,
    )
    checksums = [img.checksum_sha256 for img in result[0].embedded_images]
    assert checksums == ["within-window"]
