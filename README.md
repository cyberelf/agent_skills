# Agent Skills & Infrastructure Repository

A centralized repository for maintaining agent skills, meta-skills, and AI coding agent infrastructure for software development tasks.

## Structure

```
agent_skills/
├── skills/                  # Individual agent skills
├── agent_manager/           # Agent orchestration system
├── claude_code_server/      # Claude Code Server daemon
└── docs/                    # Documentation
```

## Components

### Agent Manager

Orchestrator for AI coding tasks that manages git branches and communicates with Claude Code Server.

- **Location**: [agent_manager/](agent_manager/)
- **Purpose**: Task orchestration, git management, statistics collection
- **Version**: 3.0.0 (Server-only architecture)

[Read more →](agent_manager/README.md)

### Claude Code Server

Containerized daemon service providing REST API and WebSocket streaming for Claude Code execution via Agent SDK.

- **Location**: [claude_code_server/](claude_code_server/)
- **Purpose**: Persistent Agent SDK sessions, task execution, real-time streaming
- **Deployment**: Docker container on port 8000

[Read more →](claude_code_server/README.md)

### Skills

Individual agent skills for specific development tasks:

- **[introspection](skills/introspection/SKILL.md)** - Meta-skill for self-analysis and improvement of agent capabilities
- **[issue-fixer](skills/issue-fixer/SKILL.md)** - Systematic approach for investigating and fixing bugs
- **[openspec-constitution-guard](skills/openspec-constitution-guard/SKILL.md)** - Compose project AGENTS.md files into openspec commands for quality validation

## Quick Start

### 1. Deploy Claude Code Server

```bash
cd claude_code_server
docker-compose up -d
curl http://localhost:8000/health  # Verify
```

### 2. Setup Agent Manager

```bash
cd agent_manager
pip install -r requirements.txt
export CLAUDE_SERVER_URL=http://localhost:8000
```

### 3. Run a Task

```bash
python3 agent_manager.py --task "Add unit tests for auth module"
```

## Architecture

```
┌────────────────────┐
│  Agent Manager     │  ← Orchestration Layer
│  • Git branches    │
│  • Task routing    │
│  • Statistics      │
└─────────┬──────────┘
          │ HTTP/WebSocket
          ↓
┌─────────────────────┐
│ Claude Code Server  │  ← Execution Layer (Daemon)
│ • Agent SDK         │
│ • Session mgmt      │
│ • Task execution    │
│ • Real-time stream  │
└─────────────────────┘
   Docker Container
```

## Documentation

- **[v3.0 Refactoring Summary](docs/v3-refactoring-summary.md)** - Architecture changes and rationale
- **[Design Document](docs/claude-code-server-design.md)** - System architecture and design decisions
- **[Phase 2 Summary](docs/phase2-implementation-summary.md)** - Initial integration details

## License

MIT License
