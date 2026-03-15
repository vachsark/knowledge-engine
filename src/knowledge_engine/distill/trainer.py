"""
Fine-tuning pipeline interface.

Provides a thin wrapper around TRL / Unsloth training for local model fine-tuning.
The actual training loop is intentionally NOT implemented here — this module
provides the interface and data preparation, and delegates to the appropriate
framework.

From vault memory: ClaudeLab venv has PyTorch 2.9.1+rocm6.3, full ML stack,
Unsloth + TRL with GRPO support (updated 2026-03-13).
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from knowledge_engine.config.settings import Settings


@dataclass
class TrainingConfig:
    """Configuration for a fine-tuning run."""

    base_model: str
    """Ollama model tag or HuggingFace model ID to fine-tune."""
    training_data_path: Path
    output_dir: Path
    method: str = "sft"
    """Training method: 'sft' (supervised) or 'dpo' (preference)."""
    epochs: int = 3
    batch_size: int = 4
    learning_rate: float = 2e-4
    max_seq_length: int = 4096
    use_lora: bool = True
    lora_rank: int = 16


class LocalModelTrainer:
    """Interface for fine-tuning local models on exported knowledge data.

    Workflow:
        1. Export training data via distill/export.py
        2. Configure TrainingConfig
        3. Call trainer.prepare() to validate data
        4. Call trainer.train() to start the fine-tuning run
        5. trainer.export_to_ollama() to make the model available locally

    This module is a scaffold — the actual TRL/Unsloth calls go in train().
    """

    def __init__(self, settings: "Settings") -> None:
        self.settings = settings

    def prepare(self, config: TrainingConfig) -> dict[str, Any]:
        """Validate training data and return statistics before committing to a run.

        Returns:
            Dict with: example_count, token_count_estimate, estimated_duration_minutes.
        """
        raise NotImplementedError

    def train(self, config: TrainingConfig) -> Path:
        """Launch the fine-tuning run.

        Returns:
            Path to the trained model directory.

        Note: Requires the ClaudeLab ML environment:
            source Projects/ClaudeLab/.venv/bin/activate
        """
        raise NotImplementedError

    def export_to_ollama(self, model_dir: Path, model_name: str) -> None:
        """Create a Modelfile and register the trained model with Ollama.

        After this, the model is available as: ollama run <model_name>
        """
        raise NotImplementedError
