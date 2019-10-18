import React from "react";
import PropTypes from "prop-types";
import TagList from "./TagList";
import Badge from "../Badge";


export default function CourseDetails({ course }) {
    const requirements = course.requirements || [];
    const crosslistings = course.crosslistings || [];
    return (
        <ul style={{ fontSize: ".8em" }}>
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
                        {<TagList elements={requirements.map(({ school, name }) => `${school.charAt(0)}: ${name}`)} limit={1} />}
                    </li>
                ) : null
            }
            {crosslistings.length > 0 ? (
                <li>
                    <span className="icon is-small">
                        <i className="fas fa-random" />
                    </span>
                    &nbsp; Crosslisted as: &nbsp;
                    {<TagList elements={crosslistings} limit={2} />}
                </li>
            ) : null
            }
        </ul>
    );
}

CourseDetails.propTypes = {
    course: PropTypes.objectOf(PropTypes.any).isRequired,
};
