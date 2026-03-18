---
name: chat-analyzer
description: >
  Analyze SpecStory chat history exports to identify problems, friction points,
  and areas needing improvement. This skill should be used when the user wants
  to understand what went wrong in their agent interactions. Use when the user
  asks to "analyze chat history", "what went wrong", "review agent sessions",
  or "find problems in conversations".
---

# Chat Analyzer

Analyze SpecStory chat history exports and produce a detailed analysis report
with actionable fixes for agent constitution files (AGENTS.md, CLAUDE.md, etc.).

## Quick Start

```bash
# Get full analysis report (main output)
python3 chat_analyze.py analyze data/history.md

# Get problems checklist
python3 chat_analyze.py problems data/history.md

# Supporting commands for deep-dive
python3 chat_analyze.py stats   data/history.md
python3 chat_analyze.py toc     data/history.md
python3 chat_analyze.py tools   data/history.md
python3 chat_analyze.py show    data/history.md <LINE>
python3 chat_analyze.py grep    data/history.md "<pattern>"
```

## Output Format

The `analyze` command produces a comprehensive report:

```
# Chat History Analysis: [filename]

## Summary
- Sessions: N
- Messages: N
- Tool calls: N
- Estimated tokens: Nk
- Dominant tool mix: tool1 N, tool2 N, tool3 N
- High-risk indicators: secret exposure, scope drift, restart loops

## Primary Findings

### 1. Secret Exposure In Chat
Severity: high
Evidence: [specific line numbers with credentials]
Pattern: [what went wrong]
Impact: [consequences]
Recommended fix: [concrete actions]

### 2. Scope Drift Across Major Sessions
...

### 3. Environment Churn And Restart Loops
...

## Session-By-Session Breakdown

### Session at line N: [title]
- Shape: N messages, N tool calls.
- Issue: [problems detected]
- Pattern: [behavioral pattern]
- Better split: [recommendation]

## Recommended Conversation Policy Changes
1. [Specific policy recommendation]
2. [Specific policy recommendation]
...
```

## Problem Detection

The analyzer detects these high-value patterns:

### Critical Issues (High Severity)
| Pattern | Detection | Impact |
|---------|-----------|--------|
| Secret exposure | Database URLs, API keys, passwords, tokens in chat | Credentials compromised, export file becomes sensitive |
| Scope drift | Session topic changes significantly from original request | Acceptance criteria unclear, test results unreliable |
| Infrastructure failure | API errors, model config errors, network failures | Sessions blocked entirely, no deliverable output |

### Code Quality Issues (Medium Severity)
| Pattern | Detection | Impact |
|---------|-----------|--------|
| Buggy code | Multiple debugging iterations, "still broken", visual bugs | Extended session time, user has to report and wait for fixes |
| User frustration | User says "no", "wrong", "try again", "not what I wanted" | Wasted effort, unclear requirements |

### Environment Issues (Medium Severity)
| Pattern | Detection | Impact |
|---------|-----------|--------|
| Restart loops | Repeated startup/restart commands across sessions | Slow feedback, unclear baseline, stale processes |
| Skill config issues | Missing SKILL.md, Python environment problems, skill format errors | Skills unusable until fixed, added friction |

### Session Issues (Low Severity)
| Pattern | Detection | Impact |
|---------|-----------|--------|
| Session bloat | >25 messages in single session | Context accumulation, hard to track progress |
| Incomplete session | Session ends with TODO/FIXME/WIP | Work not finished, unclear completion |

## Secret Detection Patterns

The analyzer detects:
- Database connection strings (mysql://, postgres://, mongodb://, redis://)
- API keys and secrets (api_key, secret_key, API_SECRET)
- Passwords in configuration
- Bearer tokens and auth tokens
- AWS access keys
- OpenAI-style keys (sk-*)
- Slack tokens (xoxb-, xoxp-)

## Scope Drift Detection

Sessions are analyzed for topic changes:
- authentication -> frontend
- requirements -> implementation
- feature work -> deployment
- development -> debugging

When the first quarter of a session focuses on one topic but the last quarter focuses on a different topic, scope drift is flagged.

## Restart Loop Detection

Detects patterns like:
- restart server/service commands
- npm start, flask run, uvicorn
- port occupation issues
- kill/stop process commands
- Multiple restart attempts in a session or across adjacent sessions

## Buggy Code Detection

Detects iterative debugging patterns:
- "still not working", "still broken", "still frozen", "still invisible"
- "now it's broken", "now the UI is bugged"
- "same error again", "still getting the same error"
- "another bug", "more issues"
- Visual bugs: "invisible lawn", "frozen zombie", "invisible element"

When 2+ debugging patterns appear in a session, it indicates buggy initial implementation.

## Infrastructure Failure Detection

Detects technical failures that block progress:
- Invalid model configuration errors
- API HTTP errors (404, 500, rate limits)
- Network errors (connection refused, timeout, DNS errors)

These failures often block sessions entirely with no deliverable output.

## Skill Configuration Issue Detection

Detects problems with skills and tools:
- Missing SKILL.md files
- Skill not found or configuration errors
- Skill format errors
- Suggestions to use Bash instead of Python

## CLI Reference

```
python3 chat_analyze.py <command> [FILE] [OPTIONS]
```

| Command | What it returns |
|---------|-----------------|
| `analyze [FILE]` | Full analysis report with session breakdown |
| `problems [FILE]` | Checklist of problems with fixes |
| `stats [FILE]` | Counts: sessions, messages, tools, tokens |
| `toc [FILE]` | Table of contents with line numbers |
| `show [FILE] LINE` | ±15 lines around LINE |
| `grep [FILE] PAT` | Regex search with line numbers |
| `tools [FILE]` | All tool calls with line numbers |
| `think [FILE]` | All think blocks with line numbers |
| `const [DIR]` | Find AGENTS.md, CLAUDE.md, etc. |

## Analysis Workflow

1. **Run `analyze` first** - get the comprehensive report
2. **Review Primary Findings** - understand severity and evidence
3. **Drill into specific sessions** - use `show` with line numbers from output
4. **Locate spec files** - use `const` to find AGENTS.md
5. **Apply policy changes** - add specific rules to constitution files

## What NOT to Output

- Generic suggestions ("improve communication")
- Praise for what worked
- "On the horizon" futuristic ideas
- Vague recommendations without line references
- Tool usage rates as problems (reading files frequently is normal)

## Example Output

```
# Chat History Analysis: history.md

## Summary

- Sessions: 22
- Messages: 132
- Tool calls: 920
- Estimated tokens: 266k
- Dominant tool mix: write 292, read 288, shell 186
- High-risk indicators: secret exposure, repeated restart loops, scope drift

The chat is not mainly failing because of one bad answer. It is failing because
analysis, implementation, debugging, environment repair, deployment, and
configuration handling were allowed to accumulate in the same long-running thread.

## Primary Findings

### 1. Secret Exposure In Chat

Severity: high

Evidence:
- `mysql+pymysql://...` appears at source lines 19179, 19938, 20066.
- API secret material appears at source lines 22934, 22945.

Pattern:
The conversation used the chat log itself as a transport for runtime credentials.

Impact:
- anyone with the export can recover live credentials,
- analysis outputs become unsafe to share.

Recommended fix:
- redact all credentials in conversation,
- rotate the leaked credentials,
- add a hard rule that the agent must never repeat pasted secrets back verbatim.

### 2. Scope Drift Across Major Sessions

Severity: high

Evidence:
- The session starting at source line 9587 begins as requirement decomposition.
- That same thread later shifts into frontend implementation at source line 14691.

Pattern:
The thread keeps carrying forward prior context instead of re-establishing a clean goal.

Recommended fix:
- enforce one major objective per thread,
- require explicit re-scoping when the task changes domain.

## Session-By-Session Breakdown

### Session at line 5: Project scaffold initialization
- Shape: 8 messages, 132 tool calls.
- Issue: heavy write volume early suggests large scaffold generation.
- Pattern: session focused on setup.
- Better split: consider breaking into smaller initialization steps.

### Session at line 9585: System module decomposition
- Shape: 24 messages, 223 tool calls.
- Issue: scope drift from requirements to implementation.
- Pattern: session started with requirements, drifted to frontend work.
- Better split: separate requirements analysis from implementation.

## Recommended Conversation Policy Changes

1. Do not allow secrets in chat. Redirect them to a secure local env file immediately.
2. Cap major sessions by objective, not by elapsed time.
3. Require a scope-reset sentence when the request switches domain.
4. Replace repeated startup replies with one canonical runbook.
```