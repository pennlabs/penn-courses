

import React from "react";
import { BaseCourseContainer, RemoveCourseButton } from '../FourYearPlan/CoursePlanned';
import { GrayIcon } from '../bulma_derived_components';
import { useDrag } from 'react-dnd';
import styled from '@emotion/styled';
import { ItemTypes } from '../dnd/constants';
import { Draggable } from "../common/DnD";

const DockedCourseContainer = styled.div`
    margin: 1px;
    position: relative;
`
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
        <Draggable isDragging={isDragging}>
            <DockedCourseContainer
                key={full_code}     
                ref={drag}
                onMouseOver={() => setMouseOver(true)} 
                onMouseLeave={() => setMouseOver(false)}>
                <BaseCourseContainer>
                    <span>{full_code.replace(/-/g, " ")}</span>
                    <RemoveCourseButton hidden={!mouseOver} onClick={() => removeDockedCourse(full_code)}>
                        <GrayIcon><i className="fas fa-times"></i></GrayIcon>
                    </RemoveCourseButton>
                </BaseCourseContainer>
            </DockedCourseContainer>
        </Draggable>
    )
}

export default DockedCourse;