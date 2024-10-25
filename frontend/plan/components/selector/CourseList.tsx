import React, { useEffect, useRef } from "react";
import styled from "styled-components";
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
            case SortMode.RECOMMENDED:
                return !courseB.recommendation_score
                    ? -1
                    : courseB.recommendation_score -
                          courseA.recommendation_score;
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
    recCoursesId: string[];
}

const CourseListContainer = styled.div`
    box-sizing: border-box;
    border-radius: 0.375em;
    height: 100%;
    display: flex;
    flex-direction: column;
    min-height: 0;
`;

const HeaderContainer = styled.div`
    display: flex;
    flex-direction: row;
    padding-bottom: 1em;
    padding-left: 2em;
`;

const Header = styled.div<{ $width: string }>`
    width: ${({ $width }) => $width};
    color: #a0a0a0;
    padding-left: 0;
    font-weight: bold;
    overflow: hidden;
`;

const CoursesContainer = styled.ul`
    height: 100%;
    overflow-y: scroll;
    overflow-x: hidden;
    font-size: 0.7em;

    &::-webkit-scrollbar {
        width: 0 !important;
    }
`;

const CourseList = ({
    courses,
    getCourse,
    sortMode,
    scrollPos,
    setScrollPos,
    recCoursesId,
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
        <CourseListContainer>
            <HeaderContainer>
                <Header $width="60%">COURSE</Header>
                <Header $width="20%">QUAL</Header>
                <Header $width="20%">DIFF</Header>
            </HeaderContainer>
            <CoursesContainer ref={listRef}>
                {courseSort(courses, sortMode).map((course) => (
                    // Star feature: recCoursesId && recCoursesId.includes(course.id)
                    <Course
                        key={course.id}
                        course={course}
                        onClick={() => getCourse(course.id)}
                        isStar={false}
                    />
                ))}
            </CoursesContainer>
        </CourseListContainer>
    );
};

export default CourseList;
