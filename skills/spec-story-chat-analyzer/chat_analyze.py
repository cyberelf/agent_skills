#!/usr/bin/env python3
"""
chat_analyze.py — CLI tool for navigating SpecStory chat history exports.

Designed to help agents analyze chat files WITHOUT reading the entire file.
Provides structured TOC with line numbers and statistics, so the agent can
then use shell/file tools (e.g. sed -n 'START,ENDp') to read only what it needs.

Usage:
  python chat_analyze.py analyze [FILE]       # Full analysis report (main output)
  python chat_analyze.py problems [FILE]      # Checklist of problems with fixes
  python chat_analyze.py stats   [FILE]       # Aggregated statistics
  python chat_analyze.py toc     [FILE]       # Table of contents with line numbers
  python chat_analyze.py show    [FILE] LINE # Show context around a line (±N lines)
  python chat_analyze.py grep    [FILE] PATTERN # Search for pattern, return line numbers
  python chat_analyze.py tools   [FILE]      # List all tool calls with line numbers
  python chat_analyze.py think   [FILE]      # List all think blocks with line numbers
  python chat_analyze.py const   [DIR]       # Find constitution/spec/AGENTS files

If FILE is omitted, scans ./data/ for .md files and uses the first (or prompts).
"""

import os
import re
import sys
import glob
import json
import argparse
from pathlib import Path
from collections import defaultdict

DATA_DIR = Path(__file__).parent / "data"

# ────────────────────────────────────────────────────────────────────────────
# Patterns
# ────────────────────────────────────────────────────────────────────────────
SESSION_RE  = re.compile(r"^# (.+?)\s*(?:\([^)]+\))?\s*$", re.MULTILINE)
USER_RE     = re.compile(r"^_\*\*User\*\*_\s*$", re.MULTILINE)
AGENT_RE    = re.compile(r"^_\*\*Agent([^*]*)\*\*_\s*$", re.MULTILINE)
THINK_RE    = re.compile(r"^襄阳$", re.MULTILINE)
TOOL_RE     = re.compile(r'^<tool-use\s+data-tool-type="([^"]*)"\s+data-tool-name="([^"]*)"', re.MULTILINE)
TOOL_RESULT_RE = re.compile(r'<tool-result[^>]*>.*?</tool-result>', re.DOTALL)
HR_RE       = re.compile(r"^\s*---\s*$", re.MULTILINE)
THINK_SUMMARY_RE = re.compile(r"<summary>Thought Process</summary>\s*\n(.*?)\n", re.DOTALL)

# Secret/credential detection patterns
SECRET_PATTERNS = [
    # Database connection strings
    (re.compile(r'mysql\+pymysql://[^\s<>"\']+@\d+\.\d+\.\d+\.\d+(:\d+)?/\w+', re.IGNORECASE), "MySQL connection string"),
    (re.compile(r'postgres(?:ql)?://[^\s<>"\']+@\d+\.\d+\.\d+\.\d+(:\d+)?/\w+', re.IGNORECASE), "PostgreSQL connection string"),
    (re.compile(r'mongodb(?:\+srv)?://[^\s<>"\']+@\w+', re.IGNORECASE), "MongoDB connection string"),
    (re.compile(r'redis://[^\s<>"\']+@\d+\.\d+\.\d+\.\d+', re.IGNORECASE), "Redis connection string"),
    # API keys and secrets
    (re.compile(r'(?:api[_-]?key|api[_-]?secret|secret[_-]?key|access[_-]?key)\s*[=:]\s*["\']?[a-zA-Z0-9_\-]{16,}["\']?', re.IGNORECASE), "API key/secret"),
    (re.compile(r'["\']?[A-Z_]+_SECRET["\']?\s*[=:]\s*["\']?[a-zA-Z0-9_\-]{12,}["\']?', re.IGNORECASE), "Secret environment variable"),
    (re.compile(r'password\s*[=:]\s*["\'][^"\']{6,}["\']', re.IGNORECASE), "Password in code"),
    (re.compile(r'password\s*[=:]\s*["\']?[^\s"\']{6,}["\']?', re.IGNORECASE), "Password assignment"),
    # Tokens
    (re.compile(r'(?:bearer|token)\s+[a-zA-Z0-9_\-\.]{20,}', re.IGNORECASE), "Bearer token"),
    (re.compile(r'sk-[a-zA-Z0-9]{20,}', re.IGNORECASE), "OpenAI-style API key"),
    (re.compile(r'xox[baprs]-[a-zA-Z0-9\-]{10,}', re.IGNORECASE), "Slack token"),
    # AWS
    (re.compile(r'AKIA[0-9A-Z]{16}', re.IGNORECASE), "AWS access key"),
    (re.compile(r'(?:aws[_-]?secret)?[_-]?access[_-]?key[_-]?id\s*[=:]\s*["\']?AKIA', re.IGNORECASE), "AWS key in config"),
]

# Restart loop detection patterns
RESTART_PATTERNS = [
    re.compile(r'(?:^|[^\w])(?:restart|restarting|re-start|reboot)\s+(?:the\s+)?(?:server|service|backend|frontend|app|application|process)', re.IGNORECASE),
    re.compile(r'(?:^|[^\w])(?:start|starting|run|running)\s+(?:the\s+)?(?:server|service|backend|frontend|app|application)', re.IGNORECASE),
    re.compile(r'(?:^|[^\w])npm\s+(?:start|run\s+dev|run\s+start)', re.IGNORECASE),
    re.compile(r'(?:^|[^\w])python\s+[\w/]+\.py', re.IGNORECASE),
    re.compile(r'(?:^|[^\w])flask\s+run', re.IGNORECASE),
    re.compile(r'(?:^|[^\w])uvicorn\s+', re.IGNORECASE),
    re.compile(r'(?:^|[^\w])gunicorn\s+', re.IGNORECASE),
    re.compile(r'(?:^|[^\w])kill\s+\w+', re.IGNORECASE),
    re.compile(r'(?:^|[^\w])(?:stop|stopping)\s+(?:the\s+)?(?:server|service|process)', re.IGNORECASE),
    re.compile(r'port\s+\d+\s+(?:is\s+)?(?:already\s+)?(?:occupied|in\s+use|blocked)', re.IGNORECASE),
    re.compile(r'(?:lsof|netstat|ss)\s+.*\d+', re.IGNORECASE),
]

# Problem detection patterns
ERROR_PATTERNS = [
    re.compile(r"(?i)(error|failed|exception|timeout|permission denied|not found)"),
]
FRUSTRATION_PATTERNS = [
    re.compile(r"(?i)^(no|wrong|incorrect|not what i|try again|that's not|doesn't work|fix it|bad|stop)"),
]
INCOMPLETE_MARKERS = [
    re.compile(r"(?i)(todo|fixme|incomplete|wip|tbd|still (working|pending|need))"),
]

# Buggy code / iterative debugging patterns
BUGGY_CODE_PATTERNS = [
    re.compile(r"(?i)(still (not working|broken|doesn't work|won't work|frozen|invisible|not rendering))", re.IGNORECASE),
    re.compile(r"(?i)(now (it's |the |it is )(broken|bugged|wrong|frozen|invisible))", re.IGNORECASE),
    re.compile(r"(?i)(same error (again|still)|still getting (the )?same error)", re.IGNORECASE),
    re.compile(r"(?i)(another (bug|issue|problem)|more bugs|more issues)", re.IGNORECASE),
    re.compile(r"(?i)(invisible (lawn|grass|element|button|ui)|frozen (zombie|enemy|character|entity))", re.IGNORECASE),
]

# Technical infrastructure failure patterns
INFRA_FAILURE_PATTERNS = [
    re.compile(r"(?i)(invalid model (configuration|config|name)|model ['\"][^'\"]+['\"] (not found|invalid|unknown))", re.IGNORECASE),
    re.compile(r"(?i)(api (returned|error) \d{3}|api (request )?failed with \d{3}|http \d{3} error)", re.IGNORECASE),
    re.compile(r"(?i)(rate limit exceeded|quota exceeded|too many requests)", re.IGNORECASE),
    re.compile(r"(?i)(connection refused|econnrefused|network error|dns error|etimedout)", re.IGNORECASE),
]

# Skill configuration issue patterns
SKILL_ISSUE_PATTERNS = [
    re.compile(r"(?i)(missing skill\.md|no skill\.md|skill not found|skill configuration error)", re.IGNORECASE),
    re.compile(r"(?i)(skill format error|invalid skill yaml|skill\.md format)", re.IGNORECASE),
    re.compile(r"(?i)(use bash instead of python|bash script instead of python|prefer bash over python)", re.IGNORECASE),
]

# Topic/category keywords for scope drift detection
TOPIC_KEYWORDS = {
    'authentication': ['login', 'auth', 'password', 'session', 'token', 'jwt', 'sso', 'oauth', 'user'],
    'frontend': ['react', 'vue', 'angular', 'component', 'ui', 'css', 'html', 'frontend', 'page', 'button', 'form'],
    'backend': ['api', 'server', 'endpoint', 'flask', 'django', 'fastapi', 'backend', 'route', 'controller'],
    'database': ['mysql', 'postgres', 'mongodb', 'sql', 'database', 'db', 'query', 'migration', 'schema', 'table'],
    'deployment': ['deploy', 'docker', 'kubernetes', 'k8s', 'container', 'nginx', 'apache', 'production', 'staging'],
    'testing': ['test', 'spec', 'pytest', 'jest', 'mocha', 'coverage', 'unit', 'integration'],
    'environment': ['env', 'config', 'setup', 'install', 'requirement', 'dependency', 'port', 'startup'],
    'requirements': ['requirement', 'spec', 'document', 'decompose', 'feature', 'user story', 'acceptance'],
}

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


def get_session_ranges(text, lines):
    """Return list of (start_line, end_line, title) tuples for each session."""
    sessions = list(SESSION_RE.finditer(text))
    session_starts = [(line_of_match(text, m), m.group(1)) for m in sessions]
    session_ranges = []
    for i, (sl, title) in enumerate(session_starts):
        el = session_starts[i + 1][0] if i + 1 < len(session_starts) else len(lines) + 1
        session_ranges.append((sl, el, title))
    return session_ranges


def categorize_topic(text_snippet):
    """Detect the dominant topic category from text."""
    text_lower = text_snippet.lower()
    scores = {}
    for topic, keywords in TOPIC_KEYWORDS.items():
        score = sum(1 for kw in keywords if kw in text_lower)
        if score > 0:
            scores[topic] = score
    if scores:
        return max(scores, key=scores.get)
    return None


def detect_secrets(text, lines):
    """Find secrets and credentials in the chat."""
    findings = []
    seen = set()  # Avoid duplicate reports for same line

    for pattern, desc in SECRET_PATTERNS:
        for m in pattern.finditer(text):
            ln = line_of_match(text, m)
            key = (ln, desc)
            if key in seen:
                continue
            seen.add(key)
            matched = m.group(0)
            # Truncate for display
            display = matched[:60] + "..." if len(matched) > 60 else matched
            findings.append({
                "line": ln,
                "type": desc,
                "snippet": display,
            })

    return findings


def detect_scope_drift(text, lines, session_ranges):
    """Detect when sessions drift from their original topic."""
    drifts = []

    for sl, el, title in session_ranges:
        # Get first portion of session for initial topic
        first_quarter_end = min(sl + (el - sl) // 4, el)
        last_quarter_start = max(sl + 3 * (el - sl) // 4, sl)

        first_text = "\n".join(lines[sl-1:first_quarter_end])
        last_text = "\n".join(lines[last_quarter_start:el-1])

        first_topic = categorize_topic(first_text)
        last_topic = categorize_topic(last_text)

        if first_topic and last_topic and first_topic != last_topic:
            drifts.append({
                "session_line": sl,
                "session_title": title,
                "original_topic": first_topic,
                "drifted_topic": last_topic,
                "drift_start": last_quarter_start,
            })

    return drifts


def detect_restart_loops(text, lines, session_ranges):
    """Detect repeated restart/start commands across the conversation."""
    restart_matches = []

    for pattern in RESTART_PATTERNS:
        for m in pattern.finditer(text):
            ln = line_of_match(text, m)
            restart_matches.append((ln, m.group(0).strip()[:50]))

    # Group by session
    restarts_by_session = defaultdict(list)
    for ln, snippet in restart_matches:
        for sl, el, title in session_ranges:
            if sl <= ln < el:
                restarts_by_session[(sl, title)].append((ln, snippet))
                break

    # Find sessions with multiple restarts
    problematic = []
    for (sl, title), restarts in restarts_by_session.items():
        if len(restarts) >= 3:
            problematic.append({
                "session_line": sl,
                "session_title": title,
                "count": len(restarts),
                "lines": [ln for ln, _ in restarts[:5]],
            })

    # Also detect restart patterns spanning sessions
    if len(restart_matches) >= 5:
        # Check if restarts are clustered
        restart_lines = sorted([ln for ln, _ in restart_matches])
        clusters = []
        current_cluster = [restart_lines[0]]
        for ln in restart_lines[1:]:
            if ln - current_cluster[-1] < 500:  # Within ~500 lines
                current_cluster.append(ln)
            else:
                if len(current_cluster) >= 3:
                    clusters.append(current_cluster)
                current_cluster = [ln]
        if len(current_cluster) >= 3:
            clusters.append(current_cluster)

        for cluster in clusters:
            problematic.append({
                "session_line": cluster[0],
                "session_title": "Multiple sessions",
                "count": len(cluster),
                "lines": cluster[:5],
                "is_cluster": True,
            })

    return problematic


def detect_buggy_code(text, lines, session_ranges):
    """Detect buggy code patterns and iterative debugging."""
    buggy_sessions = []

    for sl, el, title in session_ranges:
        session_text = "\n".join(lines[sl-1:el])

        bug_matches = []
        for pattern in BUGGY_CODE_PATTERNS:
            for m in pattern.finditer(session_text):
                # Get line within the session
                rel_line = session_text[:m.start()].count('\n') + 1
                abs_line = sl + rel_line - 1
                bug_matches.append((abs_line, m.group(0).strip()[:60]))

        if len(bug_matches) >= 2:
            buggy_sessions.append({
                "session_line": sl,
                "session_title": title,
                "count": len(bug_matches),
                "lines": [ln for ln, _ in bug_matches[:5]],
                "examples": [txt for _, txt in bug_matches[:3]],
            })

    return buggy_sessions


def detect_infra_failures(text, lines, session_ranges):
    """Detect technical infrastructure failures (API errors, config errors)."""
    failures = []

    for pattern in INFRA_FAILURE_PATTERNS:
        for m in pattern.finditer(text):
            ln = line_of_match(text, m)
            matched = m.group(0).strip()[:60]
            failures.append({
                "line": ln,
                "type": "Infrastructure Failure",
                "snippet": matched,
            })

    # Group by session
    failures_by_session = defaultdict(list)
    for f in failures:
        for sl, el, title in session_ranges:
            if sl <= f["line"] < el:
                failures_by_session[(sl, title)].append(f)
                break

    return failures, failures_by_session


def detect_skill_issues(text, lines, session_ranges):
    """Detect skill configuration issues (missing SKILL.md, Python env issues)."""
    issues = []

    for pattern in SKILL_ISSUE_PATTERNS:
        for m in pattern.finditer(text):
            ln = line_of_match(text, m)
            matched = m.group(0).strip()[:60]
            issues.append({
                "line": ln,
                "type": "Skill Configuration",
                "snippet": matched,
            })

    return issues


def analyze_session_detail(text, lines, sl, el, title, users, agents, tools):
    """Analyze a single session for the session-by-session breakdown."""
    # Count messages in session
    msg_count = sum(1 for m in users + agents if sl <= line_of_match(text, m) < el)
    tool_count = sum(1 for m in tools if sl <= line_of_match(text, m) < el)

    # Get session text
    session_text = "\n".join(lines[sl-1:el])

    # Detect issues
    issues = []

    # Check for incomplete markers
    for imp in INCOMPLETE_MARKERS:
        if imp.search(session_text):
            issues.append("incomplete markers found")
            break

    # Check for errors
    error_count = sum(1 for ep in ERROR_PATTERNS for _ in ep.finditer(session_text))
    if error_count > 5:
        issues.append(f"{error_count} error patterns")

    # Detect topic
    topic = categorize_topic(session_text)

    return {
        "start_line": sl,
        "end_line": el,
        "title": title,
        "msg_count": msg_count,
        "tool_count": tool_count,
        "topic": topic,
        "issues": issues,
    }


# ────────────────────────────────────────────────────────────────────────────
# Commands
# ────────────────────────────────────────────────────────────────────────────

def cmd_toc(p, text, lines):
    """Print table of contents: sessions -> user messages -> agent answers."""
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
            print(f"\n{'':>6}  -- {snippet} --")
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
    print(f"# {p.name} lines {start+1}-{end}  (requested line {line_num})\n")
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
    # Find end markers
    end_think_re = re.compile(r"^银阳$", re.MULTILINE)
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


def cmd_problems(p, text, lines):
    """
    Produce a checklist of problems found in the chat history.
    Focus on actionable issues, not generic suggestions.
    """
    sessions = list(SESSION_RE.finditer(text))
    users = list(USER_RE.finditer(text))
    agents = list(AGENT_RE.finditer(text))
    thinks = list(THINK_RE.finditer(text))
    tools = list(TOOL_RE.finditer(text))

    tool_types = {}
    tool_names = {}
    tool_lines = []
    for m in tools:
        ln = line_of_match(text, m)
        tt = m.group(1)
        tn = m.group(2)
        tool_types[tt] = tool_types.get(tt, 0) + 1
        tool_names[tn] = tool_names.get(tn, 0) + 1
        tool_lines.append((ln, tt, tn))

    n_sess = len(sessions)
    n_user = len(users)
    n_agent = len(agents)
    n_tool = len(tools)
    n_think = len(thinks)

    problems = []
    recurring = []

    # Session line ranges
    session_ranges = get_session_ranges(text, lines)

    # -- Detect secrets --
    secrets = detect_secrets(text, lines)
    if secrets:
        # Group by type
        by_type = defaultdict(list)
        for s in secrets:
            by_type[s["type"]].append(s["line"])

        lines_str = ", ".join(str(s["line"]) for s in secrets[:7])
        if len(secrets) > 7:
            lines_str += f", +{len(secrets)-7} more"
        problems.append({
            "category": "Secret Exposure",
            "severity": "high",
            "description": f"{len(secrets)} credential(s) exposed in chat",
            "context": f"Lines: {lines_str}",
            "fix": "Rotate all exposed credentials immediately. Add rule to AGENTS.md: never paste or echo secrets verbatim."
        })

    # -- Detect tool failures --
    error_lines = []
    for i, ln in enumerate(lines, 1):
        for ep in ERROR_PATTERNS:
            if ep.search(ln):
                error_lines.append(i)
                break

    if error_lines:
        # Group by session
        errors_by_session = {}
        for ln in error_lines[:20]:  # limit to first 20
            for sl, el, title in session_ranges:
                if sl <= ln < el:
                    if title not in errors_by_session:
                        errors_by_session[title] = []
                    errors_by_session[title].append(ln)
                    break

        examples = ", ".join(str(ln) for ln in error_lines[:5])
        problems.append({
            "category": "Tool Failure",
            "severity": "medium",
            "description": f"{len(error_lines)} tool errors detected",
            "context": f"Lines: {examples}{'...' if len(error_lines) > 5 else ''}",
            "fix": "Check error messages and fix underlying issues. Add error handling to AGENTS.md if needed."
        })

    # -- Detect user frustration --
    frustration_lines = []
    for m in users:
        ln = line_of_match(text, m)
        # Check next few lines for frustration
        for check_ln in range(ln, min(ln + 3, len(lines) + 1)):
            if check_ln <= len(lines):
                line_text = lines[check_ln - 1]
                for fp in FRUSTRATION_PATTERNS:
                    if fp.search(line_text):
                        frustration_lines.append((ln, line_text.strip()[:60]))
                        break

    if len(frustration_lines) >= 2:
        examples = "; ".join(f'"{txt}"' for _, txt in frustration_lines[:3])
        problems.append({
            "category": "User Frustration",
            "severity": "medium",
            "description": f"User corrected/rejected output {len(frustration_lines)} times",
            "context": f"Examples: {examples}",
            "fix": "Clarify task requirements upfront. Ask clarifying questions before implementing. Review AGENTS.md for ambiguous instructions."
        })

    # -- Detect restart loops --
    restart_loops = detect_restart_loops(text, lines, session_ranges)
    if restart_loops:
        all_lines = []
        for rl in restart_loops:
            all_lines.extend(rl.get("lines", []))
        examples = ", ".join(str(ln) for ln in sorted(set(all_lines))[:7])
        problems.append({
            "category": "Restart Loop",
            "severity": "medium",
            "description": f"Repeated startup/restart patterns detected ({sum(r['count'] for r in restart_loops)} instances)",
            "context": f"Lines: {examples}",
            "fix": "Create a canonical startup runbook. Verify environment once before testing instead of repeated restart cycles."
        })

    # -- Detect scope drift --
    scope_drifts = detect_scope_drift(text, lines, session_ranges)
    if scope_drifts:
        for sd in scope_drifts[:3]:  # Limit to top 3
            problems.append({
                "category": "Scope Drift",
                "severity": "medium",
                "description": f"Session at line {sd['session_line']} drifted from {sd['original_topic']} to {sd['drifted_topic']}",
                "context": f"Title: \"{sd['session_title'][:50]}\"",
                "fix": "Split into separate sessions when task domain changes. Use explicit scope-reset when switching objectives."
            })

    # -- Detect buggy code / iterative debugging --
    buggy_sessions = detect_buggy_code(text, lines, session_ranges)
    if buggy_sessions:
        all_bug_lines = []
        all_examples = []
        for bs in buggy_sessions:
            all_bug_lines.extend(bs.get("lines", []))
            all_examples.extend(bs.get("examples", []))
        examples = "; ".join(f'"{ex}"' for ex in all_examples[:3])
        problems.append({
            "category": "Buggy Code",
            "severity": "medium",
            "description": f"Multiple debugging iterations in {len(buggy_sessions)} session(s)",
            "context": f"Patterns: {examples}",
            "fix": "Add visual verification step after initial implementation. Test core mechanics before adding features. Include debug helpers in initial build."
        })

    # -- Detect infrastructure failures --
    infra_failures, _ = detect_infra_failures(text, lines, session_ranges)
    if infra_failures:
        examples = ", ".join(f"{f['line']} ({f['snippet'][:30]})" for f in infra_failures[:5])
        problems.append({
            "category": "Infrastructure Failure",
            "severity": "high",
            "description": f"{len(infra_failures)} infrastructure error(s) blocked progress",
            "context": f"Lines: {examples}",
            "fix": "Fix configuration errors first. Check model names, API endpoints, and environment variables. Block feature work until infra is stable."
        })

    # -- Detect skill configuration issues --
    skill_issues = detect_skill_issues(text, lines, session_ranges)
    if skill_issues:
        examples = ", ".join(f"line {s['line']}: {s['snippet'][:40]}" for s in skill_issues[:5])
        problems.append({
            "category": "Skill Configuration",
            "severity": "medium",
            "description": f"{len(skill_issues)} skill/tool configuration issue(s)",
            "context": f"Examples: {examples}",
            "fix": "Add SKILL.md with proper YAML frontmatter. Prefer Bash over Python for skills. Test skill execution after creation."
        })

    # -- Detect long sessions --
    long_sessions = []
    for sl, el, title in session_ranges:
        msg_count = sum(1 for m in users + agents if sl <= line_of_match(text, m) < el)
        if msg_count > 25:
            long_sessions.append((sl, msg_count, title[:50]))

    if long_sessions:
        examples = "; ".join(f"line {sl} ({cnt} msgs)" for sl, cnt, _ in long_sessions[:3])
        problems.append({
            "category": "Session Bloat",
            "severity": "low",
            "description": f"{len(long_sessions)} sessions with >25 messages",
            "context": f"Examples: {examples}",
            "fix": "Split large tasks into sub-tasks. Add task-size limit to AGENTS.md."
        })

    # -- Detect incomplete sessions --
    incomplete_found = []
    for sl, el, title in session_ranges:
        session_text = "\n".join(lines[sl-1:el])
        for imp in INCOMPLETE_MARKERS:
            if imp.search(session_text):
                incomplete_found.append((sl, title[:50]))
                break

    if incomplete_found:
        examples = "; ".join(f"line {sl}" for sl, _ in incomplete_found[:3])
        problems.append({
            "category": "Incomplete Session",
            "severity": "low",
            "description": f"{len(incomplete_found)} sessions appear incomplete (TODO/FIXME/WIP found)",
            "context": f"Examples: {examples}",
            "fix": "Review incomplete sessions. Ensure tasks have clear completion criteria."
        })

    # -- Output --
    print(f"# Chat Analysis: {p.name}\n")
    print(f"  {n_sess} sessions, {n_user + n_agent} messages, {n_tool} tool calls\n")

    if problems:
        print("## Problems Found\n")
        for pr in problems:
            sev = pr.get("severity", "medium")
            print(f"- [ ] **[{sev.upper()}] {pr['category']}**: {pr['description']}")
            print(f"  - Context: {pr['context']}")
            print(f"  - Fix: {pr['fix']}")
            print()
    else:
        print("## Problems Found\n")
        print("  (no major problems detected)\n")

    if recurring:
        print("## Recurring Patterns\n")
        for rc in recurring:
            print(f"- [ ] {rc['pattern']}")
            print(f"  - Suggestion: {rc['suggestion']}")
            print()

    print("## Quick Commands\n")
    print(f"  python chat_analyze.py toc     {p.name}  # Navigate sessions")
    print(f"  python chat_analyze.py show    {p.name} <LINE>  # Read context around line")
    print(f"  python chat_analyze.py const   <project_dir>  # Find AGENTS.md")


def cmd_analyze(p, text, lines):
    """
    Produce a comprehensive analysis report matching the sample format.
    This is the main output command.
    """
    sessions = list(SESSION_RE.finditer(text))
    users = list(USER_RE.finditer(text))
    agents = list(AGENT_RE.finditer(text))
    thinks = list(THINK_RE.finditer(text))
    tools = list(TOOL_RE.finditer(text))

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

    session_ranges = get_session_ranges(text, lines)

    # -- Detect secrets --
    secrets = detect_secrets(text, lines)

    # -- Detect restart loops --
    restart_loops = detect_restart_loops(text, lines, session_ranges)

    # -- Detect scope drift --
    scope_drifts = detect_scope_drift(text, lines, session_ranges)

    # -- Detect buggy code --
    buggy_sessions = detect_buggy_code(text, lines, session_ranges)

    # -- Detect infrastructure failures --
    infra_failures, infra_by_session = detect_infra_failures(text, lines, session_ranges)

    # -- Detect skill issues --
    skill_issues = detect_skill_issues(text, lines, session_ranges)

    # -- Detect errors --
    error_lines = []
    for i, ln in enumerate(lines, 1):
        for ep in ERROR_PATTERNS:
            if ep.search(ln):
                error_lines.append(i)
                break

    # -- Detect user frustration --
    frustration_lines = []
    for m in users:
        ln = line_of_match(text, m)
        for check_ln in range(ln, min(ln + 3, len(lines) + 1)):
            if check_ln <= len(lines):
                line_text = lines[check_ln - 1]
                for fp in FRUSTRATION_PATTERNS:
                    if fp.search(line_text):
                        frustration_lines.append((ln, line_text.strip()[:60]))
                        break

    # -- Output --
    print(f"# Chat History Analysis: {p.name}\n")

    # Summary
    print("## Summary\n")
    print(f"- Sessions: {len(sessions)}")
    print(f"- Messages: {len(users) + len(agents)}")
    print(f"- Tool calls: {len(tools)}")
    print(f"- Estimated tokens: {est_tokens // 1000}k")

    top_tools = sorted(tool_names.items(), key=lambda x: -x[1])[:3]
    if top_tools:
        print(f"- Dominant tool mix: {', '.join(f'{tn} {cnt}' for tn, cnt in top_tools)}")

    # High-risk indicators
    risk_indicators = []
    if secrets:
        risk_indicators.append("secret exposure")
    if restart_loops:
        risk_indicators.append("repeated restart loops")
    if scope_drifts:
        risk_indicators.append("scope drift")
    if frustration_lines:
        risk_indicators.append("user frustration")
    if buggy_sessions:
        risk_indicators.append("buggy code iterations")
    if infra_failures:
        risk_indicators.append("infrastructure failures")
    if skill_issues:
        risk_indicators.append("skill configuration issues")
    if risk_indicators:
        print(f"- High-risk indicators: {', '.join(risk_indicators)}")

    print()

    # Core insight
    if secrets or scope_drifts or restart_loops:
        print("The chat is not mainly failing because of one bad answer. It is failing because")
        if secrets:
            print("- credentials were exposed in the conversation, making the export file sensitive")
        if scope_drifts:
            print("- multiple unrelated tasks accumulated in the same long-running thread")
        if restart_loops:
            print("- environment issues were not resolved before feature work continued")
        print()

    # Primary Findings
    print("## Primary Findings\n")

    finding_num = 1

    # 1. Secret Exposure
    if secrets:
        print(f"### {finding_num}. Secret Exposure In Chat\n")
        print("Severity: high\n")
        print("Evidence:\n")

        # Group by type
        by_type = defaultdict(list)
        for s in secrets:
            by_type[s["type"]].append(s["line"])

        for stype, slines in by_type.items():
            examples = ", ".join(str(ln) for ln in slines[:5])
            if len(slines) > 5:
                examples += f", and {len(slines) - 5} more locations"
            print(f"- `{stype}` appears at source lines {examples}.")

        print("\nPattern:\n")
        print("The conversation used the chat log itself as a transport for runtime credentials.")
        print("That makes the export file sensitive and turns normal analysis artifacts into secret-bearing assets.\n")
        print("Impact:\n")
        print("- anyone with the export can recover live credentials,")
        print("- analysis outputs become unsafe to share,")
        print("- later summaries risk re-propagating the same secrets.\n")
        print("Recommended fix:\n")
        print("- redact all credentials in conversation,")
        print("- rotate the leaked credentials,")
        print("- add a hard rule that the agent must never repeat pasted secrets back verbatim.\n")
        finding_num += 1

    # 2. Scope Drift
    if scope_drifts:
        print(f"### {finding_num}. Scope Drift Across Major Sessions\n")
        print("Severity: high\n")
        print("Evidence:\n")

        for sd in scope_drifts[:5]:
            print(f"- The session at source line {sd['session_line']} begins focused on {sd['original_topic']}.")
            print(f"  It later shifts to {sd['drifted_topic']} around source line {sd['drift_start']}.")

        print("\nPattern:\n")
        print("The thread keeps carrying forward prior context instead of re-establishing a clean goal.")
        print("Session titles stop matching the actual work being done.\n")
        print("Impact:\n")
        print("- acceptance criteria become unclear,")
        print("- test results are hard to interpret,")
        print("- the agent can no longer tell which changes are task-critical versus opportunistic.\n")
        print("Recommended fix:\n")
        print("- enforce one major objective per thread,")
        print("- require explicit re-scoping when the task changes domain,")
        print("- split new objectives into named sub-tasks.\n")
        finding_num += 1

    # 3. Restart Loops
    if restart_loops:
        print(f"### {finding_num}. Environment Churn And Restart Loops\n")
        print("Severity: medium\n")
        print("Evidence:\n")

        all_restart_lines = []
        for rl in restart_loops:
            all_restart_lines.extend(rl.get("lines", []))
        examples = ", ".join(str(ln) for ln in sorted(set(all_restart_lines))[:9])
        print(f"- Repeated startup or restart requests appear around source lines {examples}.")
        print("- The conversation also contains repeated port-occupation and startup diagnostics in the same broad time window.\n")

        print("Pattern:\n")
        print("The environment was not stabilized first. The flow repeatedly returns to start or restart")
        print("services, then tries another change, then restarts again.\n")
        print("Impact:\n")
        print("- slow feedback loop,")
        print("- unclear runtime baseline,")
        print("- results may be produced against stale processes or wrong ports.\n")
        print("Recommended fix:\n")
        print("- define one canonical startup runbook,")
        print("- verify ports and env once before feature testing,")
        print("- treat environment failure as a blocker instead of continuing to edit code blindly.\n")
        finding_num += 1

    # 4. User Frustration
    if len(frustration_lines) >= 2:
        print(f"### {finding_num}. Response Mode Often Missed User Intent\n")
        print("Severity: medium\n")
        print("Evidence:\n")
        for ln, txt in frustration_lines[:5]:
            print(f"- The user expressed frustration at source line {ln}: \"{txt}\"")
        print("\nPattern:\n")
        print("The conversation leans toward execution and narration even when the user wants a different approach.\n")
        print("Impact:\n")
        print("- replies feel long but still incomplete,")
        print("- the user has to re-issue the request in a narrower form,")
        print("- tool activity grows without always improving clarity.\n")
        print("Recommended fix:\n")
        print("- force an early decision: execute, explain, or summarize,")
        print("- when the user expresses frustration, pause and ask for clarification before continuing.\n")
        finding_num += 1

    # 5. Long sessions
    long_sessions = []
    for sl, el, title in session_ranges:
        msg_count = sum(1 for m in users + agents if sl <= line_of_match(text, m) < el)
        tool_count = sum(1 for m in tools if sl <= line_of_match(text, m) < el)
        if msg_count > 20 or tool_count > 100:
            long_sessions.append((sl, msg_count, tool_count, title))

    if long_sessions:
        print(f"### {finding_num}. Session Complexity\n")
        print("Severity: medium\n")
        print("Evidence:\n")
        for sl, msg_cnt, tool_cnt, title in long_sessions[:3]:
            print(f"- Session at line {sl} has {msg_cnt} messages and {tool_cnt} tool calls.")
        print("\nPattern:\n")
        print("Large sessions accumulate context and make it harder to track what was done and why.\n")
        print("Recommended fix:\n")
        print("- cap sessions by objective, not by elapsed time,")
        print("- use explicit checkpoints when a session grows large.\n")
        finding_num += 1

    # 6. Buggy Code
    if buggy_sessions:
        print(f"### {finding_num}. Buggy Code And Iterative Debugging\n")
        print("Severity: medium\n")
        print("Evidence:\n")

        for bs in buggy_sessions[:3]:
            examples = ", ".join(f'"{ex}"' for ex in bs.get("examples", [])[:2])
            print(f"- Session at line {bs['session_line']} had {bs['count']} debugging iterations.")
            if examples:
                print(f"  Patterns: {examples}")

        print("\nPattern:\n")
        print("Initial implementations shipped with bugs requiring multiple fix rounds.")
        print("Visual elements or core mechanics did not work as expected on first delivery.\n")
        print("Impact:\n")
        print("- extended session time,")
        print("- user has to report bugs and wait for fixes,")
        print("- debugging effort could have been avoided with upfront verification.\n")
        print("Recommended fix:\n")
        print("- run game/UI in browser immediately after initial implementation,")
        print("- test core mechanics before adding advanced features,")
        print("- include visual debug helpers (colored borders, console logs) for initial builds.\n")
        finding_num += 1

    # 7. Infrastructure Failures
    if infra_failures:
        print(f"### {finding_num}. Technical Infrastructure Failures\n")
        print("Severity: high\n")
        print("Evidence:\n")

        for f in infra_failures[:5]:
            print(f"- At source line {f['line']}: {f['snippet']}")

        print("\nPattern:\n")
        print("API and configuration errors blocked progress entirely, leaving no deliverable.\n")
        print("Impact:\n")
        print("- sessions blocked with no output,")
        print("- wasted time on external failures,")
        print("- feature work continued before infrastructure was stable.\n")
        print("Recommended fix:\n")
        print("- fix configuration errors before feature work,")
        print("- check model names and API endpoints in settings,")
        print("- treat infra failures as blockers, not background noise.\n")
        finding_num += 1

    # 8. Skill Configuration Issues
    if skill_issues:
        print(f"### {finding_num}. Skill And Tool Configuration Gaps\n")
        print("Severity: medium\n")
        print("Evidence:\n")

        for s in skill_issues[:5]:
            print(f"- At source line {s['line']}: {s['snippet']}")

        print("\nPattern:\n")
        print("Skills were incomplete or misconfigured, requiring manual fixes before use.\n")
        print("Impact:\n")
        print("- skills couldn't be invoked until fixed,")
        print("- Python environment setup issues added friction,")
        print("- user had to request fixes before getting value.\n")
        print("Recommended fix:\n")
        print("- always include SKILL.md with proper YAML frontmatter,")
        print("- prefer Bash scripts over Python to avoid environment issues,")
        print("- test skill execution after creation.\n")
        finding_num += 1

    # Session-By-Session Breakdown
    print("## Session-By-Session Breakdown\n")

    for i, (sl, el, title) in enumerate(session_ranges):
        # Count messages and tools in session
        msg_count = sum(1 for m in users + agents if sl <= line_of_match(text, m) < el)
        tool_count = sum(1 for m in tools if sl <= line_of_match(text, m) < el)

        # Analyze session
        detail = analyze_session_detail(text, lines, sl, el, title, users, agents, tools)

        print(f"### Session at line {sl}: {title}\n")

        # Shape
        print(f"- Shape: {msg_count} messages, {tool_count} tool calls.")

        # Detect issues specific to this session
        issues = []
        session_text = "\n".join(lines[sl-1:el])

        # Check for secrets
        session_secrets = [s for s in secrets if sl <= s["line"] < el]
        if session_secrets:
            issues.append(f"contains {len(session_secrets)} credential exposure(s)")

        # Check for restarts
        session_restarts = []
        for rl in restart_loops:
            if rl.get("session_line") == sl:
                session_restarts.append(rl)
        if session_restarts:
            issues.append(f"contains {sum(r['count'] for r in session_restarts)} restart attempts")

        # Check for frustration
        session_frustration = [ln for ln, _ in frustration_lines if sl <= ln < el]
        if session_frustration:
            issues.append(f"user frustration detected at line {session_frustration[0]}")

        # Check for scope drift
        for sd in scope_drifts:
            if sd["session_line"] == sl:
                issues.append(f"scope drifted from {sd['original_topic']} to {sd['drifted_topic']}")

        # Check for incomplete
        for imp in INCOMPLETE_MARKERS:
            if imp.search(session_text):
                issues.append("incomplete markers found")
                break

        if issues:
            print(f"- Issue: {'; '.join(issues)}.")
        else:
            print(f"- Issue: no major issues detected.")

        # Pattern
        topic = detail.get("topic")
        if topic:
            print(f"- Pattern: session focused on {topic}.")
        else:
            print(f"- Pattern: no clear topic category detected.")

        # Better split suggestion
        if msg_count > 15 or tool_count > 80:
            print(f"- Better split: consider breaking this session into smaller focused tasks.")
        elif session_secrets or session_restarts or session_frustration:
            print(f"- Better split: separate concerns into dedicated sessions for cleaner context.")

        print()

    # Recommended Policy Changes
    print("## Recommended Conversation Policy Changes\n")

    policy_num = 1
    if secrets:
        print(f"{policy_num}. Do not allow secrets in chat. Redirect them to a secure local env file immediately.")
        policy_num += 1

    if scope_drifts:
        print(f"{policy_num}. Cap major sessions by objective, not by elapsed time.")
        policy_num += 1

    if scope_drifts:
        print(f"{policy_num}. Require a scope-reset sentence when the request switches domain.")
        policy_num += 1

    if restart_loops:
        print(f"{policy_num}. Replace repeated startup replies with one canonical runbook.")
        policy_num += 1

    if frustration_lines:
        print(f"{policy_num}. When the user expresses frustration, pause and ask for clarification.")
        policy_num += 1

    if not secrets and not scope_drifts and not restart_loops and not frustration_lines:
        print("1. No major policy changes required based on this analysis.")

    print()

    # Quick Commands
    print("## Quick Commands\n")
    print(f"  python chat_analyze.py toc     {p.name}  # Navigate sessions")
    print(f"  python chat_analyze.py show    {p.name} <LINE>  # Read context around line")
    print(f"  python chat_analyze.py grep    {p.name} \"pattern\"  # Search for patterns")
    print(f"  python chat_analyze.py const   <project_dir>  # Find AGENTS.md")


# ────────────────────────────────────────────────────────────────────────────
# Entry point
# ────────────────────────────────────────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser(
        description="SpecStory chat history analyzer - navigate without reading full files."
    )
    sub = parser.add_subparsers(dest="cmd", required=True)

    p_analyze  = sub.add_parser("analyze",  help="Full analysis report (main output)")
    p_problems = sub.add_parser("problems", help="Checklist of problems with actionable fixes")
    p_toc   = sub.add_parser("toc",     help="Table of contents with line numbers")
    p_stats = sub.add_parser("stats",   help="Aggregated statistics")
    p_show  = sub.add_parser("show",    help="Show context around a line")
    p_grep  = sub.add_parser("grep",    help="Search for a pattern, return line numbers")
    p_tools = sub.add_parser("tools",   help="List all tool calls with line numbers")
    p_think = sub.add_parser("think",   help="List all think blocks with line numbers")
    p_const = sub.add_parser("const",   help="Find constitution/spec/AGENTS files")

    for sp in (p_analyze, p_problems, p_toc, p_stats, p_show, p_grep, p_tools, p_think):
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

    if args.cmd == "analyze":
        cmd_analyze(p, text, lines)
    elif args.cmd == "problems":
        cmd_problems(p, text, lines)
    elif args.cmd == "toc":
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


if __name__ == "__main__":
    main()