import ELK from "elkjs/lib/elk.bundled.js";
import type { Edge, Node } from "@xyflow/react";
import type { Degree, Rule } from "@/types";

export const DEGREE_NODE_ID = "degree";
export const ruleNodeId = (rule: Rule) => `rule-${rule.id}`;

export const NODE_WIDTH = 280;
export const NODE_HEIGHT = { degree: 72, group: 68, leaf: 84 };
export type NodeKind = keyof typeof NODE_HEIGHT;

export type DegreeNodeData = { degree: Degree; expanded: boolean };
export type RuleNodeData = {
  rule: Rule;
  /** Leaves anywhere below this rule, shown on a collapsed group so you know what's hidden. */
  leafCount: number;
  expanded: boolean;
};

export type DegreeNode = Node<DegreeNodeData, "degree">;
export type GroupNode = Node<RuleNodeData, "group">;
export type LeafNode = Node<RuleNodeData, "leaf">;
export type ExplorerNode = DegreeNode | GroupNode | LeafNode;

export const isLeaf = (rule: Rule) => rule.rules.length === 0;

const countLeaves = (rule: Rule, cache: Map<number, number>): number => {
  if (isLeaf(rule)) return 1;
  const cached = cache.get(rule.id);
  if (cached !== undefined) return cached;
  const count = rule.rules.reduce((sum, child) => sum + countLeaves(child, cache), 0);
  cache.set(rule.id, count);
  return count;
};

/** Every node id that can be expanded, for "expand all". */
export const allExpandableIds = (degree: Degree): string[] => {
  const ids = [DEGREE_NODE_ID];
  const visit = (rule: Rule) => {
    if (isLeaf(rule)) return;
    ids.push(ruleNodeId(rule));
    rule.rules.forEach(visit);
  };
  degree.rules.forEach(visit);
  return ids;
};

/**
 * Flattens the nested rules into React Flow nodes and edges, walking only into nodes whose id
 * is in `expanded`. Nodes come back unpositioned; `layoutGraph` places them.
 */
export const buildGraph = (
  degree: Degree,
  expanded: Set<string>
): { nodes: ExplorerNode[]; edges: Edge[] } => {
  const leafCounts = new Map<number, number>();
  const position = { x: 0, y: 0 };
  const nodes: ExplorerNode[] = [
    {
      id: DEGREE_NODE_ID,
      type: "degree",
      position,
      data: { degree, expanded: expanded.has(DEGREE_NODE_ID) },
    },
  ];
  const edges: Edge[] = [];

  const visit = (rule: Rule, parentId: string) => {
    const id = ruleNodeId(rule);
    const leaf = isLeaf(rule);
    const isExpanded = !leaf && expanded.has(id);
    nodes.push({
      id,
      type: leaf ? "leaf" : "group",
      position,
      data: { rule, leafCount: countLeaves(rule, leafCounts), expanded: isExpanded },
    });
    edges.push({ id: `${parentId}->${id}`, source: parentId, target: id, type: "smoothstep" });
    if (isExpanded) rule.rules.forEach((child) => visit(child, id));
  };

  if (expanded.has(DEGREE_NODE_ID)) degree.rules.forEach((rule) => visit(rule, DEGREE_NODE_ID));
  return { nodes, edges };
};

const elk = new ELK();

/** Positions the nodes as a left-to-right tree. */
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
