import { ChevronDownIcon } from "@radix-ui/react-icons";
import styled from "@emotion/styled";
import { useState } from "react";
import { CourseLevel } from "@/utils/parseUtils";
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

  svg {
    transition: transform 0.15s ease;
  }

  &[aria-expanded="true"] svg {
    transform: rotate(180deg);
  }
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

const RecordHeading = styled.h3`
  margin: 0;
  padding-top: 14px;
  font-size: 15px;
  font-weight: 600;
  color: ${color.text};
`;

const SHARED_COURSE_BACKGROUND = "#d6ebdf";

const CourseChip = styled.span<{ $shared: boolean }>`
  font-size: 12.5px;
  font-weight: 500;
  padding: 4px 8px;
  border-radius: 6px;
  background: ${({ $shared }) => ($shared ? SHARED_COURSE_BACKGROUND : "#ffffff")};
  border: 1px solid ${color.border};
  color: ${color.text};
`;

const formatTermName = (sem: string) =>
  sem === "_TRAN" ? "Transfer credit" : sem[0].toUpperCase() + sem.slice(1);

const pluralize = (n: number, word: string) => `${n} ${word}${n === 1 ? "" : "s"}`;

type ScrapedSemester = { sem: string; courses: string[] };

const RECORDS: { title: string; counts: (level?: CourseLevel) => boolean }[] = [
  { title: "Bachelors", counts: (level) => level !== "GRADUATE" },
  { title: "Masters", counts: (level) => level === "GRADUATE" || level === "SHARED" },
];

type ImportedCoursesProps = {
  // Terms read from the transcript, each with its course codes.
  scrapedCourses: ScrapedSemester[];
  // Which transcript record each course is on; empty unless the transcript has a masters record.
  courseLevels?: { [course: string]: CourseLevel };
};

export default function ImportedCourses({
  scrapedCourses,
  courseLevels = {},
}: ImportedCoursesProps) {
  const [open, setOpen] = useState(false);

  if (scrapedCourses.length === 0) return null;

  const total = scrapedCourses.reduce((sum, term) => sum + term.courses.length, 0);

  const levels = Object.values(courseLevels);
  const hasMastersRecord = levels.some((level) => level !== "UNDERGRADUATE");
  const hasSharedCourses = levels.some((level) => level === "SHARED");
  const records: { title: string | null; terms: ScrapedSemester[] }[] = hasMastersRecord
    ? RECORDS.map(({ title, counts }) => ({
        title,
        terms: scrapedCourses
          .map((term) => ({
            ...term,
            courses: term.courses.filter((course) => counts(courseLevels[course])),
          }))
          .filter((term) => term.courses.length > 0),
      }))
    : [{ title: null, terms: scrapedCourses }];

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
          <ChevronDownIcon width={16} height={16} />
        </Toggle>
      </Summary>
      {open && (
        <List id="imported-courses" aria-label="Imported courses">
          <Note>You can edit these on the next step.</Note>
          {records.map(({ title, terms }) => (
            <section key={title ?? "courses"} aria-label={title ?? undefined}>
              {title && <RecordHeading>{title}</RecordHeading>}
              {title === "Masters" && hasSharedCourses && (
                <Note>Highlighted courses are on both records and count toward both degrees.</Note>
              )}
              {terms.map((term) => (
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
                      <CourseChip key={course} $shared={courseLevels[course] === "SHARED"}>
                        {course.toUpperCase()}
                      </CourseChip>
                    ))}
                  </div>
                </Term>
              ))}
            </section>
          ))}
        </List>
      )}
    </Container>
  );
}
