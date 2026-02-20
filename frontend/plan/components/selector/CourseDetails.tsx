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
    const courseRegex = /((^|\W)[A-Z]{3}[A-Z]?(-|\s)[0-9]{3,4}($|(?=\W)))/;
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
    color: #8f8f8f !important;
    text-align: center;
    border: 2px solid #eeeeee;
    border-radius: 30px;

    background-color: #fff;
    cursor: pointer;
    justify-content: center;
    padding: calc(0.375em - 1px) 0.75em;
    white-space: nowrap;

    &:hover {
        border: 2px solid #cbcbcb;
    }
`;

const ShowMoreContainer = styled.li`
    margin-top: 2em;
    margin-bottom: 2em !important;
`;

// Bulma: icon is-small
const Icon = styled.span`
    pointer-events: none;
    height: 1rem;
    width: 1rem;
    align-items: center;
    display: inline-flex;
    justify-content: center;
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
                <Icon>
                    <i className="far fa-chart-bar" />
                </Icon>
                &nbsp; Quality: &nbsp;
                <Badge value={courseQuality} />
                &nbsp; Difficulty: &nbsp;
                <Badge value={difficulty} />
            </li>
            {requirements.length > 0 ? (
                <li>
                    <Icon>
                        <i className="far fa-check-circle" />
                    </Icon>
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
                    <Icon>
                        <i className="fas fa-random" />
                    </Icon>
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
        </CourseDetailsContainer>
    );
}
