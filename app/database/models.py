"""Dataclass models representing SQLite records."""

from dataclasses import dataclass, field
from datetime import datetime
from typing import Optional, List, Dict, Any


@dataclass
class ProjectRecord:
    id: Optional[int]
    name: str
    path: str
    created_at: str = field(default_factory=lambda: datetime.now().isoformat())


@dataclass
class AnalysisRecord:
    id: Optional[int]
    project_id: int
    timestamp: str = field(default_factory=lambda: datetime.now().isoformat())
    total_size_bytes: int = 0
    total_files: int = 0
    python_files: int = 0
    health_score: int = 100
    summary_json: str = "{}"


@dataclass
class FileStatRecord:
    id: Optional[int]
    analysis_id: int
    relative_path: str
    extension: str
    size_bytes: int
    is_python: bool
    hash_sha256: Optional[str] = None
    line_count: Optional[int] = None


@dataclass
class MemorySnapshotRecord:
    id: Optional[int]
    analysis_id: int
    timestamp: str
    current_bytes: int
    peak_bytes: int
    top_allocations_json: str = "[]"


@dataclass
class LogEventRecord:
    id: Optional[int]
    analysis_id: int
    log_level: str
    timestamp: Optional[str]
    message: str
    is_anomaly: bool = False
    anomaly_reason: Optional[str] = None


@dataclass
class AnomalyRecord:
    id: Optional[int]
    analysis_id: int
    category: str  # memory, log, size, code
    severity: str  # INFO, LOW, MEDIUM, HIGH, CRITICAL
    location: str
    evidence: str
    explanation: str
    suggested_action: str
