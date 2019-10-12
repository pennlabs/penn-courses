import React from "react";
import PropTypes from "prop-types";
import "bulma-popover/css/bulma-popver.min.css";

import Badge from "../Badge";

import { getTimeString } from "../../meetUtil";

export default function Section({ section, cart, inCart }) {
    return (
        // eslint-disable-next-line
        <li className="selector-row section-row" onClick={inCart ? cart.remove : cart.add}>
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
                {inCart ? <i className="fas fa-times" /> : <i className="fas fa-plus" />}
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
