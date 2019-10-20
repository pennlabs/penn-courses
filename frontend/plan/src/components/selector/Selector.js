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
        <CourseList
            sortMode={sortMode}
            isLoading={isLoadingCourseInfo}
            courses={courses}
            getCourse={getCourse}
        />
    );

    if (course) {
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
        sortMode: state.sortMode,
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
