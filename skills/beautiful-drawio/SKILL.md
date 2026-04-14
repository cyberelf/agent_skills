---
name: beautiful-drawio
description: 'Create high-quality draw.io diagrams with better layout for architecture diagrams, flowcharts, block diagrams, system maps, data flows, and complex connection-heavy visuals. Use when draw.io routing becomes messy, edges overlap, blocks cross too much, or the user wants cleaner diagram layout than the default drawio skill.'
argument-hint: 'Describe the diagram type, key nodes, and whether topology or content density matters more.'
---

# Beautiful Draw.io

Create native `.drawio` diagrams with a layout-first workflow designed for dense block diagrams, architecture maps, and connection-heavy systems.

This skill exists because the baseline `drawio` workflow focuses on XML generation and export, while high-quality diagrams require an explicit layout pass before any mxGraph XML is written.

For complex diagrams, do not rely on natural-language layout instructions alone. The preferred path is now a typed JSON specification plus either an ELK-backed layout engine or a structured row/column packer, so the agent describes structure, hierarchy, and sibling order rather than hand-authoring absolute coordinates.

## When To Use

- The user asks for `.drawio` output but wants the visual quality closer to a Mermaid/ELK layout.
- The diagram has many edges, cross-domain links, or layered blocks.
- The user explicitly complains about overlapping edges, node collisions, or too many crossings.
- The diagram is a system architecture, block diagram, deployment map, data flow, security boundary diagram, or multi-lane flowchart.

## Core Difference From The Default Drawio Skill

- Default `drawio`: write mxGraph XML directly, then adjust routing ad hoc.
- `beautiful-drawio`: design topology first, reduce crossings before placement, route edges by lane and hierarchy, then emit mxGraph XML.
- Default `drawio`: treats layout as a side effect of coordinates.
- `beautiful-drawio`: treats layout as a first-class design step.

## Workflow

### 0. Use the typed JSON pipeline for dense diagrams

If the diagram has more than a handful of nodes or any nontrivial crossing pressure, use the structured pipeline:

1. The agent chooses a diagram type such as `product-block`, `technical-architecture`, `data-flow`, or `deployment`.
2. The agent supplies nodes, containers, parent-child hierarchy, and sibling order in JSON.
3. The agent does not supply absolute coordinates unless preserving a partially fixed legacy diagram.
4. Run [ELK layout script](./scripts/elk_layout_to_drawio.mjs).
5. Let the script generate optimized coordinates and draw.io XML.
6. Only do manual edits after the script output if a small visual adjustment is still needed.

Load the [JSON contract](./references/layout-json-contract.md) before creating the input.

### 1. Classify the diagram before drawing

Choose one primary layout model:

- Layered flow: pipelines, request paths, control chains
- Bounded architecture: domains, subgraphs, zones, trust boundaries
- Hub-and-spoke: one central orchestrator with many integrations
- Split deployment: demo vs production, current vs target, left vs right comparison
- Matrix/block layout: products vs capabilities, layers vs environments

If the diagram mixes multiple models, pick one dominant topology and demote the others to annotations or secondary edges.

### 2. Reduce the graph before placement

Before writing XML, normalize the content:

- Merge duplicate concepts that only differ in wording.
- Remove decorative nodes that do not change control flow.
- Collapse repeated low-value edges into one gateway or one labeled bus.
- Separate primary path edges from audit, sync, or optional edges.
- Prefer one edge from a container to another container over many parallel leaf-to-leaf edges when the detail is not essential.

If the diagram still feels dense after reduction, split it into two pages or two diagrams instead of forcing everything onto one canvas.

### 3. Use Mermaid as a topology sketch only when needed

For diagrams with any of the following:

- More than 8-10 meaningful nodes
- More than 10 edges
- Multiple subgraphs or trust boundaries
- Bidirectional or cross-lane connections

First draft the topology in Mermaid using `flowchart TD` and `layout: 'elk'` only if it helps the agent reason about clusters or dependencies. Then convert that topology into the typed JSON contract for the ELK script.

Why:

- Mermaid ELK is better than manual coordinate guessing at minimizing crossings.
- A quick Mermaid topology reveals which nodes belong in the same lane or cluster.
- The resulting structure can be translated into draw.io containers and orthogonal edges.

Use Mermaid only as an internal planning step unless the user explicitly asks for Mermaid output too.

### 4. Place blocks with container discipline

Use containers for every major boundary:

- Domain
- Trust zone
- Layer
- Deployment environment
- Time horizon

Rules:

- Containers own structure; edges should mostly flow between containers, not randomly through them.
- Child nodes use consistent spacing inside their container.
- Keep 40-80px internal padding on containers.
- Do not overlap containers visually or semantically.
- Keep a single reading direction per page: usually top-down for complex flows, left-right only for short linear sequences.

### 5. Route edges by class, not one-by-one improvisation

Separate edges into classes and style them consistently:

- Primary path: solid, darker, shortest readable route
- Control plane: solid but lighter or secondary accent
- Audit/telemetry/sync: dashed and visually recessed
- Optional or future path: dashed or dotted with clear label

Routing rules:

- Default to `edgeStyle=orthogonalEdgeStyle`.
- Reserve edge corridors between columns and rows.
- Exit and enter from stable sides: left/right for horizontal neighbors, top/bottom for vertical neighbors.
- Fan parallel edges through shared waypoint corridors instead of stacking them almost on top of each other.
- Never let an edge cut through the center of a dense node cluster if a corridor exists around it.
- If one edge would force three crossings, add waypoints and route around the cluster.

Load [layout heuristics](./references/layout-heuristics.md) before drawing dense diagrams.

### 6. Let the script settle structured placement

For structured requests:

- The agent supplies diagram type, node sizes, parent containers, semantic edge types, and sibling order.
- The script uses ELK layered layout for graph-shaped diagrams and a structured packer for lane-heavy row/column architectures.
- The script computes positions and container bounds.
- The script can emit either optimized JSON or a ready-to-open `.drawio` file.

Only skip the script for tiny diagrams where direct placement is obviously sufficient.

### 7. Encode mxGraph only after the layout is settled

When writing `.drawio` XML:

- Align nodes to a 10px grid.
- Use consistent block sizes for peer nodes.
- Leave generous whitespace; compactness is not the goal.
- Include `<mxGeometry relative="1" as="geometry" />` for every edge.
- Add explicit waypoints for any edge that crosses a reserved corridor or changes lane.

### 8. Validate visually before finalizing

Run a fast checklist:

- Is the main reading direction obvious in 3 seconds?
- Are primary edges visually dominant?
- Are dashed side-channel edges clearly secondary?
- Do any edges overlap labels or arrowheads?
- Can any pair of crossed edges be eliminated by swapping two sibling blocks?
- Would splitting the diagram improve clarity more than another round of micro-routing?

If the answer to the last question is yes, split the diagram.

## Output Rules

- Produce native `.drawio` XML, not Mermaid saved as text.
- Keep filenames descriptive and hyphenated.
- If the user asked for PNG/SVG/PDF, export from the `.drawio` source with the draw.io CLI and keep the source if export is unavailable.
- Prefer multiple clean pages over one overloaded page.

## Script Workflow

When invoking skill resources, follow the standard skill pattern:

- reference bundled resources with skill-relative links such as [ELK layout script](./scripts/elk_layout_to_drawio.mjs)
- do not assume the terminal working directory is the repo root or the skill folder
- resolve the absolute filesystem path of the script before running it
- do not install runtime dependencies inside the skill folder

### Input

- Build JSON using the contract in [layout-json-contract](./references/layout-json-contract.md).
- Prefer `diagramType` and sibling `order` instead of absolute `x` and `y` values.
- Include edge `kind` values such as `primary`, `control`, `audit`, or `optional`.
- Use `layoutMode: "structured"` when the hierarchy already defines the intended bands, rows, or columns.
- Do not include final waypoint coordinates unless preserving an existing locked edge.
- Prefer stdin over a visible intermediate file.
- If a file is temporarily required, write it to the OS temp directory or use a leading-dot filename such as `.beautiful-drawio-input.json` instead of leaving `*.layout.json` files in user-facing folders.

### Layout Engine

Run the script by absolute path, not by assuming a repo-relative current directory.

Preferred pattern:

```bash
node "/absolute/path/to/.github/skills/beautiful-drawio/scripts/elk_layout_to_drawio.mjs" --input - --format drawio --output result.drawio
```

Example via stdin:

```bash
cat "$TMPDIR/.beautiful-drawio-input.json" | node "/absolute/path/to/.github/skills/beautiful-drawio/scripts/elk_layout_to_drawio.mjs" --input - --format json
```

Runtime note:

- [ELK layout script](./scripts/elk_layout_to_drawio.mjs) bootstraps `elkjs` into an OS temp cache on first use.
- Do not run `npm install` in the skill folder.
- Prefer `node` with the resolved absolute script path.
- Do not use `npx ./scripts/elk_layout_to_drawio.mjs ...`; `npx` is for package resolution, not for invoking this local script path.

### Output Modes

- `json`: optimized nodes and routed edge waypoints for further inspection
- `drawio`: complete native draw.io XML for one or more pages

### Agent responsibilities

- The agent chooses topology, hierarchy, and order.
- The script owns placement.
- The agent reviews the output and only applies small post-fixes if necessary.

## Native Draw.io Requirements

- Use mxGraphModel XML with the required root cells `id="0"` and `id="1"`.
- Every edge must contain a child `<mxGeometry relative="1" as="geometry" />` element.
- Use explicit waypoint arrays for long detours or corridor routing.
- Use `parent="containerId"` for contained nodes.
- Open the resulting `.drawio` file when no export format was requested.

## Practical Heuristics

- Prefer `flowchart TD` reasoning over `LR` reasoning for dense systems.
- Use one dominant axis plus short perpendicular branches.
- Put high-degree nodes near the center of their cluster, not at the edge.
- Put sinks and outputs at the perimeter.
- Group cross-domain candidates, audit sinks, and future-state modules into clearly marked side bands.
- If several modules talk to the same external system, consider a shared gateway node.
- If a node needs more than about 4 unrelated crossing edges, the abstraction is probably wrong.

## Recommended Process For Complex Requests

1. Summarize the intended topology in words.
2. Draft a Mermaid/ELK graph mentally or explicitly.
3. Decide container structure and reading direction.
4. Place nodes by lane and hierarchy.
5. Route edge corridors for primary paths first.
6. Add secondary dashed edges.
7. Encode draw.io XML.
8. Export if requested.

## References

- [Layout heuristics](./references/layout-heuristics.md)
- [Layout JSON contract](./references/layout-json-contract.md)
- [ELK layout script](./scripts/elk_layout_to_drawio.mjs)

