"""W5 D1 Path A + W5 D4 Bug I fix — _patch_for_gpt5 wrapper unit tests (per CLAUDE.md §5.6 H6).

Tests the deterministic kwargs translation behavior of the GPT-5 reasoning model
client patcher:
- max_tokens → max_completion_tokens(rename)
- temperature / logprobs / top_logprobs → drop entirely
- max_completion_tokens floor 4096(W5 D4 Bug I fix:ragas faithfulness extraction)
- pass-through of unrelated kwargs(model, messages, response_format etc.)

Live driver flow(actual judge LLM calls)intentionally NOT mocked here — that's
the explicit purpose of F1.7 LIVE smoke。These tests pin the wrapper's
translation contract so future ragas-version upgrades or new GPT-5
reasoning-model param additions surface via test failure cleanly。
"""

from __future__ import annotations

import sys
from pathlib import Path
from unittest.mock import MagicMock

import pytest

_PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
if str(_PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(_PROJECT_ROOT))

from scripts.run_ragas_eval import _patch_for_gpt5  # noqa: E402


def _make_client_with_capture():
    """Build a minimal client whose chat.completions.create captures kwargs."""
    captured: dict = {}

    async def inner_create(**kwargs):
        captured.update(kwargs)
        return MagicMock(name="mock_completion")

    client = MagicMock()
    client.chat = MagicMock()
    client.chat.completions = MagicMock()
    client.chat.completions.create = inner_create
    return client, captured


@pytest.mark.asyncio
async def test_max_tokens_renamed_to_max_completion_tokens() -> None:
    client, captured = _make_client_with_capture()
    _patch_for_gpt5(client)

    await client.chat.completions.create(
        model="gpt-5.4-mini", messages=[], max_tokens=2000,
    )
    assert "max_tokens" not in captured
    # 4096 floor still applies — caller's 2000 below floor → bumped to 4096
    assert captured["max_completion_tokens"] == 4096


@pytest.mark.asyncio
async def test_max_completion_tokens_above_floor_preserved() -> None:
    client, captured = _make_client_with_capture()
    _patch_for_gpt5(client)

    await client.chat.completions.create(
        model="gpt-5.4-mini", messages=[], max_completion_tokens=8000,
    )
    assert captured["max_completion_tokens"] == 8000  # caller value preserved


@pytest.mark.asyncio
async def test_no_max_tokens_floor_applied() -> None:
    client, captured = _make_client_with_capture()
    _patch_for_gpt5(client)

    await client.chat.completions.create(model="gpt-5.4-mini", messages=[])
    # No max_tokens / max_completion_tokens passed → floor still applies(per
    # W5 D4 Bug I fix — ragas internally relies on default which is too small)
    assert captured["max_completion_tokens"] == 4096


@pytest.mark.asyncio
async def test_temperature_dropped() -> None:
    client, captured = _make_client_with_capture()
    _patch_for_gpt5(client)

    await client.chat.completions.create(
        model="gpt-5.4-mini", messages=[], temperature=0.0,
    )
    assert "temperature" not in captured


@pytest.mark.asyncio
async def test_logprobs_and_top_logprobs_dropped() -> None:
    client, captured = _make_client_with_capture()
    _patch_for_gpt5(client)

    await client.chat.completions.create(
        model="gpt-5.4-mini", messages=[],
        logprobs=True, top_logprobs=5,
    )
    assert "logprobs" not in captured
    assert "top_logprobs" not in captured


@pytest.mark.asyncio
async def test_unrelated_kwargs_pass_through() -> None:
    client, captured = _make_client_with_capture()
    _patch_for_gpt5(client)

    response_format = {"type": "json_object"}
    await client.chat.completions.create(
        model="gpt-5.4-mini",
        messages=[{"role": "user", "content": "hi"}],
        response_format=response_format,
        seed=42,
    )
    assert captured["model"] == "gpt-5.4-mini"
    assert captured["messages"] == [{"role": "user", "content": "hi"}]
    assert captured["response_format"] == response_format
    assert captured["seed"] == 42


@pytest.mark.asyncio
async def test_combined_translation_max_tokens_temperature_drop() -> None:
    client, captured = _make_client_with_capture()
    _patch_for_gpt5(client)

    await client.chat.completions.create(
        model="gpt-5.4-mini", messages=[],
        max_tokens=10000,  # rename + above floor → 10000 preserved
        temperature=0.7,   # drop
        logprobs=True,     # drop
    )
    assert captured["max_completion_tokens"] == 10000
    assert "max_tokens" not in captured
    assert "temperature" not in captured
    assert "logprobs" not in captured
