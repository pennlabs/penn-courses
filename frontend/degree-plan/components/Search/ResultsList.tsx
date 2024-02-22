import React, { useEffect, useRef } from "react";
import styled from '@emotion/styled';
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
    max-height: 78vh;
    display: flex;
    flex-direction: column;
    min-height: 0;
    overflow: auto;
`;

const HeaderContainer = styled.div`
    display: flex;
    flex-direction: row;
    padding-left: 0.7em;
    padding-top: 0.2em;
    padding-bottom: 0.3em;
`;

const Header = styled.div`
    width: ${({ width }: { width: string }) => width};
    color: #a0a0a0;
    padding-left: 0;
    font-weight: bold;
    overflow: hidden;
`;

const CoursesContainer = styled.ul`
    height: 100%;
    padding-left: 0;
    overflow-y: auto;
    overflow-x: hidden;
    font-size: 0.7em;
    list-style: none;

    &::-webkit-scrollbar {
        width: 0 !important;
    }
`;

// const CourseListContainerWrapper = ({children}) => <CourseListContainer>{children}</CourseListContainer>

const ResultsList = ({
    courses,
    sortMode,
    scrollPos,
    setScrollPos
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

    // if (!courses.length) return <div>{`No results:((`}</div>

    return (
        <CourseListContainer>
            <HeaderContainer>
                <Header width="60%">COURSE</Header>
                <Header width="20%">QUAL</Header>
                <Header width="20%">DIFF</Header>
            </HeaderContainer>
            <CoursesContainer ref={listRef}>
                {courses.map((course) => 
                <Course
                    key={course.id + course.semester}
                    course={course}
                    onClick={() => {/*getCourse(course.id)*/}}
                    isStar={false}
                    //showCourseDetail={} searchReqId={}
                />)}
            </CoursesContainer>
        </CourseListContainer>
    );
};

export default ResultsList;