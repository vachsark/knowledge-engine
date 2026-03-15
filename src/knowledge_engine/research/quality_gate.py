"""
Quality gate for research output.

Two-part gate adapted from:
    - vault research pipeline: quality gate with bounce-back
    - autocontext backpressure gate: minimum knowledge delta check

A run passes if ALL conditions hold:
    1. Rubric score >= settings.gate_pass_threshold (default 0.70)
    2. Knowledge delta >= settings.backpressure_min_delta (default 0.005)
    3. No critical weaknesses flagged by weakness.py

Failed runs bounce back to synthesizer for refinement (max settings.gate_max_bounces).
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from knowledge_engine.config.settings import Settings
    from knowledge_engine.evaluation.rubric import RubricScore


@dataclass
class GateDecision:
    """Result of a quality gate evaluation."""

    outcome: str  # "pass" | "bounce" | "abort"
    rubric_score: float
    delta_score: float
    weaknesses: list[str] = field(default_factory=list)
    bounce_reason: str | None = None
    """Human-readable reason for bounce, passed back to synthesizer for refinement."""


class QualityGate:
    """Evaluates research output against rubric and backpressure thresholds.

    The gate is the enforcement point between research and persistence.
    It should never be bypassed in production paths.

    From autocontext: backpressure gate rejects runs with insufficient delta,
    preventing noise accumulation in the knowledge store.
    """

    def __init__(self, settings: "Settings") -> None:
        self.settings = settings

        from knowledge_engine.evaluation.rubric import RubricEvaluator
        from knowledge_engine.evaluation.weakness import WeaknessDetector

        self.rubric = RubricEvaluator(settings=settings)
        self.weakness_detector = WeaknessDetector(settings=settings)

    def evaluate(
        self,
        synthesis: str,
        topic: str,
        existing_coverage: float = 0.0,
    ) -> GateDecision:
        """Evaluate synthesized research output.

        Args:
            synthesis: The synthesized research text from the pipeline.
            topic: Original research topic (used for rubric context).
            existing_coverage: Similarity score to existing knowledge (0–1).
                               Higher means less delta — used for backpressure.

        Returns:
            GateDecision with outcome and scores.
        """
        raise NotImplementedError

    def _compute_delta(self, synthesis: str, existing_coverage: float) -> float:
        """Estimate knowledge delta: how much new information this adds.

        From autocontext backpressure gate: delta = 1 - max_overlap_score.
        """
        raise NotImplementedError
