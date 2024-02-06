import React, { useCallback, useState, useEffect } from "https://cdn.jsdelivr.net/npm/react@18.2.0/+esm";
import ReactDOM from "https://cdn.jsdelivr.net/npm/react-dom@18.2.0/+esm";
import ReactFlow, {
  addEdge,
  ConnectionLineType,
  Panel,
  useNodesState,
  useEdgesState,
} from "https://cdn.jsdelivr.net/npm/reactflow@11.7.4/+esm";
import dagre from "https://esm.sh/dagre@0.8.5";

const params = new Proxy(new URLSearchParams(window.location.search), {
  get: (searchParams, prop) => searchParams.get(prop),
});
const nodeWidth = 172;
const nodeHeight = 36;

const dagreGraph = new dagre.graphlib.Graph();
dagreGraph.setDefaultEdgeLabel(() => ({}));
const renderRule = (rule) => {
  const excludeKeys = ["course", "rules"]
  const rows = Object.entries(rule)
  .filter(([key, value]) => value && !excludeKeys.includes(key))
  .map(([key, value]) => (
    <tr>
      <td style={{ fontWeight: "bold" }}>{key}</td>
      <td>{value}</td>
    </tr>
  ))

  return (
    <>
      <table style={{ border: "none" }}>
        {rows}
      </table>
    </>
  )
};

const getLayoutedElements = (nodes, edges, direction = 'TB') => {
  const isHorizontal = direction === 'LR';
  dagreGraph.setGraph({ rankdir: direction });

  nodes.forEach((node) => {
    dagreGraph.setNode(
      node.id, 
      { 
        width: nodeWidth, // node.__rf.width, 
        height: nodeHeight // node.__rf.width 
      }
    );
  });

  edges.forEach((edge) => {
    dagreGraph.setEdge(edge.source, edge.target);
  });

  dagre.layout(dagreGraph);

  nodes.forEach((node) => {
    const nodeWithPosition = dagreGraph.node(node.id);
    // const nodeWidth = node.__rf.width;
    // const nodeHeight = node.__rf.height;
    node.targetPosition = isHorizontal ? 'left' : 'top';
    node.sourcePosition = isHorizontal ? 'right' : 'bottom';

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

const LayoutFlow = () => {
  const [nodes, setNodes, onNodesChange] = useNodesState([]);
  const [edges, setEdges, onEdgesChange] = useEdgesState([]);

  const onConnect = useCallback(
    (params) =>
      setEdges((eds) =>
        addEdge({ ...params, type: ConnectionLineType.SmoothStep, animated: true }, eds)
      ),
    []
  );
  const onLayout = useCallback(
    (direction) => {
      const { nodes: layoutedNodes, edges: layoutedEdges } = getLayoutedElements(
        nodes,
        edges,
        direction
      );

      setNodes([...layoutedNodes]);
      setEdges([...layoutedEdges]);
    },
    [nodes, edges]
  );
  
  useEffect(() => {
    const fetchDegree = async () => {
      if (!params.id) return;

      const degree = await fetch(`/api/degree/degrees/${params.id}/`).then(response => response.json());
      
      // get the nodes: the rules + the top level node
      const group = { 
        id:  "d" + degree.id, 
        type: "group", 
        data: { label: `${degree.program} ${degree.degree} in ${degree.major} with conc. ${degree.concentration} (${degree.year})` },
      };
      
      const nodes = [];
      const edges = [];
      const stack = degree.rules.slice();
      while (stack.length > 0) {
        const rule = stack.pop();
        const id = `r${rule.id}+${group.id}`;
        nodes.push({
          id,
          type: "default",
          data: { 
            label: `${rule.id}`
          },
          parent: group.id,
          position: { x: 0, y: 0}
        });
        const source = rule.parent ? `r${rule.parent}+${group.id}` : null;
        if (source) {
          edges.push({ 
            source: source, 
            target: id,
            id: `e${source.id}-${id}`,
            type: "smoothstep",
          })
        };
        rule.rules.forEach((subrule) => stack.push(subrule));
      }

      const { nodes: layoutedNodes, edges: layoutedEdges } = getLayoutedElements([group, ...nodes], edges); 
      setNodes(layoutedNodes);
      setEdges(layoutedEdges);
    }
    fetchDegree();
  }, [])

  return (
    <ReactFlow
      nodes={nodes}
      edges={edges}
      onNodesChange={onNodesChange}
      onEdgesChange={onEdgesChange}
      onConnect={onConnect}
      connectionLineType={ConnectionLineType.SmoothStep}
      fitView
    >
      <Panel position="top-right">
        <button onClick={() => onLayout('TB')}>vertical layout</button>
        <button onClick={() => onLayout('LR')}>horizontal layout</button>
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

ReactDOM.render(<App />, document.getElementById('app'));

