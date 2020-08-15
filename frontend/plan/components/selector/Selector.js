import React from "react";
import PropTypes from "prop-types";

import { connect } from "react-redux";

import CourseList from "./CourseList";
import CourseInfo from "./CourseInfo";

import {
    fetchCourseDetails,
    updateCourseInfo,
    addSchedItem,
    removeSchedItem,
    updateScrollPos,
} from "../../actions";

const Selector = ({
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
}) => {
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
                marginTop: "5vh",
                maxWidth: "45vh",
            }}
        >
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
        </div>
    );

    const courseList = (
        <CourseList
            sortMode={sortMode}
            isLoading={isLoadingCourseInfo}
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
                            manage={{
                                addToSchedule,
                                removeFromSchedule,
                            }}
                        />
                    )}
                </div>
            </div>
        ) : (
            <CourseInfo
                getCourse={getCourse}
                course={course}
                back={clearCourse}
                manage={{
                    addToSchedule,
                    removeFromSchedule,
                }}
            />
        );
    }
    return <>{isLoading ? loadingIndicator : element}</>;
};

Selector.propTypes = {
    courses: PropTypes.arrayOf(PropTypes.object).isRequired,
    course: PropTypes.objectOf(PropTypes.any),
    getCourse: PropTypes.func.isRequired,
    clearCourse: PropTypes.func,
    addToSchedule: PropTypes.func,
    sortMode: PropTypes.string,
    removeFromSchedule: PropTypes.func,
    isLoadingCourseInfo: PropTypes.bool,
    isSearchingCourseInfo: PropTypes.bool,
    view: PropTypes.number,
    scrollPos: PropTypes.number,
    setScrollPos: PropTypes.func,
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
}) => ({
    courses: searchResults.filter(({ num_sections: num }) => num > 0),
    course,
    scrollPos,
    sortMode,
    isLoadingCourseInfo,
    isSearchingCourseInfo,
});

const mapDispatchToProps = (dispatch) => ({
    getCourse: (courseId) => dispatch(fetchCourseDetails(courseId)),
    clearCourse: () => dispatch(updateCourseInfo(null)),
    addToSchedule: (section) => dispatch(addSchedItem(section)),
    removeFromSchedule: (id) => dispatch(removeSchedItem(id)),
    setScrollPos: (scrollPos) => dispatch(updateScrollPos(scrollPos)),
});

export default connect(mapStateToProps, mapDispatchToProps)(Selector);
