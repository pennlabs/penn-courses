import { ConnectDragSource } from "react-dnd";
import { GrayIcon } from '../common/bulma_derived_components';
import styled from '@emotion/styled';
import { Course, DnDCourse } from "@/types";
import { ReviewPanelTrigger } from "../Infobox/ReviewPanel";
import { Draggable } from "../common/DnD";
import Skeleton from "react-loading-skeleton"
import 'react-loading-skeleton/dist/skeleton.css'

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
  background-color: ${props => props.$isDragging ? "#4B9AE7" : "var(--background-grey)"};
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
      opacity: unset;
    }
  }
`;

const CloseIcon = styled(GrayIcon)<{ $hidden: boolean }>`
  visibility: ${props => props.$hidden ? "hidden" : "visible"};
`

export const CourseXButton = ({ onClick, hidden }: { onClick?: (e: React.MouseEvent<HTMLInputElement>) => void, hidden: boolean }) => (
  <CloseIcon className="close-button" onClick={onClick} $hidden={hidden}>
    <i className="fas fa-times"></i>
  </CloseIcon>
)

interface DraggableComponentProps {
  course: DnDCourse;
  removeCourse: (course: Course["id"]) => void;
  semester?: Course["semester"];
  isUsed: boolean;
  isDisabled: boolean;
  isDragging: boolean;
  className?: string;
  onClick?: (arg0: React.MouseEvent<HTMLInputElement>) => void;
  dragRef: ConnectDragSource;
}

export const SkeletonCourse = () => (
  <PlannedCourseContainer $isUsed={false} $isDisabled={false}>
      <div>
        <Skeleton width="5em"/>
      </div>
  </PlannedCourseContainer>
)

const CourseComponent = ({ course, removeCourse, isUsed = false, isDisabled = false, className, onClick, isDragging, dragRef } : DraggableComponentProps) => (
    <Draggable
    isDragging={isDragging}
    onClick={onClick}
    >
    <ReviewPanelTrigger full_code={course.full_code}>
        <PlannedCourseContainer
        $isDragging={isDragging}
        $isUsed={isUsed}
        $isDisabled={isDisabled}
        ref={dragRef}
        className={className}
        >
            <div>
            {course.full_code}
            </div>
            {isUsed && <CourseXButton onClick={() => removeCourse(course.full_code)} hidden={false}/>}
        </PlannedCourseContainer>
    </ReviewPanelTrigger>
    </Draggable>
)

export default CourseComponent;