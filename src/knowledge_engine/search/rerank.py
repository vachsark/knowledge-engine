"""
LLM-based reranking of search results.

Uses the configured rerank_model (default: qwen3:8b via Ollama) to score
result relevance against a query. Applied after RRF fusion for the top-K window.

Adapted from vault-search.py --rerank flag and --intent domain hint.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from knowledge_engine.config.settings import Settings
    from knowledge_engine.search.hybrid import SearchResult


@dataclass
class RerankScore:
    doc_id: str
    relevance: float  # 0.0 – 1.0
    reasoning: str | None = None


class LLMReranker:
    """Reranks a list of search results using an LLM relevance judgment.

    The reranker scores each candidate against the query using a structured
    prompt. Scores are blended back into the final ranking using position-aware
    weights (top-5 = 40% reranker, rest = 60% reranker).

    From vault-search.py: supports --intent for domain-specific scoring.
    """

    RERANK_PROMPT = """You are a relevance judge. Given a search query and a document excerpt,
score how relevant the document is to the query on a scale of 0.0 to 1.0.

Query: {query}
Intent domain: {intent}

Document title: {title}
Document excerpt: {excerpt}

Respond with JSON: {{"relevance": 0.0-1.0, "reasoning": "one sentence"}}"""

    def __init__(self, settings: "Settings") -> None:
        self.settings = settings

    def rerank(
        self,
        query: str,
        results: list["SearchResult"],
        intent: str | None = None,
    ) -> list["SearchResult"]:
        """Score and reorder results by LLM relevance judgment.

        Args:
            query: Original search query.
            results: Pre-ranked list from RRF fusion.
            intent: Domain hint (e.g. "machine learning", "finance").

        Returns:
            Reordered list with updated scores reflecting reranker judgment.
        """
        raise NotImplementedError

    def _score_single(
        self, query: str, result: "SearchResult", intent: str | None
    ) -> RerankScore:
        """Call rerank_model to score one result. Parses JSON response."""
        raise NotImplementedError

    def _blend_scores(
        self,
        retrieval_scores: list[float],
        reranker_scores: list[float],
    ) -> list[float]:
        """Apply position-aware blending of retrieval and reranker scores.

        Top-5 positions: 60% retrieval / 40% reranker
        Remaining:       40% retrieval / 60% reranker

        From vault-search memory entry (2026-03-08).
        """
        raise NotImplementedError
