import ELK from "elkjs/lib/elk.bundled.js";
import type { Edge, Node } from "@xyflow/react";
import type { Rule } from "@/types";
import type { Program } from "./programs";

// Rules are deduplicated, so the same rule can sit in two selected programs. Prefixing with
// the program keeps each appearance its own node.
export const ruleNodeId = (program: Program, rule: Rule) => `${program.key}/rule-${rule.id}`;

export const NODE_WIDTH = 280;
export const NODE_HEIGHT = { program: 72, group: 68, leaf: 84 };
export type NodeKind = keyof typeof NODE_HEIGHT;

export type ProgramNodeData = { program: Program; expanded: boolean; highlighted: boolean };
export type RuleNodeData = {
  rule: Rule;
  /** Leaves anywhere below this rule, shown on a collapsed group so you know what's hidden. */
  leafCount: number;
  expanded: boolean;
  /** On the path to a leaf the searched course matches. */
  highlighted: boolean;
};

export type ProgramNode = Node<ProgramNodeData, "program">;
export type GroupNode = Node<RuleNodeData, "group">;
export type LeafNode = Node<RuleNodeData, "leaf">;
export type ExplorerNode = ProgramNode | GroupNode | LeafNode;

export const isLeaf = (rule: Rule) => rule.rules.length === 0;

const countLeaves = (rule: Rule, cache: Map<number, number>): number => {
  if (isLeaf(rule)) return 1;
  const cached = cache.get(rule.id);
  if (cached !== undefined) return cached;
  const count = rule.rules.reduce((sum, child) => sum + countLeaves(child, cache), 0);
  cache.set(rule.id, count);
  return count;
};

/** Every group node id across the programs, for "expand all". */
export const allGroupIds = (programs: Program[]): string[] => {
  const ids: string[] = [];
  programs.forEach((program) => {
    const visit = (rule: Rule) => {
      if (isLeaf(rule)) return;
      ids.push(ruleNodeId(program, rule));
      rule.rules.forEach(visit);
    };
    program.rules.forEach(visit);
  });
  return ids;
};

/**
 * Flattens each program's nested rules into React Flow nodes and edges, one root per program.
 * Programs start expanded and groups collapsed; `toggled` holds the node ids flipped from
 * that default, so adding a program opens it without collapsing the others. `highlighted`
 * holds the node ids to mark for a searched course. Nodes come back unpositioned;
 * `layoutGraph` places them.
 */
export const buildGraph = (
  programs: Program[],
  toggled: Set<string>,
  highlighted: Set<string>
): { nodes: ExplorerNode[]; edges: Edge[] } => {
  const leafCounts = new Map<number, number>();
  const position = { x: 0, y: 0 };
  const nodes: ExplorerNode[] = [];
  const edges: Edge[] = [];

  const visit = (program: Program, rule: Rule, parentId: string) => {
    const id = ruleNodeId(program, rule);
    const leaf = isLeaf(rule);
    const isExpanded = !leaf && toggled.has(id);
    nodes.push({
      id,
      type: leaf ? "leaf" : "group",
      position,
      data: {
        rule,
        leafCount: countLeaves(rule, leafCounts),
        expanded: isExpanded,
        highlighted: highlighted.has(id),
      },
    });
    edges.push({ id: `${parentId}->${id}`, source: parentId, target: id, type: "smoothstep" });
    if (isExpanded) rule.rules.forEach((child) => visit(program, child, id));
  };

  programs.forEach((program) => {
    const expanded = !toggled.has(program.key);
    nodes.push({
      id: program.key,
      type: "program",
      position,
      data: { program, expanded, highlighted: highlighted.has(program.key) },
    });
    if (expanded) program.rules.forEach((rule) => visit(program, rule, program.key));
  });
  return { nodes, edges };
};

const elk = new ELK();

/** Positions the nodes as left-to-right trees, one per program, stacked in selection order. */
export const layoutGraph = async (
  nodes: ExplorerNode[],
  edges: Edge[]
): Promise<ExplorerNode[]> => {
  const layout = await elk.layout({
    id: "root",
    layoutOptions: {
      "elk.algorithm": "layered",
      "elk.direction": "RIGHT",
      "elk.layered.spacing.nodeNodeBetweenLayers": "80",
      "elk.spacing.nodeNode": "16",
      // Keep siblings in the order the audit lists them.
      "elk.layered.considerModelOrder.strategy": "NODES_AND_EDGES",
      "elk.layered.nodePlacement.strategy": "BRANDES_KOEPF",
      // Each program is its own tree; keep them apart and in the order they were picked.
      "elk.spacing.componentComponent": "64",
      "elk.layered.considerModelOrder.components": "MODEL_ORDER",
    },
    children: nodes.map((node) => ({
      id: node.id,
      width: NODE_WIDTH,
      height: NODE_HEIGHT[node.type as NodeKind],
    })),
    edges: edges.map((edge) => ({ id: edge.id, sources: [edge.source], targets: [edge.target] })),
  });

  const positions = new Map(layout.children?.map((child) => [child.id, child]));
  return nodes.map((node) => {
    const placed = positions.get(node.id);
    return { ...node, position: { x: placed?.x ?? 0, y: placed?.y ?? 0 } };
  });
};
