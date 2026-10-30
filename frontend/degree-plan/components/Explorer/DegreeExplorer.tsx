import { useCallback, useEffect, useMemo, useRef, useState } from "react";
import styled from "@emotion/styled";
import {
  Background,
  Controls,
  MiniMap,
  ReactFlow,
  ReactFlowProvider,
  useEdgesState,
  useNodesState,
  useReactFlow,
  type Edge,
} from "@xyflow/react";
import "@xyflow/react/dist/style.css";
import {
  allGroupIds,
  buildGraph,
  layoutGraph,
  NODE_HEIGHT,
  NODE_WIDTH,
  type ExplorerNode,
  type NodeKind,
} from "./graph";
import { nodeTypes, ToggleContext } from "./ExplorerNodes";
import DetailPanel from "./DetailPanel";
import MatchPanel from "./MatchPanel";
import { findMatches, matchNodeIds, toMatchableCourse, type CourseDetail } from "./matcher";
import type { Program } from "./programs";

const Layout = styled.div`
  display: flex;
  flex: 1;
  min-height: 0;
`;

const Canvas = styled.div`
  flex: 1;
  position: relative;
`;

const Toolbar = styled.div`
  position: absolute;
  top: 0.75rem;
  left: 0.75rem;
  z-index: 5;
  display: flex;
  gap: 0.5rem;
  align-items: center;
  font-size: 0.8rem;
  color: #57606a;
  button {
    padding: 0.3rem 0.7rem;
    border: 1px solid #d0d4da;
    border-radius: 4px;
    background: #fff;
    cursor: pointer;
  }
`;

const MINIMAP_COLORS: Record<NodeKind, string> = {
  program: "#1f2328",
  group: "#8250df",
  leaf: "#1a7f37",
};

interface ExplorerProps {
  programs: Program[];
  /** The searched course, if any; its matching leaves are highlighted and listed. */
  course: CourseDetail | null;
}

const Explorer = ({ programs, course }: ExplorerProps) => {
  const { fitView, getNode, setCenter } = useReactFlow();
  const [nodes, setNodes, onNodesChange] = useNodesState<ExplorerNode>([]);
  const [edges, setEdges, onEdgesChange] = useEdgesState<Edge>([]);
  // Node ids flipped from their default (programs open, groups closed); see buildGraph.
  const [toggled, setToggled] = useState<Set<string>>(() => new Set());
  // Fit the whole tree into view after the next layout, rather than after every toggle,
  // so expanding a group doesn't yank the viewport away from it.
  const fitPending = useRef(true);

  const programKeys = programs.map((p) => p.key).join(",");
  useEffect(() => {
    fitPending.current = true;
  }, [programKeys]);

  const matchable = useMemo(() => course && toMatchableCourse(course), [course]);
  const matches = useMemo(
    () => (matchable ? findMatches(programs, matchable) : []),
    [programs, matchable]
  );
  const highlighted = useMemo(() => matchNodeIds(matches), [matches]);

  // Open the path to every match, so each matching leaf is on the canvas.
  useEffect(() => {
    if (highlighted.size === 0) return;
    fitPending.current = true;
    setToggled((previous) => {
      const next = new Set(previous);
      programs.forEach((program) => {
        highlighted.forEach((id) => {
          // Programs are open unless toggled; groups are closed unless toggled.
          if (id === program.key) next.delete(id);
          else if (id.startsWith(`${program.key}/`)) next.add(id);
        });
      });
      return next;
    });
  }, [programs, highlighted]);

  useEffect(() => {
    let stale = false;
    const graph = buildGraph(programs, toggled, highlighted);
    layoutGraph(graph.nodes, graph.edges).then((positioned) => {
      if (stale) return;
      // Carry the selection over, since these are new node objects.
      setNodes((previous) => {
        const selected = new Set(previous.filter((n) => n.selected).map((n) => n.id));
        return positioned.map((n) => ({ ...n, selected: selected.has(n.id) }));
      });
      setEdges(graph.edges);
    });
    return () => {
      stale = true;
    };
  }, [programs, toggled, highlighted, setNodes, setEdges]);

  useEffect(() => {
    if (!fitPending.current || nodes.length === 0) return;
    fitPending.current = false;
    // Wait a frame so React Flow has measured the new nodes.
    requestAnimationFrame(() => fitView({ padding: 0.1 }));
  }, [nodes, fitView]);

  const toggle = useCallback((id: string) => {
    setToggled((previous) => {
      const next = new Set(previous);
      if (next.has(id)) next.delete(id);
      else next.add(id);
      return next;
    });
  }, []);

  const expandAll = () => {
    fitPending.current = true;
    setToggled(new Set(allGroupIds(programs)));
  };
  const collapseAll = () => {
    fitPending.current = true;
    setToggled(new Set());
  };

  const focusNode = (id: string) => {
    setNodes((previous) => previous.map((n) => ({ ...n, selected: n.id === id })));
    const node = getNode(id);
    if (!node) return;
    const height = NODE_HEIGHT[node.type as NodeKind];
    setCenter(node.position.x + NODE_WIDTH / 2, node.position.y + height / 2, {
      zoom: 1,
      duration: 300,
    });
  };

  const selected = useMemo(() => nodes.find((n) => n.selected), [nodes]);

  return (
    <Layout>
      {course && matchable && (
        <MatchPanel
          course={matchable}
          title={course.title}
          programs={programs}
          matches={matches}
          onSelect={focusNode}
        />
      )}
      <Canvas>
        <Toolbar>
          <button onClick={expandAll}>Expand all</button>
          <button onClick={collapseAll}>Collapse all</button>
          <span>{nodes.length} nodes shown</span>
        </Toolbar>
        <ToggleContext.Provider value={toggle}>
          <ReactFlow
            nodes={nodes}
            edges={edges}
            onNodesChange={onNodesChange}
            onEdgesChange={onEdgesChange}
            nodeTypes={nodeTypes}
            nodesDraggable={false}
            nodesConnectable={false}
            minZoom={0.05}
            onlyRenderVisibleElements
            proOptions={{ hideAttribution: true }}
          >
            <Background />
            <Controls showInteractive={false} />
            <MiniMap pannable zoomable nodeColor={(n) => MINIMAP_COLORS[n.type as NodeKind]} />
          </ReactFlow>
        </ToggleContext.Provider>
      </Canvas>
      <DetailPanel
        rule={selected && "rule" in selected.data ? selected.data.rule : null}
        program={selected && "program" in selected.data ? selected.data.program : null}
      />
    </Layout>
  );
};

/** A read-only, collapsible graph of one or more programs' rule trees, one root each. */
const DegreeExplorer = (props: ExplorerProps) => (
  <ReactFlowProvider>
    <Explorer {...props} />
  </ReactFlowProvider>
);

export default DegreeExplorer;
