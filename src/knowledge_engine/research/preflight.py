"""
Pre-flight deduplication check before starting a research session.

Searches existing knowledge for semantic overlap with the proposed topic.
If overlap exceeds the similarity threshold, the run can be:
    - Narrowed: topic is scoped to uncovered sub-aspects
    - Aborted:  existing knowledge is sufficient, skip the run entirely

This prevents redundant research and keeps the knowledge store clean.
From vault research pipeline "Pre-Flight" wave (research_pipeline.md).
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from knowledge_engine.config.settings import Settings
    from knowledge_engine.search.hybrid import SearchResult


@dataclass
class PreflightResult:
    """Outcome of the pre-flight dedup check."""

    topic: str
    action: str  # "proceed" | "narrow" | "abort"
    narrowed_topic: str | None = None
    """Scoped topic if action == 'narrow'."""
    overlap_score: float = 0.0
    """Maximum similarity score found against existing knowledge (0–1)."""
    matching_docs: list["SearchResult"] = None  # type: ignore[assignment]

    def __post_init__(self) -> None:
        if self.matching_docs is None:
            self.matching_docs = []


class PreflightCheck:
    """Check for existing knowledge overlap before starting a research run.

    Similarity thresholds (configurable):
        >= 0.90 → abort  (topic well-covered)
        0.70–0.89 → narrow  (partial coverage, scope to gaps)
        < 0.70  → proceed

    The 'narrow' path uses an LLM to identify the un-covered sub-aspects
    of the topic and reformulates the research question accordingly.
    """

    ABORT_THRESHOLD = 0.90
    NARROW_THRESHOLD = 0.70

    def __init__(self, settings: "Settings") -> None:
        self.settings = settings

    def check(self, topic: str) -> PreflightResult:
        """Run pre-flight check against existing knowledge.

        Args:
            topic: The proposed research topic.

        Returns:
            PreflightResult indicating whether to proceed, narrow, or abort.
        """
        raise NotImplementedError

    def _find_coverage_gaps(
        self, topic: str, matching_docs: list["SearchResult"]
    ) -> str:
        """Use an LLM to identify what's NOT already covered about this topic.

        Returns a narrowed topic string focusing on the gaps.
        """
        raise NotImplementedError
