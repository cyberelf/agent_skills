# Claude Code Settings Templates

Configuration templates for different project types and workflows.

## Table of Contents

1. [Basic Settings](#basic-settings)
2. [Permission Configurations](#permission-configurations)
3. [Agent Team Settings](#agent-team-settings)
4. [Project-Specific Settings](#project-specific-settings)
5. [Environment Variables](#environment-variables)

## Basic Settings

### Minimal Settings

`.claude/settings.json`:

```json
{
  "$schema": "https://json.schemastore.org/claude-code-settings.json",
  "permissions": {
    "allow": [
      "Bash(git *)",
      "Read",
      "Edit"
    ],
    "deny": [
      "Read(.env)",
      "Read(secrets/**)"
    ]
  }
}
```

### Standard PM Settings

`.claude/settings.json`:

```json
{
  "$schema": "https://json.schemastore.org/claude-code-settings.json",
  "permissions": {
    "allow": [
      "Bash(git log *)",
      "Bash(git diff *)",
      "Bash(git status)",
      "Bash(npm run lint)",
      "Bash(npm run test *)",
      "Bash(npm run build)",
      "Bash(python -m pytest *)",
      "Bash(python -m pyright *)",
      "Bash(python -m ruff *)",
      "Read",
      "Edit",
      "Write",
      "Glob",
      "Grep"
    ],
    "ask": [
      "Bash(npm install *)",
      "Bash(pip install *)",
      "Bash(git push *)",
      "Bash(git commit *)"
    ],
    "deny": [
      "Read(.env)",
      "Read(.env.*)",
      "Read(secrets/**)",
      "Read(*.key)",
      "Read(*.pem)",
      "Bash(rm -rf *)",
      "Bash(git push --force *)"
    ],
    "defaultMode": "acceptEdits"
  },
  "env": {
    "CLAUDE_CODE_ENABLE_TASKS": "true"
  },
  "attribution": {
    "commit": "🤖 Generated with Claude Code via PM Agent\n\nCo-Authored-By: Claude Code PM <pm@claude-code.ai>",
    "pr": "🤖 Automated development managed by Claude Code PM"
  }
}
```

## Permission Configurations

### Development Mode (Permissive)

For rapid development with trusted team:

```json
{
  "permissions": {
    "allow": [
      "Bash(*)",
      "Read",
      "Edit",
      "Write",
      "Glob",
      "Grep",
      "WebFetch"
    ],
    "deny": [
      "Read(.env)",
      "Read(secrets/**)",
      "Bash(rm -rf /)",
      "Bash(dd *)"
    ],
    "defaultMode": "acceptEdits"
  }
}
```

### Production Mode (Restrictive)

For production environments:

```json
{
  "permissions": {
    "ask": [
      "Bash(*)",
      "Edit",
      "Write"
    ],
    "allow": [
      "Read",
      "Grep",
      "Glob"
    ],
    "deny": [
      "Read(.env)",
      "Read(secrets/**)",
      "Read(config/production.*)",
      "Edit(*.sql)",
      "Bash(git push *)",
      "Bash(docker *)",
      "Bash(kubectl *)"
    ],
    "defaultMode": "plan"
  }
}
```

### Testing Mode

For test-driven development:

```json
{
  "permissions": {
    "allow": [
      "Bash(npm test *)",
      "Bash(npm run test:*)",
      "Bash(pytest *)",
      "Bash(python -m pytest *)",
      "Bash(jest *)",
      "Bash(vitest *)",
      "Read",
      "Edit(tests/**)",
      "Edit(**/*.test.*)",
      "Edit(**/*.spec.*)",
      "Grep",
      "Glob"
    ],
    "ask": [
      "Edit(src/**)",
      "Edit(app/**)"
    ],
    "deny": [
      "Read(.env)",
      "Bash(npm install *)"
    ]
  }
}
```

### Documentation Mode

For documentation work:

```json
{
  "permissions": {
    "allow": [
      "Read",
      "Edit(docs/**)",
      "Edit(*.md)",
      "Edit(README.*)",
      "Write(docs/**)",
      "Grep",
      "Glob"
    ],
    "deny": [
      "Edit(src/**)",
      "Edit(app/**)",
      "Bash(*)"
    ]
  }
}
```

## Agent Team Settings

### Bug Fix Team

`.claude/settings.json`:

```json
{
  "permissions": {
    "allow": [
      "Bash(npm run lint)",
      "Bash(npm test *)",
      "Bash(python -m pytest *)",
      "Bash(python -m pyright *)",
      "Bash(git diff *)",
      "Read",
      "Edit",
      "Grep",
      "Glob"
    ],
    "deny": [
      "Write",
      "Bash(npm install *)",
      "Bash(git push *)"
    ]
  },
  "env": {
    "CLAUDE_CODE_ENABLE_TASKS": "true"
  },
  "attribution": {
    "commit": "🐛 Bug fix via Claude Code PM"
  }
}
```

### Feature Development Team

`.claude/settings.json`:

```json
{
  "permissions": {
    "allow": [
      "Bash(npm run *)",
      "Bash(python -m *)",
      "Bash(git *)",
      "Read",
      "Edit",
      "Write",
      "Grep",
      "Glob"
    ],
    "ask": [
      "Bash(npm install *)",
      "Bash(pip install *)"
    ],
    "deny": [
      "Read(.env)",
      "Read(secrets/**)",
      "Bash(rm -rf *)"
    ],
    "defaultMode": "acceptEdits"
  },
  "attribution": {
    "commit": "✨ Feature implementation via Claude Code PM"
  }
}
```

### Code Review Team

`.claude/settings.json`:

```json
{
  "permissions": {
    "allow": [
      "Read",
      "Grep",
      "Glob",
      "Bash(git log *)",
      "Bash(git diff *)",
      "Bash(npm run lint)",
      "Bash(npm test)"
    ],
    "deny": [
      "Edit",
      "Write",
      "Bash(git commit *)",
      "Bash(git push *)"
    ]
  }
}
```

## Project-Specific Settings

### Python Backend Project

`.claude/settings.json`:

```json
{
  "$schema": "https://json.schemastore.org/claude-code-settings.json",
  "permissions": {
    "allow": [
      "Bash(python -m pytest *)",
      "Bash(python -m pyright *)",
      "Bash(python -m ruff check *)",
      "Bash(python -m ruff format *)",
      "Bash(uv run *)",
      "Bash(poetry run *)",
      "Read",
      "Edit",
      "Grep",
      "Glob"
    ],
    "ask": [
      "Bash(pip install *)",
      "Bash(poetry add *)",
      "Bash(uv add *)",
      "Write"
    ],
    "deny": [
      "Read(.env)",
      "Read(.env.*)",
      "Read(secrets/**)",
      "Read(*.key)",
      "Bash(rm -rf *)"
    ],
    "defaultMode": "acceptEdits"
  },
  "env": {
    "PYTHONPATH": "./src",
    "CLAUDE_CODE_ENABLE_TASKS": "true"
  },
  "attribution": {
    "commit": "🤖 Python development via Claude Code PM"
  }
}
```

### TypeScript/React Frontend Project

`.claude/settings.json`:

```json
{
  "$schema": "https://json.schemastore.org/claude-code-settings.json",
  "permissions": {
    "allow": [
      "Bash(npm run lint)",
      "Bash(npm run type-check)",
      "Bash(npm test *)",
      "Bash(npm run build)",
      "Bash(pnpm run *)",
      "Read",
      "Edit",
      "Grep",
      "Glob"
    ],
    "ask": [
      "Bash(npm install *)",
      "Bash(pnpm add *)",
      "Write"
    ],
    "deny": [
      "Read(.env.local)",
      "Read(.env.production)",
      "Read(secrets/**)",
      "Bash(npm publish *)",
      "Bash(git push --force *)"
    ],
    "defaultMode": "acceptEdits"
  },
  "env": {
    "NODE_ENV": "development",
    "CLAUDE_CODE_ENABLE_TASKS": "true"
  },
  "attribution": {
    "commit": "✨ Frontend development via Claude Code PM"
  }
}
```

### Full-Stack Project

`.claude/settings.json`:

```json
{
  "$schema": "https://json.schemastore.org/claude-code-settings.json",
  "permissions": {
    "allow": [
      "Bash(npm run *)",
      "Bash(pnpm run *)",
      "Bash(python -m pytest *)",
      "Bash(python -m pyright *)",
      "Bash(docker-compose up -d)",
      "Bash(docker-compose down)",
      "Read",
      "Edit",
      "Grep",
      "Glob"
    ],
    "ask": [
      "Bash(npm install *)",
      "Bash(pip install *)",
      "Bash(docker build *)",
      "Write"
    ],
    "deny": [
      "Read(.env)",
      "Read(.env.*)",
      "Read(secrets/**)",
      "Read(backend/.env)",
      "Read(frontend/.env.local)",
      "Bash(rm -rf *)",
      "Bash(kubectl delete *)"
    ],
    "defaultMode": "acceptEdits",
    "additionalDirectories": [
      "../shared-utils",
      "../common-types"
    ]
  },
  "env": {
    "CLAUDE_CODE_ENABLE_TASKS": "true"
  },
  "attribution": {
    "commit": "🤖 Full-stack development via Claude Code PM"
  }
}
```

### Monorepo Project

`.claude/settings.json`:

```json
{
  "$schema": "https://json.schemastore.org/claude-code-settings.json",
  "permissions": {
    "allow": [
      "Bash(pnpm run *)",
      "Bash(nx run *)",
      "Bash(turbo run *)",
      "Bash(lerna run *)",
      "Read",
      "Edit",
      "Grep",
      "Glob"
    ],
    "ask": [
      "Bash(pnpm install *)",
      "Bash(pnpm add *)",
      "Write"
    ],
    "deny": [
      "Read(packages/*/.env*)",
      "Read(apps/*/.env*)",
      "Read(secrets/**)",
      "Bash(rm -rf node_modules)",
      "Bash(pnpm publish *)"
    ],
    "defaultMode": "acceptEdits",
    "additionalDirectories": [
      "./packages/shared",
      "./packages/utils",
      "./packages/types"
    ]
  },
  "attribution": {
    "commit": "🤖 Monorepo development via Claude Code PM"
  }
}
```

## Environment Variables

### Development Environment

`.claude/settings.json`:

```json
{
  "env": {
    "NODE_ENV": "development",
    "CLAUDE_CODE_ENABLE_TASKS": "true",
    "CLAUDE_CODE_EFFORT_LEVEL": "high",
    "DEBUG": "app:*"
  }
}
```

### Testing Environment

`.claude/settings.json`:

```json
{
  "env": {
    "NODE_ENV": "test",
    "CLAUDE_CODE_ENABLE_TASKS": "true",
    "CLAUDE_CODE_EFFORT_LEVEL": "medium",
    "PYTHONPATH": "./src:./tests",
    "TESTING": "true"
  }
}
```

### CI/CD Environment

`.claude/settings.json`:

```json
{
  "env": {
    "CI": "true",
    "CLAUDE_CODE_ENABLE_TASKS": "false",
    "CLAUDE_CODE_DISABLE_NONESSENTIAL_TRAFFIC": "1",
    "CLAUDE_CODE_EXIT_AFTER_STOP_DELAY": "5000"
  }
}
```

## Advanced Settings

### Sandboxing Configuration

For secure execution:

```json
{
  "permissions": {
    "allow": ["Read", "Edit", "Bash(*)"],
    "deny": ["Read(.env)", "Read(secrets/**)"]
  },
  "sandbox": {
    "enabled": true,
    "autoAllowBashIfSandboxed": true,
    "excludedCommands": ["git", "docker"],
    "network": {
      "allowedDomains": ["github.com", "*.npmjs.org", "pypi.org"],
      "allowLocalBinding": true
    }
  }
}
```

### MCP Servers Configuration

For Model Context Protocol integration:

```json
{
  "permissions": {
    "allow": ["Read", "Edit", "MCP(*)"]
  },
  "enableAllProjectMcpServers": true,
  "enabledMcpjsonServers": ["github", "filesystem", "memory"]
}
```

## Settings Inheritance

### User-Level Settings

`~/.claude/settings.json`:

```json
{
  "permissions": {
    "deny": [
      "Read(.env)",
      "Read(secrets/**)",
      "Read(~/.ssh/**)",
      "Read(~/.aws/**)"
    ]
  },
  "env": {
    "CLAUDE_CODE_ENABLE_TASKS": "true"
  }
}
```

### Project-Level Settings (Shared)

`.claude/settings.json`:

```json
{
  "permissions": {
    "allow": [
      "Bash(npm run *)",
      "Read",
      "Edit"
    ]
  },
  "attribution": {
    "commit": "🤖 Generated with Claude Code"
  }
}
```

### Local-Level Settings (Personal)

`.claude/settings.local.json`:

```json
{
  "permissions": {
    "allow": [
      "Bash(echo *)"
    ]
  },
  "env": {
    "DEBUG": "verbose"
  }
}
```

## Template Selector

### Quick Start: Choose Your Template

```bash
# Copy template based on project type
cp templates/python-backend.json .claude/settings.json
cp templates/typescript-frontend.json .claude/settings.json
cp templates/fullstack.json .claude/settings.json
cp templates/monorepo.json .claude/settings.json
```

### PM Agent Template Installation

```bash
# Create PM settings directory
mkdir -p .claude/pm

# Install standard PM settings
cat > .claude/settings.json << 'EOF'
{
  "$schema": "https://json.schemastore.org/claude-code-settings.json",
  "permissions": {
    "allow": [
      "Bash(git *)",
      "Bash(npm run lint)",
      "Bash(npm run test *)",
      "Bash(npm run build)",
      "Bash(python -m pytest *)",
      "Bash(python -m pyright *)",
      "Read",
      "Edit",
      "Write",
      "Glob",
      "Grep"
    ],
    "ask": [
      "Bash(npm install *)",
      "Bash(pip install *)"
    ],
    "deny": [
      "Read(.env)",
      "Read(.env.*)",
      "Read(secrets/**)",
      "Bash(rm -rf *)"
    ],
    "defaultMode": "acceptEdits"
  },
  "env": {
    "CLAUDE_CODE_ENABLE_TASKS": "true"
  },
  "attribution": {
    "commit": "🤖 Generated with Claude Code via PM Agent"
  }
}
EOF

echo "✅ PM settings installed to .claude/settings.json"
```

## Validation

### Validate Settings

```bash
# Check if settings file is valid JSON
cat .claude/settings.json | jq . > /dev/null && echo "✅ Valid JSON" || echo "❌ Invalid JSON"

# Validate against schema
curl -s https://json.schemastore.org/claude-code-settings.json > schema.json
cat .claude/settings.json | jq --argfile schema schema.json -e '. as $data | $schema' > /dev/null
```

## Tips

1. **Start Restrictive**: Begin with deny rules, gradually add allow rules as needed
2. **Use Schema**: Add `$schema` for IDE autocomplete and validation
3. **Environment-Specific**: Use different settings files for dev/test/prod
4. **Gitignore Local**: Always gitignore `.claude/settings.local.json`
5. **Document Decisions**: Add comments (JSON5) or separate docs explaining rules
6. **Test Incrementally**: Test each permission change before committing
7. **Review Regularly**: Audit permissions as project evolves
8. **Use Scopes**: Leverage user/project/local scopes appropriately

## Reference

- **Official Docs**: https://code.claude.com/docs/en/settings
- **JSON Schema**: https://json.schemastore.org/claude-code-settings.json
- **Permission Syntax**: https://code.claude.com/docs/en/permissions

---

**For PM agents**: Always review and customize these templates based on specific project requirements and security policies.
