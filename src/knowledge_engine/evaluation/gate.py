"""
Backpressure gate — prevents low-delta runs from accumulating in the knowledge store.

Adapted from autocontext backpressure gate pattern.

Core idea: if a research run doesn't add at least `backpressure_min_delta` new
information (as measured by semantic distance from existing knowledge), it should
be rejected. This keeps the knowledge store high-signal.

The gate is stateful: it tracks the running average delta so the threshold can
self-adjust if the system is consistently producing low-delta output.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from knowledge_engine.config.settings import Settings


@dataclass
class BackpressureState:
    """Persistent state for the backpressure gate (written to knowledge store)."""

    run_count: int = 0
    total_delta: float = 0.0
    last_delta: float = 0.0
    consecutive_low_delta: int = 0
    """Number of consecutive runs below the minimum delta threshold."""

    @property
    def average_delta(self) -> float:
        if self.run_count == 0:
            return 0.0
        return self.total_delta / self.run_count


class BackpressureGate:
    """Stateful gate that rejects runs with insufficient knowledge delta.

    From autocontext: the gate enforces quality by ensuring each run
    meaningfully advances the knowledge base.

    Self-adjusting behavior:
        - After 5 consecutive low-delta runs, emits a warning
        - If domain is exhausted, suggests broadening the topic scope
    """

    def __init__(self, settings: "Settings") -> None:
        self.settings = settings
        self._state: BackpressureState | None = None

    @property
    def state(self) -> BackpressureState:
        """Load state from disk (lazy)."""
        raise NotImplementedError

    def check(self, delta: float) -> tuple[bool, str]:
        """Check if a run's knowledge delta meets the minimum threshold.

        Args:
            delta: Knowledge delta score for this run (0–1).

        Returns:
            Tuple of (passes: bool, reason: str).
        """
        raise NotImplementedError

    def record(self, delta: float, passed: bool) -> None:
        """Record a run's outcome in the gate state.

        Call this after each run, regardless of outcome, to maintain
        accurate statistics for threshold self-adjustment.
        """
        raise NotImplementedError

    def reset(self) -> None:
        """Reset gate state (use at start of a new research domain)."""
        raise NotImplementedError

    def summary(self) -> dict[str, float | int]:
        """Return a summary of gate statistics for display."""
        raise NotImplementedError
