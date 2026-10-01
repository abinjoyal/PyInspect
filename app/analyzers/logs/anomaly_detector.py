"""Log Anomaly Detector facade integrating statistics and pattern clustering."""

from collections import Counter
from dataclasses import dataclass, field
from typing import List, Dict
from app.analyzers.logs.log_parser import LogEntry
from app.analyzers.logs.pattern_detector import PatternDetector, LogPatternMatch
from app.database.models import AnomalyRecord
from app.core.constants import Severity


@dataclass
class LogAnalysisSummary:
    total_events: int
    level_counts: Dict[str, int]
    pattern_matches: List[LogPatternMatch]
    log_health_score: int
    anomalies: List[AnomalyRecord] = field(default_factory=list)


class LogAnomalyDetector:
    """Analyzes log event frequency, error spikes, and recurring failure signatures."""

    @staticmethod
    def analyze_logs(entries: List[LogEntry]) -> LogAnalysisSummary:
        total_events = len(entries)
        level_counts: Dict[str, int] = Counter([e.level for e in entries])

        pattern_matches = PatternDetector.detect_patterns(entries)
        anomalies: List[AnomalyRecord] = []

        errors_count = level_counts.get("ERROR", 0) + level_counts.get("CRITICAL", 0)
        error_percentage = (errors_count / total_events * 100.0) if total_events > 0 else 0.0

        # Anomaly 1: High Error Rate
        if error_percentage > 5.0:
            anomalies.append(
                AnomalyRecord(
                    id=None,
                    analysis_id=0,
                    category="logs",
                    severity=Severity.HIGH if error_percentage > 15.0 else Severity.MEDIUM,
                    location="Log Stream",
                    evidence=f"{errors_count} errors/criticals ({error_percentage:.1f}% of total events)",
                    explanation="Elevated ratio of error and critical log entries detected.",
                    suggested_action="Review log stack traces and fix recurring exception causes."
                )
            )

        # Anomaly 2: Pattern Spike Alerts
        for p in pattern_matches:
            if p.count >= 3:
                anomalies.append(
                    AnomalyRecord(
                        id=None,
                        analysis_id=0,
                        category="logs",
                        severity=p.severity,
                        location=f"Line #{p.sample_entry.line_number}",
                        evidence=f"Pattern '{p.pattern_name}' matched {p.count} times",
                        explanation=f"Sample: {p.sample_entry.message[:80]}",
                        suggested_action=f"Investigate cause of repeated '{p.pattern_name}' errors."
                    )
                )

        # Health score calculation
        health_score = 100
        health_score -= int(error_percentage * 2)
        for p in pattern_matches:
            if p.severity == Severity.CRITICAL:
                health_score -= 15
            elif p.severity == Severity.HIGH:
                health_score -= 10
            elif p.severity == Severity.MEDIUM:
                health_score -= 5

        health_score = max(0, min(100, health_score))

        return LogAnalysisSummary(
            total_events=total_events,
            level_counts=dict(level_counts),
            pattern_matches=pattern_matches,
            log_health_score=health_score,
            anomalies=anomalies
        )
