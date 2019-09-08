import React from "react";
import PropTypes from "prop-types";
import CourseDetails from "./CourseDetails";
import SectionList from "./SectionList";

export default function CourseInfo({ course, back }) {
    return (
        <div style={{ height: "100%", display: "flex", flexDirection: "column" }}>
            <div className="segment" style={{ maxHeight: "10%" }}>
                <button type="button" className="button is-white" onClick={back} style={{ fontSize: "1em" }}>
                    <span className="icon">
                        <i className="fas fa-arrow-left" />
                    </span>
                    &nbsp; Back
                </button>
            </div>
            <div style={{ margin: ".5em", maxHeight: "40%" }}>
                <h3 className="title is-4">{course.id}</h3>
                <h5 className="subtitle is-6">{course.title}</h5>
                <CourseDetails course={course} />
            </div>
            <SectionList sections={course.sections} />
        </div>
    );
}

CourseInfo.propTypes = {
    course: PropTypes.objectOf(PropTypes.any).isRequired,
    back: PropTypes.func,
};
