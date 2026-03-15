"""
Token and cost budget tracking.

Tracks token usage across all model calls within a session and against a
rolling daily budget. Emits warnings when approaching the daily limit.

From vault: token tracking via _collab/heartbeat/token-usage.tsv and
token-report.sh --days N. This module is the programmatic equivalent.

Budget file: knowledge/.budget/usage.tsv (TSNE: timestamp, model, tokens, task)
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import date, datetime
from pathlib import Path
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from knowledge_engine.config.settings import Settings


@dataclass
class UsageEntry:
    """A single token usage record."""

    timestamp: datetime
    model: str
    task_name: str
    input_tokens: int
    output_tokens: int

    @property
    def total_tokens(self) -> int:
        return self.input_tokens + self.output_tokens

    def to_tsv(self) -> str:
        return "\t".join([
            self.timestamp.isoformat(),
            self.model,
            self.task_name,
            str(self.input_tokens),
            str(self.output_tokens),
        ])


class BudgetTracker:
    """Tracks token usage and enforces daily budget limits.

    Usage is appended to a TSV file for easy inspection and reporting.
    Provides warnings (not hard blocks) when the daily budget is exceeded.
    """

    def __init__(self, settings: "Settings") -> None:
        self.settings = settings
        self.usage_path = settings.knowledge_dir / ".budget" / "usage.tsv"

    def record(self, model: str, task_name: str, input_tokens: int, output_tokens: int) -> None:
        """Record a model call's token usage."""
        raise NotImplementedError

    def daily_total(self, day: date | None = None) -> int:
        """Return total tokens used on a given day (default: today)."""
        raise NotImplementedError

    def is_over_budget(self) -> bool:
        """Return True if today's usage exceeds settings.token_budget_daily."""
        return self.daily_total() > self.settings.token_budget_daily

    def report(self, days: int = 7) -> dict[str, int]:
        """Return per-day token totals for the last N days.

        From vault: token-report.sh --days N equivalent.
        """
        raise NotImplementedError

    def warn_if_over(self) -> None:
        """Print a warning to stderr if daily budget is exceeded."""
        raise NotImplementedError
