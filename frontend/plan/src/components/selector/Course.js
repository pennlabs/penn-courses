import React from "react";
import PropTypes from "prop-types";

import Badge from "../Badge";

export default function Course({ course, onClick }) {
    return (
        // eslint-disable-next-line
        <li className="selector-row">
            <div
                onClick={onClick}
                role="button"
                style={{
                    paddingLeft: "2.85em",
                    paddingTop: "1em",
                    paddingBottom: "1em",
                    alignItems: "center",
                    display: "flex",
                    flexDirection: "row",
                }}
            >
                <div style={{ overflow: "hidden", width: "60%" }}>
                    <h3 className="title is-6" style={{ marginBottom: 0 }}>
                        {course.id.replace(/-/g, " ")}
                    </h3>
                    <span style={{ fontWeight: "normal", color: "#888888" }}>
                        {course.title}
                    </span>
                </div>
                <div style={{ marginRight: "2px", width: "20%" }}>
                    <Badge
                        baseColor={[45, 160, 240]}
                        value={course.course_quality}
                    />
                </div>
                <div style={{ width: "20%" }}>
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
