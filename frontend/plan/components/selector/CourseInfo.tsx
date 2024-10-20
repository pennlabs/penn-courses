import React from "react";
import styled from "styled-components";
import CourseDetails from "./CourseDetails";
import SectionList from "./SectionList";
import { Course } from "../../types";

interface CourseInfoProps {
    course: Course;
    back?: () => void; // Only show the back button if the `back` callback is provided.
    getCourse: (id: string) => void;
    view: number;
}

const InfoContainer = styled.div`
    height: 100%;
    display: flex;
    flex-direction: column;
    min-height: 0;
`;

const BackContainer = styled.div`
    max-height: 10;
`;

const BackButton = styled.button`
    font-size: 1em;
    border-color: transparent;
`;

const DetailsContainer = styled.div`
    margin: 0.5em 0.5em 0.5em 2em;
`;

const CourseInformationContainer = styled.ul`
    height: 100%;
    overflow-y: scroll;
    overflow-x: hidden;

    &::-webkit-scrollbar {
        width: 0 !important;
    }

    li {
        margin-bottom: 0.5em;
    }
`;

// Bulma: title is-4
const CourseID = styled.h3`
    color: #363636;
    font-weight: 600;
    line-height: 1.125;
    font-size: 1.5rem;
    word-break: break-word;
    margin-bottom: 1.5rem;
`;

// Bulma: subtitle is-6
const CourseName = styled.h5`
    color: #4a4a4a;
    font-weight: 400;
    line-height: 1.25;
    font-size: 1rem;
    margin-top: -1.25rem;
`;

export default function CourseInfo({
    course,
    back,
    getCourse,
    view,
}: CourseInfoProps) {
    const { id, title, sections } = course;
    return (
        <InfoContainer>
            <BackContainer>
                {back && (
                    <BackButton
                        type="button"
                        className="button back-button grey-text"
                        onClick={back}
                    >
                        <span className="icon">
                            <i
                                className="fas fa-arrow-left"
                                style={{ color: "#c6c6c6" }}
                            />
                        </span>
                        &nbsp; Back
                    </BackButton>
                )}
            </BackContainer>
            <DetailsContainer>
                <CourseID>{id.replace(/-/g, " ")}</CourseID>
                <CourseName>{title}</CourseName>
            </DetailsContainer>
            <CourseInformationContainer>
                <DetailsContainer>
                    <CourseDetails
                        view={view}
                        course={course}
                        getCourse={getCourse}
                    />
                </DetailsContainer>
                <SectionList view={view} sections={sections} />
            </CourseInformationContainer>
        </InfoContainer>
    );
}
