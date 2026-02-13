# Claude Code Product Manager Skill

Enables AI agents to act as Product Managers, orchestrating Claude Code using the OpenSpec standardized protocol for AI development.

## Overview

This skill transforms an AI agent into a PM who:
- **Gathers requirements** from users (PM's ONLY implementation responsibility)
- **Initiates OpenSpec workflow** with `/opsx:new`
- **Installs proper skills** for the development domain
- **Delegates to Claude Code** in full automation mode
- **Validates completion** using `/opsx:verify`
- **Archives changes** with `/opsx:archive`
- **Hands over** completed work to users

**Key Principle**: PM handles requirements only. Claude Code + OpenSpec handle design and implementation through implicit multi-agent coordination.

## Quick Start

### Installation

Install to your workspace:

```bash
npx skills add <your-repo> --skill claude-code-pm -a claude-code -y
```

### Basic Usage

Invoke the skill when you need managed development work:

```
I need to implement user authentication with login, logout, and password reset features.
Use the claude-code-pm skill to manage this development.
```

The PM agent will:
1. Gather detailed requirements and confirm with you
2. Install OpenSpec and relevant domain skills
3. Create OpenSpec change with `/opsx:new`
4. Delegate to Claude Code in full automation mode
5. Verify completion with `/opsx:verify`
6. Archive with `/opsx:archive`
7. Deliver completed work with summary

**Example command executed by PM:**
```bash
cd <workspace>
npx skills add Fission-AI/OpenSpec --agent all -y
npx skills add cyberelf/agent_skills --skill api-development --agent all -y

claude -p --dangerously-skip-permissions --max-turns 50 \
  "Use /opsx:new user-auth, then /opsx:ff, then /opsx:apply, then /opsx:verify"
```

## Use Cases

### Bug Fixing

**Scenario**: User reports a bug
**PM Actions**: 
- Document bug with reproduction steps and acceptance criteria
- Install OpenSpec + debugging/testing skills
- Create OpenSpec change: `/opsx:new fix-login-bug`
- Delegate: Claude Code autonomously investigates and fixes
- Verify with `/opsx:verify`
- Archive and deliver

### Feature Development

**Scenario**: User requests a new feature
**PM Actions**:
- Gather detailed requirements with acceptance criteria
- Install OpenSpec + domain skills (api-development, ui-development, etc.)
- Create change: `/opsx:new add-user-profile`
- Delegate: Claude Code autonomously plans (proposal → specs → design → tasks) and implements
- Verify completion
- Archive and deliver

### Code Refactoring

**Scenario**: User wants code quality improvements
**PM Actions**:
- Document refactoring goals and constraints
- Install OpenSpec + code-quality skills
- Create change: `/opsx:new refactor-auth-module`
- Delegate: Claude Code analyzes, refactors, validates
- Verify no functionality broken
- Archive and document improvements

## Workflow Phases

### Phase 1: Requirements (PM Only)
- Ask clarifying questions
- Document requirements with acceptance criteria
- Get user confirmation
- **PM does NOT design or implement**

### Phase 2: OpenSpec Setup
- Install OpenSpec skill: `npx skills add Fission-AI/OpenSpec --agent all -y`
- Install domain skills based on project type
- Create OpenSpec change: `claude -p "/opsx:new <change-name>"`
- Write requirements to `requirements.md`

### Phase 3: Autonomous Delegation
- Single command with full automation
- Claude Code runs `/opsx:ff` (proposal → specs → design → tasks)
- Then `/opsx:apply` (implement all tasks)
- Then `/opsx:verify` (validate)
- **PM trusts Claude Code + OpenSpec protocol**

### Phase 4: Validation & Archive
- Review `/opsx:verify` results
- Quick PM spot check (completeness, tests passing)
- Archive: `claude -p "/opsx:archive <change-name>"`

### Phase 5: Handover to User
- Prepare simple summary from OpenSpec artifacts
- Share verification instructions
- Get user feedback
- Handle adjustment requests if needed

## Configuration

### OpenSpec Protocol

The skill uses the OpenSpec standardized protocol:
- **Artifacts**: `openspec/changes/<change-name>/`
- **Commands**: `/opsx:new`, `/opsx:ff`, `/opsx:apply`, `/opsx:verify`, `/opsx:archive`
- **Structure**: proposal.md, specs/, design.md, tasks.md

See [OpenSpec Documentation](https://github.com/Fission-AI/OpenSpec)

### Skills

Instead of custom agent definitions, use skills for context:
- OpenSpec: `npx skills add Fission-AI/OpenSpec --agent all -y`
- Domain skills: `npx skills add cyberelf/agent_skills --skill <name> --agent all -y`
- Claude Code reads skills and self-organizes

See [references/skills-catalog.md](references/skills-catalog.md)

## Reference Documents

### [CLI Commands Reference](references/cli-commands.md)
Complete Claude Code CLI reference with:
- Basic commands and flags
- OpenSpec integration
- Full automation mode
- Output formats
- Common workflows

### [Workflow Guide](references/workflow.md)
Step-by-step procedures:
- Requirements gathering
- OpenSpec setup
- Autonomous delegation
- Validation and archive
- Troubleshooting

### [Skills Catalog](references/skills-catalog.md)
Available skills:
- Installation instructions
- Domain-specific skills
- PM-recommended combinations
- Skill management

## Example Workflows

### Example 1: Quick Bug Fix

```
User: "The login button isn't working"

PM Agent:
1. Gathers info: What happens when clicked? Any error messages?
2. Documents requirements in requirements.md
3. Installs OpenSpec + debugging + testing skills
4. Creates change: /opsx:new fix-login-button
5. Delegates: Claude Code autonomously investigates and fixes
6. Verifies with /opsx:verify
7. Archives and delivers summary
```

### Example 2: Feature Development

```
User: "Add dark mode to the application"

PM Agent:
1. Gathers requirements: Which components? Storage? Default?
2. Documents feature specification with acceptance criteria
3. Installs OpenSpec + ui-development + react-patterns skills
4. Creates change: /opsx:new add-dark-mode
5. Delegates: Claude Code plans (proposal → specs → design → tasks) and implements
6. Verifies completion
7. Archives and delivers
```

### Example 3: Refactoring Project

```
User: "Refactor the authentication system to use JWT tokens"

PM Agent:
1. Gathers requirements and constraints
2. Documents migration plan
3. Installs OpenSpec + api-development + test-automation skills
4. Creates change: /opsx:new jwt-auth-migration
5. Delegates: Claude Code autonomously:
   - Designs new JWT architecture
   - Implements JWT utilities
   - Migrates existing auth
   - Updates tests
   - Updates docs
6. Verifies all existing functionality works
7. Archives and delivers migration guide
```

## CLI Usage Examples

### Basic Feature Development

```bash
cd /path/to/workspace

# Install skills
npx skills add Fission-AI/OpenSpec --agent all -y
npx skills add cyberelf/agent_skills --skill api-development --agent all -y

# Create and execute
claude -p --dangerously-skip-permissions --max-turns 50 \
  "Use /opsx:new user-profile-api, then /opsx:ff, then /opsx:apply, then /opsx:verify"
```

### Bug Fix Workflow

```bash
cd /path/to/workspace

# Install skills
npx skills add Fission-AI/OpenSpec --agent all -y
npx skills add cyberelf/agent_skills --skill debugging --agent all -y

# Execute fix
claude -p --dangerously-skip-permissions --max-turns 30 \
  "Use /opsx:new fix-auth-error, then /opsx:ff, then /opsx:apply, then /opsx:verify"
```

### Archive After Verification

```bash
# Archive completed change
claude -p --dangerously-skip-permissions "/opsx:archive user-profile-api"
```

## Best Practices for PM Agents

1. **Requirements Only**: PM handles only requirements, not design/implementation
2. **OpenSpec Protocol**: Use standardized `/opsx:*` commands
3. **Skills Not Prompts**: Install skills for context, don't pass system prompts
4. **Full Automation**: Use `--dangerously-skip-permissions` for autonomous execution
5. **Trust the Process**: Let Claude Code + OpenSpec handle quality
6. **Clear Acceptance Criteria**: Define measurable success criteria
7. **User Confirmation**: Get explicit approval of requirements
8. **Archive Properly**: Use `/opsx:archive` to finalize changes

## Troubleshooting

### Claude Code Stops Early
- Increase `--max-turns` to 50-100
- Be explicit: "Ensure all tasks are completed"
- Check if waiting for requirements clarity

### Verification Fails
- Review tasks.md for issues
- Run fix iteration with /opsx:apply
- Check test failures

### Skills Not Applied
- Verify: `ls -la .agents/skills/`
- Reinstall with `--agent all` flag
- Don't pass system prompts (they override skills)

### Permission Errors
- Check spelling: `--dangerously-skip-permissions`
- Ensure `-p` print mode enabled
- Check `.claude/settings.json`

## Advanced Features

### Parallel Changes
OpenSpec supports multiple parallel changes in different directories

### Change Archiving
Bulk archive completed changes with `/opsx:archive`

### Skill Composition
Combine multiple domain skills for complex projects

### Custom Verification
Extend `/opsx:verify` with project-specific validation

## Contributing

This skill is part of the agent_skills repository. To improve:
1. Use the introspection skill to learn from PM sessions
2. Document patterns that work well with OpenSpec
3. Share skill combinations that work for different domains
4. Contribute to reference documentation

## License

[Your project's license]

## Support

For issues or questions:
- Review the reference documents
- Check Claude Code documentation: https://code.claude.com/docs
- Review OpenSpec documentation: https://github.com/Fission-AI/OpenSpec
- Review skills documentation: https://github.com/cyberelf/agent_skills

---

**Remember**: As a PM, your job is requirements expertise. Claude Code + OpenSpec + Skills handle the rest. Trust the protocol.
