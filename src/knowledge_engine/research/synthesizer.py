"""
Synthesizer — merges and deduplicates multi-wave research output.

Takes outputs from all Wave 1 parallel agents + skeptic challenges (Wave 1.5)
and produces a single coherent synthesis for the quality gate.

Also handles bounce-back refinement: when the gate rejects output, the
synthesizer receives the bounce reason and attempts to address it.

Adapted from vault research pipeline Wave 2 (synthesis + skeptic, 20% of session time).
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from knowledge_engine.config.settings import Settings
    from knowledge_engine.research.skeptic import SkepticReport


@dataclass
class SynthesisInput:
    """All inputs gathered before synthesis."""

    topic: str
    wave_outputs: list[str]
    """Raw output from each parallel Wave 1 agent."""
    skeptic_report: "SkepticReport | None" = None
    bounce_reason: str | None = None
    """If this is a retry after gate bounce, the reason for rejection."""
    attempt: int = 1


class Synthesizer:
    """Merges parallel agent outputs into a coherent, deduplicated synthesis.

    Responsibilities:
        - Merge overlapping information from parallel agents
        - Incorporate skeptic challenges as caveats or corrections
        - On bounce-back: specifically address the gate's rejection reason
        - Maintain citation traceability

    The synthesizer is the final content producer before the quality gate.
    Its output is what gets evaluated and (if passing) persisted.
    """

    def __init__(self, settings: "Settings") -> None:
        self.settings = settings

    def synthesize(self, inputs: SynthesisInput) -> str:
        """Produce a merged, deduplicated synthesis from all wave inputs.

        Args:
            inputs: All wave outputs, skeptic report, and optional bounce context.

        Returns:
            Synthesized research text, structured per research-report.md template.
        """
        raise NotImplementedError

    def _build_synthesis_prompt(self, inputs: SynthesisInput) -> str:
        """Construct the synthesis prompt, incorporating skeptic challenges
        and any bounce-back refinement instructions."""
        raise NotImplementedError

    def _dedup_claims(self, texts: list[str]) -> list[str]:
        """Remove near-duplicate claims/sentences across agent outputs.

        Uses embedding similarity to identify and drop redundant content
        before passing to the synthesis LLM call.
        """
        raise NotImplementedError
