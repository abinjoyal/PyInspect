"""Repository pattern for persisting and querying PyInspect diagnostic data."""

import json
from typing import Optional, List, Dict, Any, Tuple
from app.database.database import Database
from app.database.models import (
    ProjectRecord, AnalysisRecord, FileStatRecord, AnomalyRecord
)
from app.core.logger import get_logger

logger = get_logger("repository")


class Repository:
    """CRUD operations for storing project scans, file statistics, anomalies, and historical comparison."""

    def __init__(self, db: Database):
        self.db = db

    def get_or_create_project(self, name: str, path: str) -> ProjectRecord:
        """Finds an existing project record by path or creates a new one."""
        with self.db.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT id, name, path, created_at FROM projects WHERE path = ?", (path,))
            row = cursor.fetchone()
            if row:
                return ProjectRecord(
                    id=row["id"],
                    name=row["name"],
                    path=row["path"],
                    created_at=row["created_at"]
                )

            cursor.execute(
                "INSERT INTO projects (name, path, created_at) VALUES (?, ?, datetime('now'))",
                (name, path)
            )
            conn.commit()
            project_id = cursor.lastrowid
            
            cursor.execute("SELECT id, name, path, created_at FROM projects WHERE id = ?", (project_id,))
            row = cursor.fetchone()
            return ProjectRecord(
                id=row["id"],
                name=row["name"],
                path=row["path"],
                created_at=row["created_at"]
            )

    def save_analysis(
        self,
        project_id: int,
        total_size_bytes: int,
        total_files: int,
        python_files: int,
        health_score: int,
        summary: Dict[str, Any],
        file_stats: List[FileStatRecord],
        anomalies: List[AnomalyRecord]
    ) -> int:
        """Saves a complete analysis run along with file stats and anomalies."""
        with self.db.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                """
                INSERT INTO analyses (
                    project_id, timestamp, total_size_bytes, total_files, python_files, health_score, summary_json
                ) VALUES (?, datetime('now'), ?, ?, ?, ?, ?)
                """,
                (
                    project_id,
                    total_size_bytes,
                    total_files,
                    python_files,
                    health_score,
                    json.dumps(summary)
                )
            )
            analysis_id = cursor.lastrowid

            # Save file stats
            file_rows = [
                (
                    analysis_id,
                    fs.relative_path,
                    fs.extension,
                    fs.size_bytes,
                    1 if fs.is_python else 0,
                    fs.hash_sha256,
                    fs.line_count
                )
                for fs in file_stats
            ]
            cursor.executemany(
                """
                INSERT INTO file_statistics (
                    analysis_id, relative_path, extension, size_bytes, is_python, hash_sha256, line_count
                ) VALUES (?, ?, ?, ?, ?, ?, ?)
                """,
                file_rows
            )

            # Save anomalies
            anomaly_rows = [
                (
                    analysis_id,
                    a.category,
                    a.severity,
                    a.location,
                    a.evidence,
                    a.explanation,
                    a.suggested_action
                )
                for a in anomalies
            ]
            cursor.executemany(
                """
                INSERT INTO anomalies (
                    analysis_id, category, severity, location, evidence, explanation, suggested_action
                ) VALUES (?, ?, ?, ?, ?, ?, ?)
                """,
                anomaly_rows
            )

            conn.commit()
            logger.debug(f"Saved analysis #{analysis_id} for project #{project_id}")
            return analysis_id

    def get_latest_analyses(self, project_id: int, limit: int = 5) -> List[AnalysisRecord]:
        """Gets the most recent analysis runs for a project."""
        with self.db.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                """
                SELECT id, project_id, timestamp, total_size_bytes, total_files, python_files, health_score, summary_json
                FROM analyses
                WHERE project_id = ?
                ORDER BY id DESC
                LIMIT ?
                """,
                (project_id, limit)
            )
            rows = cursor.fetchall()
            return [
                AnalysisRecord(
                    id=row["id"],
                    project_id=row["project_id"],
                    timestamp=row["timestamp"],
                    total_size_bytes=row["total_size_bytes"],
                    total_files=row["total_files"],
                    python_files=row["python_files"],
                    health_score=row["health_score"],
                    summary_json=row["summary_json"]
                )
                for row in rows
            ]

    def compare_analyses(self, analysis_id_1: int, analysis_id_2: int) -> Dict[str, Any]:
        """Compares two historical analyses and returns the differences."""
        with self.db.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM analyses WHERE id = ?", (analysis_id_1,))
            a1 = cursor.fetchone()
            cursor.execute("SELECT * FROM analyses WHERE id = ?", (analysis_id_2,))
            a2 = cursor.fetchone()

            if not a1 or not a2:
                return {"error": "One or both analysis records were not found."}

            size_diff = a2["total_size_bytes"] - a1["total_size_bytes"]
            files_diff = a2["total_files"] - a1["total_files"]
            health_diff = a2["health_score"] - a1["health_score"]

            return {
                "before": {
                    "id": a1["id"],
                    "timestamp": a1["timestamp"],
                    "total_size_bytes": a1["total_size_bytes"],
                    "total_files": a1["total_files"],
                    "health_score": a1["health_score"]
                },
                "after": {
                    "id": a2["id"],
                    "timestamp": a2["timestamp"],
                    "total_size_bytes": a2["total_size_bytes"],
                    "total_files": a2["total_files"],
                    "health_score": a2["health_score"]
                },
                "delta": {
                    "size_bytes": size_diff,
                    "total_files": files_diff,
                    "health_score": health_diff
                }
            }
