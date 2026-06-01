# Graphwiki Sub-Agent Prompts

When the main agent spawns sub-agents to do extraction or query work in parallel, use these prompt templates verbatim (with `{{...}}` placeholders filled in). They encode the patch schema, quote rules, and anti-patterns that caused failures in past runs.

| File | Use when |
|---|---|
| `entity_extractor.md` | Spawning a sub-agent to extract entities from a batch of source documents into a patch JSON. Each sub-agent owns one non-overlapping batch. |
| `query_agent.md` | Spawning a sub-agent to answer a question about the knowledge base and optionally write a `synthesis` patch. |
| `html_report_generator.md` | Spawning a sub-agent to generate a standalone HTML report under `output/reports/<report-id>/` using `schema/html-report-schema.md`. |

## Workflow Pattern (main agent)

1. Decide batching: group source documents by topic/collection, 5–15 docs per batch.
2. For each batch, spawn a sub-agent in parallel using `entity_extractor.md` with placeholders filled. The sub-agent writes one patch JSON to `.graphwiki/patches/batchN_<topic>.json`.
3. **Serial apply** in the main agent: for each completed patch, refresh `base_graph_hash` from the current `graph.json`, then run `apply`. Do not parallelize apply — each apply changes the graph hash.
4. After all patches applied, run `validate-wiki` and inspect `.graphwiki/GRAPH_REPORT.md`.

## Placeholders

These appear in the prompt files and must be filled in by the main agent before sending:

- `{{PROJECT_ROOT}}` — absolute path to the project root
- `{{GRAPH_HASH}}` — current `graph.hash` from `.graphwiki/graph.json`
- `{{ENTITY_TYPES}}` — comma-separated list of configured types (e.g. `concept, synthesis, product, security_risk`)
- `{{BATCH_NAME}}` — human label like "AI Coding Agents & Dev Tools"
- `{{BATCH_ID}}` — slug for `patch_id`, e.g. `batch1-coding-agents`
- `{{SOURCE_DOCUMENT_LIST}}` — bullet list of `source/...` paths for this batch
- `{{OUTPUT_PATH}}` — where the sub-agent writes its patch JSON
- `{{QUESTION}}` (query agent only) — the user question
- `{{SHORT_QUESTION_SLUG}}` (query agent only) — kebab-case slug for synthesis entity id
- `{{REPORT_QUERY}}` (HTML report agent only) — the report topic or user request
- `{{REPORT_ID}}` (HTML report agent only) — stable slug used in `output/reports/<report-id>/`
- `{{AUDIENCE}}` (HTML report agent only) — target reader for tone and section choices
