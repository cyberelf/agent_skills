# Agent Worker 🤖

A powerful tool for orchestrating containerized AI coding agents that work autonomously on development tasks. Agent Worker creates isolated Docker environments, manages git branches, and executes tasks using Claude Code with full automation and comprehensive statistics tracking.

## Features

✨ **Key Capabilities:**
- 🐳 **Containerized Execution**: Isolated Docker environments for safe agent operations
- 🌿 **Git Integration**: Automatic branch creation and change tracking
- 🤖 **Autonomous Agents**: Claude Code agents work independently until task completion
- 📊 **Detailed Statistics**: Track time, tokens, LOC changes, and more
- 🔒 **Security**: Firewall rules and isolated workspace environments
- 📝 **Comprehensive Logging**: Full visibility into agent operations

## Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                     Host System                             │
│  ┌──────────────────────────────────────────────────────┐  │
│  │           agent_worker.sh (Orchestrator)              │  │
│  │  • Creates git branch                                 │  │
│  │  • Builds Docker image                                │  │
│  │  • Manages container lifecycle                        │  │
│  │  • Collects statistics                                │  │
│  └────────────────┬─────────────────────────────────────┘  │
│                   │                                          │
│  ┌────────────────▼─────────────────────────────────────┐  │
│  │           Docker Container                            │  │
│  │  ┌────────────────────────────────────────────────┐  │  │
│  │  │      agent_inside.sh (Executor)                │  │  │
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
- **Bash**: Version 4.0 or higher (pre-installed on most Linux/macOS)
- **Git**: Version 2.0 or higher
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

### 2. Make Scripts Executable
```bash
chmod +x agent_worker.sh agent_inside.sh init-firewall.sh
```

### 3. Set Environment Variables
```bash
export ANTHROPIC_API_KEY="your-api-key-here"
export TZ="Asia/Shanghai"  # Optional: set timezone
```

### 4. Build Docker Image
```bash
docker build -t agent-worker:latest .
```

## Usage

### Basic Usage

```bash
./agent_worker.sh --task "Your task description here"
```

### With Custom Branch Name

```bash
./agent_worker.sh \
  --task "Fix TypeScript errors in src directory" \
  --branch "fix/typescript-errors"
```

### Specify Project Path

```bash
./agent_worker.sh \
  --project /path/to/your/project \
  --task "Implement user authentication"
```

### Full Options

```bash
./agent_worker.sh \
  --project /path/to/project \
  --branch "feature/new-feature" \
  --task "Add new feature X with tests" \
  --api-key "sk-ant-..." \
  --timezone "UTC"
```

## Command Line Options

| Option | Description | Default |
|--------|-------------|---------|
| `--project <path>` | Path to project directory | Current directory |
| `--branch <name>` | Git branch name | `agent-task-<timestamp>` |
| `--task <description>` | Task for the agent | Prompts if not provided |
| `--api-key <key>` | Anthropic API key | `$ANTHROPIC_API_KEY` |
| `--timezone <tz>` | Container timezone | System timezone |
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
./agent_worker.sh \
  --task "Fix all ESLint errors in the codebase and ensure tests pass"
```

### Example 2: Add Feature

```bash
./agent_worker.sh \
  --branch "feature/dark-mode" \
  --task "Implement dark mode theme support with toggle in settings"
```

### Example 3: Refactoring

```bash
./agent_worker.sh \
  --task "Refactor the authentication module to use async/await instead of callbacks"
```

### Example 4: Documentation

```bash
./agent_worker.sh \
  --task "Add JSDoc comments to all public functions in src/api/ directory"
```

### Example 5: Testing

```bash
./agent_worker.sh \
  --task "Write unit tests for the UserService class with 100% coverage"
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
./agent_worker.sh --api-key "your-key"
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

### Custom Dockerfile Modifications

Edit [Dockerfile](Dockerfile) to:
- Change base image
- Add more development tools
- Modify Claude Code version
- Adjust security settings

### Timeout Configuration

```bash
# Set 2-hour timeout (in seconds)
AGENT_TIMEOUT=7200 ./agent_worker.sh --task "Long task"
```

### Multiple Projects

```bash
# Process multiple projects sequentially
for project in project1 project2 project3; do
  ./agent_worker.sh --project "./$project" --task "Update dependencies"
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
├── agent_worker.sh       # Main orchestrator (bash)
├── agent_inside.sh       # Container execution script (bash)
├── Dockerfile            # Container image definition
├── init-firewall.sh      # Network security setup
├── package.json          # Project metadata
└── README.md            # This file
```

### Contributing

Contributions welcome! Please:
1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Submit a pull request

### Running in Development

```bash
# Run linting (requires shellcheck)
sudo apt-get install shellcheck  # or: brew install shellcheck
shellcheck agent_worker.sh agent_inside.sh init-firewall.sh

# Test locally
./agent_worker.sh --task "Simple test task"
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
