import React, {
  useCallback,
  useEffect,
} from "https://cdn.jsdelivr.net/npm/react@18.2.0/+esm";
import ReactDOM from "https://cdn.jsdelivr.net/npm/react-dom@18.2.0/+esm";
import ReactFlow, {
  ConnectionLineType,
  useNodesState,
  useEdgesState,
  Controls,
  Background,
  Panel,
} from "https://cdn.jsdelivr.net/npm/reactflow@11.7.4/+esm";
import dagre from "https://esm.sh/dagre@0.8.5";

const params = new Proxy(new URLSearchParams(window.location.search), {
  get: (searchParams, prop) => searchParams.get(prop),
});
const id = Number(params.id);
const renderRule = (rule) => {
  return (
    <div style={{ display: "flex", flexDirection: "column", gap: ".5em" }}>
      <div>{rule.id}</div>
      <div style={{ fontWeight: "bold" }}>{rule.title || "<No title>"}</div>
      <div>Q: {rule.q}</div>
      <div>Num: {rule.num}</div>
      <div>Credits: {rule.credits}</div>
    </div>
  );
};

const nodeWidth = 172;
const nodeHeight = 300;
const dagreGraph = new dagre.graphlib.Graph();
dagreGraph.setDefaultEdgeLabel(() => ({}));
const getLayoutedElements = (nodes, edges, direction = "TB") => {
  const isHorizontal = direction === "LR";
  dagreGraph.setGraph({ rankdir: direction });

  nodes.forEach((node) => {
    dagreGraph.setNode(node.id, {
      width: nodeWidth,
      height: nodeHeight,
    });
  });

  edges.forEach((edge) => {
    dagreGraph.setEdge(edge.source, edge.target);
  });

  dagre.layout(dagreGraph);

  nodes.forEach((node) => {
    const nodeWithPosition = dagreGraph.node(node.id);
    node.targetPosition = isHorizontal ? "left" : "top";
    node.sourcePosition = isHorizontal ? "right" : "bottom";

    // We are shifting the dagre node position (anchor=center center) to the top left
    // so it matches the React Flow node anchor point (top left).
    node.position = {
      x: nodeWithPosition.x - nodeWidth / 2,
      y: nodeWithPosition.y - nodeHeight / 2,
    };

    return node;
  });

  return { nodes, edges };
};

const pkOfNodeId = (nodeId) => [
  nodeId.startsWith("d"),
  Number(nodeId.slice(1)),
];

const LayoutFlow = () => {
  const [nodes, setNodes, onNodesChange] = useNodesState([]);
  const [edges, setEdges, onEdgesChange] = useEdgesState([]);

  const onConnect = useCallback((params) => {
    if (params.source === params.target) return;
    const [sourceIsDegree, sourceId] = pkOfNodeId(params.source);
    const [targetIsDegree, targetId] = pkOfNodeId(params.target);
    if (sourceIsDegree || targetIsDegree) return;
    const redirect = `/admin/degree/doublecountrestriction/add/?rule=${sourceId}&other_rule=${targetId}`;
    window.location.href = redirect;
  }, []);

  const onEdgeDelete = useCallback((edge) => {
    if (!edge.id.startsWith("c")) return;
  }, []);

  useEffect(() => {
    const fetchDegree = async () => {
      if (!id) return;
      const degree = await fetch(`/api/degree/degrees/${id}`).then(
        (response) => response.json()
      );

      // get the nodes: the rules + the top level node
      const root = {
        id: "d" + degree.id,
        type: "default",
        width: 300,
        data: {
          label: `${degree.program} ${degree.degree} in ${degree.major} with conc. ${degree.concentration} (${degree.year})`,
        },
        style: {
          background: "lightblue",
        },
      };

      const nodes = [];
      const edges = [];
      const stack = degree.rules.slice();
      while (stack.length > 0) {
        const rule = stack.pop();
        const id = `r${rule.id}`;
        nodes.push({
          id,
          type: "default",
          data: {
            label: renderRule(rule),
          },
          position: { x: 0, y: 0 },
          width: 300,
        });
        const source = rule.parent ? `r${rule.parent}` : `d${degree.id}`;
        if (source) {
          edges.push({
            source: source,
            target: id,
            id: `e${source.id}-${id}`,
            type: "smoothstep",
          });
        }
        rule.rules.forEach((subrule) => stack.push(subrule));
      }

      for (const doubleCountRestriction of degree.double_count_restrictions ||
        []) {
        const source = `r${doubleCountRestriction.rule}`;
        const target = `r${doubleCountRestriction.other_rule}`;
        edges.push({
          source,
          target,
          id: `c${source}-${target}`,
          type: "smoothstep",
          animated: true,
          style: { stroke: "red" },
        });
      }

      const { nodes: layoutedNodes, edges: layoutedEdges } =
        getLayoutedElements([root, ...nodes], edges);
      setNodes(layoutedNodes);
      setEdges(layoutedEdges);
    };
    fetchDegree();
  }, []);

  return (
    <ReactFlow
      nodes={nodes}
      edges={edges}
      onNodesChange={onNodesChange}
      onEdgesChange={onEdgesChange}
      onEdgeDelete={onEdgeDelete}
      minZoom={0.2}
      onConnect={onConnect}
      connectionLineType={ConnectionLineType.SmoothStep}
      fitView
    >
      <Controls />
      <Background variant="dots" gap={50} size={1} />
      <Panel
        position="top-right"
        style={{
          display: "flex",
          flexDirection: "column",
          gap: ".5em",
          padding: "1em",
          backgroundColor: "rgba(0, 0, 0, 0.4)",
        }}
      >
        <a href={`${window.location.pathname}?id=${id + 1}`}>Next Degree</a>
        {id > 1 && (
          <a href={`${window.location.pathname}?id=${id - 1}`}>Prev Degree</a>
        )}
      </Panel>
    </ReactFlow>
  );
};

const App = () => {
  return (
    <div class="editor">
      <LayoutFlow />
    </div>
  );
};

ReactDOM.render(<App />, document.getElementById("app"));
