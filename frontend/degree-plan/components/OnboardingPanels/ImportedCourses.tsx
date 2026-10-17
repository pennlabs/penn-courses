import { ChevronDownIcon } from "@radix-ui/react-icons";
import styled from "@emotion/styled";
import { useState } from "react";
import { color } from "./onboardingStyles";

const Container = styled.div`
  display: flex;
  flex-direction: column;
  gap: 20px;
`;

const Summary = styled.p`
  margin: 0;
  display: flex;
  align-items: center;
  flex-wrap: wrap;
  gap: 6px;
  font-size: 15px;
  color: ${color.muted};
`;

const Toggle = styled.button`
  display: inline-flex;
  align-items: center;
  gap: 2px;
  padding: 0;
  border: 0;
  background: transparent;
  font: inherit;
  font-weight: 500;
  color: ${color.accent};
  cursor: pointer;

  &:hover {
    color: ${color.accentHover};
  }
`;

const Chevron = styled(ChevronDownIcon)<{ $open: boolean }>`
  transform: rotate(${({ $open }) => ($open ? 180 : 0)}deg);
  transition: transform 0.15s ease;
`;

const List = styled.div`
  display: flex;
  flex-direction: column;
  padding: 0 20px;
  background: #f8f9fb;
  border: 1px solid ${color.border};
  border-radius: 12px;
`;

const Term = styled.div`
  display: grid;
  grid-template-columns: 160px 1fr;
  gap: 16px;
  padding: 14px 0;
  border-top: 1px solid #eceef2;

  @media (max-width: 600px) {
    grid-template-columns: 1fr;
    gap: 8px;
  }
`;

const Note = styled.p`
  margin: 0;
  padding: 14px 0;
  font-size: 14px;
  color: ${color.muted};
`;

const CourseChip = styled.span`
  font-size: 12.5px;
  font-weight: 500;
  padding: 4px 8px;
  border-radius: 6px;
  background: #ffffff;
  border: 1px solid ${color.border};
  color: ${color.text};
`;

const formatTermName = (sem: string) =>
  sem === "_TRAN" ? "Transfer credit" : sem[0].toUpperCase() + sem.slice(1);

const pluralize = (n: number, word: string) => `${n} ${word}${n === 1 ? "" : "s"}`;

type ImportedCoursesProps = {
  // Terms read from the transcript, each with its course codes.
  scrapedCourses: { sem: string; courses: string[] }[];
};

export default function ImportedCourses({ scrapedCourses }: ImportedCoursesProps) {
  const [open, setOpen] = useState(false);

  if (scrapedCourses.length === 0) return null;

  const total = scrapedCourses.reduce((sum, term) => sum + term.courses.length, 0);

  return (
    <Container>
      <Summary>
        {pluralize(total, "course")} imported from your transcript.
        <Toggle
          type="button"
          aria-expanded={open}
          aria-controls="imported-courses"
          onClick={() => setOpen((o) => !o)}
        >
          {open ? "Hide courses" : "Show courses"}
          <Chevron $open={open} width={16} height={16} />
        </Toggle>
      </Summary>
      {open && (
        <List id="imported-courses" aria-label="Imported courses">
          <Note>You can edit these on the next step.</Note>
          {scrapedCourses.map((term) => (
            <Term key={term.sem}>
              <div style={{ display: "flex", flexDirection: "column", gap: 2 }}>
                <span style={{ fontSize: 14, fontWeight: 600 }}>
                  {formatTermName(term.sem)}
                </span>
                <span style={{ fontSize: 13, color: color.muted }}>
                  {pluralize(term.courses.length, "course")}
                </span>
              </div>
              <div
                style={{
                  display: "flex",
                  flexWrap: "wrap",
                  gap: 6,
                  alignContent: "flex-start",
                }}
              >
                {term.courses.map((course) => (
                  <CourseChip key={course}>{course.toUpperCase()}</CourseChip>
                ))}
              </div>
            </Term>
          ))}
        </List>
      )}
    </Container>
  );
}
