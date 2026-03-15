"""
Configurable evaluation rubric for research output scoring.

Rubric dimensions are loaded from templates/evaluation-rubric.yaml.
Default dimensions are RACE-like (Relevance, Accuracy, Completeness, Evidence).

Each dimension has:
    - name: str
    - weight: float (weights sum to 1.0)
    - prompt: str (what to ask the LLM evaluator)
    - min_score: float (per-dimension threshold, if any)

Adapted from vault quality gate rubric pattern.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import TYPE_CHECKING

import yaml

if TYPE_CHECKING:
    from knowledge_engine.config.settings import Settings


@dataclass
class RubricDimension:
    """A single evaluation dimension in the rubric."""

    name: str
    weight: float
    prompt: str
    min_score: float | None = None
    """Optional per-dimension minimum. Failing this can bounce regardless of total."""


@dataclass
class RubricScore:
    """Scored output from rubric evaluation."""

    total: float
    """Weighted total score across all dimensions (0–1)."""
    dimensions: dict[str, float] = field(default_factory=dict)
    """Per-dimension scores."""
    failed_minimums: list[str] = field(default_factory=list)
    """Dimensions that failed their per-dimension minimum (cause immediate bounce)."""


class RubricEvaluator:
    """Evaluates research synthesis against configurable rubric dimensions.

    Dimensions are loaded from templates/evaluation-rubric.yaml by default.
    Custom rubrics can be passed via the rubric_path parameter.
    """

    DEFAULT_RUBRIC_PATH = Path(__file__).parent.parent.parent.parent / "templates" / "evaluation-rubric.yaml"

    def __init__(self, settings: "Settings", rubric_path: Path | None = None) -> None:
        self.settings = settings
        self.rubric_path = rubric_path or self.DEFAULT_RUBRIC_PATH
        self._dimensions: list[RubricDimension] | None = None

    @property
    def dimensions(self) -> list[RubricDimension]:
        """Lazy-load dimensions from YAML."""
        if self._dimensions is None:
            self._dimensions = self._load_rubric()
        return self._dimensions

    def evaluate(self, synthesis: str, topic: str) -> RubricScore:
        """Score synthesis against all rubric dimensions.

        Uses the configured default_model (or local_model if tier='local')
        to evaluate each dimension with a structured prompt.

        Args:
            synthesis: Research synthesis text to evaluate.
            topic: Original research topic (for relevance dimension).

        Returns:
            RubricScore with weighted total and per-dimension breakdown.
        """
        raise NotImplementedError

    def _load_rubric(self) -> list[RubricDimension]:
        """Parse evaluation-rubric.yaml into RubricDimension objects."""
        if not self.rubric_path.exists():
            return self._default_dimensions()
        with open(self.rubric_path) as f:
            data = yaml.safe_load(f)
        return [RubricDimension(**d) for d in data.get("dimensions", [])]

    def _default_dimensions(self) -> list[RubricDimension]:
        """Fallback RACE dimensions if rubric file not found."""
        return [
            RubricDimension("relevance", 0.25, "How well does this address the research topic?"),
            RubricDimension("accuracy", 0.30, "Are claims accurate and well-supported?"),
            RubricDimension("completeness", 0.25, "Does this cover the topic's key aspects?"),
            RubricDimension("evidence", 0.20, "Are claims backed by citations or evidence?"),
        ]
