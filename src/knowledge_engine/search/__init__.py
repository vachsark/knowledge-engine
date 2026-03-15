"""
Hybrid search: BM25 sparse retrieval + dense embeddings, fused with RRF.

Adapted from vault-search (vault-search.py hybrid retrieval, ~560ms, no API cost).
Adds: LLM reranking pass, position-aware blending, typed sub-queries.
"""
