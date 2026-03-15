"""
Settings for knowledge-engine.

Sources (in priority order):
    1. Environment variables (prefix: KE_)
    2. ke.yaml in the current working directory
    3. Defaults defined here

All settings are also available as a singleton via `get_settings()`, but
prefer explicit injection in production code and tests.
"""

from __future__ import annotations

from pathlib import Path
from typing import Optional

from pydantic import Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Top-level configuration for knowledge-engine.

    Environment variables use the prefix KE_ (e.g. KE_DEFAULT_MODEL=sonnet).
    Can also be configured via ke.yaml in the working directory.
    """

    model_config = SettingsConfigDict(
        env_prefix="KE_",
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    # --- Paths ---
    knowledge_dir: Path = Field(
        default=Path("./knowledge"),
        description="Root directory for persisted knowledge files.",
    )

    # --- Model selection ---
    # From vault CLAUDE.md model selection table: Haiku/Sonnet/Opus routing
    default_model: str = Field(
        default="sonnet",
        description="Default model tier: 'sonnet', 'opus', 'haiku', or 'local'.",
    )
    local_model: str = Field(
        default="qwen3:8b",
        description="Ollama model tag for local inference.",
    )
    embed_model: str = Field(
        default="qwen3-embedding:0.6b",
        description="Ollama model tag for embedding generation.",
    )
    rerank_model: str = Field(
        default="qwen3:8b",
        description="Model used for LLM-based reranking passes.",
    )

    # --- API keys ---
    anthropic_api_key: Optional[str] = Field(
        default=None,
        description="Anthropic API key. Required when default_model is sonnet/opus/haiku.",
    )

    # --- Ollama ---
    ollama_base: str = Field(
        default="http://localhost:11434",
        description="Base URL for the Ollama HTTP API.",
    )
    # Critical: always pass num_ctx — Vulkan runner hangs without it on large prompts.
    # From vault memory: "Always pass num_ctx to Ollama API calls"
    ollama_num_ctx: int = Field(
        default=8192,
        description="Context window size passed to Ollama. Never omit — required for Vulkan runner stability.",
    )

    # --- Evaluation / gating ---
    # From autocontext backpressure gate: minimum delta to accept a run
    backpressure_min_delta: float = Field(
        default=0.005,
        description="Minimum knowledge delta (0–1) required for a run to pass the backpressure gate.",
    )
    gate_max_bounces: int = Field(
        default=3,
        description="Maximum number of gate bounce-back retries before aborting.",
    )
    gate_pass_threshold: float = Field(
        default=0.70,
        description="Rubric score threshold (0–1) required to pass the quality gate.",
    )

    # --- Lessons ---
    # From autocontext: applicability windowing — lessons age out
    max_lessons: int = Field(
        default=50,
        description="Maximum number of lessons to keep active. Oldest are archived when exceeded.",
    )
    staleness_window: int = Field(
        default=10,
        description="Number of research runs after which an un-applied lesson is considered stale.",
    )

    # --- Budget ---
    token_budget_daily: int = Field(
        default=500_000,
        description="Daily token budget across all model calls. Triggers warnings when exceeded.",
    )

    # --- Search ---
    search_bm25_weight: float = Field(default=0.4, description="BM25 weight in RRF fusion.")
    search_embed_weight: float = Field(default=0.6, description="Embedding weight in RRF fusion.")
    search_top_k_default: int = Field(default=5)

    @field_validator("knowledge_dir", mode="before")
    @classmethod
    def expand_knowledge_dir(cls, v: str | Path) -> Path:
        return Path(v).expanduser().resolve()

    @field_validator("default_model")
    @classmethod
    def validate_model_tier(cls, v: str) -> str:
        valid = {"sonnet", "opus", "haiku", "local"}
        if v not in valid:
            raise ValueError(f"default_model must be one of {valid}, got '{v}'")
        return v


_settings_instance: Settings | None = None


def get_settings() -> Settings:
    """Return the global Settings singleton (lazy-loaded).

    Prefer explicit injection in tests. Use this only at application entry points.
    """
    global _settings_instance
    if _settings_instance is None:
        _settings_instance = Settings()
    return _settings_instance
