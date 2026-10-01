"""Runtime execution tracer using sys.settrace() with strict safety boundaries."""

import sys
import time
import inspect
from pathlib import Path
from typing import List, Dict, Any, Optional
from app.analyzers.code_behavior.execution_event import ExecutionEvent, VariableSnapshot
from app.core.logger import get_logger

logger = get_logger("tracer")


def safe_repr(val: Any, max_len: int = 100) -> str:
    """Safely produces string representations without crashing or blowing memory."""
    try:
        r = repr(val)
        if len(r) > max_len:
            return r[:max_len] + "..."
        return r
    except Exception:
        return "<unrepresentable object>"


class CodeTracer:
    """Traces Python script execution step-by-step capturing calls, lines, returns, and variable mutations."""

    def __init__(self, target_script: Path | str, max_depth: int = 15, timeout_sec: float = 10.0):
        self.target_script = Path(target_script).resolve()
        self.max_depth = max_depth
        self.timeout_sec = timeout_sec
        self.events: List[ExecutionEvent] = []
        self._start_time: float = 0.0
        self._previous_locals: Dict[str, str] = {}

    def _create_snapshot(self, local_vars: dict) -> Dict[str, VariableSnapshot]:
        snapshot = {}
        for name, val in local_vars.items():
            if name.startswith("__"):
                continue
            val_repr = safe_repr(val)
            prev_val = self._previous_locals.get(name)
            is_modified = prev_val is not None and prev_val != val_repr
            self._previous_locals[name] = val_repr

            snapshot[name] = VariableSnapshot(
                name=name,
                value_repr=val_repr,
                type_name=type(val).__name__,
                is_modified=is_modified
            )
        return snapshot

    def trace_func(self, frame, event: str, arg: Any):
        if time.time() - self._start_time > self.timeout_sec:
            sys.settrace(None)
            logger.warning("Execution tracing timeout reached.")
            return None

        co = frame.f_code
        filename = co.co_filename

        # Only trace code executing within or under the target script directory/file
        if not filename.endswith(self.target_script.name) and not str(self.target_script.parent) in filename:
            return self.trace_func

        func_name = co.co_name
        line_number = frame.f_lineno
        now_ms = (time.time() - self._start_time) * 1000.0

        if event == "call":
            self.events.append(
                ExecutionEvent(
                    event_type="call",
                    filename=filename,
                    func_name=func_name,
                    line_number=line_number,
                    timestamp_ms=now_ms,
                    locals_snapshot=self._create_snapshot(frame.f_locals)
                )
            )
        elif event == "line":
            self.events.append(
                ExecutionEvent(
                    event_type="line",
                    filename=filename,
                    func_name=func_name,
                    line_number=line_number,
                    timestamp_ms=now_ms,
                    locals_snapshot=self._create_snapshot(frame.f_locals)
                )
            )
        elif event == "return":
            self.events.append(
                ExecutionEvent(
                    event_type="return",
                    filename=filename,
                    func_name=func_name,
                    line_number=line_number,
                    timestamp_ms=now_ms,
                    locals_snapshot=self._create_snapshot(frame.f_locals),
                    return_value_repr=safe_repr(arg)
                )
            )
        elif event == "exception":
            exc_type, exc_val, _ = arg
            self.events.append(
                ExecutionEvent(
                    event_type="exception",
                    filename=filename,
                    func_name=func_name,
                    line_number=line_number,
                    timestamp_ms=now_ms,
                    locals_snapshot=self._create_snapshot(frame.f_locals),
                    exception_repr=f"{exc_type.__name__}: {safe_repr(exc_val)}"
                )
            )

        return self.trace_func

    def run_and_trace(self) -> List[ExecutionEvent]:
        """Executes the target script within the tracer context."""
        self.events.clear()
        self._start_time = time.time()
        self._previous_locals.clear()

        global_ns = {"__file__": str(self.target_script), "__name__": "__main__"}
        
        old_trace = sys.gettrace()
        sys.settrace(self.trace_func)
        try:
            with open(self.target_script, "r", encoding="utf-8") as f:
                code_obj = compile(f.read(), str(self.target_script), "exec")
                exec(code_obj, global_ns)
        except Exception as e:
            logger.warning(f"Exception raised during traced execution of {self.target_script}: {e}")
        finally:
            sys.settrace(old_trace)

        return self.events
