"""Embedder Protocol + EmbeddingResult dataclass (per architecture.md §3.2).

The orchestrator (F5) feeds chunk_text strings to the embedder and gets back
EmbeddingResult per chunk to populate ChunkRecord.embedding[] (1024d) +
log per-chunk token cost via structlog.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Protocol, runtime_checkable


@dataclass(slots=True, frozen=True)
class EmbeddingResult:
    """One embedding output: 1024d vector + token count consumed.

    Token count enables aggregate cost accounting for Langfuse traces +
    structlog event records per architecture.md §3.2 (text-embedding-3-large
    pricing $0.13 / 1M input tokens).
    """

    vector: list[float]  # length 1024 per spec MRL truncate
    input_tokens: int    # billed tokens consumed by Azure OpenAI


@runtime_checkable
class Embedder(Protocol):
    """Async embedder contract — supports parallel batch via embed_batch."""

    embedding_dimension: int

    async def embed(self, text: str) -> EmbeddingResult:
        """Single-text embedding. Useful for query path (single user query)."""
        ...

    async def embed_batch(self, texts: list[str]) -> list[EmbeddingResult]:
        """Parallel batch embedding. Used by F5 orchestrator over chunks of a doc."""
        ...
