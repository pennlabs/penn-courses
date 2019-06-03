import React from "react";
import PropTypes from "prop-types";
import Course from "./Course";

export default function CourseList({ courses, getCourse }) {
    return (
        <div className="scroll-container">
            <div className="columns segment">
                <div className="column header">QUAL</div>
                <div className="column header">DIFF</div>
                <div className="column header is-two-thirds" style={{ overflow: "hidden" }}>
                    TITLE
                </div>
            </div>
            <ul className="scrollable course-list">
                {
                    courses.map(course => (
                        <Course
                            key={course.id}
                            course={course}
                            onClick={() => getCourse(course.id)}
                        />
                    ))
                }
            </ul>
        </div>
    );
}

CourseList.propTypes = {
    courses: PropTypes.arrayOf(PropTypes.object).isRequired,
    getCourse: PropTypes.func.isRequired,
};
