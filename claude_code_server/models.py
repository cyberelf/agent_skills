"""
Pydantic models for API request/response and internal data structures
"""

from datetime import datetime
from enum import Enum
from typing import Dict, Any, Optional, List
from pydantic import BaseModel, Field


class TaskStatus(str, Enum):
    """Task execution status"""
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    INTERRUPTED = "interrupted"


class SessionStatus(str, Enum):
    """Session status"""
    ACTIVE = "active"
    IDLE = "idle"
    TERMINATED = "terminated"


class TaskOptions(BaseModel):
    """Options for task execution"""
    allowed_tools: List[str] = Field(
        default=["Read", "Write", "Edit", "Bash"],
        description="List of allowed tool names"
    )
    permission_mode: str = Field(
        default="acceptEdits",
        description="Permission mode for tool usage"
    )
    max_turns: Optional[int] = Field(
        default=50,
        description="Maximum conversation turns"
    )
    timeout: int = Field(
        default=3600,
        description="Task timeout in seconds"
    )
    model: Optional[str] = Field(
        default=None,
        description="Claude model to use"
    )
    cwd: Optional[str] = Field(
        default=None,
        description="Working directory override"
    )


class SessionConfig(BaseModel):
    """Session configuration"""
    reuse_existing: bool = Field(
        default=False,
        description="Reuse existing session"
    )
    session_id: Optional[str] = Field(
        default=None,
        description="Session ID to reuse"
    )


class TaskRequest(BaseModel):
    """Request to create a new task"""
    task_id: str = Field(..., description="Unique task identifier")
    prompt: str = Field(..., description="Task prompt for Claude")
    workspace: str = Field(..., description="Workspace directory path")
    options: TaskOptions = Field(
        default_factory=TaskOptions,
        description="Task execution options"
    )
    session: SessionConfig = Field(
        default_factory=SessionConfig,
        description="Session configuration"
    )


class TaskResponse(BaseModel):
    """Response after task creation"""
    task_id: str
    session_id: str
    status: TaskStatus
    websocket_url: str
    created_at: datetime


class TaskProgress(BaseModel):
    """Task execution progress"""
    turns: int = 0
    tokens_used: int = 0
    tokens_input: int = 0
    tokens_output: int = 0
    files_modified: int = 0
    elapsed_time_ms: int = 0


class TaskResult(BaseModel):
    """Final task result"""
    exit_code: int = 0
    summary: Optional[str] = None
    errors: List[str] = Field(default_factory=list)
    total_cost_usd: Optional[float] = None


class TaskStatusResponse(BaseModel):
    """Response for task status query"""
    task_id: str
    session_id: str
    status: TaskStatus
    progress: TaskProgress
    result: Optional[TaskResult] = None
    created_at: datetime
    updated_at: datetime


class InterruptResponse(BaseModel):
    """Response after task interruption"""
    task_id: str
    status: TaskStatus
    interrupted_at: datetime


class SessionInfo(BaseModel):
    """Session information"""
    session_id: str
    tasks: List[str] = Field(default_factory=list)
    status: SessionStatus
    created_at: datetime
    last_activity: datetime


class SessionListResponse(BaseModel):
    """Response for session list query"""
    sessions: List[SessionInfo]


# WebSocket event models

class EventType(str, Enum):
    """WebSocket event types"""
    MESSAGE = "message"
    TOOL_USE = "tool_use"
    TOOL_RESULT = "tool_result"
    PROGRESS = "progress"
    COMPLETE = "complete"
    ERROR = "error"


class MessageEvent(BaseModel):
    """Message event from Claude"""
    type: EventType = EventType.MESSAGE
    timestamp: datetime
    data: Dict[str, Any]


class ToolUseEvent(BaseModel):
    """Tool usage event"""
    type: EventType = EventType.TOOL_USE
    timestamp: datetime
    data: Dict[str, Any]


class ToolResultEvent(BaseModel):
    """Tool result event"""
    type: EventType = EventType.TOOL_RESULT
    timestamp: datetime
    data: Dict[str, Any]


class ProgressEvent(BaseModel):
    """Progress update event"""
    type: EventType = EventType.PROGRESS
    timestamp: datetime
    data: TaskProgress


class CompleteEvent(BaseModel):
    """Task completion event"""
    type: EventType = EventType.COMPLETE
    timestamp: datetime
    data: TaskResult


class ErrorEvent(BaseModel):
    """Error event"""
    type: EventType = EventType.ERROR
    timestamp: datetime
    data: Dict[str, Any]


# Health check models

class HealthStatus(str, Enum):
    """Health check status"""
    HEALTHY = "healthy"
    DEGRADED = "degraded"
    UNHEALTHY = "unhealthy"


class HealthResponse(BaseModel):
    """Health check response"""
    status: HealthStatus
    version: str
    active_sessions: int
    active_tasks: int
    uptime_seconds: int
