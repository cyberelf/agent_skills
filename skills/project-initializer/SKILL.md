---
name: project-initializer
description: Helps users scaffold new projects with production-ready files: README.md, AGENTS.md (agent memory), and CI/CD pipelines (GitLab CI, GitHub Actions, or both). Handles tech stack selection, coding standards ingestion, quality level configuration (demo vs. production), and SDD framework integration (OpenSpec, SpecKit, or GSD). Use this skill whenever a user wants to create a new project, initialize a repository, set up CI/CD, choose a spec-driven development workflow, scaffold project files, or asks about project structure and agent memory files. Even if the user only asks about one part (e.g., "set up CI/CD" or "create AGENTS.md"), use this skill — it ensures all files stay consistent with each other.
---

# Project Initializer

A skill for scaffolding new projects with consistent README.md, AGENTS.md, and CI/CD pipelines — all wired together with an SDD (Spec-Driven Development) framework.

## Overview

The skill does five things:

1. **Interview** — Understand the project's goals, tech stack, coding standards, quality requirements, CI platform(s), and preferred SDD workflow.
2. **Generate** — Create README.md, AGENTS.md, and CI pipeline file(s) from templates.
3. **Integrate** — Install SDD framework tools and initialize project structure; wire coding standards and quality checks into the CI pipeline.
4. **Tag** — Embed a machine-readable project identity tag in AGENTS.md so server-side CI can verify the project was properly initialized.
5. **Verify consistency** — Make sure all generated files agree with each other (same tech stack, same quality gates, same SDD expectations).

---

## Phase 1: Interview

Ask the user the following questions. You can ask them all in one message or spread them across a natural conversation — use your judgment based on how much context you already have.

**Required information:**

1. **Project name and one-sentence description** — What is this project? What problem does it solve?

2. **Tech stack** — Language(s), framework(s), package manager, database, deployment target. If they're unsure, suggest sensible defaults based on the problem domain.

3. **Quality level** — Is this a demo/prototype or a production project?
   - *Demo*: minimal CI, no coverage gates, no security scans, lightweight SDD
   - *Production*: full CI, coverage thresholds, security scans, strict SDD alignment checks

4. **SDD framework** — Spec-driven development system the team will use. Present all three options with a brief description:

   | Framework | Style | Best for |
   |-----------|-------|----------|
   | **OpenSpec** | Fluid, brownfield-first, delta specs | Existing codebases, solo devs, iterative work |
   | **SpecKit** | Constitution-enforced, phase-gated | Teams, enterprise, strict quality standards |
   | **GSD** | Phase-based roadmap, context-engineering | Solo devs who want AI to do the heavy lifting |

   > After selection, read the corresponding reference file for detailed knowledge:
   > - OpenSpec → `references/openspec.md`
   > - SpecKit → `references/speckit.md`
   > - GSD → `references/gsd.md`

5. **CI platform** — Which CI system(s) should be configured? Allow selecting one or both:
   - *GitLab CI* — generates `.gitlab-ci.yml`
   - *GitHub Actions* — generates `.github/workflows/ci.yml`
   - *Both* — generates both files, kept consistent with each other

6. **Main branch name** — What branch triggers a release pipeline? (default: `main`)

7. **Coding standards** — Does the team have existing coding standards, a style guide, or a linting config? Options:
   - *Paste content directly* — user pastes the standards into the conversation
   - *File path* — user provides a path to an existing file (e.g., `docs/coding-standards.md`, `.eslintrc.json`)
   - *None* — derive sensible defaults from the tech stack
   
   If provided, read and summarize the standards. They will be injected into AGENTS.md and used to configure CI lint commands.

8. **Additional quality requirements** (for production projects):
   - Minimum test coverage % (e.g., 80%)
   - Static analysis tools (e.g., ESLint, Pylint, SonarQube) — may already be covered by coding standards
   - Security scanning (Trivy, Semgrep, Bandit, etc.)

---

## Phase 2: File Generation

> **CRITICAL — Template Fidelity:** Reproduce every CI pipeline template verbatim. Substitute only the `{{PLACEHOLDER}}` tokens. Do **not** remove, merge, rename, or omit any stages, jobs, or comment blocks. The complete job set in each template is the minimum viable pipeline; dropping any job will break SDD checks, project-tag validation, or coverage gates. For demo projects, dial down strictness through placeholder values (e.g., set `{{COVERAGE_THRESHOLD}}` to `0`, `{{SECURITY_SCAN_CMD}}` to `echo "skipped"`) — never by removing jobs.

After gathering information, generate files. Use the templates in `assets/templates/` as starting points and fill in the placeholders.

**File locations:**
- `README.md` — project root
- `AGENTS.md` — project root
- `.gitlab-ci.yml` — project root (if GitLab CI selected)
- `.github/workflows/ci.yml` — project root (if GitHub Actions selected)

**Placeholder convention** used in templates: `{{VARIABLE_NAME}}`

After creating all files, do a consistency pass:
- The tech stack in README.md must match AGENTS.md and the CI environment images
- Quality gates in CI files must reflect what's specified in AGENTS.md
- The SDD check script path must match the framework chosen
- Both CI files (if both selected) must use the same quality thresholds, check scripts, and branch names

### README.md

Read `assets/templates/README.template.md`. Fill in:
- `{{PROJECT_NAME}}` — project name
- `{{PROJECT_DESCRIPTION}}` — one-paragraph description
- `{{TECH_STACK_LIST}}` — bulleted list of stack components
- `{{SDD_FRAMEWORK}}` — name of chosen SDD framework
- `{{SDD_DOCS_PATH}}` — where SDD documents live (see framework reference)
- `{{GETTING_STARTED_STEPS}}` — installation and run steps appropriate for the tech stack

### AGENTS.md

Read `assets/templates/AGENTS.template.md`. Fill in:
- `{{PROJECT_NAME}}` — project name
- `{{PROJECT_DESCRIPTION}}` — concise single-sentence summary
- `{{TECH_STACK_DETAILS}}` — structured tech stack list with versions if known
- `{{SDD_FRAMEWORK}}` — framework display name (e.g., "OpenSpec")
- `{{SDD_FRAMEWORK_ID}}` — framework lowercase id: `openspec`, `speckit`, or `gsd`
- `{{SDD_WORKFLOW_SUMMARY}}` — 3-5 bullet points describing the team's SDD workflow from the reference doc
- `{{QUALITY_LEVEL}}` — "demo" or "production" (display)
- `{{QUALITY_LEVEL_ID}}` — "demo" or "production" (machine-readable, same as display)
- `{{CI_PLATFORMS_ID}}` — `gitlab`, `github`, or `gitlab,github` (no spaces)
- `{{COVERAGE_THRESHOLD}}` — number (e.g., "80") or "N/A" for demo
- `{{LINT_TOOL}}` — linter/formatter names (from coding standards or tech stack defaults)
- `{{SECURITY_TOOLS}}` — security scan tools or "N/A"
- `{{IGNORE_TAG_DOCS}}` — the git commit ignore tag reference for the chosen framework (see reference docs)
- `{{CODING_STANDARDS_SUMMARY}}` — see Coding Standards Composition section above
- `{{INITIALIZED_DATE}}` — today's date in `YYYY-MM-DD` format
- `{{MAIN_BRANCH}}` — release branch name

**Important**: AGENTS.md is a living document. Keep it minimal at creation time. Agents should append to it during development but never remove existing entries. The initial version is just the skeleton — it will grow.

### Coding Standards Composition

If the user provided coding standards:

1. Read the content (from the pasted text or the file path).
2. Extract the key rules relevant to: naming conventions, file structure, formatting, forbidden patterns, and required patterns.
3. Summarize them into the `## Coding Standards` section of AGENTS.md (concise bullet-point form — the full doc lives separately).
4. If the standards specify a linter/formatter config, reference it in the `{{LINT_CMD}}` for CI (e.g., `eslint --config .eslintrc.json`, `ruff check --config pyproject.toml`).
5. If the user provided a file path, also add a reference to that file in AGENTS.md so agents know where the canonical source is.

If no standards were provided, write a minimal placeholder in the Coding Standards section appropriate for the tech stack (e.g., "Follow PEP 8" for Python, "Follow Airbnb JavaScript Style Guide" for JS).

### .gitlab-ci.yml

Read `assets/templates/gitlab-ci.template.yml`. Fill in:
- `{{DOCKER_IMAGE}}` — appropriate base image for the tech stack
- `{{INSTALL_CMD}}` — dependency install command (e.g., `npm ci`, `pip install -r requirements.txt`)
- `{{LINT_CMD}}` — lint/format check command
- `{{TEST_CMD}}` — test run command
- `{{COVERAGE_CMD}}` — coverage report command
- `{{COVERAGE_THRESHOLD}}` — minimum coverage (skip/set to 0 for demo)
- `{{SECURITY_SCAN_CMD}}` — security scan command or `echo "skipped"` for demo
- `{{SDD_CHECK_SCRIPT}}` — path to framework check script: one of:
  - `scripts/check_sdd_openspec.sh`
  - `scripts/check_sdd_speckit.sh`
  - `scripts/check_sdd_gsd.sh`
- `{{MAIN_BRANCH}}` — release branch name (default: `main`)

Run the install script to copy all required check scripts into the project:

    python assets/install_scripts.py <project_root> --framework <fw>

This installs all three runtime variants (`.sh`, `.ps1`, `.js`) of `check_project_tag` and `check_sdd_<framework>` into `<project_root>/scripts/`. **Do not manually recreate or copy-paste script files** — the install script guarantees the exact asset versions are used without modification. Pass `--dry-run` first to verify what will be copied.

### .github/workflows/ci.yml (if GitHub Actions selected)

Read `assets/templates/github-actions.template.yml`. Fill in the same placeholders as the GitLab template — the values must be identical to ensure both pipelines enforce the same standards.

---

## Phase 3: SDD Framework Installation

After generating files, install the SDD framework tools and initialize the project structure for the chosen framework.

    python assets/initialize_sdd.py <project_root> --framework <fw> [--ai-provider claude]

This script:
- Installs the framework CLI tool (`npm`, `uv`, or `npx` as appropriate)
- Initializes framework-specific directories
- For **OpenSpec**: initializes `openspec/specs/` and `openspec/changes/`
- For **SpecKit**: initializes `specs/` (auto-numbered) and `memory/constitution.md`
- For **GSD**: initializes `.planning/` with PROJECT.md, REQUIREMENTS.md, ROADMAP.md, STATE.md, config.json

Use `--ai-provider` (SpecKit only) to set the AI model (default: `claude`). Supported: claude, gemini, copilot, cursor-agent, windsurf, opencode, codex, qwen, amp, shai, agy, bob, qodercli, roo, codebuddy, jules, kilocode, generic.

Pass `--dry-run` to preview without installing.

### Prerequisites

| Framework | Requires |
|-----------|----------|
| OpenSpec | `npm` (Node.js) |
| SpecKit | `uv` (Python tool installer) + `git` |
| GSD | `npx` + Node.js ≥18 |

If a required tool is not installed, the script will exit with an error message indicating what needs to be installed.

---

## Phase 4: SDD Check Script

The check script reads the latest git commit message and the project's SDD documents. It enforces documentation consistency.

### Ignore Tag System

Agents and developers can place structured tags in commit messages to suppress specific checks:

```
feat: implement user login [ignore:spec_sync]
fix: typo in variable name [ignore:all_sdd]
```

**Universal tags (all frameworks):**

| Tag | What it suppresses |
|-----|-------------------|
| `[ignore:all_sdd]` | All SDD process checks |

**Framework-specific tags** — see the relevant reference file for the complete list. They follow the pattern `[ignore:<check_name>]`.

### When checks fail

The script exits non-zero and prints a message explaining:
1. What was found (e.g., "3 tasks incomplete in openspec/changes/add-auth/tasks.md")
2. What the developer should do (e.g., `Run /opsx:sync add-auth to sync delta specs`)
3. How to suppress the check if appropriate (e.g., `Add [ignore:spec_sync] to commit message if this is a bug fix not tied to a feature`)

---

## Phase 5: Project Identity Tag

Every project initialized by this skill must have a machine-readable identity tag embedded at the top of `AGENTS.md`. This tag allows server-side CI to:
- Confirm the project was properly initialized (not just a hand-crafted AGENTS.md)
- Know which SDD framework and CI platforms are in use
- Enforce version-specific checks appropriate for the project's configuration

The tag takes the form of a structured HTML comment block (the first thing in the file, before any Markdown):

```
<!-- @project-initializer
version: 1
initialized_at: YYYY-MM-DD
sdd_framework: openspec|speckit|gsd
quality_level: demo|production
ci_platforms: gitlab|github|gitlab,github
project_initializer_version: 1.0.0
-->
```

Rules:
- Always place it as the very first content in `AGENTS.md` (before the `#` heading)
- Use the actual initialization date (today)
- `sdd_framework` — lowercase identifier: `openspec`, `speckit`, or `gsd`
- `ci_platforms` — comma-separated, no spaces: `gitlab`, `github`, or `gitlab,github`
- Do not modify this block after creation except through a deliberate re-initialization

The CI check script (`scripts/check_project_tag.sh`) reads this tag and exits non-zero if it is missing or malformed. It is installed automatically by the `install_scripts.py` step described in Phase 2 — `check_project_tag` is always included regardless of the chosen SDD framework. The framework's initialize script (Phase 3) must complete successfully before this tag is validated.

---

## Phase 6: Consistency Verification

After generating all files, perform this checklist:

- [ ] `AGENTS.md` starts with a valid `<!-- @project-initializer` tag
- [ ] `sdd_framework` in tag matches chosen framework
- [ ] `ci_platforms` in tag matches files actually generated
- [ ] Docker/runner image in CI file(s) matches tech stack
- [ ] `AGENTS.md` tech stack section matches `README.md`
- [ ] Coverage threshold in CI file(s) matches `AGENTS.md` → Quality Standards
- [ ] SDD framework name consistent across all generated files
- [ ] The correct SDD check script is referenced (OpenSpec/SpecKit/GSD)
- [ ] Both CI platform files (if both generated) use identical quality thresholds
- [ ] Branch name in CI rules matches the stated main branch
- [ ] SDD framework initialized successfully (Phase 3)
  - OpenSpec: `openspec/specs/` and `openspec/changes/` exist
  - SpecKit: `specs/` and `memory/constitution.md` exist
  - GSD: `.planning/` contains PROJECT.md, REQUIREMENTS.md, ROADMAP.md, STATE.md, config.json
- [ ] `scripts/` directory was populated via `install_scripts.py` (not manually recreated)
- [ ] All three script variants (`.sh`, `.ps1`, `.js`) are present in `scripts/`
- [ ] `.gitlab-ci.yml` (if generated) contains **all** required jobs: `lint`, `unit-tests`, `commit-format`, `full-test-suite`, `coverage-gate`, `security-scan`, `project-tag-check`, `sdd-process-check`, `deploy`
- [ ] `.github/workflows/ci.yml` (if generated) contains **all** required jobs: `lint`, `unit-tests`, `commit-format`, `full-test-suite`, `security-scan`, `project-tag-check`, `sdd-process-check`
- [ ] No jobs were removed or merged compared to the template; only `{{PLACEHOLDER}}` tokens were substituted
- [ ] `AGENTS.md` starts with a valid `<!-- @project-initializer` tag
- [ ] First commit includes: README.md, AGENTS.md, CI files, scripts/, and framework directories

Report any inconsistencies to the user before finishing.

---

## Reference files

- `references/openspec.md` — OpenSpec document structure, sync workflow, ignore tags
- `references/speckit.md` — SpecKit spec lifecycle, constitution, phase gates, ignore tags
- `references/gsd.md` — GSD phase workflow, document set, planning structure, ignore tags

## Installation scripts

- `assets/install_scripts.py` — copies all required check scripts into `<project_root>/scripts/`

  Usage: `python assets/install_scripts.py <project_root> --framework <openspec|speckit|gsd>`

  Always run this instead of manually copying scripts. Add `--dry-run` to preview.

- `assets/initialize_sdd.py` — installs SDD framework tools and initializes project structure

  Usage: `python assets/initialize_sdd.py <project_root> --framework <openspec|speckit|gsd> [--ai-provider claude]`

  Installs the appropriate framework CLI, then sets up directories. For SpecKit, specify the AI provider. Add `--dry-run` to preview.

## Template files

- `assets/templates/README.template.md`
- `assets/templates/AGENTS.template.md`
- `assets/templates/gitlab-ci.template.yml`
- `assets/templates/github-actions.template.yml`

## Check scripts

Each check is available in three runtime variants. Copy **all three variants** of each script into the project's `scripts/` directory — which one gets invoked in CI depends on the runner OS and what's available.

| Script | Shell (Linux/macOS) | PowerShell (Windows/cross-platform) | Node.js (any platform) |
|--------|--------------------|------------------------------------|------------------------|
| Project tag | `check_project_tag.sh` | `check_project_tag.ps1` | `check_project_tag.js` |
| OpenSpec | `check_sdd_openspec.sh` | `check_sdd_openspec.ps1` | `check_sdd_openspec.js` |
| SpecKit | `check_sdd_speckit.sh` | `check_sdd_speckit.ps1` | `check_sdd_speckit.js` |
| GSD | `check_sdd_gsd.sh` | `check_sdd_gsd.ps1` | `check_sdd_gsd.js` |

### Selecting which variant to use in CI

When generating CI pipeline files, choose the invocation command based on the project's runner environment:

| Runner environment | CI invocation |
|--------------------|--------------|
| Linux / macOS (bash available) | `bash scripts/check_sdd_<fw>.sh` |
| Windows (PowerShell 7+ available) | `pwsh scripts/check_sdd_<fw>.ps1` |
| Any (Node.js ≥ 18 available) | `node scripts/check_sdd_<fw>.js` |
| Unknown / mixed | Use Node.js — it works everywhere Node.js is installed |

The Node.js variants are the most portable choice if the runner environment is uncertain. They require no npm dependencies — only the Node.js built-in modules (`fs`, `path`, `child_process`).

The GitLab CI and GitHub Actions templates default to the shell variant. If the user's CI runners are Windows-based or they prefer Node.js, update the `script:` / `run:` lines accordingly. All three variants implement identical logic and exit codes.
````
