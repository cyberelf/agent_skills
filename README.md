# Agent Skills & Meta-Skills Repository

A centralized repository for maintaining agent skills and meta-skills for software development tasks.


## Skills

This repository includes the following skills under the `skills/` directory. Each skill contains a `SKILL.md` describing its purpose and usage.

- [brownfield-onboarding](skills/brownfield-onboarding/SKILL.md)
- [claude-code-pm](skills/claude-code-pm/SKILL.md)
- [deepresearch](skills/deepresearch/SKILL.md)
- [issue-fixer](skills/issue-fixer/SKILL.md)
- [openspec-constitution-guard](skills/openspec-constitution-guard/SKILL.md)
- [polymarket-analyzer](skills/polymarket-analyzer/SKILL.md)
- [project-initializer](skills/project-initializer/SKILL.md)
- [retrospect](skills/retrospect/SKILL.md)
- [session-review](skills/session-review/SKILL.md)


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
