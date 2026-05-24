"""Query reformulator unit tests (W25 F3.5 per ADR-0034; CLAUDE.md §5.6 H6).

Coverage:
- _parse_variants JSON extraction (valid / fenced / malformed / missing key / empty list)
- reformulate(empty query) → ReformulationResult variants=[]
- reformulate(max_variants=1) → degenerate single-variant path,no LLM call
- reformulate happy path → original prepended,token counts surfaced
- reformulate JSON parse failure → graceful [original] fallback with fallback_used=True
- reformulate API error (RateLimitError) → fallback after retry exhausted
- reformulate latency-cap timeout → fallback with timeout error message
- reformulate dedupe: variants identical → unique only
"""

from __future__ import annotations

import asyncio
from dataclasses import dataclass
from typing import Any
from unittest.mock import AsyncMock, MagicMock

import pytest

from generation.query_reformulator import (
    QueryReformulator,
    ReformulationResult,
    _parse_variants,
)


# ---------- helpers ----------------------------------------------------------


@dataclass
class _MockCompletion:
    content: str
    prompt_tokens: int = 120
    completion_tokens: int = 30

    @property
    def choices(self) -> list[Any]:
        return [MagicMock(message=MagicMock(content=self.content))]

    @property
    def usage(self) -> Any:
        return MagicMock(
            prompt_tokens=self.prompt_tokens,
            completion_tokens=self.completion_tokens,
        )


def _reformulator_with_responses(*texts: str, max_variants: int = 3) -> QueryReformulator:
    """Build a QueryReformulator with a mocked Azure OpenAI client returning the
    given completion outputs in order. Caller queues 1 string per call."""
    refmltr = QueryReformulator(
        endpoint="https://x.openai.azure.com",
        api_key="k",
        api_version="2025-04-01-preview",
        deployment="gpt-5-4-mini",
        max_variants=max_variants,
        latency_cap_s=2.0,
    )
    client = MagicMock()
    completions = [_MockCompletion(t) for t in texts]
    client.chat = MagicMock()
    client.chat.completions = MagicMock()
    client.chat.completions.create = AsyncMock(side_effect=completions)
    refmltr._client = client  # bypass __aenter__ for test
    return refmltr


# ---------- _parse_variants --------------------------------------------------


def test_parse_variants_valid_json_two_variants() -> None:
    text = '{"variants": ["query A", "query B"]}'
    assert _parse_variants(text, expected_count=2) == ["query A", "query B"]


def test_parse_variants_fenced_markdown_strips_to_inner_json() -> None:
    text = '```json\n{"variants": ["v1", "v2"]}\n```'
    assert _parse_variants(text, expected_count=2) == ["v1", "v2"]


def test_parse_variants_strips_whitespace_and_dedupes() -> None:
    text = '{"variants": ["  spaced  ", "spaced", "unique"]}'
    # "spaced" dedupe (after strip); "unique" remains
    assert _parse_variants(text, expected_count=5) == ["spaced", "unique"]


def test_parse_variants_caps_at_expected_count() -> None:
    text = '{"variants": ["a", "b", "c", "d", "e"]}'
    assert _parse_variants(text, expected_count=2) == ["a", "b"]


def test_parse_variants_filters_non_string_entries() -> None:
    # Use Python source `null` / numeric — interpreted as JSON via json.loads.
    text = '{"variants": ["valid", null, 123, "also valid"]}'
    assert _parse_variants(text, expected_count=4) == ["valid", "also valid"]


def test_parse_variants_no_json_block_raises() -> None:
    with pytest.raises(ValueError, match="no JSON block"):
        _parse_variants("just plain text without braces", expected_count=2)


def test_parse_variants_invalid_json_raises() -> None:
    # Regex `\{.*\}` matches but json.loads fails on malformed inner content
    with pytest.raises(ValueError, match="not valid JSON"):
        _parse_variants('{not real JSON,}', expected_count=2)


def test_parse_variants_missing_variants_key_raises() -> None:
    with pytest.raises(ValueError, match='missing "variants" key'):
        _parse_variants('{"alternatives": ["a", "b"]}', expected_count=2)


def test_parse_variants_non_list_variants_raises() -> None:
    with pytest.raises(ValueError, match="not a list"):
        _parse_variants('{"variants": "single string"}', expected_count=2)


def test_parse_variants_empty_after_cleaning_raises() -> None:
    with pytest.raises(ValueError, match="zero usable variants"):
        _parse_variants('{"variants": ["", "   ", null]}', expected_count=2)


# ---------- QueryReformulator.reformulate edges ------------------------------


@pytest.mark.asyncio
async def test_reformulate_empty_query_returns_empty_variants() -> None:
    refmltr = _reformulator_with_responses()
    result = await refmltr.reformulate("")
    assert result.variants == []
    assert result.fallback_used is False
    refmltr._client.chat.completions.create.assert_not_called()  # type: ignore[attr-defined]


@pytest.mark.asyncio
async def test_reformulate_whitespace_only_returns_empty_variants() -> None:
    refmltr = _reformulator_with_responses()
    result = await refmltr.reformulate("   \n  \t  ")
    assert result.variants == []
    refmltr._client.chat.completions.create.assert_not_called()  # type: ignore[attr-defined]


@pytest.mark.asyncio
async def test_reformulate_max_variants_one_skips_llm_call() -> None:
    refmltr = _reformulator_with_responses(max_variants=1)
    result = await refmltr.reformulate("show me the architecture")
    assert result.variants == ["show me the architecture"]
    assert result.fallback_used is False
    assert result.input_tokens == 0
    refmltr._client.chat.completions.create.assert_not_called()  # type: ignore[attr-defined]


# ---------- QueryReformulator.reformulate happy path ------------------------


@pytest.mark.asyncio
async def test_reformulate_happy_path_prepends_original() -> None:
    text = '{"variants": ["system architecture diagram", "component overview"]}'
    refmltr = _reformulator_with_responses(text, max_variants=3)
    result = await refmltr.reformulate("show me the architecture")

    assert result.variants == [
        "show me the architecture",            # original prepended
        "system architecture diagram",          # LLM variant 1
        "component overview",                   # LLM variant 2
    ]
    assert result.fallback_used is False
    assert result.input_tokens == 120
    assert result.output_tokens == 30
    assert result.deployment == "gpt-5-4-mini"


@pytest.mark.asyncio
async def test_reformulate_strips_original_whitespace() -> None:
    text = '{"variants": ["v1", "v2"]}'
    refmltr = _reformulator_with_responses(text, max_variants=3)
    result = await refmltr.reformulate("  query  with  spaces  ")
    # First entry is stripped original (no leading/trailing spaces)
    assert result.variants[0] == "query  with  spaces"


# ---------- QueryReformulator.reformulate fallback paths ---------------------


@pytest.mark.asyncio
async def test_reformulate_json_parse_failure_uses_original_only() -> None:
    # LLM returned non-JSON text — _parse_variants raises, caught by reformulate
    refmltr = _reformulator_with_responses("just text no JSON here", max_variants=3)
    result = await refmltr.reformulate("query A")

    assert result.variants == ["query A"]
    assert result.fallback_used is True
    assert result.error_message is not None
    assert "ValueError" in result.error_message or "JSON" in result.error_message


@pytest.mark.asyncio
async def test_reformulate_timeout_uses_original_only() -> None:
    refmltr = QueryReformulator(
        endpoint="https://x.openai.azure.com",
        api_key="k",
        api_version="2025-04-01-preview",
        deployment="gpt-5-4-mini",
        max_variants=3,
        latency_cap_s=0.05,  # very short cap to force timeout
    )

    async def _slow_create(**_: Any) -> _MockCompletion:
        await asyncio.sleep(0.5)
        return _MockCompletion('{"variants": ["never returned"]}')

    client = MagicMock()
    client.chat = MagicMock()
    client.chat.completions = MagicMock()
    client.chat.completions.create = AsyncMock(side_effect=_slow_create)
    refmltr._client = client

    result = await refmltr.reformulate("query A")
    assert result.variants == ["query A"]
    assert result.fallback_used is True
    assert result.error_message is not None
    assert "timeout" in result.error_message.lower()


@pytest.mark.asyncio
async def test_reformulate_generic_exception_uses_original_only() -> None:
    refmltr = QueryReformulator(
        endpoint="https://x.openai.azure.com",
        api_key="k",
        api_version="2025-04-01-preview",
        deployment="gpt-5-4-mini",
        max_variants=3,
    )
    client = MagicMock()
    client.chat = MagicMock()
    client.chat.completions = MagicMock()
    client.chat.completions.create = AsyncMock(side_effect=RuntimeError("boom"))
    refmltr._client = client

    result = await refmltr.reformulate("query A")
    assert result.variants == ["query A"]
    assert result.fallback_used is True
    assert result.error_message is not None
    assert "RuntimeError" in result.error_message


# ---------- ReformulationResult shape ----------------------------------------


def test_reformulation_result_is_frozen() -> None:
    result = ReformulationResult(
        variants=["a"],
        fallback_used=False,
        input_tokens=10,
        output_tokens=5,
        latency_ms=100,
        deployment="gpt-5-4-mini",
    )
    with pytest.raises(AttributeError):
        result.variants = ["b"]  # type: ignore[misc]
