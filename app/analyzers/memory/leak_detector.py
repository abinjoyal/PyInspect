"""Heuristic leak detector for classifying memory growth patterns."""

from typing import List
from app.analyzers.memory.snapshot import MemoryAnalysisResult, MemoryDiffItem
from app.database.models import AnomalyRecord
from app.core.constants import Severity


class MemoryLeakDetector:
    """Evaluates memory growth and snapshot diffs to identify potential leaks."""

    @staticmethod
    def detect_leaks(result: MemoryAnalysisResult, growth_threshold_mb: float = 20.0) -> List[AnomalyRecord]:
        anomalies: List[AnomalyRecord] = []
        growth_mb = result.total_growth_bytes / (1024 * 1024)

        if growth_mb < 5.0:
            result.leak_classification = "Normal growth"
            return anomalies

        if growth_mb >= growth_threshold_mb:
            result.leak_classification = "Potential leak"
            severity = Severity.HIGH if growth_mb > 100 else Severity.MEDIUM
        else:
            result.leak_classification = "Suspicious growth"
            severity = Severity.LOW

        # Inspect top differential memory consumers
        for diff in result.top_diffs[:5]:
            diff_mb = diff.size_diff_bytes / (1024 * 1024)
            if diff_mb >= 2.0:  # If a single line accumulated > 2MB
                anomalies.append(
                    AnomalyRecord(
                        id=None,
                        analysis_id=0,
                        category="memory",
                        severity=severity,
                        location=f"{diff.filename}:{diff.line_number}",
                        evidence=f"Memory net change: {diff.formatted_diff} ({diff.count_diff:+d} objects)",
                        explanation=f"Line {diff.line_number} in '{diff.filename}' retained {diff_mb:.2f} MB across profiling snapshots.",
                        suggested_action="Check for unclosed resource handles, growing global caches, or circular references."
                    )
                )

        return anomalies
