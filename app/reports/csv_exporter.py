"""CSV report exporter for file statistics and anomalies."""

import csv
from pathlib import Path
from typing import List, Dict, Any


class CsvExporter:
    """Exports structured file statistics and anomaly findings to CSV."""

    @staticmethod
    def export_anomalies(anomalies: List[Any], output_path: Path | str) -> Path:
        path = Path(output_path)
        path.parent.mkdir(parents=True, exist_ok=True)

        fieldnames = ["severity", "category", "location", "evidence", "explanation", "suggested_action"]
        with open(path, "w", newline="", encoding="utf-8") as f:
            writer = csv.DictWriter(f, fieldnames=fieldnames)
            writer.writeheader()
            for a in anomalies:
                writer.writerow({
                    "severity": getattr(a, "severity", "INFO"),
                    "category": getattr(a, "category", "general"),
                    "location": getattr(a, "location", "N/A"),
                    "evidence": getattr(a, "evidence", ""),
                    "explanation": getattr(a, "explanation", ""),
                    "suggested_action": getattr(a, "suggested_action", "")
                })

        return path
