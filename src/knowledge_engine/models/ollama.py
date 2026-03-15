"""
Ollama integration for local model inference.

Uses httpx for HTTP calls to the Ollama REST API.
CRITICAL: Always pass num_ctx in options — the Vulkan runner hangs when prompts
exceed the default 4096 context without it. (From vault memory 2026-03-13.)

API reference: https://github.com/ollama/ollama/blob/main/docs/api.md
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Any, AsyncIterator

import httpx

if TYPE_CHECKING:
    from knowledge_engine.config.settings import Settings
    from knowledge_engine.models.router import ModelResponse


class OllamaClient:
    """HTTP client for the Ollama local inference API.

    Handles:
        - Text completions (/api/generate)
        - Chat completions (/api/chat)
        - Embeddings (/api/embeddings)
        - Model listing and pulling

    CRITICAL: num_ctx is always included in options payload.
    Without it, Vulkan GPU runner hangs on long prompts.
    """

    def __init__(self, settings: "Settings") -> None:
        self.settings = settings
        self.base_url = settings.ollama_base
        self.num_ctx = settings.ollama_num_ctx

    def generate(
        self,
        model: str,
        prompt: str,
        system: str | None = None,
        max_tokens: int = 4096,
        **kwargs: Any,
    ) -> "ModelResponse":
        """Call /api/generate — single-turn completion.

        Always includes num_ctx in options to prevent Vulkan runner hangs.
        """
        raise NotImplementedError

    def chat(
        self,
        model: str,
        messages: list[dict[str, str]],
        max_tokens: int = 4096,
        **kwargs: Any,
    ) -> "ModelResponse":
        """Call /api/chat — multi-turn chat completion."""
        raise NotImplementedError

    def embed(self, model: str, text: str) -> list[float]:
        """Call /api/embeddings — return embedding vector for text."""
        raise NotImplementedError

    def list_models(self) -> list[str]:
        """Return list of locally available model tags."""
        raise NotImplementedError

    def is_available(self) -> bool:
        """Check if Ollama server is reachable."""
        try:
            with httpx.Client(timeout=2.0) as client:
                resp = client.get(f"{self.base_url}/api/tags")
                return resp.status_code == 200
        except httpx.ConnectError:
            return False

    def _build_options(self, max_tokens: int) -> dict[str, Any]:
        """Build options dict. Always includes num_ctx.

        CRITICAL: Do not remove num_ctx. Vulkan runner will hang on long prompts.
        """
        return {
            "num_ctx": self.num_ctx,
            "num_predict": max_tokens,
        }
