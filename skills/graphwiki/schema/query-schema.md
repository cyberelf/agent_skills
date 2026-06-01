# Graphwiki Query Schema

Use this schema to decide between direct answers and HTML reports, and to understand what each mode must return and which schema documents apply.

## 1. Default Decision Rule

- Default to `question_answer`.
- Switch to `html_report` only when the user clearly asks for a report, briefing, dashboard, audit deliverable, or another shareable HTML artifact.
- If the user's intent is ambiguous, answer directly and mention that a formal HTML report can be generated on request.

## 2. Built-in Query Modes

### 2.1 `question_answer`

| Field | Value |
|---|---|
| Mode id | `question_answer` |
| Label | Question Answering |
| Output kind | `answer` |
| Allow synthesis | Yes |
| Primary schema | `schema/wiki-page.schema.md` |

Use this mode for normal knowledge-base questions, explanation requests, relationship tracing, and source-backed synthesis in chat form.

#### Required workflow

1. Run `query` or `explain` before broad reading.
2. Read the minimum wiki pages and source evidence needed to answer.
3. Return a concise answer with relevant entities, relationships, source paths, and line ranges.
4. Distinguish clearly between source-backed facts and inference or gaps.
5. If the result should become durable knowledge, create a separate `synthesis` patch that follows `schema/wiki-page.schema.md`.

#### Response contract

- Direct answer to the user question
- Relevant entity IDs and labels when they help orientation
- Original source paths and line ranges for load-bearing claims
- Explicit note for missing, stale, or contradictory evidence

### 2.2 `html_report`

| Field | Value |
|---|---|
| Mode id | `html_report` |
| Label | HTML Report Generation |
| Output kind | `html_report` |
| Allow synthesis | No |
| Primary schemas | `schema/query-schema.md`, `schema/html-report-schema.md`, `schema/wiki-page.schema.md` |
| Output directory pattern | `output/reports/<report-id>/` |

Use this mode when the user wants a polished artifact rather than an inline answer.

#### Trigger phrases

Typical triggers include requests such as:

- generate a report
- create an HTML report
- produce a briefing or dashboard
- write an audit output
- make a shareable report

#### Required workflow

1. Query the graph first to identify the relevant entities, wiki pages, and source documents.
2. Draft `report.spec.json` using the field contract in `schema/html-report-schema.md`.
3. Render the report under `output/reports/<report-id>/`.
4. Keep source provenance attached to every load-bearing claim.
5. If durable knowledge is discovered, recommend or create a separate `synthesis` patch instead of treating the report as canonical knowledge.

#### Response contract

- Output paths for generated report files
- Section list or report outline
- Citation/evidence summary
- Unsupported, inferred, or uncertain claims called out explicitly

## 3. Shared Provenance Rules

- `source/` documents and `.graphwiki/source_views/` are the only source evidence roots.
- `wiki/` pages are compiled knowledge and can guide navigation, but they must not be treated as source evidence.
- Reports and answers must separate confirmed facts from interpretation or recommendation.
- If a claim cannot be grounded in the knowledge base, say so plainly.

## 4. Local Extension Rules

Projects may add `.graphwiki/schema/query-schema.md` to narrow or extend the available modes, but local rules must not:

- weaken source provenance requirements
- allow reports to be written outside `output/reports/`
- treat generated wiki pages or reports as source evidence

When local extensions exist, follow the local file in addition to this one.