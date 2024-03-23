import { useDrag } from "react-dnd";
import { ItemTypes } from "../dnd/constants";
import { GrayIcon } from '../common/bulma_derived_components';
import styled from '@emotion/styled';
import { Course, DnDCourse, Fulfillment } from "@/types";
import { ReviewPanelTrigger } from "../Infobox/ReviewPanel";
import { Draggable } from "../common/DnD";
import Skeleton from "react-loading-skeleton"
import 'react-loading-skeleton/dist/skeleton.css'

export const BaseCourseContainer = styled.div<{ $isDragging?: boolean, $isUsed: boolean, $isDisabled: boolean }>`
  display: flex;
  justify-content: center;
  align-items: center;
  min-width: 70px;
  min-height: 35px;
  border-radius: 10px;
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
    display: none;
    position: absolute;
    right: 5px;
    top: 0; 
    bottom: 0; 
    margin-top: auto; 
    margin-bottom: auto;
    height: 1.5rem;
  }

  &:hover {
    .close-button {
      display: unset;
    }
  }
`;

interface CoursePlannedProps {
  course: DnDCourse;
  removeCourse: (course: Course["full_code"]) => void;
  semester: Course["semester"];
  isUsed: boolean;
  isDisabled: boolean;
  className?: string;
  onClick?: () => void;
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
              {isUsed &&
                <GrayIcon className="close-button" onClick={() => removeCourse(course.full_code)}>
                  <i className="fas fa-times"></i>
                </GrayIcon>
                }
          </PlannedCourseContainer>
        </ReviewPanelTrigger>
      </Draggable>
    </div>
  )
}


export default CourseInPlan;