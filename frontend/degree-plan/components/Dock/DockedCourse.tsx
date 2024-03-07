

import React from "react";
import { GrayIcon } from '@/components/common/bulma_derived_components';
import { useDrag } from 'react-dnd';
import styled from '@emotion/styled';
import { ItemTypes } from '../dnd/constants';
import { Draggable } from "../common/DnD";
import { ReviewPanelTrigger } from "../Infobox/ReviewPanel";

const BaseCourseContainer = styled.span<{ $isDragging?: boolean, $isDepressed: boolean, $isDisabled: boolean }>`
  display: flex;
  justify-content: center;
  align-items: center;
  min-width: 70px;
  background: #F2F3F4;
  margin: 0px 6px;
  border-radius: 0px;
  padding: 0rem 2rem;
  text-wrap: nowrap;
  color: ${props => props.$isDisabled ? "rgba(0, 0, 0, .6)" : "#000"};
  cursor: ${props => props.$isDisabled || props.$isDepressed ? "not-allowed" : "grab"};
  opacity: ${props => props.$isDragging ? 0.5 : 1};
  background-color: ${props => props.$isDragging ? "#4B9AE7" : props.$isDepressed ? "var(--primary-color)" : "#F2F3F4"};
`;

const DockedCourseContainer = styled(BaseCourseContainer)`
    height: 100%;
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


const DockedCourse = ({removeDockedCourse, full_code}: any) => {
    const [mouseOver, setMouseOver] = React.useState(false);

    /** React dnd */
    const [{ isDragging, color }, drag, dragPreview] = useDrag(() => ({
        type: ItemTypes.COURSE,
        item: {full_code: full_code, semester:-1},
        collect: (monitor) => ({
            isDragging: !!monitor.isDragging(),
            color: monitor.isDragging() ? 'none' : 'none'
        })
    }))

    return (
        <DockedCourseContainer
        $isDragging={isDragging}
        $isDepressed={false}
        $isDisabled={false}
        ref={drag} 
        >
            <Draggable isDragging={isDragging} >
                <ReviewPanelTrigger full_code={full_code}>
                  <BaseCourseContainer $isDisabled={false} $isDragging={isDragging} $isDepressed={false}>
                    {full_code.replace(/-/g, " ")}
                  </BaseCourseContainer>
                </ReviewPanelTrigger>
            </Draggable>
            <GrayIcon className="close-button" onClick={() => removeDockedCourse(full_code)}>
                <i className="fas fa-times"></i>
            </GrayIcon>
        </DockedCourseContainer>
    )
}

export default DockedCourse;