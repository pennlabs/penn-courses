import React from "react";
import PropTypes from "prop-types";

import { getTimeString } from "../../meetUtil";

export default function SectionDetails({ section, isOpen }) {
    return (
        <li style={{ display: isOpen ? "block" : "none" }}>
            <div style={{ margin: ".5em .5em .5em 3em", maxHeight: "40%" }}>
                <h3 className="title is-5">{section.id}</h3>
                <h5 className="subtitle is-6">{section.instructors.join(", ")}</h5>
                <i className="far fa-clock" />
                &nbsp;
                {getTimeString(section.meetings)}
                &nbsp;&nbsp;
                <i className="fas fa-map-marker-alt" />
                &nbsp;
                {section.meetings.map(m => m.room).join(", ")}
            </div>
        </li>
    );
}

SectionDetails.propTypes = {
    // eslint-disable-next-line
    section: PropTypes.object.isRequired,
    isOpen: PropTypes.bool.isRequired,
};