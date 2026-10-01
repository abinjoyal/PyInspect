"""JSON report exporter."""

import json
from dataclasses import asdict
from datetime import datetime
from pathlib import Path
from typing import Dict, Any


class JsonExporter:
    """Exports diagnostic results into formatted JSON files."""

    @staticmethod
    def export(report_data: Dict[str, Any], output_path: Path | str) -> Path:
        path = Path(output_path)
        path.parent.mkdir(parents=True, exist_ok=True)

        payload = {
            "pyinspect_version": "0.1.0",
            "timestamp": datetime.now().isoformat(),
            "data": report_data
        }

        with open(path, "w", encoding="utf-8") as f:
            json.dump(payload, f, indent=2, default=str)

        return path
