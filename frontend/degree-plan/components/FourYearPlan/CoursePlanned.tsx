import { useState } from "react";
import { useDrag } from "react-dnd";
import { ItemTypes } from "../dnd/constants";
import { GrayIcon } from '../bulma_derived_components';
import styled from '@emotion/styled';
import { Course } from "@/types";
import { ReviewPanelTrigger } from "../Infobox/ReviewPanel";

export const BaseCourseContainer = styled.span<{ $isDragging: boolean }>`
  display: flex;
  justify-content: center;
  align-items: center;
  min-width: 70px;
  min-height: 35px;
  background: #F2F3F4;
  border-radius: 10px;
  padding: .5rem;
  text-wrap: nowrap;
  opacity: ${props => props.$isDragging ? 0.5 : 1};
  background-color: ${props => props.$isDragging ? "#4B9AE7" : "#F2F3F4"};
`;

export const PlannedCourseContainer = styled(BaseCourseContainer)`
  width: 100%;
  position: relative;
  opacity: ${props => props.$isDragging ? 0.5 : 1};
`;

const RemoveCourseButton = styled.div<{ isDragging: boolean }>`
  position: absolute;
  right: 5px;
  bottom: 7px;
`

interface CoursePlannedProps {
  full_code: Course["full_code"],
  removeCourse: (course: Course["full_code"]) => void,
  semester: Course["semester"]
}

const CoursePlanned = ({full_code, semester, removeCourse} : CoursePlannedProps) => {
  const [mouseOver, setMouseOver] = useState(false);

  const [{ isDragging }, drag] = useDrag(() => ({
    type: ItemTypes.COURSE,
    item: {full_code: full_code, semester },
    collect: (monitor) => ({
      isDragging: !!monitor.isDragging()
    })
  }), [full_code, semester])

  return (   
    <PlannedCourseContainer
    $isDragging={isDragging}
    ref={drag} 
    onMouseOver={() => setMouseOver(true)} 
    onMouseLeave={() => setMouseOver(false)}
    >
      <ReviewPanelTrigger full_code={full_code}>
        <div>
          {full_code}
        </div>
        <RemoveCourseButton hidden={!mouseOver} onClick={() => removeCourse(full_code)}>
          <GrayIcon><i className="fas fa-times"></i></GrayIcon>
        </RemoveCourseButton>
      </ReviewPanelTrigger>
    </PlannedCourseContainer>
  )
}


export default CoursePlanned;