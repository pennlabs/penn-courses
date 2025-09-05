import { ConnectDragSource } from "react-dnd";
import { GrayIcon } from '../common/bulma_derived_components';
import styled from '@emotion/styled';
import { Course, DnDCourse, Fulfillment } from "@/types";
import { ReviewPanelTrigger } from "../Infobox/ReviewPanel";
import { Draggable } from "../common/DnD";
import Skeleton from "react-loading-skeleton"
import 'react-loading-skeleton/dist/skeleton.css'
import { TRANSFER_CREDIT_SEMESTER_KEY } from "@/constants";
import { Icon } from "../common/bulma_derived_components";
import { Tooltip } from "react-tooltip";
import { ItemTypes } from "../Dock/dnd/constants";

const COURSE_BORDER_RADIUS = "9px";

export const BaseCourseContainer = styled.div<{ $isDragging?: boolean, $isUsed: boolean, $isDisabled: boolean }>`
  display: flex;
  justify-content: center;
  align-items: center;
  min-width: 70px;
  min-height: 35px;
  border-radius: ${COURSE_BORDER_RADIUS};
  padding: .75rem;
  text-wrap: nowrap;
  cursor: ${props => props.$isDisabled || props.$isUsed ? "not-allowed" : "grab"};
  opacity: ${props => props.$isDisabled || props.$isDragging ? 0.7 : 1};
  background-color: ${props => props.$isDragging ? "#4B9AE7" : "var(--background-grey)"};
  box-shadow: rgba(0, 0, 0, 0.01) 0px 6px 5px 0px, rgba(0, 0, 0, 0.04) 0px 0px 0px 1px;
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

  .illegal-icon {
    padding-right: 0.5rem;
    margin-top: auto; 
    margin-bottom: auto;
  }

  &:hover {
    .close-button {
      opacity: unset;
    }
  }
`;



const CloseIcon = styled(GrayIcon) <{ $hidden: boolean }>`
  visibility: ${props => props.$hidden ? "hidden" : "visible"};
`

export const CourseXButton = ({ onClick, hidden }: { onClick?: (e: React.MouseEvent<HTMLInputElement>) => void, hidden: boolean }) => (
  <CloseIcon className="close-button" onClick={onClick} $hidden={hidden}>
    <i className="fas fa-times"></i>
  </CloseIcon>
)

interface DraggableComponentProps {
  courseType: string
  course: DnDCourse;
  removeCourse: (course: Course["id"]) => void;
  semester?: Course["semester"];
  isUsed: boolean;
  isDisabled: boolean;
  isDragging: boolean;
  fulfillment?: Fulfillment;
  className?: string;
  onClick?: (arg0: React.MouseEvent<HTMLInputElement>) => void;
  dragRef: ConnectDragSource;
}


export const SkeletonCourse = () => (
  <PlannedCourseContainer $isUsed={false} $isDisabled={false}>
    <div>
      <Skeleton width="5em" />
    </div>
  </PlannedCourseContainer>
)

const CourseBadge = styled.div`
  display: flex;
  flex-direction: row;
  align-items: center;
  gap: 0.25rem;
`

const IconBadge = styled.div`
  padding: 0.2rem;
  border-radius: 5px;
  display: flex;
  flex-direction: row;
  align-items:center;
  gap: 0.07rem;
  background-color: #EBEBEB;

  p {
    font-size: 14px;
    font-weight: bold;
  }

`

const YellowExclamationIcon = () => {
  const YellowExclamation = styled(Icon)`
    width: 1.1rem;
    height: 1.1rem;
    flex-shrink: 0;
    fill: #E6BB4E;
    margin-left: 0.5rem;
  `

  return (
    <YellowExclamation>
      <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 512 512">
        <path d="M256 512A256 256 0 1 0 256 0a256 256 0 1 0 0 512zm0-384c13.3 0 24 10.7 24 24l0 112c0 13.3-10.7 24-24 24s-24-10.7-24-24l0-112c0-13.3 10.7-24 24-24zM224 352a32 32 0 1 1 64 0 32 32 0 1 1 -64 0z" />
      </svg>
    </YellowExclamation>
  )
}

const RedExclamationIcon = () => {
  return (
    <svg className="illegal-icon" width="22" height="22" viewBox="0 0 21 21" fill="none" xmlns="http://www.w3.org/2000/svg">
      <path d="M10.709 20.9102C5.26953 20.9102 0.748047 16.3887 0.748047 10.9492C0.748047 5.5 5.25977 0.988281 10.6992 0.988281C16.1484 0.988281 20.6699 5.5 20.6699 10.9492C20.6699 16.3887 16.1582 20.9102 10.709 20.9102ZM10.6992 12.7656C11.1875 12.7656 11.4707 12.4922 11.4805 11.9648L11.6172 6.65234C11.627 6.13477 11.2266 5.75391 10.6895 5.75391C10.1426 5.75391 9.76172 6.125 9.77148 6.64258L9.89844 11.9648C9.9082 12.4824 10.1914 12.7656 10.6992 12.7656ZM10.6992 16.0371C11.2852 16.0371 11.793 15.5781 11.793 14.9922C11.793 14.4062 11.2949 13.9375 10.6992 13.9375C10.1035 13.9375 9.60547 14.416 9.60547 14.9922C9.60547 15.5684 10.1133 16.0371 10.6992 16.0371Z" fill="#E66161" />
    </svg>
  )
}

const SemesterIcon = ({ semester }: { semester: string | null }) => {
  if (!semester) return <div></div>;
  const year = semester === TRANSFER_CREDIT_SEMESTER_KEY ? "AP" : semester.substring(2, 4);
  const sem = semester.substring(4);

  return (
    <IconBadge>
      <p>{year}</p>
      {sem === "A" && <i className="spring-icon"></i>}
      {sem === "B" && <i className="summer-icon"></i>}
      {sem === "C" && <i className="fall-icon"></i>}
    </IconBadge>
  )
}

const CourseComponent = ({ courseType, course, fulfillment, removeCourse, isUsed = false, isDisabled = false, className, onClick, isDragging, dragRef }: DraggableComponentProps) => (
  <Draggable
    isDragging={isDragging}
    onClick={onClick}
  >
    <ReviewPanelTrigger full_code={course.full_code} triggerType="click">
      <PlannedCourseContainer
        $isDragging={isDragging}
        $isUsed={isUsed}
        $isDisabled={isDisabled}
        ref={dragRef}
        className={className}
      >
        {fulfillment && !fulfillment?.legal &&
        <>
          <a
            data-tooltip-id={fulfillment.full_code + courseType}
            data-tooltip-content="This course is being illegally double counted in your plan!"
          >
            <RedExclamationIcon />
          </a>
          <Tooltip id={fulfillment.full_code + courseType} place="top" />
</>

        }
        <CourseBadge>
          {course.full_code.replace("-", " ")}
          {!!fulfillment && fulfillment.semester !== "" && <SemesterIcon semester={fulfillment.semester} />}
        </CourseBadge>
        {isUsed && <CourseXButton onClick={(e) => { removeCourse(course.full_code); e.stopPropagation(); }} hidden={false} />}
      </PlannedCourseContainer>
    </ReviewPanelTrigger>
  </Draggable>
)

export default CourseComponent;