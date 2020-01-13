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
    } = props;
    let element = (
        <div style={{
            fontSize: "0.8em",
            textAlign: "center",
            marginTop: "5vh",
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

    if (courses.length > 0) {
        element = (
            <CourseList
                sortMode={sortMode}
                isLoading={isLoadingCourseInfo}
                courses={courses}
                getCourse={getCourse}
            />
        );
    }

    if (course) {
        element = (
            <CourseInfo
                getCourse={getCourse}
                course={course}
                back={courses.length > 1 ? clearCourse : null}
                manage={{
                    addToSchedule,
                    removeFromSchedule,
                }}
            />
        );
    }

    const isLoading = isLoadingCourseInfo || isSearchingCourseInfo;

    return (
        <>
            {isLoading && (
                <div
                    className="button is-loading"
                    style={{
                        height: "100%", width: "100%", border: "none", fontSize: "3rem",
                    }}
                />
            )
            }
            {!isLoading && element}
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
