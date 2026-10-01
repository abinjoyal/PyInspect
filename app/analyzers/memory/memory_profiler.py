"""Memory profiler using tracemalloc, psutil, and gc."""

import gc
import sys
import tracemalloc
from dataclasses import dataclass
from pathlib import Path
from typing import List, Optional

try:
    import psutil
    HAS_PSUTIL = True
except ImportError:
    HAS_PSUTIL = False

from app.analyzers.memory.snapshot import (
    MemorySnapshot, MemoryAllocationItem, MemoryDiffItem, MemoryAnalysisResult
)
from app.core.logger import get_logger

logger = get_logger("memory_profiler")


class MemoryProfiler:
    """Manages tracemalloc session, collects snapshots, and compares memory diffs."""

    def __init__(self, key_type: str = "lineno"):
        self.key_type = key_type
        self.snapshots: List[MemorySnapshot] = []
        self._initial_snapshot: Optional[tracemalloc.Snapshot] = None
        self._is_profiling: bool = False
        self._process = psutil.Process() if HAS_PSUTIL else None

    def get_rss_bytes(self) -> int:
        if self._process:
            try:
                return self._process.memory_info().rss
            except Exception:
                pass
        return 0

    def start(self, frames: int = 25):
        if not tracemalloc.is_tracing():
            tracemalloc.start(frames)
        gc.collect()
        self.snapshots.clear()
        self._initial_snapshot = tracemalloc.take_snapshot()
        self._is_profiling = True
        logger.debug("Memory profiling started.")

    def take_snapshot(self) -> MemorySnapshot:
        if not tracemalloc.is_tracing():
            self.start()

        curr_bytes, peak_bytes = tracemalloc.get_traced_memory()
        tm_snapshot = tracemalloc.take_snapshot()
        stats = tm_snapshot.statistics(self.key_type)

        alloc_items = []
        for stat in stats[:15]:
            frame = stat.traceback[0]
            alloc_items.append(
                MemoryAllocationItem(
                    filename=frame.filename,
                    line_number=frame.lineno,
                    size_bytes=stat.size,
                    count=stat.count
                )
            )

        snap = MemorySnapshot(
            current_rss_bytes=self.get_rss_bytes(),
            tracemalloc_current_bytes=curr_bytes,
            tracemalloc_peak_bytes=peak_bytes,
            allocations=alloc_items
        )
        self.snapshots.append(snap)
        return snap

    def stop(self) -> MemoryAnalysisResult:
        if not self._is_profiling:
            return MemoryAnalysisResult(
                initial_rss_bytes=0,
                peak_rss_bytes=0,
                final_rss_bytes=0,
                total_growth_bytes=0
            )

        final_snapshot = tracemalloc.take_snapshot()

        top_diffs = []
        if self._initial_snapshot:
            diff_stats = final_snapshot.compare_to(self._initial_snapshot, self.key_type)
            for stat in diff_stats[:15]:
                frame = stat.traceback[0]
                top_diffs.append(
                    MemoryDiffItem(
                        filename=frame.filename,
                        line_number=frame.lineno,
                        size_diff_bytes=stat.size_diff,
                        count_diff=stat.count_diff
                    )
                )

        init_rss = self.snapshots[0].current_rss_bytes if self.snapshots else 0
        final_rss = self.get_rss_bytes()
        peak_rss = max([s.current_rss_bytes for s in self.snapshots], default=final_rss)
        growth = max(0, final_rss - init_rss)

        self._is_profiling = False
        return MemoryAnalysisResult(
            initial_rss_bytes=init_rss,
            peak_rss_bytes=peak_rss,
            final_rss_bytes=final_rss,
            total_growth_bytes=growth,
            snapshots=self.snapshots,
            top_diffs=top_diffs
        )
