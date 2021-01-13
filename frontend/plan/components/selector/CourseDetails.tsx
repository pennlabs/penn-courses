import React from "react";
import styled from "styled-components";
import TagList from "./TagList";
import Badge from "../Badge";
import ShowMore from "../ShowMore";
import { Course, School } from "../../types";

const schoolToLetter = (school: School) => {
    switch (school) {
        case School.COLLEGE:
            return "C";
        case School.NURSING:
            return "N";
        case School.SEAS:
            return "E";
        case School.WHARTON:
            return "W";
        default:
            return "";
    }
};
const getReqCode = (school: School, name: string) =>
    `${schoolToLetter(school)}: ${name}`;

const annotatePrerequisites = (
    text: string | null,
    onClick: (course: string) => void
) => {
    if (typeof text !== "string" || !/\S/.test(text)) return null;
    const courseRegex = /((^|\W)[A-Z]{3}[A-Z]?(-|\s)[0-9]{3}($|(?=\W)))/;
    const tokens = text.split(courseRegex).filter((elem) => /\S/.test(elem));
    tokens.unshift("Prerequisites: ");
    return tokens.map((token, i) =>
        courseRegex.test(token) ? (
            <a
                key={i}
                role="button"
                onClick={(e) => {
                    e.preventDefault();
                    onClick && onClick(token.trim().replace(/\s/g, "-"));
                }}
            >
                {token}
            </a>
        ) : (
            token
        )
    );
};

interface CourseDetailsProps {
    course: Course;
    getCourse: (course: string) => void;
    view: number;
}

const CourseDetailsContainer = styled.ul`
    font-size: 0.8em;
    margin-top: 1em;
`;

const PCRButtonLink = styled.a`
    font-weight: 700;
    font-size: 0.8 em;
    color: #8f8f8f;
    text-align: center;
    border: 2px solid #eeeeee;
    border-radius: 4px;

    &:hover {
        border: 2px solid #cbcbcb;
        border-radius: 4px;
    }
`;

const ShowMoreContainer = styled.li`
    margin-top: 2em;
    margin-bottom: 2em !important;
`;

export default function CourseDetails({
    course: {
        requirements = [],
        crosslistings = [],
        description,
        prerequisites: prereqText,
        course_quality: courseQuality,
        difficulty,
        id,
    },
    getCourse,
    view,
}: CourseDetailsProps) {
    const prerequisites = annotatePrerequisites(prereqText, getCourse);
    const isExpandedView = view === 1;
    return (
        <CourseDetailsContainer>
            <li>
                <span className="icon is-small">
                    <i className="far fa-chart-bar" />
                </span>
                &nbsp; Quality: &nbsp;
                <Badge value={courseQuality} />
                &nbsp; Difficulty: &nbsp;
                <Badge value={difficulty} />
            </li>
            {requirements.length > 0 ? (
                <li>
                    <span className="icon is-small">
                        <i className="far fa-check-circle" />
                    </span>
                    &nbsp; Fulfills: &nbsp;
                    <TagList
                        elements={requirements.map(({ school, name }) =>
                            getReqCode(school, name)
                        )}
                        limit={1}
                    />
                </li>
            ) : null}
            {crosslistings.length > 0 ? (
                <li>
                    <span className="icon is-small">
                        <i className="fas fa-random" />
                    </span>
                    &nbsp; Crosslisted as: &nbsp;
                    <TagList
                        elements={crosslistings.map((e) =>
                            e.replace(/-/g, " ")
                        )}
                        limit={2}
                        onClick={getCourse}
                    />
                </li>
            ) : null}
            <PCRButtonLink
                target="_blank"
                rel="noopener noreferrer"
                className="button is-small"
                type="button"
                href={`https://penncoursereview.com/course/${id}`}
            >
                View on Penn Course Review
            </PCRButtonLink>
            {prerequisites && (
                <ShowMoreContainer>
                    <ShowMore
                        disabled={isExpandedView}
                        lines={2}
                        more="See more"
                        less="See less"
                    >
                        {prerequisites}
                    </ShowMore>
                </ShowMoreContainer>
            )}
            {
                <ShowMoreContainer>
                    <ShowMore
                        disabled={isExpandedView}
                        lines={2}
                        more="See more"
                        less="See less"
                    >
                        {description}
                    </ShowMore>
                </ShowMoreContainer>
            }
        </CourseDetailsContainer>
    );
}
