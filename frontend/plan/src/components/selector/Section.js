import React, { useState } from "react";
import PropTypes from "prop-types";
import "bulma-popover/css/bulma-popver.min.css";

import Badge from "../Badge";
import SectionDetails from "./SectionDetails";

import { getTimeString } from "../../meetUtil";

export default function Section({ section, cart, inCart }) {
    const [isOpen, toggleOpen] = useState(false);
    const { instructors } = section;
    return (
<<<<<<< HEAD
        <>
            <li>
                <a
                    role="button"
                    className="selector-row section-row"
                    onClick={() => toggleOpen(!isOpen)}
                >
                    <div
                        role="button"
                        onClick={inCart ? cart.remove : cart.add}
                    >
                        {inCart ? (
                            <div className="hover-switch">
                                <i className="fas fa-check" />
                                <i className="fas fa-times" />
                            </div>
                        ) : <i className="fas fa-plus" />}
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
                                {instructors.length > 1 ? `${instructors[0]}, and ${instructors.length - 1} other(s)` : instructors[0]}
                            </span>
                        </div>
                    </div>
                    <div>
                        {section.activity}
                    </div>
                    <div>
                        {getTimeString(section.meetings)}
                    </div>
                </a>
            </li>
            <SectionDetails section={section} isOpen={isOpen} />
        </>
=======
        // eslint-disable-next-line
        <li className="selector-row section-row" onClick={inCart ? cart.remove : cart.add}>
            <div>
                {section.id.split("-").pop()}
            </div>
            <div>
                { section.activity }
            </div>
            <div style={{ whiteSpace: "nowrap" }}>
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
>>>>>>> master
    );
}

Section.propTypes = {
    // eslint-disable-next-line
    section: PropTypes.object.isRequired,
    cart: PropTypes.objectOf(PropTypes.func),
    inCart: PropTypes.bool,
};
