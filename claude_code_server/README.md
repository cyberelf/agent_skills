# Claude Code Server

A **containerized daemon service** for executing Claude Code tasks via the Agent SDK. Runs persistently as a background service, providing REST API and WebSocket interfaces for task submission and real-time progress streaming. Designed to be called by Agent Manager for orchestrated AI coding tasks.

## Overview

Claude Code Server is a long-running service (daemon) that:
- Runs in a Docker container with persistent sessions
- Listens on port 8000 for API requests
- Maintains Agent SDK connections across multiple tasks
- Provides real-time WebSocket streaming of task progress
- Handles session management and cleanup automatically

## Features

- 🐳 **Containerized Daemon**: Runs as a persistent Docker service
- 🚀 **Persistent Sessions**: Reuse Agent SDK sessions across multiple tasks
- 🔄 **Real-time Streaming**: WebSocket-based progress updates
- 📊 **Full Observability**: Structured events, metrics, and logging
- 🎯 **Task Management**: Submit, monitor, and interrupt tasks
- 🔒 **Security**: Optional API key authentication
- 📈 **Scalable**: Horizontal scaling with Redis backend
- 🌐 **Multi-tenant**: Handle concurrent tasks from multiple clients

## Architecture

```
┌──────────────────┐         HTTP/WebSocket         ┌───────────────────────────┐
│ Agent Manager    │  ─────────────────────▶       │ Claude Code Server        │
│ (Orchestrator)   │  POST /tasks                   │ (Containerized Daemon)    │
│                  │  WS /ws/tasks/{id}            │                           │
│ • Git management │                                │  ┌─────────────────────┐ │
│ • Task routing   │                                │  │ FastAPI Application │ │
│ • Statistics     │                                │  │ • REST Endpoints    │ │
└──────────────────┘                                │  │ • WebSocket Server  │ │
                                                    │  └─────────────────────┘ │
                                                    │  ┌─────────────────────┐ │
                                                    │  │ Session Manager     │ │
                                                    │  │ • Agent SDK Client  │ │
                                                    │  │ • Task Executor     │ │
                                                    │  │ • Event Streaming   │ │
                                                    │  └─────────────────────┘ │
                                                    │                           │
                                                    │  Docker Container         │
                                                    │  Port: 8000               │
                                                    └───────────────────────────┘
```

## Quick Start

### Prerequisites

- Docker & Docker Compose
- Anthropic API key
- Agent Manager (for orchestration)

### Deployment as Daemon Service

1. **Navigate to server directory**
   ```bash
   cd claude_code_server
   ```

2. **Create .env file**
   ```bash
   cat > .env << EOF
   ANTHROPIC_API_KEY=your-api-key-here
   WORKSPACE_PATH=./workspaces
   EOF
   ```

3. **Start daemon service**
   ```bash
   docker-compose up -d
   ```

4. **Verify server is running**
   ```bash
   curl http://localhost:8000/health
   ```

   Expected response:
   ```json
   {"status": "healthy", "version": "1.0.0"}
   ```

The server now runs as a background daemon, ready to accept tasks from Agent Manager.

## API Documentation

### REST Endpoints

#### Health Check
```bash
GET /health
```

Response:
```json
{
  "status": "healthy",
  "version": "1.0.0",
  "active_sessions": 2,
  "active_tasks": 3,
  "uptime_seconds": 3600
}
```

#### Submit Task
```bash
POST /api/v1/tasks
Content-Type: application/json

{
  "task_id": "task-123",
  "prompt": "Implement user authentication",
  "workspace": "/workspace/project",
  "options": {
    "allowed_tools": ["Read", "Write", "Edit", "Bash"],
    "permission_mode": "acceptEdits",
    "max_turns": 50,
    "timeout": 3600
  },
  "session": {
    "reuse_existing": false
  }
}
```

Response:
```json
{
  "task_id": "task-123",
  "session_id": "session-task-123",
  "status": "running",
  "websocket_url": "ws://localhost:8000/ws/tasks/task-123",
  "created_at": "2026-01-19T10:00:00Z"
}
```

#### Get Task Status
```bash
GET /api/v1/tasks/{task_id}
```

#### Interrupt Task
```bash
POST /api/v1/tasks/{task_id}/interrupt
```

#### List Sessions
```bash
GET /api/v1/sessions
```

#### Delete Session
```bash
DELETE /api/v1/sessions/{session_id}
```

### WebSocket Interface

Connect to receive real-time task updates:

```javascript
const ws = new WebSocket('ws://localhost:8000/ws/tasks/task-123');

ws.onmessage = (event) => {
  const data = JSON.parse(event.data);
  console.log('Event:', data.type, data.data);
};
```

Event types:
- `message`: Assistant messages and responses
- `tool_use`: Tool invocation
- `tool_result`: Tool execution result
- `progress`: Progress update (tokens, turns, files)
- `complete`: Task completion
- `error`: Error occurred

## Configuration

Configuration via environment variables:

### Server
- `SERVER_HOST`: Server host (default: `0.0.0.0`)
- `SERVER_PORT`: Server port (default: `8000`)
- `SERVER_LOG_LEVEL`: Logging level (default: `INFO`)

### API
- `API_AUTH_ENABLED`: Enable authentication (default: `false`)
- `API_API_KEY`: API key for authentication
- `API_RATE_LIMIT_ENABLED`: Enable rate limiting (default: `true`)
- `API_RATE_LIMIT_PER_MINUTE`: Requests per minute (default: `100`)

### Claude SDK
- `CLAUDE_API_KEY`: Anthropic API key (**required**)
- `CLAUDE_BASE_URL`: API base URL (optional)
- `CLAUDE_DEFAULT_MODEL`: Default model (optional)
- `CLAUDE_MAX_TURNS`: Max conversation turns (default: `50`)

### Sessions
- `SESSION_MAX_CONCURRENT`: Max concurrent sessions (default: `10`)
- `SESSION_IDLE_TIMEOUT_SECONDS`: Idle timeout (default: `1800`)
- `SESSION_CLEANUP_INTERVAL_SECONDS`: Cleanup interval (default: `300`)

### Storage
- `STORAGE_TYPE`: Storage backend: `memory`, `redis`, `sqlite` (default: `memory`)
- `STORAGE_REDIS_HOST`: Redis host (default: `localhost`)
- `STORAGE_REDIS_PORT`: Redis port (default: `6379`)

## Development

### Running Tests

```bash
# Install dev dependencies
pip install -r requirements.txt

# Run tests
pytest claude_code_server/tests/ -v

# With coverage
pytest --cov=claude_code_server --cov-report=html
```

### Code Quality

```bash
# Format code
black claude_code_server/

# Lint
ruff check claude_code_server/

# Type checking
mypy claude_code_server/
```

## Monitoring

### Prometheus Metrics

Metrics endpoint: `http://localhost:9090/metrics`

Available metrics:
- `http_requests_total`: Total HTTP requests
- `tasks_total`: Total tasks by status
- `tasks_duration_seconds`: Task execution duration
- `active_sessions`: Active sessions count
- `tokens_used_total`: Token usage by type

### Logging

Structured JSON logging to stdout:

```json
{
  "timestamp": "2026-01-19T10:00:00Z",
  "level": "INFO",
  "logger": "claude_code_server.server",
  "message": "Task completed",
  "task_id": "task-123",
  "duration_ms": 45000,
  "tokens_used": 12500
}
```

## Troubleshooting

### Common Issues

**Problem**: `CLAUDE_API_KEY not set`
**Solution**: Export the environment variable or add to `.env` file

**Problem**: `Maximum concurrent sessions reached`
**Solution**: Increase `SESSION_MAX_CONCURRENT` or wait for idle sessions to cleanup

**Problem**: `WebSocket connection failed`
**Solution**: Ensure task exists before connecting, check firewall rules

## Architecture Details

See [design document](../docs/claude-code-server-design.md) for comprehensive architecture details.

## License

See main repository LICENSE file.

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Run tests and linting
5. Submit a pull request
