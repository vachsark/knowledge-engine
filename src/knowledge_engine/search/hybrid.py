"""
Hybrid search combining BM25 sparse retrieval with dense embeddings via RRF fusion.

Adapted from vault-search hybrid retrieval (vault-search.py).
Supports typed sub-queries: lex:"term", vec:"concept", hyde:"question".
Position-aware blending: top-5 = 60% retrieval / 40% reranker, rest = 40/60.

References:
    - vault-search.py — BM25 + embedding + RRF pipeline
    - autocontext retrieval — dedup-aware query expansion
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from knowledge_engine.config.settings import Settings


@dataclass
class SearchResult:
    """A single search result with metadata for downstream use."""

    doc_id: str
    title: str
    excerpt: str
    score: float
    source_path: str
    retrieval_scores: dict[str, float] = field(default_factory=dict)
    """Individual scores from each retrieval method before fusion."""


@dataclass
class SearchQuery:
    """Parsed search query, supporting typed sub-queries.

    Examples:
        lex:"transformer attention"     — lexical BM25 only
        vec:"semantic clustering"       — vector embedding only
        hyde:"how does RAG work?"       — HyDE expansion then vector search
        plain text                      — both, fused via RRF
    """

    raw: str
    lex_terms: list[str] = field(default_factory=list)
    vec_terms: list[str] = field(default_factory=list)
    hyde_questions: list[str] = field(default_factory=list)
    intent: str | None = None

    @classmethod
    def parse(cls, raw: str, intent: str | None = None) -> "SearchQuery":
        """Parse typed sub-queries from raw query string."""
        raise NotImplementedError


class HybridSearch:
    """Hybrid BM25 + embedding search with RRF fusion and optional LLM reranking.

    Adapted from vault-search.py. Key differences:
    - Index backed by SQLite (via search/index.py) rather than flat files
    - LLM reranker pass available for top-K results
    - Position-aware score blending for final ranking
    """

    def __init__(self, settings: "Settings") -> None:
        self.settings = settings
        # Lazy-loaded in search()
        self._index: object | None = None
        self._reranker: object | None = None

    def search(
        self,
        query: str,
        top_k: int | None = None,
        rerank: bool = True,
        intent: str | None = None,
    ) -> list[SearchResult]:
        """Run hybrid search and return ranked results.

        Pipeline:
            1. Parse typed sub-queries
            2. BM25 over full-text index
            3. Embedding similarity over vector index
            4. RRF fusion of both ranked lists
            5. (Optional) LLM rerank of top results

        Args:
            query: Raw query string, optionally with typed sub-queries.
            top_k: Number of results to return. Defaults to settings.search_top_k_default.
            rerank: Whether to apply LLM reranking to the fused list.
            intent: Domain hint passed to reranker (e.g. "ml", "finance").

        Returns:
            Ranked list of SearchResult objects.
        """
        raise NotImplementedError

    def _bm25_search(self, terms: list[str], top_k: int) -> list[SearchResult]:
        """BM25 sparse retrieval over keyword index."""
        raise NotImplementedError

    def _embedding_search(self, text: str, top_k: int) -> list[SearchResult]:
        """Dense embedding similarity search over vector index."""
        raise NotImplementedError

    def _rrf_fuse(
        self,
        ranked_lists: list[list[SearchResult]],
        k: int = 60,
    ) -> list[SearchResult]:
        """Reciprocal Rank Fusion over multiple ranked lists.

        RRF score = sum(1 / (k + rank_i)) for each list i.
        Position-aware blending applied after fusion:
            - Top 5: 60% retrieval weight / 40% reranker weight
            - Rest:   40% retrieval weight / 60% reranker weight
        """
        raise NotImplementedError

    def index_document(self, doc_id: str, title: str, content: str, path: str) -> None:
        """Add or update a document in the search index."""
        raise NotImplementedError

    def dedup_check(self, text: str, threshold: float = 0.85) -> list[SearchResult]:
        """Check for near-duplicate documents above similarity threshold.

        Used by research/preflight.py to skip topics already well-covered.
        """
        raise NotImplementedError
