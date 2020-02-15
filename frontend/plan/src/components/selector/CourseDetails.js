import React from "react";
import PropTypes from "prop-types";
import TagList from "./TagList";
import Badge from "../Badge";
import ShowMore from "../ShowMore";

const getReqCode = (school, name) => `${{ SAS: "C", SEAS: "E", WH: "W" }[school]}: ${name}`;
const annotatePrerequisites = (text, onClick) => {
    if (typeof text !== "string" || !/\S/.test(text)) return null;
    const courseRegex = /((^|\W)[A-Z]{3}[A-Z]?(-|\s)[0-9]{3}($|(?=\W)))/;
    const tokens = text.split(courseRegex).filter(elem => /\S/.test(elem));
    tokens.unshift("Prerequisites: ");
    return tokens.map(token => (courseRegex.test(token)
        ? (
            <a
                role="button"
                onClick={(e) => {
                    e.preventDefault();
                    onClick && onClick(token.trim().replace(/\s/g, "-"));
                }}
            >
                {token}
            </a>
        )
        : token));
};


export default function CourseDetails({
    course: {
        requirements = [],
        crosslistings = [],
        description,
        prerequisites: prereqText,
        course_quality: courseQuality,
        difficulty,
        id,
    }, getCourse, view,
}) {
    const prerequisites = annotatePrerequisites(prereqText, getCourse);
    return (
        <ul style={{ fontSize: ".8em", marginTop: "1em" }}>
            <li>
                <span className="icon is-small">
                    <i className="far fa-chart-bar" />
                </span>
                &nbsp; Quality: &nbsp;
                <Badge
                    baseColor={[43, 236, 56]}
                    value={courseQuality}
                />
                &nbsp; Difficulty: &nbsp;
                <Badge
                    baseColor={[43, 236, 56]}
                    value={difficulty}
                />
            </li>
            {requirements.length > 0
                ? (
                    <li>
                        <span className="icon is-small">
                            <i className="far fa-check-circle" />
                        </span>
                        &nbsp; Fulfills: &nbsp;
                        <TagList
                            elements={requirements.map(
                                ({ school, name }) => getReqCode(school, name)
                            )}
                            limit={1}
                        />
                    </li>
                ) : null
            }
            {crosslistings.length > 0 ? (
                <li>
                    <span className="icon is-small">
                        <i className="fas fa-random" />
                    </span>
                    &nbsp; Crosslisted as: &nbsp;
                    <TagList elements={crosslistings.map(e => e.replace(/-/g, " "))} limit={2} onClick={getCourse} />
                </li>
            ) : null
            }
            <a
                target="_blank"
                className="button is-small pcr-svg"
                type="button"
                href={`https://penncoursereview.com/course/${(id)}`}
                style={{
                    fontWeight: "700",
                    fontSize: "0.8 em",
                    color: "#8F8F8F",
                    textAlign: "center",
                }}
            >
                View on Penn Course Review
            </a>
            {prerequisites && (
                <li style={{
                    marginTop: "2em",
                    marginBottom: "2em",
                }}
                >
                    <ShowMore
                        disabled={view === 1}
                        lines={2}
                        more="See more"
                        less="See less"
                    >
                        {prerequisites}
                    </ShowMore>
                </li>
            )}
            {description && (
                <li style={{
                    marginTop: "2em",
                    marginBottom: "2em",
                }}
                >
                    <ShowMore
                        disabled={view === 1}
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

CourseDetails.propTypes = {
    course: PropTypes.objectOf(PropTypes.any).isRequired,
    getCourse: PropTypes.func,
    view: PropTypes.number,
};
