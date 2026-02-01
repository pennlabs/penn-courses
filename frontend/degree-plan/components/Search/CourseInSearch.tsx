import React, { useState } from "react";
import styled from "styled-components";
import { useDrag } from "react-dnd";
import { ItemTypes } from "@/components/Dock/dnd/constants";
import Badge from "./Badge";
import { Course as CourseType, DnDCourse, Rule } from "@/types";
import Skeleton from "react-loading-skeleton";
import "react-loading-skeleton/dist/skeleton.css";
import { ReviewPanelTrigger } from "@/components/Infobox/ReviewPanel";

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

const CourseContainer = styled.div<{ $isRecCourse?: boolean }>`
    padding-left: 0em;
    padding-top: 1em;
    padding-bottom: 1em;
    align-items: center;
    display: flex;
    flex-direction: row;
    cursor: default;
`;

const CourseInfoContainer = styled.div<{ $isRecCourse?: boolean }>`
    display: flex;
    flex-direction: row;
    width: ${({ $isRecCourse }) => ($isRecCourse ? "95%" : "100%")};
`;

const CourseIdentityContainer = styled.div<{ $isRecCourse?: boolean }>`
    overflow: hidden;
    width: ${({ $isRecCourse }) => ($isRecCourse ? "58.5%" : "60%")};
`;

// Bulma: title is-6
export const CourseID = styled.h3`
    font-size: 1rem;
    color: #363636;
    font-weight: 600;
    line-height: 1.125;
    word-break: break-word;
    margin-bottom: 0;
`;

export const CourseIDContainer = styled.div`
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

const AddButton = styled.div`
    margin: 0.1rem 0.3rem 0.1rem;
    color: var(--green-color);
    cursor: pointer;
`;

export const SkeletonCourse = () => (
    // eslint-disable-next-line
    <RowSelectors>
        <CourseContainer>
            <CourseInfoContainer role="button">
                <CourseIdentityContainer>
                    <CourseIDContainer>
                        <CourseID>
                            <Skeleton width="5rem" />
                        </CourseID>
                    </CourseIDContainer>
                    <CourseTitle></CourseTitle>
                </CourseIdentityContainer>
                <CourseQualityContainer>
                    <Badge />
                </CourseQualityContainer>
                <CourseDifficultyContainer>
                    <Badge />
                </CourseDifficultyContainer>
            </CourseInfoContainer>
        </CourseContainer>
    </RowSelectors>
);

interface CourseProps {
    course: CourseType;
    ruleId: Rule["id"] | null;
    onClick: () => void;
    isRecCourse?: boolean;
    onClickDelete?: () => void;
    isStar?: boolean;
}

export default function Course({
    course,
    ruleId,
    onClick,
    isRecCourse,
    onClickDelete,
    isStar,
}: CourseProps) {
    /** React dnd */

    const [{ isDragging }, drag] = useDrag<
        DnDCourse,
        never,
        { isDragging: boolean }
    >(
        () => ({
            type: ItemTypes.COURSE_IN_SEARCH,
            item: {
                full_code: course.id,
                rule_id: ruleId == null ? -1 : ruleId,
            },
            collect: (monitor) => ({
                isDragging: !!monitor.isDragging(),
            }),
        }),
        [course],
    );

    const [isMouseOver, setIsMouseOver] = useState(false);

    return (
        <RowSelectors>
            <ReviewPanelTrigger full_code={course.id} triggerType="click">
                <CourseContainer
                    onMouseEnter={() => setIsMouseOver(true)}
                    onMouseLeave={() => setIsMouseOver(false)}
                >
                    <CourseInfoContainer>
                        <CourseIdentityContainer
                            ref={drag}
                            className="draggable"
                        >
                            <CourseIDContainer>
                                <CourseID>
                                    {course.id.replace(/-/g, " ")}
                                </CourseID>
                                {/* {isMouseOver && 
                                <AddButton onClick={onClick}>
                                    <i className="fas fa-md fa-plus-circle" aria-hidden="true"></i>
                                </AddButton>} */}
                            </CourseIDContainer>
                            <CourseTitle>{course.title}</CourseTitle>
                        </CourseIdentityContainer>

                        <CourseQualityContainer>
                            <Badge value={course.course_quality} />
                        </CourseQualityContainer>
                        <CourseDifficultyContainer>
                            <Badge value={course.difficulty} />
                        </CourseDifficultyContainer>
                    </CourseInfoContainer>
                </CourseContainer>
            </ReviewPanelTrigger>
        </RowSelectors>
    );
}
