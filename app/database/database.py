"""SQLite database connection manager and schema initializer."""

import sqlite3
from pathlib import Path
from contextlib import contextmanager
from typing import Generator
from app.core.exceptions import DatabaseError
from app.core.logger import get_logger

logger = get_logger("database")

SCHEMA_SQL = """
CREATE TABLE IF NOT EXISTS projects (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL,
    path TEXT NOT NULL UNIQUE,
    created_at TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS analyses (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    project_id INTEGER NOT NULL,
    timestamp TEXT NOT NULL,
    total_size_bytes INTEGER DEFAULT 0,
    total_files INTEGER DEFAULT 0,
    python_files INTEGER DEFAULT 0,
    health_score INTEGER DEFAULT 100,
    summary_json TEXT DEFAULT '{}',
    FOREIGN KEY(project_id) REFERENCES projects(id) ON DELETE CASCADE
);

CREATE TABLE IF NOT EXISTS file_statistics (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    analysis_id INTEGER NOT NULL,
    relative_path TEXT NOT NULL,
    extension TEXT NOT NULL,
    size_bytes INTEGER NOT NULL,
    is_python INTEGER NOT NULL,
    hash_sha256 TEXT,
    line_count INTEGER,
    FOREIGN KEY(analysis_id) REFERENCES analyses(id) ON DELETE CASCADE
);

CREATE TABLE IF NOT EXISTS memory_snapshots (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    analysis_id INTEGER NOT NULL,
    timestamp TEXT NOT NULL,
    current_bytes INTEGER NOT NULL,
    peak_bytes INTEGER NOT NULL,
    top_allocations_json TEXT DEFAULT '[]',
    FOREIGN KEY(analysis_id) REFERENCES analyses(id) ON DELETE CASCADE
);

CREATE TABLE IF NOT EXISTS log_events (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    analysis_id INTEGER NOT NULL,
    log_level TEXT NOT NULL,
    timestamp TEXT,
    message TEXT NOT NULL,
    is_anomaly INTEGER DEFAULT 0,
    anomaly_reason TEXT,
    FOREIGN KEY(analysis_id) REFERENCES analyses(id) ON DELETE CASCADE
);

CREATE TABLE IF NOT EXISTS anomalies (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    analysis_id INTEGER NOT NULL,
    category TEXT NOT NULL,
    severity TEXT NOT NULL,
    location TEXT NOT NULL,
    evidence TEXT NOT NULL,
    explanation TEXT NOT NULL,
    suggested_action TEXT NOT NULL,
    FOREIGN KEY(analysis_id) REFERENCES analyses(id) ON DELETE CASCADE
);
"""

class Database:
    """SQLite Database manager for PyInspect."""

    def __init__(self, db_path: str | Path = "pyinspect.db"):
        self.db_path = Path(db_path)

    def initialize(self) -> None:
        """Creates table schemas if they do not already exist."""
        try:
            with self.get_connection() as conn:
                conn.executescript(SCHEMA_SQL)
                conn.commit()
            logger.debug(f"Database schema initialized at {self.db_path}")
        except Exception as e:
            raise DatabaseError(
                message="Failed to initialize database tables.",
                details=str(e),
                suggested_action="Verify file write permissions for the database path."
            ) from e

    @contextmanager
    def get_connection(self) -> Generator[sqlite3.Connection, None, None]:
        """Provides a context-managed SQLite connection."""
        conn = None
        try:
            conn = sqlite3.connect(self.db_path)
            conn.row_factory = sqlite3.Row
            conn.execute("PRAGMA foreign_keys = ON;")
            yield conn
        except sqlite3.Error as e:
            if conn:
                conn.rollback()
            raise DatabaseError(
                message="SQLite database error occurred.",
                details=str(e)
            ) from e
        finally:
            if conn:
                conn.close()
