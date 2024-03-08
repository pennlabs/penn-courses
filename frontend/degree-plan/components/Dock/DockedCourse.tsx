

import React from "react";
import { GrayIcon } from '@/components/common/bulma_derived_components';
import { useDrag } from 'react-dnd';
import styled from '@emotion/styled';
import { ItemTypes } from '../dnd/constants';
import { Draggable } from "../common/DnD";
import { ReviewPanelTrigger } from "../Infobox/ReviewPanel";
import { BaseCourseContainer } from "../FourYearPlan/CoursePlanned";


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
        $isUsed={false}
        $isDisabled={false}
        ref={drag} 
        >
            <Draggable isDragging={isDragging} >
                <ReviewPanelTrigger full_code={full_code}>
                  <BaseCourseContainer $isDisabled={false} $isDragging={isDragging} $isUsed={false}>
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