import React, { useState } from "react";
import styled from "styled-components";
import { useDrag } from "react-dnd";
import { ItemTypes } from "../dnd/constants";

import Badge from "./Badge";
// import { Course as CourseType } from "../../types";
// import { Icon } from "../bulma_derived_components";

const RowSelectors = styled.li`
    transition: ease background;
    &:hover {
        background-color: rgb(240, 240, 240);
        cursor: pointer;
    }
    &:active {
        background-color: rgb(230, 230, 230);
        cursor: pointer;
    }
    padding-left: 1em;
`;

const CourseContainer = styled.div<{ $isRecCourse: boolean }>`
    padding-left: 0em;
    padding-top: 1em;
    padding-bottom: 1em;
    align-items: center;
    display: flex;
    flex-direction: row;
`;


const CourseInfoContainer = styled.div<{ $isRecCourse: boolean }>`
    display: flex;
    flex-direction: row;
    width: ${({ $isRecCourse: isRecCourse }) => (isRecCourse ? "95%" : "100%")};
`;

const CourseIdentityContainer = styled.div<{ $isRecCourse: boolean }>`
    overflow: hidden;
    width: ${({ $isRecCourse: isRecCourse }) => (isRecCourse ? "58.5%" : "60%")};
`;

// Bulma: title is-6
const CourseID = styled.h3`
    font-size: 1rem;
    color: #363636;
    font-weight: 600;
    line-height: 1.125;
    word-break: break-word;
    margin-bottom: 0;
`;

const CourseIDContainer = styled.div`
    display: flex;
    align-content: center;
    flex-direction: row;
    z-index: 20;
    overflow: none;
`;

const CourseTitle = styled.span`
    fontweight: normal;
    color: #888888;
`;

const CourseQualityContainer = styled.div`
    margin-right: 1.5px;
    width: 20%;
    padding-left: 7px;
    padding-top: 5px;
`;

const CourseDifficultyContainer = styled.div`
    width: 20%;
    padding-left: 7px;
    padding-top: 5px;
`;

const InfoPopup = styled.div<{ $show: boolean }>`
    position: absolute;
    display: ${({ $show: show }) => (show ? "flex" : "none")};
    visibility: ${({ $show: show }) => (show ? "visible" : "hidden")};
    text-align: center;
    z-index: 20;
    background-color: white;
    border-radius: 4px;
    padding: 0.5rem;
    color: #333333;
    font-size: 0.6875rem;
    width: 8.5rem;
    max-width: 25rem;
    max-height: 12.5rem;
    bottom: -0.33rem;
    overflow: hidden;
    left: 3.4375rem;
    box-shadow: 0 2px 3px rgba(10, 10, 10, 0.1), 0 0 0 1px rgba(10, 10, 10, 0.1);
`;

interface CourseProps {
    course: CourseType;
    onClick: () => void;
    isRecCourse?: boolean;
    onClickDelete?: () => void;
    isStar?: boolean;
}

export default function Course({
    course,
    onClick,
    isRecCourse,
    onClickDelete,
    isStar,
}: CourseProps) {
    /** React dnd */
    const [{ isDragging, color }, drag, dragPreview] = useDrag(() => ({
        type: ItemTypes.COURSE,
        item: {course: {...course, satisfyIds:[]}, semester:-1},
        collect: (monitor) => ({
            isDragging: !!monitor.isDragging(),
            color: monitor.isDragging() ? 'none' : 'none'
        })
    }))

    return (
        // eslint-disable-next-line
        <RowSelectors>
            <CourseContainer>
                <CourseInfoContainer
                    onClick={onClick}
                    role="button"
                >
                    <CourseIdentityContainer>
                        <CourseIDContainer>
                                <CourseID ref={drag} style={{color}}>{course.id.replace(/-/g, " ")}</CourseID>
                        </CourseIDContainer>
                        <CourseTitle>{course.title}</CourseTitle>
                    </CourseIdentityContainer>
                    
                    <CourseQualityContainer>
                        <Badge value={3.3} /> {/*course.course_quality*/}
                    </CourseQualityContainer>
                    <CourseDifficultyContainer>
                        <Badge value={2.1} /> {/*course.difficulty*/}
                    </CourseDifficultyContainer>
                </CourseInfoContainer>
            </CourseContainer>
        </RowSelectors>
    );
}