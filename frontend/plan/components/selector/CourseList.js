import React, { useEffect, useRef } from "react";
import PropTypes from "prop-types";
import Course from "./Course";

const goodEasy = ({ difficulty, course_quality: courseQuality }) =>
    !difficulty || !courseQuality
        ? 0
        : Math.pow(courseQuality + 0.5, 1.5) / (difficulty + 1);

/**
 * Sorts courses by the given sort mode
 * @param courses A list of course objects
 * @param sortMode The sort mode as a string
 * @returns {*} A sorted list of courses
 */
const courseSort = (courses, sortMode) => {
    const sorted = [...courses];
    sorted.sort((courseA, courseB) => {
        switch (sortMode && sortMode.toLowerCase()) {
            case "quality":
                return !courseB.course_quality
                    ? -1
                    : courseB.course_quality - courseA.course_quality;
            case "difficulty":
                return !courseB.difficulty
                    ? -1
                    : courseA.difficulty - courseB.difficulty;
            case "good & easy":
                return goodEasy(courseB) - goodEasy(courseA);
            default:
                return courseA.id.localeCompare(courseB.id);
        }
    });
    return sorted;
};

const CourseList = ({
    courses,
    getCourse,
    sortMode,
    scrollPos,
    setScrollPos,
}) => {
    const listRef = useRef(null);
    useEffect(() => {
        // Set sections list scroll position to stored position
        const { current: ref } = listRef;
        ref.scrollTop = scrollPos;
        // Return cleanup function that stores current sections scroll position
        return () => setScrollPos(ref.scrollTop);
    }, [scrollPos, setScrollPos]);

    return (
        <div className="scroll-container">
            <div
                style={{
                    display: "flex",
                    flexDirection: "row",
                    paddingBottom: "1em",
                    paddingLeft: "2em",
                }}
            >
                <div
                    className="header"
                    style={{
                        overflow: "hidden",
                        width: "60%",
                    }}
                >
                    COURSE
                </div>
                <div className="header" style={{ width: "20%" }}>
                    QUAL
                </div>
                <div className="header" style={{ width: "20%" }}>
                    DIFF
                </div>
            </div>
            <ul className="scrollable course-list" ref={listRef}>
                {courseSort(courses, sortMode).map((course) => (
                    <Course
                        key={course.id}
                        course={course}
                        onClick={() => getCourse(course.id)}
                    />
                ))}
            </ul>
        </div>
    );
};

export default CourseList;

CourseList.propTypes = {
    courses: PropTypes.arrayOf(PropTypes.object).isRequired,
    getCourse: PropTypes.func.isRequired,
    sortMode: PropTypes.string.isRequired,
    scrollPos: PropTypes.number,
    setScrollPos: PropTypes.func,
};
