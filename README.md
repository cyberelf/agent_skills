# Agent Skills & Meta-Skills Repository

A centralized repository for maintaining agent skills and meta-skills for software development tasks.


## Skills

This repository includes the following skills under the `skills/` directory. Each skill contains a `SKILL.md` describing its purpose and usage.

- [retrospect](skills/retrospect/SKILL.md) - A meta-skill for self-analysis and improvement of agent capabilities.
- [issue-fixer](skills/issue-fixer/SKILL.md) - A systematic approach for investigating and fixing bugs and issues in the codebase.
- [openspec-constitution-guard](skills/openspec-constitution-guard/SKILL.md) - A skill to compose project AGENTS.md constitution files into openspec commands to enforce quality validation gates.


## Installation

To install all skills from this repository using the `skills` CLI:

```
npx skills add cyberelf/agent_skills
```

To install a specific skill from this repo, use the `-s` option with the skill folder name. Example:

```
npx skills add cyberelf/agent_skills -s issue-fixer
```


## License

MIT License
