"""Multi-format streaming log parser for raw text logs and JSON Lines."""

import json
import re
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import List, Generator, Optional, Dict
from app.core.logger import get_logger

logger = get_logger("log_parser")


@dataclass
class LogEntry:
    timestamp_str: Optional[str]
    level: str  # INFO, WARNING, ERROR, CRITICAL, DEBUG, UNKNOWN
    message: str
    raw_line: str
    line_number: int
    metadata: Dict[str, str] = field(default_factory=dict)


DEFAULT_PATTERNS = [
    # 2026-09-30 10:20:14 ERROR Database connection failed
    re.compile(r"^(?P<timestamp>\d{4}-\d{2}-\d{2}\s+\d{2}:\d{2}:\d{2})\s+(?P<level>INFO|WARNING|WARN|ERROR|CRITICAL|DEBUG)\s+(?P<message>.*)$", re.IGNORECASE),
    # [2026-09-30T10:20:14] [ERROR] Database failure
    re.compile(r"^\[(?P<timestamp>.*?)\]\s+\[(?P<level>.*?)\]\s+(?P<message>.*)$", re.IGNORECASE),
    # 2026-09-30 10:20:14,123 - mymodule - ERROR - msg
    re.compile(r"^(?P<timestamp>\d{4}-\d{2}-\d{2}\s+\d{2}:\d{2}:\d{2}(?:,\d+)?)\s*-\s*(?P<logger>.*?)\s*-\s*(?P<level>INFO|WARNING|WARN|ERROR|CRITICAL|DEBUG)\s*-\s*(?P<message>.*)$", re.IGNORECASE)
]


class LogParser:
    """Parses raw log files and JSON log streams into structured LogEntry dataclasses."""

    @staticmethod
    def parse_file(file_path: Path | str, max_lines: int = 100_000) -> List[LogEntry]:
        path = Path(file_path)
        if not path.is_file():
            return []

        entries: List[LogEntry] = []
        is_json = path.suffix.lower() in [".json", ".jsonl"]

        try:
            with open(path, "r", encoding="utf-8", errors="ignore") as f:
                for line_idx, line in enumerate(f, start=1):
                    if line_idx > max_lines:
                        break
                    line_str = line.strip()
                    if not line_str:
                        continue

                    if is_json:
                        entry = LogParser._parse_json_line(line_str, line_idx)
                    else:
                        entry = LogParser._parse_text_line(line_str, line_idx)
                    
                    if entry:
                        entries.append(entry)
        except Exception as e:
            logger.warning(f"Error reading log file {path}: {e}")

        return entries

    @staticmethod
    def _parse_json_line(line: str, line_number: int) -> Optional[LogEntry]:
        try:
            data = json.loads(line)
            level = str(data.get("level") or data.get("levelname") or data.get("severity") or "INFO").upper()
            msg = str(data.get("message") or data.get("msg") or data.get("event") or line)
            ts = data.get("timestamp") or data.get("time") or data.get("asctime")
            return LogEntry(
                timestamp_str=str(ts) if ts else None,
                level=level,
                message=msg,
                raw_line=line,
                line_number=line_number,
                metadata={k: str(v) for k, v in data.items() if k not in ["level", "levelname", "message", "msg", "timestamp"]}
            )
        except json.JSONDecodeError:
            return LogParser._parse_text_line(line, line_number)

    @staticmethod
    def _parse_text_line(line: str, line_number: int) -> LogEntry:
        for regex in DEFAULT_PATTERNS:
            match = regex.match(line)
            if match:
                gd = match.groupdict()
                level = gd.get("level", "INFO").upper()
                if level == "WARN":
                    level = "WARNING"
                return LogEntry(
                    timestamp_str=gd.get("timestamp"),
                    level=level,
                    message=gd.get("message", line),
                    raw_line=line,
                    line_number=line_number
                )

        # Fallback unformatted line
        level = "INFO"
        if "ERROR" in line.upper():
            level = "ERROR"
        elif "WARNING" in line.upper() or "WARN" in line.upper():
            level = "WARNING"
        elif "CRITICAL" in line.upper() or "FATAL" in line.upper():
            level = "CRITICAL"

        return LogEntry(
            timestamp_str=None,
            level=level,
            message=line,
            raw_line=line,
            line_number=line_number
        )
