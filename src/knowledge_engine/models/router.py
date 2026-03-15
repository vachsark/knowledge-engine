"""
Model router — dispatches LLM calls to the right backend.

Never call Ollama or Anthropic directly from business logic.
Always route through this module so the backend can be swapped, mocked in tests,
and budget-tracked centrally.

From vault CLAUDE.md model selection table: Haiku/Sonnet/Opus/Local routing.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from knowledge_engine.config.settings import Settings


@dataclass
class ModelResponse:
    """Structured response from any model backend."""

    content: str
    model: str
    input_tokens: int
    output_tokens: int
    finish_reason: str = "stop"


class ModelRouter:
    """Routes LLM calls to Anthropic or Ollama based on model tier.

    Usage:
        router = ModelRouter(settings=settings)
        response = router.complete("Summarize this...", model="sonnet")
        response = router.complete("Embed this...", model="local", task="embed")

    Model tiers:
        "sonnet"  → claude-sonnet-4-6
        "opus"    → claude-opus-4-6
        "haiku"   → claude-haiku-4-5
        "local"   → settings.local_model via Ollama
    """

    ANTHROPIC_MODEL_MAP = {
        "sonnet": "claude-sonnet-4-6",
        "opus": "claude-opus-4-6",
        "haiku": "claude-haiku-4-5",
    }

    def __init__(self, settings: "Settings") -> None:
        self.settings = settings
        self._anthropic: Any = None
        self._ollama: Any = None

    def complete(
        self,
        prompt: str,
        model: str | None = None,
        system: str | None = None,
        max_tokens: int = 4096,
        **kwargs: Any,
    ) -> ModelResponse:
        """Send a completion request to the appropriate backend.

        Args:
            prompt: User prompt text.
            model: Model tier override. Defaults to settings.default_model.
            system: Optional system prompt.
            max_tokens: Maximum tokens to generate.

        Returns:
            ModelResponse with content and token counts.
        """
        raise NotImplementedError

    def embed(self, text: str) -> list[float]:
        """Generate embeddings using settings.embed_model (always local Ollama).

        Embedding calls always go to Ollama regardless of default_model setting.
        """
        raise NotImplementedError

    def _get_backend(self, tier: str) -> str:
        """Return 'anthropic' or 'ollama' for a model tier."""
        if tier in self.ANTHROPIC_MODEL_MAP:
            return "anthropic"
        return "ollama"

    def _requires_api_key(self, tier: str) -> bool:
        return self._get_backend(tier) == "anthropic"
