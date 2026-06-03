---
name: graphwiki
description: Agent-first graph-backed knowledge wiki builder with a self-contained CLI. Use for Graphwiki init/build/ingest/update, source indexing, semantic entity and relationship extraction, generated wiki pages, graph JSON/HTML explorer, evidence line ranges, query/explain question answering, synthesis pages, HTML reports, adding confirmed entity types, applying patches, cleanup, validation, tasks, and SQLite cache generation.
---

# Graphwiki

Graphwiki builds and maintains a graph-backed knowledge wiki without installing a separate package. This skill contains the CLI at `graphwiki.py` and the bundled Python package under `tool/`.

Use this skill when the user asks to initialize, build, ingest, update, query, explain, answer from, report on, clean up, validate, cache, or extend a Graphwiki knowledge base. The user-facing entrypoint is the skill/agent, not the script; `graphwiki.py` is the internal executor that the skill calls after the agent decides what workflow is appropriate.

## Operation Entrypoint

Users should ask the agent for operations such as "initialize this knowledge base", "update changed documents", "extract entities and build wiki pages", "query a concept relationship", or "generate an HTML report". The agent then selects the workflow and internally calls the bundled executor:

```bash
python /path/to/this/skill/graphwiki.py --root <project-root> <command>
```

Do not make the script the user's primary interface. The agent owns skill discovery, path substitution, command selection, and execution.

## Load-Time Repo Guidance

When this skill is loaded, the agent should quickly inspect the current repository state and tell the user what kinds of requests are available:

- If `.graphwiki/graph.json` is missing: suggest requests such as "initialize and build the knowledge base" or "index the documents under `source/`."
- If `source/` exists but the graph has no semantic entities or wiki pages: suggest "extract entities and relationships concurrently and build wiki pages."
- If `.graphwiki/GRAPH_REPORT.md` or `tasks next` shows pending/stale/orphaned/needs_update work: suggest "process pending tasks," "repair stale evidence," or "update affected pages."
- If source documents were added or changed: suggest "run an incremental update and process only changed documents."
- If configured entity types are insufficient: suggest "recommend and confirm new entity types" or "add an entity type and re-scan existing sources."
- If the graph already has semantic entities: suggest "query entity relationships," "explain shortest paths," or "answer from the knowledge graph."
- If the user needs a deliverable: suggest "generate a standalone HTML report."
- If an answer combines multiple sources: suggest "save the answer as a synthesis knowledge page."

## Schema Directory

The `schema/` subdirectory is the semantic extension point for this skill. Read `schema/README.md` before creating or changing semantic outputs.

- `schema/wiki-page.schema.md` defines the richer wiki page structure for entity and synthesis pages.
- `schema/html-report-schema.md` defines the semantic report contract, including the required `report.spec.json` shape used before rendering standalone HTML reports.
- `schema/query-schema.md` defines the built-in query modes and when to use `question_answer` versus `html_report`.

Project-local schema under `.graphwiki/schema/` may narrow these contracts, but it must not weaken source provenance or allow wiki pages to become source evidence.

## Application Scenarios

Graphwiki has four primary application scenarios. Keep them separate when deciding what to do next. All four scenarios rely on the shared rules in `Entity and Relationship Extraction Rules` and `Tool Usage Contract`.

### 1. init: Initial Build and Batch Wiki Construction

Use this when the user starts a new knowledge base or asks for a full first build from an existing `source/` corpus.

1. Confirm the project root and ensure curated raw documents are under `source/`. Do not put generated wiki pages into `source/`.
2. Run `init`, then `build`. This creates deterministic project state: source document nodes, collection nodes, hashes, source views, schemas, reports, graph explorer, and build-time `community_id` assignments. Re-running `build` preserves existing semantic entities, wiki page nodes, relationships, and evidence edges.
3. Read `.graphwiki/entities/schema.json`, `.graphwiki/entities/concept.md`, `.graphwiki/entities/synthesis.md`, and any project-specific entity type docs.
4. Run `entity-types recommend` to get deterministic candidate type suggestions from `source/`. Use the tool question UI to ask the user which suggested types to confirm; only then run `entity-types add ... --confirmed`.
5. Batch the source corpus by collection, document size, or entity type. Use `tasks next` and `tasks claim` when pending actions exist or when multiple subagents can process independent source groups.
6. For each batch, spawn a sub-agent using the `prompts/entity_extractor.md` template. Fill in the `{{...}}` placeholders (project root, graph hash, entity types, batch name, source list, output path). Each sub-agent reads its source documents and writes one patch JSON to `.graphwiki/patches/`.
7. Apply patches serially with `apply`. After each apply, the graph hash changes — always read the current hash from `.graphwiki/graph.json` before applying the next patch. The main agent must not parallelize `apply`.
8. Run `validate-wiki --strict`, inspect `.graphwiki/GRAPH_REPORT.md`, use `stats` to inspect communities and hub nodes, and open `.graphwiki/graph.html` when a visual audit is useful.
9. Finish only when the graph contains semantic entities and wiki pages, not merely source document indexes.

### 2. ingest: Incremental Indexing for Added, Changed, or Deleted Documents

Use this when source documents are added, modified, moved, renamed, or deleted.

1. Run `update` first. This refreshes file hashes, Merkle state, source views, source document nodes, reports, and pending actions while preserving existing semantic nodes.
2. Inspect `.graphwiki/GRAPH_REPORT.md`, `.graphwiki/graph.json` indexes, and `tasks next` to identify new documents, changed documents, stale evidence, orphaned entities, or `needs_update` pages.
3. For added or changed documents, process only the affected source documents unless the report shows a wider dependency. Apply the shared extraction rules to add new entities, merge aliases, update wiki content, and add or revise relationships.
4. For deleted documents, run `cleanup`. Then update affected wiki pages by patch: remove unsupported claims, mark pages `orphaned` when no source evidence remains, or mark `needs_update` when remaining evidence still supports a narrower version.
5. If quote validation fails because line numbers drifted, relocate the same quote in the source document or source view. If relocation fails, mark the affected page or entity as `stale_evidence` and leave an explicit pending item.
6. Apply patches serially, then run `validate-wiki --strict` and inspect the report again. Do not treat `ingest` as finished while source changes have unresolved stale, orphaned, or missing-evidence actions.

### 3. add_entity: Add or Refine an Entity Type

Use this when the user needs a new semantic object type, such as product, component, policy, application, scenario, capability, or decision record.

1. Clarify the type boundary before creating it: purpose, inclusion rules, exclusion rules, examples, counterexamples, expected fields, and relationship names.
2. If the distinction changes extraction behavior or query ergonomics, ask the user to confirm the new type boundary, then run `entity-types add ... --confirmed`. If it does not, use the existing `concept` type instead.
3. Read and refine `.graphwiki/entities/<type>.md` after command generation. Fill in recognition boundaries, examples, counterexamples, fields, and relationship rules so future extraction is consistent.
4. Run `update` if needed so entity config changes queue extraction work across existing source documents.
5. Use `tasks claim` or a scoped source list to extract the new type from existing documents. Apply the shared extraction rules, but only create entities that match the new type boundary.
6. Patch the graph with new typed entities, evidence, wiki pages, and supported relationships. Patches using unknown entity types are rejected by `apply`; do not invent or add entity types during extraction.
7. Run `validate-wiki --strict` and inspect the report for duplicates with existing `concept` pages. Merge or alias duplicates instead of leaving parallel pages for the same thing.

### 4. query: Retrieval, Answering, Synthesis, and Reports

Use this when the user asks a question about the knowledge base.

1. Select a query mode from `schema/query-schema.md`. Use `question_answer` for normal answers and optional synthesis. Use `html_report` when the user asks for a report, dashboard, briefing, audit output, or shareable HTML artifact.
2. Run `query` or `explain` before reading broad files. `query` supports multi-keyword matching, `--match all|any`, `--fuzzy`, `--include-source`, `--semantic-only`, and optional `--traverse bfs|dfs`. Use returned entity IDs, wiki paths, source paths, and line ranges as the navigation plan.
3. Read the minimal necessary wiki pages first, then exact source evidence from `source/` or `.graphwiki/source_views/` when the answer depends on provenance.
4. For relationship questions, use `neighbors <node>` for directly related nodes, `path <source> <target>` for shortest semantic paths, and `stats` for communities, hub nodes, isolated semantic nodes, and graph overview. Query-like commands support `--semantic-only` when source_document/wiki_page/collection nodes must be excluded from resolution or ranking; use `--include-structural` when structural nodes are needed.
5. For `question_answer`, return a concise answer with relevant entities, relationships, source paths, and line ranges. Separate confirmed source-backed facts from inference or gaps.
6. If a `question_answer` result should become reusable knowledge, spawn a sub-agent using `prompts/query_agent.md` (or do it inline) to create a `synthesis` entity and wiki page by patch. The synthesis page must follow `schema/wiki-page.schema.md`.
7. For `html_report`, first draft a report spec that follows `schema/html-report-schema.md`: title, query, audience, source scope, sections, evidence, visuals, rendering options, and the required `report.spec.json` contract. Then render the report under `output/reports/<report-id>/` with `index.html` as the default entry file. Do not write report artifacts under `wiki/` or `.graphwiki/`.
8. HTML reports must cite original source evidence for load-bearing claims. They may summarize wiki pages, but wiki pages are not source evidence.
9. If the report creates durable knowledge that should affect future queries, create a separate `synthesis` patch; do not rely on the HTML report as the canonical knowledge layer.
10. If query reveals missing entities, stale evidence, contradictions, or duplicate pages, either patch the issue immediately or leave explicit pending work in the report-facing workflow.

## Sub-Agent Prompts

When spawning sub-agents for parallel extraction or query work, use the templates in `prompts/`:

- `prompts/entity_extractor.md` — batch entity extraction. Each sub-agent owns one non-overlapping batch of source documents and writes one patch JSON.
- `prompts/query_agent.md` — question answering with optional `synthesis` patch.
- `prompts/html_report_generator.md` — HTML report generation using `schema/html-report-schema.md`, writing only under `output/reports/<report-id>/`.
- `prompts/README.md` — placeholder reference and workflow pattern.

These templates encode the canonical patch schema, quote-matching rules, wiki frontmatter requirements, and known anti-patterns. Use them with the contracts in `schema/` — they exist because freeform prompts produced schema drift and quote mismatches in past runs.

## Entity and Relationship Extraction Rules

These rules are shared by `init`, `ingest`, `add_entity`, and `query` synthesis work.

### Entity Rules

- Use IDs in the form `type:stable-slug`, for example `concept:source-view` or `synthesis:architecture-overview`.
- Use only configured entity types from `.graphwiki/entities/schema.json`. If a candidate suggests a new type, stop and ask for user confirmation; do not add the type or emit patch entities with that type during extraction.
- Keep entities that are durable, reusable, named or clearly bounded, and likely to be queried again. Do not create one entity for every heading, paragraph, transient claim, or source-only summary.
- Every non-draft entity should have at least one `source_document` evidence block with exact `start_line`, `end_line`, and preferably an exact `quote`.
- A good entity definition is short, stable, and source-grounded. Put elaboration, caveats, and examples in the wiki page body.
- Use `aliases` for alternate names, abbreviations, spelling variants, and translated names.
- Merge before creating. Query existing labels and aliases. Update an existing entity when the candidate is the same concept under another name. Add aliases instead of duplicates.
- Use `draft` when the entity is plausible but the evidence boundary is weak. Use `needs_update` when a changed source affects an existing page. Use `stale_evidence` only after evidence no longer validates.

### Relationship Rules

- A relationship edge is a compact graph fact, not prose. Good relation names include `depends_on`, `implements`, `contradicts`, `supersedes`, `part_of`, `uses`, `causes`, or configured project-specific relations.
- Add direct entity-to-entity edges only for durable relationships that are stated or strongly supported by source evidence.
- Do not add relationship edges based only on broad inference. The relationship must be supported by source evidence attached to the related entity or entities and described in the wiki page `## 关系` section.
- Current CLI validation is strict for entity evidence and permissive for free-form edge metadata. Do not rely on edge-only metadata as the sole proof of a relationship.
- Avoid duplicate edges, self-edges, and aliases represented as edges. Use aliases on the entity node for same-thing names.
- When a relationship is important but disputed, record the competing claims in the wiki page and use conservative status or confidence.

### Wiki Page Rules

- Follow `schema/wiki-page.schema.md` when writing `wiki.content` for new or updated pages.
- Each accepted entity should have a wiki page with definition, key facts, relationships, evidence references, and open questions or pending updates. The page should integrate knowledge across sources, not merely summarize one document.
- If `wiki.content` is omitted, `apply` writes a default page template. If `wiki.content` is provided, it must include valid frontmatter and the standard sections because the CLI writes it verbatim.
- Before updating an existing entity, read its current wiki page and preserve useful free-form content. `apply` rewrites the page for every entity included in the patch, so include merged `wiki.content` when changing an existing page.
- Minimal page shape remains frontmatter, H1 title, `## 定义`, `## 关键事实`, `## 关系`, `## 证据引用`, and `## 待更新事项`; the schema adds richer sections such as `## 摘要`, `## 范围与边界`, `## 冲突与不确定性`, and `## 变更记录`.
- Keep claims evidence-grounded. Reference source paths and line ranges in prose when useful, but rely on patch evidence for structured graph references.
- The wiki is the compiled knowledge layer. Never use `wiki/` pages as source evidence; evidence must come from `source/` or its source views.

### Semantic Anti-Patterns

- Running `build` and stopping, leaving only source document nodes with no semantic entities.
- Mixing init, ingest, add_entity, and query into one undifferentiated workflow.
- Creating isolated source summaries with no links to existing concepts, entities, or synthesis pages.
- Duplicating an entity because a new source uses a different label.
- Writing a polished wiki page without structured patch evidence.
- Adding relationships that cannot be traced back to source lines.
- Rewriting an existing wiki page without first preserving user or Agent-maintained content.

### Loader Tolerances (and the limits of relying on them)

`apply` normalizes and repairs common sub-agent mistakes so that one bad quote does not abort the whole patch. Knowing what it tolerates helps you avoid spending tokens on shapes that get rewritten anyway, and knowing the limits keeps you from depending on the tolerance:

- **Entity field aliases**: `name` is accepted as `label`, `summary` as `definition`, and flat `source_documents`/`source_document` lists are converted to the canonical `evidence` array. Still prefer the canonical names — they survive future schema tightening.
- **Quote matching fallbacks**: if `quote` is not a verbatim substring of `lines[start_line-1 : end_line]`, the loader retries by stripping markdown link syntax, then searches a ±20-line window, then falls back to longest-fragment matching. Each repair emits a `warning:` line in the apply output; if all fallbacks fail, the quote is **dropped** (the range is kept). A dropped quote means the entity loses provenance — fix it in the next patch.
- **Wiki frontmatter**: `validate-wiki` accepts both `entity_id: <id>` and `id: <id>` in the page frontmatter. New pages should use `entity_id:` to match the default template.

Tolerances exist for resilience, not as a substitute for reading the source. The sub-agent prompts in `prompts/` describe the canonical shape — follow them.

## Tool Usage Contract

- `build` and `update` are deterministic indexing commands. They do not perform LLM extraction, entity merging, relationship selection, or wiki prose synthesis.
- `build` assigns graph communities deterministically. If `networkx` is installed, it uses networkx modularity communities; otherwise it falls back to connected components while keeping the CLI usable.
- The Agent performs semantic extraction and writes patch JSON. The CLI validates patch shape, configured entity types, source paths, line ranges, quote matches, and then updates graph and wiki artifacts.
- `source/` is the raw document corpus and the only source evidence root. `wiki/` is generated knowledge and must not be used as source evidence.
- `.graphwiki/source_views/` contains stable text views for source documents. Read these when query output points there. Markdown/text line numbers refer directly to source text; PDF/DOCX line numbers refer to the stable source view, with optional original locators in sidecar maps.
- `.graphwiki/source_views/*.map.json` is generated only when a source format has meaningful original locators, such as PDF pages or DOCX paragraphs/table rows.
- `output/reports/<report-id>/` is the only default location for generated HTML reports. Reports are user-facing artifacts, not graph state and not source evidence.
- Use `tasks next` and `tasks claim` to split pending extraction work across subagents. Subagents produce patches; the main agent applies them serially.
- Never edit `.graphwiki/graph.json` directly. Use patch JSON plus `apply`.

## Core Commands

```bash
python graphwiki.py --root . init
python graphwiki.py --root . build
python graphwiki.py --root . update
python graphwiki.py --root . query "term"
python graphwiki.py --root . query "agent feedback" --match all --fuzzy --semantic-only --traverse bfs --depth 2
python graphwiki.py --root . explain "concept:example" --semantic-only
python graphwiki.py --root . neighbors "concept:example" --target-type concept --semantic-only
python graphwiki.py --root . path "concept:a" "concept:b" --semantic-only
python graphwiki.py --root . stats --semantic-only --type concept
python graphwiki.py --root . entity-types list
python graphwiki.py --root . entity-types recommend
python graphwiki.py --root . entity-types add "decision record" --confirmed --description "Architecture decisions with evidence" --field decision --relation supersedes
python graphwiki.py --root . schema patch
python graphwiki.py --root . apply patch.json
python graphwiki.py --root . cleanup
python graphwiki.py --root . validate-wiki
python graphwiki.py --root . validate-wiki --strict
python graphwiki.py --root . sqlite build
```

## Patch Shape

Patches are the only supported way to add semantic entities from Agent work:

```json
{
  "patch_id": "agent-run-001",
  "base_graph_hash": "current graph hash from .graphwiki/graph.json",
  "entities": [
    {
      "id": "concept:example",
      "type": "concept",
      "label": "Example",
      "definition": "Short definition written by the Agent.",
      "evidence": [
        {
          "source_document": "source/example.md",
          "ranges": [
            {
              "start_line": 10,
              "end_line": 14,
              "quote": "Exact text that must appear in that range.",
              "confidence": 1.0
            }
          ]
        }
      ]
    }
  ]
}
```

The CLI validates patch shape, source paths, line ranges, quotes, and configured entity types before writing the graph or wiki page. The generated schema path is `.graphwiki/schemas/patch.schema.json`.

## Output Files

- `.graphwiki/graph.json`: canonical JSON database.
- `.graphwiki/GRAPH_REPORT.md`: Agent audit report and pending actions.
- `.graphwiki/graph.html`: self-contained graph explorer with search, filters, node details, evidence, and pending actions.
- `.graphwiki/schemas/patch.schema.json`: JSON Schema for Agent patches.
- `.graphwiki/sqlite/graphwiki.sqlite`: optional derived query cache.
- `output/reports/<report-id>/index.html`: generated HTML report output for `html_report` query mode.
- `wiki/`: generated entity and synthesis pages.
