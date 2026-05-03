"""Embedding pipeline package (per architecture.md §3.2 + components/C01-ingestion.md §1).

W2 baseline: AzureOpenAIEmbedder using openai SDK (R8 mitigated 2026-05-03).
- base.py:                 EmbeddingResult dataclass + Embedder Protocol
- azure_openai_embedder.py: AsyncAzureOpenAI + MRL truncate to 1024d + tenacity retry
"""
