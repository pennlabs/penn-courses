import React from "react";
import PropTypes from "prop-types";

import Badge from "../../Badge";

export default function Course({ course }) {
    return (
        <div className="columns selector-row">
            <div className="column">
                <Badge
                    baseColor={[45, 160, 240]}
                    value={course.course_quality}
                />
            </div>
            <div className="column">
                <Badge
                    baseColor={[231, 76, 60]}
                    value={course.difficulty}
                />
            </div>
            <div className="column is-two-thirds" style={{ paddingRight: "1em" }}>
                {`${course.id} ${course.title}`}
            </div>
        </div>
    );
}

Course.propTypes = {
    // eslint-disable-next-line
    course: PropTypes.object.isRequired,
};
