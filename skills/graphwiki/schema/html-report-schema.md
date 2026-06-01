# Graphwiki HTML Report Semantic Schema

Use this schema when generating a standalone HTML report from a Graphwiki knowledge base. Follow the report structure, evidence rules, rendering stack, and consistency requirements in this document before writing `report.spec.json` and `index.html`.

Every generated report must include a sibling `report.spec.json` that satisfies the field contract described here.

## 1. Output Scope

- Use this schema only when the selected query mode is `html_report`.
- Write report artifacts only under `output/reports/<report-id>/`.
- Do not write generated reports under `wiki/`, `.graphwiki/`, or `source/`.
- Reports are user-facing deliverables, not canonical graph state and not source evidence.

## 2. Required Deliverables

Every HTML report run must produce:

1. `output/reports/<report-id>/index.html`
2. `output/reports/<report-id>/report.spec.json`
3. Optional supporting assets under the same `output/reports/<report-id>/` directory

## 3. Required `report.spec.json` Contract

The report spec remains a JSON object with this stable top-level shape:

| Field | Required | Type | Rules |
|---|---|---|---|
| `schema_version` | Yes | string | Must be `1.0`. |
| `report_id` | Yes | string | Lowercase slug matching `^[a-z0-9][a-z0-9_-]*$`. |
| `title` | Yes | string | Human-readable report title. |
| `subtitle` | No | string | Optional secondary heading. |
| `audience` | No | string | Target reader or stakeholder group. |
| `query` | Yes | string | Original report request or condensed query. |
| `generated_at` | No | string | ISO date or datetime. |
| `output_dir` | Yes | string | Must match `output/reports/<report-id>` or a child path under `output/reports/`. |
| `source_scope` | No | object | Declares the entity/wiki/source slice used for the report. |
| `sections` | Yes | array | At least one section object. |
| `global_evidence` | No | array | Evidence shared across multiple sections. |
| `assets` | No | array | Emitted files under `output/reports/`. |
| `rendering` | No | object | Rendering preferences and toggles. |

### 3.1 `source_scope`

Use `source_scope` to make report provenance explicit before rendering:

| Field | Type | Rules |
|---|---|---|
| `entity_ids` | array of string | Semantic entities used as anchors for the report. |
| `wiki_pages` | array of string | Paths must start with `wiki/`. These guide synthesis, but are not source evidence. |
| `source_documents` | array of string | Paths must start with `source/`. These are the preferred evidence anchors. |

### 3.2 `sections`

Each section object must include:

| Field | Required | Type | Rules |
|---|---|---|---|
| `id` | Yes | string | Slug matching `^[a-z0-9][a-z0-9_-]*$`. |
| `title` | Yes | string | Section heading shown to the reader. |
| `type` | Yes | string | One of `summary`, `findings`, `comparison`, `timeline`, `entity_profile`, `graph_insight`, `risk`, `recommendations`, `appendix`, `custom`. |
| `purpose` | Yes | string | Why this section exists and what question it answers. |
| `required_entities` | No | array of string | Entities that must be reflected in the rendered section. |
| `body_requirements` | No | array of string | Concrete guidance for what the body must cover. |
| `evidence` | No | array | Section-scoped evidence blocks. |
| `visuals` | No | array | Tables, charts, timelines, graphs, or callouts required by the section. |

### 3.3 `evidence`

Each evidence block must include:

| Field | Required | Type | Rules |
|---|---|---|---|
| `source_document` | Yes | string | Must start with `source/`. |
| `entity_id` | No | string | Semantic entity associated with the claim. |
| `claim` | No | string | Concise claim supported by the cited ranges. |
| `ranges` | Yes | array | One or more line ranges. |

Each range object must include:

| Field | Required | Type | Rules |
|---|---|---|---|
| `start_line` | Yes | integer | 1-based inclusive. |
| `end_line` | Yes | integer | 1-based inclusive, `>= start_line`. |
| `quote` | No | string | Prefer verbatim quote when practical. |
| `confidence` | No | number | Between `0` and `1`. |

### 3.4 `visuals`

Each visual object must include:

| Field | Required | Type | Rules |
|---|---|---|---|
| `id` | Yes | string | Stable identifier within the report. |
| `type` | Yes | string | One of `table`, `chart`, `timeline`, `graph`, `callout`, `custom`. |
| `description` | Yes | string | Reader-facing purpose of the visual. |
| `data_source` | No | string | Data source note for rendering. |

### 3.5 `assets`

Each asset object must include:

| Field | Required | Type | Rules |
|---|---|---|---|
| `path` | Yes | string | Must start with `output/reports/`. |
| `kind` | Yes | string | One of `html`, `css`, `js`, `json`, `image`, `other`. |
| `description` | No | string | Brief purpose of the asset. |

### 3.6 `rendering`

Recognized rendering keys:

| Field | Type | Default | Rules |
|---|---|---|---|
| `entry_file` | string | `index.html` | Main entrypoint file name. |
| `style` | string | none | One of `executive`, `technical`, `audit`, `briefing`, `custom`. |
| `single_file` | boolean | `true` | Prefer one self-contained HTML file when possible. |
| `include_graph_snapshot` | boolean | `true` | Include a graph-oriented visual when it improves comprehension. |
| `include_citations` | boolean | `true` | Load-bearing claims must remain citeable. |

## 4. HTML Rendering Rules

### 4.0 Required Frontend Stack

Use the following stack by default so report output stays visually and structurally consistent across runs:

- Tailwind CSS 3.x via `https://cdn.tailwindcss.com`
- Font Awesome 4.7.0 via `https://cdn.jsdelivr.net/npm/font-awesome@4.7.0/css/all.min.css` when iconography is needed
- Chart.js 4.4.x via `https://cdn.jsdelivr.net/npm/chart.js@4.4.8/dist/chart.umd.min.js` when charts are needed

Do not introduce another CSS framework. If the target environment may be offline, compile the needed Tailwind styles into inline `<style>` blocks while preserving the same utility-driven structure.

Every report should include this Tailwind config unless the main agent explicitly narrows it:

```html
<script>
tailwind.config = {
	theme: {
		extend: {
			colors: {
				'morph-u': '#22c55e',
				'morph-a': '#3b82f6',
				'morph-h': '#f97316',
				'morph-s': '#ef4444',
				'phase-1': '#dbeafe',
				'phase-2': '#93c5fd',
				'phase-3': '#1e40af'
			},
			fontFamily: {
				sans: ['Inter', 'system-ui', '-apple-system', 'sans-serif']
			}
		}
	}
}
</script>
```

Graphwiki should stay as close as possible to the HTML discipline used by the llmwiki workflow, while remaining domain-agnostic.

### 4.1 Required Page Skeleton

Every report must contain these six regions:

1. `<nav>`: sticky top navigation with report title, anchor links, and a print action
2. `<header>`: report cover with title, subtitle or audience, and generation metadata
3. `<main>`: reading guide plus the substantive report body
4. `<section id="data-sources">`: non-optional data-source appendix
5. `<footer>`: Graphwiki/knowledge-base identity plus generation timestamp
6. `<script>`: any inline interaction helpers needed by the page

When the report uses tabs or collapsible cards, the inline script must provide `switchTab(...)` and `toggleCollapse(...)` helpers so interaction patterns remain consistent across reports.

### 4.2 Page-Level Constraints

- Prefer a single standalone HTML file with inline CSS/JS unless the request clearly benefits from separate assets.
- Keep the content area centered and readable on desktop and mobile.
- Include print-friendly styles that hide non-essential controls.
- Support modern Chromium browsers at minimum. Avoid dependencies on a backend service.
- Use Tailwind utility classes as the primary styling mechanism; avoid ad hoc CSS except for print rules, lightweight component polish, or offline Tailwind fallback.
- Preserve a stable visual hierarchy across reports: top navigation, cover, reading guide, section cards, data-source appendix, footer.
- Keep typography, spacing, card treatments, callouts, and citation presentation consistent between reports unless the user explicitly asks for a different style.

### 4.3 Content Structure

At minimum, the main body should include:

1. A short reading guide that states report purpose, audience, and how to interpret the sections.
2. A coverage view that locates the report in the knowledge base. If the domain has a defined matrix or maturity model, render it. Otherwise render an entity/source coverage map, timeline, or graph snapshot.
3. A body organized by the planned `sections` in `report.spec.json`.
4. A data-source appendix whose numbering and labels match the citations used in the main body.

Recommended section patterns by type:

- `summary`: executive overview, key takeaways, or reader briefing
- `findings`: grouped evidence-backed findings and implications
- `comparison`: side-by-side entity or option comparison tables
- `timeline`: chronology, milestones, or roadmap views
- `entity_profile`: deep dive on a named entity or cluster
- `graph_insight`: graph neighborhood, hub analysis, or dependency explanation
- `risk`: threat, weakness, contradiction, or uncertainty analysis
- `recommendations`: evidence-backed actions, decision options, or next steps
- `appendix`: supporting tables, citations, methodology, or unresolved gaps

## 5. Evidence and Citation Discipline

### 5.1 Source Tracking Comment

Before the visible HTML body, maintain an HTML comment that tracks source usage:

```html
<!-- Source Tracking Table
| Ref | Query Theme | Source Path | Title or Node | Key extracted facts |
|-----|-------------|-------------|---------------|---------------------|
| 1 | example | source/example.md | Example Source | Main supporting claim |
-->
```

Every source-backed claim in the report must map to at least one row in this table.

### 5.2 What Counts as Evidence

- Original `source/` files and `.graphwiki/source_views/` are valid evidence roots.
- `wiki/` pages can guide navigation and synthesis, but they are not source evidence.
- If a claim is inferred rather than directly source-backed, mark it as inference or uncertainty.

### 5.3 Citation Requirements

- Every load-bearing claim should cite original source paths and line ranges.
- Prefer inline source labels or footnotes that clearly map to the source tracking table.
- If a section is intentionally context-only or appendix-only, mark it explicitly.

## 6. Governance Rules

- Separate source-backed facts from inference, interpretation, or recommendation.
- Mark unresolved contradictions and missing evidence instead of silently smoothing them over.
- If recommendations are included, state assumptions or applicability boundaries.
- If the knowledge base does not cover a needed claim, state that explicitly in the appendix.
- Do not invent market data, case studies, or source citations.
- Keep both content structure and rendered form as consistent as possible across runs for similar report requests; vary only when the query, evidence, or audience materially requires it.

## 7. Self-Check Before Returning

Do not finalize the report unless all of the following are true:

1. `index.html` exists under `output/reports/<report-id>/`.
2. `report.spec.json` exists and contains all required fields listed in section 3.
3. Every non-appendix section is source-backed or explicitly marked as context-only.
4. `section#data-sources` exists and lists the cited sources.
5. No report files were written under `wiki/`, `.graphwiki/`, or `source/`.