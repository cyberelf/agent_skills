---
name: chat-analyzer
description: >
  Analyze SpecStory chat history exports to identify workflow patterns,
  inefficiencies, and produce actionable suggestions for improving AGENTS.md,
  constitution files, and any spec/constraint documents. Uses a companion CLI
  script (chat_analyze.py) to navigate large files efficiently without reading
  them whole — essential for keeping context size manageable.
---

# Chat Analyzer Skill

Analyze SpecStory (or compatible) chat history exports and produce concrete
improvement suggestions for agent constitution files (AGENTS.md, CLAUDE.md,
.cursorrules, OpenSpec, etc.).

## The Core Problem

Chat history files are large (10k–100k+ lines). Reading them wholesale burns
context. Instead, use the **chat_analyze.py** CLI to get a lightweight map of
the file, then drill into specific areas with targeted reads.

## CLI Reference

The CLI lives at `<chat_ana_dir>/chat_analyze.py`.  All commands accept a
file path or default to the first `.md` in `./data/`.

```
python3 chat_analyze.py <command> [FILE] [OPTIONS]
```

| Command            | What it returns                                             |
|--------------------|-------------------------------------------------------------|
| `stats [FILE]`     | Counts: sessions, messages, tool calls (by type+name), tokens |
| `toc [FILE]`       | Flat TOC: session titles + user/agent lines with line numbers |
| `show [FILE] LINE` | ±15 lines around LINE (use `--context N` to change window)  |
| `grep [FILE] PAT`  | Regex search → all matching lines with numbers              |
| `tools [FILE]`     | Every tool call: line number, type, tool name               |
| `think [FILE]`     | Every think block: start/end line + first line of content   |
| `const [DIR]`      | Finds AGENTS.md, CLAUDE.md, .cursorrules, OpenSpec, etc.    |
| `suggest [FILE]`   | Automated hints → which AGENTS.md areas to improve         |

### Typical analysis workflow

```bash
# Step 1 — get the lay of the land (cheap, ~1000 tokens)
python3 chat_analyze.py stats  data/history.md
python3 chat_analyze.py toc    data/history.md

# Step 2 — drill into a session of interest  (line from toc output)
python3 chat_analyze.py show   data/history.md 9587 --context 30

# Step 3 — find all uses of a specific tool or keyword
python3 chat_analyze.py tools  data/history.md | grep edit_file
python3 chat_analyze.py grep   data/history.md "AGENTS\.md"

# Step 4 — locate constitution files in the target project
python3 chat_analyze.py const  /path/to/project

# Step 5 — get automated suggestions
python3 chat_analyze.py suggest data/history.md
```

For exact line ranges use the shell directly:
```bash
sed -n '9585,9700p' data/history.md
```

## Analysis Methodology

### Phase 1 — Structural scan (always start here)

Run `stats` and `toc`. Look for:

- **sessions**: how many independent tasks were performed?
- **think_blocks / agent_messages** ratio: >2 means unclear instructions
- **tool_type breakdown**: imbalanced write/read/shell ratios
- **Top tool names**: which tools are called most — are there repeated patterns?
- **Session breakdown table**: which sessions are long (many messages or tool calls)?

### Phase 2 — Deep-dive into problem sessions

For sessions with many messages (>20) or tool calls (>100):
1. `show FILE <session_start_line>` — read the user request
2. `show FILE <agent_line>` — read the agent's first think block
3. `tools FILE | grep <line_range>` — list all tools used in that session
4. `sed -n 'START,ENDp' FILE` — read a contiguous block if needed

### Phase 3 — Identify patterns

| Pattern | What to look for | Likely AGENTS.md fix |
|---------|-----------------|---------------------|
| Repeated reads | `tools` output shows same file read 5+ times | Add "read once" policy |
| Long think blocks | `think` shows many >50-line blocks | Clarify decision rules in spec |
| Shell dominance | `stats` shows shell >40% of tool calls | Add allowed-commands list |
| Write dominance | `stats` shows write >35% | Add file hygiene policy |
| Missing bootstrap reads | `tools` first 10 lines have no `read` | Add "read AGENTS.md first" rule |
| Session sprawl | TOC shows sessions with >30 messages | Add task-size rule |
| Unknown tool type | `tools` shows `unknown` type frequently | Check tool registration config |

### Phase 4 — Locate and improve spec files

```bash
python3 chat_analyze.py const /path/to/project
```

Then read the relevant sections:
```bash
# Read first 100 lines of AGENTS.md
head -100 /path/to/project/AGENTS.md

# Find what's already covered
grep -n "^##" /path/to/project/AGENTS.md
```

### Phase 5 — Draft improvements

Based on the patterns, propose specific additions/changes.  Follow these rules:
- **Be surgical**: add the minimum text needed to address the pattern
- **Use examples**: bad examples are more memorable than abstract rules
- **Link to evidence**: cite session line numbers (e.g. "see line 9587")
- **Avoid duplication**: always `grep` before adding new rules

## Improvement Categories

### 1. Context bootstrapping
Add to AGENTS.md if missing:
```markdown
## Task Start Checklist
1. Read AGENTS.md (this file) and relevant spec files
2. Run `python3 chat_analyze.py stats data/latest.md` to orient yourself
3. Identify the task type and applicable constraints before taking any action
```

### 2. Tool use policies
Common additions to reduce repeated reads and shell sprawl:
```markdown
## Tool Use Rules
- **Read once**: cache file contents in your working memory; do not re-read unless the file has changed
- **Shell safety**: only run commands explicitly approved in the task description; never use `rm -rf`, `sudo`, or pipeline chains >3 stages without approval
- **Write batching**: collect all edits before writing; prefer a single multi-edit call over multiple single-line writes
```

### 3. Task scoping
Add when sessions run long:
```markdown
## Task Size Limit
- If a task requires >15 tool calls to complete, pause and ask the user to confirm scope
- Break tasks into sub-tasks with acceptance criteria before starting
```

### 4. File hygiene
Add when write ratio is high:
```markdown
## File Management
- Temp files: use `tmp_<task_id>_<name>` naming; delete after task
- Never create files outside the project root without explicit approval
- Log all new files created in the session summary
```

### 5. Decision rules
Add when think ratio is high (agent deliberates excessively):
```markdown
## Decision Framework
When in doubt about approach:
1. Re-read the relevant spec section
2. Choose the option least likely to require reverting
3. If still unclear, ask the user — a 30-second question beats a 10-minute wrong path
```

## Output Format

When reporting analysis results, use this structure:

```markdown
## Chat History Analysis: <filename>

### Summary
- Sessions: N, Messages: N, Tool calls: N, Est. tokens: Nk
- Key sessions: [line: title, ...]

### Issues Found
1. **<issue title>** (severity: high/medium/low)
   - Evidence: line NNN — <describe what's there>
   - Pattern: <what it means>
   - Fix: <specific text to add/change in AGENTS.md>

### Suggested AGENTS.md Changes
<diff-style or prose description of changes>

### Spec Files Checked
- <path> — <current coverage gaps>
```

## Important Notes

- **Never read the full chat file** if it's >5000 lines — always navigate with the CLI first
- The CLI companion script must exist at `<project>/chat_analyze.py` — if missing, instructions for creating it are at `<chat_ana_dir>/chat_analyze.py`
- For cross-file analysis (comparing two chat histories), run `stats` and `suggest` on each and diff the output
- The CLI uses `python3` — ensure it's available in the shell before running
