# Agent Worker 🤖

A powerful Python tool for orchestrating containerized AI coding agents that work autonomously on development tasks. Agent Worker creates isolated Docker environments, manages git branches, and executes tasks using Claude Code with full automation and comprehensive statistics tracking.

**Version 2.1.0** - Enhanced with .env support, image caching, and clean tree validation!

## Features

✨ **Key Capabilities:**
- 🐳 **Containerized Execution**: Isolated Docker environments for safe agent operations
- 🌿 **Git Integration**: Automatic branch creation and change tracking
- 🤖 **Autonomous Agents**: Claude Code agents work independently until task completion
- 📊 **Detailed Statistics**: Track time, tokens, LOC changes, and more
- 🔒 **Security**: Firewall rules and isolated workspace environments
- 📝 **Comprehensive Logging**: Full visibility into agent operations
- 🌐 **Remote Docker Support**: Execute on remote Docker hosts
- 🔌 **Extensible**: Plugin architecture for multiple AI backends
- 🛡️ **Robust Error Handling**: Comprehensive exception handling
- ⚙️ **.env File Support**: Easy configuration management with environment files
- ⚡ **Smart Image Caching**: Skip rebuilds for 90% faster subsequent runs
- ✅ **Clean Tree Validation**: Ensures reproducible results from known state

## Quick Links

- **[Changelog](CHANGELOG.md)** - What's new in version 2.1.0
- **[Docker Hub](https://hub.docker.com/)** - Docker installation

## Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                     Host System                             │
│  ┌──────────────────────────────────────────────────────┐  │
│  │         agent_worker.py (Orchestrator)                │  │
│  │  • Validates prerequisites                            │  │
│  │  • Creates git branch                                 │  │
│  │  • Builds Docker image (with caching)                 │  │
│  │  • Manages container lifecycle                        │  │
│  │  • Collects statistics                                │  │
│  └────────────────┬─────────────────────────────────────┘  │
│                   │                                          │
│  ┌────────────────▼─────────────────────────────────────┐  │
│  │           Docker Container                            │  │
│  │  ┌────────────────────────────────────────────────┐  │  │
│  │  │    agent_inside.sh (Container Executor)        │  │  │
│  │  │  • Runs Claude Code                            │  │  │
│  │  │  • Monitors execution                          │  │  │
│  │  │  • Captures metrics                            │  │  │
│  │  └────────────────────────────────────────────────┘  │  │
│  │                                                        │  │
│  │  Workspace: /workspace (mounted from host)            │  │
│  │  Environment: Claude Code + dev tools                 │  │
│  └────────────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────┘
```

## Prerequisites

### Required:
- **Docker**: Version 20.10 or higher
- **Git**: Version 2.0 or higher
- **Anthropic API Key**: For Claude Code access

### For Shell Version:
## Prerequisites

### Required:
- **Docker**: Version 20.10 or higher
- **Git**: Version 2.0 or higher
- **Python**: Version 3.8 or higher
- **Anthropic API Key**: For Claude Code access

### System Requirements:
- Linux or macOS (Windows with WSL2)
- Minimum 4GB RAM available for containers
- Docker daemon running and accessible

## Installation

### 1. Clone or Navigate to Repository
```bash
cd agent_worker
```

### 2. Install Python Dependencies

```bash
pip install -r requirements.txt
```

### 3. Configure Environment Variables (Recommended)

Create a `.env` file for easy configuration:

```bash
cp .env.example .env
# Edit .env with your settings
nano .env
```

Example `.env` file:
```bash
# Required
ANTHROPIC_API_KEY=your_api_key_here

# Optional
ANTHROPIC_BASE_URL=https://api.anthropic.com
TZ=America/New_York
AGENT_TIMEOUT=3600
```

Or set environment variables directly:
```bash
export ANTHROPIC_API_KEY="your-api-key-here"
export ANTHROPIC_BASE_URL="https://api.anthropic.com"  # Optional
export TZ="Asia/Shanghai"  # Optional
```

### 4. Make Script Executable

```bash
chmod +x agent_worker.py
```

### 5. Verify Installation

```bash
./agent_worker.py --help
```

## Configuration

The agent worker supports multiple configuration methods (in order of precedence):

1. **Command-line arguments** (highest priority)
2. **Environment variables**
3. **.env file** (most convenient)
4. **Defaults** (lowest priority)

### .env File Configuration

The `.env` file is automatically loaded from the agent_worker directory. This is the **recommended** approach for persistent configuration:

```bash
# Required Configuration
ANTHROPIC_API_KEY=your_api_key_here

# Optional Configuration
ANTHROPIC_BASE_URL=https://api.anthropic.com    # Custom API endpoint
TZ=America/New_York                              # Container timezone
AGENT_TIMEOUT=3600                               # Execution timeout (seconds)
DOCKER_HOST=tcp://remote-host:2375              # Remote Docker host
PROJECT_PATH=/path/to/project                    # Default project directory
AGENT_TYPE=claude                                # Agent type (currently: claude)
DEBUG=true                                       # Enable debug logging
```

### Environment Variables

All settings in `.env` can also be set as environment variables:

```bash
export ANTHROPIC_API_KEY="your-key"
export ANTHROPIC_BASE_URL="https://custom.api.com"
```

### Command-Line Arguments

Command-line arguments override both `.env` and environment variables. See usage examples below.

## Usage

### Basic Usage

```bash
python3 agent_worker.py --task "Your task description here"
```

### With Custom Branch Name

```bash
python3 agent_worker.py \
  --task "Fix TypeScript errors in src directory" \
  --branch "fix/typescript-errors"
```

### Remote Docker Execution

```bash
python3 agent_worker.py \
  --remote-docker "tcp://192.168.1.100:2375" \
  --task "Add authentication feature"
```

### Full Options

```bash
python3 agent_worker.py \
  --project /path/to/project \
  --branch "feature/new-feature" \
  --task "Add new feature X with tests" \
  --agent-type claude \
  --api-key "sk-ant-..." \
  --base-url "https://api.custom.com" \
  --remote-docker "tcp://host:2375" \
  --timeout 7200 \
  --force-rebuild \
  --debug
```

**Important:** The agent worker requires a clean git working tree. Commit or stash any uncommitted changes before running.

## Performance Optimizations

The agent worker includes several optimizations for faster execution:

### Docker Image Caching

By default, the agent worker **skips rebuilding** the Docker image if it already exists. This dramatically speeds up subsequent runs:

```bash
# First run: builds image (~2-5 minutes)
./agent_worker.py --task "Add feature A"

# Second run: skips build (~instant)
./agent_worker.py --task "Add feature B"
```

To force a rebuild (e.g., after updating dependencies):

```bash
./agent_worker.py --task "Your task" --force-rebuild
```

#### Clean Working Tree Requirement

The agent worker requires a clean git working tree to ensure:
- **Reproducible results** - starts from a known state
- **Clear attribution** - all changes are from the agent
- **Easy rollback** - can safely discard the agent's branch

If you have uncommitted changes:

```bash
# Option 1: Commit your changes
git add .
git commit -m "My changes"

# Option 2: Stash your changes
git stash

# Then run the agent
./agent_worker.py --task "Your task"

# Later: restore stashed changes
git stash pop
```

## Command Line Options

| Option | Description | Default |
|--------|-------------|---------|
| `--project <path>` | Path to project directory | Current directory |
| `--branch <name>` | Git branch name | `agent-task-<timestamp>` |
| `--task <description>` | Task for the agent (required) | - |
| `--api-key <key>` | Anthropic API key | `$ANTHROPIC_API_KEY` |
| `--base-url <url>` | Custom API endpoint | `$ANTHROPIC_BASE_URL` |
| `--timezone <tz>` | Container timezone | System timezone / UTC |
| `--timeout <seconds>` | Execution timeout | 3600 (1 hour) |
| `--remote-docker <url>` | Remote Docker host | Local Docker |
| `--force-rebuild` | Force rebuild Docker image | false |
| `--debug` | Enable debug logging | false |
| `--help, -h` | Show help message | - |

## Environment Variables

| Variable | Description | Required |
|----------|-------------|----------|
| `ANTHROPIC_API_KEY` | API key for Claude Code | Yes |
| `ANTHROPIC_BASE_URL` | Base URL for Claude API (custom endpoints) | No |
| `TZ` | Timezone setting | No |
| `AGENT_TIMEOUT` | Max execution time (seconds) | No (default: 3600) |

## Examples

### Example 1: Fix Bugs

```bash
python3 agent_worker.py \
  --task "Fix all ESLint errors in the codebase and ensure tests pass"
```

### Example 2: Add Feature

```bash
python3 agent_worker.py \
  --branch "feature/dark-mode" \
  --task "Implement dark mode theme support with toggle in settings"
```

### Example 3: Refactoring

```bash
python3 agent_worker.py \
  --task "Refactor the authentication module to use async/await instead of callbacks"
```

### Example 4: Documentation

```bash
python3 agent_worker.py \
  --task "Add JSDoc comments to all public functions in src/api/ directory"
```

### Example 5: Remote Docker Execution

```bash
python3 agent_worker.py \
  --remote-docker "tcp://build-server:2375" \
  --task "Run full test suite and fix failures"
```

### Example 6: Debug Mode

```bash
python3 agent_worker.py --task "Refactor auth module" --debug
```

## Statistics & Reporting

After execution, Agent Worker provides a detailed report:

```
╔═══════════════════════════════════════════════════════════╗
║               AGENT EXECUTION REPORT                      ║
╠═══════════════════════════════════════════════════════════╣
║ Branch:           feature/new-api-endpoint               ║
║ Duration:         5m 23.4s                                ║
║ Exit Code:        0                                       ║
╠═══════════════════════════════════════════════════════════╣
║ TOKEN USAGE                                               ║
║   Total:          15420                                   ║
║   Input:          8230                                    ║
║   Output:         7190                                    ║
╠═══════════════════════════════════════════════════════════╣
║ CODE CHANGES                                              ║
║   Lines Added:    234                                     ║
║   Lines Removed:  87                                      ║
║   Files Changed:  5                                       ║
╚═══════════════════════════════════════════════════════════╝

Changed files:
  📝 src/api/users.js
  ➕ src/api/endpoints.js
  📝 tests/api/users.test.js
  📝 README.md
  📝 package.json
```

## How It Works

### Workflow

1. **Initialization**: Agent Worker validates inputs and API key
2. **Branch Creation**: Creates a new git branch for the task
3. **Docker Build**: Builds or uses cached Docker image with Claude Code
4. **Container Launch**: Starts container with workspace mounted
5. **Task Assignment**: Copies task to container and starts agent
6. **Autonomous Execution**: Agent works independently until completion
7. **Statistics Collection**: Gathers metrics from git and agent output
8. **Cleanup**: Stops and removes container
9. **Reporting**: Displays comprehensive execution report

### Agent Execution Inside Container

The `agent_inside.sh` script:
- Sets up git configuration
- Creates a task description file
- Launches Claude Code with the task
- Monitors execution and captures output
- Tracks token usage and conversation turns
- Handles errors and timeouts
- Reports back to orchestrator

### Security Features

- Isolated Docker containers
- Network firewall rules via `init-firewall.sh`
- Read/write workspace isolation
- No host system access except mounted workspace
- Configurable timeouts to prevent runaway execution

## Troubleshooting

### Docker Permission Issues

```bash
# Add user to docker group
sudo usermod -aG docker $USER
# Re-login or run:
newgrp docker
```

### API Key Not Found

```bash
# Ensure environment variable is set
echo $ANTHROPIC_API_KEY
# Or pass directly
./agent_worker.py --api-key "your-key"
```

### Container Build Failures

```bash
# Clean Docker cache
docker system prune -a
# Rebuild
docker build -t agent-worker:latest .
```

### Git Conflicts

Agent Worker requires a clean git working directory. Commit or stash changes before running.

### Port Conflicts

If using services in container, ensure ports are available on host.

## Advanced Configuration

### Adding New Agent Types (Python Version)

The Python version uses a plugin architecture for agents:

```python
# agents/my_agent.py
from .base_agent import BaseAgent, AgentException

class MyCustomAgent(BaseAgent):
    """Custom agent implementation"""
    
    def get_execution_script(self) -> str:
        return str(self.config.project_path / 'agent_worker' / 'my_agent_script.sh')
    
    def execute(self, container, docker_manager):
        # Custom execution logic
        pass
    
    def parse_output(self, output: str):
        # Custom output parsing
        pass
```

Then update `agent_worker.py` to support your agent type.

### Remote Docker Configuration

```bash
# TCP connection (unsecured - use with caution)
python3 agent_worker.py \
  --remote-docker "tcp://192.168.1.100:2375" \
  --task "Your task"

# Unix socket (local only)
python3 agent_worker.py \
  --remote-docker "unix:///var/run/docker.sock" \
  --task "Your task"

# SSH tunnel (recommended for remote)
ssh -L 2375:localhost:2375 user@remote-host
python3 agent_worker.py \
  --remote-docker "tcp://localhost:2375" \
  --task "Your task"
```

### Custom Dockerfile Modifications

Edit [Dockerfile](Dockerfile) to:
- Change base image
- Add more development tools
- Modify Claude Code version
- Adjust security settings

### Timeout Configuration

```bash
# Set 2-hour timeout (in seconds)
AGENT_TIMEOUT=7200 ./agent_worker.py --task "Long task"
# Or use command-line argument
./agent_worker.py --timeout 7200 --task "Long task"
```

### Multiple Projects

```bash
# Process multiple projects sequentially
for project in project1 project2 project3; do
  ./agent_worker.py --project "./$project" --task "Update dependencies"
done
```

## Limitations & Considerations

- **Resource Usage**: Each container requires significant RAM and CPU
- **API Costs**: Claude Code API usage will incur costs based on tokens
- **Task Complexity**: Very complex tasks may require human intervention
- **Docker Requirement**: Must have Docker daemon accessible
- **Network Access**: Agent needs internet access for API calls

## Best Practices

1. **Clear Task Descriptions**: Provide specific, actionable tasks
2. **Scope Management**: Break large tasks into smaller chunks
3. **Branch Naming**: Use descriptive branch names with prefixes
4. **Monitor Costs**: Track token usage to manage API costs
5. **Review Changes**: Always review agent changes before merging
6. **Test Isolation**: Run in separate branches for safety

## Development

### Project Structure

```
agent_worker/
├── agent_worker.py        # Main orchestrator
├── config.py              # Configuration management
├── docker_manager.py      # Docker operations
├── agents/                # Agent implementations
│   ├── __init__.py       
│   ├── base_agent.py     # Abstract base class
│   └── claude_agent.py   # Claude Code implementation
├── container/             # Container-related files
│   ├── Dockerfile        # Container image definition
│   └── agent_inside.sh   # Container execution script
├── requirements.txt       # Python dependencies
├── .env.example          # Configuration template
├── README.md             # This file
└── CHANGELOG.md          # Version history
```

### Contributing

Contributions welcome! Please:
1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Submit a pull request

### Running in Development

```bash
# Run Python linting
pip install pylint
pylint agent_worker.py config.py docker_manager.py agents/*.py

# Run type checking
pip install mypy
mypy agent_worker.py config.py docker_manager.py

# Test locally
./agent_worker.py --task "Simple test task"
```

## License

MIT License - See [LICENSE](../LICENSE) for details

## Support

For issues, questions, or contributions:
- **GitHub Issues**: https://github.com/cyberelf/agent_skills/issues
- **Repository**: https://github.com/cyberelf/agent_skills

## Changelog

### Version 1.0.0 (2026-01-18)
- Initial release
- Docker container orchestration
- Git branch management
- Claude Code integration
- Statistics tracking and reporting
- Comprehensive error handling

---

Built with ❤️ for autonomous development workflows
