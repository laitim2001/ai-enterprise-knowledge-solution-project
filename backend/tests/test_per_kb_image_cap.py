"""W45 / ADR-0042 — per-KB ingest-time chunker image cap.

Tests the resolution layer (`_select_chunker` + KbConfig field), NOT the chunker
force-split mechanics — those are W44 / ADR-0041 territory, already covered in
`test_chunker.py` (cap=8 vs cap=None). W45's contract is purely: a per-KB
`chunker_max_images_per_chunk` resolves to a chunker carrying that cap (composed
with W44's tested behaviour = force-split at N), and `None` inherits the global
singleton bit-identically.
"""

from __future__ import annotations

from collections.abc import Callable
from typing import cast

from api.routes.documents import _IngestionDeps, _select_chunker
from api.schemas.kb import KbConfig
from indexing.populate import IndexPopulator
from ingestion.chunker.base import Chunker
from ingestion.chunker.layout_aware import LayoutAwareChunker
from ingestion.embedding.base import Embedder


def _deps(
    chunker: Chunker,
    make_chunker: Callable[[int | None], Chunker] | None = None,
) -> _IngestionDeps:
    """Build _IngestionDeps with sentinel embedder/populator (_select_chunker
    only touches `chunker` + `make_chunker`)."""
    sentinel = object()
    return _IngestionDeps(
        embedder=cast(Embedder, sentinel),
        populator=cast(IndexPopulator, sentinel),
        chunker=chunker,
        make_chunker=make_chunker,
    )


def _recording_factory() -> tuple[Callable[[int | None], Chunker], list[int | None]]:
    """A factory that records the caps it was asked for (assert it's/isn't called)."""
    calls: list[int | None] = []

    def factory(cap: int | None) -> Chunker:
        calls.append(cap)
        return LayoutAwareChunker(max_images_per_chunk=cap)

    return factory, calls


def test_none_cap_inherits_global_singleton() -> None:
    """G3 — KB with no per-KB cap (None) → the global-cap singleton, factory untouched."""
    singleton = LayoutAwareChunker(max_images_per_chunk=8)
    factory, calls = _recording_factory()
    deps = _deps(singleton, make_chunker=factory)

    result = _select_chunker(deps, KbConfig(chunker_max_images_per_chunk=None))

    assert result is singleton
    assert calls == []  # inherit path must NOT construct a per-ingest chunker


def test_absent_kb_config_inherits_singleton() -> None:
    """No KB record (kb_config=None) → singleton (pre-W45 behaviour preserved)."""
    singleton = LayoutAwareChunker(max_images_per_chunk=8)
    factory, calls = _recording_factory()
    deps = _deps(singleton, make_chunker=factory)

    assert _select_chunker(deps, None) is singleton
    assert calls == []


def test_per_kb_cap_builds_chunker_with_that_cap() -> None:
    """G2 — a per-KB cap resolves to a chunker carrying that cap (force-split @ N
    via the W44-tested mechanics)."""
    singleton = LayoutAwareChunker(max_images_per_chunk=8)
    factory, calls = _recording_factory()
    deps = _deps(singleton, make_chunker=factory)

    result = _select_chunker(deps, KbConfig(chunker_max_images_per_chunk=3))

    assert result is not singleton
    assert calls == [3]
    assert isinstance(result, LayoutAwareChunker)
    assert result.max_images_per_chunk == 3


def test_factory_absent_falls_back_to_singleton() -> None:
    """make_chunker=None (a test wiring only the singleton) → inherit even if a cap
    is set — safe because the deployed lifespan always wires the factory."""
    singleton = LayoutAwareChunker(max_images_per_chunk=8)
    deps = _deps(singleton, make_chunker=None)

    assert _select_chunker(deps, KbConfig(chunker_max_images_per_chunk=3)) is singleton


def test_kbconfig_backcompat_missing_key_is_none() -> None:
    """G1 — a KB persisted before W45 (JSONB config lacks the key) reconstructs with
    chunker_max_images_per_chunk=None → inherit → bit-identical (production-preserve)."""
    cfg = KbConfig.model_validate({"embedding_model": "text-embedding-3-large"})
    assert cfg.chunker_max_images_per_chunk is None
