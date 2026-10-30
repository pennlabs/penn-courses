import { Fragment } from "react";
import styled from "@emotion/styled";
import type { Rule } from "@/types";
import { isLeaf } from "./graph";
import type { Program } from "./programs";
import { qToText } from "./qToText";
import { blockText, requirementText, ruleTitle, shareTargetText } from "./ruleText";

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

const ProgramDetails = ({ program }: { program: Program }) => (
  <>
    <Heading>{program.name}</Heading>
    <Fields>
      {program.facts.map(([label, value]) => (
        <Fragment key={label}>
          <dt>{label}</dt>
          <dd>{value}</dd>
        </Fragment>
      ))}
    </Fields>
  </>
);

interface DetailPanelProps {
  /** The selected rule, if a rule is selected. */
  rule: Rule | null;
  /** The selected program, if a program's own node is selected. */
  program: Program | null;
}

const DetailPanel = ({ rule, program }: DetailPanelProps) =>
  rule ? (
    <section>
      <RuleDetails rule={rule} />
    </section>
  ) : program ? (
    <section>
      <ProgramDetails program={program} />
    </section>
  ) : null;

export default DetailPanel;
