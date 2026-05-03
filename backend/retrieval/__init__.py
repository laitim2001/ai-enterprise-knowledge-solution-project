"""Retrieval package (per architecture.md §3.1 + components/C04-retrieval.md).

W2 baseline: hybrid retrieval (Azure AI Search built-in RRF: BM25 + vector).
W3+ adds Cohere Rerank reranker via Reranker Protocol.

- hybrid.py:           Azure AI Search REST POST /docs/search async client
- retrieval_engine.py: public RetrievalEngine.retrieve(query, kb_id, top_k)
"""
