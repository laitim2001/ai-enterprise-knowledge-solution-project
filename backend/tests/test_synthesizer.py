"""Synthesizer + prompt builder + citation extraction tests (W3 D2 F2)."""

from __future__ import annotations

from types import SimpleNamespace
from unittest.mock import AsyncMock, patch

import pytest

from generation.prompt_builder import REFUSAL_PHRASE, SYSTEM_PROMPT, build_prompt
from generation.synthesizer import Synthesizer, extract_citation_ids
from retrieval.retrieval_engine import RetrievedChunk


def _chunk(cid: str = "c1", title: str = "T", text: str = "body", section=None) -> RetrievedChunk:
    return RetrievedChunk(
        score=0.5,
        fields={
            "chunk_id": cid,
            "chunk_title": title,
            "chunk_text": text,
            "section_path": section or [],
        },
    )


# ----- prompt builder -----


def test_prompt_messages_have_system_and_user_roles() -> None:
    prompt = build_prompt("hi", [_chunk()])
    roles = [m["role"] for m in prompt.messages]
    assert roles == ["system", "user"]


def test_prompt_user_msg_includes_query_and_chunk_id() -> None:
    prompt = build_prompt("how to register asset?", [_chunk(cid="kb-x_doc-y_chunk-0001")])
    user = prompt.messages[1]["content"]
    assert "how to register asset?" in user
    assert "[chunk-kb-x_doc-y_chunk-0001]" in user


def test_prompt_no_chunks_user_msg_says_no_chunks() -> None:
    prompt = build_prompt("anything", [])
    user = prompt.messages[1]["content"]
    assert "(no chunks retrieved)" in user


def test_system_prompt_enforces_refusal_phrase_quoted_literal() -> None:
    assert f'"{REFUSAL_PHRASE}"' in SYSTEM_PROMPT


# ----- citation extractor -----


def test_extract_citation_ids_orders_by_appearance() -> None:
    txt = "first [chunk-c2] then [chunk-c1] then [chunk-c3]"
    assert extract_citation_ids(txt) == ["c2", "c1", "c3"]


def test_extract_citation_ids_dedups_preserving_order() -> None:
    txt = "[chunk-a] sentence [chunk-a] again [chunk-b]"
    assert extract_citation_ids(txt) == ["a", "b"]


def test_extract_citation_ids_no_citations_returns_empty() -> None:
    assert extract_citation_ids("plain text no markers") == []


# ----- Synthesizer (mocked Azure OpenAI) -----


def _mock_completion(content: str, in_tokens: int = 100, out_tokens: int = 30) -> SimpleNamespace:
    return SimpleNamespace(
        choices=[SimpleNamespace(message=SimpleNamespace(content=content))],
        usage=SimpleNamespace(prompt_tokens=in_tokens, completion_tokens=out_tokens),
    )


@pytest.mark.asyncio
async def test_synthesize_returns_answer_and_citations() -> None:
    answer = "Use [chunk-c1] for step 1, then [chunk-c2] for step 2."
    fake = AsyncMock(return_value=_mock_completion(answer, 200, 50))

    with patch("generation.synthesizer.AsyncAzureOpenAI") as MockClient:
        instance = MockClient.return_value
        instance.chat = SimpleNamespace(completions=SimpleNamespace(create=fake))
        instance.close = AsyncMock()

        async with Synthesizer(
            endpoint="https://x", api_key="k", api_version="v", deployment="gpt-5-5"
        ) as s:
            result = await s.synthesize("q", [_chunk("c1"), _chunk("c2")])

    assert result.answer == answer
    assert result.citation_ids == ["c1", "c2"]
    assert result.refused is False
    assert result.input_tokens == 200
    assert result.output_tokens == 50
    assert result.deployment == "gpt-5-5"


@pytest.mark.asyncio
async def test_synthesize_detects_refusal_phrase() -> None:
    answer = f"{REFUSAL_PHRASE}. Please add the relevant manual to the KB."
    fake = AsyncMock(return_value=_mock_completion(answer))

    with patch("generation.synthesizer.AsyncAzureOpenAI") as MockClient:
        instance = MockClient.return_value
        instance.chat = SimpleNamespace(completions=SimpleNamespace(create=fake))
        instance.close = AsyncMock()

        async with Synthesizer(
            endpoint="https://x", api_key="k", api_version="v", deployment="gpt-5-5"
        ) as s:
            result = await s.synthesize("unanswerable", [_chunk()])

    assert result.refused is True
    assert result.citation_ids == []


@pytest.mark.asyncio
async def test_synthesize_passes_temperature_and_deployment_to_chat_completions() -> None:
    captured: dict = {}

    async def _capture(**kwargs):
        captured.update(kwargs)
        return _mock_completion("ok")

    with patch("generation.synthesizer.AsyncAzureOpenAI") as MockClient:
        instance = MockClient.return_value
        instance.chat = SimpleNamespace(completions=SimpleNamespace(create=_capture))
        instance.close = AsyncMock()

        async with Synthesizer(
            endpoint="https://x",
            api_key="k",
            api_version="v",
            deployment="gpt-5-5",
            temperature=0.3,
        ) as s:
            await s.synthesize("q", [_chunk()])

    assert captured["model"] == "gpt-5-5"
    assert captured["temperature"] == 0.3
    assert captured["messages"][0]["role"] == "system"
