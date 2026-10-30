import styled from "@emotion/styled";
import type { Degree, Rule } from "@/types";
import { isLeaf } from "./graph";
import { qToText } from "./qToText";
import { blockText, requirementText, ruleTitle, shareTargetText } from "./ruleText";

const Panel = styled.aside`
  width: 340px;
  flex-shrink: 0;
  overflow-y: auto;
  border-left: 1px solid #d0d4da;
  background: #fff;
  padding: 1rem;
  font-size: 0.85rem;
`;

const Heading = styled.h2`
  font-size: 1rem;
  font-weight: 600;
  margin: 0 0 0.75rem;
`;

const Fields = styled.dl`
  display: grid;
  grid-template-columns: max-content 1fr;
  gap: 0.4rem 0.75rem;
  margin: 0;
  dt {
    color: #57606a;
  }
  dd {
    margin: 0;
    word-break: break-word;
  }
`;

const Code = styled.pre`
  margin: 0;
  padding: 0.5rem;
  background: #f6f8fa;
  border-radius: 4px;
  font-size: 0.72rem;
  white-space: pre-wrap;
  word-break: break-word;
`;

const Hint = styled.p`
  color: #57606a;
`;

const RuleDetails = ({ rule }: { rule: Rule }) => (
  <>
    <Heading>{ruleTitle(rule)}</Heading>
    <Fields>
      <dt>Rule id</dt>
      <dd>{rule.id}</dd>
      <dt>Kind</dt>
      <dd>{isLeaf(rule) ? "Leaf (matches courses)" : `Group of ${rule.rules.length} rules`}</dd>
      <dt>Requires</dt>
      <dd>{requirementText(rule) || "—"}</dd>
      {isLeaf(rule) && (
        <>
          <dt>Courses</dt>
          <dd>{qToText(rule.q_json) || "—"}</dd>
        </>
      )}
      <dt>Block</dt>
      <dd>{blockText(rule) || "—"}</dd>
      <dt>Shares with</dt>
      <dd>{shareTargetText(rule) || "Nothing"}</dd>
      <dt>AP / transfer</dt>
      <dd>{rule.transfer_credit_allowed ? "Allowed" : "Not allowed"}</dd>
      {rule.concentration && (
        <>
          <dt>Concentration</dt>
          <dd>{rule.concentration}</dd>
        </>
      )}
    </Fields>
    {rule.q && (
      <details style={{ marginTop: "1rem" }}>
        <summary>Raw q</summary>
        <Code>{rule.q}</Code>
      </details>
    )}
  </>
);

const DegreeDetails = ({ degree }: { degree: Degree }) => (
  <>
    <Heading>
      {degree.degree} {degree.major_name || degree.major}
    </Heading>
    <Fields>
      <dt>Degree id</dt>
      <dd>{degree.id}</dd>
      <dt>Program</dt>
      <dd>{degree.program}</dd>
      <dt>Major</dt>
      <dd>{degree.major}</dd>
      <dt>Concentration</dt>
      <dd>{degree.concentration_name || degree.concentration || "—"}</dd>
      <dt>Year</dt>
      <dd>{degree.year}</dd>
      <dt>Top-level rules</dt>
      <dd>{degree.rules.length}</dd>
    </Fields>
  </>
);

interface DetailPanelProps {
  degree: Degree;
  /** The selected rule, or null when the degree itself (or nothing) is selected. */
  rule: Rule | null;
  degreeSelected: boolean;
}

const DetailPanel = ({ degree, rule, degreeSelected }: DetailPanelProps) => (
  <Panel>
    {rule ? (
      <RuleDetails rule={rule} />
    ) : degreeSelected ? (
      <DegreeDetails degree={degree} />
    ) : (
      <Hint>Click a node to see its details. Use + to expand a group.</Hint>
    )}
  </Panel>
);

export default DetailPanel;
