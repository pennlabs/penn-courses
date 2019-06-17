import React from "react";
import PropTypes from "prop-types";
import "bulma-popover/css/bulma-popver.min.css";

import Badge from "../Badge";

import { getTimeString } from "../../meetUtil";

export default function Section({ section, schedule, inSchedule }) {
    return (
        // eslint-disable-next-line
        <li className="selector-row section-row" onClick={inSchedule ? schedule.remove : schedule.add}>
            <div>
                {section.id.split("-").pop()}
            </div>
            <div>
                { section.activity }
            </div>
            <div>
                { getTimeString(section.meetings) }
            </div>
            <div>
                <div className="popover is-popover-left">
                    <Badge
                        baseColor={[43, 236, 56]}
                        value={section.instructor_quality}
                    />
                    <span className="popover-content">
                        Instructor Name
                    </span>
                </div>
            </div>
            <div>
                {inSchedule ? <i className="fas fa-times" /> : <i className="fas fa-plus" />}
            </div>
        </li>
    );
}

Section.propTypes = {
    // eslint-disable-next-line
    section: PropTypes.object.isRequired,
    schedule: PropTypes.objectOf(PropTypes.func),
    inSchedule: PropTypes.bool,
};
