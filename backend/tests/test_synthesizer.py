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


# ----- synthesize_stream (W3 D3 F4) -----


def _stream_chunk(content: str | None = None, usage: tuple[int, int] | None = None) -> SimpleNamespace:
    """Mimic openai ChatCompletionChunk shape."""
    return SimpleNamespace(
        choices=(
            [SimpleNamespace(delta=SimpleNamespace(content=content))]
            if content is not None
            else []
        ),
        usage=(
            SimpleNamespace(prompt_tokens=usage[0], completion_tokens=usage[1])
            if usage is not None
            else None
        ),
    )


class _MockStream:
    """Minimal openai AsyncStream stand-in with __aiter__ + close()."""

    def __init__(self, chunks: list[SimpleNamespace]) -> None:
        self._chunks = chunks
        self.close = AsyncMock()

    def __aiter__(self):
        return self._iterate()

    async def _iterate(self):
        for c in self._chunks:
            yield c


def _make_async_stream(chunks: list[SimpleNamespace]) -> _MockStream:
    return _MockStream(chunks)


@pytest.mark.asyncio
async def test_synthesize_stream_yields_text_deltas_then_result() -> None:
    stream_obj = _make_async_stream([
        _stream_chunk(content="Hello "),
        _stream_chunk(content="[chunk-c1] world"),
        _stream_chunk(usage=(120, 30)),
    ])

    async def _create(**kwargs):
        return stream_obj

    with patch("generation.synthesizer.AsyncAzureOpenAI") as MockClient:
        instance = MockClient.return_value
        instance.chat = SimpleNamespace(completions=SimpleNamespace(create=_create))
        instance.close = AsyncMock()

        async with Synthesizer(
            endpoint="https://x", api_key="k", api_version="v", deployment="gpt-5-5"
        ) as s:
            events = [e async for e in s.synthesize_stream("q", [_chunk("c1")])]

    types = [e["type"] for e in events]
    assert types == ["text-delta", "text-delta", "result"]
    assert events[0]["content"] == "Hello "
    assert events[1]["content"] == "[chunk-c1] world"
    result = events[2]
    assert result["answer"] == "Hello [chunk-c1] world"
    assert result["citation_ids"] == ["c1"]
    assert result["input_tokens"] == 120
    assert result["output_tokens"] == 30
    assert result["refused"] is False
    assert result["deployment"] == "gpt-5-5"


@pytest.mark.asyncio
async def test_synthesize_stream_detects_refusal_phrase() -> None:
    refusal_text = REFUSAL_PHRASE + ". Please add the manual."
    stream_obj = _make_async_stream([
        _stream_chunk(content=refusal_text),
        _stream_chunk(usage=(50, 10)),
    ])

    async def _create(**kwargs):
        return stream_obj

    with patch("generation.synthesizer.AsyncAzureOpenAI") as MockClient:
        instance = MockClient.return_value
        instance.chat = SimpleNamespace(completions=SimpleNamespace(create=_create))
        instance.close = AsyncMock()

        async with Synthesizer(
            endpoint="https://x", api_key="k", api_version="v", deployment="gpt-5-5"
        ) as s:
            events = [e async for e in s.synthesize_stream("q", [_chunk()])]

    assert events[-1]["type"] == "result"
    assert events[-1]["refused"] is True
    assert events[-1]["citation_ids"] == []


@pytest.mark.asyncio
async def test_synthesize_stream_skips_empty_choices_and_continues() -> None:
    """Stream chunks with empty choices (e.g. usage-only final) must not break iteration."""
    stream_obj = _make_async_stream([
        _stream_chunk(content="A"),
        _stream_chunk(),  # empty choices, no content
        _stream_chunk(content="B"),
        _stream_chunk(usage=(10, 2)),
    ])

    async def _create(**kwargs):
        return stream_obj

    with patch("generation.synthesizer.AsyncAzureOpenAI") as MockClient:
        instance = MockClient.return_value
        instance.chat = SimpleNamespace(completions=SimpleNamespace(create=_create))
        instance.close = AsyncMock()

        async with Synthesizer(
            endpoint="https://x", api_key="k", api_version="v", deployment="gpt-5-5"
        ) as s:
            events = [e async for e in s.synthesize_stream("q", [])]

    # Two text-delta + one result; empty-choices and usage-only chunks pass through silently
    text_deltas = [e for e in events if e["type"] == "text-delta"]
    assert [e["content"] for e in text_deltas] == ["A", "B"]
    result = events[-1]
    assert result["answer"] == "AB"


@pytest.mark.asyncio
async def test_synthesize_stream_closes_underlying_stream_on_finally() -> None:
    stream_obj = _make_async_stream([_stream_chunk(content="x")])

    async def _create(**kwargs):
        return stream_obj

    with patch("generation.synthesizer.AsyncAzureOpenAI") as MockClient:
        instance = MockClient.return_value
        instance.chat = SimpleNamespace(completions=SimpleNamespace(create=_create))
        instance.close = AsyncMock()

        async with Synthesizer(
            endpoint="https://x", api_key="k", api_version="v", deployment="gpt-5-5"
        ) as s:
            async for _ in s.synthesize_stream("q", []):
                pass

    stream_obj.close.assert_awaited()


# ---------- W31 F1.5.c citation expansion wire tests ------------------------


def _chunk_with_idx(
    cid: str, doc_id: str, chunk_index: int, chunk_title: str, score: float = 0.9,
) -> RetrievedChunk:
    return RetrievedChunk(
        score=score,
        fields={
            "chunk_id": cid,
            "doc_id": doc_id,
            "chunk_index": chunk_index,
            "chunk_title": chunk_title,
            "chunk_text": f"body for {cid}",
            "section_path": [],
        },
    )


@pytest.mark.asyncio
async def test_synthesize_invokes_citation_expansion_when_enabled() -> None:
    """W31 F1.4.a — synthesizer.synthesize wires expand_citations when not refused
    and `enable_citation_post_hoc_expansion=True` (W31 default)。

    Verifies the expansion module is invoked with (answer_text, citation_ids, chunks)
    and its return value replaces synthesizer's result fields。
    """
    chunks = [
        _chunk_with_idx("0044", "doc-A", 44, "§8 Integration"),
        _chunk_with_idx("0046", "doc-A", 46, "§8.1 Walkthrough"),
    ]

    # Mock OpenAI completion returning a citation of chunk-0044 only
    completion = SimpleNamespace(
        choices=[
            SimpleNamespace(
                message=SimpleNamespace(content="Integration scenarios [chunk-0044]."),
            ),
        ],
        usage=SimpleNamespace(prompt_tokens=10, completion_tokens=5),
    )

    async def _create(**kwargs):
        return completion

    with patch("generation.synthesizer.AsyncAzureOpenAI") as MockClient:
        instance = MockClient.return_value
        instance.chat = SimpleNamespace(completions=SimpleNamespace(create=_create))
        instance.close = AsyncMock()

        async with Synthesizer(
            endpoint="https://x", api_key="k", api_version="v", deployment="gpt-5-5"
        ) as s:
            result = await s.synthesize("show me all integration scenarios", chunks)

    # 0046 expanded into citation_ids by post-hoc expansion (W31 axis 3 B'.c)
    assert "0044" in result.citation_ids
    assert "0046" in result.citation_ids
    assert "[chunk-0044][chunk-0046]" in result.answer


@pytest.mark.asyncio
async def test_synthesize_skips_citation_expansion_when_refused() -> None:
    """W31 F1.4.a — refusal path bypasses expand_citations (no citations to expand)。"""
    chunks = [_chunk_with_idx("0044", "doc-A", 44, "§8.1 Walkthrough")]

    completion = SimpleNamespace(
        choices=[
            SimpleNamespace(message=SimpleNamespace(content=REFUSAL_PHRASE)),
        ],
        usage=SimpleNamespace(prompt_tokens=10, completion_tokens=5),
    )

    async def _create(**kwargs):
        return completion

    with patch("generation.synthesizer.AsyncAzureOpenAI") as MockClient:
        instance = MockClient.return_value
        instance.chat = SimpleNamespace(completions=SimpleNamespace(create=_create))
        instance.close = AsyncMock()

        async with Synthesizer(
            endpoint="https://x", api_key="k", api_version="v", deployment="gpt-5-5"
        ) as s:
            result = await s.synthesize("unanswerable query", chunks)

    assert result.refused is True
    assert result.citation_ids == []  # Refusal phrase has no citation markers
    assert REFUSAL_PHRASE in result.answer
