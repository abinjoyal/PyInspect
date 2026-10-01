"""Unit tests for MemoryProfiler and MemoryLeakDetector."""

import pytest
import time
from app.analyzers.memory.memory_profiler import MemoryProfiler
from app.analyzers.memory.leak_detector import MemoryLeakDetector


def test_memory_profiler_and_leak_detector():
    profiler = MemoryProfiler()
    profiler.start()

    # Allocate temporary memory buffer
    buf = [b"X" * 1024 * 1024 for _ in range(10)]  # 10MB
    profiler.take_snapshot()

    res = profiler.stop()

    assert res is not None
    assert len(res.snapshots) >= 1
    assert len(res.top_diffs) >= 0

    anomalies = MemoryLeakDetector.detect_leaks(res, growth_threshold_mb=1.0)
    assert isinstance(anomalies, list)
