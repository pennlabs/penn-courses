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
                            <i className="fas fa-arrow-left" />
                        </span>
                        &nbsp; Back
                    </BackButton>
                )}
            </BackContainer>
            <DetailsContainer>
                <h3 className="title is-4">{id.replace(/-/g, " ")}</h3>
                <h5 className="subtitle is-6">{title}</h5>
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
