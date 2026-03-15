"""
Task definition and execution for the heartbeat scheduler.

A Task is a unit of scheduled work: research a topic, distill lessons,
export knowledge, run a benchmark, etc.

From vault: each heartbeat task has a name, schedule, model preference,
tool dependencies, and a timeout. Tool-dependent tasks skip local fallback.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, TYPE_CHECKING

if TYPE_CHECKING:
    from knowledge_engine.config.settings import Settings


@dataclass
class Task:
    """A configured scheduled task."""

    name: str
    schedule: str
    """Schedule expression, e.g. 'daily 02:30', 'weekly monday,wednesday 08:00'."""
    action: str
    """Action type: 'research', 'distill', 'export', 'benchmark', 'custom'."""
    params: dict[str, Any] = field(default_factory=dict)
    """Parameters passed to the action handler."""
    model: str = "local"
    """Model tier to use: 'local', 'sonnet', 'opus', 'haiku'."""
    timeout_seconds: int = 300
    requires_tools: bool = False
    """If True, skip local model fallback — task needs tool access."""
    enabled: bool = True

    @classmethod
    def from_yaml(cls, data: dict) -> "Task":
        """Construct a Task from a schedule.yaml entry."""
        return cls(
            name=data["name"],
            schedule=data["schedule"],
            action=data["action"],
            params=data.get("params", {}),
            model=data.get("model", "local"),
            timeout_seconds=data.get("timeout_seconds", 300),
            requires_tools=data.get("requires_tools", False),
            enabled=data.get("enabled", True),
        )


@dataclass
class TaskResult:
    """Outcome of a task execution."""

    task_name: str
    started_at: datetime
    completed_at: datetime
    outcome: str  # "success" | "failure" | "skip" | "timeout"
    output: str = ""
    error: str | None = None
    token_cost: int = 0

    @property
    def duration_seconds(self) -> float:
        return (self.completed_at - self.started_at).total_seconds()


class TaskRunner:
    """Executes a single Task and returns a TaskResult.

    Handles:
        - Model selection (frontier vs local, with fallback logic)
        - Timeout enforcement
        - Budget tracking
        - Local model fallback guard (skips fallback for requires_tools tasks)
    """

    def __init__(self, settings: "Settings") -> None:
        self.settings = settings

    def run(self, task: Task) -> TaskResult:
        """Execute a task and return its result.

        Dispatches to the appropriate action handler based on task.action.
        """
        raise NotImplementedError

    def _dispatch(self, task: Task) -> tuple[str, int]:
        """Dispatch task to action handler. Returns (output, token_cost)."""
        handlers = {
            "research": self._run_research,
            "distill": self._run_distill,
            "export": self._run_export,
            "benchmark": self._run_benchmark,
        }
        handler = handlers.get(task.action)
        if handler is None:
            raise ValueError(f"Unknown task action: {task.action!r}")
        return handler(task)

    def _run_research(self, task: Task) -> tuple[str, int]:
        raise NotImplementedError

    def _run_distill(self, task: Task) -> tuple[str, int]:
        raise NotImplementedError

    def _run_export(self, task: Task) -> tuple[str, int]:
        raise NotImplementedError

    def _run_benchmark(self, task: Task) -> tuple[str, int]:
        raise NotImplementedError
