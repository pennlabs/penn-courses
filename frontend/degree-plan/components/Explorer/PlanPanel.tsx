import styled from "@emotion/styled";
import type { PlanCourse } from "./plan";

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

const Section = styled.h3`
  font-size: 0.8rem;
  font-weight: 600;
  margin: 1rem 0 0.4rem;
`;

const CourseButton = styled.button<{ $current: boolean }>`
  display: block;
  width: 100%;
  text-align: left;
  margin-bottom: 0.4rem;
  padding: 0.4rem 0.5rem;
  border: 1px solid ${({ $current }) => ($current ? "#d4a72c" : "#d0d4da")};
  border-radius: 4px;
  background: ${({ $current }) => ($current ? "#fff8c5" : "#fff")};
  cursor: pointer;
  font-size: 0.8rem;
  &:hover {
    background: ${({ $current }) => ($current ? "#fff1a8" : "#f6f8fa")};
  }
`;

const Muted = styled.div`
  color: #57606a;
  font-size: 0.72rem;
`;

const Flag = styled.span`
  margin-left: 0.4rem;
  color: #cf222e;
  font-size: 0.72rem;
`;

const count = (n: number, word: string) => `${n} ${word}${n === 1 ? "" : "s"}`;

interface CourseRowProps {
  planCourse: PlanCourse;
  current: boolean;
  onSelect: () => void;
}

const CourseRow = ({ planCourse, current, onSelect }: CourseRowProps) => {
  const { fulfillment, matches, programs } = planCourse;
  return (
    <CourseButton $current={current} onClick={onSelect}>
      {fulfillment.full_code.replace("-", " ")}
      {!fulfillment.legal && <Flag>not legal</Flag>}
      <Muted>
        {matches.length === 0
          ? "No requirements"
          : `${count(matches.length, "bucket")} · ${programs.map((p) => p.name).join(", ")}`}
      </Muted>
    </CourseButton>
  );
};

interface PlanPanelProps {
  name: string;
  planCourses: PlanCourse[];
  /** The course whose buckets are shown, if any. */
  current: string | null;
  /** Called with null when the current course is clicked again, to show the whole plan. */
  onSelect: (fullCode: string | null) => void;
}

/** A degree plan's courses: the double counts between its programs first, then every course. */
const PlanPanel = ({ name, planCourses, current, onSelect }: PlanPanelProps) => {
  const doubleCounts = planCourses.filter((c) => c.programs.length > 1);
  const row = (planCourse: PlanCourse) => {
    const fullCode = planCourse.fulfillment.full_code;
    return (
      <CourseRow
        key={fullCode}
        planCourse={planCourse}
        current={fullCode === current}
        onSelect={() => onSelect(fullCode === current ? null : fullCode)}
      />
    );
  };
  return (
    <Panel>
      <Heading>{name}</Heading>
      <Muted>
        {count(planCourses.length, "course")}. Click one to see only its buckets, and again to see
        the whole plan. ✓ marks where the plan put a course.
      </Muted>
      <Section>Double counts between programs ({doubleCounts.length})</Section>
      {doubleCounts.length === 0 ? <Muted>None</Muted> : doubleCounts.map(row)}
      <Section>All courses</Section>
      {planCourses.map(row)}
    </Panel>
  );
};

export default PlanPanel;
