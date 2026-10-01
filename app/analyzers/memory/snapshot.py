"""Dataclass models for memory allocation snapshots and differential analysis."""

from dataclasses import dataclass, field
from datetime import datetime
from typing import List, Dict, Optional


@dataclass
class MemoryAllocationItem:
    filename: str
    line_number: int
    size_bytes: int
    count: int
    formatted_size: str = ""

    def __post_init__(self):
        sz = self.size_bytes
        for unit in ['B', 'KB', 'MB', 'GB']:
            if abs(sz) < 1024.0:
                self.formatted_size = f"{sz:3.1f} {unit}"
                break
            sz /= 1024.0
        else:
            self.formatted_size = f"{sz:.1f} TB"


@dataclass
class MemorySnapshot:
    timestamp: str = field(default_factory=lambda: datetime.now().isoformat())
    current_rss_bytes: int = 0
    tracemalloc_current_bytes: int = 0
    tracemalloc_peak_bytes: int = 0
    allocations: List[MemoryAllocationItem] = field(default_factory=list)


@dataclass
class MemoryDiffItem:
    filename: str
    line_number: int
    size_diff_bytes: int
    count_diff: int
    formatted_diff: str = ""

    def __post_init__(self):
        sz = self.size_diff_bytes
        sign = "+" if sz >= 0 else ""
        abs_sz = abs(sz)
        for unit in ['B', 'KB', 'MB', 'GB']:
            if abs_sz < 1024.0:
                self.formatted_diff = f"{sign}{sz:3.1f} {unit}"
                break
            abs_sz /= 1024.0
        else:
            self.formatted_diff = f"{sign}{sz:.1f} TB"


@dataclass
class MemoryAnalysisResult:
    initial_rss_bytes: int
    peak_rss_bytes: int
    final_rss_bytes: int
    total_growth_bytes: int
    snapshots: List[MemorySnapshot] = field(default_factory=list)
    top_diffs: List[MemoryDiffItem] = field(default_factory=list)
    leak_classification: str = "Normal growth"  # Normal growth, Suspicious growth, Potential leak
