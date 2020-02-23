import React from "react";
import PropTypes from "prop-types";
import CourseDetails from "./CourseDetails";
import SectionList from "./SectionList";

export default function CourseInfo({
    course, back, getCourse, view,
}) {
    const { id, title, sections } = course;
    return (
        <div style={{ height: "100%", display: "flex", flexDirection: "column" }}>
            <div style={{ maxHeight: "10%" }}>
                {back
                    && (
                        <button type="button" className="button back-button grey-text" onClick={back} style={{ fontSize: "1em" }}>
                            <span className="icon">
                                <i className="fas fa-arrow-left" />
                            </span>
                        &nbsp; Back
                        </button>
                    )
                }
            </div>
            <div style={{ margin: ".5em .5em .5em 2em" }}>
                <h3 className="title is-4">{id.replace(/-/g, " ")}</h3>
                <h5 className="subtitle is-6">{title}</h5>
            </div>
            <ul className="badges-list scrollable">
                <div style={{ margin: ".5em .5em .5em 2em" }}>
                    <CourseDetails view={view} course={course} getCourse={getCourse} />
                </div>
                <SectionList view={view} sections={sections} />
            </ul>
        </div>
    );
}

CourseInfo.propTypes = {
    course: PropTypes.objectOf(PropTypes.any).isRequired,
    back: PropTypes.func,
    getCourse: PropTypes.func,
    view: PropTypes.number,
};
