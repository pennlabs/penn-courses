import React from "react";
import PropTypes from "prop-types";

export default function CourseDetail({ course, back }) {
    return (
        <div style={{ height: "100%" }}>
            <button className="delete" type="button" onClick={back} />
            { course.id }
            <pre style={{ overflowY: "auto", maxHeight: "90%" }}>
                { JSON.stringify(course, null, 2) }
            </pre>
        </div>
    );
}

CourseDetail.propTypes = {
    course: PropTypes.objectOf(PropTypes.any).isRequired,
    back: PropTypes.func,
};
