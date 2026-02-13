# Skills Catalog

Available skills for Claude Code agents, organized by category.

## Installing Skills

Use the `skills` CLI tool to install skills:

```bash
# Install from GitHub repository
npx skills add vercel-labs/agent-skills --skill <skill-name> -a claude-code -y

# Install to global scope
npx skills add vercel-labs/agent-skills --skill <skill-name> -a claude-code -g -y

# List available skills in a repository
npx skills add vercel-labs/agent-skills --list

# Find skills by keyword
npx skills find <keyword>
```

## Meta Skills

### find-skills

**Source**: vercel-labs/agent-skills
**Description**: Helps discover and install additional skills when the agent needs new capabilities.
**When to Use**: When you need functionality that might exist as an installable skill.

```bash
npx skills add vercel-labs/agent-skills --skill find-skills -a claude-code -y
```

### introspection

**Source**: Your repository (`skills/introspection/SKILL.md`)
**Description**: Reviews sessions and instructions to identify learning opportunities and improve.
**When to Use**: After completing work, when mistakes were made, or to ensure standards compliance.

Already available in your workspace.

### claude-code-pm

**Source**: Your repository (`skills/claude-code-pm/SKILL.md`)
**Description**: Act as a Product Manager managing Claude Code development teams.
**When to Use**: For complex development work requiring managed workflow with quality gates.

This is the current skill.

## Issue Management Skills

### issue-fixer

**Source**: Your repository (`skills/issue-fixer/SKILL.md`)
**Description**: Systematic approach for investigating and fixing bugs with minimal impact.
**When to Use**: Bug reports, test failures, unexpected behavior, or issue fixes.

Already available in your workspace.

## Design & Architecture Skills

### frontend-design

**Source**: vercel-labs/agent-skills (common pattern)
**Description**: Frontend design patterns, UI/UX best practices, component architecture.
**When to Use**: Building UI components, designing user interfaces, frontend architecture.

```bash
npx skills find frontend-design
# Then install the appropriate skill
```

### api-design

**Description**: RESTful API design, GraphQL schema design, API best practices.
**When to Use**: Designing new APIs, refactoring existing endpoints.

```bash
npx skills find api-design
```

### architecture

**Description**: System architecture, design patterns, scalability considerations.
**When to Use**: Designing system architecture, selecting patterns, planning scalability.

```bash
npx skills find architecture
```

### design-patterns

**Description**: Common design patterns (Singleton, Factory, Observer, etc.) and when to use them.
**When to Use**: Implementing complex functionality, refactoring for maintainability.

```bash
npx skills find design-patterns
```

## Development Skills

### code-quality

**Description**: Code quality standards, clean code principles, readability improvements.
**When to Use**: Code reviews, refactoring, ensuring maintainability.

```bash
npx skills find code-quality
```

### testing

**Description**: Testing strategies, unit tests, integration tests, test-driven development.
**When to Use**: Writing tests, improving test coverage, TDD workflows.

```bash
npx skills find testing
```

### e2e-testing

**Description**: End-to-end testing with Playwright, Cypress, or Selenium.
**When to Use**: Full-stack integration testing, user workflow validation.

```bash
npx skills find e2e-testing
```

### refactoring

**Description**: Safe refactoring techniques, code smells identification, incremental improvements.
**When to Use**: Improving code quality, reducing technical debt, simplifying complex code.

```bash
npx skills find refactoring
```

## Specialized Domain Skills

### database-design

**Description**: Database schema design, migrations, query optimization, indexing.
**When to Use**: Working with databases, designing schemas, optimizing queries.

```bash
npx skills find database
```

### devops

**Description**: CI/CD pipelines, containerization, deployment automation, infrastructure.
**When to Use**: Setting up CI/CD, Docker/Kubernetes work, deployment scripts.

```bash
npx skills find devops
```

### security-audit

**Description**: Security vulnerability detection, secure coding practices, OWASP guidelines.
**When to Use**: Security reviews, vulnerability scanning, implementing security features.

```bash
npx skills find security
```

### documentation

**Description**: Technical writing, API documentation, README creation, user guides.
**When to Use**: Writing or improving documentation.

```bash
npx skills find documentation
```

### migration

**Description**: Dependency upgrades, framework migrations, version updates.
**When to Use**: Upgrading packages, migrating to new framework versions.

```bash
npx skills find migration
```

## Language/Framework Specific Skills

### python-best-practices

**Description**: Python-specific best practices, type hints, async patterns, Pythonic code.
**When to Use**: Python development, code reviews.

```bash
npx skills find python
```

### typescript-patterns

**Description**: TypeScript patterns, advanced types, generics, type safety.
**When to Use**: TypeScript development, improving type safety.

```bash
npx skills find typescript
```

### react-patterns

**Description**: React patterns, hooks, state management, component composition.
**When to Use**: React development, component design.

```bash
npx skills find react
```

### fastapi-development

**Description**: FastAPI patterns, async routes, dependency injection, Pydantic models.
**When to Use**: FastAPI backend development.

```bash
npx skills find fastapi
```

## PM-Recommended Skills Combinations

### For Bug Fixes

Install these skills for developer agents working on bug fixes:

```bash
npx skills add vercel-labs/agent-skills --skill issue-fixer -a claude-code -y
npx skills add vercel-labs/agent-skills --skill introspection -a claude-code -y
npx skills add vercel-labs/agent-skills --skill testing -a claude-code -y
```

### For Feature Development

Install these skills for feature development:

```bash
npx skills add vercel-labs/agent-skills --skill code-quality -a claude-code -y
npx skills add vercel-labs/agent-skills --skill testing -a claude-code -y
npx skills add vercel-labs/agent-skills --skill design-patterns -a claude-code -y
npx skills add vercel-labs/agent-skills --skill documentation -a claude-code -y
```

### For Code Reviews

Install these skills for code review agents:

```bash
npx skills add vercel-labs/agent-skills --skill code-quality -a claude-code -y
npx skills add vercel-labs/agent-skills --skill security-audit -a claude-code -y
npx skills add vercel-labs/agent-skills --skill introspection -a claude-code -y
```

### For Full-Stack Development

Install these skills for full-stack work:

```bash
npx skills add vercel-labs/agent-skills --skill frontend-design -a claude-code -y
npx skills add vercel-labs/agent-skills --skill api-design -a claude-code -y
npx skills add vercel-labs/agent-skills --skill database-design -a claude-code -y
npx skills add vercel-labs/agent-skills --skill testing -a claude-code -y
npx skills add vercel-labs/agent-skills --skill e2e-testing -a claude-code -y
```

## Discovering New Skills

### Using find-skills

1. Install the find-skills skill:
```bash
npx skills add vercel-labs/agent-skills --skill find-skills -a claude-code -y
```

2. Let Claude Code agent search for skills:
```bash
claude -p "Use find-skills to discover testing-related skills"
```

### Manual Discovery

Search the skills directory:
```bash
npx skills find <keyword>
```

Browse GitHub repositories:
- https://github.com/vercel-labs/agent-skills
- https://skills.sh/ - Skills directory website

## Creating Custom Skills

If you can't find a skill that fits your needs, create one:

```bash
# Initialize new skill
npx skills init my-custom-skill

# Edit the SKILL.md file
# Add to your repository
# Use it in your agents
```

### Custom Skill Template

```markdown
---
name: my-custom-skill
description: What this skill does and when to use it
tags:
  - category
  - keywords
---

# My Custom Skill

## When to Use

Describe when this skill should be invoked.

## Steps

1. First, do this
2. Then, do that
3. Finally, do this

## Examples

Show examples of using this skill.

## Tips

- Helpful tips
- Best practices
```

## Skill Management for PM Agents

### Install Skills Programmatically

```bash
# Define required skills
REQUIRED_SKILLS=(
  "issue-fixer"
  "introspection"
  "testing"
  "code-quality"
)

# Install each skill
for skill in "${REQUIRED_SKILLS[@]}"; do
  npx skills add vercel-labs/agent-skills --skill "$skill" -a claude-code -y
done
```

### Check Installed Skills

```bash
# List all installed skills
npx skills list

# List for specific agent
npx skills list -a claude-code

# List global skills
npx skills list -g
```

### Update Skills

```bash
# Check for updates
npx skills check

# Update all skills
npx skills update
```

### Remove Skills

```bash
# Remove a skill
npx skills remove <skill-name>

# Remove from specific agent
npx skills remove <skill-name> -a claude-code

# Remove from global scope
npx skills remove <skill-name> --global
```

## Skills Best Practices

1. **Install What You Need**: Don't over-install skills; they add context overhead
2. **Start with Essentials**: issue-fixer, introspection, testing are good defaults
3. **Domain-Specific Skills**: Add skills based on project tech stack
4. **Keep Updated**: Regularly check for skill updates
5. **Document Usage**: Note which skills are used for which agent types
6. **Remove Unused**: Clean up skills that aren't being utilized
7. **Custom Skills**: Create project-specific skills for recurring patterns
8. **Share Skills**: Commit useful skills to your repository for team use

## Skill Scopes

### Project Scope (Default)

Installed to `.claude/skills/` in the project directory:
```bash
npx skills add vercel-labs/agent-skills --skill <skill-name> -a claude-code -y
```

**Shared with team**: Yes (committed to git)
**Available across projects**: No

### Global Scope

Installed to `~/.claude/skills/` in user's home directory:
```bash
npx skills add vercel-labs/agent-skills --skill <skill-name> -a claude-code -g -y
```

**Shared with team**: No
**Available across projects**: Yes

## Integration with PM Workflow

### Phase 2: Planning & Agent Setup

When setting up agents, install required skills:

```bash
cd <target_workspace>

# Install core skills
npx skills add vercel-labs/agent-skills \
  --skill issue-fixer \
  --skill introspection \
  --skill testing \
  -a claude-code -y

# Install domain-specific skills based on workspace analysis
# Example: Python backend
npx skills add vercel-labs/agent-skills \
  --skill python-best-practices \
  -a claude-code -y

# Example: React frontend
npx skills add vercel-labs/agent-skills \
  --skill react-patterns \
  --skill frontend-design \
  -a claude-code -y
```

### Using Skills in Agent Definitions

Reference skills in agent configurations:

```json
{
  "developer": {
    "description": "Senior developer",
    "prompt": "Implement features using best practices",
    "skills": ["issue-fixer", "testing", "code-quality"],
    "model": "sonnet"
  }
}
```

### Dynamic Skill Installation

If an agent needs a skill during execution:

```bash
# PM agent detects need for database skill
claude -p "Use find-skills to discover database migration skills, then install the best match"

# Then continue with task
claude -p --agent developer "Create database migration for user table"
```

## Reference

- **Skills CLI Documentation**: https://github.com/vercel-labs/skills
- **Agent Skills Specification**: https://agentskills.io/
- **Skills Directory**: https://skills.sh/
- **Claude Code Skills Documentation**: https://code.claude.com/docs/en/skills

---

**For PM agents**: Always analyze the target workspace and requirements to determine which skills will be most valuable for the dev agents to have.
