"""
Top-level research pipeline orchestrator.

Adapted from vault research pipeline (waves: Pre-Flight → Research → Critique+Deepen
→ Quality Gate → Synthesis+Skeptic → Refinement → Report).

Key design decisions:
    - Each wave is a named stage; stages are logged to the mutation log
    - The quality gate sits between synthesis and persistence
    - Bounce-back sends output back into refinement (max 3 attempts)
    - Pre-flight dedup can narrow the topic or abort entirely
"""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from knowledge_engine.config.settings import Settings


@dataclass
class ResearchResult:
    """Output of a completed (or aborted) research pipeline run."""

    topic: str
    gate_outcome: str  # "pass" | "bounce_limit" | "abort_preflight"
    score: float = 0.0
    persisted_path: Path | None = None
    bounce_count: int = 0
    token_cost: int = 0
    stages: list[str] = field(default_factory=list)
    """Names of pipeline stages that completed, in order."""


@dataclass
class WaveOutput:
    """Intermediate output from a single research wave."""

    wave: int
    agent_outputs: list[str]
    synthesis: str = ""
    skeptic_challenges: list[str] = field(default_factory=list)


class ResearchPipeline:
    """Orchestrates the full multi-wave research pipeline.

    Usage:
        pipeline = ResearchPipeline(settings=settings)
        result = pipeline.run("transformer attention mechanisms", waves=2)

    Stages:
        1. preflight   — dedup check; may narrow or abort topic
        2. wave_1      — N parallel research agents
        3. wave_1_5    — skeptic adversarial pass (if with_skeptic=True)
        4. synthesize  — merge + dedup wave outputs
        5. gate        — quality gate; may bounce back to synthesize
        6. curate      — decide what to persist
        7. persist     — write to knowledge store
    """

    def __init__(self, settings: "Settings") -> None:
        self.settings = settings

        # Lazy imports to avoid circular deps
        from knowledge_engine.research.preflight import PreflightCheck
        from knowledge_engine.research.quality_gate import QualityGate
        from knowledge_engine.research.skeptic import SkepticAgent
        from knowledge_engine.research.synthesizer import Synthesizer
        from knowledge_engine.evaluation.curator import KnowledgeCurator
        from knowledge_engine.knowledge.store import KnowledgeStore

        self.preflight = PreflightCheck(settings=settings)
        self.gate = QualityGate(settings=settings)
        self.skeptic = SkepticAgent(settings=settings)
        self.synthesizer = Synthesizer(settings=settings)
        self.curator = KnowledgeCurator(settings=settings)
        self.store = KnowledgeStore(settings=settings)

    def run(
        self,
        topic: str,
        waves: int = 2,
        with_skeptic: bool = True,
        dry_run: bool = False,
    ) -> ResearchResult:
        """Run the full pipeline for a topic.

        Args:
            topic: Research topic or question.
            waves: Number of research waves (1 or 2).
            with_skeptic: Whether to include the Wave 1.5 skeptic pass.
            dry_run: Skip persistence even if gate passes.

        Returns:
            ResearchResult with gate outcome, score, and persisted path.
        """
        raise NotImplementedError

    def _run_wave(self, topic: str, wave_num: int, context: str = "") -> WaveOutput:
        """Execute a single research wave with parallel agents.

        Args:
            topic: Research topic.
            wave_num: Wave index (used for prompt variation).
            context: Prior wave output for context injection.
        """
        raise NotImplementedError

    def _build_research_prompt(self, topic: str, wave: int, context: str) -> str:
        """Build the prompt for a research wave agent."""
        raise NotImplementedError
