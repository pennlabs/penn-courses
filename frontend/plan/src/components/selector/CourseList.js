import React from "react";
import PropTypes from "prop-types";
import Course from "./Course";

/**
 * Sorts courses by the given sort mode
 * @param courses A list of course objects
 * @param sortMode The sort mode as a string
 * @returns {*} A sorted list of courses
 */
const courseSort = (courses, sortMode) => {
    const sorted = [...courses];
    sorted.sort((courseA, courseB) => {
        console.log(courseA, courseB);
        switch (sortMode) {
            case "Quality":
                return courseB.course_quality - courseA.course_quality;
            case "Difficulty":
                return courseA.difficulty - courseB.difficulty;
            default:
                return courseA.id.localeCompare(courseB.id);
        }
    });
    return sorted;
};

export default function CourseList({ courses, getCourse, sortMode }) {
    return (
        <div className="scroll-container">
            <div className="columns" style={{ paddingLeft: "2em" }}>
                <div className="column header is-three-fifths" style={{ overflow: "hidden" }}>
                    COURSE
                </div>
                <div className="column header">QUAL</div>
                <div className="column header">DIFF</div>
            </div>
            <ul className="scrollable course-list">
                {
                    courseSort(courses, sortMode)
                        .map(course => (
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
    sortMode: PropTypes.string,
};
