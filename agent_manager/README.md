# Agent Manager

AI Coding Agent Orchestrator that manages autonomous coding tasks via Claude Code Server.

**Version 3.0.0** - Streamlined server-only architecture!

## Overview

Agent Manager orchestrates AI coding agents through the Claude Code Server API. It handles git branch management, task execution, and comprehensive statistics tracking. The Claude Code Server runs as a containerized daemon service, providing persistent Agent SDK sessions and real-time progress monitoring.

## Architecture

```
┌──────────────────────────────────────────────────────────┐
│                   Agent Manager                          │
│  • Git branch management                                 │
│  • Task orchestration                                    │
│  • Statistics collection                                 │
│  • Result reporting                                      │
└─────────────────────┬────────────────────────────────────┘
                      │ HTTP/WebSocket
                      │
┌─────────────────────▼────────────────────────────────────┐
│         Claude Code Server (Containerized Daemon)        │
│  ┌────────────────────────────────────────────────────┐  │
│  │  • REST API Endpoints                              │  │
│  │  • WebSocket Streaming                             │  │
│  │  • Agent SDK Integration                           │  │
│  │  • Session Management                              │  │
│  │  • Task Execution                                  │  │
│  └────────────────────────────────────────────────────┘  │
│                                                           │
│  Docker Container (Port 8000)                            │
└──────────────────────────────────────────────────────────┘
```

## Features

✨ **Key Capabilities:**
- 🌐 **Server-Based Execution**: Communicates with Claude Code Server API
- 🌿 **Git Integration**: Automatic branch creation and change tracking
- 🤖 **Autonomous Agents**: Claude Code agents work independently until task completion
- 📊 **Detailed Statistics**: Track time, tokens, LOC changes, and more
- 📡 **Real-time Streaming**: WebSocket-based progress updates
- 📝 **Comprehensive Logging**: Full visibility into agent operations
- ⚙️ **.env File Support**: Easy configuration management
- 🔒 **Clean Tree Validation**: Ensures reproducible results from known state

## Prerequisites

### Required:
- **Python**: Version 3.8 or higher
- **Git**: Version 2.0 or higher
- **Claude Code Server**: Running and accessible (see setup below)

### System Requirements:
- Linux or macOS (Windows with WSL2)
- Docker for Claude Code Server deployment

## Quick Start

### 1. Deploy Claude Code Server

```bash
cd claude_code_server
docker-compose up -d
curl http://localhost:8000/health  # Verify
```

### 2. Install Dependencies

```bash
cd agent_manager
pip install -r requirements.txt
```

### 3. Configure

```bash
export CLAUDE_SERVER_URL=http://localhost:8000
```

### 4. Run a Task

```bash
python3 agent_manager.py --task "Add unit tests for auth module"
```

## Usage

### Basic Usage

```bash
python3 agent_manager.py --task "Your task description here"
```

### With Custom Branch

```bash
python3 agent_manager.py \
  --branch "feature/dark-mode" \
  --task "Implement dark mode theme support"
```

### Full Options

```bash
python3 agent_manager.py \
  --project /path/to/project \
  --branch "feature/new-feature" \
  --task "Add new feature X with tests" \
  --server-url "http://localhost:8000" \
  --server-api-key "your-api-key" \
  --timeout 7200 \
  --debug
```

## Configuration

| Option | Description | Default |
|--------|-------------|---------|
| `--project` | Project directory path | Current directory |
| `--branch` | Git branch name | `agent-task-<timestamp>` |
| `--task` | Task description **(required)** | - |
| `--server-url` | Claude Code Server URL | `$CLAUDE_SERVER_URL` |
| `--server-api-key` | Server API key | `$CLAUDE_SERVER_API_KEY` |
| `--timeout` | Execution timeout (seconds) | 3600 |
| `--debug` | Enable debug logging | false |

### Environment Variables

```bash
# Required
CLAUDE_SERVER_URL=http://localhost:8000

# Optional
CLAUDE_SERVER_API_KEY=your-api-key
AGENT_TIMEOUT=3600
```

Or use a `.env` file:
```bash
cp .env.example .env
nano .env
```

## Examples

### Fix Bugs
```bash
python3 agent_manager.py \
  --task "Fix all ESLint errors in the codebase"
```

### Add Feature
```bash
python3 agent_manager.py \
  --branch "feature/auth" \
  --task "Add JWT authentication with refresh tokens"
```

### Refactoring
```bash
python3 agent_manager.py \
  --task "Refactor database queries to use async/await"
```

### Documentation
```bash
python3 agent_manager.py \
  --task "Add comprehensive JSDoc to all API endpoints"
```

### Testing
```bash
python3 agent_manager.py \
  --task "Add unit tests for user service with 90%+ coverage"
```

## Output

After execution, you'll see:

```
=================================================================
  AGENT EXECUTION SUMMARY
=================================================================
  Status:         ✅ SUCCESS
  Duration:       145.3s
  Branch:         agent-task-1737278400

  TOKEN USAGE
    Total:          12,345
    Input:          8,234
    Output:         4,111

  CODE CHANGES
    Lines Added:    156
    Lines Removed:  42
    Files Changed:  8
=================================================================

📁 Run directory: .agent_runs/run-1737278400
📝 Full logs: .agent_runs/run-1737278400/agent.log

🌿 Git branch: agent-task-1737278400
   To review changes: git diff agent-task-1737278400
   To merge changes:  git merge agent-task-1737278400
   To delete branch:  git branch -d agent-task-1737278400
```

## Managing Claude Code Server

```bash
# Start
docker-compose -f claude_code_server/docker-compose.yml up -d

# Stop
docker-compose -f claude_code_server/docker-compose.yml down

# Logs
docker-compose -f claude_code_server/docker-compose.yml logs -f

# Health check
curl http://localhost:8000/health

# View sessions
curl http://localhost:8000/api/v1/sessions
```

## Troubleshooting

### "server_url is required"
```bash
export CLAUDE_SERVER_URL=http://localhost:8000
```

### Connection Refused
```bash
# Check server is running
docker-compose -f claude_code_server/docker-compose.yml ps
curl http://localhost:8000/health
```

### Clean Working Tree Error
```bash
# Commit changes
git add . && git commit -m "Save work"
# Or stash
git stash
```

### Branch Already Exists
```bash
git branch -D agent-task-1234567890
```

## Project Structure

```
agent_manager/
├── agent_manager.py          # Main orchestrator
├── config.py                 # Configuration
├── server_client.py          # API client
├── requirements.txt          # Dependencies
├── agents/
│   ├── base_agent.py        # Agent interface
│   └── server_agent.py      # Server agent
└── tests/
    └── test_server_integration.py
```

## Development

### Tests
```bash
pytest tests/
```

### Debug Mode
```bash
python3 agent_manager.py --debug --task "Your task"
```

## Related Documentation

- **[Claude Code Server](../claude_code_server/README.md)** - Server setup
- **[Design Document](../docs/claude-code-server-design.md)** - Architecture
- **[CHANGELOG](CHANGELOG.md)** - Version history

## License

See [LICENSE](../LICENSE) file.
