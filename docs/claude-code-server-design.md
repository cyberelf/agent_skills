# Claude Code Server Architecture Design

**Date:** January 19, 2026  
**Version:** 1.0  
**Status:** Design Proposal

## Executive Summary

This document outlines the architectural redesign of the Agent Worker system to replace CLI-based Claude Code execution with a persistent Claude Code server using the Agent SDK. The new architecture separates concerns by:

1. **Agent Worker**: Orchestration, task management, and lifecycle control
2. **Claude Code Server**: Persistent agent server handling code generation tasks via Agent SDK
3. **Communication**: REST/WebSocket API for task submission and real-time updates

## Table of Contents

- [1. Current Architecture Analysis](#1-current-architecture-analysis)
- [2. Agent SDK Overview](#2-agent-sdk-overview)
- [3. Proposed Architecture](#3-proposed-architecture)
- [4. Communication Protocol](#4-communication-protocol)
- [5. Implementation Plan](#5-implementation-plan)
- [6. Security Considerations](#6-security-considerations)
- [7. Performance & Scalability](#7-performance--scalability)
- [8. Migration Strategy](#8-migration-strategy)

---

## 1. Current Architecture Analysis

### 1.1 Current Flow

```
┌─────────────────┐      ┌──────────────────┐      ┌─────────────────┐
│  Agent Worker   │─────▶│ Docker Container │─────▶│  Claude CLI     │
│  (Orchestrator) │      │  (Isolated Env)  │      │  (One-shot)     │
└─────────────────┘      └──────────────────┘      └─────────────────┘
         │                        │
         │                        │
         ▼                        ▼
    ┌─────────┐            ┌─────────┐
    │  Task   │            │  Bash   │
    │  File   │            │  Script │
    └─────────┘            └─────────┘
```

### 1.2 Current Components

| Component | Responsibility | Issues |
|-----------|----------------|---------|
| `agent_worker.py` | Orchestration, Git management, Docker control | Tightly coupled to CLI execution |
| `docker_manager.py` | Container lifecycle, image building | No reusability across tasks |
| `agent_inside.sh` | Bash script invoking `claude` CLI | No programmatic control, limited observability |
| `claude_agent.py` | CLI output parsing | Fragile regex-based parsing |

### 1.3 Pain Points

1. **No Session Continuity**: Each task spawns a new Claude instance
2. **Limited Control**: Cannot interrupt, modify, or query agent state
3. **Poor Observability**: Parsing bash output for statistics
4. **Resource Intensive**: Full Docker container per task
5. **Tight Coupling**: Orchestration logic mixed with execution
6. **No Programmatic API**: Everything goes through CLI and bash

---

## 2. Agent SDK Overview

### 2.1 Key Capabilities

The [Agent SDK (Python)](https://platform.claude.com/docs/en/agent-sdk/python) provides:

#### Core Features
- **`ClaudeSDKClient`**: Persistent session with conversation continuity
- **`query()`**: One-off task execution
- **Custom Tools**: Define MCP tools with `@tool` decorator
- **Hooks**: Intercept and modify agent behavior
- **Streaming**: Real-time message streaming
- **Interrupts**: Stop agent mid-execution
- **Session Management**: Resume, fork, and checkpoint sessions

#### API Design
```python
# Persistent client with session continuity
async with ClaudeSDKClient(options=options) as client:
    await client.query("First task")
    async for message in client.receive_response():
        # Process messages
    
    # Continue conversation
    await client.query("Follow-up task")
```

### 2.2 Architecture Options

| Approach | Pros | Cons | Use Case |
|----------|------|------|----------|
| **`query()` per task** | Simple, stateless | No session continuity | Independent one-shot tasks |
| **`ClaudeSDKClient` instance** | Session memory, interrupts | State management complexity | Multi-turn conversations |
| **Hybrid** | Flexibility | Implementation complexity | Task-dependent strategy |

### 2.3 Recommended Approach

**Use `ClaudeSDKClient` with managed sessions** for:
- Better observability (structured message types)
- Session continuity across related tasks
- Interrupt capability
- Custom hooks for logging and control
- Programmatic access to agent state

---

## 3. Proposed Architecture

### 3.1 High-Level Design

```
┌──────────────────────────────────────────────────────────────┐
│                       Agent Worker                            │
│  ┌────────────────┐  ┌──────────────┐  ┌─────────────────┐  │
│  │ Orchestrator   │  │ Task Manager │  │ Git Manager     │  │
│  │ - Workflow     │  │ - Queue      │  │ - Worktrees     │  │
│  │ - Lifecycle    │  │ - Priority   │  │ - Branching     │  │
│  └────────┬───────┘  └──────┬───────┘  └────────┬────────┘  │
│           │                  │                    │            │
│           └──────────────────┴────────────────────┘            │
│                              │                                 │
└──────────────────────────────┼─────────────────────────────────┘
                               │
                          REST/WebSocket API
                               │
┌──────────────────────────────┼─────────────────────────────────┐
│                              │                                 │
│              Claude Code Server (Python)                       │
│  ┌─────────────────────────────────────────────────────────┐  │
│  │                  API Server (FastAPI/aiohttp)            │  │
│  │  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐  │  │
│  │  │ /tasks       │  │ /sessions    │  │ /status      │  │  │
│  │  │  - POST      │  │  - GET       │  │  - GET       │  │  │
│  │  │  - GET       │  │  - DELETE    │  │  - WS        │  │  │
│  │  └──────────────┘  └──────────────┘  └──────────────┘  │  │
│  └─────────────────────────┬───────────────────────────────┘  │
│                            │                                  │
│  ┌─────────────────────────┴───────────────────────────────┐  │
│  │              Session Manager                            │  │
│  │  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐   │  │
│  │  │ Session Pool │  │ Message Queue│  │ Event Bus    │   │  │
│  │  │ - Create     │  │ - Per-task   │  │ - Streaming  │   │  │
│  │  │ - Cleanup    │  │ - History    │  │ - Hooks      │   │  │
│  │  └──────────────┘  └──────────────┘  └──────────────┘   │  │
│  └─────────────────────────┬───────────────────────────────┘  │
│                            │                                  │
│  ┌─────────────────────────┴───────────────────────────────┐  │
│  │              Claude SDK Layer                           │  │
│  │  ┌────────────────────────────────────────────────────┐ │  │
│  │  │  ClaudeSDKClient (Agent SDK)                       │ │  │
│  │  │  - Session management                              │ │  │
│  │  │  - Message streaming                               │ │  │
│  │  │  - Tool execution                                  │ │  │
│  │  │  - Interrupt handling                              │ │  │
│  │  └────────────────────────────────────────────────────┘ │  │
│  └─────────────────────────────────────────────────────────┘  │
│                                                               │
└───────────────────────────────────────────────────────────────┘
                               │
                               ▼
                    ┌──────────────────┐
                    │  Workspace       │
                    │  - Git worktrees │
                    │  - File system   │
                    └──────────────────┘
```

### 3.2 Component Responsibilities

#### 3.2.1 Agent Worker (Orchestrator)

**Responsibilities:**
- Task lifecycle management
- Git worktree creation/cleanup
- Docker management (if containerizing server)
- Task submission to Claude Code Server
- Result aggregation and reporting
- Metrics collection

**Does NOT:**
- Execute Claude Code directly
- Parse Claude output
- Manage agent sessions

**Key Files:**
- `agent_worker.py` - Main orchestration
- `task_manager.py` - Task queue and priority
- `git_manager.py` - Worktree management
- `docker_manager.py` - Container lifecycle (if needed)

#### 3.2.2 Claude Code Server

**Responsibilities:**
- Agent SDK session management
- Task execution via `ClaudeSDKClient`
- Real-time message streaming
- Session cleanup and resource management
- Metrics emission
- Error handling and recovery

**Does NOT:**
- Git operations
- Project-level orchestration
- Multi-task scheduling

**Key Files:**
- `server.py` - FastAPI/aiohttp server
- `session_manager.py` - Session lifecycle
- `task_executor.py` - Agent SDK wrapper
- `websocket_handler.py` - Real-time updates
- `hooks.py` - Custom hook implementations

---

## 4. Communication Protocol

### 4.1 API Endpoints

#### 4.1.1 Task Submission

**POST /api/v1/tasks**

Request:
```json
{
  "task_id": "task-1737291000",
  "prompt": "Implement user authentication",
  "workspace": "/workspace/project",
  "options": {
    "allowed_tools": ["Read", "Write", "Edit", "Bash"],
    "permission_mode": "acceptEdits",
    "max_turns": 50,
    "timeout": 3600
  },
  "session": {
    "reuse_existing": false,
    "session_id": null
  }
}
```

Response:
```json
{
  "task_id": "task-1737291000",
  "session_id": "session-abc123",
  "status": "running",
  "websocket_url": "ws://localhost:8000/ws/task-1737291000",
  "created_at": "2026-01-19T10:00:00Z"
}
```

#### 4.1.2 Task Status

**GET /api/v1/tasks/{task_id}**

Response:
```json
{
  "task_id": "task-1737291000",
  "session_id": "session-abc123",
  "status": "running|completed|failed|interrupted",
  "progress": {
    "turns": 5,
    "tokens_used": 12500,
    "files_modified": 3,
    "elapsed_time_ms": 45000
  },
  "result": {
    "exit_code": 0,
    "summary": "Implemented authentication with JWT",
    "errors": []
  }
}
```

#### 4.1.3 Task Interruption

**POST /api/v1/tasks/{task_id}/interrupt**

Response:
```json
{
  "task_id": "task-1737291000",
  "status": "interrupted",
  "interrupted_at": "2026-01-19T10:05:00Z"
}
```

#### 4.1.4 Session Management

**GET /api/v1/sessions**

Response:
```json
{
  "sessions": [
    {
      "session_id": "session-abc123",
      "tasks": ["task-1737291000", "task-1737291100"],
      "status": "active|idle|terminated",
      "created_at": "2026-01-19T10:00:00Z",
      "last_activity": "2026-01-19T10:05:00Z"
    }
  ]
}
```

**DELETE /api/v1/sessions/{session_id}**

### 4.2 WebSocket Protocol

**WS /ws/tasks/{task_id}**

Server → Client Messages:

```json
{
  "type": "message",
  "timestamp": "2026-01-19T10:00:05.123Z",
  "data": {
    "message_type": "assistant|user|system|result",
    "content": "Assistant message or tool result",
    "metadata": {
      "model": "claude-sonnet-4",
      "tokens": 150
    }
  }
}
```

```json
{
  "type": "tool_use",
  "timestamp": "2026-01-19T10:00:06.456Z",
  "data": {
    "tool_name": "Write",
    "tool_input": {
      "file_path": "/workspace/auth.py",
      "content": "..."
    }
  }
}
```

```json
{
  "type": "tool_result",
  "timestamp": "2026-01-19T10:00:07.789Z",
  "data": {
    "tool_name": "Write",
    "result": {
      "message": "File written successfully",
      "bytes_written": 1024
    }
  }
}
```

```json
{
  "type": "progress",
  "timestamp": "2026-01-19T10:00:08.012Z",
  "data": {
    "turn": 3,
    "tokens_total": 5000,
    "tokens_input": 3000,
    "tokens_output": 2000,
    "files_modified": 2
  }
}
```

```json
{
  "type": "complete",
  "timestamp": "2026-01-19T10:05:00.000Z",
  "data": {
    "task_id": "task-1737291000",
    "status": "success|error",
    "result": {
      "summary": "Task completed",
      "duration_ms": 300000,
      "total_tokens": 15000,
      "files_changed": 5
    }
  }
}
```

---

## 5. Implementation Plan

### 5.1 Phase 1: Core Server (Week 1-2)

**Goal:** Basic Claude Code Server with Agent SDK integration

**Tasks:**
1. Set up FastAPI project structure
2. Implement `ClaudeSDKClient` wrapper
3. Create basic task execution endpoint (POST /tasks)
4. Implement session management (in-memory)
5. Add basic WebSocket streaming
6. Write unit tests

**Deliverables:**
- `claude_code_server/` package
  - `server.py` - FastAPI app
  - `session_manager.py` - Session lifecycle
  - `task_executor.py` - Agent SDK wrapper
  - `models.py` - Pydantic models
  - `config.py` - Configuration

**Success Criteria:**
- Server accepts task via REST API
- Executes task using Agent SDK
- Returns structured results
- WebSocket streams messages

### 5.2 Phase 2: Agent Worker Integration (Week 3)

**Goal:** Refactor Agent Worker to use server

**Tasks:**
1. Create `ServerClient` in agent_worker
2. Refactor `agent_worker.py` to submit via API
3. Update `claude_agent.py` to use API client
4. Implement WebSocket listener for progress
5. Update error handling
6. Migration tests

**Deliverables:**
- `agent_worker/server_client.py` - API client
- Updated `agent_worker.py`
- Updated `claude_agent.py`
- Integration tests

**Success Criteria:**
- Agent Worker submits tasks to server
- Receives real-time progress
- Handles errors gracefully
- Backward compatibility maintained

### 5.3 Phase 3: Advanced Features (Week 4)

**Goal:** Production-ready features

**Tasks:**
1. Persistent session storage (Redis/SQLite)
2. Task queuing and prioritization
3. Rate limiting and resource management
4. Custom hooks for logging/metrics
5. Health checks and monitoring
6. Authentication/authorization
7. Load testing

**Deliverables:**
- Session persistence layer
- Queue management
- Monitoring integration
- Security implementation
- Performance benchmarks

**Success Criteria:**
- Sessions survive server restarts
- Multiple concurrent tasks
- Metrics exported to Prometheus
- API secured with authentication
- Handles 10+ concurrent tasks

### 5.4 Phase 4: Deployment & Docs (Week 5)

**Goal:** Production deployment

**Tasks:**
1. Docker containerization
2. Kubernetes manifests (optional)
3. Configuration management
4. API documentation (OpenAPI)
5. User guide
6. Migration guide

**Deliverables:**
- `Dockerfile` for server
- `docker-compose.yml` for local dev
- Deployment guides
- API documentation
- Migration runbook

---

## 6. Security Considerations

### 6.1 Authentication & Authorization

**Options:**

1. **API Key-based** (Phase 1)
   - Simple bearer tokens
   - Environment variable configuration
   - Good for single-tenant deployments

2. **JWT-based** (Phase 3)
   - Token-based authentication
   - Role-based access control
   - Good for multi-tenant scenarios

3. **mTLS** (Future)
   - Certificate-based authentication
   - Highest security
   - Complex setup

**Recommendation:** Start with API key, migrate to JWT for production.

### 6.2 Workspace Isolation

**Risks:**
- Cross-workspace access
- Path traversal attacks
- Resource exhaustion

**Mitigations:**
1. **Path validation:** Ensure workspace paths are absolute and validated
2. **Chroot/container isolation:** Run server in container with limited filesystem access
3. **Resource limits:** CPU/memory limits per task
4. **Workspace whitelisting:** Only allow pre-approved workspace paths

### 6.3 API Security

**Best Practices:**
1. **Rate limiting:** Prevent DoS (e.g., 100 req/min per API key)
2. **Input validation:** Validate all API inputs with Pydantic
3. **Output sanitization:** Prevent information leakage
4. **CORS:** Restrict to allowed origins
5. **HTTPS only:** Enforce TLS in production

### 6.4 Secrets Management

**Anthropic API Key:**
- Store in environment variables
- Never log or expose in API responses
- Rotate regularly
- Use secret management service (Vault, AWS Secrets Manager)

---

## 7. Performance & Scalability

### 7.1 Performance Targets

| Metric | Target | Notes |
|--------|--------|-------|
| Task submission latency | < 100ms | REST API response time |
| WebSocket message latency | < 50ms | Real-time streaming |
| Concurrent tasks | 10+ | Per server instance |
| Session creation time | < 500ms | Agent SDK initialization |
| Task throughput | 100+ tasks/hour | With queueing |

### 7.2 Scaling Strategies

#### Vertical Scaling
- **CPU:** 4-8 cores for concurrent Agent SDK instances
- **Memory:** 8-16GB (Agent SDK can be memory-intensive)
- **Storage:** Fast SSD for workspace access

#### Horizontal Scaling
1. **Stateless server instances**
   - Load balancer in front
   - Shared session store (Redis)
   - Shared workspace (NFS/EFS)

2. **Task queue (Celery/RQ)**
   - Worker pool model
   - Task prioritization
   - Retry logic

#### Resource Management
```python
# Concurrent session limit
MAX_CONCURRENT_SESSIONS = 10

# Task timeout
DEFAULT_TASK_TIMEOUT = 3600  # 1 hour

# Session idle timeout
SESSION_IDLE_TIMEOUT = 1800  # 30 minutes

# Memory limit per session
MAX_MEMORY_PER_SESSION = 2 * 1024 * 1024 * 1024  # 2GB
```

### 7.3 Caching Strategy

**Session Caching:**
- Keep idle sessions alive for 30 minutes
- LRU eviction when limit reached
- Checkpoint sessions for resume

**Workspace Caching:**
- Cache git worktree metadata
- Invalidate on external changes

---

## 8. Migration Strategy

### 8.1 Backward Compatibility

**Approach:** Support both old and new execution modes during transition.

```python
# config.py
class Config:
    execution_mode: str = 'cli'  # 'cli' or 'server'
    server_url: Optional[str] = None
```

### 8.2 Migration Steps

1. **Phase 1: Dual mode support (Week 1-2)**
   - Agent Worker supports both CLI and server mode
   - Feature flag to switch modes
   - CLI remains default

2. **Phase 2: Server as default (Week 3-4)**
   - Server mode becomes default
   - CLI mode deprecated but functional
   - Documentation updated

3. **Phase 3: CLI removal (Week 5+)**
   - Remove CLI execution code
   - Remove `agent_inside.sh`
   - Update Docker image

### 8.3 Rollback Plan

If server approach fails:
1. Feature flag to revert to CLI mode
2. Keep CLI code until server is proven
3. Gradual rollout (staging → production)

### 8.4 Testing Strategy

**Unit Tests:**
- Agent SDK wrapper
- API endpoints
- Session management

**Integration Tests:**
- End-to-end task execution
- WebSocket streaming
- Error scenarios

**Performance Tests:**
- Concurrent task load
- Long-running tasks
- Resource cleanup

**Migration Tests:**
- CLI → Server comparison
- Feature parity validation
- Backward compatibility

---

## 9. Code Examples

### 9.1 Claude Code Server (Basic Structure)

```python
# claude_code_server/server.py
from fastapi import FastAPI, WebSocket, HTTPException
from pydantic import BaseModel
from typing import Optional
import asyncio

from .session_manager import SessionManager
from .task_executor import TaskExecutor

app = FastAPI(title="Claude Code Server", version="1.0.0")
session_manager = SessionManager()

class TaskRequest(BaseModel):
    task_id: str
    prompt: str
    workspace: str
    options: dict = {}
    session: dict = {"reuse_existing": False}

@app.post("/api/v1/tasks")
async def create_task(request: TaskRequest):
    """Submit a new task for execution"""
    
    # Get or create session
    if request.session.get("reuse_existing"):
        session_id = request.session.get("session_id")
        session = session_manager.get(session_id)
        if not session:
            raise HTTPException(404, "Session not found")
    else:
        session = await session_manager.create(
            workspace=request.workspace,
            options=request.options
        )
    
    # Start task execution
    executor = TaskExecutor(session)
    asyncio.create_task(executor.execute(request.task_id, request.prompt))
    
    return {
        "task_id": request.task_id,
        "session_id": session.id,
        "status": "running",
        "websocket_url": f"ws://localhost:8000/ws/tasks/{request.task_id}"
    }

@app.websocket("/ws/tasks/{task_id}")
async def websocket_endpoint(websocket: WebSocket, task_id: str):
    """Stream task progress via WebSocket"""
    await websocket.accept()
    
    # Subscribe to task events
    queue = session_manager.subscribe_task(task_id)
    
    try:
        while True:
            event = await queue.get()
            await websocket.send_json(event)
            
            if event["type"] == "complete":
                break
    except Exception as e:
        await websocket.close(code=1011, reason=str(e))
```

### 9.2 Task Executor with Agent SDK

```python
# claude_code_server/task_executor.py
from claude_agent_sdk import ClaudeSDKClient, ClaudeAgentOptions
from claude_agent_sdk import AssistantMessage, ToolUseBlock, ResultMessage
from typing import AsyncIterator
import asyncio

class TaskExecutor:
    def __init__(self, session):
        self.session = session
        self.client = session.client
        
    async def execute(self, task_id: str, prompt: str):
        """Execute a task using the Agent SDK"""
        
        try:
            # Send query to Claude
            await self.client.query(prompt)
            
            # Stream messages
            async for message in self.client.receive_response():
                # Emit event for each message
                await self._emit_event(task_id, message)
                
                # Handle different message types
                if isinstance(message, AssistantMessage):
                    await self._handle_assistant_message(task_id, message)
                elif isinstance(message, ResultMessage):
                    await self._handle_result(task_id, message)
                    break
                    
            # Mark task complete
            await self._complete_task(task_id, success=True)
            
        except Exception as e:
            await self._complete_task(task_id, success=False, error=str(e))
    
    async def _emit_event(self, task_id: str, message):
        """Emit event to WebSocket subscribers"""
        event = {
            "type": "message",
            "timestamp": datetime.utcnow().isoformat(),
            "data": self._serialize_message(message)
        }
        await self.session.manager.publish_event(task_id, event)
    
    async def _handle_assistant_message(self, task_id: str, message: AssistantMessage):
        """Handle assistant message with tool usage"""
        for block in message.content:
            if isinstance(block, ToolUseBlock):
                await self._emit_tool_use(task_id, block)
    
    async def _handle_result(self, task_id: str, result: ResultMessage):
        """Handle final result"""
        await self.session.manager.publish_event(task_id, {
            "type": "progress",
            "data": {
                "turn": result.num_turns,
                "tokens_total": result.usage.get("total_tokens", 0) if result.usage else 0,
                "duration_ms": result.duration_ms
            }
        })
    
    async def _complete_task(self, task_id: str, success: bool, error: str = None):
        """Mark task as complete"""
        await self.session.manager.publish_event(task_id, {
            "type": "complete",
            "data": {
                "task_id": task_id,
                "status": "success" if success else "error",
                "error": error
            }
        })
```

### 9.3 Agent Worker Client

```python
# agent_worker/server_client.py
import aiohttp
import asyncio
from typing import AsyncIterator, Dict, Any

class ClaudeServerClient:
    """Client for Claude Code Server API"""
    
    def __init__(self, base_url: str, api_key: str):
        self.base_url = base_url
        self.api_key = api_key
        self.session = None
    
    async def submit_task(
        self,
        task_id: str,
        prompt: str,
        workspace: str,
        options: dict = None
    ) -> Dict[str, Any]:
        """Submit a task to the server"""
        
        async with aiohttp.ClientSession() as session:
            async with session.post(
                f"{self.base_url}/api/v1/tasks",
                json={
                    "task_id": task_id,
                    "prompt": prompt,
                    "workspace": workspace,
                    "options": options or {}
                },
                headers={"Authorization": f"Bearer {self.api_key}"}
            ) as response:
                response.raise_for_status()
                return await response.json()
    
    async def stream_progress(
        self,
        task_id: str
    ) -> AsyncIterator[Dict[str, Any]]:
        """Stream task progress via WebSocket"""
        
        ws_url = f"{self.base_url.replace('http', 'ws')}/ws/tasks/{task_id}"
        
        async with aiohttp.ClientSession() as session:
            async with session.ws_connect(ws_url) as ws:
                async for msg in ws:
                    if msg.type == aiohttp.WSMsgType.TEXT:
                        yield msg.json()
                    elif msg.type == aiohttp.WSMsgType.ERROR:
                        break
    
    async def get_task_status(self, task_id: str) -> Dict[str, Any]:
        """Get task status"""
        
        async with aiohttp.ClientSession() as session:
            async with session.get(
                f"{self.base_url}/api/v1/tasks/{task_id}",
                headers={"Authorization": f"Bearer {self.api_key}"}
            ) as response:
                response.raise_for_status()
                return await response.json()
    
    async def interrupt_task(self, task_id: str) -> Dict[str, Any]:
        """Interrupt a running task"""
        
        async with aiohttp.ClientSession() as session:
            async with session.post(
                f"{self.base_url}/api/v1/tasks/{task_id}/interrupt",
                headers={"Authorization": f"Bearer {self.api_key}"}
            ) as response:
                response.raise_for_status()
                return await response.json()
```

### 9.4 Updated Agent Worker Usage

```python
# agent_worker/agent_worker.py (modified)
from .server_client import ClaudeServerClient

class AgentWorker:
    def __init__(self, config: Config):
        # ...existing init...
        
        if config.execution_mode == 'server':
            self.server_client = ClaudeServerClient(
                base_url=config.server_url,
                api_key=config.api_key
            )
    
    async def _execute_agent_via_server(self):
        """Execute agent via Claude Code Server"""
        
        # Submit task
        result = await self.server_client.submit_task(
            task_id=self.run_config.run_id,
            prompt=self.config.task_description,
            workspace=str(self.config.project_path),
            options={
                "allowed_tools": ["Read", "Write", "Edit", "Bash"],
                "permission_mode": "acceptEdits",
                "max_turns": 50
            }
        )
        
        self.logger.info(f"Task submitted: {result['task_id']}")
        
        # Stream progress
        async for event in self.server_client.stream_progress(result['task_id']):
            event_type = event.get("type")
            
            if event_type == "message":
                self._log_message(event["data"])
            elif event_type == "tool_use":
                self._log_tool_use(event["data"])
            elif event_type == "progress":
                self._update_stats(event["data"])
            elif event_type == "complete":
                self._finalize_stats(event["data"])
                break
        
        return result
```

---

## 10. Monitoring & Observability

### 10.1 Metrics

**Server Metrics (Prometheus format):**
```python
# claude_code_server/metrics.py
from prometheus_client import Counter, Histogram, Gauge

# Request metrics
http_requests_total = Counter(
    'http_requests_total',
    'Total HTTP requests',
    ['method', 'endpoint', 'status']
)

# Task metrics
tasks_total = Counter(
    'tasks_total',
    'Total tasks submitted',
    ['status']  # success, error, interrupted
)

tasks_duration_seconds = Histogram(
    'tasks_duration_seconds',
    'Task execution duration'
)

# Session metrics
active_sessions = Gauge(
    'active_sessions',
    'Number of active Agent SDK sessions'
)

# Token usage
tokens_used_total = Counter(
    'tokens_used_total',
    'Total tokens consumed',
    ['type']  # input, output
)
```

### 10.2 Logging

**Structured logging with context:**
```python
import structlog

logger = structlog.get_logger()

logger.info(
    "task_started",
    task_id="task-123",
    session_id="session-abc",
    workspace="/workspace/project"
)

logger.info(
    "task_completed",
    task_id="task-123",
    duration_ms=45000,
    tokens_used=12500,
    files_modified=3
)
```

### 10.3 Tracing

**OpenTelemetry integration:**
```python
from opentelemetry import trace
from opentelemetry.sdk.trace import TracerProvider

tracer = trace.get_tracer(__name__)

with tracer.start_as_current_span("execute_task"):
    with tracer.start_as_current_span("claude_sdk_query"):
        await client.query(prompt)
```

---

## 11. Configuration Management

### 11.1 Server Configuration

```yaml
# claude_code_server/config.yaml
server:
  host: "0.0.0.0"
  port: 8000
  workers: 4
  
api:
  version: "v1"
  auth:
    enabled: true
    type: "bearer"  # bearer, jwt
  rate_limit:
    enabled: true
    requests_per_minute: 100

claude_sdk:
  default_options:
    permission_mode: "acceptEdits"
    allowed_tools:
      - Read
      - Write
      - Edit
      - Bash
    max_turns: 50
  
sessions:
  max_concurrent: 10
  idle_timeout_seconds: 1800
  cleanup_interval_seconds: 300

tasks:
  default_timeout_seconds: 3600
  max_queue_size: 100

storage:
  type: "redis"  # redis, memory, sqlite
  redis:
    host: "localhost"
    port: 6379
    db: 0

monitoring:
  prometheus:
    enabled: true
    port: 9090
  logging:
    level: "INFO"
    format: "json"
```

### 11.2 Agent Worker Configuration

```yaml
# agent_worker/config.yaml
execution:
  mode: "server"  # server, cli (deprecated)
  
server:
  url: "http://localhost:8000"
  api_key: "${CLAUDE_SERVER_API_KEY}"
  timeout: 3600

# ... existing config ...
```

---

## 12. Deployment Architecture

### 12.1 Docker Compose (Development)

```yaml
# docker-compose.yml
version: '3.8'

services:
  claude-server:
    build: ./claude_code_server
    ports:
      - "8000:8000"
      - "9090:9090"  # Prometheus metrics
    environment:
      - ANTHROPIC_API_KEY=${ANTHROPIC_API_KEY}
      - REDIS_HOST=redis
    volumes:
      - ./workspaces:/workspaces
    depends_on:
      - redis
  
  redis:
    image: redis:7-alpine
    ports:
      - "6379:6379"
    volumes:
      - redis-data:/data
  
  agent-worker:
    build: ./agent_worker
    environment:
      - CLAUDE_SERVER_URL=http://claude-server:8000
      - CLAUDE_SERVER_API_KEY=${CLAUDE_SERVER_API_KEY}
    volumes:
      - ./workspaces:/workspaces
    depends_on:
      - claude-server

volumes:
  redis-data:
```

### 12.2 Kubernetes (Production)

```yaml
# k8s/claude-server-deployment.yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: claude-server
spec:
  replicas: 3
  selector:
    matchLabels:
      app: claude-server
  template:
    metadata:
      labels:
        app: claude-server
    spec:
      containers:
      - name: claude-server
        image: claude-server:latest
        ports:
        - containerPort: 8000
        - containerPort: 9090
        env:
        - name: ANTHROPIC_API_KEY
          valueFrom:
            secretKeyRef:
              name: claude-secrets
              key: api-key
        - name: REDIS_HOST
          value: "redis-service"
        resources:
          requests:
            memory: "4Gi"
            cpu: "2"
          limits:
            memory: "8Gi"
            cpu: "4"
        livenessProbe:
          httpGet:
            path: /health
            port: 8000
          initialDelaySeconds: 30
          periodSeconds: 10
        readinessProbe:
          httpGet:
            path: /ready
            port: 8000
          initialDelaySeconds: 10
          periodSeconds: 5
---
apiVersion: v1
kind: Service
metadata:
  name: claude-server
spec:
  selector:
    app: claude-server
  ports:
  - name: http
    port: 80
    targetPort: 8000
  - name: metrics
    port: 9090
    targetPort: 9090
  type: LoadBalancer
```

---

## 13. Testing Strategy

### 13.1 Unit Tests

```python
# tests/test_task_executor.py
import pytest
from unittest.mock import AsyncMock, MagicMock
from claude_code_server.task_executor import TaskExecutor

@pytest.mark.asyncio
async def test_execute_task_success():
    """Test successful task execution"""
    
    # Mock session and client
    session = MagicMock()
    session.client.query = AsyncMock()
    session.client.receive_response = AsyncMock(return_value=iter([
        MockAssistantMessage("Task completed"),
        MockResultMessage(num_turns=1, duration_ms=1000)
    ]))
    
    executor = TaskExecutor(session)
    await executor.execute("task-123", "Test prompt")
    
    # Assert client.query was called
    session.client.query.assert_called_once_with("Test prompt")
```

### 13.2 Integration Tests

```python
# tests/integration/test_api.py
import pytest
from httpx import AsyncClient
from claude_code_server.server import app

@pytest.mark.asyncio
async def test_submit_task():
    """Test task submission via API"""
    
    async with AsyncClient(app=app, base_url="http://test") as client:
        response = await client.post(
            "/api/v1/tasks",
            json={
                "task_id": "test-task",
                "prompt": "Write hello world",
                "workspace": "/tmp/test",
                "options": {}
            }
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["task_id"] == "test-task"
        assert data["status"] == "running"
```

### 13.3 E2E Tests

```python
# tests/e2e/test_workflow.py
import pytest
import asyncio
from agent_worker.server_client import ClaudeServerClient

@pytest.mark.asyncio
@pytest.mark.e2e
async def test_full_workflow():
    """Test full task workflow from submission to completion"""
    
    client = ClaudeServerClient("http://localhost:8000", "test-key")
    
    # Submit task
    result = await client.submit_task(
        task_id="e2e-test",
        prompt="Create a hello.py file",
        workspace="/tmp/test-workspace"
    )
    
    assert result["status"] == "running"
    
    # Stream progress
    events = []
    async for event in client.stream_progress("e2e-test"):
        events.append(event)
        if event["type"] == "complete":
            break
    
    # Verify completion
    assert any(e["type"] == "complete" for e in events)
    assert any(e["type"] == "tool_use" for e in events)
```

---

## 14. Migration Checklist

### Phase 1: Server Development
- [ ] Set up Claude Code Server project structure
- [ ] Implement Agent SDK wrapper
- [ ] Create FastAPI endpoints
- [ ] Implement session management
- [ ] Add WebSocket streaming
- [ ] Write unit tests
- [ ] Create Docker image
- [ ] Document API (OpenAPI spec)

### Phase 2: Integration
- [ ] Create Agent Worker server client
- [ ] Add feature flag for execution mode
- [ ] Refactor agent_worker.py to support both modes
- [ ] Update claude_agent.py to use API
- [ ] Write integration tests
- [ ] Test backward compatibility
- [ ] Update documentation

### Phase 3: Production Features
- [ ] Add session persistence (Redis)
- [ ] Implement rate limiting
- [ ] Add authentication/authorization
- [ ] Set up monitoring (Prometheus)
- [ ] Configure structured logging
- [ ] Load testing
- [ ] Security audit
- [ ] Create runbooks

### Phase 4: Deployment
- [ ] Create docker-compose for local dev
- [ ] Create Kubernetes manifests
- [ ] Set up CI/CD pipeline
- [ ] Deploy to staging
- [ ] Performance testing
- [ ] Deploy to production
- [ ] Monitor metrics
- [ ] Gradual rollout (canary)

### Phase 5: Cleanup
- [ ] Remove CLI execution code
- [ ] Remove agent_inside.sh
- [ ] Update Docker image
- [ ] Archive old documentation
- [ ] Announce deprecation
- [ ] Final migration verification

---

## 15. Risks & Mitigation

| Risk | Impact | Probability | Mitigation |
|------|--------|-------------|------------|
| Agent SDK instability | High | Medium | Thorough testing, fallback to CLI |
| Performance regression | High | Medium | Benchmark before/after, optimize |
| Session management complexity | Medium | High | Simple design, Redis for state |
| Breaking changes in Agent SDK | Medium | Low | Pin versions, test upgrades |
| Security vulnerabilities | High | Low | Security audit, input validation |
| Resource exhaustion | High | Medium | Resource limits, monitoring |
| Migration failures | High | Low | Feature flag, rollback plan |

---

## 16. Success Metrics

### Technical Metrics
- **Latency:** P95 task submission < 200ms
- **Throughput:** > 100 tasks/hour per instance
- **Availability:** > 99.5% uptime
- **Error rate:** < 1% task failures
- **Resource usage:** < 4GB memory per session

### Business Metrics
- **Developer productivity:** 30% faster task execution
- **Cost reduction:** 20% lower infrastructure costs
- **Reliability:** 50% fewer execution failures
- **Observability:** 100% task traceability

---

## 17. Future Enhancements

### Short-term (3-6 months)
1. **Multi-agent orchestration:** Parallel task execution
2. **Advanced queuing:** Priority queues, SLA guarantees
3. **Session sharing:** Share sessions between tasks
4. **Custom plugins:** Load custom MCP tools

### Long-term (6-12 months)
1. **Distributed execution:** Multi-region deployment
2. **Cost optimization:** Intelligent model selection
3. **Advanced analytics:** Task success prediction
4. **Integration ecosystem:** GitHub Actions, GitLab CI
5. **UI dashboard:** Web-based task monitoring

---

## 18. Conclusion

This architecture redesign achieves the following goals:

✅ **Separation of Concerns:** Orchestration logic cleanly separated from agent execution  
✅ **Programmatic Control:** Full API access to agent capabilities  
✅ **Better Observability:** Structured messages, real-time streaming, metrics  
✅ **Scalability:** Horizontal scaling, resource management  
✅ **Session Continuity:** Persistent conversations across tasks  
✅ **Maintainability:** Cleaner codebase, better testing  

The phased implementation approach minimizes risk while delivering incremental value. The feature flag strategy ensures smooth migration with rollback capability.

**Next Steps:**
1. Review and approve design document
2. Create implementation tickets
3. Set up development environment
4. Begin Phase 1 implementation

---

## Appendix A: References

- [Agent SDK Python Documentation](https://platform.claude.com/docs/en/agent-sdk/python)
- [FastAPI Documentation](https://fastapi.tiangolo.com/)
- [WebSocket Protocol](https://developer.mozilla.org/en-US/docs/Web/API/WebSockets_API)
- [OpenTelemetry Python](https://opentelemetry.io/docs/instrumentation/python/)
- [Prometheus Client Python](https://github.com/prometheus/client_python)

## Appendix B: Glossary

- **Agent SDK:** Python/TypeScript SDK for programmatic access to Claude Code
- **ClaudeSDKClient:** Persistent client for multi-turn conversations
- **Session:** A persistent conversation context with Claude
- **Task:** A single unit of work submitted to the agent
- **Worktree:** Git feature for isolated branch checkouts
- **MCP:** Model Context Protocol for custom tool integration

---

**Document Version History:**

| Version | Date | Author | Changes |
|---------|------|--------|---------|
| 1.0 | 2026-01-19 | System | Initial design document |
