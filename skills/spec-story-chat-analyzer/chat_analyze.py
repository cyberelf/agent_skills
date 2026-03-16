#!/usr/bin/env python3
"""
chat_analyze.py — CLI tool for navigating SpecStory chat history exports.

Designed to help agents analyze chat files WITHOUT reading the entire file.
Provides structured TOC with line numbers and statistics, so the agent can
then use shell/file tools (e.g. sed -n 'START,ENDp') to read only what it needs.

Usage:
  python chat_analyze.py toc   [FILE]         # Table of contents with line numbers
  python chat_analyze.py stats [FILE]         # Aggregated statistics
  python chat_analyze.py show  [FILE] LINE    # Show context around a line (±N lines)
  python chat_analyze.py grep  [FILE] PATTERN # Search for pattern, return line numbers
  python chat_analyze.py tools [FILE]         # List all tool calls with line numbers
  python chat_analyze.py think [FILE]         # List all think blocks with line numbers
  python chat_analyze.py const [DIR]          # Find constitution/spec/AGENTS files
  python chat_analyze.py suggest [FILE]       # Read stats+TOC and emit analysis hints

If FILE is omitted, scans ./data/ for .md files and uses the first (or prompts).
"""

import os
import re
import sys
import glob
import json
import argparse
from pathlib import Path

DATA_DIR = Path(__file__).parent / "data"

# ────────────────────────────────────────────────────────────────────────────
# Patterns
# ────────────────────────────────────────────────────────────────────────────
SESSION_RE  = re.compile(r"^(# .+)$", re.MULTILINE)
USER_RE     = re.compile(r"^_\*\*User\*\*_\s*$", re.MULTILINE)
AGENT_RE    = re.compile(r"^_\*\*Agent([^*]*)\*\*_\s*$", re.MULTILINE)
THINK_RE    = re.compile(r"^<think>$", re.MULTILINE)
TOOL_RE     = re.compile(r'^<tool-use\s+data-tool-type="([^"]*)"\s+data-tool-name="([^"]*)"', re.MULTILINE)
HR_RE       = re.compile(r"^\s*---\s*$", re.MULTILINE)
THINK_SUMMARY_RE = re.compile(r"<summary>Thought Process</summary>\s*\n(.*?)\n", re.DOTALL)

# Constitution / spec / AGENTS file patterns
SPEC_FILE_PATTERNS = [
    "**/AGENTS.md", "**/agents.md",
    "**/CLAUDE.md", "**/claude.md",
    "**/.cursorrules", "**/cursorrules.md",
    "**/CONSTITUTION.md", "**/constitution.md",
    "**/COPILOT-INSTRUCTIONS.md", "**/.github/copilot-instructions.md",
    "**/openspec/**/*.md",
    "**/.agents/**/*.md",
    "**/SPEC.md", "**/spec.md",
    "**/RULES.md", "**/rules.md",
]

# ────────────────────────────────────────────────────────────────────────────
# Helpers
# ────────────────────────────────────────────────────────────────────────────

def resolve_file(arg=None):
    """Return (path, lines) for the chat file, or exit with error."""
    if arg:
        p = Path(arg)
        if not p.is_file():
            # Try relative to data dir
            p = DATA_DIR / arg
        if not p.is_file():
            print(f"ERROR: file not found: {arg}", file=sys.stderr)
            sys.exit(1)
    else:
        candidates = sorted(DATA_DIR.glob("*.md"))
        if not candidates:
            print(f"ERROR: no .md files in {DATA_DIR}", file=sys.stderr)
            sys.exit(1)
        p = candidates[0]
        print(f"[Using {p.name}]", file=sys.stderr)
    with open(p, "r", encoding="utf-8") as f:
        text = f.read()
    lines = text.splitlines()
    return p, text, lines


def line_of_match(text, match):
    """Return 1-based line number of a regex match in text."""
    return text[: match.start()].count("\n") + 1


def first_text_after(lines, start_line, max_chars=80):
    """Get first non-empty, non-markup text line after start_line (1-based)."""
    for ln in lines[start_line:start_line + 30]:
        stripped = ln.strip()
        # skip empty, HR, HTML tags, markdown markup-only lines
        if not stripped:
            continue
        if stripped.startswith("<") or stripped.startswith("|") or stripped in ("---", "***"):
            continue
        stripped = re.sub(r"[*_`#>]+", "", stripped).strip()
        if stripped:
            return stripped[:max_chars]
    return ""


# ────────────────────────────────────────────────────────────────────────────
# Commands
# ────────────────────────────────────────────────────────────────────────────

def cmd_toc(p, text, lines):
    """Print table of contents: sessions → user messages → agent answers."""
    sessions = list(SESSION_RE.finditer(text))
    users    = list(USER_RE.finditer(text))
    agents   = list(AGENT_RE.finditer(text))

    # Map each message to its session index
    session_starts = [(line_of_match(text, m), m.group(1)) for m in sessions]

    def session_for_line(ln):
        idx = 0
        for i, (sl, _) in enumerate(session_starts):
            if sl <= ln:
                idx = i
        return idx

    print(f"# TOC: {p.name}  ({len(lines)} lines)\n")
    print(f"{'LINE':>6}  {'TYPE':<8}  SUMMARY")
    print("-" * 78)

    # Merge sessions + messages sorted by line
    events = []
    for m in sessions:
        ln = line_of_match(text, m)
        events.append(("session", ln, m.group(1), ""))
    for m in users:
        ln = line_of_match(text, m)
        snippet = first_text_after(lines, ln, 80)
        events.append(("user", ln, snippet, ""))
    for m in agents:
        ln = line_of_match(text, m)
        model_hint = m.group(1).strip(" ,")
        snippet = first_text_after(lines, ln, 80)
        events.append(("agent", ln, snippet, model_hint))

    events.sort(key=lambda e: e[1])

    for kind, ln, snippet, extra in events:
        if kind == "session":
            print(f"\n{'':>6}  ── {snippet} ──")
        elif kind == "user":
            print(f"{ln:>6}  USER      {snippet}")
        else:
            label = f"AGENT"
            if extra:
                label = f"AGENT({extra[:12]})"
            print(f"{ln:>6}  {label:<8}  {snippet}")


def cmd_stats(p, text, lines):
    """Print detailed statistics."""
    sessions  = list(SESSION_RE.finditer(text))
    users     = list(USER_RE.finditer(text))
    agents    = list(AGENT_RE.finditer(text))
    thinks    = list(THINK_RE.finditer(text))
    tools     = list(TOOL_RE.finditer(text))

    tool_types = {}
    tool_names = {}
    for m in tools:
        tt = m.group(1)
        tn = m.group(2)
        tool_types[tt] = tool_types.get(tt, 0) + 1
        tool_names[tn] = tool_names.get(tn, 0) + 1

    text_only = re.sub(r"<[^>]+>", "", text)
    text_only = re.sub(r"[#*_`>\-|[\]()]+", "", text_only)
    chars = len(text_only)
    est_tokens = max(100, int(chars * 0.25))

    # Per-session breakdown
    session_lines = [line_of_match(text, m) for m in sessions]
    session_lines.append(len(lines) + 1)  # sentinel

    print(f"# Stats: {p.name}\n")
    print(f"  File size   : {len(text):,} bytes  ({len(lines):,} lines)")
    print(f"  Sessions    : {len(sessions)}")
    print(f"  Messages    : {len(users)+len(agents):,}  "
          f"(user={len(users)}, agent={len(agents)})")
    print(f"  Think blocks: {len(thinks):,}")
    print(f"  Tool calls  : {len(tools):,}")
    print(f"  Est. tokens : {est_tokens:,}  ({chars:,} content chars)")

    if tool_types:
        print("\n  Tool type breakdown:")
        for tt, cnt in sorted(tool_types.items(), key=lambda x: -x[1]):
            print(f"    {tt:<20} {cnt:>5}")

    print("\n  Top 10 tool names:")
    for tn, cnt in sorted(tool_names.items(), key=lambda x: -x[1])[:10]:
        print(f"    {tn:<36} {cnt:>5}")

    print("\n  Session breakdown:")
    print(f"  {'LINE':>6}  {'MSG':>4}  {'TOOL':>5}  TITLE")
    for i, sm in enumerate(sessions):
        sl = session_lines[i]
        el = session_lines[i + 1]
        # messages in range
        msg_count = sum(1 for m in users + agents
                        if sl <= line_of_match(text, m) < el)
        tool_count = sum(1 for m in tools
                         if sl <= line_of_match(text, m) < el)
        title = sm.group(1)[:60]
        print(f"  {sl:>6}  {msg_count:>4}  {tool_count:>5}  {title}")


def cmd_show(p, text, lines, line_num, context=15):
    """Print lines around a given line number."""
    start = max(0, line_num - context - 1)
    end   = min(len(lines), line_num + context)
    print(f"# {p.name} lines {start+1}–{end}  (requested line {line_num})\n")
    for i, ln in enumerate(lines[start:end], start=start + 1):
        marker = ">>>" if i == line_num else "   "
        print(f"{i:>6} {marker} {ln}")


def cmd_grep(p, text, lines, pattern):
    """Search for pattern in text, print matching lines with numbers."""
    try:
        rx = re.compile(pattern, re.IGNORECASE)
    except re.error as e:
        print(f"ERROR: bad pattern: {e}", file=sys.stderr)
        sys.exit(1)
    print(f"# grep '{pattern}' in {p.name}\n")
    found = 0
    for i, ln in enumerate(lines, 1):
        if rx.search(ln):
            print(f"{i:>6}  {ln}")
            found += 1
    print(f"\n{found} match(es)")


def cmd_tools(p, text, lines):
    """List all tool calls with line numbers."""
    print(f"# Tool calls in {p.name}\n")
    print(f"{'LINE':>6}  {'TYPE':<12}  TOOL NAME")
    print("-" * 60)
    for m in TOOL_RE.finditer(text):
        ln  = line_of_match(text, m)
        tt  = m.group(1)
        tn  = m.group(2)
        print(f"{ln:>6}  {tt:<12}  {tn}")


def cmd_think(p, text, lines):
    """List all think blocks with line numbers and first line of content."""
    print(f"# Think blocks in {p.name}\n")
    print(f"{'LINE':>6}  {'END':>6}  FIRST LINE")
    print("-" * 70)
    # Find </think> to determine block end
    end_think_re = re.compile(r"^</think>$", re.MULTILINE)
    opens  = list(THINK_RE.finditer(text))
    closes = list(end_think_re.finditer(text))
    for i, m in enumerate(opens):
        sl = line_of_match(text, m)
        el = line_of_match(text, closes[i]) if i < len(closes) else "?"
        snippet = first_text_after(lines, sl, 80)
        print(f"{sl:>6}  {str(el):>6}  {snippet}")


def cmd_const(search_dir=None):
    """Find constitution / spec / AGENTS files in a directory tree."""
    base = Path(search_dir) if search_dir else Path.cwd()
    print(f"# Constitution/spec/AGENTS files under {base}\n")
    found = []
    for pattern in SPEC_FILE_PATTERNS:
        for p in sorted(base.glob(pattern)):
            if p not in found:
                found.append(p)
    if not found:
        print("  (none found)")
    else:
        for p in found:
            size = p.stat().st_size
            print(f"  {str(p.relative_to(base)):<60}  {size:>8} bytes")
    print(f"\n{len(found)} file(s) found")
    return found


def cmd_suggest(p, text, lines):
    """
    Emit a structured analysis hint without reading the full file.
    Combines stats + structure patterns + common issues to produce
    actionable suggestions for improving AGENTS.md and spec files.
    """
    # Re-use stats logic
    sessions  = list(SESSION_RE.finditer(text))
    users     = list(USER_RE.finditer(text))
    agents    = list(AGENT_RE.finditer(text))
    thinks    = list(THINK_RE.finditer(text))
    tools     = list(TOOL_RE.finditer(text))
    tool_types = {}
    tool_names = {}
    for m in tools:
        tool_types[m.group(1)] = tool_types.get(m.group(1), 0) + 1
        tool_names[m.group(2)] = tool_names.get(m.group(2), 0) + 1

    n_sess  = len(sessions)
    n_user  = len(users)
    n_agent = len(agents)
    n_tool  = len(tools)
    n_think = len(thinks)

    # Detect re-read patterns: same tool name called many times
    repeated_reads = {tn: cnt for tn, cnt in tool_names.items()
                      if cnt >= 5 and any(k in tn.lower() for k in ("read", "get", "fetch", "cat", "view"))}

    # Detect shell/write heavy sessions (may indicate scripting tasks)
    shell_pct = tool_types.get("shell", 0) / max(n_tool, 1) * 100
    write_pct = tool_types.get("write", 0) / max(n_tool, 1) * 100
    read_pct  = tool_types.get("read",  0) / max(n_tool, 1) * 100

    # Think-to-message ratio (heavy thinking may mean ambiguous instructions)
    think_ratio = n_think / max(n_agent, 1)

    # Messages per session
    msgs_per_sess = (n_user + n_agent) / max(n_sess, 1)

    # Collect session titles for pattern detection
    session_titles = [m.group(1) for m in sessions]

    print(f"# Analysis hints for {p.name}\n")
    print(f"  {n_sess} sessions, {n_user+n_agent} messages, "
          f"{n_tool} tool calls, {n_think} think blocks\n")

    suggestions = []

    # ── Think ratio ────────────────────────────────────────────────────────
    if think_ratio > 2.0:
        suggestions.append({
            "area": "AGENTS.md / instructions clarity",
            "observation": f"High think-block ratio ({think_ratio:.1f} thinks/agent-msg). "
                           "The agent is deliberating a lot, which usually means the task "
                           "instructions or constraints are ambiguous.",
            "suggestion": "Review AGENTS.md for unclear or missing constraints. "
                          "Consider adding explicit decision rules or step-by-step procedures "
                          "for high-think-ratio workflows.",
            "how_to_verify": f"Run: python chat_analyze.py think {p.name}  — inspect the "
                             "think blocks around frequently-confused topics.",
        })

    # ── Repeated reads ──────────────────────────────────────────────────────
    if repeated_reads:
        names = ", ".join(f"{k}({v})" for k, v in sorted(repeated_reads.items(), key=lambda x: -x[1])[:5])
        suggestions.append({
            "area": "Context management / AGENTS.md guidance",
            "observation": f"Repeated read/fetch tool calls: {names}. "
                           "The agent is re-reading the same files multiple times.",
            "suggestion": "Add a note to AGENTS.md instructing the agent to cache or "
                          "summarize file contents at the start of a task instead of "
                          "re-reading repeatedly. Consider adding a 'Read once' policy.",
            "how_to_verify": f"Run: python chat_analyze.py tools {p.name} | grep <toolname>  "
                             "to see which sessions trigger repeated reads.",
        })

    # ── Shell usage ─────────────────────────────────────────────────────────
    if shell_pct > 40:
        suggestions.append({
            "area": "Workflow automation / AGENTS.md",
            "observation": f"Shell tool usage is {shell_pct:.0f}% of all tool calls. "
                           "High shell usage often means manual steps that could be scripted.",
            "suggestion": "Create reusable scripts for common shell sequences and reference "
                          "them in AGENTS.md. Also add safety rules: whitelist allowed commands, "
                          "prohibit dangerous patterns (rm -rf, sudo, etc.).",
            "how_to_verify": "Run: python chat_analyze.py grep <file> 'shell' | head -30",
        })

    # ── Session length ───────────────────────────────────────────────────────
    if msgs_per_sess > 20:
        suggestions.append({
            "area": "Session scoping / task decomposition",
            "observation": f"Average {msgs_per_sess:.1f} messages/session. "
                           "Long sessions may indicate tasks that are too broad.",
            "suggestion": "Consider splitting long tasks into sub-tasks with clear "
                          "acceptance criteria. Add a 'task size limit' guideline to AGENTS.md.",
            "how_to_verify": "Review session titles with: python chat_analyze.py toc <file>",
        })

    # ── Write ratio ──────────────────────────────────────────────────────────
    if write_pct > 35:
        suggestions.append({
            "area": "File creation policy / AGENTS.md",
            "observation": f"File-write tool usage is {write_pct:.0f}% of all tool calls. "
                           "High write usage can create clutter if files aren't cleaned up.",
            "suggestion": "Add a section to AGENTS.md about file hygiene: temp file naming, "
                          "cleanup after tasks, and avoiding unnecessary file creation.",
            "how_to_verify": "Scan write calls: python chat_analyze.py tools <file> | grep write",
        })

    # ── Read ratio ───────────────────────────────────────────────────────────
    if read_pct < 10 and n_tool > 20:
        suggestions.append({
            "area": "Context bootstrapping / AGENTS.md",
            "observation": f"Read tool usage is only {read_pct:.0f}% of tool calls. "
                           "The agent may not be reading spec/constitution files at task start.",
            "suggestion": "Add an explicit instruction to AGENTS.md: 'At the start of every "
                          "task, read AGENTS.md, relevant spec files, and current task\'s "
                          "requirement.md before taking any action.'",
            "how_to_verify": "python chat_analyze.py const <project_dir>  — check what "
                             "spec files exist and add them to the bootstrap reading list.",
        })

    # ── No suggestions ───────────────────────────────────────────────────────
    if not suggestions:
        suggestions.append({
            "area": "General",
            "observation": "No obvious structural issues detected.",
            "suggestion": "Review individual sessions using the toc and show commands "
                          "to look for task-specific patterns.",
            "how_to_verify": "python chat_analyze.py toc <file>",
        })

    # Print
    for i, s in enumerate(suggestions, 1):
        print(f"──── Suggestion {i}: {s['area']}")
        print(f"  Observation : {s['observation']}")
        print(f"  Suggestion  : {s['suggestion']}")
        print(f"  Verify with : {s['how_to_verify']}")
        print()

    print("─" * 70)
    print("Next steps for the agent:")
    print("  1. python chat_analyze.py toc  <file>          — navigate sessions/messages")
    print("  2. python chat_analyze.py show <file> <LINE>   — read a specific context window")
    print("  3. python chat_analyze.py const <project_dir>  — locate spec/AGENTS files")
    print("  4. Use shell tool: sed -n 'L1,L2p' <file>      — read any line range precisely")


# ────────────────────────────────────────────────────────────────────────────
# Entry point
# ────────────────────────────────────────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser(
        description="SpecStory chat history analyzer — navigate without reading full files."
    )
    sub = parser.add_subparsers(dest="cmd", required=True)

    p_toc   = sub.add_parser("toc",     help="Table of contents with line numbers")
    p_stats = sub.add_parser("stats",   help="Aggregated statistics")
    p_show  = sub.add_parser("show",    help="Show context around a line")
    p_grep  = sub.add_parser("grep",    help="Search for a pattern, return line numbers")
    p_tools = sub.add_parser("tools",   help="List all tool calls with line numbers")
    p_think = sub.add_parser("think",   help="List all think blocks with line numbers")
    p_const = sub.add_parser("const",   help="Find constitution/spec/AGENTS files")
    p_sug   = sub.add_parser("suggest", help="Emit analysis hints and improvement suggestions")

    for sp in (p_toc, p_stats, p_show, p_grep, p_tools, p_think, p_sug):
        sp.add_argument("file", nargs="?", help="Chat history .md file (default: first in ./data/)")

    p_show.add_argument("line", type=int, help="Target line number (1-based)")
    p_show.add_argument("--context", "-c", type=int, default=15, help="Lines of context (default 15)")
    p_grep.add_argument("pattern", help="Regex pattern to search")
    p_const.add_argument("dir", nargs="?", help="Directory to search (default: cwd)")

    args = parser.parse_args()

    if args.cmd == "const":
        cmd_const(args.dir)
        return

    p, text, lines = resolve_file(getattr(args, "file", None))

    if args.cmd == "toc":
        cmd_toc(p, text, lines)
    elif args.cmd == "stats":
        cmd_stats(p, text, lines)
    elif args.cmd == "show":
        cmd_show(p, text, lines, args.line, args.context)
    elif args.cmd == "grep":
        cmd_grep(p, text, lines, args.pattern)
    elif args.cmd == "tools":
        cmd_tools(p, text, lines)
    elif args.cmd == "think":
        cmd_think(p, text, lines)
    elif args.cmd == "suggest":
        cmd_suggest(p, text, lines)


if __name__ == "__main__":
    main()
