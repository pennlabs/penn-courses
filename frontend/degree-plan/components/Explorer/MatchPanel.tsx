import { useEffect, useState } from "react";
import styled from "@emotion/styled";
import { ruleNodeId } from "./graph";
import type { Match, MatchableCourse } from "./matcher";
import type { Program } from "./programs";
import { ruleTitle } from "./ruleText";
import { verifyAgainstBackend, type VerifyResult } from "./verify";

const Panel = styled.aside`
  width: 300px;
  flex-shrink: 0;
  overflow-y: auto;
  border-right: 1px solid #d0d4da;
  background: #fff;
  padding: 1rem;
  font-size: 0.85rem;
`;

const Heading = styled.h2`
  font-size: 1rem;
  font-weight: 600;
  margin: 0 0 0.25rem;
`;

const ProgramName = styled.h3`
  font-size: 0.8rem;
  font-weight: 600;
  margin: 1rem 0 0.4rem;
`;

const MatchButton = styled.button`
  display: block;
  width: 100%;
  text-align: left;
  margin-bottom: 0.4rem;
  padding: 0.4rem 0.5rem;
  border: 1px solid #d4a72c;
  border-radius: 4px;
  background: #fff8c5;
  cursor: pointer;
  font-size: 0.8rem;
  &:hover {
    background: #fff1a8;
  }
`;

const Muted = styled.div`
  color: #57606a;
  font-size: 0.72rem;
`;

const VerifyBox = styled.div`
  margin-top: 1.25rem;
  padding-top: 0.75rem;
  border-top: 1px solid #d0d4da;
  button {
    padding: 0.3rem 0.7rem;
    border: 1px solid #d0d4da;
    border-radius: 4px;
    background: #fff;
    cursor: pointer;
  }
  ul {
    padding-left: 1.1rem;
  }
`;

type VerifyState =
  | { status: "idle" }
  | { status: "running"; done: number; total: number }
  | { status: "done"; result: VerifyResult }
  | { status: "error"; message: string };

/** Checks the matcher against the backend's own rule filter, one request per leaf. */
const Verify = ({ programs, course }: { programs: Program[]; course: MatchableCourse }) => {
  const [state, setState] = useState<VerifyState>({ status: "idle" });

  // A new course or selection makes the last result stale.
  useEffect(() => setState({ status: "idle" }), [programs, course]);

  const run = () => {
    setState({ status: "running", done: 0, total: 0 });
    verifyAgainstBackend(programs, course, (done, total) =>
      setState({ status: "running", done, total })
    )
      .then((result) => setState({ status: "done", result }))
      .catch((error: Error) => setState({ status: "error", message: error.message }));
  };

  return (
    <VerifyBox>
      {state.status === "running" ? (
        <Muted>
          Checking {state.done} of {state.total || "…"} rules…
        </Muted>
      ) : (
        <button onClick={run}>Check against backend</button>
      )}
      {state.status === "done" &&
        (state.result.disagreements.length === 0 ? (
          <p>The backend agrees on all {state.result.checked} rules.</p>
        ) : (
          <>
            <p>
              The backend disagrees on {state.result.disagreements.length} of{" "}
              {state.result.checked} rules:
            </p>
            <ul>
              {state.result.disagreements.map(({ rule, ours, backend }) => (
                <li key={rule.id}>
                  {ruleTitle(rule)} (rule {rule.id}): explorer says {ours ? "yes" : "no"},
                  backend says {backend ? "yes" : "no"}
                </li>
              ))}
            </ul>
          </>
        ))}
      {state.status === "error" && <p>{state.message}</p>}
    </VerifyBox>
  );
};

interface MatchPanelProps {
  course: MatchableCourse;
  title: string;
  programs: Program[];
  matches: Match[];
  onSelect: (nodeId: string) => void;
}

/** Lists every requirement the searched course can count toward, grouped by program. */
const MatchPanel = ({ course, title, programs, matches, onSelect }: MatchPanelProps) => (
  <Panel>
    <Heading>{course.full_code.replace("-", " ")}</Heading>
    <Muted>{title}</Muted>
    <p>
      Can count toward {matches.length} requirement{matches.length === 1 ? "" : "s"} in the
      selected programs.
    </p>
    {programs.map((program) => {
      const own = matches.filter((m) => m.program === program);
      return (
        <section key={program.key}>
          <ProgramName>{program.name}</ProgramName>
          {own.length === 0 && <Muted>No requirements</Muted>}
          {own.map(({ leaf, path }) => (
            <MatchButton key={leaf.id} onClick={() => onSelect(ruleNodeId(program, leaf))}>
              {ruleTitle(leaf)}
              {path.length > 1 && (
                <Muted>{path.slice(0, -1).map(ruleTitle).join(" › ")}</Muted>
              )}
            </MatchButton>
          ))}
        </section>
      );
    })}
    <Verify programs={programs} course={course} />
  </Panel>
);

export default MatchPanel;
