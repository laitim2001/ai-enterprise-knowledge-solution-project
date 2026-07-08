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

    async def _list(
        kb_id: str,
        doc_id: str,
        top: int = 1000,
        user_principals: list[str] | None = None,
    ) -> list[dict]:
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
        [intro_cit],
        kb_id="kb1",
        engine=engine,
        max_aux_per_citation=2,
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
    engine = _mock_engine(
        {
            "doc-A": [_doc_chunk_dict(5)],
            "doc-B": [_doc_chunk_dict(5)],
        }
    )

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

    async def _list(
        kb_id: str,
        doc_id: str,
        top: int = 1000,
        user_principals: list[str] | None = None,
    ) -> list[dict]:
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
        [cit],
        kb_id="kb1",
        engine=engine,
        max_aux_per_citation=1,
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
        [cit],
        kb_id="kb1",
        engine=engine,
        max_aux_per_citation=5,
        neighbour_window=2,
    )
    checksums = [img.checksum_sha256 for img in result[0].embedded_images]
    assert checksums == ["within-window"]


# ---------- BUG-041 ACL trim (user_principals threading) --------------------


@pytest.mark.asyncio
async def test_attach_forwards_user_principals_to_list_chunks() -> None:
    """BUG-041 — attach must thread user_principals into every engine.list_chunks
    fetch so the neighbour-chunk query is ACL-trimmed (confused-deputy fix).
    Regression guard: dropping the arg silently loses ACL filtering on the
    neighbour-image path."""
    engine = _mock_engine({"doc-A": [_doc_chunk_dict(6, images=[_img_dict("nb")])]})
    cit = _citation(chunk_id="c1", doc_id="doc-A", chunk_index=5)

    await attach_neighbour_images(
        [cit], kb_id="kb1", engine=engine, user_principals=["group:eng", "user:alice"]
    )

    assert engine.list_chunks.await_count >= 1
    for call in engine.list_chunks.await_args_list:
        assert call.kwargs.get("user_principals") == ["group:eng", "user:alice"]


@pytest.mark.asyncio
async def test_attach_admin_forwards_none_principals() -> None:
    """BUG-041 — admin (user_principals=None, the default) forwards None so
    list_chunks applies no ACL filter → admin sees all neighbour images (no
    regression vs pre-fix behaviour)."""
    engine = _mock_engine({"doc-A": [_doc_chunk_dict(6, images=[_img_dict("nb")])]})
    cit = _citation(chunk_id="c1", doc_id="doc-A", chunk_index=5)

    await attach_neighbour_images([cit], kb_id="kb1", engine=engine)

    assert engine.list_chunks.await_count >= 1
    for call in engine.list_chunks.await_args_list:
        assert call.kwargs.get("user_principals") is None


@pytest.mark.asyncio
async def test_attach_respects_acl_trimmed_engine() -> None:
    """BUG-041 — end-to-end intent: when the engine ACL-trims restricted chunks
    (as Azure Search does via _build_acl_filter on allowed_principals), attach
    surfaces only images from chunks the caller's principals can see. Mock engine
    simulates the trim by principal set; the restricted neighbour image must not
    leak to a non-privileged user, and must appear for a privileged one."""
    public_img = _img_dict("public-img")
    restricted_img = _img_dict("restricted-img")

    def _chunks_for(principals: list[str] | None) -> list[dict]:
        # admin (None) or a matching principal sees both neighbour chunks; else
        # the restricted chunk is trimmed (mirrors allowed_principals/any()).
        if principals is None or "group:eng" in principals:
            return [
                _doc_chunk_dict(4, images=[public_img], chunk_id="pub"),
                _doc_chunk_dict(6, images=[restricted_img], chunk_id="restricted"),
            ]
        return [_doc_chunk_dict(4, images=[public_img], chunk_id="pub")]

    engine = MagicMock()

    async def _list(
        kb_id: str,
        doc_id: str,
        top: int = 1000,
        user_principals: list[str] | None = None,
    ) -> list[dict]:
        return _chunks_for(user_principals)

    engine.list_chunks = AsyncMock(side_effect=_list)

    # non-privileged user → restricted neighbour trimmed by engine → only public
    trimmed = await attach_neighbour_images(
        [_citation(chunk_id="c1", doc_id="doc-A", chunk_index=5)],
        kb_id="kb1",
        engine=engine,
        user_principals=["group:sales"],
    )
    got = {img.checksum_sha256 for img in trimmed[0].embedded_images}
    assert got == {"public-img"}, "restricted neighbour image leaked past ACL trim"

    # privileged user → sees both neighbour images
    full = await attach_neighbour_images(
        [_citation(chunk_id="c1", doc_id="doc-A", chunk_index=5)],
        kb_id="kb1",
        engine=engine,
        user_principals=["group:eng"],
    )
    got_full = {img.checksum_sha256 for img in full[0].embedded_images}
    assert got_full == {"public-img", "restricted-img"}


# ---------- BUG-027 section-aware mode (section_path_prefix_depth > 0) -------


def _section_chunk(
    chunk_index: int,
    section_path: list[str],
    images: list[dict] | None = None,
    chunk_id: str | None = None,
) -> dict:
    """A doc-chunk dict with an explicit section_path (default helper uses [])."""
    d = _doc_chunk_dict(chunk_index, images=images, chunk_id=chunk_id)
    d["section_path"] = section_path
    return d


def test_section_mode_attaches_all_same_section_beyond_window() -> None:
    """BUG-027 — §8 intro (chunk 44) surfaces ALL §8.* scenario figures (chunk
    45/47/49/51/53) even though 49/51/53 sit outside the ±3 window. Section
    membership replaces window proximity; CH-011 document-order (chunk_index
    ascending) ordering."""
    intro = _citation(chunk_index=44, section_path=["8. Integration scenarios"])
    sp = ["8. Integration scenarios", "8.x Scenario"]
    doc_chunks = [
        _section_chunk(45, sp, images=[_img_dict("A")]),
        _section_chunk(47, sp, images=[_img_dict("B")]),
        _section_chunk(49, sp, images=[_img_dict("C")]),  # outside window=3
        _section_chunk(51, sp, images=[_img_dict("D")]),  # outside window=3
        _section_chunk(53, sp, images=[_img_dict("E")]),  # outside window=3
    ]
    result = _find_neighbour_images(
        intro,
        doc_chunks,
        max_aux=8,
        window=3,
        section_path_prefix_depth=1,
    )
    assert [img.checksum_sha256 for img in result] == ["A", "B", "C", "D", "E"]


def test_section_mode_excludes_other_sections() -> None:
    """A §3 figure within the window must NOT attach to a §8 citation."""
    intro = _citation(chunk_index=44, section_path=["8. Integration scenarios"])
    doc_chunks = [
        _section_chunk(45, ["8. Integration scenarios", "8.1"], images=[_img_dict("in-8")]),
        # chunk 43 is within ±3 window but a DIFFERENT top-level section:
        _section_chunk(43, ["3. Architecture"], images=[_img_dict("in-3")]),
    ]
    result = _find_neighbour_images(
        intro,
        doc_chunks,
        max_aux=8,
        window=3,
        section_path_prefix_depth=1,
    )
    assert [img.checksum_sha256 for img in result] == ["in-8"]


def test_section_mode_caps_at_max_aux_document_order() -> None:
    """CH-011 / ADR-0048 — the cap takes the EARLIEST document positions
    (chunk_index ascending), NOT the nearest-by-distance siblings, so a capped
    set spans the procedure from its start. The lead sits in the MIDDLE (49) so
    the two orderings diverge: nearest-first would pick chunks 47+51 (distance 2),
    but document-order picks chunks 45+47 (the procedure start)."""
    intro = _citation(chunk_index=49, section_path=["8. Integration scenarios"])
    sp = ["8. Integration scenarios", "8.x"]
    doc_chunks = [
        _section_chunk(53, sp, images=[_img_dict("e")]),  # last
        _section_chunk(45, sp, images=[_img_dict("a")]),  # first
        _section_chunk(51, sp, images=[_img_dict("d")]),  # nearest-first would pick this
        _section_chunk(47, sp, images=[_img_dict("b")]),  # second
    ]
    result = _find_neighbour_images(
        intro,
        doc_chunks,
        max_aux=2,
        window=3,
        section_path_prefix_depth=1,
    )
    # document-order ascending = 45(a),47(b),51(d),53(e); cap 2 → a,b (procedure start)
    assert [img.checksum_sha256 for img in result] == ["a", "b"]


def test_section_mode_requires_citation_section_path_else_window() -> None:
    """depth>0 but the citation has NO section_path → falls through to the
    window-mode path (chunk within ±window still attaches)."""
    cit = _citation(chunk_index=44, section_path=[])
    doc_chunks = [_section_chunk(45, ["8. Integration scenarios"], images=[_img_dict("x")])]
    result = _find_neighbour_images(
        cit,
        doc_chunks,
        max_aux=8,
        window=3,
        section_path_prefix_depth=1,
    )
    assert [img.checksum_sha256 for img in result] == ["x"]


def test_section_mode_citation_shallower_than_depth_returns_empty() -> None:
    """depth=2 but the citation has only a 1-level section_path → no stable
    section key → [] (does NOT silently fall back to window)."""
    cit = _citation(chunk_index=44, section_path=["8. Integration scenarios"])
    doc_chunks = [
        _section_chunk(45, ["8. Integration scenarios", "8.1"], images=[_img_dict("x")]),
    ]
    result = _find_neighbour_images(
        cit,
        doc_chunks,
        max_aux=8,
        window=99,
        section_path_prefix_depth=2,
    )
    assert result == []


def test_section_mode_dedup_against_own() -> None:
    own = _img(checksum="own")
    intro = _citation(
        chunk_index=44,
        section_path=["8. Integration scenarios"],
        embedded_images=[own],
    )
    doc_chunks = [
        _section_chunk(
            45,
            ["8. Integration scenarios", "8.1"],
            images=[_img_dict("own"), _img_dict("new")],
        ),
    ]
    result = _find_neighbour_images(
        intro,
        doc_chunks,
        max_aux=8,
        window=3,
        section_path_prefix_depth=1,
    )
    assert [img.checksum_sha256 for img in result] == ["new"]


@pytest.mark.asyncio
async def test_attach_section_mode_surfaces_all_section_figures() -> None:
    """End-to-end: attach_neighbour_images(section_path_prefix_depth=1) surfaces
    same-section figures across the whole doc, not just within ±window."""
    intro = _citation(
        chunk_id="ch-44",
        doc_id="doc-A",
        chunk_index=44,
        section_path=["8. Integration scenarios"],
    )
    sp = ["8. Integration scenarios", "8.x"]
    doc_chunks = [
        _section_chunk(45, sp, images=[_img_dict("A")]),
        _section_chunk(49, sp, images=[_img_dict("C")]),  # outside window=3
        _section_chunk(53, sp, images=[_img_dict("E")]),  # outside window=3
    ]
    engine = _mock_engine({"doc-A": doc_chunks})
    result = await attach_neighbour_images(
        [intro],
        kb_id="kb1",
        engine=engine,
        max_aux_per_citation=8,
        neighbour_window=3,
        section_path_prefix_depth=1,
    )
    assert [img.checksum_sha256 for img in result[0].embedded_images] == ["A", "C", "E"]


# ---------- CH-012 / ADR-0049 section-fair round-robin distribution ----------


def test_section_mode_round_robin_spreads_budget_across_subsections() -> None:
    """CH-012 / ADR-0049 — the max_aux budget is taken ROUND-ROBIN across the finer
    sub-sections (section_path[:depth+1]) so each step gets representation, instead
    of the earliest sub-section saturating the cap. With 4 sub-sections and
    max_aux=4, one figure from EACH sub-section is taken (not 4 from the first)."""
    intro = _citation(chunk_index=20, section_path=["3 GL03"])
    g111 = ["3 GL03", "3.1.1 Overview"]
    g113 = ["3 GL03", "3.1.3 Create"]
    g114 = ["3 GL03", "3.1.4 Approve"]
    g115 = ["3 GL03", "3.1.5 Post"]
    doc_chunks = [
        _section_chunk(21, g111, images=[_img_dict("a1"), _img_dict("a2")]),
        _section_chunk(25, g113, images=[_img_dict("b1"), _img_dict("b2")]),
        _section_chunk(31, g114, images=[_img_dict("c1")]),
        _section_chunk(34, g115, images=[_img_dict("d1")]),
    ]
    result = _find_neighbour_images(
        intro, doc_chunks, max_aux=4, window=3, section_path_prefix_depth=1
    )
    # pass 1 = one figure from each sub-section, sub-sections in document order
    assert [img.checksum_sha256 for img in result] == ["a1", "b1", "c1", "d1"]


def test_section_mode_round_robin_tail_section_not_starved_bug() -> None:
    """CH-012 — the GL03 bug: the §3.1.1 sub-section (many figures) saturated
    max_aux and starved the procedure tail (§3.1.5 Post got zero figures).
    Round-robin guarantees the tail sub-section a slot within the SAME budget."""
    intro = _citation(chunk_index=20, section_path=["3 GL03"])
    head = ["3 GL03", "3.1.1 Overview"]
    tail = ["3 GL03", "3.1.5 Post"]
    doc_chunks = [
        _section_chunk(21, head, images=[_img_dict(f"h{i}") for i in range(10)]),  # 10 head
        _section_chunk(34, tail, images=[_img_dict("post-fig")]),  # 1 tail
    ]
    result = _find_neighbour_images(
        intro, doc_chunks, max_aux=3, window=3, section_path_prefix_depth=1
    )
    checksums = [img.checksum_sha256 for img in result]
    # round-robin: h0, post-fig, h1 — the tail figure SURVIVES the cap (pre-fix it
    # would be h0,h1,h2 and post-fig starved).
    assert "post-fig" in checksums
    assert len(result) == 3


def test_section_mode_round_robin_within_group_keeps_document_order() -> None:
    """CH-012 — within a single sub-section the round-robin degenerates to the
    prior document-ordered take (production-preserve for single-group sections)."""
    intro = _citation(chunk_index=20, section_path=["3 GL03"])
    one = ["3 GL03", "3.1.1 Overview"]
    doc_chunks = [
        _section_chunk(23, one, images=[_img_dict("third")]),
        _section_chunk(21, one, images=[_img_dict("first")]),
        _section_chunk(22, one, images=[_img_dict("second")]),
    ]
    result = _find_neighbour_images(
        intro, doc_chunks, max_aux=8, window=3, section_path_prefix_depth=1
    )
    assert [img.checksum_sha256 for img in result] == ["first", "second", "third"]


def test_section_mode_round_robin_dedups_shared_figure_first_wins() -> None:
    """CH-012 — a figure that appears in two sub-sections counts once (first
    occurrence in round-robin order wins); the cap is not wasted on the dup."""
    intro = _citation(chunk_index=20, section_path=["3 GL03"])
    g1 = ["3 GL03", "3.1.1 Overview"]
    g2 = ["3 GL03", "3.1.5 Post"]
    doc_chunks = [
        _section_chunk(21, g1, images=[_img_dict("shared"), _img_dict("a-only")]),
        _section_chunk(34, g2, images=[_img_dict("shared"), _img_dict("b-only")]),
    ]
    result = _find_neighbour_images(
        intro, doc_chunks, max_aux=8, window=3, section_path_prefix_depth=1
    )
    checksums = [img.checksum_sha256 for img in result]
    assert checksums.count("shared") == 1  # deduped across sub-sections
    assert set(checksums) == {"shared", "a-only", "b-only"}
