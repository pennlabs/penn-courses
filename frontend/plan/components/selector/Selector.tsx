import React, { FunctionComponent } from "react";
import styled from "styled-components";
import { connect } from "react-redux";
import { ThunkDispatch } from "redux-thunk";

import CourseList from "./CourseList";
import CourseInfo from "./CourseInfo";

import {
    fetchCourseDetails,
    updateCourseInfo,
    addSchedItem,
    removeSchedItem,
    updateScrollPos,
} from "../../actions";
import { Course, Section, SortMode } from "../../types";

interface SelectorProps {
    courses: Course[];
    course: Course;
    getCourse: (courseId: string) => void;
    clearCourse: () => void;
    addToSchedule: (section: string) => void;
    removeFromSchedule: (id: string) => void;
    isLoadingCourseInfo: boolean;
    isSearchingCourseInfo: boolean;
    view: number;
    scrollPos: number;
    setScrollPos: (scrollPos: number) => void;
    sortMode: SortMode;
}

const Loading = styled.div`
    height: 100%;
    width: 100%;
    border: none;
    font-size: 3rem;
`;

const EmptyResultsContainer = styled.div`
    font-size: 0.8rem;
    text-align: center;
    margin-top: 5vh;
    max-width: 45vh;
`;

const Selector: FunctionComponent<SelectorProps> = ({
    courses,
    course,
    getCourse,
    clearCourse,
    addToSchedule,
    removeFromSchedule,
    isLoadingCourseInfo,
    isSearchingCourseInfo,
    sortMode,
    view,
    scrollPos,
    setScrollPos,
}: SelectorProps) => {
    const isExpanded = view === 1;
    const isLoading =
        isSearchingCourseInfo || (isLoadingCourseInfo && !isExpanded);

    const loadingIndicator = <Loading className="button is-loading" />;

    let element = (
        <EmptyResultsContainer>
            <img src="/icons/empty-state-search.svg" alt="" />
            <h3
                style={{
                    fontWeight: "bold",
                    marginBottom: "0.5rem",
                }}
            >
                No result found
            </h3>
            Search for courses, departments, or instructors above. Looking for
            something specific? Try using the filters!
        </EmptyResultsContainer>
    );

    const courseList = (
        <CourseList
            sortMode={sortMode}
            courses={courses}
            getCourse={getCourse}
            scrollPos={scrollPos}
            setScrollPos={setScrollPos}
        />
    );

    if (courses.length > 0 && !course) {
        element = isExpanded ? (
            <div className="columns">
                <div
                    className="column is-one-third"
                    style={{
                        height: "calc(100vh - 12.5em)",
                        borderRight: "1px solid #dddddd",
                    }}
                >
                    {courseList}
                </div>
            </div>
        ) : (
            courseList
        );
    }

    if (course) {
        element = isExpanded ? (
            <div className="columns">
                <div
                    className="column is-one-third"
                    style={{
                        height: "calc(100vh - 12.5em)",
                        borderRight: "1px solid #dddddd",
                    }}
                >
                    {courseList}
                </div>
                <div
                    className="column is-two-thirds"
                    style={{ height: "calc(100vh - 12.5em)" }}
                >
                    {isLoadingCourseInfo ? (
                        loadingIndicator
                    ) : (
                        <CourseInfo
                            getCourse={getCourse}
                            course={course}
                            view={view}
                        />
                    )}
                </div>
            </div>
        ) : (
            <CourseInfo
                getCourse={getCourse}
                course={course}
                back={clearCourse}
                view={view}
            />
        );
    }
    return <>{isLoading ? loadingIndicator : element}</>;
};

const mapStateToProps = ({
    sections: {
        scrollPos,
        sortMode,
        searchResults,
        course,
        courseInfoLoading: isLoadingCourseInfo,
        searchInfoLoading: isSearchingCourseInfo,
    },
}: any) => ({
    courses: searchResults.filter(({ num_sections: num }: Course) => num > 0),
    course,
    scrollPos,
    sortMode,
    isLoadingCourseInfo,
    isSearchingCourseInfo,
});

const mapDispatchToProps = (dispatch: ThunkDispatch<any, any, any>) => ({
    getCourse: (courseId: string) => dispatch(fetchCourseDetails(courseId)),
    clearCourse: () => dispatch(updateCourseInfo(null)),
    addToSchedule: (section: Section) => dispatch(addSchedItem(section)),
    removeFromSchedule: (id: string) => dispatch(removeSchedItem(id)),
    setScrollPos: (scrollPos: number) => dispatch(updateScrollPos(scrollPos)),
});

// no clue why the higher-order connect function isn't working with typescript -- Selector is definitely a component.
// @ts-ignore
export default connect(mapStateToProps, mapDispatchToProps)(Selector);
