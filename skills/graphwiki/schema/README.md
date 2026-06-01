# Graphwiki Skill Schemas

This directory is the semantic extension point for the Graphwiki skill. The CLI owns deterministic indexing and patch validation; these schemas tell Agents how to shape higher-level wiki content, query modes, and generated reports.

Read these files before creating semantic wiki pages, synthesis pages, or HTML reports:

| File | Purpose |
|---|---|
| `wiki-page.schema.md` | Markdown/frontmatter contract for generated entity and synthesis pages. |
| `html-report-schema.md` | Markdown semantic schema for HTML reports, including the required `report.spec.json` contract and rendering rules. |
| `query-schema.md` | Markdown query-mode contract for choosing between direct answers and HTML reports. |

Project-specific schema can narrow these rules by adding local docs under `.graphwiki/schema/`, but it must not weaken provenance: source evidence still comes only from `source/` or `.graphwiki/source_views/`. New entity types require an explicitly confirmed type boundary; agents must not add them opportunistically during extraction.