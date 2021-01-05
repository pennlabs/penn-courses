import React, { useEffect, useRef } from "react";
import Course from "./Course";
import { Course as CourseType, SortMode } from "../../types";

const goodEasy = ({ difficulty, course_quality: courseQuality }: CourseType) =>
    !difficulty || !courseQuality
        ? 0
        : Math.pow(courseQuality + 0.5, 1.5) / (difficulty + 1);

/**
 * Sorts courses by the given sort mode
 * @param courses A list of course objects
 * @param sortMode The sort mode as a string
 * @returns {*} A sorted list of courses
 */
const courseSort = (courses: CourseType[], sortMode: SortMode) => {
    const sorted = [...courses];
    sorted.sort((courseA, courseB) => {
        switch (sortMode) {
            case SortMode.QUALITY:
                return !courseB.course_quality
                    ? -1
                    : courseB.course_quality - courseA.course_quality;
            case SortMode.DIFFICULTY:
                return !courseB.difficulty
                    ? -1
                    : courseA.difficulty - courseB.difficulty;
            case SortMode.GOOD_AND_EASY:
                return goodEasy(courseB) - goodEasy(courseA);
            case SortMode.NAME:
            default:
                return courseA.id.localeCompare(courseB.id);
        }
    });
    return sorted;
};

export interface CourseListProps {
    courses: CourseType[];
    getCourse: (id: string) => void;
    sortMode: SortMode;
    scrollPos: number;
    setScrollPos: (pos: number) => void;
}
const CourseList = ({
    courses,
    getCourse,
    sortMode,
    scrollPos,
    setScrollPos,
}: CourseListProps) => {
    const listRef = useRef<HTMLUListElement>(null);
    useEffect(() => {
        // Set sections list scroll position to stored position
        if (listRef.current) {
            listRef.current.scrollTop = scrollPos;
        }
        // Return cleanup function that stores current sections scroll position
        return () => setScrollPos(listRef.current?.scrollTop || 0);
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
                {courseSort(courses, sortMode).map(course => (
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
