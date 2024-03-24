import { useDrag } from "react-dnd";
import { ItemTypes } from "../dnd/constants";
import { GrayIcon } from '../common/bulma_derived_components';
import styled from '@emotion/styled';
import { Course, DnDCourse, Fulfillment } from "@/types";
import { ReviewPanelTrigger } from "../Infobox/ReviewPanel";
import { Draggable } from "../common/DnD";
import Skeleton from "react-loading-skeleton"
import 'react-loading-skeleton/dist/skeleton.css'
import { DarkGrayIcon } from "../Requirements/QObject";

const COURSE_BORDER_RADIUS = "10px";

export const BaseCourseContainer = styled.div<{ $isDragging?: boolean, $isUsed: boolean, $isDisabled: boolean }>`
  display: flex;
  justify-content: center;
  align-items: center;
  min-width: 70px;
  min-height: 35px;
  border-radius: ${COURSE_BORDER_RADIUS};
  padding: .5rem;
  text-wrap: nowrap;
  cursor: ${props => props.$isDisabled || props.$isUsed ? "not-allowed" : "grab"};
  opacity: ${props => props.$isDisabled || props.$isDragging ? 0.7 : 1};
  background-color: ${props => props.$isDragging ? "#4B9AE7" : props.$isUsed ? "var(--primary-color)" : "var(--background-grey)"};
`;

export const PlannedCourseContainer = styled(BaseCourseContainer)`
  width: 100%;
  position: relative;
  opacity: ${props => props.$isDragging ? 0.5 : 1};

  .close-button {
    padding-left: 1rem;
    padding-right: 10px;
    margin-top: auto; 
    margin-bottom: auto;
    height: 100%;
    align-items: center;
    opacity: 0.6;
  }

  &:hover {
    .close-button {
      display: flex;
      opacity: unset;
    }
  }
`;

export const CourseXButton = ({ onClick }: { onClick?: (e: React.MouseEvent<HTMLInputElement>) => void }) => (
  <GrayIcon className="close-button" onClick={onClick}>
    <i className="fas fa-times"></i>
  </GrayIcon>
)

interface CoursePlannedProps {
  course: DnDCourse;
  removeCourse: (course: Course["full_code"]) => void;
  semester: Course["semester"];
  isUsed: boolean;
  isDisabled: boolean;
  className?: string;
  onClick?: (arg0: React.MouseEvent<HTMLInputElement>) => void;
}

export const SkeletonCourse = () => (
  <PlannedCourseContainer $isUsed={false} $isDisabled={false}>
      <div>
        <Skeleton width="5em"/>
      </div>
  </PlannedCourseContainer>
)

const CourseInPlan = ({ course, removeCourse, isUsed = false, isDisabled = false, className, onClick } : CoursePlannedProps) => {
  const [{ isDragging }, drag] = useDrag<DnDCourse, never, { isDragging: boolean }>(() => ({
    type: ItemTypes.COURSE_IN_PLAN,
    item: course,
    collect: (monitor) => ({
      isDragging: !!monitor.isDragging()
    })
  }), [course])

  return (
    <div onClick={onClick}>
      <Draggable
      isDragging={isDragging}
      >
        <ReviewPanelTrigger full_code={course.full_code}>
          <PlannedCourseContainer
          $isDragging={isDragging}
          $isUsed={isUsed}
          $isDisabled={isDisabled}
          ref={drag}
          className={className}
          >
              <div>
                {course.full_code}
              </div>
              <CourseXButton onClick={() => removeCourse(course.full_code)} hidden={!isUsed}/>
          </PlannedCourseContainer>
        </ReviewPanelTrigger>
      </Draggable>
    </div>
  )
}


export default CourseInPlan;