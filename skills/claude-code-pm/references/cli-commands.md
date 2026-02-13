# Claude Code CLI Commands Reference

Complete reference for Claude Code command-line interface for PM agents managing development teams.

## Table of Contents

1. [Basic Commands](#basic-commands)
2. [Print Mode (Automation)](#print-mode-automation)
3. [Agent Management](#agent-management)
4. [Settings & Configuration](#settings--configuration)
5. [Session Management](#session-management)
6. [Output Formats](#output-formats)
7. [Common Workflows](#common-workflows)

## Basic Commands

### Interactive Mode

Start Claude Code in interactive REPL mode:

```bash
claude
```

With an initial prompt:

```bash
claude "Explain this project"
```

### Print Mode (SDK/Automation)

Execute and exit (non-interactive):

```bash
claude -p "query"
# or
claude --print "query"
```

### Continue Recent Session

Resume most recent conversation in current directory:

```bash
claude -c
# or
claude --continue
```

### Resume Specific Session

Resume by session ID or name:

```bash
claude -r <session-id-or-name>
claude --resume <session-id-or-name>

# Examples:
claude -r auth-refactor
claude -r 550e8400-e29b-41d4-a716-446655440000
```

### Update Claude Code

```bash
claude update
```

## Print Mode (Automation)

Print mode (`-p` or `--print`) is essential for PM agents to programmatically control developer agents.

### Basic Print Mode

```bash
claude -p "Fix the login bug"
```

### With Output Format

```bash
# JSON output for parsing
claude -p --output-format json "Explain auth logic"

# Streaming JSON
claude -p --output-format stream-json "Implement feature"

# Text output (default)
claude -p --output-format text "Check code"
```

### With Max Turns

Limit the number of agentic turns:

```bash
claude -p --max-turns 10 "Fix bug and run tests"
```

### With Budget Limit

Limit API spending:

```bash
claude -p --max-budget-usd 5.00 "Implement feature"
```

### With Piped Input

```bash
cat error.log | claude -p "Analyze this error"
```

### No Session Persistence

Don't save session to disk:

```bash
claude -p --no-session-persistence "Quick analysis"
```

## Agent Management

### Using Inline Agent Definitions

Define custom agents via JSON:

```bash
claude --agents '{
  "debugger": {
    "description": "Expert debugger for finding and fixing bugs",
    "prompt": "You are an expert debugger. Use systematic investigation.",
    "tools": ["Read", "Edit", "Bash", "Grep"],
    "model": "sonnet",
    "skills": ["issue-fixer"],
    "maxTurns": 15
  }
}' "Use the debugger agent to fix the authentication issue"
```

### Agent Definition Fields

| Field | Required | Description | Example |
|-------|----------|-------------|---------|
| `description` | Yes | When to invoke this agent | "Expert code reviewer" |
| `prompt` | Yes | System prompt for agent | "You are a senior developer..." |
| `tools` | No | Allowed tools | `["Read", "Edit", "Bash"]` |
| `disallowedTools` | No | Blocked tools | `["WebFetch"]` |
| `model` | No | Model to use | `"sonnet"`, `"opus"`, `"haiku"`, `"inherit"` |
| `skills` | No | Skills to preload | `["issue-fixer", "testing"]` |
| `mcpServers` | No | MCP servers | `["github", "filesystem"]` |
| `maxTurns` | No | Max agentic turns | `10` |

### Specifying Active Agent

Use a specific agent for the session:

```bash
claude --agent my-debugger "Fix this bug"
```

### Multiple Agents in Print Mode

```bash
# Define multiple agents
claude -p --agents '{
  "designer": {
    "description": "Design system architect",
    "prompt": "Create scalable system designs",
    "model": "opus"
  },
  "developer": {
    "description": "Implementation specialist",
    "prompt": "Implement features following design",
    "model": "sonnet"
  }
}' "Use designer to create design, then developer to implement"
```

## Settings & Configuration

### Using Settings Files

Load settings from file:

```bash
claude --settings ./path/to/settings.json
```

Load settings from JSON string:

```bash
claude --settings '{"permissions":{"allow":["Bash(npm *)"]}}'
```

### Setting Sources

Control which settings to load:

```bash
# Only user and project settings (skip local)
claude --setting-sources user,project

# Only user settings
claude --setting-sources user
```

### Additional Working Directories

Give Claude access to additional directories:

```bash
claude --add-dir ../shared-lib --add-dir ../docs
```

### Environment Variables

Set environment variables for the session:

```bash
# Via settings file
claude --settings '{"env":{"DEBUG":"true","NODE_ENV":"development"}}'
```

### Permission Modes

Start in specific permission mode:

```bash
# Plan mode (requires approval)
claude --permission-mode plan

# Accept edits mode (auto-accept file edits)
claude --permission-mode acceptEdits

# Bypass permissions (dangerous)
claude --dangerously-skip-permissions
```

### Allowed Tools

Specify tools that execute without permission:

```bash
claude --allowedTools "Bash(git log *)" "Bash(git diff *)" "Read"
```

### Restricted Tools

Limit available tools:

```bash
# Only specific tools
claude --tools "Read,Edit,Bash"

# No tools (disable all)
claude --tools ""

# All tools (default)
claude --tools "default"
```

### Disallowed Tools

Block specific tools:

```bash
claude --disallowedTools "WebFetch" "Bash(rm *)"
```

## System Prompt Customization

### Replace System Prompt

```bash
# Replace entire prompt
claude --system-prompt "You are a Python expert who only writes type-annotated code"

# From file
claude -p --system-prompt-file ./custom-prompt.txt "Query"
```

### Append to System Prompt

```bash
# Append text (preserves Claude Code instructions)
claude --append-system-prompt "Always use TypeScript and include JSDoc comments"

# Append from file
claude -p --append-system-prompt-file ./extra-rules.txt "Query"
```

### Recommended: Use Append for PM Work

When delegating to developer agents, use append to add requirements while keeping Claude Code's built-in capabilities:

```bash
claude -p \
  --append-system-prompt "Follow the project's Python standards in .github/instructions/python_standard.instructions.md. Use the issue-fixer skill for all bug fixes." \
  "Fix the authentication bug"
```

## MCP (Model Context Protocol) Servers

### Load MCP Config

```bash
# From file
claude --mcp-config ./mcp.json

# Multiple configs
claude --mcp-config ./mcp-base.json ./mcp-extra.json

# Strict mode (only use specified MCP servers)
claude --strict-mcp-config --mcp-config ./mcp.json
```

### MCP Config Format

```json
{
  "mcpServers": {
    "filesystem": {
      "command": "npx",
      "args": ["-y", "@modelcontextprotocol/server-filesystem", "/path/to/directory"]
    },
    "github": {
      "command": "npx",
      "args": ["-y", "@modelcontextprotocol/server-github"]
    }
  }
}
```

## Session Management

### Session ID

Use specific session ID:

```bash
claude --session-id "550e8400-e29b-41d4-a716-446655440000"
```

### Fork Session

Create new session ID when resuming:

```bash
claude --resume abc123 --fork-session
```

### From Pull Request

Resume sessions from GitHub PR:

```bash
# By PR number
claude --from-pr 123

# By PR URL
claude --from-pr https://github.com/owner/repo/pull/123
```

## Model Selection

### Specify Model

```bash
# Use model alias
claude --model sonnet
claude --model opus
claude --model haiku

# Use full model name
claude --model claude-sonnet-4-5-20250929
```

### Fallback Model

Auto-fallback if primary model is overloaded (print mode only):

```bash
claude -p --fallback-model sonnet "Query"
```

## Output Formats

### Text (Default)

```bash
claude -p "Explain this code"
# Output: plain text response
```

### JSON

```bash
claude -p --output-format json "Explain this code"
```

Output structure:

```json
{
  "success": true,
  "result": "...",
  "sessionId": "...",
  "usage": {
    "inputTokens": 1234,
    "outputTokens": 567
  }
}
```

### Streaming JSON

```bash
claude -p --output-format stream-json "Implement feature"
```

Outputs newline-delimited JSON events:

```json
{"type":"start","sessionId":"..."}
{"type":"content","text":"First, I'll..."}
{"type":"tool","tool":"Read","args":{...}}
{"type":"content","text":"Next..."}
{"type":"end","success":true}
```

### Include Partial Messages

Include streaming partial messages:

```bash
claude -p --output-format stream-json --include-partial-messages "Query"
```

## Structured Outputs

### JSON Schema Validation

Get validated JSON output matching a schema (print mode only):

```bash
claude -p --json-schema '{
  "type": "object",
  "properties": {
    "summary": {"type": "string"},
    "issues": {
      "type": "array",
      "items": {
        "type": "object",
        "properties": {
          "file": {"type": "string"},
          "line": {"type": "number"},
          "description": {"type": "string"}
        }
      }
    }
  },
  "required": ["summary", "issues"]
}' "Analyze code for security issues"
```

## Debugging & Verbose Mode

### Enable Debug Mode

```bash
# All debug output
claude --debug

# Specific categories
claude --debug "api,hooks"

# Exclude categories
claude --debug "!statsig,!file"
```

### Verbose Mode

Show full turn-by-turn output:

```bash
claude --verbose -p "Complex task"
```

## Plugin Management

### Load Plugins from Directory

```bash
claude --plugin-dir ./my-plugins --plugin-dir ./more-plugins
```

## Hooks & Lifecycle

### Run Initialization Hooks

```bash
# Init and start interactive
claude --init

# Init only (no interactive session)
claude --init-only
```

### Run Maintenance Hooks

```bash
claude --maintenance
```

## Chrome Integration

### Enable Chrome for Web Automation

```bash
claude --chrome
```

### Disable Chrome

```bash
claude --no-chrome
```

## Beta Features

### Enable Beta Headers

```bash
claude --betas interleaved-thinking
```

## Common PM Workflows

### Workflow 1: Simple Bug Fix

```bash
cd /path/to/workspace

claude -p \
  --settings .claude/settings.json \
  --append-system-prompt "Use issue-fixer skill. Fix only the specific bug, no other changes." \
  --max-turns 10 \
  --output-format json \
  "Fix the login button not responding issue"
```

### Workflow 2: Feature with Custom Agent

```bash
cd /path/to/workspace

# Define agent
AGENT_CONFIG='{
  "feature-dev": {
    "description": "Senior developer for feature implementation",
    "prompt": "You are a senior developer. Implement features following project standards and best practices. Use tests to validate your work.",
    "skills": ["testing", "code-quality"],
    "tools": ["Read", "Edit", "Write", "Bash", "Grep", "Glob"],
    "model": "sonnet",
    "maxTurns": 20
  }
}'

# Execute
claude -p \
  --agents "$AGENT_CONFIG" \
  --agent feature-dev \
  --append-system-prompt "$(cat requirements/dark-mode.md)" \
  --max-turns 20 \
  --output-format json \
  "Implement dark mode feature per requirements document"
```

### Workflow 3: Multi-Phase Development

```bash
cd /path/to/workspace

# Phase 1: Design
claude -p \
  --agents '{"architect":{"description":"System architect","prompt":"Design scalable systems","model":"opus"}}' \
  --agent architect \
  --max-turns 5 \
  --output-format json \
  "Design authentication system architecture" > design-output.json

# Phase 2: Implementation
claude -p \
  --agents '{"developer":{"description":"Senior developer","prompt":"Implement per design","model":"sonnet"}}' \
  --agent developer \
  --append-system-prompt "Implement the design from docs/auth-design.md" \
  --max-turns 15 \
  --output-format json \
  "Implement authentication system" > implementation-output.json

# Phase 3: QA
claude -p \
  --agents '{"qa":{"description":"QA engineer","prompt":"Test thoroughly","model":"sonnet"}}' \
  --agent qa \
  --max-turns 5 \
  --output-format json \
  "Review and test authentication implementation. Run all tests." > qa-output.json
```

### Workflow 4: With Budget Control

```bash
claude -p \
  --max-budget-usd 3.00 \
  --max-turns 15 \
  --output-format json \
  --append-system-prompt "Be efficient. Fix only the reported bug." \
  "Fix memory leak in data processing pipeline"
```

### Workflow 5: With Additional Context

```bash
# Give access to shared libraries
claude -p \
  --add-dir ../shared-utils \
  --add-dir ../common-types \
  --append-system-prompt "Use shared utilities from ../shared-utils when applicable" \
  "Refactor user service to use shared utilities"
```

### Workflow 6: Parsing Output

```bash
# Capture and parse JSON output
OUTPUT=$(claude -p --output-format json "List all TODO comments in the code")

# Extract result
echo "$OUTPUT" | jq -r '.result'

# Check success
echo "$OUTPUT" | jq -r '.success'

# Get usage stats
echo "$OUTPUT" | jq '.usage'
```

### Workflow 7: Streaming with Progress Monitoring

```bash
# Stream output and monitor progress
claude -p --output-format stream-json "Implement feature" | while IFS= read -r line; do
  TYPE=$(echo "$line" | jq -r '.type')
  case "$TYPE" in
    "content")
      echo "📝 $(echo "$line" | jq -r '.text')"
      ;;
    "tool")
      TOOL=$(echo "$line" | jq -r '.tool')
      echo "🔧 Using tool: $TOOL"
      ;;
    "end")
      SUCCESS=$(echo "$line" | jq -r '.success')
      if [ "$SUCCESS" = "true" ]; then
        echo "✅ Task completed successfully"
      else
        echo "❌ Task failed"
      fi
      ;;
  esac
done
```

## Environment Variables

Key environment variables for PM automation:

```bash
# Enable tasks/todo system
export CLAUDE_CODE_ENABLE_TASKS=true

# Set effort level
export CLAUDE_CODE_EFFORT_LEVEL=high  # low, medium, high

# Disable non-essential features
export CLAUDE_CODE_DISABLE_NONESSENTIAL_TRAFFIC=1

# Custom temp directory
export CLAUDE_CODE_TMPDIR=/custom/tmp

# Auto-exit after idle
export CLAUDE_CODE_EXIT_AFTER_STOP_DELAY=5000  # milliseconds
```

## Tips for PM Agents

1. **Always use `--output-format json`** for programmatic workflows
2. **Set `--max-turns`** to prevent runaway executions
3. **Use `--append-system-prompt`** to add requirements without losing Claude Code capabilities
4. **Monitor output** for errors and tool calls
5. **Use verbose mode** (`--verbose`) when debugging
6. **Set budget limits** (`--max-budget-usd`) for cost control
7. **Save session IDs** for resuming if needed
8. **Parse JSON output** with `jq` for automation
9. **Use custom agents** for specialized tasks
10. **Combine settings files** with CLI flags for flexibility

## Error Handling

### Check Exit Codes

```bash
claude -p "Task" --output-format json
EXIT_CODE=$?

if [ $EXIT_CODE -eq 0 ]; then
  echo "Success"
else
  echo "Failed with exit code: $EXIT_CODE"
fi
```

### Handle Timeouts

```bash
# Set timeout with timeout command
timeout 300 claude -p --max-turns 10 "Task"
if [ $? -eq 124 ]; then
  echo "Task timed out after 5 minutes"
fi
```

### Retry Logic

```bash
MAX_RETRIES=3
RETRY_COUNT=0

while [ $RETRY_COUNT -lt $MAX_RETRIES ]; do
  claude -p "Task" --output-format json > output.json
  if [ $? -eq 0 ]; then
    echo "Success"
    break
  fi
  RETRY_COUNT=$((RETRY_COUNT + 1))
  echo "Retry $RETRY_COUNT/$MAX_RETRIES"
  sleep 5
done
```

## Quick Reference

### Essential Flags for PM

| Flag | Purpose | Example |
|------|---------|---------|
| `-p` | Print mode (automation) | `claude -p "task"` |
| `--output-format json` | JSON output | `claude -p --output-format json "task"` |
| `--max-turns 10` | Limit turns | `claude -p --max-turns 10 "task"` |
| `--append-system-prompt` | Add instructions | `claude -p --append-system-prompt "Use skill X" "task"` |
| `--agents` | Define custom agents | `claude --agents '{"dev":{...}}'` |
| `--settings` | Load settings | `claude --settings settings.json` |
| `--verbose` | Debug output | `claude -p --verbose "task"` |
| `--max-budget-usd` | Cost limit | `claude -p --max-budget-usd 5 "task"` |

### Essential Commands for PM

```bash
# Simple task
claude -p --output-format json "task"

# With custom agent
claude -p --agents '{...}' --agent dev "task"

# With requirements
claude -p --append-system-prompt "$(cat requirements.md)" "task"

# With settings and limits
claude -p --settings settings.json --max-turns 10 --max-budget-usd 5 "task"

# Full control
claude -p \
  --agents '{"dev":{...}}' \
  --agent dev \
  --settings settings.json \
  --append-system-prompt "instructions" \
  --max-turns 15 \
  --max-budget-usd 10 \
  --output-format json \
  --verbose \
  "task"
```

---

**For full documentation**: https://code.claude.com/docs/en/cli-reference
