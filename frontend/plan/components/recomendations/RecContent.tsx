import React from "react";
import styled from "styled-components";
import Course from "../selector/Course";
import { Course as CourseType } from "../../types";
import { Loading } from "../bulma_derived_components";

const RecWrapper = styled.div`
    overflow-y: scroll;
    height: 100%;
    display: flex;
    flex-direction: column;

    &::-webkit-scrollbar {
        display: none;
    }
`;

const RecContentContainer = styled.div<{
    $collapse: boolean;
}>`
    height: 100%;
    max-height: 8.125rem;
    min-height: 8.125rem;
    margin-top: ${({ $collapse: collapse }) => (collapse ? "-100%" : "0px")};
    transition: all 1s;
    overflow-y: scroll;
    overflow-x: hidden;

    &::-webkit-scrollbar {
        display: none;
    }

    // safari only - to fix unequal max height on chrome vs safari
    @media not all and (min-resolution: 0.001dpcm) {
        @media {
            max-height: 14.375rem;
            min-height: 14.375rem;
        }
    }
`;

const RecLoading = styled(Loading)`
    margin-top: 50px;
`;

const CoursesContainer = styled.ul`
    height: 100%;
    overflow-y: scroll;
    overflow-x: hidden;
    font-size: 0.7em;

    &::-webkit-scrollbar {
        width: 0 !important;
    }
`;

const EmptyContainer = styled.div`
    font-size: 0.8rem;
    margin: 0 0.9375rem;
    padding: 0.625rem;
    text-align: center;
    border-radius: 8px;
    background-color: rgb(241, 241, 241);
`;

const getStatusHeadingText = (status: number) => {
    switch (status) {
        case 1:
            return "No recommended course";
        case 2:
            return "Error";
        case 3:
            return "Log in";
        default:
            return "No recommended course";
    }
};

const getStatusDescText = (status: number) => {
    switch (status) {
        case 1:
            return "Sorry, we couldn't find any course to recommend you.";
        case 2:
            return "Sorry, there was an error loading the recommendations.";
        case 3:
            return "Please log in to view your recommendations.";
        default:
            return "Sorry, we couldn't find any course to recommend you.";
    }
};

interface RecContentProps {
    show: boolean;
    recCourses: CourseType[];
    getCourse: (id: string) => void;
    fetchStatus: number;
}

const RecContent = ({
    show,
    recCourses,
    getCourse,
    fetchStatus,
}: RecContentProps) => {
    return (
        <RecWrapper>
            <RecContentContainer $collapse={!show}>
                {/* Only create list if there is recommended course(s) */}
                {fetchStatus == 0 ? (
                    <RecLoading />
                ) : recCourses && recCourses.length > 0 ? (
                    <CoursesContainer>
                        {recCourses.map((recCourse) => (
                            <Course
                                key={recCourse.id}
                                course={recCourse}
                                onClick={() => getCourse(recCourse.id)}
                            />
                        ))}
                    </CoursesContainer>
                ) : (
                    // Show if no there is no recommended courses
                    <EmptyContainer>
                        <h3
                            style={{
                                fontWeight: "bold",
                                marginBottom: "0.5rem",
                            }}
                        >
                            {getStatusHeadingText(fetchStatus)}
                        </h3>
                        {getStatusDescText(fetchStatus)}
                    </EmptyContainer>
                )}
            </RecContentContainer>
        </RecWrapper>
    );
};

export default RecContent;
