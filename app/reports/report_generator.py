"""Unified Report Generator facade."""

from pathlib import Path
from typing import Dict, Any, List
from app.reports.json_exporter import JsonExporter
from app.reports.csv_exporter import CsvExporter
from app.reports.html_exporter import HtmlExporter


class ReportGenerator:
    """Facade for exporting PyInspect diagnostic summaries into HTML, JSON, or CSV formats."""

    @staticmethod
    def generate_all_reports(report_data: Dict[str, Any], output_dir: Path | str) -> Dict[str, Path]:
        out_dir = Path(output_dir).resolve()
        out_dir.mkdir(parents=True, exist_ok=True)

        json_file = JsonExporter.export(report_data, out_dir / "report.json")
        html_file = HtmlExporter.export(report_data, out_dir / "report.html")
        csv_file = CsvExporter.export_anomalies(report_data.get("anomalies", []), out_dir / "anomalies.csv")

        return {
            "json": json_file,
            "html": html_file,
            "csv": csv_file
        }
