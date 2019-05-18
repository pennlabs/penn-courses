import React from "react";
import PropTypes from "prop-types";

export function SearchResult({ course, requestSectionInfo }) {
    return (
        <li
            id={course.idDashed}
            onClick={() => requestSectionInfo()}
            role="menuitem"
        >
            <span
                className="PCR Qual"
                style={{
                    background: `rgba(45, 160, 240, ${course.pcrQShade})`,
                    color: course.pcrQColor,
                }}
            >
                {course.revs.cQ || course.revs.cQT}
            </span>

            <span
                className="PCR Diff"
                style={{
                    background: `rgba(231, 76, 60, ${course.pcrDShade})`,
                    color: course.pcrDColor,
                }}
            >
                {course.revs.cD || course.revs.cDT}
            </span>

            <span className="cID">
                {course.idSpaced}
            </span>

            <span className="cTitle">
                {course.courseTitle}
            </span>

        </li>
    );
}

SearchResult.propTypes = {
    // eslint-disable-next-line react/forbid-prop-types
    course: PropTypes.object.isRequired,
    requestSectionInfo: PropTypes.func.isRequired,
};
