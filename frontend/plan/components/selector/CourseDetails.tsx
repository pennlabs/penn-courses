import React from "react";
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
    return tokens.map((token) =>
        courseRegex.test(token) ? (
            <a
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
        <ul style={{ fontSize: ".8em", marginTop: "1em" }}>
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
            <a
                target="_blank"
                rel="noopener noreferrer"
                className="button is-small pcr-svg"
                type="button"
                href={`https://penncoursereview.com/course/${id}`}
                style={{
                    fontWeight: 700,
                    fontSize: "0.8 em",
                    color: "#8F8F8F",
                    textAlign: "center",
                }}
            >
                View on Penn Course Review
            </a>
            {prerequisites && (
                <li
                    style={{
                        marginTop: "2em",
                        marginBottom: "2em",
                    }}
                >
                    <ShowMore
                        disabled={isExpandedView}
                        lines={2}
                        more="See more"
                        less="See less"
                    >
                        {prerequisites}
                    </ShowMore>
                </li>
            )}
            {description && (
                <li
                    style={{
                        marginTop: "2em",
                        marginBottom: "2em",
                    }}
                >
                    <ShowMore
                        disabled={isExpandedView}
                        lines={2}
                        more="See more"
                        less="See less"
                    >
                        {description}
                    </ShowMore>
                </li>
            )}
        </ul>
    );
}
