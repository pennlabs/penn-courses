import { createContext, memo, useContext } from "react";
import styled from "@emotion/styled";
import { Handle, Position, type NodeProps } from "@xyflow/react";
import type { DegreeNode, GroupNode, LeafNode } from "./graph";
import { NODE_HEIGHT, NODE_WIDTH } from "./graph";
import { blockText, requirementText, ruleTitle } from "./ruleText";
import { qToText } from "./qToText";

/** Lets a node expand or collapse itself without putting callbacks in node data. */
export const ToggleContext = createContext<(id: string) => void>(() => {});

const Card = styled.div<{ $selected: boolean; $accent: string; $height: number }>`
  width: ${NODE_WIDTH}px;
  height: ${({ $height }) => $height}px;
  box-sizing: border-box;
  padding: 0.5rem 0.75rem;
  border-radius: 6px;
  background: #fff;
  border: 1px solid ${({ $selected }) => ($selected ? "#1a73e8" : "#d0d4da")};
  border-left: 4px solid ${({ $accent }) => $accent};
  box-shadow: ${({ $selected }) => ($selected ? "0 0 0 2px #1a73e855" : "0 1px 2px #0001")};
  font-size: 0.8rem;
  display: flex;
  flex-direction: column;
  gap: 0.2rem;
  overflow: hidden;
`;

const TopRow = styled.div`
  display: flex;
  align-items: flex-start;
  gap: 0.4rem;
`;

const Title = styled.div<{ $lines?: number }>`
  flex: 1;
  font-weight: 600;
  color: #1f2328;
  overflow: hidden;
  display: -webkit-box;
  -webkit-line-clamp: ${({ $lines }) => $lines ?? 1};
  -webkit-box-orient: vertical;
`;

const Meta = styled.div`
  color: #57606a;
  font-size: 0.72rem;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
`;

const Query = styled.div`
  color: #3d4450;
  font-family: ui-monospace, monospace;
  font-size: 0.7rem;
  overflow: hidden;
  display: -webkit-box;
  -webkit-line-clamp: 2;
  -webkit-box-orient: vertical;
`;

const ToggleButton = styled.button`
  flex-shrink: 0;
  width: 22px;
  height: 22px;
  border-radius: 4px;
  border: 1px solid #d0d4da;
  background: #f6f8fa;
  cursor: pointer;
  font-size: 0.85rem;
  line-height: 1;
  &:hover {
    background: #eaeef2;
  }
`;

const Toggle = ({ id, expanded }: { id: string; expanded: boolean }) => {
  const toggle = useContext(ToggleContext);
  return (
    <ToggleButton
      // "nodrag" stops React Flow from treating the click as the start of a drag
      className="nodrag"
      title={expanded ? "Collapse" : "Expand"}
      onClick={(e) => {
        e.stopPropagation();
        toggle(id);
      }}
    >
      {expanded ? "−" : "+"}
    </ToggleButton>
  );
};

const Handles = ({ source = true, target = true }) => (
  <>
    {target && <Handle type="target" position={Position.Left} isConnectable={false} />}
    {source && <Handle type="source" position={Position.Right} isConnectable={false} />}
  </>
);

const join = (parts: (string | false | null | undefined)[]) => parts.filter(Boolean).join(" · ");

export const DegreeNodeView = memo(({ id, data, selected }: NodeProps<DegreeNode>) => {
  const { degree, expanded } = data;
  return (
    <Card $selected={!!selected} $accent="#1f2328" $height={NODE_HEIGHT.degree}>
      <Handles target={false} />
      <TopRow>
        <Title>{join([degree.degree, degree.major_name || degree.major])}</Title>
        <Toggle id={id} expanded={expanded} />
      </TopRow>
      <Meta>
        {join([degree.program, String(degree.year), degree.concentration_name || degree.concentration])}
      </Meta>
      <Meta>{degree.rules.length} top-level rules</Meta>
    </Card>
  );
});
DegreeNodeView.displayName = "DegreeNodeView";

export const GroupNodeView = memo(({ id, data, selected }: NodeProps<GroupNode>) => {
  const { rule, leafCount, expanded } = data;
  return (
    <Card $selected={!!selected} $accent="#8250df" $height={NODE_HEIGHT.group}>
      <Handles />
      <TopRow>
        <Title $lines={2}>{ruleTitle(rule)}</Title>
        <Toggle id={id} expanded={expanded} />
      </TopRow>
      <Meta>
        {join([requirementText(rule), !expanded && `${leafCount} leaves`, blockText(rule)])}
      </Meta>
    </Card>
  );
});
GroupNodeView.displayName = "GroupNodeView";

export const LeafNodeView = memo(({ data, selected }: NodeProps<LeafNode>) => {
  const { rule } = data;
  return (
    <Card $selected={!!selected} $accent="#1a7f37" $height={NODE_HEIGHT.leaf}>
      <Handles source={false} />
      <Title>{ruleTitle(rule)}</Title>
      <Meta>
        {join([requirementText(rule), rule.share_targets.length > 0 && "can double count"])}
      </Meta>
      {/* Untitled leaves already show their query as the title */}
      {rule.title && <Query>{qToText(rule.q_json)}</Query>}
    </Card>
  );
});
LeafNodeView.displayName = "LeafNodeView";

export const nodeTypes = {
  degree: DegreeNodeView,
  group: GroupNodeView,
  leaf: LeafNodeView,
};
