"""
Adversarial skeptic agent — Wave 1.5 of the research pipeline.

The skeptic challenges claims made in Wave 1 output, looking for:
    - Unsupported assertions
    - Missing counterarguments
    - Overconfident conclusions
    - Temporal staleness (claims that may be outdated)
    - Contradictions with existing knowledge

Adapted from vault research pipeline (research-critic, Wave 1.5, added 2026-03-13).
The skeptic output is fed into the Wave 2 synthesizer alongside Wave 1 output.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from knowledge_engine.config.settings import Settings


@dataclass
class SkepticChallenge:
    """A single challenge raised by the skeptic agent."""

    claim: str
    challenge: str
    severity: str  # "minor" | "major" | "fatal"
    suggestion: str | None = None


@dataclass
class SkepticReport:
    """Full adversarial review of a research wave output."""

    wave_output: str
    challenges: list[SkepticChallenge] = field(default_factory=list)
    overall_confidence: float = 0.0
    """Skeptic's overall confidence in the Wave 1 output (0–1). Low = many issues."""
    recommendation: str = ""
    """Brief recommendation for the synthesizer (e.g., 'strengthen claims X and Y')."""


class SkepticAgent:
    """Adversarial reviewer that challenges research wave output.

    The skeptic is intentionally argumentative — it should find fault.
    Its output does NOT block the pipeline; it enriches Wave 2 synthesis.

    From vault: research-critic agent definition in agents/research-skeptic.md.
    """

    SKEPTIC_PROMPT = """You are a rigorous, adversarial research critic.
Your job is to find weaknesses, unsupported claims, and missing perspectives
in the following research output.

Topic: {topic}
Research output:
---
{wave_output}
---

For each significant claim you challenge, provide:
1. The specific claim
2. Why it's problematic or unsupported
3. Severity: minor | major | fatal
4. A suggestion for how to strengthen it

Be thorough. The synthesizer will use your critique to produce a better final output."""

    def __init__(self, settings: "Settings") -> None:
        self.settings = settings

    def review(self, topic: str, wave_output: str) -> SkepticReport:
        """Run adversarial review of wave output.

        Args:
            topic: Original research topic for context.
            wave_output: The synthesized output from Wave 1 agents.

        Returns:
            SkepticReport with structured challenges and a recommendation.
        """
        raise NotImplementedError

    def _parse_challenges(self, llm_response: str) -> list[SkepticChallenge]:
        """Parse structured challenges from LLM response."""
        raise NotImplementedError
