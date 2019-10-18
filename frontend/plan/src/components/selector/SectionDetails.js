import React from "react";
import PropTypes from "prop-types";

import { getTimeString } from "../../meetUtil";

const getSectionId = id => (tokens => tokens[tokens.length - 1])(id.split("-"));

export default function SectionDetails({ section, isOpen }) {
    const { id, instructors, meetings } = section;
    return (
        <li style={{ display: isOpen ? "block" : "none" }}>
            <div style={{ margin: ".5em .5em .5em 2em", maxHeight: "40%" }}>
                <h3 className="title is-6 section-details-title">
                    <b>{`${getSectionId(id)}`}</b>
                    &nbsp;&nbsp;
                    {`${instructors.join(", ")}`}
                </h3>
                <i className="far fa-clock" />
                &nbsp;
                {getTimeString(meetings)}
                &nbsp;&nbsp;
                <i className="fas fa-map-marker-alt" />
                &nbsp;
                {meetings.map(m => m.room).join(", ")}
            </div>
        </li>
    );
}

SectionDetails.propTypes = {
    // eslint-disable-next-line
    section: PropTypes.object.isRequired,
    isOpen: PropTypes.bool.isRequired,
};
