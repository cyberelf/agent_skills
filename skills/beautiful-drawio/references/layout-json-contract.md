# Layout JSON Contract

Use this contract when the agent should describe diagram structure and let the layout engine compute the final geometry.

## Goal

The agent defines:

- boxes
- hierarchy
- ordering
- diagram type
- hierarchy
- semantic edge types

The script computes:

- overlap-free coordinates
- container bounds
- snapped grid positions
- optional draw.io XML

## Intermediate File Handling

- Prefer piping JSON to stdin instead of leaving a visible intermediate file in the workspace.
- If a temporary file is required, place it under the OS temp directory or use a leading-dot filename such as `.beautiful-drawio-input.json`.
- Do not leave user-facing `*.layout.json` files behind unless the user explicitly asked to inspect that intermediate artifact.

## Preferred Top-Level Shape

The script accepts either a single diagram object or a wrapper with `diagrams`.

Single diagram:

```json
{
  "id": "overall-tech-system",
  "name": "整体技术系统架构",
  "diagramType": "technical-architecture",
  "page": {
    "width": 1800,
    "height": 1100,
    "grid": 10
  },
  "nodes": [],
  "edges": []
}
```

Multiple diagrams:

```json
{
  "diagrams": [
    {
      "id": "page-1",
      "name": "Page 1",
      "nodes": [],
      "edges": []
    }
  ]
}
```

## Node Object

Required fields:

```json
{
  "id": "svc-guard",
  "label": "Agent Guard Service",
  "width": 220,
  "height": 58
}
```

Optional fields:

```json
{
  "parent": "lane-service",
  "kind": "node",
  "order": 3,
  "style": "rounded=1;whiteSpace=wrap;html=1;fillColor=#dcfce7;strokeColor=#16a34a;fontColor=#052e16;fontStyle=1;",
  "locked": false,
  "autoBounds": false,
  "margin": 24,
  "x": 600,
  "y": 440
}
```

`x` and `y` are now optional hints rather than the preferred authoring model.

## Node Kinds

- `node`: normal box
- `container`: bounding region whose size may be recomputed from children
- `text`: title or annotation box; usually not included in collision scoring

## Edge Object

Required fields:

```json
{
  "id": "e16",
  "source": "gw-tool",
  "target": "svc-guard"
}
```

Optional fields:

```json
{
  "label": "授权 / 工具治理",
  "kind": "primary",
  "style": "edgeStyle=orthogonalEdgeStyle;rounded=0;orthogonalLoop=1;jettySize=auto;html=1;strokeColor=#16a34a;fontColor=#16a34a;endArrow=block;"
}
```

## Edge Kinds

- `primary`: main path, prefer short internal routes
- `control`: secondary control-plane path
- `audit`: dashed or outer-band path
- `optional`: future-state or nonblocking path, often outer-band

## Important Rules

- Prefer `diagramType` and sibling `order` over absolute coordinates.
- Use `x` and `y` only as optional hints when you want a weak bias for legacy or mixed workflows.
- Do not provide final edge waypoints unless an edge is intentionally locked.
- Put child nodes inside containers using `parent`.
- Use `autoBounds: true` on containers that should resize to fit their children.
- Use `locked: true` only when the optimizer should not move a node.

The preferred ELK pipeline does not require absolute coordinates. If `x` and `y` are present, they are treated as weak hints rather than fixed placement.

## Layout Modes

- omit `layoutMode` or use `"elk"` for graph-shaped diagrams where edge topology should drive placement
- use `"structured"` for layered architecture pages, row/column banding, and block diagrams where the declared container hierarchy should drive placement

Example:

```json
{
  "layoutMode": "structured",
  "diagramType": "technical-architecture"
}
```

## Diagram Types

- `product-block`: product capability and module block diagrams, usually left to right
- `technical-architecture`: layered architectures, usually top down
- `data-flow`: directional data paths, usually left to right
- `deployment`: environment and target deployment diagrams, usually left to right with larger spacing

## Minimal Example

```json
{
  "id": "simple-system",
  "name": "Simple System",
  "diagramType": "product-block",
  "page": {
    "width": 1200,
    "height": 800,
    "grid": 10
  },
  "nodes": [
    {
      "id": "lane-service",
      "label": "核心服务层",
      "kind": "container",
      "order": 1,
      "width": 880,
      "height": 260,
      "autoBounds": true,
      "style": "rounded=1;whiteSpace=wrap;html=1;verticalAlign=top;align=left;spacingTop=8;spacingLeft=10;fillColor=#f8fafc;strokeColor=#475569;fontStyle=1;fontColor=#0f172a;"
    },
    {
      "id": "svc-orch",
      "label": "Orchestrator",
      "parent": "lane-service",
      "order": 1,
      "width": 180,
      "height": 56,
      "style": "rounded=1;whiteSpace=wrap;html=1;fillColor=#f5f5f4;strokeColor=#a8a29e;fontColor=#292524;fontStyle=1;"
    },
    {
      "id": "svc-guard",
      "label": "Agent Guard",
      "parent": "lane-service",
      "order": 2,
      "width": 180,
      "height": 56,
      "style": "rounded=1;whiteSpace=wrap;html=1;fillColor=#dcfce7;strokeColor=#16a34a;fontColor=#052e16;fontStyle=1;"
    }
  ],
  "edges": [
    {
      "id": "e1",
      "source": "svc-orch",
      "target": "svc-guard",
      "kind": "primary"
    }
  ]
}
```

## Expected Optimizer Behavior

- choose a typed layout preset from `diagramType`
- preserve sibling order where possible
- resize containers around children when `autoBounds` is true
- for `layoutMode: "structured"`, pack children directly from declared rows, columns, and wrapping width
- output optimized JSON or a draw.io file
