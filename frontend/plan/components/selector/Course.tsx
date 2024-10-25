import React, { useState } from "react";
import styled from "styled-components";

import Badge from "../Badge";
import { Course as CourseType } from "../../types";
import { Icon } from "../bulma_derived_components";

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

const CourseContainer = styled.div<{ $isRecCourse: boolean }>`
    padding-left: ${({ $isRecCourse: isRecCourse }) => (isRecCourse ? "1.5em" : "2.85em")};
    padding-top: 1em;
    padding-bottom: 1em;
    align-items: center;
    display: flex;
    flex-direction: row;
`;

const DeleteContainer = styled.div<{ $isRecCourse: boolean }>`
    overflow: hidden;
    width: 5%;
    display: flex;
    justify-content: center;
    align-items: center;
    margin-right: 10px;

    &:hover {
        ${Icon} {
            color: #4a4a4a !important;
        }
    }
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

const CourseQualityContainer = styled.div<{ $isRecCourse: boolean }>`
    margin-right: 2px;
    width: ${({ $isRecCourse: isRecCourse }) => (isRecCourse ? "20.75%" : "20%")};
`;

const CourseDifficultyContainer = styled.div<{ $isRecCourse: boolean }>`
    width: ${({ $isRecCourse: isRecCourse }) => (isRecCourse ? "20.75%" : "20%")};
`;

const StarIcon = styled(Icon)`
    margin-left: 5px;
    color: #ffc400 !important;
    font-size: 0.6875rem;
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
    const existIsRecCourse = isRecCourse ?? false;
    const [showInfo, setShowInfo] = useState(false);

    return (
        // eslint-disable-next-line
        <RowSelectors>
            {isStar && (
                <div
                    style={{
                        position: "relative",
                    }}
                >
                    <InfoPopup $show={showInfo}>Recommended Course</InfoPopup>
                </div>
            )}
            <CourseContainer $isRecCourse={existIsRecCourse}>
                {isRecCourse && (
                    <DeleteContainer
                        $isRecCourse={isRecCourse}
                        onClick={onClickDelete}
                        role="button"
                    >
                        <Icon>
                            <i
                                className="fa fa-times fa-1x"
                                aria-hidden="true"
                            />
                        </Icon>
                    </DeleteContainer>
                )}
                <CourseInfoContainer
                    $isRecCourse={existIsRecCourse}
                    onClick={onClick}
                    role="button"
                >
                    <CourseIdentityContainer $isRecCourse={existIsRecCourse}>
                        <CourseIDContainer>
                            <CourseID>{course.id.replace(/-/g, " ")}</CourseID>
                            {isStar && (
                                <>
                                    <span
                                        onMouseEnter={() => setShowInfo(true)}
                                        onMouseLeave={() => setShowInfo(false)}
                                        style={{
                                            lineHeight: "0.6875rem",
                                            cursor: "pointer",
                                        }}
                                    >
                                        <StarIcon>
                                            <i
                                                className="fa fa-star fa-1x"
                                                aria-hidden="true"
                                            />
                                        </StarIcon>
                                    </span>
                                </>
                            )}
                        </CourseIDContainer>

                        <CourseTitle>{course.title}</CourseTitle>
                    </CourseIdentityContainer>
                    <CourseQualityContainer $isRecCourse={existIsRecCourse}>
                        <Badge value={course.course_quality} />
                    </CourseQualityContainer>
                    <CourseDifficultyContainer $isRecCourse={existIsRecCourse}>
                        <Badge value={course.difficulty} />
                    </CourseDifficultyContainer>
                </CourseInfoContainer>
            </CourseContainer>
        </RowSelectors>
    );
}
