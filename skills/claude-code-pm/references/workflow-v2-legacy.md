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

# Install OpenSpec protocol skill
npx skills add Fission-AI/OpenSpec --agent all -y

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
  "debugger": {
    "description": "Expert debugger for investigating and fixing bugs",
    "prompt": "You are an expert debugger. Use the issue-fixer skill systematically: register issue in .issues/opening.md, investigate thoroughly, assess impact, implement minimal fix, validate with tests. Follow all project coding standards.",
    "skills": ["issue-fixer", "introspection"],
    "tools": ["Read", "Edit", "Bash", "Grep", "Glob"],
    "model": "sonnet",
    "maxTurns": 15
  },
  "developer": {
    "description": "Senior developer for feature implementation",
    "prompt": "You are a senior developer. Implement features following project standards. Write tests first (TDD), implement functionality, ensure all tests pass. Add proper error handling and documentation.",
    "skills": ["code-quality", "testing"],
    "tools": ["Read", "Edit", "Write", "Bash", "Grep", "Glob"],
    "model": "sonnet",
    "maxTurns": 25
  },
  "qa": {
    "description": "QA engineer for testing and validation",
    "prompt": "You are a QA engineer. Test thoroughly: run all tests, check coverage, verify edge cases, test error handling. Report all issues found. DO NOT fix issues, only test and report.",
    "skills": ["testing"],
    "tools": ["Read", "Bash", "Grep"],
    "model": "sonnet",
    "maxTurns": 10
  }
}
EOF

echo "✅ Agents configured"
```

## Phase 3: Task Delegation

### Step 3.1: Prepare Task Brief

Create a focused task description:

```markdown
# Task Brief

## Objective
<One-sentence objective>

## Context
<Relevant background from requirements>

## Specific Instructions
1. Read requirements document at .claude/pm/requirements/<file>.md
2. Follow project standards in .github/instructions/
3. <Task-specific guidance>

## Constraints
- Only modify files related to this specific task
- Make minimal necessary changes
- Preserve all existing functionality
- Follow existing code patterns

## Deliverables
- <Specific deliverable 1>
- <Specific deliverable 2>
- All tests passing

## Success Criteria
- <Copy from requirements doc>
```

### Step 3.2: Execute Claude Code CLI

**For Bug Fixes:**
```bash
cd <target_workspace>

# Execute with debugger agent
OUTPUT=$(claude -p \
  --agents "$(cat .claude/pm/agents.json)" \
  --agent debugger \
  --settings .claude/settings.json \
  --append-system-prompt "$(cat .claude/pm/requirements/<requirements-file>.md)" \
  --max-turns 15 \
  --output-format json \
  "Use the issue-fixer skill to fix the bug: <bug description>")

# Save output
echo "$OUTPUT" > .claude/pm/output_debugger_$(date +%Y%m%d_%H%M%S).json

# Check if successful
SUCCESS=$(echo "$OUTPUT" | jq -r '.success')
if [ "$SUCCESS" = "true" ]; then
  echo "✅ Debugger completed successfully"
else
  echo "❌ Debugger encountered issues"
  echo "$OUTPUT" | jq -r '.error'
fi
```

**For Features:**
```bash
cd <target_workspace>

# Phase 1: Design (if complex)
if [ "$COMPLEXITY" = "high" ]; then
  echo "Step 1: Design phase"
  claude -p \
    --agents "$(cat .claude/pm/agents.json)" \
    --agent designer \
    --max-turns 5 \
    --output-format json \
    "Design the architecture for: <feature description>" > design_output.json
fi

# Phase 2: Implementation
echo "Step 2: Implementation phase"
claude -p \
  --agents "$(cat .claude/pm/agents.json)" \
  --agent developer \
  --append-system-prompt "$(cat .claude/pm/requirements/<requirements-file>.md)" \
  --max-turns 25 \
  --output-format json \
  "Implement the feature: <feature description>" > implementation_output.json

# Phase 3: QA
echo "Step 3: QA phase"
claude -p \
  --agents "$(cat .claude/pm/agents.json)" \
  --agent qa \
  --max-turns 10 \
  --output-format json \
  "Test the implementation thoroughly. Run all tests and report any issues." > qa_output.json
```

### Step 3.3: Monitor Execution

```bash
# Monitor output in real-time with streaming
claude -p \
  --output-format stream-json \
  "Task" | while IFS= read -r line; do
  TYPE=$(echo "$line" | jq -r '.type')
  
  case "$TYPE" in
    "start")
      echo "🚀 Task started"
      ;;
    "content")
      TEXT=$(echo "$line" | jq -r '.text')
      echo "💬 $TEXT"
      ;;
    "tool")
      TOOL=$(echo "$line" | jq -r '.tool')
      echo "🔧 Using tool: $TOOL"
      ;;
    "error")
      ERROR=$(echo "$line" | jq -r '.message')
      echo "❌ Error: $ERROR"
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

## Phase 4: Quality Validation

### Step 4.1: Automated Quality Checks

**Backend (Python):**
```bash
cd <target_workspace>

echo "Running quality checks..."

# Type checking
echo "1. Type checking..."
python -m pyright app/ || echo "Type errors found!"

# Linting
echo "2. Linting..."
python -m ruff check app/ || echo "Lint issues found!"

# Tests
echo "3. Running tests..."
python -m pytest tests/ -v || echo "Test failures found!"

# Coverage
echo "4. Checking coverage..."
python -m pytest --cov=app tests/ --cov-report=term

echo "✅ Quality checks complete"
```

**Frontend (TypeScript/JavaScript):**
```bash
cd <target_workspace>

echo "Running quality checks..."

# Type checking
echo "1. Type checking..."
npm run type-check || echo "Type errors found!"

# Linting
echo "2. Linting..."
npm run lint || echo "Lint issues found!"

# Tests
echo "3. Running tests..."
npm test || echo "Test failures found!"

# Build
echo "4. Build check..."
npm run build || echo "Build failed!"

echo "✅ Quality checks complete"
```

### Step 4.2: Manual PM Review

Review checklist:

```markdown
## PM Code Review Checklist

### Scope Adherence
- [ ] Only files related to the task were modified
- [ ] No unrelated refactoring or fixes
- [ ] No unnecessary changes

### Requirements Met
- [ ] All acceptance criteria addressed
- [ ] Feature works as specified
- [ ] Bug is actually fixed

### Code Quality
- [ ] Follows project conventions
- [ ] Appropriate error handling
- [ ] Proper logging where needed
- [ ] Type safety maintained/improved

### Testing
- [ ] Existing tests still pass
- [ ] New tests added for new functionality
- [ ] Edge cases covered
- [ ] Good test coverage

### Documentation
- [ ] Code comments where needed
- [ ] README updated if necessary
- [ ] API docs updated if applicable
- [ ] Docstrings/JSDoc added

### Safety
- [ ] No security vulnerabilities introduced
- [ ] No sensitive data exposed
- [ ] Proper input validation
- [ ] Safe error handling
```

### Step 4.3: Map Deliverables to Criteria

```bash
# Create validation report
cat > .claude/pm/validation_report.md << 'EOF'
# Validation Report

**Task**: <task name>
**Date**: <date>
**PM**: <session id>

## Acceptance Criteria Verification

### Criterion 1: <description>
- **Status**: ✅ Pass / ❌ Fail
- **Evidence**: <where verified, which tests>
- **Notes**: <any observations>

### Criterion 2: <description>
- **Status**: ✅ Pass / ❌ Fail
- **Evidence**: <where verified, which tests>
- **Notes**: <any observations>

### Criterion 3: <description>
- **Status**: ✅ Pass / ❌ Fail
- **Evidence**: <where verified, which tests>
- **Notes**: <any observations>

## Quality Checks

- Type Checking: ✅ 0 errors
- Linting: ✅ 0 issues
- Tests: ✅ 45/45 passing
- Coverage: ✅ 92%
- Build: ✅ Success

## Issues Found

<List any issues, or "None">

## Recommendation

✅ **READY FOR HANDOVER** / ⚠️ **NEEDS ITERATION**

<Justification>
EOF
```

## Phase 5: Iteration & Refinement

### Step 5.1: Compile Feedback

If issues found:

```bash
cat > .claude/pm/feedback.md << 'EOF'
# Developer Feedback

**Iteration**: #1
**Date**: <date>

## Issues to Address

### Issue 1: <Title>
**Severity**: Critical | High | Medium | Low
**Location**: <file:line>
**Problem**: <description>
**Required Fix**: <specific fix needed>
**Acceptance**: <how to verify fix>

### Issue 2: <Title>
**Severity**: Critical | High | Medium | Low
**Location**: <file:line>
**Problem**: <description>
**Required Fix**: <specific fix needed>
**Acceptance**: <how to verify fix>

## Unmet Acceptance Criteria

- [ ] Criterion X: <description of what's missing>
  - Current state: <what exists>
  - Required: <what's needed>
  - How to verify: <test/check>

## Quality Issues

- Type errors: <list>
- Lint issues: <list>
- Test failures: <list>

## Instructions

Address all issues listed above. Make only the necessary changes to fix these specific issues. Do not make unrelated changes. Run tests after each fix.
EOF
```

### Step 5.2: Request Fixes

```bash
cd <target_workspace>

echo "Sending developer back for fixes..."

claude -p \
  --agents "$(cat .claude/pm/agents.json)" \
  --agent developer \
  --append-system-prompt "$(cat .claude/pm/feedback.md)" \
  --max-turns 10 \
  --output-format json \
  "Fix all issues listed in the feedback document" > fix_output.json

SUCCESS=$(cat fix_output.json | jq -r '.success')
if [ "$SUCCESS" = "true" ]; then
  echo "✅ Fixes completed"
else
  echo "❌ Fix attempt failed"
fi
```

### Step 5.3: Re-validate

After fixes, repeat Phase 4 validation:

```bash
# Run quality checks again
./run_quality_checks.sh

# Update validation report
echo "Iteration #2" >> .claude/pm/validation_report.md
# ... check criteria again
```

**Continue iteration until:**
- All acceptance criteria met: ✅
- All tests passing: ✅
- Code quality standards met: ✅
- No blockers remain: ✅

## Phase 6: Final Handover

### Step 6.1: Generate Delivery Summary

```bash
cat > .claude/pm/delivery_summary.md << 'EOF'
# Delivery Summary: <Task Name>

**Completed**: <YYYY-MM-DD HH:MM>
**Duration**: <X hours/days>
**Status**: ✅ Ready for Review
**PM Session**: <session-id>

## Summary

<1-2 paragraph summary of what was delivered>

## Changes Made

### Files Modified
1. `path/to/file1.py` - <brief description of changes>
2. `path/to/file2.ts` - <brief description of changes>
3. `path/to/file3.md` - <brief description of changes>

### Files Added
1. `path/to/newfile1.py` - <brief description>
2. `path/to/newfile2.ts` - <brief description>

### Files Deleted
1. `path/to/oldfile.py` - <reason for deletion>

## Quality Metrics

### Test Results
- ✅ Unit Tests: 45/45 passing
- ✅ Integration Tests: 12/12 passing
- ✅ E2E Tests: 5/5 passing
- ✅ Total: 62/62 passing

### Code Quality
- ✅ Type Checking: 0 errors
- ✅ Linting: 0 issues
- ✅ Code Coverage: 92% (target: 80%)
- ✅ Build: Success

### Performance
- API response time: <X ms> (target: <Y ms>)
- Bundle size: <X KB> (target: <Y KB>)

## Acceptance Criteria

- [x] **Criterion 1**: <description>
  - Verified in: <location>
  - Test coverage: <test name>
  
- [x] **Criterion 2**: <description>
  - Verified in: <location>
  - Test coverage: <test name>
  
- [x] **Criterion 3**: <description>
  - Verified in: <location>
  - Test coverage: <test name>

## How to Verify

### Manual Testing
\`\`\`bash
# Start the application
npm run dev  # or python -m uvicorn app.main:app --reload

# Navigate to:
# http://localhost:3000/<relevant-page>

# Test the following:
1. <Test step 1>
2. <Test step 2>
3. <Test step 3>
\`\`\`

### Automated Testing
\`\`\`bash
# Run all tests
npm test  # or python -m pytest

# Run specific test suite
npm test -- <test-file>  # or python -m pytest tests/<test-file>
\`\`\`

## Technical Notes

### Implementation Decisions
- **Decision 1**: <what> - <why>
- **Decision 2**: <what> - <why>

### Known Limitations
- <Limitation 1> - <why>
- <Limitation 2> - <why>

### Trade-offs Made
- <Trade-off 1>: Chose X over Y because <reason>
- <Trade-off 2>: Chose X over Y because <reason>

## Documentation Updates

- ✅ README.md updated
- ✅ API documentation updated
- ✅ Code comments added
- ✅ Docstrings completed

## Next Steps (Optional)

### Immediate Follow-ups
- None required

### Future Enhancements
- <Enhancement 1>: <description>
- <Enhancement 2>: <description>

### Potential Improvements
- <Improvement 1>: <description>
- <Improvement 2>: <description>

## PM Notes

<Any additional context, learnings, or observations for future reference>

---

**Delivered by**: Claude Code PM Agent
**Reviewed by**: <PM session>
**Approved by**: <Awaiting user approval>
EOF
```

### Step 6.2: Present to User

Format for user:

> "🎉 **Task Complete: [Task Name]**
> 
> I've completed the work and validated everything thoroughly. Here's what was delivered:
> 
> **Summary:**
> <Brief overview>
> 
> **Quality Metrics:**
> - ✅ All tests passing (62/62)
> - ✅ Code coverage: 92%
> - ✅ No type/lint errors
> 
> **Acceptance Criteria:**
> - ✅ Criterion 1
> - ✅ Criterion 2
> - ✅ Criterion 3
> 
> **How to verify:**
> ```bash
> npm test  # Run tests
> npm run dev  # Test manually at http://localhost:3000
> ```
> 
> Full delivery summary is in `.claude/pm/delivery_summary.md`
> 
> Please review and let me know if you'd like any adjustments!"

### Step 6.3: Archive Project Artifacts

```bash
# Create archive directory
TIMESTAMP=$(date +%Y%m%d_%H%M%S)
TASK_NAME="<short-task-name>"
ARCHIVE_DIR=".claude/pm/archive/${TIMESTAMP}_${TASK_NAME}"
mkdir -p "$ARCHIVE_DIR"

# Archive files
cp .claude/pm/requirements/*.md "$ARCHIVE_DIR/"
cp .claude/pm/agents.json "$ARCHIVE_DIR/"
cp .claude/pm/validation_report.md "$ARCHIVE_DIR/"
cp .claude/pm/delivery_summary.md "$ARCHIVE_DIR/"
cp .claude/pm/feedback.md "$ARCHIVE_DIR/" 2>/dev/null || true
cp .claude/pm/output_*.json "$ARCHIVE_DIR/" 2>/dev/null || true

# Clean up working files
rm -f .claude/pm/requirements/*.md
rm -f .claude/pm/feedback.md
rm -f .claude/pm/validation_report.md
rm -f .claude/pm/output_*.json

echo "✅ Artifacts archived to $ARCHIVE_DIR"
```

### Step 6.4: Get User Acceptance

Wait for user response:

**If approved:**
```
✅ Task accepted by user
Archive complete: .claude/pm/archive/<timestamp>_<task>
PM session successful
```

**If changes requested:**
```
⚠️ User requested changes
Creating new feedback document
Returning to Phase 5: Iteration
```

## PM Success Checklist

Before marking task complete:

```markdown
## PM Final Checklist

### Requirements
- [ ] All acceptance criteria met
- [ ] User confirmed requirements understood correctly
- [ ] Scope maintained (no scope creep)

### Quality
- [ ] All automated tests pass
- [ ] Code quality checks pass
- [ ] Manual review completed
- [ ] No regressions introduced

### Documentation
- [ ] Requirements documented
- [ ] Changes documented
- [ ] Delivery summary prepared
- [ ] Technical notes added

### Communication
- [ ] User kept informed throughout
- [ ] Delivery summary presented clearly
- [ ] Verification instructions provided
- [ ] User given opportunity to review

### Artifacts
- [ ] Requirements saved
- [ ] Agent configs saved
- [ ] Validation reports saved
- [ ] Artifacts archived properly

### Handover
- [ ] Clear how-to-verify instructions
- [ ] Known limitations documented
- [ ] Next steps identified
- [ ] User approval received
```

---

**Remember**: The PM's job is complete delivery with quality assurance. Follow this workflow systematically for consistent, reliable results.
