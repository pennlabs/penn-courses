import React from "react";
import PropTypes from "prop-types";

import connect from "react-redux/es/connect/connect";

import "../../styles/selector.css";

import CourseList from "./CourseList";
import CourseInfo from "./CourseInfo";

import {
    fetchCourseDetails, updateCourseInfo, addSchedItem, removeSchedItem
} from "../../actions";

function Selector(props) {
    const {
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
    } = props;

    const isLoading = isSearchingCourseInfo || (isLoadingCourseInfo && view === 0);

    const loadingIndicator = (
        <div
            className="button is-loading"
            style={{
                height: "100%", width: "100%", border: "none", fontSize: "3rem",
            }}
        />
    );

    let element = (
        <div style={{
            fontSize: "0.8em",
            textAlign: "center",
            marginTop: "5vh",
            maxWidth: "45vh",
        }}
        >
            <img src="/static/empty-state-search.svg" />

            <h3 style={{
                fontWeight: "bold",
                marginBottom: "0.5rem",
            }}
            >
            No result found
            </h3>
        Search for courses, departments, or instructors above.
        Looking for something specific? Try using the filters!
        </div>
    );

    const courseList = (
        <CourseList
            sortMode={sortMode}
            isLoading={isLoadingCourseInfo}
            courses={courses}
            getCourse={getCourse}
        />
    );


    if (courses.length > 0 && !course) {
        if (view === 0) {
            element = courseList;
        } else {
            element = (
                <div className="columns">
                    <div className="column is-one-third" style={{ height: "calc(100vh - 12.5em)", borderRight: "1px solid #dddddd" }}>
                        {courseList}
                    </div>
                </div>

            );
        }
    }

    if (course) {
        if (view === 0) {
            element = (
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
        } else {
            element = (
                <div className="columns">
                    <div className="column is-one-third" style={{ height: "calc(100vh - 12.5em)", borderRight: "1px solid #dddddd" }}>
                        {courseList}
                    </div>
                    <div className="column is-two-thirds" style={{ height: "calc(100vh - 12.5em)" }}>
                        {isLoadingCourseInfo ? loadingIndicator
                            : (
                                <CourseInfo
                                    getCourse={getCourse}
                                    course={course}
                                    view={view}
                                    manage={{
                                        addToSchedule,
                                        removeFromSchedule,
                                    }}
                                />
                            )
                        }
                    </div>

                </div>
            );
        }
    }
    return (
        <>
            {isLoading ? loadingIndicator : element}
        </>
    );
}

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
};

const mapStateToProps = state => (
    {
        courses: state.sections.searchResults.filter(course => course.num_sections > 0),
        course: state.sections.course,
        sortMode: state.sections.sortMode,
        isLoadingCourseInfo: state.sections.courseInfoLoading,
        isSearchingCourseInfo: state.sections.searchInfoLoading,
    }
);


const mapDispatchToProps = dispatch => (
    {
        getCourse: courseId => dispatch(fetchCourseDetails(courseId)),
        clearCourse: () => dispatch(updateCourseInfo(null)),
        addToSchedule: section => dispatch(addSchedItem(section)),
        removeFromSchedule: id => dispatch(removeSchedItem(id)),
    }
);

export default connect(mapStateToProps, mapDispatchToProps)(Selector);
