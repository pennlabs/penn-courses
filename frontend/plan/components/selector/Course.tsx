import React from "react";
import styled from "styled-components";

import Badge from "../Badge";
import { Course as CourseType } from "../../types";

interface CourseProps {
    course: CourseType;
    onClick: () => void;
}

const RowSelectors = styled.li`
    transition: 250ms ease background;

    &:hover {
        background-color: rgb(240, 240, 240);
        cursor: pointer;
    }

    &:active {
        background-color: rgb(230, 230, 230);
        cursor: pointer;
    }
`;

const CourseContainer = styled.div`
    padding-left: 2.85em;
    padding-top: 1em;
    padding-bottom: 1em;
    align-items: center;
    display: flex;
    flex-direction: row;
`;

const CourseIdentityContainer = styled.div`
    overflow: hidden;
    width: 60%;
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

const CourseTitle = styled.span`
    fontweight: normal;
    color: #888888;
`;

const CourseQualityContainer = styled.div`
    margin-right: 2px;
    width: 20%;
`;

const CourseDifficultyContainer = styled.div`
    width: 20%;
`;

export default function Course({ course, onClick }: CourseProps) {
    return (
        // eslint-disable-next-line
        <RowSelectors>
            <CourseContainer onClick={onClick} role="button">
                <CourseIdentityContainer>
                    <CourseID>{course.id.replace(/-/g, " ")}</CourseID>
                    <CourseTitle>{course.title}</CourseTitle>
                </CourseIdentityContainer>
                <CourseQualityContainer>
                    <Badge value={course.course_quality} />
                </CourseQualityContainer>
                <CourseDifficultyContainer>
                    <Badge value={course.difficulty} />
                </CourseDifficultyContainer>
            </CourseContainer>
        </RowSelectors>
    );
}
