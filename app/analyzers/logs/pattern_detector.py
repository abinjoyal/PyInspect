"""Pattern detector for identifying common application log failures."""

import re
from dataclasses import dataclass
from typing import List, Dict
from app.analyzers.logs.log_parser import LogEntry


@dataclass
class LogPatternMatch:
    pattern_name: str
    count: int
    sample_entry: LogEntry
    severity: str  # CRITICAL, HIGH, MEDIUM, LOW


KNOWN_PATTERNS = [
    ("Database Failure", re.compile(r"(database|db|postgres|mysql|sqlite|conn).*?(fail|error|refused|timeout|disconnect)", re.IGNORECASE), "CRITICAL"),
    ("HTTP 500 Spike", re.compile(r"HTTP\s+500|Internal\s+Server\s+Error|500\s+Internal", re.IGNORECASE), "HIGH"),
    ("Authentication Failure", re.compile(r"(auth|login|token|permission|unauthorized|401|403).*?(fail|denied|invalid|expired)", re.IGNORECASE), "MEDIUM"),
    ("Timeout Pattern", re.compile(r"(timeout|timed out|deadline exceeded)", re.IGNORECASE), "MEDIUM"),
    ("Unhandled Exception Burst", re.compile(r"(Traceback \(most recent call last\)|Unhandled Exception|NullPointerException|AttributeError)", re.IGNORECASE), "HIGH"),
]


class PatternDetector:
    """Detects recurring failure signatures and clusters log pattern frequencies."""

    @staticmethod
    def detect_patterns(entries: List[LogEntry]) -> List[LogPatternMatch]:
        pattern_counts: Dict[str, int] = {}
        samples: Dict[str, LogEntry] = {}
        severities: Dict[str, str] = {}

        for entry in entries:
            text = f"{entry.message} {entry.raw_line}"
            for name, regex, sev in KNOWN_PATTERNS:
                if regex.search(text):
                    pattern_counts[name] = pattern_counts.get(name, 0) + 1
                    if name not in samples:
                        samples[name] = entry
                        severities[name] = sev

        results = []
        for name, count in pattern_counts.items():
            results.append(
                LogPatternMatch(
                    pattern_name=name,
                    count=count,
                    sample_entry=samples[name],
                    severity=severities[name]
                )
            )

        return sorted(results, key=lambda p: p.count, reverse=True)
