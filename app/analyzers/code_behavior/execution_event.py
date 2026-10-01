"""Dataclasses representing runtime execution events and call trees."""

from dataclasses import dataclass, field
from typing import Dict, Any, List, Optional


@dataclass
class VariableSnapshot:
    name: str
    value_repr: str
    type_name: str
    is_modified: bool = False


@dataclass
class ExecutionEvent:
    event_type: str  # 'call', 'line', 'return', 'exception'
    filename: str
    func_name: str
    line_number: int
    timestamp_ms: float
    locals_snapshot: Dict[str, VariableSnapshot] = field(default_factory=dict)
    globals_snapshot: Dict[str, VariableSnapshot] = field(default_factory=dict)
    return_value_repr: Optional[str] = None
    exception_repr: Optional[str] = None
    duration_ms: float = 0.0


@dataclass
class CallNode:
    func_name: str
    filename: str
    line_number: int
    duration_ms: float = 0.0
    children: List['CallNode'] = field(default_factory=list)
    events: List[ExecutionEvent] = field(default_factory=list)
