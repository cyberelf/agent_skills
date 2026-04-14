# Beautiful Draw.io Layout Heuristics

Use this reference when the diagram has dense connectivity, multiple containers, or long-distance edges.

## What Visual-Explainer Does Better

The `visual-explainer` skill produces cleaner connection-heavy diagrams because it explicitly does four things the baseline `drawio` skill does not require:

1. It chooses a rendering strategy based on diagram complexity instead of forcing one format.
2. It uses Mermaid with `layout: 'elk'` for topology-first automatic layout.
3. It prefers top-down structure for complex graphs to reduce horizontal sprawl.
4. It treats zoom, readability, and diagram scale as part of the output quality, not an afterthought.

## What To Borrow For Draw.io

### Complexity thresholds

- Up to 6 nodes: direct draw.io placement is usually fine.
- 7-10 nodes: use containers and preplanned edge corridors.
- 10+ nodes or 10+ edges: do a Mermaid/ELK planning pass first.
- 15+ elements with rich text: use a hybrid approach or multiple pages.

### Direction selection

- Prefer top-down for complex architectures, governance stacks, and layered systems.
- Use left-right only for short pipelines, lifecycle comparisons, or explicit before/after layouts.
- Avoid deep LR chains with many labels; they force cramped nodes and unreadable edges.

### Crossing reduction

- Sort sibling nodes by dependency order before placing them.
- Swap neighboring siblings if that removes one or more crossings.
- Keep high-fan-out nodes centered.
- Convert repeated cross-links into one upstream aggregator or gateway when semantically valid.
- Route telemetry, audit, and sync edges in outer bands instead of through the middle.

### Container strategy

- Put each domain or layer in a container.
- Keep peer containers aligned to the same width or height where possible.
- Use extra whitespace between containers, not inside the hottest node cluster.
- Use side bands for optional, future, or audit planes.

### Edge strategy

- Reserve one corridor for primary flow.
- Reserve a different corridor for audit and sync edges.
- Label only the edges that materially change interpretation.
- Do not label every connector.
- Prefer one bend with intention over many tiny bends.

### Block sizing

- Peer blocks should share widths unless content requires otherwise.
- Avoid extreme aspect ratios.
- Use larger nodes for hubs, smaller ones for adapters and sinks.
- If a label forces a very wide box, split the label across lines instead of widening the whole row.

## Draw.io XML Implications

When translating the layout into mxGraph:

- Use `rounded=1` for blocks unless the visual language needs hard rectangles.
- Use `html=1` and `<div>` line breaks for multi-line labels.
- Use `parent="containerId"` for contained nodes, not just visual stacking.
- Use `edgeStyle=orthogonalEdgeStyle` by default.
- Add waypoint arrays for edges that need reserved corridors.
- Keep coordinates on a stable grid.

## Failure Modes To Catch

- A dashed secondary edge visually dominates the main path.
- Several edges terminate on different sides of the same node without a reason.
- A container exists only as decoration and does not help structure the layout.
- A diagram mixes comparison layout and flow layout in the same page.
- Rich text inside nodes forces inconsistent block widths and broken alignment.

## Decision Rule

If the cleanest diagram still needs too many routing exceptions, the diagram should be split, not endlessly tuned.