import styled from "@emotion/styled";
import useSWR from "swr";
import { DockedCourse, User } from "@/types";
import { PanelBody, PanelContainer, PanelHeader } from "../FourYearPlan/PanelCommon";
import CourseInDock from "../Dock/CourseInDock";

const Title = styled.h2`
  margin: 0;
  font-size: 1.1rem;
  font-weight: 600;
  color: var(--primary-color-ultra-dark);
`;

const Courses = styled.div`
  display: flex;
  flex-wrap: wrap;
  gap: 0.75rem;
`;

const Empty = styled.p`
  margin: 2rem auto;
  max-width: 16rem;
  text-align: center;
  color: var(--primary-color-extra-dark);
`;

const DockedPanel = ({ user }: { user: User | null }) => {
  const { data: dockedCourses = [] } = useSWR<DockedCourse[]>(
    user ? `/api/degree/docked` : null
  );

  return (
    <PanelContainer>
      <PanelHeader>
        <Title>Docked courses</Title>
      </PanelHeader>
      <PanelBody>
        {dockedCourses.length ? (
          <Courses>
            {dockedCourses.map((course) => (
              <CourseInDock key={course.full_code} course={course} isDisabled={false} />
            ))}
          </Courses>
        ) : (
          <Empty>Courses you save for later show up here.</Empty>
        )}
      </PanelBody>
    </PanelContainer>
  );
};

export default DockedPanel;
