from enum import Enum
from typing import Dict, Any, Optional, List
from pydantic import BaseModel, Field
from datetime import datetime

class ExecutionMode(str, Enum):
    DIRECT = "direct"
    WORKFLOW = "workflow"
    LLM = "llm"
    AGENT = "agent"

class TaskStatus(str, Enum):
    PENDING = "pending"
    PLANNING = "planning"
    WAITING_CONFIRMATION = "waiting_confirmation"
    EXECUTING = "executing"
    WAITING_USER = "waiting_user"
    SUCCESS = "success"
    FAILED = "failed"
    CANCELLED = "cancelled"
    TIMEOUT = "timeout"

class ExecutionResultStatus(str, Enum):
    SUCCESS = "success"
    FAILED = "failed"
    RETRYABLE = "retryable"
    NEEDS_USER = "needs_user"
    NOT_FOUND = "not_found"
    PERMISSION_DENIED = "permission_denied"
    TIMEOUT = "timeout"

class RiskLevel(str, Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"

class Intent(BaseModel):
    name: str
    confidence: float
    entities: Dict[str, Any] = Field(default_factory=dict)
    source: str = "voice"
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    raw_transcript: Optional[str] = None
    normalized_text: Optional[str] = None
    locale: str = "es-ES"
    context_id: Optional[str] = None

class Context(BaseModel):
    context_id: str
    current_task: Optional[str] = None
    previous_entities: Dict[str, Any] = Field(default_factory=dict)
    active_app: Optional[str] = None
    last_item: Optional[Any] = None # e.g. last_video
    pending_action: Optional[str] = None

class Task(BaseModel):
    id: str
    user_input: str
    intent: Optional[Intent] = None
    entities: Dict[str, Any] = Field(default_factory=dict)
    priority: int = 1
    confirmation_required: bool = False
    execution_mode: Optional[ExecutionMode] = None
    status: TaskStatus = TaskStatus.PENDING
    created_at: datetime = Field(default_factory=datetime.utcnow)
    deadline: Optional[datetime] = None
    context: Optional[Context] = None

class Tool(BaseModel):
    name: str
    description: str
    parameters: Dict[str, Any]

    def execute(self, **kwargs) -> Any:
        raise NotImplementedError()

class Skill(BaseModel):
    name: str
    version: str
    description: str
    intents: List[str]
    capabilities: List[str]
    parameters: Dict[str, Any] = Field(default_factory=dict)
    permissions: List[str] = Field(default_factory=dict)
    risk_level: RiskLevel = RiskLevel.LOW
    requires_llm: bool = False
    requires_network: bool = False
    requires_confirmation: bool = False

    def execute(self, task: Task) -> Any:
        raise NotImplementedError()

class ExecutionResult(BaseModel):
    status: ExecutionResultStatus
    data: Optional[Any] = None
    message: Optional[str] = None
    trace_id: Optional[str] = None
