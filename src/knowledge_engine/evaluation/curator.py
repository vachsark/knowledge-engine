"""
Knowledge curator — decides what to persist, what to update, what to discard.

Adapted from autocontext curator.py pattern.

The curator sits between the quality gate and the knowledge store. Its job is
not to evaluate quality (that's the gate's job) but to make architectural
decisions about the knowledge base:
    - Should this be a new note or an update to an existing one?
    - What's the minimal, atomic representation?
    - What existing notes does this supersede?
    - What connections should be created?
"""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from knowledge_engine.config.settings import Settings


@dataclass
class CurationDecision:
    """The curator's output: what to do with a research synthesis."""

    action: str  # "create" | "update" | "merge" | "discard"
    title: str
    content: str
    target_path: Path | None = None
    """For 'update' and 'merge': the existing file to modify."""
    superseded_ids: list[str] = field(default_factory=list)
    """Doc IDs that this note partially or fully supersedes."""
    connections: list[str] = field(default_factory=list)
    """Doc IDs that should be linked from this note."""
    tags: list[str] = field(default_factory=list)
    rationale: str = ""
    """Curator's explanation for its decision (logged to mutation log)."""


class KnowledgeCurator:
    """LLM-based curator that makes persistence decisions for research output.

    The curator uses hybrid search to find related existing notes, then
    decides whether to create, update, or merge. It also formats the
    content into the zettelkasten-note.md template.

    From autocontext: curator pattern enforces atomic, non-redundant notes.
    """

    CURATOR_PROMPT = """You are a knowledge curator maintaining a high-quality knowledge base.

Existing related notes:
{related_notes}

New research synthesis:
---
{synthesis}
---

Decide:
1. Should this be a NEW note, an UPDATE to an existing note, a MERGE of several notes, or DISCARDED?
2. What's the best title (atomic, specific)?
3. What existing notes does this supersede (if any)?
4. What connections should be created?

Respond with JSON matching the CurationDecision schema."""

    def __init__(self, settings: "Settings") -> None:
        self.settings = settings

    def curate(self, synthesis: str, topic: str) -> CurationDecision:
        """Decide how to persist a research synthesis.

        Args:
            synthesis: The gate-passing research synthesis text.
            topic: Original research topic for search context.

        Returns:
            CurationDecision describing what action to take and with what content.
        """
        raise NotImplementedError

    def _find_related(self, synthesis: str, top_k: int = 5) -> list[dict]:
        """Search for existing notes related to this synthesis."""
        raise NotImplementedError

    def _format_as_note(self, decision: CurationDecision) -> str:
        """Format curated content using the zettelkasten-note.md template."""
        raise NotImplementedError
