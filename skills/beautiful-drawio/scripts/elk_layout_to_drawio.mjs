import fs from 'node:fs/promises';
import os from 'node:os';
import path from 'node:path';
import { execFileSync } from 'node:child_process';
import { existsSync, mkdirSync } from 'node:fs';
import { pathToFileURL } from 'node:url';

const ELK_SPEC = 'elkjs@0.11.1';
const RUNTIME_CACHE_ROOT = process.env.BEAUTIFUL_DRAWIO_RUNTIME_DIR
  ? path.resolve(process.env.BEAUTIFUL_DRAWIO_RUNTIME_DIR)
  : path.join(os.tmpdir(), 'beautiful-drawio-runtime');
const ELK_ENTRY_PATH = path.join(RUNTIME_CACHE_ROOT, 'node_modules', 'elkjs', 'lib', 'elk.bundled.js');

function npmExecutable() {
  return process.platform === 'win32' ? 'npm.cmd' : 'npm';
}

function ensureElkRuntime() {
  if (existsSync(ELK_ENTRY_PATH)) return;
  mkdirSync(RUNTIME_CACHE_ROOT, { recursive: true });
  try {
    if (process.platform === 'win32') {
      execFileSync(
        process.env.ComSpec || 'cmd.exe',
        ['/d', '/s', '/c', `${npmExecutable()} install --no-save --no-package-lock ${ELK_SPEC}`],
        {
          cwd: RUNTIME_CACHE_ROOT,
          stdio: 'ignore'
        }
      );
    } else {
      execFileSync(
        npmExecutable(),
        ['install', '--no-save', '--no-package-lock', ELK_SPEC],
        {
          cwd: RUNTIME_CACHE_ROOT,
          stdio: 'ignore'
        }
      );
    }
  } catch (error) {
    const detail = error instanceof Error ? error.message : String(error);
    throw new Error(`Failed to prepare ELK runtime in temp cache ${RUNTIME_CACHE_ROOT}: ${detail}`);
  }
  if (!existsSync(ELK_ENTRY_PATH)) {
    throw new Error(`ELK runtime cache is missing expected module: ${ELK_ENTRY_PATH}`);
  }
}

async function loadElkConstructor() {
  ensureElkRuntime();
  const elkModule = await import(pathToFileURL(ELK_ENTRY_PATH).href);
  return elkModule.default;
}

const EDGE_KIND_STYLES = {
  primary: 'edgeStyle=orthogonalEdgeStyle;rounded=0;orthogonalLoop=1;jettySize=auto;html=1;strokeColor=#374151;fontColor=#374151;endArrow=block;',
  control: 'edgeStyle=orthogonalEdgeStyle;rounded=0;orthogonalLoop=1;jettySize=auto;html=1;strokeColor=#2563eb;fontColor=#2563eb;endArrow=block;',
  audit: 'edgeStyle=orthogonalEdgeStyle;rounded=0;orthogonalLoop=1;jettySize=auto;html=1;strokeColor=#7c3aed;fontColor=#7c3aed;dashed=1;endArrow=block;',
  optional: 'edgeStyle=orthogonalEdgeStyle;rounded=0;orthogonalLoop=1;jettySize=auto;html=1;strokeColor=#a855f7;fontColor=#a855f7;dashed=1;endArrow=block;'
};

const DEFAULT_NODE_STYLE = 'rounded=1;whiteSpace=wrap;html=1;fillColor=#ffffff;strokeColor=#a8a29e;fontColor=#292524;';
const DEFAULT_CONTAINER_STYLE = 'rounded=1;whiteSpace=wrap;html=1;verticalAlign=top;align=left;spacingTop=8;spacingLeft=10;fillColor=#ffffff;strokeColor=#111827;strokeWidth=2;fontStyle=1;fontColor=#111827;';

const LAYOUT_PRESETS = {
  'product-block': {
    direction: 'RIGHT',
    nodeSpacing: '40',
    layerSpacing: '90',
    padding: '[top=32,left=32,bottom=32,right=32]'
  },
  'technical-architecture': {
    direction: 'DOWN',
    nodeSpacing: '48',
    layerSpacing: '96',
    padding: '[top=40,left=32,bottom=32,right=32]'
  },
  'data-flow': {
    direction: 'RIGHT',
    nodeSpacing: '50',
    layerSpacing: '110',
    padding: '[top=28,left=28,bottom=28,right=28]'
  },
  deployment: {
    direction: 'RIGHT',
    nodeSpacing: '70',
    layerSpacing: '130',
    padding: '[top=36,left=36,bottom=36,right=36]'
  }
};

function parseArgs(argv) {
  const args = { format: 'json' };
  for (let index = 0; index < argv.length; index += 1) {
    const arg = argv[index];
    if (arg === '--input') args.input = argv[++index];
    else if (arg === '--output') args.output = argv[++index];
    else if (arg === '--format') args.format = argv[++index];
  }
  if (!args.input) throw new Error('--input is required');
  if (!['json', 'drawio'].includes(args.format)) throw new Error('--format must be json or drawio');
  return args;
}

async function readInput(path) {
  if (path === '-') {
    return new Promise((resolve, reject) => {
      let data = '';
      process.stdin.setEncoding('utf8');
      process.stdin.on('data', (chunk) => {
        data += chunk;
      });
      process.stdin.on('end', () => resolve(data));
      process.stdin.on('error', reject);
    });
  }
  return fs.readFile(path, 'utf8');
}

async function writeOutput(path, content) {
  if (!path) {
    process.stdout.write(content);
    if (!content.endsWith('\n')) process.stdout.write('\n');
    return;
  }
  await fs.writeFile(path, content, 'utf8');
}

function normalizePayload(payload) {
  return Array.isArray(payload?.diagrams) ? payload.diagrams : [payload];
}

function estimateWidth(label = '') {
  const text = String(label).replace(/<[^>]+>/g, '');
  return Math.max(140, Math.min(320, 44 + text.length * 8));
}

function normalizeNode(node) {
  const container = node.kind === 'container';
  return {
    ...node,
    kind: node.kind ?? 'node',
    parent: node.parent ?? '1',
    order: node.order ?? 0,
    width: node.width ?? (container ? 260 : estimateWidth(node.label)),
    height: node.height ?? (container ? 180 : 56),
    autoBounds: node.autoBounds ?? container,
    layoutDirection: node.layoutDirection,
    nodeSpacing: node.nodeSpacing,
    layerSpacing: node.layerSpacing,
    padding: node.padding,
    style: node.style ?? (container ? DEFAULT_CONTAINER_STYLE : DEFAULT_NODE_STYLE)
  };
}

function presetFor(diagram) {
  const preset = LAYOUT_PRESETS[diagram.diagramType] ?? LAYOUT_PRESETS['technical-architecture'];
  return {
    'elk.algorithm': 'layered',
    'elk.direction': diagram.direction ?? preset.direction,
    'elk.edgeRouting': 'ORTHOGONAL',
    'elk.hierarchyHandling': 'INCLUDE_CHILDREN',
    'elk.layered.considerModelOrder.strategy': 'NODES_AND_EDGES',
    'elk.layered.crossingMinimization.forceNodeModelOrder': 'true',
    'elk.spacing.nodeNode': preset.nodeSpacing,
    'elk.layered.spacing.nodeNodeBetweenLayers': preset.layerSpacing,
    'elk.padding': preset.padding
  };
}

function parsePadding(padding) {
  const result = { top: 0, left: 0, bottom: 0, right: 0 };
  const matches = String(padding ?? '').matchAll(/(top|left|bottom|right)=(-?\d+)/g);
  for (const [, side, value] of matches) result[side] = Number(value);
  return result;
}

function parseStyle(style) {
  const result = {};
  for (const entry of String(style ?? '').split(';')) {
    if (!entry) continue;
    const separator = entry.indexOf('=');
    if (separator === -1) {
      result[entry] = '1';
      continue;
    }
    result[entry.slice(0, separator)] = entry.slice(separator + 1);
  }
  return result;
}

function decodeHtmlEntities(text) {
  return String(text)
    .replace(/&nbsp;/g, ' ')
    .replace(/&amp;/g, '&')
    .replace(/&lt;/g, '<')
    .replace(/&gt;/g, '>')
    .replace(/&quot;/g, '"');
}

function labelLines(label) {
  const normalized = decodeHtmlEntities(label)
    .replace(/<br\s*\/?>/gi, '\n')
    .replace(/<\/div>/gi, '\n')
    .replace(/<div[^>]*>/gi, '')
    .replace(/<\/p>/gi, '\n')
    .replace(/<p[^>]*>/gi, '')
    .replace(/<[^>]+>/g, '');
  const lines = normalized
    .split(/\n+/)
    .map((line) => line.trim())
    .filter(Boolean);
  return lines.length ? lines : [''];
}

function estimateWrappedLineCount(line, availableWidth, fontSize) {
  if (!line) return 1;
  const cjkCount = (line.match(/[\u3400-\u9fff]/g) ?? []).length;
  const otherCount = Math.max(0, line.length - cjkCount);
  const estimatedWidth = cjkCount * fontSize + otherCount * fontSize * 0.55;
  return Math.max(1, Math.ceil(estimatedWidth / Math.max(availableWidth, fontSize)));
}

function estimateTitleReserve(node, padding) {
  if (node.kind !== 'container') return 0;
  if (!String(node.label ?? '').trim()) return 0;
  const style = parseStyle(node.style);
  const fontSize = Number(style.fontSize ?? 12);
  const spacingTop = Number(style.spacingTop ?? 8);
  const spacingLeft = Number(style.spacingLeft ?? 0);
  const availableWidth = Math.max(80, (node.width ?? 260) - padding.left - padding.right - spacingLeft - 12);
  const lineHeight = Math.ceil(fontSize * 1.35);
  const wrappedLineCount = labelLines(node.label)
    .reduce((count, line) => count + estimateWrappedLineCount(line, availableWidth, fontSize), 0);
  const bottomGap = Math.max(8, Math.round(fontSize * 0.5));
  return spacingTop + wrappedLineCount * lineHeight + bottomGap;
}

function buildChildrenMap(nodes) {
  const map = new Map();
  for (const node of nodes) {
    const parent = node.parent ?? '1';
    if (!map.has(parent)) map.set(parent, []);
    map.get(parent).push(node);
  }
  for (const children of map.values()) {
    children.sort((left, right) => (left.order ?? 0) - (right.order ?? 0) || left.id.localeCompare(right.id));
  }
  return map;
}

function buildElkNode(node, childrenMap, preset) {
  const children = (childrenMap.get(node.id) ?? []).map((child) => buildElkNode(child, childrenMap, preset));
  const elkNode = {
    id: node.id,
    width: node.width,
    height: node.height
  };
  if (children.length) {
    elkNode.children = children;
    elkNode.layoutOptions = {
      'elk.algorithm': 'layered',
      'elk.direction': node.layoutDirection ?? preset['elk.direction'],
      'elk.edgeRouting': 'ORTHOGONAL',
      'elk.spacing.nodeNode': String(node.nodeSpacing ?? 36),
      'elk.layered.spacing.nodeNodeBetweenLayers': String(node.layerSpacing ?? 72),
      'elk.padding': node.padding ?? '[top=34,left=28,bottom=28,right=28]'
    };
  }
  return elkNode;
}

function toElkGraph(diagram) {
  const nodes = (diagram.nodes ?? []).map(normalizeNode);
  const nodeMap = new Map(nodes.map((node) => [node.id, node]));
  const childrenMap = buildChildrenMap(nodes);
  const preset = presetFor(diagram);
  const edges = diagram.edges ?? [];
  return {
    id: diagram.id,
    layoutOptions: preset,
    children: (childrenMap.get('1') ?? []).map((node) => buildElkNode(node, childrenMap, preset)),
    edges: edges.map((edge, index) => ({
      id: edge.id ?? `e${index + 1}`,
      sources: [edge.source],
      targets: [edge.target]
    })),
    _meta: {
      name: diagram.name,
      page: diagram.page ?? { width: 1800, height: 1100, grid: 10 },
      diagramType: diagram.diagramType,
      nodeMap,
      edgeMap: new Map(edges.map((edge, index) => [edge.id ?? `e${index + 1}`, edge]))
    }
  };
}

function flattenNodes(elkNode, nodeMap, offsetX = 0, offsetY = 0, sink = []) {
  for (const child of elkNode.children ?? []) {
    const meta = nodeMap.get(child.id);
    const absoluteX = Math.round(offsetX + (child.x ?? 0));
    const absoluteY = Math.round(offsetY + (child.y ?? 0));
    sink.push({
      id: child.id,
      label: meta.label ?? '',
      x: absoluteX,
      y: absoluteY,
      width: Math.round(child.width ?? meta.width),
      height: Math.round(child.height ?? meta.height),
      parent: meta.parent ?? '1',
      kind: meta.kind ?? 'node',
      order: meta.order ?? 0,
      autoBounds: meta.autoBounds ?? false,
      layoutDirection: meta.layoutDirection,
      style: meta.style ?? DEFAULT_NODE_STYLE
    });
    flattenNodes(child, nodeMap, absoluteX, absoluteY, sink);
  }
  return sink;
}

function flattenEdges(elkNode, sink = []) {
  for (const edge of elkNode.edges ?? []) sink.push(edge);
  for (const child of elkNode.children ?? []) flattenEdges(child, sink);
  return sink;
}

function edgeWaypoints(edge) {
  const points = [];
  for (const section of edge.sections ?? []) {
    for (const point of section.bendPoints ?? []) {
      points.push([Math.round(point.x), Math.round(point.y)]);
    }
  }
  return points;
}

function normalizeOutputEdge(meta, id, waypoints = []) {
  const kind = meta.kind ?? 'primary';
  const hidden = Boolean(meta.hidden || meta.layoutOnly);
  return {
    id,
    source: meta.source,
    target: meta.target,
    label: meta.label ?? '',
    kind,
    style: meta.style ?? EDGE_KIND_STYLES[kind] ?? EDGE_KIND_STYLES.primary,
    waypoints,
    ...(hidden ? { hidden: true } : {})
  };
}

function measureStructuredNode(node, nodeMap, childrenMap) {
  const children = childrenMap.get(node.id) ?? [];
  const padding = parsePadding(node.padding ?? '[top=34,left=28,bottom=28,right=28]');
  const titleReserve = estimateTitleReserve(node, padding);
  if (!children.length) {
    return {
      width: node.width,
      height: node.height,
      padding,
      titleReserve,
      childLayouts: []
    };
  }

  const direction = node.layoutDirection ?? 'RIGHT';
  const spacing = node.nodeSpacing ?? 36;
  const childLayouts = [];
  let contentWidth = 0;
  let contentHeight = 0;

  for (const child of children) {
    child._structured = measureStructuredNode(child, nodeMap, childrenMap);
  }

  if (direction === 'DOWN') {
    let cursorY = 0;
    let maxWidth = 0;
    for (const child of children) {
      const measured = child._structured;
      childLayouts.push({ id: child.id, x: 0, y: cursorY });
      cursorY += measured.height + spacing;
      maxWidth = Math.max(maxWidth, measured.width);
    }
    contentWidth = maxWidth;
    contentHeight = children.length ? cursorY - spacing : 0;
  } else {
    const explicitWidth = node.width ? Math.max(0, node.width - padding.left - padding.right) : Number.POSITIVE_INFINITY;
    let cursorX = 0;
    let cursorY = 0;
    let rowHeight = 0;
    let maxRight = 0;
    for (const child of children) {
      const measured = child._structured;
      if (cursorX > 0 && Number.isFinite(explicitWidth) && cursorX + measured.width > explicitWidth) {
        cursorX = 0;
        cursorY += rowHeight + spacing;
        rowHeight = 0;
      }
      childLayouts.push({ id: child.id, x: cursorX, y: cursorY });
      maxRight = Math.max(maxRight, cursorX + measured.width);
      rowHeight = Math.max(rowHeight, measured.height);
      cursorX += measured.width + spacing;
    }
    contentWidth = maxRight;
    contentHeight = children.length ? cursorY + rowHeight : 0;
  }

  const measuredWidth = padding.left + contentWidth + padding.right;
  const measuredHeight = padding.top + titleReserve + contentHeight + padding.bottom;
  return {
    width: node.autoBounds ? Math.max(node.width ?? 0, measuredWidth) : (node.width ?? measuredWidth),
    height: node.autoBounds ? Math.max(node.height ?? 0, measuredHeight) : (node.height ?? measuredHeight),
    padding,
    titleReserve,
    childLayouts
  };
}

function positionStructuredNode(node, nodeMap, childrenMap, originX, originY, sink) {
  const measured = node._structured ?? { width: node.width, height: node.height, padding: { top: 0, left: 0, bottom: 0, right: 0 }, titleReserve: 0, childLayouts: [] };
  sink.push({
    id: node.id,
    label: node.label ?? '',
    x: Math.round(originX),
    y: Math.round(originY),
    width: Math.round(measured.width),
    height: Math.round(measured.height),
    parent: node.parent ?? '1',
    kind: node.kind ?? 'node',
    order: node.order ?? 0,
    autoBounds: node.autoBounds ?? false,
    layoutDirection: node.layoutDirection,
    style: node.style ?? DEFAULT_NODE_STYLE
  });

  for (const childLayout of measured.childLayouts) {
    const child = nodeMap.get(childLayout.id);
    positionStructuredNode(
      child,
      nodeMap,
      childrenMap,
      originX + measured.padding.left + childLayout.x,
      originY + measured.padding.top + measured.titleReserve + childLayout.y,
      sink
    );
  }
}

function optimizeStructuredDiagram(diagram) {
  const nodes = (diagram.nodes ?? []).map(normalizeNode);
  const nodeMap = new Map(nodes.map((node) => [node.id, node]));
  const childrenMap = buildChildrenMap(nodes);
  const preset = presetFor(diagram);
  const rootNode = {
    id: '1',
    kind: 'container',
    width: diagram.page?.width ?? 1800,
    height: diagram.page?.height ?? 1100,
    autoBounds: false,
    layoutDirection: diagram.layoutDirection ?? preset['elk.direction'],
    nodeSpacing: Number(preset['elk.spacing.nodeNode'] ?? 40),
    layerSpacing: Number(preset['elk.layered.spacing.nodeNodeBetweenLayers'] ?? 96),
    padding: preset['elk.padding']
  };
  rootNode._structured = measureStructuredNode(rootNode, nodeMap, childrenMap);
  const positionedNodes = [];
  for (const childLayout of rootNode._structured.childLayouts) {
    const child = nodeMap.get(childLayout.id);
    positionStructuredNode(
      child,
      nodeMap,
      childrenMap,
      rootNode._structured.padding.left + childLayout.x,
      rootNode._structured.padding.top + childLayout.y,
      positionedNodes
    );
  }
  const edges = (diagram.edges ?? [])
    .map((edge, index) => normalizeOutputEdge(edge, edge.id ?? `e${index + 1}`))
    .filter((edge) => !edge.hidden);
  return {
    id: diagram.id,
    name: diagram.name,
    layoutMode: diagram.layoutMode,
    rootLayoutDirection: diagram.layoutDirection ?? preset['elk.direction'],
    diagramType: diagram.diagramType,
    page: diagram.page,
    nodes: positionedNodes,
    edges
  };
}

function optimizeDiagram(result) {
  const nodes = flattenNodes(result, result._meta.nodeMap);
  const edges = flattenEdges(result).map((edge, index) => {
    const meta = result._meta.edgeMap.get(edge.id) ?? {};
    return normalizeOutputEdge(
      {
        ...meta,
        source: edge.sources?.[0],
        target: edge.targets?.[0]
      },
      edge.id ?? `e${index + 1}`,
      edgeWaypoints(edge)
    );
  }).filter((edge) => !edge.hidden);
  return {
    id: result.id,
    name: result._meta.name,
    layoutMode: result._meta.layoutMode,
    rootLayoutDirection: result._meta.rootLayoutDirection,
    diagramType: result._meta.diagramType,
    page: result._meta.page,
    nodes,
    edges
  };
}

function nodeDepths(nodes) {
  const nodeMap = new Map(nodes.map((node) => [node.id, node]));
  const depths = new Map();
  function depth(node) {
    if (depths.has(node.id)) return depths.get(node.id);
    if (!node.parent || node.parent === '1' || !nodeMap.has(node.parent)) {
      depths.set(node.id, 0);
      return 0;
    }
    const value = depth(nodeMap.get(node.parent)) + 1;
    depths.set(node.id, value);
    return value;
  }
  for (const node of nodes) depth(node);
  return depths;
}

function drawioGeometry(node, nodeMap) {
  if (!node.parent || node.parent === '1' || !nodeMap.has(node.parent)) {
    return { x: node.x, y: node.y };
  }
  const parent = nodeMap.get(node.parent);
  return { x: node.x - parent.x, y: node.y - parent.y };
}

function escapeXml(value = '') {
  return String(value)
    .replace(/&/g, '&amp;')
    .replace(/</g, '&lt;')
    .replace(/>/g, '&gt;')
    .replace(/"/g, '&quot;');
}

function stringifyStyle(styleObject) {
  return `${Object.entries(styleObject)
    .filter(([, value]) => value !== undefined && value !== null && value !== '')
    .map(([key, value]) => `${key}=${value}`)
    .join(';')};`;
}

function nodeCenter(node) {
  return {
    x: node.x + node.width / 2,
    y: node.y + node.height / 2
  };
}

function sideVector(side) {
  if (side === 'left') return { x: -1, y: 0 };
  if (side === 'right') return { x: 1, y: 0 };
  if (side === 'top') return { x: 0, y: -1 };
  return { x: 0, y: 1 };
}

function sideAnchor(node, side) {
  if (side === 'left') return { x: node.x, y: node.y + node.height / 2 };
  if (side === 'right') return { x: node.x + node.width, y: node.y + node.height / 2 };
  if (side === 'top') return { x: node.x + node.width / 2, y: node.y };
  return { x: node.x + node.width / 2, y: node.y + node.height };
}

function sidePort(side) {
  if (side === 'left') return { exitX: 0, exitY: 0.5 };
  if (side === 'right') return { exitX: 1, exitY: 0.5 };
  if (side === 'top') return { exitX: 0.5, exitY: 0 };
  return { exitX: 0.5, exitY: 1 };
}

function oppositeSide(side) {
  if (side === 'left') return 'right';
  if (side === 'right') return 'left';
  if (side === 'top') return 'bottom';
  return 'top';
}

function buildGroupOffsets(keys) {
  const counts = new Map();
  for (const key of keys) {
    counts.set(key, (counts.get(key) ?? 0) + 1);
  }
  const seen = new Map();
  const offsets = new Map();
  for (const key of keys) {
    const count = counts.get(key) ?? 1;
    const index = seen.get(key) ?? 0;
    seen.set(key, index + 1);
    offsets.set(`${key}::${index}`, (index - (count - 1) / 2) * 16);
  }
  return offsets;
}

function buildEdgeRoutingHints(edges, nodeMap) {
  const descriptors = [];
  for (const edge of edges) {
    const sourceNode = nodeMap.get(edge.source);
    const targetNode = nodeMap.get(edge.target);
    if (!sourceNode || !targetNode) {
      descriptors.push({ edge, sourceNode: null, targetNode: null });
      continue;
    }
    const { sourceSide, targetSide } = chooseAttachmentSides(sourceNode, targetNode, nodeMap);
    descriptors.push({ edge, sourceNode, targetNode, sourceSide, targetSide });
  }

  const sourceKeys = descriptors.map((descriptor) => `${descriptor.edge.source}:${descriptor.sourceSide ?? 'none'}`);
  const targetKeys = descriptors.map((descriptor) => `${descriptor.edge.target}:${descriptor.targetSide ?? 'none'}`);
  const sourceOffsets = buildGroupOffsets(sourceKeys);
  const targetOffsets = buildGroupOffsets(targetKeys);
  const seenSource = new Map();
  const seenTarget = new Map();

  return descriptors.map((descriptor) => {
    if (!descriptor.sourceNode || !descriptor.targetNode) {
      return { edge: descriptor.edge, style: descriptor.edge.style, points: descriptor.edge.waypoints ?? [] };
    }
    const sourceKey = `${descriptor.edge.source}:${descriptor.sourceSide}`;
    const targetKey = `${descriptor.edge.target}:${descriptor.targetSide}`;
    const sourceIndex = seenSource.get(sourceKey) ?? 0;
    const targetIndex = seenTarget.get(targetKey) ?? 0;
    seenSource.set(sourceKey, sourceIndex + 1);
    seenTarget.set(targetKey, targetIndex + 1);
    const sourceOffset = sourceOffsets.get(`${sourceKey}::${sourceIndex}`) ?? 0;
    const targetOffset = targetOffsets.get(`${targetKey}::${targetIndex}`) ?? 0;
    const points = descriptor.edge.waypoints?.length
      ? descriptor.edge.waypoints
      : computeFallbackWaypoints(descriptor.sourceNode, descriptor.targetNode, descriptor.sourceSide, descriptor.targetSide, sourceOffset, targetOffset, nodeMap);
    const style = withEdgePorts(descriptor.edge.style, descriptor.sourceSide, descriptor.targetSide);
    return { edge: descriptor.edge, style, points };
  });
}

function withEdgePorts(style, sourceSide, targetSide) {
  const styleObject = parseStyle(style);
  const sourcePort = sidePort(sourceSide);
  const targetPort = sidePort(targetSide);
  styleObject.exitX = sourcePort.exitX;
  styleObject.exitY = sourcePort.exitY;
  styleObject.exitPerimeter = 1;
  styleObject.entryX = targetPort.exitX;
  styleObject.entryY = targetPort.exitY;
  styleObject.entryPerimeter = 1;
  return stringifyStyle(styleObject);
}

function collectAncestors(node, nodeMap) {
  const ancestors = [];
  let currentId = node?.parent;
  while (currentId && nodeMap.has(currentId)) {
    const current = nodeMap.get(currentId);
    ancestors.push(current);
    currentId = current?.parent;
  }
  return ancestors;
}

function childUnderAncestor(node, ancestorId, nodeMap) {
  let current = node;
  while (current && current.parent && current.parent !== ancestorId) {
    current = nodeMap.get(current.parent);
  }
  return current;
}

function lowestCommonAncestor(sourceNode, targetNode, nodeMap) {
  const sourceAncestors = collectAncestors(sourceNode, nodeMap);
  const targetIds = new Set(collectAncestors(targetNode, nodeMap).map((node) => node.id));
  return sourceAncestors.find((node) => targetIds.has(node.id)) ?? null;
}

function axisSides(axis, delta) {
  if (axis === 'horizontal') {
    return delta >= 0
      ? { sourceSide: 'right', targetSide: 'left' }
      : { sourceSide: 'left', targetSide: 'right' };
  }
  return delta >= 0
    ? { sourceSide: 'bottom', targetSide: 'top' }
    : { sourceSide: 'top', targetSide: 'bottom' };
}

function offsetAnchor(anchor, side, offset) {
  if (side === 'left' || side === 'right') {
    return { x: anchor.x, y: anchor.y + offset };
  }
  return { x: anchor.x + offset, y: anchor.y };
}

function moveOut(anchor, side, distance) {
  const vector = sideVector(side);
  return { x: anchor.x + vector.x * distance, y: anchor.y + vector.y * distance };
}

function chooseBypassCoordinate(container, sourceNode, targetNode, axis) {
  const gutter = 12;
  if (axis === 'x') {
    const left = container.x + gutter;
    const right = container.x + container.width - gutter;
    const average = (nodeCenter(sourceNode).x + nodeCenter(targetNode).x) / 2;
    return Math.abs(average - left) <= Math.abs(average - right) ? left : right;
  }
  const top = container.y + gutter;
  const bottom = container.y + container.height - gutter;
  const average = (nodeCenter(sourceNode).y + nodeCenter(targetNode).y) / 2;
  return Math.abs(average - top) <= Math.abs(average - bottom) ? top : bottom;
}

function structuredBypassWaypoints(sourceNode, targetNode, sourceSide, targetSide, sourceClear, targetClear, nodeMap) {
  const lca = lowestCommonAncestor(sourceNode, targetNode, nodeMap);
  if (!lca || !lca.layoutDirection || lca.id === '1') return null;

  const sourceBranch = childUnderAncestor(sourceNode, lca.id, nodeMap);
  const targetBranch = childUnderAncestor(targetNode, lca.id, nodeMap);
  if (!sourceBranch || !targetBranch || sourceBranch.id === targetBranch.id) return null;

  if (lca.layoutDirection === 'DOWN') {
    const descending = sourceBranch.y <= targetBranch.y;
    const corridorPad = 10;
    const sourceCorridorY = descending ? sourceBranch.y + sourceBranch.height + corridorPad : sourceBranch.y - corridorPad;
    const targetCorridorY = descending ? targetBranch.y - corridorPad : targetBranch.y + targetBranch.height + corridorPad;
    const bypassX = chooseBypassCoordinate(lca, sourceNode, targetNode, 'x');
    return normalizeWaypointList([
      [Math.round(sourceClear.x), Math.round(sourceCorridorY)],
      [Math.round(bypassX), Math.round(sourceCorridorY)],
      [Math.round(bypassX), Math.round(targetCorridorY)],
      [Math.round(targetClear.x), Math.round(targetCorridorY)]
    ]);
  }

  if (lca.layoutDirection === 'RIGHT') {
    const forward = sourceBranch.x <= targetBranch.x;
    const corridorPad = 10;
    const sourceCorridorX = forward ? sourceBranch.x + sourceBranch.width + corridorPad : sourceBranch.x - corridorPad;
    const targetCorridorX = forward ? targetBranch.x - corridorPad : targetBranch.x + targetBranch.width + corridorPad;
    const bypassY = chooseBypassCoordinate(lca, sourceNode, targetNode, 'y');
    return normalizeWaypointList([
      [Math.round(sourceCorridorX), Math.round(sourceClear.y)],
      [Math.round(sourceCorridorX), Math.round(bypassY)],
      [Math.round(targetCorridorX), Math.round(bypassY)],
      [Math.round(targetCorridorX), Math.round(targetClear.y)]
    ]);
  }

  return null;
}

function computeFallbackWaypoints(sourceNode, targetNode, sourceSide, targetSide, sourceOffset, targetOffset, nodeMap) {
  const margin = 24;
  const sourceAnchor = offsetAnchor(sideAnchor(sourceNode, sourceSide), sourceSide, sourceOffset);
  const targetAnchor = offsetAnchor(sideAnchor(targetNode, targetSide), targetSide, targetOffset);
  const sourceClear = moveOut(sourceAnchor, sourceSide, margin);
  const targetClear = moveOut(targetAnchor, targetSide, margin);

  const bypassPoints = structuredBypassWaypoints(sourceNode, targetNode, sourceSide, targetSide, sourceClear, targetClear, nodeMap);
  if (bypassPoints?.length) return bypassPoints;

  if ((sourceSide === 'left' || sourceSide === 'right') && (targetSide === 'left' || targetSide === 'right')) {
    const midX = Math.round((sourceClear.x + targetClear.x) / 2);
    return normalizeWaypointList([
      [midX, Math.round(sourceClear.y)],
      [midX, Math.round(targetClear.y)]
    ]);
  }

  if ((sourceSide === 'top' || sourceSide === 'bottom') && (targetSide === 'top' || targetSide === 'bottom')) {
    const midY = Math.round((sourceClear.y + targetClear.y) / 2);
    return normalizeWaypointList([
      [Math.round(sourceClear.x), midY],
      [Math.round(targetClear.x), midY]
    ]);
  }

  return normalizeWaypointList([[Math.round(sourceClear.x), Math.round(targetClear.y)]]);
}

function normalizeWaypointList(points) {
  const normalized = [];
  for (const point of points) {
    const current = [Math.round(point[0]), Math.round(point[1])];
    const previous = normalized[normalized.length - 1];
    if (!previous || previous[0] !== current[0] || previous[1] !== current[1]) {
      normalized.push(current);
    }
  }
  let changed = true;
  while (changed) {
    changed = false;
    for (let index = 1; index < normalized.length - 1; index += 1) {
      const previous = normalized[index - 1];
      const current = normalized[index];
      const next = normalized[index + 1];
      const collinearX = previous[0] === current[0] && current[0] === next[0];
      const collinearY = previous[1] === current[1] && current[1] === next[1];
      if (collinearX || collinearY) {
        normalized.splice(index, 1);
        changed = true;
        break;
      }
    }
  }
  return normalized;
}

function chooseAttachmentSides(sourceNode, targetNode, nodeMap) {
  const sourceCenter = nodeCenter(sourceNode);
  const targetCenter = nodeCenter(targetNode);
  const dx = targetCenter.x - sourceCenter.x;
  const dy = targetCenter.y - sourceCenter.y;
  const sharedParent = sourceNode.parent && sourceNode.parent === targetNode.parent ? nodeMap.get(sourceNode.parent) : null;
  if (sharedParent?.layoutDirection === 'RIGHT') {
    return axisSides('horizontal', dx);
  }
  if (sharedParent?.layoutDirection === 'DOWN') {
    return axisSides('vertical', dy);
  }

  const lca = lowestCommonAncestor(sourceNode, targetNode, nodeMap);
  if (lca?.layoutDirection === 'RIGHT') {
    return axisSides('horizontal', dx);
  }
  if (lca?.layoutDirection === 'DOWN') {
    return axisSides('vertical', dy);
  }

  if (Math.abs(dx) >= Math.abs(dy)) {
    return axisSides('horizontal', dx);
  }
  return axisSides('vertical', dy);
}

function toDrawio(diagrams) {
  const lines = ['<mxfile host="Copilot" version="1.0">'];
  for (const diagram of diagrams) {
    const page = diagram.page ?? { width: 1800, height: 1100, grid: 10 };
    const nodes = [...diagram.nodes];
    const depths = nodeDepths(nodes);
    nodes.sort((left, right) => (depths.get(left.id) ?? 0) - (depths.get(right.id) ?? 0) || (left.order ?? 0) - (right.order ?? 0) || left.id.localeCompare(right.id));
    const nodeMap = new Map(nodes.map((node) => [node.id, node]));
    nodeMap.set('1', {
      id: '1',
      kind: 'container',
      parent: null,
      x: 0,
      y: 0,
      width: page.width ?? 1800,
      height: page.height ?? 1100,
      layoutDirection: diagram.rootLayoutDirection
    });
    lines.push(`  <diagram id="${escapeXml(diagram.id)}" name="${escapeXml(diagram.name)}">`);
    lines.push(`    <mxGraphModel dx="1380" dy="820" grid="1" gridSize="${page.grid ?? 10}" guides="1" tooltips="1" connect="1" arrows="1" fold="1" page="1" pageScale="1" pageWidth="${page.width ?? 1800}" pageHeight="${page.height ?? 1100}" math="0" shadow="0" adaptiveColors="auto">`);
    lines.push('      <root>');
    lines.push('        <mxCell id="0" />');
    lines.push('        <mxCell id="1" parent="0" />');
    for (const node of nodes) {
      const geometry = drawioGeometry(node, nodeMap);
      lines.push(`        <mxCell id="${escapeXml(node.id)}" value="${escapeXml(node.label)}" style="${escapeXml(node.style)}" parent="${escapeXml(node.parent || '1')}" vertex="1">`);
      lines.push(`          <mxGeometry x="${Math.round(geometry.x)}" y="${Math.round(geometry.y)}" width="${Math.round(node.width)}" height="${Math.round(node.height)}" as="geometry" />`);
      lines.push('        </mxCell>');
    }
    const routedEdges = buildEdgeRoutingHints(diagram.edges, nodeMap);
    for (const { edge, style, points } of routedEdges) {
      lines.push(`        <mxCell id="${escapeXml(edge.id)}" value="${escapeXml(edge.label || '')}" style="${escapeXml(style)}" parent="1" source="${escapeXml(edge.source)}" target="${escapeXml(edge.target)}" edge="1">`);
      lines.push('          <mxGeometry relative="1" as="geometry">');
      if (points?.length) {
        lines.push('            <Array as="points">');
        for (const [x, y] of points) {
          lines.push(`              <mxPoint x="${Math.round(x)}" y="${Math.round(y)}" />`);
        }
        lines.push('            </Array>');
      }
      lines.push('          </mxGeometry>');
      lines.push('        </mxCell>');
    }
    lines.push('      </root>');
    lines.push('    </mxGraphModel>');
    lines.push('  </diagram>');
  }
  lines.push('</mxfile>');
  return `${lines.join('\n')}\n`;
}

function toJson(diagrams) {
  if (diagrams.length === 1) return `${JSON.stringify(diagrams[0], null, 2)}\n`;
  return `${JSON.stringify({ diagrams }, null, 2)}\n`;
}

async function main() {
  const args = parseArgs(process.argv.slice(2));
  const payload = JSON.parse(await readInput(args.input));
  const diagrams = normalizePayload(payload);
  const optimized = [];
  let elk = null;
  for (const diagram of diagrams) {
    if (diagram.layoutMode === 'structured') {
      optimized.push(optimizeStructuredDiagram(diagram));
      continue;
    }
    if (!elk) {
      const ELK = await loadElkConstructor();
      elk = new ELK();
    }
    const graph = toElkGraph(diagram);
    const result = await elk.layout(graph);
    result._meta = graph._meta;
    optimized.push(optimizeDiagram(result));
  }
  await writeOutput(args.output, args.format === 'drawio' ? toDrawio(optimized) : toJson(optimized));
}

main().catch((error) => {
  console.error(error instanceof Error ? error.stack || error.message : String(error));
  process.exit(1);
});