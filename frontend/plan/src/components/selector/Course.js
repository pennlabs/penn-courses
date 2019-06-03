import React from "react";
import PropTypes from "prop-types";

import Badge from "../Badge";

export default function Course({ course, onClick }) {
    return (
        // eslint-disable-next-line
        <li className="selector-row">
            <div onClick={onClick} className="columns" role="button">
                <div className="column header">
                    <Badge
                        baseColor={[45, 160, 240]}
                        value={course.course_quality}
                    />
                </div>
                <div className="column header">
                    <Badge
                        baseColor={[231, 76, 60]}
                        value={course.difficulty}
                    />
                </div>
                <div className="column header is-two-thirds" style={{ overflow: "hidden" }}>
                    {`${course.id} ${course.title}`}
                </div>
            </div>
        </li>
    );
}

Course.propTypes = {
    // eslint-disable-next-line
    course: PropTypes.object.isRequired,
    onClick: PropTypes.func,
};
