import { useState } from "react";
import { useDrag } from "react-dnd";
import { ItemTypes } from "../dnd/constants";
import { GrayIcon } from '../bulma_derived_components';
import styled from '@emotion/styled';

export const PlannedCourseContainer = styled.div<{ $isDragging: boolean, $isHighlighted: boolean}>`
  display: flex;
  justify-content: center;
  align-items: center;
  width: 100%;
  min-width: 70px;
  height: 35px;
  background: #F2F3F4;
  border-radius: 8.51786px;
  position: relative;
  opacity: ${props => props.$isDragging ? 0.5 : 1};
  background-color: ${props => props.$isDragging ? "#4B9AE7" : props.$isHighlighted ? "yellow" : "#F2F3F4" };
`;

const RemoveCourseButton = styled.div<{ isDragging: boolean }>`
  position: absolute;
  right: 5px;
  bottom: 7px;
`

interface CoursePlannedProps {
  course: any,
  semesterIndex: number,
  removeCourse: (course: any) => void,
  highlightReqId: string,
  setCourseOpen: (course: any) => void,
  showCourseDetail: (course: any) => void
}

const CoursePlanned = ({course, semesterIndex, removeCourse, highlightReqId, setCourseOpen, showCourseDetail} : CoursePlannedProps) => {
  const [mouseOver, setMouseOver] = useState(false);

  const [{ isDragging }, drag] = useDrag(() => ({
    type: ItemTypes.COURSE,
    item: {course: course, semester:semesterIndex},
    collect: (monitor) => ({
      isDragging: !!monitor.isDragging()
    })
  }), [course, semesterIndex])

  return (   
    <PlannedCourseContainer
    $isDragging={isDragging}
    $isHighlighted={course.satisfyIds.includes(highlightReqId)}
    ref={drag} 
    onMouseOver={() => setMouseOver(true)} 
    onMouseLeave={() => setMouseOver(false)}
    >
      <div onClick={() => showCourseDetail(course)}>
        {course.id}
      </div>
      <RemoveCourseButton hidden={!mouseOver} onClick={() => removeCourse(course)}>
        <GrayIcon><i className="fas fa-times"></i></GrayIcon>
      </RemoveCourseButton>
    </PlannedCourseContainer>
  )
}


export default CoursePlanned;