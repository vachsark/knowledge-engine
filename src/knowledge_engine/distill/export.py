"""
Training data export from the validated knowledge store.

Generates structured (prompt, completion) pairs suitable for:
    - Supervised fine-tuning (SFT) via Unsloth / TRL
    - DPO training (using curator decision pairs as preference data)
    - RAG evaluation dataset generation

Export strategies:
    qa_pairs       — question-answer pairs from note content
    reasoning      — synthesis + curator rationale as chain-of-thought traces
    retrieval      — query + relevant note pairs for embedding model training
    dpo_curation   — (pass, bounce) pairs for curator preference training

From vault: ClaudeLab venv has full ML stack (PyTorch + ROCm + TRL).
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import TYPE_CHECKING, Literal

if TYPE_CHECKING:
    from knowledge_engine.config.settings import Settings

ExportStrategy = Literal["qa_pairs", "reasoning", "retrieval", "dpo_curation"]


@dataclass
class TrainingPair:
    """A single training example."""

    prompt: str
    completion: str
    strategy: ExportStrategy
    source_note_id: str
    quality_score: float
    """The gate score of the source note — used to filter low-quality training data."""


class TrainingExporter:
    """Exports knowledge store content as structured training data.

    The exporter reads from the knowledge store and mutation log to generate
    training pairs. Only notes above a minimum quality score are included.
    """

    MIN_QUALITY_SCORE = 0.70

    def __init__(self, settings: "Settings") -> None:
        self.settings = settings

    def export(
        self,
        output_path: Path,
        strategies: list[ExportStrategy] | None = None,
        min_score: float | None = None,
    ) -> int:
        """Export training data to a JSONL file.

        Args:
            output_path: Path to write the JSONL file.
            strategies: Which export strategies to run. Default: all.
            min_score: Minimum gate score for included notes. Default: MIN_QUALITY_SCORE.

        Returns:
            Total number of training pairs exported.
        """
        raise NotImplementedError

    def generate_qa_pairs(self, note_content: str, note_id: str) -> list[TrainingPair]:
        """Generate question-answer pairs from a knowledge note using an LLM.

        Prompt: note content → questions that this note answers.
        Completion: the relevant excerpt answering each question.
        """
        raise NotImplementedError

    def generate_reasoning_traces(
        self, synthesis: str, curator_rationale: str, note_id: str
    ) -> list[TrainingPair]:
        """Generate chain-of-thought training pairs from curator decisions.

        Prompt:     research synthesis + gate scores
        Completion: curator rationale + action decision

        These teach a local model to reason about knowledge curation.
        """
        raise NotImplementedError

    def generate_dpo_pairs(self) -> list[dict]:
        """Generate DPO preference pairs from gate bounce history.

        Chosen: synthesis that passed the gate
        Rejected: synthesis from the same topic that bounced

        Requires at least one bounce in the mutation log.
        """
        raise NotImplementedError
