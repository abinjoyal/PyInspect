"""Analyzer that transforms raw execution events into call trees and execution timelines."""

from dataclasses import dataclass, field
from typing import List, Dict, Optional
from app.analyzers.code_behavior.execution_event import ExecutionEvent, CallNode


@dataclass
class BehaviorAnalysisResult:
    events: List[ExecutionEvent]
    call_tree_root: CallNode
    total_execution_time_ms: float
    total_events: int
    function_durations: Dict[str, float]
    frequent_lines: Dict[int, int]  # line_no -> execution_count


class BehaviorAnalyzer:
    """Builds call hierarchy tree and summary statistics from traced execution events."""

    @staticmethod
    def analyze_events(events: List[ExecutionEvent]) -> BehaviorAnalysisResult:
        if not events:
            root = CallNode(func_name="root", filename="", line_number=0)
            return BehaviorAnalysisResult(
                events=[],
                call_tree_root=root,
                total_execution_time_ms=0.0,
                total_events=0,
                function_durations={},
                frequent_lines={}
            )

        root = CallNode(func_name="<main>", filename=events[0].filename, line_number=events[0].line_number)
        stack = [root]
        func_durations: Dict[str, float] = {}
        line_counts: Dict[int, int] = {}
        call_start_times: Dict[str, float] = {}

        for evt in events:
            if evt.event_type == "line":
                line_counts[evt.line_number] = line_counts.get(evt.line_number, 0) + 1
                if stack:
                    stack[-1].events.append(evt)

            elif evt.event_type == "call":
                node = CallNode(
                    func_name=evt.func_name,
                    filename=evt.filename,
                    line_number=evt.line_number
                )
                if stack:
                    stack[-1].children.append(node)
                stack.append(node)
                call_start_times[evt.func_name] = evt.timestamp_ms

            elif evt.event_type == "return":
                if len(stack) > 1:
                    popped = stack.pop()
                    start_t = call_start_times.get(evt.func_name, evt.timestamp_ms)
                    dur = evt.timestamp_ms - start_t
                    popped.duration_ms = max(0.0, dur)
                    func_durations[evt.func_name] = func_durations.get(evt.func_name, 0.0) + dur

        total_time = events[-1].timestamp_ms - events[0].timestamp_ms if events else 0.0

        return BehaviorAnalysisResult(
            events=events,
            call_tree_root=root,
            total_execution_time_ms=max(0.0, total_time),
            total_events=len(events),
            function_durations=func_durations,
            frequent_lines=line_counts
        )
