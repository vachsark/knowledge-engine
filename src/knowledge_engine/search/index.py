"""
SQLite-backed search index for both BM25 full-text and vector embeddings.

Uses sqlite-utils for schema management and sqlite's FTS5 extension for BM25.
Embedding vectors are stored as binary blobs and compared with cosine similarity.
"""

from __future__ import annotations

from pathlib import Path
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    import sqlite_utils
    from knowledge_engine.config.settings import Settings


class SearchIndex:
    """Manages the SQLite FTS5 and vector stores for hybrid search.

    Schema:
        documents(id TEXT, title TEXT, content TEXT, path TEXT, created_at TEXT)
        documents_fts(content)  -- FTS5 virtual table mirroring documents
        embeddings(doc_id TEXT, vector BLOB, model TEXT)
    """

    def __init__(self, settings: "Settings") -> None:
        self.settings = settings
        self.db_path = settings.knowledge_dir / ".index" / "search.db"
        self._db: "sqlite_utils.Database | None" = None

    @property
    def db(self) -> "sqlite_utils.Database":
        """Lazy-open (and migrate) the SQLite database."""
        raise NotImplementedError

    def ensure_schema(self) -> None:
        """Create tables and FTS5 virtual table if they don't exist."""
        raise NotImplementedError

    def upsert_document(
        self, doc_id: str, title: str, content: str, path: str
    ) -> None:
        """Insert or replace a document and update FTS5 + embedding indexes."""
        raise NotImplementedError

    def delete_document(self, doc_id: str) -> None:
        """Remove a document from all indexes."""
        raise NotImplementedError

    def bm25_query(self, query: str, top_k: int) -> list[dict]:
        """Execute FTS5 BM25 query, return ranked rows with bm25() score."""
        raise NotImplementedError

    def vector_query(self, embedding: list[float], top_k: int) -> list[dict]:
        """Cosine similarity search over stored embeddings.

        Note: This is a full scan — acceptable for <10k documents.
        Replace with sqlite-vss or hnswlib for larger corpora.
        """
        raise NotImplementedError

    def count(self) -> int:
        """Return total number of indexed documents."""
        raise NotImplementedError

    def rebuild_fts(self) -> None:
        """Drop and rebuild the FTS5 index (use after bulk inserts)."""
        raise NotImplementedError
