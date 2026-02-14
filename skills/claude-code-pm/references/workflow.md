# Claude Code PM Workflow Reference

Detailed step-by-step guide using OpenSpec protocol.

## Version

**Current**: v3.0 (OpenSpec Protocol)
- Uses standardized `/opsx:*` commands
- Implicit multi-agent via skills
- No custom agent JSON definitions
- Full automation with `--dangerously-skip-permissions`

## Workflow Overview

```
Requirements → OpenSpec Setup → Delegation → Validation → Archive → Handover
     ↓               ↓              ↓            ↓           ↓         ↓
  Document       Install         Execute      /opsx:      /opsx:    Deliver
   + Confirm     Skills          Claude       verify     archive   Summary
                                 Code
```

## Key Principles

1. **PM = Requirements Expert**: Don't design or implement
2. **OpenSpec = Standard Protocol**: Use `/opsx:*` commands
3. **Skills = Context**: Install skills, don't pass system prompts
4. **Implicit Multi-Agent**: Claude Code self-organizes
5. **Full Automation**: Use `--dangerously-skip-permissions`

## Phase 1: Requirements Gathering

### Step 1.1: Initial Discovery Questions

Ask these questions systematically:

**For Bug Reports:**
- What is the expected behavior?
- What is the actual behavior?
- How can the bug be reproduced?
- What error messages appear (if any)?
- When did this start happening?
- What is the impact (users affected, severity)?
- Are there any workarounds?

**For Features:**
- What problem does this feature solve?
- Who will use this feature?
- What are the success criteria?
- Are there examples or references?
- What constraints exist (performance, security, compatibility)?
- What is out of scope?
- Priority level?

**For Refactoring:**
- What pain points exist currently?
- What improvements are desired?
- What must be preserved?
- What are the risks?
- How is success measured?

### Step 1.2: Create Requirements Document

```bash
cd <target_workspace>

# Create simple requirements file
cat > requirements.md << 'EOF'
# <Task Name>

## Goal
<What needs to be accomplished>

## Acceptance Criteria
- [ ] Criterion 1: Specific, measurable outcome
- [ ] Criterion 2: Specific, measurable outcome
- [ ] Criterion 3: Specific, measurable outcome

## Context
<Important background information>
- Affected components
- Related code locations
- Tech stack details

## Constraints
<What must be preserved or avoided>

## Out of Scope
<What will NOT be included>
EOF
```

**IMPORTANT**: Don't include design decisions or implementation details. That's for Claude Code to decide.

### Step 1.3: User Confirmation

Present to user:
> "I've documented the requirements for [task]. Here's what I understand:
> 
> [Summary of key points]
> 
> Acceptance criteria:
> - Criterion 1
> - Criterion 2
> - Criterion 3
> 
> Does this capture everything correctly? Any additions or corrections?"

Wait for explicit confirmation before proceeding.

## Phase 2: OpenSpec Setup & Skill Installation

### Step 2.1: Install OpenSpec

```bash
cd <target_workspace>

# Install OpenSpec protocol tools
openspec init --tools claude

echo "✅ OpenSpec installed"
```

### Step 2.2: Analyze Project & Identify Skills

```bash
# Check tech stack
if [ -f package.json ]; then
  echo "Node.js/TypeScript project"
  TECH="nodejs"
elif [ -f pyproject.toml ] || [ -f requirements.txt ]; then
  echo "Python project"
  TECH="python"
fi

# Check for framework
if grep -q '"next"' package.json 2>/dev/null; then
  echo "Next.js detected"
  FRAMEWORK="nextjs"
elif grep -q '"react"' package.json 2>/dev/null; then
  echo "React detected"
  FRAMEWORK="react"
elif grep -q 'fastapi' requirements.txt 2>/dev/null; then
  echo "FastAPI detected"
  FRAMEWORK="fastapi"
fi
```

### Step 2.3: Install Domain Skills

Based on project type and task:

**Backend API Tasks:**
```bash
npx skills add cyberelf/agent_skills --skill api-development --agent all -y
npx skills add cyberelf/agent_skills --skill database-design --agent all -y
npx skills add cyberelf/agent_skills --skill test-automation --agent all -y
```

**Frontend Tasks:**
```bash
npx skills add cyberelf/agent_skills --skill ui-development --agent all -y
npx skills add cyberelf/agent_skills --skill react-patterns --agent all -y
npx skills add cyberelf/agent_skills --skill test-automation --agent all -y
```

**Bug Fixing:**
```bash
npx skills add cyberelf/agent_skills --skill debugging --agent all -y
npx skills add cyberelf/agent_skills --skill issue-fixer --agent all -y
npx skills add cyberelf/agent_skills --skill test-automation --agent all -y
```

**Python Projects:**
```bash
npx skills add cyberelf/agent_skills --skill python-best-practices --agent all -y
```

**TypeScript Projects:**
```bash
npx skills add cyberelf/agent_skills --skill typescript-patterns --agent all -y
```

### Step 2.4: Create OpenSpec Change

```bash
cd <target_workspace>

# Create the change
claude -p "/opsx:new <change-name>"

# This creates: openspec/changes/<change-name>/
```

### Step 2.5: Add Requirements to Change

```bash
# Copy requirements to OpenSpec change directory
cp requirements.md openspec/changes/<change-name>/

echo "✅ OpenSpec change created with requirements"
```

## Phase 3: Autonomous Delegation to Claude Code

### Step 3.1: Execute Single Autonomous Command

**Full automation using OpenSpec protocol:**

```bash
cd <target_workspace>

# Execute Claude Code with OpenSpec workflow
claude -p \
  --dangerously-skip-permissions \
  --max-turns 50 \
  --output-format json \
  "Continue the OpenSpec change '<change-name>'. Read requirements from requirements.md. Use /opsx:ff to generate all planning artifacts (proposal, specs, design, tasks), then /opsx:apply to implement all tasks, then /opsx:verify to validate. Ensure all tasks are completed." \
  > output.json

echo "✅ Claude Code execution complete"
```

**What happens autonomously:**
1. Claude Code reads requirements.md
2. `/opsx:ff` generates:
   - proposal.md (what and why)
   - specs/ (detailed requirements)
   - design.md (implementation approach)
   - tasks.md (task breakdown)
3. `/opsx:apply` implements all tasks
4. `/opsx:verify` validates completeness/correctness/coherence

### Step 3.2: Monitor Completion

```bash
# Parse output
SUCCESS=$(cat output.json | jq -r '.success')
RESULT=$(cat output.json | jq -r '.result')

if [ "$SUCCESS" = "true" ]; then
  echo "✅ Claude Code completed successfully"
  echo "Result: $RESULT"
else
  echo "❌ Claude Code encountered issues"
  ERROR=$(cat output.json | jq -r '.error')
  echo "Error: $ERROR"
fi
```

### Step 3.3: Check Artifacts Created

```bash
cd openspec/changes/<change-name>

# Verify all artifacts exist
echo "Checking OpenSpec artifacts..."

[ -f proposal.md ] && echo "✅ proposal.md" || echo "❌ Missing proposal.md"
[ -d specs ] && echo "✅ specs/" || echo "❌ Missing specs/"
[ -f design.md ] && echo "✅ design.md" || echo "❌ Missing design.md"
[ -f tasks.md ] && echo "✅ tasks.md" || echo "❌ Missing tasks.md"

# Check tasks.md for completion
TOTAL_TASKS=$(grep -c "^- \[" tasks.md)
COMPLETED_TASKS=$(grep -c "^- \[x\]" tasks.md)

echo "Tasks: $COMPLETED_TASKS/$TOTAL_TASKS completed"
```

## Phase 4: Validation & Archive

### Step 4.1: Review Verification Results

```bash
cd <target_workspace>

# Check what /opsx:verify reported
cat openspec/changes/<change-name>/tasks.md
```

Look for:
- ✅ All tasks checked off `[x]`
- ✅ Verification notes showing tests passed
- ✅ Implementation matches specs
- ✅ No errors reported

### Step 4.2: PM Spot Check (Quick)

**Minimal validation - trust OpenSpec:**

```bash
# 1. Completeness check
TOTAL=$(grep -c "^- \[" openspec/changes/<change-name>/tasks.md)
DONE=$(grep -c "^- \[x\]" openspec/changes/<change-name>/tasks.md)

if [ "$TOTAL" -eq "$DONE" ]; then
  echo "✅ All tasks complete ($DONE/$TOTAL)"
else
  echo "⚠️ Incomplete: $DONE/$TOTAL tasks"
fi

# 2. Tests check (if applicable)
if [ -f package.json ]; then
  npm test && echo "✅ Tests passing" || echo "❌ Tests failing"
elif [ -f pyproject.toml ]; then
  python -m pytest && echo "✅ Tests passing" || echo "❌ Tests failing"
fi

# 3. Artifacts check
ls -la openspec/changes/<change-name>/
```

**That's it.** Don't do deep code review - OpenSpec handles quality.

### Step 4.3: Archive the Change

```bash
cd <target_workspace>

# Archive using OpenSpec
claude -p \
  --dangerously-skip-permissions \
  "/opsx:archive <change-name>"

echo "✅ Change archived"
```

This will:
- Sync delta specs to main spec repository
- Move to `openspec/changes/archive/<date>-<change-name>/`
- Finalize the change

## Phase 5: Handover to User

### Step 5.1: Prepare Delivery Summary

```bash
cat > delivery_summary.md << 'EOF'
# ✅ Completed: <Change Name>

**Status**: Complete
**OpenSpec Change**: openspec/changes/archive/<date>-<change-name>/

## What Was Done

<1-2 sentence summary from proposal.md>

## Artifacts Created

- ✅ Proposal: What and why
- ✅ Specs: Requirements and scenarios
- ✅ Design: Implementation approach
- ✅ Tasks: All completed (X/X tasks done)
- ✅ Code: Implementation complete
- ✅ Tests: All passing

## How to Verify

```bash
# View change artifacts
cat openspec/changes/archive/<date>-<change-name>/proposal.md

# Run tests
<test command from tasks.md>

# Try it out
<manual testing steps if applicable>
```

## OpenSpec Artifacts

All artifacts in: `openspec/changes/archive/<date>-<change-name>/`

Review:
- `proposal.md` for what and why
- `specs/` for detailed requirements
- `design.md` for implementation approach
- `tasks.md` for completed tasks
EOF
```

### Step 5.2: Present to User

Share with user:

> "✅ **Work Complete: <change-name>**
> 
> Claude Code has completed the work following OpenSpec protocol:
> - All planning artifacts generated (proposal, specs, design, tasks)
> - All tasks implemented
> - Verification passed
> - Change archived
> 
> Artifacts location: `openspec/changes/archive/<date>-<change-name>/`
> 
> <How to verify section>
> 
> Let me know if you need any adjustments!"

### Step 5.3: Handle User Feedback

Wait for response:

**If user approves:**
```
✅ Task complete
PM session successful
```

**If user requests changes:**
```
⚠️ Changes requested
Creating new requirements
Returning to Phase 2 (OpenSpec setup)
Run new iteration with /opsx:ff and /opsx:apply
```

## Troubleshooting

### Issue: Claude Code Stopped Early

**Symptom**: Not all tasks completed

**Solution**:
```bash
# Increase max-turns and be explicit
claude -p --dangerously-skip-permissions --max-turns 100 \
  "Continue change '<name>'. Complete ALL remaining tasks in tasks.md. Use /opsx:apply until EVERY task is checked [x]. Then /opsx:verify."
```

### Issue: Verification Failed

**Symptom**: `/opsx:verify` reports issues

**Solution**:
```bash
# Review issues
cat openspec/changes/<change-name>/tasks.md

# Run fix iteration
claude -p --dangerously-skip-permissions --max-turns 30 \
  "Continue change '<name>'. Fix issues from verification. Use /opsx:apply then /opsx:verify."
```

### Issue: Skills Not Working

**Symptom**: Claude Code doesn't apply domain knowledge

**Solution**:
```bash
# Verify installation
ls -la .agents/skills/

# Reinstall OpenSpec
openspec init --tools claude

# Reinstall other skills
npx skills add cyberelf/agent_skills --skill <skill> --agent all -y
```

### Issue: Permission Errors

**Symptom**: Claude Code asks for permission despite flags

**Solution**:
- Check double-dash: `--dangerously-skip-permissions`
- Ensure `-p` print mode enabled
- Check `.claude/settings.json` doesn't restrict operations

## PM Success Checklist

Before completing task:

```markdown
## PM Final Checklist

### Requirements
- [ ] Requirements documented clearly
- [ ] User confirmed understanding
- [ ] No design/implementation by PM

### OpenSpec Setup
- [ ] OpenSpec skill installed
- [ ] Domain skills installed
- [ ] Change created with /opsx:new

### Delegation
- [ ] Single autonomous command executed
- [ ] --dangerously-skip-permissions used
- [ ] Sufficient --max-turns set (30-50)

### Artifacts
- [ ] proposal.md exists
- [ ] specs/ directory exists
- [ ] design.md exists
- [ ] tasks.md exists with all tasks [x]

### Validation
- [ ] /opsx:verify completed
- [ ] PM spot check done
- [ ] Tests passing (if applicable)

### Archive
- [ ] Change archived with /opsx:archive
- [ ] Artifacts in archive directory

### Handover
- [ ] Summary prepared
- [ ] Verification instructions provided
- [ ] User informed
```

---

**Remember**: PM handles requirements only. OpenSpec + Claude Code + Skills handle everything else. Trust the protocol.
