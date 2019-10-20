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
        sortMode
    } = props;

    let element = <CourseList sortMode={sortMode}
                              courses={courses} getCourse={getCourse}/>;

    if (course) {
        element = (
            <CourseInfo
                getCourse={getCourse}
                course={course}
                back={clearCourse}
                manage={{
                    addToSchedule,
                    removeFromSchedule
                }}
            />
        );
    }


    return element;
}

Selector.propTypes = {
    courses: PropTypes.arrayOf(PropTypes.object).isRequired,
    course: PropTypes.objectOf(PropTypes.any),
    getCourse: PropTypes.func.isRequired,
    clearCourse: PropTypes.func,
    addToSchedule: PropTypes.func,
    sortMode: PropTypes.string,
};

const mapStateToProps = state => (
    {
        courses: state.sections.searchResults.filter(course => course.num_sections > 0),
        course: state.sections.course,
        sortMode: state.sortMode,
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
