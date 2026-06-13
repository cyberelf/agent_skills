---
name: grill-with-change
description: Stress-test and refine an OpenSpec change through a structured grilling session. Use when the user wants Codex to interrogate, complete, or improve an existing or planned OpenSpec change, maintain a visible problem panorama and progress map, resolve unclear requirements and design decisions one question at a time, and write confirmed decisions back into proposal.md, design.md, specs, and tasks.md.
---

Apply the `grill-with-docs` working mode to an OpenSpec change.

Interview the user relentlessly until the change is coherent across requirements, design, specification deltas, and implementation tasks. Walk the decision tree one branch at a time. Resolve dependencies between decisions before moving on. Write confirmed decisions into the relevant OpenSpec artifacts as they crystallize.

Ask exactly one user-facing question at a time and wait for the answer before continuing. If a structured user-input tool is available, use it; otherwise ask the question in plain text. Include a recommended answer whenever the decision is not obvious.

Do not implement application code while using this skill. Edit OpenSpec artifacts only.

If the user asks a clarifying side question, answer it directly, then return to
the same panorama node unless the answer changes the decision tree. If it does
change the tree, redraw the panorama before the next question.

## Inputs

Accept any of these inputs:

- A change id, such as `add-guard-management-plane`
- A vague reference, such as "this change" or "the current OpenSpec change"
- A design concern, goal, or partial change idea

If the target change is unclear, inspect active changes before asking:

```bash
openspec list --json
```

If exactly one active change exists, use it. If several active changes exist, ask the user which one to grill. If no change exists, ask whether to create a new change or refine a proposed one.

## Inspect First

Before asking product or design questions, inspect what can be discovered locally.

Run:

```bash
openspec status --change "<change-id>" --json
```

Read existing artifacts for the change:

- `openspec/changes/<change-id>/proposal.md`
- `openspec/changes/<change-id>/design.md`
- `openspec/changes/<change-id>/tasks.md`
- `openspec/changes/<change-id>/specs/**/spec.md`

If an expected artifact is missing, get its OpenSpec instructions before creating it:

```bash
openspec instructions <artifact-id> --change "<change-id>" --json
```

Follow returned templates, rules, and context. Do not copy instruction metadata into artifact files.

Also inspect project context that explains the change:

- Existing OpenSpec specs touched by the change
- Project docs or ADRs referenced by the proposal
- Code paths named by tasks or design notes
- Validation commands already used for the affected surfaces

If a question can be answered from these sources, answer it from the sources and continue instead of asking the user.

## Build A Change Map

Create an internal map before grilling:

- Problem statement and desired outcome
- Actors, operators, and affected users
- Scope boundaries and explicit non-goals
- Changed capabilities and requirement deltas
- Concrete scenarios already covered
- Design commitments, alternatives, and trade-offs
- Implementation tasks and validation tasks
- Open questions, contradictions, weak assumptions, and missing failure paths

Prefer a map that exposes dependency order, not just document order. For
agent-platform workflows, map the full path across client skill, MCP helper,
API validation, persisted state, worker/runtime behavior, readiness or status
query, review or execution gate, UI copy, feedback or handoff evidence, and
regression coverage.

## Maintain A Visible Panorama

Before asking the first design or product question, show the user a compact
problem panorama for the change. Keep it simple enough to scan, but complete
enough that the user can see the remaining discussion space.

The panorama must include:

- Current phase: Requirements, Design, Specs, Tasks, or Final Sweep.
- A compact progress bar or fraction, updated as phases or major branches are
  resolved.
- Major branches still to resolve.
- Current branch and question position.
- Known decisions already confirmed.
- Open or risky areas that may change the map.

Use a low-height ASCII map for the normal view. Node labels should be short.
Show a more detailed explanation only the first time, or when the discussion
tree changes materially. On ordinary turns, show only the compact map and the
current node. Include enough progress signal that the user can tell when the
discussion is likely to finish.

```text
Panorama [██░░░] 2/5
[Req] -> [Design] -> [Specs] -> [Tasks] -> [Sweep]
  ^
  Scope
```

Before each user-facing question, briefly mark where the question sits in the
panorama. After each user answer, update the panorama if the answer changes the
discussion tree, scope, order, or unresolved risks.

Also maintain a tasklist or plan for your own progress. Update it as the
grilling session moves through phases so you do not lose track of unresolved
branches. The plan can be internal tool state, a short visible checklist, or
both. Do not let the plan replace the one-question-at-a-time discipline.

When the user asks "how much remains" or appears lost, show the panorama and the
remaining branches before asking the next question.

Look for these defects:

- Terms used inconsistently between proposal, design, specs, and tasks
- Requirements without observable scenarios
- Scenarios that are not supported by requirements
- Tasks that are not justified by requirements or design
- Design decisions without rationale
- Hidden scope expansion inside tasks
- Missing compatibility, migration, rollback, authorization, or failure behavior
- Missing tests or validation commands for the changed surfaces

For interaction contracts, also look for:

- A capability advertised by skills, UI, docs, or helpers before the downstream
  platform path can complete or actionably reject it
- Matrices used as permissive runtime flags instead of release guidance
- Pseudo-states that represent partial implementation rather than real product
  states
- Diagnostic-only evidence routed through formal production objects
- Failure states that hide who can remediate the issue and whether retry,
  re-upload, review, or downstream execution is required

## Grilling Order

### 1. Requirements

Challenge the problem and boundaries first.

Ask about:

- Who the affected user, operator, or system is
- What success looks like
- What behavior changes by default
- What stays backward compatible
- What is explicitly out of scope
- What security, privacy, safety, or governance constraints apply
- What should happen on failure or partial availability

When a requirement is confirmed:

- Update `proposal.md` for problem, scope, impact, or non-goal changes
- Update `specs/<capability>/spec.md` with `ADDED`, `MODIFIED`, or `REMOVED` requirements
- Add concrete scenarios using the repository's OpenSpec scenario style

### 2. Design

Challenge architecture only after the requirement boundary is clear.

Ask about:

- Ownership and source of truth
- Data flow and control flow
- APIs, schemas, and versioning
- State transitions and persistence
- Authorization, confirmation, and audit requirements
- Failure modes and degraded behavior
- Migration, rollback, and compatibility
- Alternatives rejected and why

For workflows that cross agents and platform runtime, ask which boundary owns
truth and which boundary owns remediation. Split states or references when that
distinction changes the correct user action. For example, do not collapse an
ingest failure that requires re-upload with a downstream materialization failure
that requires mapping, review, or worker remediation.

When a design decision is confirmed:

- Update `design.md` immediately
- Record rationale and trade-offs when future readers would otherwise miss the reason
- Reflect behavior changes back into specs
- Add or refine tasks needed to implement the decision
- Validate the change after meaningful write-backs when validation is cheap

### 3. Specs

Validate every changed capability.

For each capability:

- Make requirement names precise and behavior-oriented
- Ensure each requirement has observable scenarios
- Add negative, conflict, and degraded-path scenarios where correctness depends on them
- Keep specs focused on what the system SHALL do, not implementation steps
- Create missing capability spec files only after checking OpenSpec instructions

### 4. Tasks

Finalize tasks after proposal, design, and specs are coherent.

Ensure `tasks.md`:

- Covers every confirmed requirement and scenario that needs implementation
- Orders dependencies clearly
- Includes schema or contract work before consumers
- Includes tests for new behavior, negative paths, and degraded states
- Includes documentation or migration work when needed
- Includes validation commands for the changed surfaces
- Avoids implementation work outside confirmed scope
- Names known residual code, skill, docs, or copy locations when a sweep has
  found them, so implementation does not rely on memory

## Question Discipline

Ask one focused question at a time.

Every question should include:

- The decision that needs confirmation
- Why it matters
- A recommended answer first when a recommendation is defensible
- Concrete alternatives when useful

Prefer this shape:

```text
Which component should own desired guard configuration revisions? This matters because it determines conflict handling and source-of-truth semantics.

Recommended: The guard manager owns desired revisions; defenders own effective validation.
Alternatives: Defenders own both desired and effective revisions; gateway owns desired revisions and pushes them to defenders.
```

Do not ask questions that local inspection can answer. Do not ask several branches in one message.

## Write-Back Rules

Use this mapping when capturing confirmed decisions:

| Decision or finding | Artifact |
| --- | --- |
| Problem, why, outcome, impact, scope, non-goals | `proposal.md` |
| Ownership, architecture, interface choice, rationale, alternatives, migration, rollback | `design.md` |
| Required observable behavior | `specs/<capability>/spec.md` |
| Implementation, tests, docs, migration, validation | `tasks.md` |

Write updates as soon as the decision is confirmed. If the user explicitly defers a blocking answer, record the deferral in the most relevant artifact as an open question or deferred task.

After each write-back, check whether the same decision must also update related
capability specs, concept docs, skill guidance, frontend copy, or validation
tasks. Do not leave a confirmed cross-surface decision captured in only one
artifact.

## Final Sweep

Before finishing:

1. Re-read every changed artifact.
2. Confirm proposal, design, specs, and tasks tell the same story.
3. Run targeted searches for deprecated terms, pseudo-states, removed tools, or
   advertised capabilities that should no longer appear.
4. Run:

   ```bash
   openspec validate "<change-id>"
   openspec status --change "<change-id>"
   ```

5. Fix OpenSpec artifact issues and validate again.

Finish with a concise summary:

- Change id and location
- Artifacts updated
- Key decisions confirmed
- Remaining open questions, if any
- Validation result

Do not call the grilling session complete while unresolved questions still block coherent OpenSpec artifacts.
