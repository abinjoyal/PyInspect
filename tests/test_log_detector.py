"""Unit tests for LogParser, PatternDetector, and LogAnomalyDetector."""

import pytest
from pathlib import Path
from app.analyzers.logs.log_parser import LogParser
from app.analyzers.logs.pattern_detector import PatternDetector
from app.analyzers.logs.anomaly_detector import LogAnomalyDetector


def test_log_parser_and_anomaly_detector(tmp_path):
    log_file = tmp_path / "app.log"
    log_file.write_text(
        """2026-09-30 10:00:00 INFO System started
2026-09-30 10:00:05 ERROR Database connection failed: refused
2026-09-30 10:00:06 ERROR Database connection failed: refused
2026-09-30 10:00:07 ERROR Database connection failed: refused
2026-09-30 10:00:10 CRITICAL HTTP 500 Internal Server Error
""",
        encoding="utf-8"
    )

    entries = LogParser.parse_file(log_file)
    assert len(entries) == 5
    assert entries[1].level == "ERROR"

    summary = LogAnomalyDetector.analyze_logs(entries)

    assert summary.total_events == 5
    assert summary.level_counts.get("ERROR") == 3
    assert len(summary.pattern_matches) >= 1
    assert any(p.pattern_name == "Database Failure" for p in summary.pattern_matches)
    assert summary.log_health_score < 100
