"""CH-006 — per-KB answer detail level (concise | detailed).

Covers spec.md §3 acceptance:
- prompt_builder: concise variant keeps the 150-word cap; detailed variant drops it +
  demands full sub-step enumeration; SYSTEM_PROMPT alias pinned to concise; build_prompt
  picks the variant by detail_level; only Rule 3 differs (other rules preserved).
- EffectiveConfig: answer_detail resolves per-query > per-KB > global Settings default.
- KbConfig: answer_detail field round-trips, defaults None, rejects bad values.
- synthesizer: threads detail_level into build_prompt (system message swaps).
"""

from __future__ import annotations

from types import SimpleNamespace
from unittest.mock import AsyncMock, patch

import pytest
from pydantic import ValidationError

from api.schemas.kb import KbConfig
from generation.effective_config import PerQueryOverrides, resolve_effective_config
from generation.prompt_builder import (
    REFUSAL_PHRASE,
    SYSTEM_PROMPT,
    SYSTEM_PROMPT_CONCISE,
    SYSTEM_PROMPT_DETAILED,
    _system_prompt_for,
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


# --------------------------------------------------------------------------- #
# T1 — prompt_builder variants
# --------------------------------------------------------------------------- #


def test_concise_variant_keeps_150_word_cap() -> None:
    assert "150" in SYSTEM_PROMPT_CONCISE


def test_detailed_variant_drops_cap_and_demands_full_enumeration() -> None:
    assert "150" not in SYSTEM_PROMPT_DETAILED
    low = SYSTEM_PROMPT_DETAILED.lower()
    assert "do not summarize" in low
    assert "no word limit" in low


def test_detailed_variant_dedups_repeated_source_headings_bug036() -> None:
    # BUG-036 — the Drive manuals repeat the same step as a process-step-list table
    # entry + a section heading + a caption; the detailed prompt must instruct the LLM
    # to list each distinct step ONCE (fold the summary table into the detailed step)
    # so the answer does not show duplicate step lines. Completeness ("every DISTINCT
    # step") is preserved — only exact/near-exact repeats are folded.
    low = SYSTEM_PROMPT_DETAILED.lower()
    assert "distinct step" in low  # still enumerate every DISTINCT step (completeness)
    assert "only once" in low  # but each distinct step listed only once
    assert "process-step-list" in low  # do not enumerate the summary table separately
    # the over-faithful "merge" prohibition that caused verbatim heading repeats is gone
    assert "compress, merge" not in SYSTEM_PROMPT_DETAILED


def test_detailed_variant_preserves_source_grouping_bug036() -> None:
    # BUG-036 follow-up — the first dedup pass removed duplicates but flattened the
    # procedure into one long decimal list (1.1..1.19), losing the source's nested
    # sub-procedure grouping (GL03-1 > "Create General Journal header" > steps). The
    # prompt must preserve the source hierarchy as nested sub-lists, not flatten it.
    low = SYSTEM_PROMPT_DETAILED.lower()
    assert "grouping" in low  # preserve the source's grouping
    assert "nest" in low  # nest each group's steps as a sub-list
    assert "flatten" in low  # ...and the explicit do-NOT-flatten instruction


def test_detailed_actually_differs_from_concise() -> None:
    # Guards the .replace() match — if _RULE_3_CONCISE stopped matching, the replace
    # would be a no-op and the two prompts would be identical.
    assert SYSTEM_PROMPT_DETAILED != SYSTEM_PROMPT_CONCISE


def test_detailed_only_rule_3_changed_other_rules_preserved() -> None:
    # Citation + refusal + overview rules survive in the detailed variant.
    assert f'"{REFUSAL_PHRASE}"' in SYSTEM_PROMPT_DETAILED
    assert "overview" in SYSTEM_PROMPT_DETAILED.lower()
    assert "[chunk-{chunk_id}]" in SYSTEM_PROMPT_DETAILED


def test_system_prompt_alias_pinned_to_concise() -> None:
    assert SYSTEM_PROMPT == SYSTEM_PROMPT_CONCISE


def test_system_prompt_for_selection() -> None:
    assert _system_prompt_for("detailed") == SYSTEM_PROMPT_DETAILED
    assert _system_prompt_for("concise") == SYSTEM_PROMPT_CONCISE
    assert _system_prompt_for("unknown") == SYSTEM_PROMPT_CONCISE  # safe fallback


def test_build_prompt_default_is_concise() -> None:
    msgs = build_prompt("q", [_chunk()])
    assert msgs.messages[0]["content"] == SYSTEM_PROMPT_CONCISE


def test_build_prompt_detailed_uses_detailed_system_prompt() -> None:
    msgs = build_prompt("q", [_chunk()], detail_level="detailed")
    assert msgs.messages[0]["content"] == SYSTEM_PROMPT_DETAILED


# --------------------------------------------------------------------------- #
# T2 — EffectiveConfig + KbConfig resolution
# --------------------------------------------------------------------------- #


def test_answer_detail_inherits_global_when_kb_none() -> None:
    eff = resolve_effective_config(_settings(), kb_config=None)
    assert eff.answer_detail == "concise"  # class default


def test_answer_detail_global_override() -> None:
    eff = resolve_effective_config(_settings(synthesis_answer_detail="detailed"), kb_config=None)
    assert eff.answer_detail == "detailed"


def test_answer_detail_per_kb_overrides_global() -> None:
    eff = resolve_effective_config(_settings(), kb_config=KbConfig(answer_detail="detailed"))
    assert eff.answer_detail == "detailed"


def test_answer_detail_per_query_overrides_kb() -> None:
    eff = resolve_effective_config(
        _settings(),
        kb_config=KbConfig(answer_detail="detailed"),
        per_query=PerQueryOverrides(answer_detail="concise"),
    )
    assert eff.answer_detail == "concise"


def test_kbconfig_answer_detail_defaults_none_and_validates() -> None:
    assert KbConfig().answer_detail is None
    assert KbConfig(answer_detail="detailed").answer_detail == "detailed"
    with pytest.raises(ValidationError):
        KbConfig(answer_detail="verbose")  # not in Literal


# --------------------------------------------------------------------------- #
# T3 — synthesizer threads detail_level into build_prompt
# --------------------------------------------------------------------------- #


@pytest.mark.asyncio
async def test_synthesize_threads_detail_level_into_system_prompt() -> None:
    captured: dict = {}

    completion = SimpleNamespace(
        choices=[SimpleNamespace(message=SimpleNamespace(content="answer [chunk-0001]."))],
        usage=SimpleNamespace(prompt_tokens=10, completion_tokens=5),
    )

    async def _create(**kwargs):
        captured["messages"] = kwargs["messages"]
        return completion

    with patch("generation.synthesizer.AsyncAzureOpenAI") as MockClient:
        instance = MockClient.return_value
        instance.chat = SimpleNamespace(completions=SimpleNamespace(create=_create))
        instance.close = AsyncMock()
        async with Synthesizer(
            endpoint="https://x", api_key="k", api_version="v", deployment="gpt-5-5"
        ) as s:
            await s.synthesize("q", [_chunk("kb-x_doc-y_chunk-0001")], detail_level="detailed")

    assert captured["messages"][0]["content"] == SYSTEM_PROMPT_DETAILED
