# Helper Scripts

Automation scripts for common claude-code-pm operations.

## Available Scripts

### setup.sh
Setup OpenSpec and install skills for a workspace.

**Usage:**
```bash
scripts/setup.sh <workspace-path> [skill1] [skill2] ...
```

**Examples:**
```bash
# Setup in current directory with API skills
scripts/setup.sh . api-development test-automation

# Setup in another workspace with debugging skills
scripts/setup.sh ~/projects/myapp debugging test-automation
```

---

### delegate.sh
Start Claude Code in background for a change.

**Usage:**
```bash
scripts/delegate.sh <change-name> [max-turns] [workspace-path]
```

**Examples:**
```bash
# Start with defaults (50 turns, current dir)
scripts/delegate.sh user-profile-api

# Start with custom turns
scripts/delegate.sh fix-login-bug 30

# Start in different workspace
scripts/delegate.sh add-dark-mode 40 ~/projects/webapp
```

**What it does:**
- Starts Claude Code in background
- Saves PID to `.claude_<change-name>.pid`
- Redirects output to `<change-name>.jsonl`
- Shows initial output and monitoring commands

---

### monitor.sh
Check status and recent output of a running change.

**Usage:**
```bash
scripts/monitor.sh <change-name> [lines]
```

**Examples:**
```bash
# Show last 20 lines (default)
scripts/monitor.sh user-profile-api

# Show last 50 lines
scripts/monitor.sh user-profile-api 50
```

**What it shows:**
- Process status (running/stopped)
- Elapsed time
- Recent output lines
- Error count and recent errors
- Task progress from tasks.md

---

### check-completion.sh
Validate completion and readiness for archive.

**Usage:**
```bash
scripts/check-completion.sh <change-name>
```

**Examples:**
```bash
scripts/check-completion.sh user-profile-api
```

**What it checks:**
- Process status
- Output file size and errors
- OpenSpec artifacts existence
- Task completion percentage
- Readiness for archive

**Output:**
- ✅ All complete → Ready for archive
- ⏸️ Incomplete tasks → Shows what's left
- ❌ Issues found → Shows errors

---

## Typical Workflow

```bash
# 1. Setup workspace
cd ~/projects/myapp
scripts/setup.sh . api-development test-automation

# 2. Create requirements.md with your requirements

# 3. Delegate
scripts/delegate.sh user-profile-api 50

# 4. Monitor (optional, while running)
scripts/monitor.sh user-profile-api

# 5. Check completion
scripts/check-completion.sh user-profile-api

# 6. Archive (when complete)
claude -p --dangerously-skip-permissions "/opsx:archive user-profile-api"
```

---

## Environment Requirements

These scripts require:
- `bash` 4.0+
- `claude` CLI installed
- `openspec` CLI installed
- `npx` (Node.js) for skills installation
- Standard Unix tools: `ps`, `grep`, `tail`, `wc`

## Permissions

All scripts have execute permissions. If needed:
```bash
chmod +x scripts/*.sh
```
