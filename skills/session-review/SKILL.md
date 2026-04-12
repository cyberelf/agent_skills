---
name: session-review
description: >
  Multi-session AI coding history analysis across Copilot CLI,
  Claude Code, and VS Code sessions for a project. Collects raw logs,
  normalizes them into a unified format, and produces an actionable report
  covering recurring bugs, tool-error patterns, missing tests, refactoring
  opportunities, process improvements, and documentation gaps. Supports
  incremental analysis — only new sessions are processed on repeat runs, with
  persistent storage at ~/.retro/<project>/. Use this skill whenever the user
  asks to review, analyze, or get a retrospective on AI coding sessions, chat
  history, agent logs, copilot sessions, what went wrong across sessions, what
  patterns the AI made, or wants a report on how the AI performed on a project.
  Also trigger for phrases like "look at my sessions", "analyze my chat history",
  "what bugs recurred", "review my AI sessions", or "how has the AI been doing".
metadata:
  author: cyberelf
  version: "1.2"
  scripts_dir: scripts/   # all scripts are bundled here — no external dependencies
---

# Session Review Skill

You are performing a cross-session AI assistant analysis for a software project.
The scripts you need are bundled alongside this SKILL.md in `scripts/`.

```
~/.claude/skills/session-review/
├── SKILL.md          ← you are here
└── scripts/
    ├── retro.ts      ← orchestrator (run this)
    ├── get_hist.ts   ← raw session collector
    └── normalize_hist.ts ← normalizer
```

Set `SKILL_SCRIPTS="$HOME/.claude/skills/session-review/scripts"` at the start of any bash
commands you run, so you can refer to scripts as `$SKILL_SCRIPTS/retro.ts`.

Follow each phase in order. Do not skip phases.

---

## Phase 0 — Determine the project

1. If the user invoked this skill with an argument (e.g. `/session-review ~/workspace/crab`),
   use that path as `PROJECT_PATH`.
2. Otherwise check the current working directory: if it has `Cargo.toml`, `package.json`,
   `src/`, or similar project markers, use `$PWD`.
3. If still ambiguous, ask: "Which project path should I analyze?"

`PROJECT_NAME` is the directory's basename. Storage lives at `~/.retro/<PROJECT_NAME>/`.

---

## Phase 1 — Collect and normalize (the pipeline)

```bash
SKILL_SCRIPTS="$HOME/.claude/skills/session-review/scripts"
npx tsx "$SKILL_SCRIPTS/retro.ts" "$PROJECT_PATH" run
```

This runs two steps automatically:
- **collect** — `get_hist.ts` copies raw sessions from Copilot CLI
  (`~/.copilot/session-state`), Claude Code (`~/.claude/projects/`), and VS Code to
  `~/.retro/<PROJECT_NAME>/raw/`
- **normalize** — `normalize_hist.ts --incremental` converts sessions to unified
  Markdown in `~/.retro/<PROJECT_NAME>/normalized/`

On the first run, all sessions are collected. On subsequent runs, only sessions newer
than `lastCollectedAt` in the manifest are added.

If the user wants a **full re-analysis from scratch**, add `--full`:
```bash
npx tsx "$SKILL_SCRIPTS/retro.ts" "$PROJECT_PATH" run --full
```

If the pipeline exits non-zero, read its stderr to diagnose before continuing.

Check progress anytime:
```bash
npx tsx "$SKILL_SCRIPTS/retro.ts" "$PROJECT_PATH" status
```

---

## Phase 2 — Orient: read the index

Read `~/.retro/<PROJECT_NAME>/normalized/index.json`.

From the `sessions` array, compute:
- Total sessions, date range (first and last `timestamp`)
- Source breakdown (`copilot-cli`, `claude-code`, `vscode`)
- Total tool calls: sum of `toolCallCount`
- Total errors: sum of `errorCount`
- Top 5 sessions by `errorCount` (ID, date, count)

Print a brief summary:
```
Sessions: N  •  Date range: YYYY-MM-DD – YYYY-MM-DD
Sources: copilot-cli(N)  claude-code(N)  vscode(N)
Tool calls: N  •  Errors: N
Top error sessions: [list]
```

---

## Phase 3 — Deep read: strategic sampling

Do **not** read `combined.md` in full — it will overflow context. Read individual
session `.md` files from `~/.retro/<PROJECT_NAME>/normalized/sessions/`.

**Sampling order:**
1. The 5 sessions with the highest `errorCount`
2. The 5 most recent sessions by `timestamp`
3. The 2 oldest sessions (detect long-standing patterns)
4. 3 sessions evenly spread across the date range

If total session count ≤ 15, read them all.

For each session note:
- What the user was trying to accomplish (first user message)
- Which tools were called most often
- What errors occurred and whether they repeat across sessions
- Explicit user corrections ("no, don't", "this is wrong", "stop X")
- Tasks marked done before they were actually tested or verified

---

## Phase 4 — Read project context

If present, read these files (they're essential for judging whether a pattern is
a known limitation vs. an actionable gap):
- `<PROJECT_PATH>/AGENTS.md` — coding agent instructions (highest priority)
- `<PROJECT_PATH>/ARCHITECTURE.md`
- `<PROJECT_PATH>/README.md` (first 80 lines only)
- `<PROJECT_PATH>/openspec/changes/` directory listing (if it exists)

---

## Phase 5 — Write the report

Write to:
```
~/.retro/<PROJECT_NAME>/reports/<YYYY-MM-DD>-report.md
```
Also write/overwrite `~/.retro/<PROJECT_NAME>/reports/latest-report.md` with the same
content. Create the `reports/` directory if it doesn't exist.

After writing, update the manifest's `lastReportAt` by editing the file directly:
```
~/.retro/<PROJECT_NAME>/manifest.json
```

### Report template

Use this structure exactly. Omit sections with no findings.

```markdown
# <PROJECT_NAME> — Session Analysis Report

**Period:** <first-date> – <last-date>
**Sessions analyzed:** N (M tool calls · K errors)
**Sources:** <breakdown>

---

## Executive Summary

<3–5 sentences. Lead with P0 issues. Be specific — name files and functions.>

---

## 1. Recurring Bugs — Demand Regression Tests

### 1.N <Short title>

Observed in sessions **<dates>**. <What happened, root cause if known.>

**Action:** <File path + what the test should assert.>

---

## 2. Critical Unresolved Issues (open as of <last-date>)

### 2.N <Short title>  *(P0|P1)*

> "<Exact quote from session showing the problem>"

<Root cause.>

**Action:**
1. <File and function to change.>
2. <Test to add.>

---

## 3. Tool Error Tax — Documentation-Preventable Failures

| Category | Count | Root cause |
|---|---|---|

Add to AGENTS.md under **"Known Tool Behavior"**:
\`\`\`markdown
### <tool>
<guidance>
\`\`\`

---

## 4. Code Refactoring

### 4.N <Title>  *(P1|P2)*

<Which files, what to change, step-by-step if non-trivial.>

---

## 5. Missing Tests — Specific Gaps

| File | Missing test |
|---|---|

---

## 6. Process Improvements

### 6.N <Title>

**Add to AGENTS.md `## <Section>`:**
> <Exact text to add>

---

## 7. Documentation Updates Required

<AGENTS.md, ARCHITECTURE.md, README — specific sections and what to add.>

---

## 8. OpenSpec Gaps

<Specs that should exist but don't, or specs needing updates.>

---

## Priority Summary

| Priority | Item | Owner area |
|---|---|---|
| **P0** | ... | ... |
| **P1** | ... | ... |
| **P2** | ... | ... |
| **P3** | ... | ... |
```

---

## Phase 6 — Storage management

After writing the report, tell the user:
- Report location: `~/.retro/<PROJECT_NAME>/reports/<date>-report.md`
- To re-run incrementally next time: `/session-review <project-path>`
- Storage usage: `npx tsx "$SKILL_SCRIPTS/retro.ts" <project-path> status`
- To free space (raw data is safe to delete after normalizing):
  ```bash
  npx tsx "$SKILL_SCRIPTS/retro.ts" <project-path> cleanup --clean=raw
  ```
  Options: `--clean=raw` (largest), `--clean=normalized`, `--clean=reports`, `--clean=all`

---

## Analysis rules

These exist so the report is trustworthy and actionable, not just voluminous.

- **Never fabricate.** Every claim must come from a session you actually read.
- **Name files and functions.** "Add more tests" is useless. "Add a test in
  `crab-agents/src/system_agent.rs` asserting that `agent_send_message` returns an
  error when `sender_id == receiver_id`" is actionable.
- **Quote the session.** For critical bugs include a short direct quote.
- **Distinguish recurrence from first occurrence.** One session = finding. Three or
  more sessions across weeks = systemic gap requiring a process fix.
- **Tool errors need root cause.** "grep exits 1 on no match" is a misuse pattern
  preventable by documentation. "Network timeout" is environment noise. Treat them
  differently.
- **Cross-reference project docs.** If AGENTS.md already covers a pattern, note it.
  If it doesn't but should, that's the gap to document in §6/§7.
- **No trailing summaries.** The report is a punch list. Don't add a "what went well"
  section or restate what the code does correctly.
