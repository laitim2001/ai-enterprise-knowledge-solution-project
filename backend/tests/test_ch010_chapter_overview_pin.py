"""CH-010 / ADR-0047 — chapter-overview image pin tests (CLAUDE.md §5.6 H6).

`pin_chapter_overview_images` prepends the dominant chapter's §X.1 "Overview"
figures to the FRONT of the lead citation so a procedural answer leads with the
chapter overview/flow diagram (and the images survive the citation-order
`cap_images_per_answer`). Coverage:

- happy path: overview figures pinned to the front of citations[0]
- dominant chapter = most common section_path[:depth] (other chapters ignored)
- no overview chunk in the chapter → unchanged
- empty citations / lead with no doc_id → unchanged (no engine call)
- dedup: an overview image already on the lead citation is not duplicated
- fetch exception → graceful degradation (original citations returned)
"""

from __future__ import annotations

import json
from unittest.mock import AsyncMock, MagicMock

import pytest

from api.schemas.query import Citation, ImageRef
from generation.citation_image_neighbors import pin_chapter_overview_images

CHAPTER = "3 GL03. Processing Journal Vouchers"


def _img(checksum: str) -> ImageRef:
    return ImageRef(
        blob_url=f"https://blob/{checksum}.png",
        alt_text="",
        checksum_sha256=checksum,
        width=800,
        height=400,
    )


def _citation(
    chunk_id: str,
    chunk_index: int,
    section_leaf: str,
    *,
    doc_id: str = "doc-A",
    images: list[ImageRef] | None = None,
) -> Citation:
    return Citation(
        chunk_id=chunk_id,
        doc_id=doc_id,
        doc_title="GL03 Manual",
        doc_format="docx",
        chunk_title=section_leaf,
        chunk_index=chunk_index,
        section_path=[CHAPTER, section_leaf],
        relevance_score=0.8,
        embedded_images=images or [],
    )


def _chunk(chunk_index: int, section_leaf: str, image_checksums: list[str]) -> dict:
    return {
        "chunk_id": f"chunk-{chunk_index}",
        "chunk_index": chunk_index,
        "chunk_title": section_leaf,
        "section_path": [CHAPTER, section_leaf],
        "embedded_images_json": json.dumps(
            [
                {
                    "blob_url": f"https://blob/{c}.png",
                    "alt_text": "",
                    "checksum_sha256": c,
                    "width": 800,
                    "height": 400,
                }
                for c in image_checksums
            ]
        )
        if image_checksums
        else "",
    }


def _engine(doc_chunks: list[dict]) -> MagicMock:
    engine = MagicMock()

    async def _list(kb_id: str, doc_id: str, top: int = 1000) -> list[dict]:
        return doc_chunks

    engine.list_chunks = AsyncMock(side_effect=_list)
    return engine


@pytest.mark.asyncio
async def test_pins_overview_figures_to_lead_front() -> None:
    # Lead citation is a §3.1.3 step (no own images); the §3.1.1 Overview chunk
    # carries the overview diagrams. They must land at the FRONT of citations[0].
    citations = [
        _citation(
            "c-step",
            27,
            "3.1.3 System Instruction for each step",
            images=[_img("step-a"), _img("step-b")],
        ),
        _citation("c-step2", 30, "3.1.3 System Instruction for each step"),
    ]
    engine = _engine(
        [
            _chunk(24, "3.1.1 Overview", ["ov-high-level", "ov-flow"]),
            _chunk(27, "3.1.3 System Instruction for each step", ["step-a", "step-b"]),
        ]
    )
    out = await pin_chapter_overview_images(citations, "kb-1", engine)
    lead_checksums = [i.checksum_sha256 for i in out[0].embedded_images]
    # overview images prepended, then the lead's own images preserved
    assert lead_checksums == ["ov-high-level", "ov-flow", "step-a", "step-b"]
    # other citations untouched
    assert out[1].chunk_id == "c-step2"


@pytest.mark.asyncio
async def test_dominant_chapter_only() -> None:
    # Two chapters cited; §3 GL03 is the majority → only its overview is pinned.
    other = "8 GL08. Other Chapter"
    citations = [
        _citation("c1", 27, "3.1.3 System Instruction for each step"),
        _citation("c2", 28, "3.1.3 System Instruction for each step"),
        Citation(
            chunk_id="c3",
            doc_id="doc-A",
            doc_title="t",
            doc_format="docx",
            chunk_title="8.1.3",
            chunk_index=62,
            section_path=[other, "8.1.3 Step"],
            relevance_score=0.5,
            embedded_images=[],
        ),
    ]
    engine = _engine(
        [
            _chunk(24, "3.1.1 Overview", ["gl03-ov"]),
            {
                "chunk_id": "chunk-59",
                "chunk_index": 59,
                "chunk_title": "8.1.1 Overview",
                "section_path": [other, "8.1.1 Overview"],
                "embedded_images_json": json.dumps(
                    [
                        {
                            "blob_url": "b",
                            "alt_text": "",
                            "checksum_sha256": "gl08-ov",
                            "width": 800,
                            "height": 400,
                        }
                    ]
                ),
            },
        ]
    )
    out = await pin_chapter_overview_images(citations, "kb-1", engine)
    lead_checksums = [i.checksum_sha256 for i in out[0].embedded_images]
    assert lead_checksums == ["gl03-ov"]  # GL03 overview only; GL08 not pinned


@pytest.mark.asyncio
async def test_no_overview_chunk_unchanged() -> None:
    citations = [
        _citation("c1", 27, "3.1.3 System Instruction for each step", images=[_img("step-a")])
    ]
    engine = _engine([_chunk(27, "3.1.3 System Instruction for each step", ["step-a"])])
    out = await pin_chapter_overview_images(citations, "kb-1", engine)
    assert [i.checksum_sha256 for i in out[0].embedded_images] == ["step-a"]


@pytest.mark.asyncio
async def test_empty_citations_no_engine_call() -> None:
    engine = _engine([])
    out = await pin_chapter_overview_images([], "kb-1", engine)
    assert out == []
    engine.list_chunks.assert_not_called()


@pytest.mark.asyncio
async def test_lead_without_doc_id_unchanged() -> None:
    c = _citation("c1", 27, "3.1.3 System Instruction for each step", doc_id="")
    engine = _engine([_chunk(24, "3.1.1 Overview", ["ov"])])
    out = await pin_chapter_overview_images([c], "kb-1", engine)
    assert out == [c]
    engine.list_chunks.assert_not_called()


@pytest.mark.asyncio
async def test_overview_image_already_on_lead_not_duplicated() -> None:
    # Lead already carries the overview image (e.g. retrieved directly) → no dup.
    citations = [_citation("c1", 24, "3.1.1 Overview", images=[_img("ov-flow")])]
    engine = _engine([_chunk(24, "3.1.1 Overview", ["ov-flow"])])
    out = await pin_chapter_overview_images(citations, "kb-1", engine)
    assert [i.checksum_sha256 for i in out[0].embedded_images] == ["ov-flow"]


@pytest.mark.asyncio
async def test_fetch_exception_returns_original() -> None:
    citations = [
        _citation("c1", 27, "3.1.3 System Instruction for each step", images=[_img("step-a")])
    ]
    engine = MagicMock()
    engine.list_chunks = AsyncMock(side_effect=RuntimeError("azure down"))
    out = await pin_chapter_overview_images(citations, "kb-1", engine)
    assert out == citations  # graceful degradation
