"""Standalone interactive HTML report template generator."""

import json
from datetime import datetime
from pathlib import Path
from typing import Dict, Any


HTML_TEMPLATE = """<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>PyInspect Diagnostic Report — {project_name}</title>
    <style>
        body {{
            background-color: #11111b;
            color: #cdd6f4;
            font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif;
            margin: 0;
            padding: 40px;
        }}
        .header {{
            border-bottom: 2px solid #313244;
            padding-bottom: 20px;
            margin-bottom: 30px;
        }}
        h1 {{ color: #89b4fa; margin: 0 0 10px 0; }}
        .subtitle {{ color: #a6adc8; font-size: 14px; }}
        .cards {{
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
            gap: 20px;
            margin-bottom: 30px;
        }}
        .card {{
            background: #1e1e2e;
            border: 1px solid #313244;
            border-radius: 8px;
            padding: 20px;
        }}
        .card-title {{ color: #a6adc8; font-size: 12px; text-transform: uppercase; margin-bottom: 8px; }}
        .card-value {{ color: #89b4fa; font-size: 28px; font-weight: bold; }}
        table {{
            width: 100%;
            border-collapse: collapse;
            background: #1e1e2e;
            border-radius: 8px;
            overflow: hidden;
            margin-bottom: 30px;
        }}
        th, td {{ padding: 12px 16px; text-align: left; border-bottom: 1px solid #313244; }}
        th {{ background: #181825; color: #89b4fa; }}
        .badge-HIGH, .badge-CRITICAL {{ color: #f38ba8; font-weight: bold; }}
        .badge-MEDIUM {{ color: #f9e2af; font-weight: bold; }}
        .badge-LOW, .badge-INFO {{ color: #a6e3a1; font-weight: bold; }}
    </style>
</head>
<body>
    <div class="header">
        <h1>PyInspect Diagnostic Report</h1>
        <div class="subtitle">Target: <strong>{project_name}</strong> | Generated: {timestamp}</div>
    </div>

    <div class="cards">
        <div class="card">
            <div class="card-title">Project Storage</div>
            <div class="card-value">{total_size_mb} MB</div>
        </div>
        <div class="card">
            <div class="card-title">Total Files</div>
            <div class="card-value">{total_files}</div>
        </div>
        <div class="card">
            <div class="card-title">Python Files</div>
            <div class="card-value">{python_files}</div>
        </div>
        <div class="card">
            <div class="card-title">Health Score</div>
            <div class="card-value" style="color: #a6e3a1;">{health_score} / 100</div>
        </div>
    </div>

    <h2>Detected Findings & Recommendations</h2>
    <table>
        <thead>
            <tr>
                <th>Severity</th>
                <th>Category</th>
                <th>Location</th>
                <th>Evidence & Recommended Action</th>
            </tr>
        </thead>
        <tbody>
            {anomalies_rows}
        </tbody>
    </table>
</body>
</html>
"""


class HtmlExporter:
    """Generates standalone HTML report files."""

    @staticmethod
    def export(report_data: Dict[str, Any], output_path: Path | str) -> Path:
        path = Path(output_path)
        path.parent.mkdir(parents=True, exist_ok=True)

        proj_name = report_data.get("project_name", "PyInspect Target")
        total_size_mb = f"{report_data.get('total_size_bytes', 0) / (1024 * 1024):.1f}"
        total_files = report_data.get("total_files", 0)
        python_files = report_data.get("python_files", 0)
        health_score = report_data.get("health_score", 100)

        anom_rows = []
        for a in report_data.get("anomalies", []):
            sev = getattr(a, "severity", "INFO")
            cat = getattr(a, "category", "general").upper()
            loc = getattr(a, "location", "N/A")
            ev = getattr(a, "evidence", "")
            act = getattr(a, "suggested_action", "")

            row_html = f"""<tr>
                <td class="badge-{sev}">{sev}</td>
                <td>{cat}</td>
                <td>{loc}</td>
                <td><strong>{ev}</strong><br><span style="color:#a6adc8;">{act}</span></td>
            </tr>"""
            anom_rows.append(row_html)

        if not anom_rows:
            anom_rows.append("<tr><td colspan='4' style='color:#a6e3a1;'>✓ No critical anomalies or issues detected!</td></tr>")

        html_content = HTML_TEMPLATE.format(
            project_name=proj_name,
            timestamp=datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            total_size_mb=total_size_mb,
            total_files=total_files,
            python_files=python_files,
            health_score=health_score,
            anomalies_rows="\n".join(anom_rows)
        )

        with open(path, "w", encoding="utf-8") as f:
            f.write(html_content)

        return path
