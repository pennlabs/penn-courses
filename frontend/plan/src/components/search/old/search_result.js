import React from "react";
import PropTypes from "prop-types";

import Badge from "../../Badge";

export function SearchResult({ course, requestSectionInfo }) {
    return (
        <li
            id={course.id}
            onClick={() => requestSectionInfo()}
            role="menuitem"
        >
            <Badge
                baseColor={[45, 160, 240]}
                value={2.0}
            />
            <Badge
                baseColor={[231, 76, 60]}
                value={4.0}
            />

            <span className="cID">
                {course.id}
            </span>
            &nbsp;
            <span className="cTitle">
                {course.title}
            </span>

        </li>
    );
}

SearchResult.propTypes = {
    // eslint-disable-next-line react/forbid-prop-types
    course: PropTypes.object.isRequired,
    requestSectionInfo: PropTypes.func.isRequired,
};
