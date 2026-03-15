"""
Heartbeat scheduler — runs tasks on a configurable wall-clock schedule.

Adapted directly from vault heartbeat architecture.

Key fixes encoded here (from vault memory 2026-03-13):
    - Timer uses OnCalendar wall-clock, not OnUnitActiveSec (drift prevention)
    - Comma-separated days: 'weekly monday,wednesday,friday HH:MM'
    - State and config are separate: schedule.yaml (config) vs state.yaml (state)
    - Fallback guard: tool-dependent tasks skip local model fallback

State file (state.yaml) tracks:
    - last_run per task
    - last_outcome per task
    - consecutive_failures per task

Config file (schedule.yaml) defines:
    - task name, schedule, model, timeout
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import TYPE_CHECKING

import yaml

if TYPE_CHECKING:
    from knowledge_engine.config.settings import Settings
    from knowledge_engine.scheduler.task import Task, TaskResult


@dataclass
class TaskState:
    """Per-task runtime state (written to state.yaml)."""

    name: str
    last_run: datetime | None = None
    last_outcome: str = "never"  # "success" | "failure" | "skip" | "never"
    consecutive_failures: int = 0


class Heartbeat:
    """Task scheduler that runs `ke schedule --once` style execution.

    Configuration is read from schedule.yaml (or the path in settings).
    State is tracked in a separate state.yaml file.
    Tasks are executed synchronously in this implementation; async variant TBD.

    From vault: heartbeat timer runs every 15 minutes (*:0/15) and checks
    which tasks are due based on their schedule expression.
    """

    def __init__(self, settings: "Settings") -> None:
        self.settings = settings
        self.schedule_path = settings.knowledge_dir / "schedule.yaml"
        self.state_path = settings.knowledge_dir / "state.yaml"

    def run_due(self) -> list["TaskResult"]:
        """Check all tasks and run any that are currently due.

        Returns:
            List of TaskResult for all tasks that were run.
        """
        raise NotImplementedError

    def run_task(self, name: str) -> "TaskResult":
        """Run a specific task by name, regardless of schedule.

        Args:
            name: Task name as defined in schedule.yaml.
        """
        raise NotImplementedError

    def list_tasks(self) -> None:
        """Print all configured tasks with their next-due time."""
        raise NotImplementedError

    def is_due(self, task: "Task", now: datetime | None = None) -> bool:
        """Check if a task is due based on its schedule expression.

        Supports schedule formats:
            daily HH:MM                          — run every day at HH:MM
            weekly monday HH:MM                  — run on a specific weekday
            weekly monday,wednesday,friday HH:MM — comma-separated days
            interval Nm                          — every N minutes (cron-style)

        From vault memory: comma-separated days fixed 2026-03-13.
        """
        raise NotImplementedError

    def _load_schedule(self) -> list["Task"]:
        """Parse schedule.yaml into Task objects."""
        raise NotImplementedError

    def _load_state(self) -> dict[str, TaskState]:
        """Load per-task state from state.yaml."""
        raise NotImplementedError

    def _save_state(self, state: dict[str, TaskState]) -> None:
        """Persist updated task state to state.yaml (atomic write)."""
        raise NotImplementedError

    def get_last_run(self, name: str) -> datetime | None:
        """Get the last run time for a named task. Returns None if never run."""
        state = self._load_state()
        return state.get(name, TaskState(name=name)).last_run

    def update_state(self, name: str, outcome: str) -> None:
        """Update task state after a run. Persists to state.yaml."""
        raise NotImplementedError
