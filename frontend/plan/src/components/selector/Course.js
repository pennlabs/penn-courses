import React from "react";
import PropTypes from "prop-types";

import Badge from "../Badge";

export default function Course({ course, onClick }) {
    return (
        // eslint-disable-next-line
        <li className="selector-row">
            <div onClick={onClick} className="columns" role="button" style={{ paddingLeft: "2.85em" }}>
                <div className="column header is-three-fifths" style={{ overflow: "hidden" }}>
                    <h3 className="title is-6" style={{ marginBottom: 0 }}>{course.id.replace(/-/g, " ")}</h3>
                    <span style={{ fontWeight: "normal" }}>
                        {course.title}
                    </span>
                </div>
                <div
                    className="column header"
                    style={{ marginRight: "2px" }}
                >
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
            </div>
        </li>
    );
}

Course.propTypes = {
    // eslint-disable-next-line
    course: PropTypes.object.isRequired,
    onClick: PropTypes.func,
};
