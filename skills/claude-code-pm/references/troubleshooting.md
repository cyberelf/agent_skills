# Troubleshooting Guide

Common issues and solutions when using the claude-code-pm skill.

## Process Management Issues

### Background Process Not Responding

**Symptoms:**
- No new output in jsonl file
- Process appears stuck
- No progress for extended period

**Diagnosis:**
```bash
# Check if process is still running
ps -p $PID > /dev/null && echo "✓ Running" || echo "✗ Stopped"

# Check recent output
tail -n 50 output.jsonl

# Check for errors
grep -i error output.jsonl | tail -n 10
```

**Solutions:**

1. **If process is truly stuck** (no output for 5+ minutes):
   ```bash
   # Graceful termination
   kill $PID
   
   # Force kill if needed
   kill -9 $PID
   ```

2. **Restart with adjustments**:
   ```bash
   # Increase max-turns or clarify requirements
   claude -p \
     --dangerously-skip-permissions \
     --max-turns 100 \
     --output-format stream-json \
     --verbose \
     "..." > output_retry.jsonl 2>&1 &
   ```

3. **Inform user** and ask if they want to retry or adjust approach.

---

## Execution Issues

### Claude Code Stops Early

**Symptoms:**
- Process exits before all tasks complete
- Tasks.md shows incomplete items
- Exit code 0 but work not finished

**Causes:**
- Insufficient `--max-turns`
- Unclear requirements
- Implicit stopping condition triggered

**Solutions:**

1. **Increase max-turns**:
   ```bash
   # For complex features
   --max-turns 100
   
   # For simple fixes
   --max-turns 50
   ```

2. **Be explicit in prompt**:
   ```bash
   "... then /opsx:verify. Ensure ALL tasks are completed before stopping."
   ```

3. **Refine requirements**:
   - Add more specific acceptance criteria
   - Clarify ambiguous points
   - Provide examples

4. **Continue from where it stopped**:
   ```bash
   claude -p \
     --dangerously-skip-permissions \
     --max-turns 50 \
     --output-format stream-json \
     --verbose \
     "Continue change '<name>'. Complete remaining tasks and run /opsx:verify." \
     > <name>_continue.jsonl 2>&1 &
   ```

---

### Verification Fails

**Symptoms:**
- `/opsx:verify` reports failures
- Tests don't pass
- Tasks.md shows incomplete checkboxes

**Diagnosis:**
```bash
# Review what failed
cat openspec/changes/<name>/tasks.md

# Check verification output in jsonl
grep -A 10 "verify" output.jsonl | tail -n 20
```

**Solutions:**

1. **Run fix iteration**:
   ```bash
   cd <target_workspace>
   
   claude -p \
     --dangerously-skip-permissions \
     --max-turns 30 \
     --output-format stream-json \
     --verbose \
     "Continue change '<name>'. Fix issues from verification. Use /opsx:apply then /opsx:verify." \
     > <name>_fix.jsonl 2>&1 &
   
   PID=$!
   echo "🔄 Started fix iteration (PID: $PID)"
   ```

2. **Review specific failures**:
   - Read tasks.md for unchecked items
   - Check test output
   - Review error messages

3. **Multiple iterations if needed**:
   - First iteration: Address obvious failures
   - Second iteration: Edge cases and polish
   - Final iteration: Comprehensive verification

---

## Configuration Issues

### Skills Not Applied

**Symptoms:**
- Claude Code doesn't follow expected patterns
- Missing features that skills should provide
- Generic output instead of specialized

**Diagnosis:**
```bash
# Check if skills are installed
ls -la .agents/skills/

# Check OpenSpec tools
ls -la .agents/tools/ | grep opsx

# Verify skill content
cat .agents/skills/<skill-name>/SKILL.md
```

**Solutions:**

1. **Reinstall OpenSpec**:
   ```bash
   cd <target_workspace>
   openspec init --tools claude
   ```

2. **Reinstall skills with --agent all**:
   ```bash
   npx skills add cyberelf/agent_skills --skill <skill-name> --agent all -y
   ```

3. **Don't pass custom system prompts**:
   - System prompts override skill context
   - Use skills instead of prompts
   - Let skills provide specialized knowledge

4. **Verify skills are loaded**:
   ```bash
   # Check claude reads skills
   grep -r "SKILL.md" .agents/skills/
   ```

---

### Permission Errors

**Symptoms:**
- Claude Code still asks for permission
- Operations blocked despite flags
- Interactive prompts appear

**Diagnosis:**
```bash
# Check settings
cat .claude/settings.json

# Verify command flags
echo $LAST_COMMAND
```

**Solutions:**

1. **Double-check flag spelling**:
   ```bash
   # Correct (double dash)
   --dangerously-skip-permissions
   
   # Wrong
   -dangerously-skip-permissions
   --dangerous-skip-permissions
   ```

2. **Ensure print mode enabled**:
   ```bash
   # Must have -p flag
   claude -p --dangerously-skip-permissions ...
   ```

3. **Check settings.json**:
   ```bash
   # Look for restricted operations
   cat .claude/settings.json
   
   # Remove restrictions if present
   # Or add to allowlist
   ```

4. **Run with explicit permissions**:
   ```bash
   # If specific operations blocked
   claude -p \
     --dangerously-skip-permissions \
     --allow-all-operations \
     ...
   ```

---

## Output and Monitoring Issues

### Cannot Parse JSON Output

**Symptoms:**
- `jq` commands fail
- Corrupted or incomplete JSON lines
- Mixed text and JSON in output

**Solutions:**

1. **Use stream-json format**:
   ```bash
   --output-format stream-json
   ```

2. **Filter for valid JSON**:
   ```bash
   # Extract only JSON lines
   grep '^{' output.jsonl | jq -r 'select(.type == "stream_event")'
   ```

3. **Parse with error handling**:
   ```bash
   # Ignore invalid lines
   cat output.jsonl | jq -r 'select(.type == "stream_event") .event.delta.text' 2>/dev/null
   ```

---

### Output File Too Large

**Symptoms:**
- JSONL file grows to hundreds of MB
- Slow to read/parse
- Fills disk space

**Solutions:**

1. **Tail recent entries only**:
   ```bash
   tail -n 1000 output.jsonl > recent.jsonl
   ```

2. **Rotate output files**:
   ```bash
   mv output.jsonl output_backup.jsonl
   # Claude Code continues writing to original file handle
   ```

3. **Filter important events**:
   ```bash
   # Extract errors and completions only
   grep -E 'error|warning|completed|verified' output.jsonl > events.jsonl
   ```

4. **Use compression**:
   ```bash
   gzip output.jsonl
   zcat output.jsonl.gz | tail -n 100
   ```

---

## Workflow Issues

### Multiple Concurrent Sessions Conflict

**Symptoms:**
- Git conflicts
- Overlapping file changes
- Output files overwritten

**Solutions:**

1. **Use git worktrees**:
   ```bash
   # Create separate worktree for each task
   git worktree add ../workspace-feature-a feature-a
   git worktree add ../workspace-bugfix-b bugfix-b
   
   # Run Claude Code in each
   cd ../workspace-feature-a
   claude -p ... > feature_a.jsonl 2>&1 &
   
   cd ../workspace-bugfix-b
   claude -p ... > bugfix_b.jsonl 2>&1 &
   ```

2. **Use unique output files**:
   ```bash
   # Include timestamp or change name
   > feature_$(date +%s).jsonl
   > fix_password_$(date +%Y%m%d_%H%M%S).jsonl
   ```

3. **Track PIDs separately**:
   ```bash
   PID_FEATURE_A=$!
   PID_BUGFIX_B=$!
   
   # Monitor each
   ps -p $PID_FEATURE_A
   ps -p $PID_BUGFIX_B
   ```

---

## Common Mistakes

### Mistake: Breaking Work Into Steps

**Wrong:**
```bash
# Step 1
claude -p "Create design"

# Step 2
claude -p "Implement design"

# Step 3
claude -p "Write tests"
```

**Right:**
```bash
# Single command with OpenSpec
claude -p \
  --dangerously-skip-permissions \
  --max-turns 50 \
  "Use /opsx:new <name>, then /opsx:ff, /opsx:apply, /opsx:verify" \
  > output.jsonl 2>&1 &
```

---

### Mistake: PM Making Technical Decisions

**Wrong:**
```markdown
## Requirements
Use React with Redux.
Create components: Header, Sidebar, Dashboard.
API calls via Axios.
```

**Right:**
```markdown
## Requirements
Display user dashboard with navigation.
Must load data from API.
Must be responsive.
```

---

### Mistake: Over-Monitoring

**Wrong:**
```bash
# Checking every 10 seconds
while true; do
  tail -n 5 output.jsonl
  sleep 10
done
```

**Right:**
```bash
# Check once at start, once at end
echo "Started (PID: $PID)"
wait $PID
echo "Completed with exit code $?"
```

---

## Quick Diagnostic Commands

```bash
# Is process running?
ps -p $PID > /dev/null && echo "Running" || echo "Stopped"

# How long has it been running?
ps -p $PID -o etime=

# Recent output (last 20 lines)
tail -n 20 output.jsonl

# Any errors?
grep -i error output.jsonl | tail -n 5

# Parse JSON events
tail -n 100 output.jsonl | jq -r 'select(.type == "stream_event") | .event.delta.text' 2>/dev/null | tail -n 20

# Check exit code
wait $PID
echo $?

# OpenSpec status
cat openspec/changes/<name>/tasks.md | grep -E '\[[ x]\]'
```

---

## Getting Help

If issues persist:

1. **Check recent output**: `tail -n 100 output.jsonl`
2. **Review OpenSpec artifacts**: Especially `tasks.md` and `design.md`
3. **Consult references**: 
   - [CLI Commands](cli-commands.md)
   - [Workflow Details](workflow.md)
   - [Examples](examples.md)
4. **Check OpenSpec docs**: https://github.com/Fission-AI/OpenSpec
5. **Ask user for clarification**: On requirements or priorities
