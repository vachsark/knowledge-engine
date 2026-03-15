"""
Weakness pattern detection for research output.

Flags common failure modes before the quality gate decision:
    - Hallucination markers ("studies show", "research suggests" without citations)
    - Temporal staleness markers ("recently", "new", "latest" without dates)
    - Overconfidence ("always", "never", "definitively")
    - Missing counterarguments (one-sided framing on contested topics)
    - Circular reasoning (conclusion restates the premise)

Heuristic patterns run cheaply (no LLM call). LLM-based checks run only when
heuristics fire above a severity threshold.

Adapted from autocontext weakness detection + vault rules pattern.
"""

from __future__ import annotations

import re
from dataclasses import dataclass
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from knowledge_engine.config.settings import Settings


@dataclass
class Weakness:
    """A detected weakness in a research output."""

    pattern: str
    """Name of the pattern that triggered (e.g., 'unsupported_citation')."""
    excerpt: str
    """The specific text fragment that triggered the pattern."""
    severity: str  # "minor" | "major" | "critical"
    suggestion: str = ""


class WeaknessDetector:
    """Detect common failure modes in research output.

    Two-tier detection:
        1. Heuristic patterns (regex, fast, no cost) — run always
        2. LLM-based patterns (slow, costly) — run only when heuristics fire

    Critical weaknesses cause the quality gate to bounce regardless of rubric score.
    """

    # Tier 1: heuristic patterns
    PATTERNS: dict[str, tuple[str, str]] = {
        # pattern_name: (regex, severity)
        "unsupported_citation": (
            r"\b(studies show|research suggests|experts say|scientists found)\b(?![^.]*\[)",
            "major",
        ),
        "temporal_staleness": (
            r"\b(recently|the latest|new research|just released|cutting-edge)\b(?![^.]*20\d\d)",
            "minor",
        ),
        "overconfidence": (
            r"\b(always|never|definitively|certainly|undoubtedly|without question)\b",
            "minor",
        ),
        "vague_quantifier": (
            r"\b(many|most|some|several|various|numerous) (studies|researchers|experts)\b",
            "minor",
        ),
    }

    def __init__(self, settings: "Settings") -> None:
        self.settings = settings

    def detect(self, synthesis: str) -> list[Weakness]:
        """Run all weakness detectors against synthesis text.

        Returns list of weaknesses, sorted by severity (critical first).
        """
        raise NotImplementedError

    def _run_heuristics(self, text: str) -> list[Weakness]:
        """Apply regex-based heuristic patterns. Fast, always runs."""
        weaknesses: list[Weakness] = []
        for name, (pattern, severity) in self.PATTERNS.items():
            for match in re.finditer(pattern, text, re.IGNORECASE):
                weaknesses.append(
                    Weakness(
                        pattern=name,
                        excerpt=match.group(0),
                        severity=severity,
                    )
                )
        return weaknesses

    def _run_llm_checks(self, text: str, heuristic_hits: list[Weakness]) -> list[Weakness]:
        """LLM-based checks for complex patterns (circular reasoning, missing counterargs).

        Only runs when heuristic_hits contains at least one 'major' weakness.
        """
        raise NotImplementedError

    def has_critical(self, weaknesses: list[Weakness]) -> bool:
        """Return True if any weakness is critical severity."""
        return any(w.severity == "critical" for w in weaknesses)
