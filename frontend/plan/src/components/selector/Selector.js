import React from "react";
import PropTypes from "prop-types";

import connect from "react-redux/es/connect/connect";

import "../../styles/selector.css";

import CourseList from "./courses/CourseList";

function Selector({ courses }) {
    return (
        <CourseList courses={courses} />
    );
}

Selector.propTypes = {
    courses: PropTypes.arrayOf(PropTypes.object).isRequired,
};

const mapStateToProps = state => (
    {
        courses: state.sections.searchResults,
    }
);


const mapDispatchToProps = dispatch => (
    {}
);

export default connect(mapStateToProps, mapDispatchToProps)(Selector);
