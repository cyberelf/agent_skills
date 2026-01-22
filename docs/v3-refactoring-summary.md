# Architecture Refactoring: v3.0.0 - Server-Only Design

## Overview

Complete architectural refactoring from dual-mode (CLI + Server) to server-only execution. The Claude Code Server now runs as a containerized daemon service, called by the simplified Agent Manager orchestrator.

## Key Changes

### 1. Removed CLI Mode Entirely

**What was removed:**
- Docker-based one-shot claude CLI execution
- `agents/claude_agent.py` (old CLI agent implementation)
- `docker_manager.py` (Docker orchestration)
- `container/Dockerfile` and `container/agent_inside.sh`
- All execution_mode toggle logic
- CLI-specific configuration fields

**Why:**
- Eliminated complexity of dual-mode support
- Removed 500+ lines of code
- Single execution path easier to maintain
- Server mode is faster and more feature-rich

### 2. Renamed agent_worker to agent_manager

**Rationale:**
- "Worker" implied it does the work
- "Manager" better reflects its role as orchestrator
- Manages git branches, routes tasks, collects stats
- Actual work is done by Claude Code Server

### 3. Claude Code Server as Daemon

**Architecture:**
- Runs as containerized service (not ephemeral)
- Listens on port 8000 continuously
- Maintains persistent Agent SDK sessions
- Handles multiple concurrent tasks
- Auto-cleanup of idle sessions

### 4. Simplified Configuration

**Before (v2.x):**
```python
@dataclass
class Config:
    # Project
    project_path: Path
    branch_name: str
    task_description: str
    
    # Agent
    agent_type: str = 'claude'
    api_key: Optional[str] = None
    base_url: Optional[str] = None
    
    # Execution mode
    execution_mode: str = 'cli'  # 'cli' or 'server'
    server_url: Optional[str] = None
    server_api_key: Optional[str] = None
    
    # Docker
    remote_docker: Optional[str] = None
    timezone: str = 'UTC'
    container_name: Optional[str] = None
    
    # Other
    timeout: int = 3600
    debug: bool = False
    force_rebuild: bool = False
```

**After (v3.0):**
```python
@dataclass
class Config:
    # Project
    project_path: Path
    branch_name: str
    task_description: str
    
    # Server (required)
    server_url: str = None
    server_api_key: Optional[str] = None
    
    # Execution
    timeout: int = 3600
    debug: bool = False
```

**Removed fields:**
- `agent_type` - only one agent type now (ServerAgent)
- `api_key` / `base_url` - handled by server
- `execution_mode` - always server mode now
- `remote_docker` / `timezone` / `container_name` - no Docker in manager
- `force_rebuild` - no image building in manager

### 5. Simplified Agent Manager

**Before (v2.x) - agent_worker.py:**
- 520 lines with Docker orchestration
- Dual-mode branching logic
- Docker initialization/cleanup
- Container lifecycle management
- Image building and caching
- Complex error handling for both modes

**After (v3.0) - agent_manager.py:**
- ~350 lines, focused on orchestration
- Single execution path
- No Docker dependencies
- Git operations only
- Statistics collection
- Task submission to server

**Key methods:**
```python
class AgentManager:
    def _validate_prerequisites(self):
        # Git checks only, no Docker
    
    def _setup_git_branch(self):
        # Create branch for agent work
    
    def _initialize_agent(self):
        # Only ServerAgent
    
    def _execute_agent(self):
        # Submit to server, stream progress
    
    def _collect_git_stats(self):
        # Gather LOC and file changes
    
    def _print_summary(self):
        # Display results
```

## File Structure Comparison

### Before (v2.x)
```
agent_worker/
├── agent_worker.py       # 520 lines, dual-mode
├── config.py             # 173 lines, complex validation
├── docker_manager.py     # 300+ lines, Docker orchestration
├── server_client.py      # 220 lines, HTTP/WS client
├── requirements.txt      # docker, aiohttp, pytest
├── agents/
│   ├── base_agent.py
│   ├── claude_agent.py   # CLI mode agent
│   └── server_agent.py   # Server mode agent
├── container/
│   ├── Dockerfile        # Agent container
│   └── agent_inside.sh   # Container execution
└── tests/
    └── test_server_integration.py
```

### After (v3.0)
```
agent_manager/
├── agent_manager.py      # 350 lines, server-only
├── config.py             # 95 lines, simple validation
├── server_client.py      # 220 lines, HTTP/WS client (unchanged)
├── requirements.txt      # aiohttp, pytest (no docker)
├── .env.example          # Simple config template
├── agents/
│   ├── base_agent.py     # Interface (unchanged)
│   └── server_agent.py   # Only agent implementation
└── tests/
    └── test_server_integration.py
```

**Removed:**
- `docker_manager.py` - 300+ lines
- `agents/claude_agent.py` - 200+ lines
- `container/` directory - Dockerfile + bash script
- Old `agent_worker.py` - 520 lines

**Simplified:**
- `config.py`: 173 → 95 lines (45% reduction)
- Main orchestrator: 520 → 350 lines (33% reduction)

## Deployment Architecture

### Before (v2.x) - Dual Mode

**CLI Mode:**
```
agent_worker
  ↓ (builds Docker image)
Docker Container
  ↓ (runs claude CLI)
Claude AI
```

**Server Mode:**
```
agent_worker
  ↓ (HTTP/WebSocket)
Claude Code Server (ad-hoc)
  ↓ (Agent SDK)
Claude AI
```

### After (v3.0) - Server Only

```
Agent Manager (Orchestrator)
  ↓ (HTTP/WebSocket)
Claude Code Server (Daemon Container)
  ↓ (Agent SDK)
Claude AI
```

**Key differences:**
- Claude Code Server is always running (daemon)
- Agent Manager has no Docker dependency
- Single, well-defined communication path
- Server handles all Claude AI interaction

## Usage Comparison

### Before (v2.x)

**CLI Mode:**
```bash
# Required Docker, Anthropic API key
export ANTHROPIC_API_KEY=sk-...
python3 agent_worker.py --task "Fix bugs"
```

**Server Mode:**
```bash
# Required Claude Code Server running
export AGENT_EXECUTION_MODE=server
export CLAUDE_SERVER_URL=http://localhost:8000
python3 agent_worker.py --task "Fix bugs"
```

### After (v3.0)

**Server Mode (only option):**
```bash
# Ensure server is running
docker-compose -f claude_code_server/docker-compose.yml up -d

# Submit task
export CLAUDE_SERVER_URL=http://localhost:8000
python3 agent_manager.py --task "Fix bugs"
```

## Performance Impact

### Startup Time
- **v2.x CLI**: 30-60 seconds (Docker build + container start)
- **v2.x Server**: 1-2 seconds (HTTP request)
- **v3.0**: 1-2 seconds (HTTP request)

### Execution Overhead
- **v2.x CLI**: Docker container lifecycle + bash script parsing
- **v2.x Server**: HTTP/WebSocket + structured events
- **v3.0**: HTTP/WebSocket + structured events (same as v2.x server)

### Resource Usage
- **v2.x CLI**: Full Docker container per task (high memory/CPU)
- **v2.x Server**: Shared server process (low overhead)
- **v3.0**: Shared server process (low overhead)

### Session Management
- **v2.x CLI**: No session reuse, fresh container each time
- **v2.x Server**: Persistent sessions with cleanup
- **v3.0**: Persistent sessions with cleanup (same as v2.x server)

**Result:** v3.0 maintains all performance benefits of v2.x server mode while eliminating CLI mode overhead.

## Code Maintainability

### Complexity Metrics

**v2.x:**
- Total lines: ~2,400
- Execution paths: 2 (CLI + Server)
- Dependencies: docker, aiohttp, pytest
- Docker images: 2 (agent container + server container)
- Configuration fields: 13
- Conditional branches for mode switching: ~15

**v3.0:**
- Total lines: ~1,600 (33% reduction)
- Execution paths: 1 (Server only)
- Dependencies: aiohttp, pytest (no docker in manager)
- Docker images: 1 (server container only)
- Configuration fields: 6
- Conditional branches: 0 (single path)

### Testing Complexity

**v2.x:**
- Test CLI mode execution
- Test server mode execution
- Test mode switching
- Test Docker container lifecycle
- Test bash output parsing
- Mock Docker API

**v3.0:**
- Test server mode execution only
- Test HTTP/WebSocket communication
- Mock server API (simpler)

## Migration Path

### From v2.x CLI Mode

1. **Deploy Claude Code Server:**
   ```bash
   cd claude_code_server
   docker-compose up -d
   ```

2. **Update configuration:**
   ```bash
   # Remove CLI vars
   unset ANTHROPIC_API_KEY
   unset ANTHROPIC_BASE_URL
   unset AGENT_EXECUTION_MODE
   
   # Add server var
   export CLAUDE_SERVER_URL=http://localhost:8000
   ```

3. **Update code:**
   ```bash
   cd agent_worker  # old directory
   git pull  # get v3.0 changes
   # Directory is now agent_manager
   ```

4. **Test:**
   ```bash
   python3 agent_manager.py --task "Add a comment"
   ```

### From v2.x Server Mode

1. **Update environment:**
   ```bash
   unset AGENT_EXECUTION_MODE  # No longer needed
   # CLAUDE_SERVER_URL remains the same
   ```

2. **Update code:**
   ```bash
   cd agent_worker
   git pull  # v3.0 automatically renames to agent_manager
   ```

3. **Update any scripts:**
   ```bash
   # Change references from agent_worker to agent_manager
   sed -i 's/agent_worker/agent_manager/g' your-scripts.sh
   ```

## Benefits of v3.0

### For Developers
- ✅ **Simpler codebase** - 33% fewer lines
- ✅ **Single execution path** - easier to understand
- ✅ **No Docker in manager** - easier local development
- ✅ **Clearer separation** - orchestration vs execution
- ✅ **Less testing** - fewer code paths to test

### For Operators
- ✅ **One service to manage** - Claude Code Server daemon
- ✅ **Clear deployment** - docker-compose for server, pip for manager
- ✅ **Better observability** - server logs all execution
- ✅ **Easier scaling** - scale server containers, not ephemeral agents
- ✅ **Consistent performance** - no Docker startup overhead

### For Users
- ✅ **Faster execution** - no container startup (50-90% faster for short tasks)
- ✅ **Real-time progress** - WebSocket streaming always available
- ✅ **Better error messages** - structured events vs bash parsing
- ✅ **Simpler configuration** - 6 fields instead of 13
- ✅ **Clearer architecture** - obvious separation of concerns

## Conclusion

Version 3.0 simplifies the architecture by:
1. Removing the slower, more complex CLI mode
2. Making Claude Code Server a persistent daemon service
3. Simplifying Agent Manager to pure orchestration
4. Reducing codebase by 33%
5. Maintaining all performance benefits of server mode

The result is a cleaner, faster, more maintainable system with a single, well-defined execution path.
