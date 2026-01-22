# Changelog

## Version 3.0.0 (2026-01-19)

### 🎉 Major Architecture Refactoring

Complete redesign focused on server-only execution with Claude Code Server as a containerized daemon.

### Breaking Changes

- **Removed CLI Mode**: No longer supports Docker-based one-shot claude CLI execution
- **Removed Docker Dependency**: Agent Manager no longer requires Docker (only Claude Code Server does)
- **Renamed**: `agent_worker` → `agent_manager` to better reflect orchestration role
- **Simplified Configuration**: Removed all CLI-mode specific fields

### Added

#### 1. Server-Only Architecture
- Claude Code Server runs as containerized daemon service
- Agent Manager communicates via HTTP/WebSocket only
- Persistent Agent SDK sessions for better performance
- Real-time progress monitoring

#### 2. Simplified Agent Manager
- Removed dual-mode complexity
- Only ServerAgent implementation
- No Docker initialization in agent manager
- Cleaner, more maintainable codebase

#### 3. Streamlined Configuration
- Only server-related configuration fields
- Removed: `execution_mode`, `agent_type`, `api_key`, `base_url`, `remote_docker`, `timezone`, `container_name`, `force_rebuild`
- Kept: `server_url`, `server_api_key`, `timeout`, `debug`
- Simpler validation logic

### Removed

**Files Deleted**:
- `agents/claude_agent.py` - Old CLI-based agent
- `docker_manager.py` - Docker orchestration
- `container/Dockerfile` - Agent container build
- `container/agent_inside.sh` - Container execution script

**Code Removed**:
- All CLI mode execution logic
- Docker initialization and cleanup
- Dual-mode routing
- CLI-specific configuration fields
- Container management code

### Changed

- **Directory Name**: `agent_worker/` → `agent_manager/`
- **Main Script**: Focus on orchestration, not execution
- **Configuration**: Simplified to server-only settings
- **Dependencies**: Removed `docker` package, kept `aiohttp`
- **Documentation**: Complete rewrite for server-only architecture

### Technical Details

**New Architecture**:
```
Agent Manager (Orchestrator)
     ↓ HTTP/WebSocket
Claude Code Server (Daemon)
     ↓ Agent SDK
Claude AI
```

**Performance**:
- **Startup**: < 2 seconds (vs 30-60s with Docker)
- **Overhead**: Minimal HTTP request overhead only
- **Sessions**: Reused across multiple tasks
- **Scalability**: Handle concurrent tasks easily

**Configuration Example**:
```bash
# Before (v2.x)
AGENT_EXECUTION_MODE=server
CLAUDE_SERVER_URL=http://localhost:8000
ANTHROPIC_API_KEY=sk-...  # Not needed anymore

# After (v3.0)
CLAUDE_SERVER_URL=http://localhost:8000
# That's it!
```

### Migration Guide (v2.x to v3.0)

#### 1. Update Environment Variables
```bash
# Remove old CLI mode vars
unset AGENT_EXECUTION_MODE
unset ANTHROPIC_API_KEY
unset ANTHROPIC_BASE_URL

# Keep server vars
export CLAUDE_SERVER_URL=http://localhost:8000
export CLAUDE_SERVER_API_KEY=your-key  # optional
```

#### 2. Update Command Usage
```bash
# Before (v2.x)
python3 agent_worker.py --execution-mode server --task "..."

# After (v3.0)
python3 agent_manager.py --task "..."
```

#### 3. Ensure Claude Code Server is Running
```bash
cd claude_code_server
docker-compose up -d
```

### Backward Compatibility

**NOT backward compatible** with v2.x CLI mode. If you need CLI mode:
- Use v2.x releases
- Or deploy claude CLI in a separate container and integrate manually

### Upgrade Instructions

1. **Stop any running agent_worker processes**
2. **Update configuration** (remove CLI mode settings)
3. **Deploy Claude Code Server** (if not already running)
4. **Update code**: Rename `agent_worker` to `agent_manager`
5. **Test with simple task**:
   ```bash
   python3 agent_manager.py --task "Add a comment to README"
   ```

### Benefits of v3.0

- ⚡ **50-90% faster** - No Docker overhead
- 🎯 **Simpler** - 500+ lines of code removed
- 🔧 **More maintainable** - Single execution path
- 📡 **Better observability** - Real-time WebSocket streaming
- 🚀 **More scalable** - Concurrent tasks support
- 🐛 **Easier to debug** - Fewer moving parts

---

## Version 2.2.0 (2026-01-19) - DEPRECATED

Dual-mode execution (CLI + Server). Use v3.0 for server-only.

## Version 2.1.0 (2026-01-18) - DEPRECATED

CLI-mode only with Docker. Use v3.0 for server-based execution.
