"""W97 / ADR-0069 — coverage-oriented synthesis knob (`enable_complete_coverage`).

乙類 over-summarisation mitigation. Covers plan.md §2 F1-F3 acceptance:
- prompt_builder: knob OFF → system prompt byte-identical pre-W97 (concise + detailed);
  knob ON under detailed → additive COVERAGE rule appended; ON under concise → no-op;
  composes AFTER the optional Rule 9 marker rule.
- EffectiveConfig: enable_complete_coverage resolves per-query > per-DOC > per-KB >
  global Settings (default OFF).
- KbConfig / DocConfig: field round-trips, defaults None.
- synthesizer: threads the resolved knob into build_prompt.

production-preserve: every OFF path is byte-identical to pre-W97.
"""

from __future__ import annotations

from types import SimpleNamespace
from unittest.mock import AsyncMock, patch

import pytest

from api.schemas.doc_config import DocConfig
from api.schemas.kb import KbConfig
from generation.effective_config import PerQueryOverrides, resolve_effective_config
from generation.prompt_builder import (
    _COVERAGE_RULE,
    _MARKER_RULE,
    SYSTEM_PROMPT_CONCISE,
    SYSTEM_PROMPT_DETAILED,
    build_prompt,
)
from generation.synthesizer import Synthesizer
from retrieval.retrieval_engine import RetrievedChunk
from storage.settings import Settings


def _settings(**overrides: object) -> Settings:
    return Settings(_env_file=None, **overrides)  # type: ignore[arg-type]


def _chunk(cid: str = "kb-x_doc-y_chunk-0001") -> RetrievedChunk:
    return RetrievedChunk(
        score=1.0,
        fields={"chunk_id": cid, "chunk_title": "T", "chunk_text": "body", "section_path": []},
    )


def _system(msgs) -> str:  # type: ignore[no-untyped-def]
    return msgs.messages[0]["content"]


# --------------------------------------------------------------------------- #
# T1 — _COVERAGE_RULE constant content
# --------------------------------------------------------------------------- #


def test_coverage_rule_targets_variants_branches_scenarios() -> None:
    low = _COVERAGE_RULE.lower()
    assert "coverage" in low
    assert "variant" in low
    assert "branch" in low
    assert "scenario" in low
    # refines DEDUP so a real branch is never folded as a duplicate
    assert "dedup" in low
    assert "never a duplicate" in low


def test_coverage_rule_forbids_fabrication_and_padding() -> None:
    # W97 iteration 2 — the rule must enumerate variants ONLY when present, and must
    # never invent / pad (reduce the C005-type over-enumeration regression).
    low = _COVERAGE_RULE.lower()
    assert "actually appear" in low  # enumerate only variants that exist
    assert "never invent" in low  # anti-fabrication
    assert "never pad" in low  # anti-padding
    assert "no conditional" in low  # explicit no-variant => single procedure, add nothing


# --------------------------------------------------------------------------- #
# T2 — build_prompt OFF = byte-identical (production-preserve)
# --------------------------------------------------------------------------- #


def test_coverage_off_concise_byte_identical() -> None:
    base = _system(build_prompt("q", [_chunk()]))
    off = _system(build_prompt("q", [_chunk()], complete_coverage=False))
    assert off == base == SYSTEM_PROMPT_CONCISE


def test_coverage_off_detailed_byte_identical() -> None:
    base = _system(build_prompt("q", [_chunk()], detail_level="detailed"))
    off = _system(build_prompt("q", [_chunk()], detail_level="detailed", complete_coverage=False))
    assert off == base == SYSTEM_PROMPT_DETAILED


def test_coverage_default_is_off() -> None:
    # default arg = OFF — omitting the kwarg is byte-identical to passing False.
    assert _system(build_prompt("q", [_chunk()], detail_level="detailed")) == SYSTEM_PROMPT_DETAILED


# --------------------------------------------------------------------------- #
# T3 — build_prompt ON behaviour (detailed appends; concise no-op)
# --------------------------------------------------------------------------- #


def test_coverage_on_detailed_appends_rule() -> None:
    sp = _system(build_prompt("q", [_chunk()], detail_level="detailed", complete_coverage=True))
    assert sp == f"{SYSTEM_PROMPT_DETAILED}\n{_COVERAGE_RULE}"
    assert "COVERAGE" in sp


def test_coverage_on_concise_is_noop() -> None:
    # the rule only refines the detailed full-enumeration prompt; under concise it is a
    # no-op so the 150-word baseline answer shape is untouched.
    sp = _system(build_prompt("q", [_chunk()], detail_level="concise", complete_coverage=True))
    assert sp == SYSTEM_PROMPT_CONCISE
    assert "COVERAGE" not in sp


def test_coverage_composes_after_marker_rule() -> None:
    sp = _system(
        build_prompt(
            "q",
            [_chunk()],
            detail_level="detailed",
            inline_image_markers=True,
            complete_coverage=True,
        )
    )
    assert _MARKER_RULE in sp
    assert _COVERAGE_RULE in sp
    # marker rule (Rule 9) appended first, coverage rule after — no numbering collision.
    assert sp.index(_MARKER_RULE) < sp.index(_COVERAGE_RULE)


# --------------------------------------------------------------------------- #
# T4 — EffectiveConfig four-layer resolution (default OFF)
# --------------------------------------------------------------------------- #


def test_coverage_inherits_global_default_off() -> None:
    eff = resolve_effective_config(_settings(), kb_config=None)
    assert eff.enable_complete_coverage is False


def test_coverage_global_override() -> None:
    eff = resolve_effective_config(_settings(enable_complete_coverage=True), kb_config=None)
    assert eff.enable_complete_coverage is True


def test_coverage_per_kb_overrides_global() -> None:
    eff = resolve_effective_config(_settings(), kb_config=KbConfig(enable_complete_coverage=True))
    assert eff.enable_complete_coverage is True


def test_coverage_per_doc_overrides_kb() -> None:
    eff = resolve_effective_config(
        _settings(),
        kb_config=KbConfig(enable_complete_coverage=False),
        doc_config=DocConfig(enable_complete_coverage=True),
    )
    assert eff.enable_complete_coverage is True


def test_coverage_per_query_overrides_all() -> None:
    eff = resolve_effective_config(
        _settings(enable_complete_coverage=True),
        kb_config=KbConfig(enable_complete_coverage=True),
        per_query=PerQueryOverrides(enable_complete_coverage=False),
    )
    assert eff.enable_complete_coverage is False


def test_schemas_default_none() -> None:
    assert KbConfig().enable_complete_coverage is None
    assert DocConfig().enable_complete_coverage is None


# --------------------------------------------------------------------------- #
# T5 — synthesizer threads the resolved knob into build_prompt
# --------------------------------------------------------------------------- #


@pytest.mark.asyncio
async def test_synthesize_threads_coverage_into_system_prompt() -> None:
    captured: dict = {}

    completion = SimpleNamespace(
        choices=[SimpleNamespace(message=SimpleNamespace(content="answer [chunk-0001]."))],
        usage=SimpleNamespace(prompt_tokens=10, completion_tokens=5),
    )

    async def _create(**kwargs):
        captured["messages"] = kwargs["messages"]
        return completion

    # minimal resolved-config stand-in: synthesize reads both knobs via getattr.
    eff = SimpleNamespace(enable_complete_coverage=True, enable_inline_image_markers=False)

    with patch("generation.synthesizer.AsyncAzureOpenAI") as MockClient:
        instance = MockClient.return_value
        instance.chat = SimpleNamespace(completions=SimpleNamespace(create=_create))
        instance.close = AsyncMock()
        async with Synthesizer(
            endpoint="https://x", api_key="k", api_version="v", deployment="gpt-5-5"
        ) as s:
            await s.synthesize(
                "q",
                [_chunk("kb-x_doc-y_chunk-0001")],
                effective_config=eff,  # type: ignore[arg-type]
                detail_level="detailed",
            )

    assert "COVERAGE" in captured["messages"][0]["content"]


# --------------------------------------------------------------------------- #
# T6 — per-query override wiring (F4 A/B lever): QueryRequest -> PerQueryOverrides
# --------------------------------------------------------------------------- #


def test_query_request_synthesis_overrides_default_none() -> None:
    # chat path sends neither → production-preserve (inherit per-KB / global).
    from api.routes.query import _per_query_from_payload
    from api.schemas.query import QueryRequest

    pq = _per_query_from_payload(QueryRequest(query="q", kb_id="x"))
    assert pq.answer_detail is None
    assert pq.enable_complete_coverage is None


def test_query_request_synthesis_overrides_flow_to_effective_config() -> None:
    # the A/B harness arm B sets both → effective config resolves to detailed + ON.
    from api.routes.query import _per_query_from_payload
    from api.schemas.query import QueryRequest

    pq = _per_query_from_payload(
        QueryRequest(
            query="q", kb_id="x", answer_detail="detailed", enable_complete_coverage=True
        )
    )
    assert pq.answer_detail == "detailed"
    assert pq.enable_complete_coverage is True
    eff = resolve_effective_config(_settings(), kb_config=None, per_query=pq)
    assert eff.answer_detail == "detailed"
    assert eff.enable_complete_coverage is True


@pytest.mark.asyncio
async def test_synthesize_coverage_off_no_rule() -> None:
    captured: dict = {}

    completion = SimpleNamespace(
        choices=[SimpleNamespace(message=SimpleNamespace(content="answer [chunk-0001]."))],
        usage=SimpleNamespace(prompt_tokens=10, completion_tokens=5),
    )

    async def _create(**kwargs):
        captured["messages"] = kwargs["messages"]
        return completion

    eff = SimpleNamespace(enable_complete_coverage=False, enable_inline_image_markers=False)

    with patch("generation.synthesizer.AsyncAzureOpenAI") as MockClient:
        instance = MockClient.return_value
        instance.chat = SimpleNamespace(completions=SimpleNamespace(create=_create))
        instance.close = AsyncMock()
        async with Synthesizer(
            endpoint="https://x", api_key="k", api_version="v", deployment="gpt-5-5"
        ) as s:
            await s.synthesize(
                "q",
                [_chunk("kb-x_doc-y_chunk-0001")],
                effective_config=eff,  # type: ignore[arg-type]
                detail_level="detailed",
            )

    assert captured["messages"][0]["content"] == SYSTEM_PROMPT_DETAILED
