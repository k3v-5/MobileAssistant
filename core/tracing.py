from pydantic import BaseModel, Field
from typing import List, Optional, Any, Dict
from datetime import datetime

class TraceRecord(BaseModel):
    trace_id: str
    task_id: Optional[str] = None
    timestamp: datetime = Field(default_factory=datetime.now)
    intent: Optional[str] = None
    router_decision: Optional[str] = None
    tools_called: List[str] = Field(default_factory=list)
    latency_ms: Dict[str, float] = Field(default_factory=dict)
    tokens_used: int = 0
    errors: List[str] = Field(default_factory=list)
    result: Optional[str] = None

class ExecutionTracer:
    """
    Handles observability (tracing, latency, errors, token usage).
    """
    def __init__(self):
        self.traces: Dict[str, TraceRecord] = {}

    def start_trace(self, trace_id: str, task_id: Optional[str] = None) -> TraceRecord:
        record = TraceRecord(trace_id=trace_id, task_id=task_id)
        self.traces[trace_id] = record
        return record

    def record_latency(self, trace_id: str, step_name: str, latency_ms: float):
        if trace_id in self.traces:
            self.traces[trace_id].latency_ms[step_name] = latency_ms

    def record_error(self, trace_id: str, error_msg: str):
        if trace_id in self.traces:
            self.traces[trace_id].errors.append(error_msg)

    def record_tool_call(self, trace_id: str, tool_name: str):
        if trace_id in self.traces:
            self.traces[trace_id].tools_called.append(tool_name)

    def get_trace(self, trace_id: str) -> Optional[TraceRecord]:
        return self.traces.get(trace_id)

tracer = ExecutionTracer()
