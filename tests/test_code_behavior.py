"""Unit tests for CodeTracer and BehaviorAnalyzer."""

import pytest
from pathlib import Path
from app.analyzers.code_behavior.tracer import CodeTracer
from app.analyzers.code_behavior.behavior_analyzer import BehaviorAnalyzer


def test_code_tracer_and_analyzer(tmp_path):
    script_file = tmp_path / "sample_traced.py"
    script_file.write_text(
        """
def compute(a, b):
    x = a + b
    y = x * 2
    return y

res = compute(5, 10)
""",
        encoding="utf-8"
    )

    tracer = CodeTracer(target_script=script_file, timeout_sec=5.0)
    events = tracer.run_and_trace()

    assert len(events) > 0

    result = BehaviorAnalyzer.analyze_events(events)

    assert result.total_events == len(events)
    assert result.call_tree_root is not None
    assert "compute" in result.function_durations or any(e.func_name == "compute" for e in events)
