"""
Anthropic API integration.

Wraps the anthropic Python SDK with retry logic and budget tracking.
Requires the `anthropic` extra: `uv sync --extra anthropic`.

Model mapping (from vault CLAUDE.md, updated 2026):
    sonnet → claude-sonnet-4-6   (default: all implementation)
    opus   → claude-opus-4-6     (quality gates, multi-agent coord)
    haiku  → claude-haiku-4-5    (read-only scans, cheap tasks)
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from knowledge_engine.config.settings import Settings
    from knowledge_engine.models.router import ModelResponse


class AnthropicClient:
    """Wraps the Anthropic SDK with retry logic and token tracking.

    Import is deferred to support optional anthropic dependency.
    Raises ImportError at instantiation if anthropic is not installed.
    """

    MODEL_MAP = {
        "sonnet": "claude-sonnet-4-6",
        "opus": "claude-opus-4-6",
        "haiku": "claude-haiku-4-5",
    }

    def __init__(self, settings: "Settings") -> None:
        self.settings = settings
        self._client: Any = None  # Lazy-loaded anthropic.Anthropic instance

    @property
    def client(self) -> Any:
        """Lazy-load the anthropic client. Raises ImportError if not installed."""
        if self._client is None:
            try:
                import anthropic
            except ImportError as e:
                raise ImportError(
                    "anthropic package not installed. Run: uv sync --extra anthropic"
                ) from e
            if not self.settings.anthropic_api_key:
                raise ValueError(
                    "ANTHROPIC_API_KEY not set. Export KE_ANTHROPIC_API_KEY or set in ke.yaml."
                )
            self._client = anthropic.Anthropic(api_key=self.settings.anthropic_api_key)
        return self._client

    def complete(
        self,
        prompt: str,
        model: str = "sonnet",
        system: str | None = None,
        max_tokens: int = 4096,
    ) -> "ModelResponse":
        """Send a messages API request and return a structured response.

        Args:
            prompt: User message content.
            model: Model tier ('sonnet', 'opus', 'haiku').
            system: Optional system prompt.
            max_tokens: Maximum tokens to generate.

        Returns:
            ModelResponse with content and token counts for budget tracking.
        """
        raise NotImplementedError

    def _resolve_model(self, tier: str) -> str:
        """Map tier name to full model ID."""
        if tier not in self.MODEL_MAP:
            raise ValueError(f"Unknown model tier '{tier}'. Valid: {list(self.MODEL_MAP)}")
        return self.MODEL_MAP[tier]
