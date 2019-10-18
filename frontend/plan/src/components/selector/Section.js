import React from "react";
import PropTypes from "prop-types";
import "bulma-popover/css/bulma-popver.min.css";

import Badge from "../Badge";

import { getTimeString } from "../../meetUtil";

export default function Section({ section, cart, inCart }) {
    return (
        // eslint-disable-next-line
        <li className="selector-row section-row">
            <div onClick={inCart ? cart.remove : cart.add}>
                {inCart ? <div className="hover-switch">
                    <i className="fas fa-check" />
                    <i className="fas fa-times" />
                </div> : <i className="fas fa-plus" />}
            </div>
            <div>
                {section.id.split("-").pop()}
            </div>
            <div>
                <div className="popover is-popover-right">
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
                { section.activity }
            </div>
            <div>
                { getTimeString(section.meetings) }
            </div>
        </li>
    );
}

Section.propTypes = {
    // eslint-disable-next-line
    section: PropTypes.object.isRequired,
    cart: PropTypes.objectOf(PropTypes.func),
    inCart: PropTypes.bool,
};
