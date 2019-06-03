import React from "react";
import PropTypes from "prop-types";

import connect from "react-redux/es/connect/connect";

import "../../styles/selector.css";

import CourseList from "./CourseList";
import CourseDetail from "./CourseDetail";

import { fetchCourseDetails, updateCourseInfo } from "../../actions";

function Selector(props) {
    const {
        courses,
        course,
        getCourse,
        clearCourse,
    } = props;
    let element = <CourseList courses={courses} getCourse={getCourse} />;

    if (course) {
        element = <CourseDetail course={course} back={clearCourse} />;
    }


    return element;
}

Selector.propTypes = {
    courses: PropTypes.arrayOf(PropTypes.object).isRequired,
    course: PropTypes.objectOf(PropTypes.any),
    getCourse: PropTypes.func.isRequired,
    clearCourse: PropTypes.func,
};

const mapStateToProps = state => (
    {
        courses: state.sections.searchResults,
        course: state.sections.course,
    }
);


const mapDispatchToProps = dispatch => (
    {
        getCourse: courseId => dispatch(fetchCourseDetails(courseId)),
        clearCourse: () => dispatch(updateCourseInfo(null)),
    }
);

export default connect(mapStateToProps, mapDispatchToProps)(Selector);
