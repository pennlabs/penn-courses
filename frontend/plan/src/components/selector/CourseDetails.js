import React from "react";
import ShowMoreText from "react-show-more-text";
import PropTypes from "prop-types";
import TagList from "./TagList";
import Badge from "../Badge";

const getReqCode = (school, name) => `${{ SAS: "C", SEAS: "E", WH: "W" }[school]}: ${name}`;

export default function CourseDetails({ course, getCourse, view }) {
    const requirements = course.requirements || [];
    const crosslistings = course.crosslistings || [];
    const { description } = course;
    return (
        <ul style={{ fontSize: ".8em", marginTop: "1em" }}>
            <li>
                <span className="icon is-small">
                    <i className="far fa-chart-bar" />
                </span>
                &nbsp; Quality: &nbsp;
                <Badge
                    baseColor={[43, 236, 56]}
                    value={course.course_quality}
                />
                &nbsp; Difficulty: &nbsp;
                <Badge
                    baseColor={[43, 236, 56]}
                    value={course.difficulty}
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
                href={`https://penncoursereview.com/course/${(course.id)}`}
                style={{
                    fontWeight: "700",
                    fontSize: "0.8 em",
                    color: "#8F8F8F",
                    textAlign: "center",
                }}
            >
                 View on Penn Course Review
            </a>
            {description ? (
                <li style={{
                    marginTop: "2em",
                    marginBottom: "2em",
                }}
                >
                    {view !== 1
                        && (
                            <ShowMoreText
                                lines={2}
                                more="See more"
                                less="See less"
                            >
                                {description}
                            </ShowMoreText>
                        )
                    }
                    {view === 1 && description}
                </li>
            ) : null}
        </ul>
    );
}

CourseDetails.propTypes = {
    course: PropTypes.objectOf(PropTypes.any).isRequired,
    getCourse: PropTypes.func,
    view: PropTypes.number,
};
