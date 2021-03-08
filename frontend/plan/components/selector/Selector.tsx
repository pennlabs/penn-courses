import React, { FunctionComponent } from "react";

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

    const loadingIndicator = (
        <div
            className="button is-loading"
            style={{
                height: "100%",
                width: "100%",
                border: "none",
                fontSize: "3rem",
            }}
        />
    );

    let element = (
        <div
            style={{
                fontSize: "0.8em",
                textAlign: "center",
                // marginTop: "5vh",
                maxWidth: "45vh",
                display: "flex",
                flexDirection: "column",
                justifyContent: "flex-end",
                alignSelf: "center",
                alignItems: "center",
                overflow: "hidden",
            }}
        >
            <img
                src="/icons/empty-state-search.svg"
                alt=""
                style={{
                    height: "auto",
                    maxWidth: "80%",
                    maxHeight: "18.75rem",
                }}
            />
            <h3
                style={{
                    fontWeight: "bold",
                    marginBottom: "0.5rem",
                }}
            >
                No results found
            </h3>
            Search for courses, departments, or instructors above. Looking for
            something specific? Try using the filters!
        </div>
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
