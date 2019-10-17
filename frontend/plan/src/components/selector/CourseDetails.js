import React from "react";
import PropTypes from "prop-types";
import TagList from "./TagList";


export default function CourseDetails({ course, getCourse }) {
    const requirements = course.requirements || [];
    const crosslistings = course.crosslistings || [];
    return (
        <ul style={{ fontSize: ".8em" }}>
            <li>
                <span className="icon is-small">
                    <i className="far fa-check-circle" />
                </span>
                &nbsp; Fulfills: &nbsp;
                { <TagList elements={requirements.map(req => `${req.school}: ${req.name}`)} limit={1} /> }
            </li>
            {course.crosslistings.length !== 0 ? (
                <li>
                    <span className="icon is-small">
                        <i className="fas fa-random" />
                    </span>
                    &nbsp; Crosslisted as: &nbsp;
                    { <TagList elements={crosslistings.map(e => e.replace(/-/g, " "))} limit={2} onClick={getCourse} /> }
                </li>
            ) : null
            }
        </ul>
    );
}

CourseDetails.propTypes = {
    course: PropTypes.objectOf(PropTypes.any).isRequired,
};
