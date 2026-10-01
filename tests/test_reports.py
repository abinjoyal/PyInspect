"""Unit tests for ReportGenerator, JsonExporter, CsvExporter, and HtmlExporter."""

import pytest
from pathlib import Path
from app.reports.report_generator import ReportGenerator
from app.reports.json_exporter import JsonExporter
from app.reports.csv_exporter import CsvExporter
from app.reports.html_exporter import HtmlExporter


def test_report_generation(tmp_path):
    report_data = {
        "project_name": "TestProject",
        "total_size_bytes": 1024 * 1024 * 15,
        "total_files": 42,
        "python_files": 12,
        "health_score": 85,
        "anomalies": []
    }

    results = ReportGenerator.generate_all_reports(report_data, tmp_path)

    assert results["json"].exists()
    assert results["html"].exists()
    assert results["csv"].exists()

    # Check HTML output content
    html_text = results["html"].read_text(encoding="utf-8")
    assert "TestProject" in html_text
    assert "85 / 100" in html_text
