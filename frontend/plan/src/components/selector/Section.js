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
                        {instructors.length > 0 ? (
                            <div className="popover is-popover-right">
                                <Badge
                                    baseColor={[43, 236, 56]}
                                    value={section.instructor_quality}
                                />
                                <span className="popover-content">
                                    {instructors.length > 1 ? `${instructors[0]}, and ${instructors.length - 1} other(s)` : instructors[0]}
                                </span>
                            </div>
                        ) : (
                            <Badge
                                baseColor={[43, 236, 56]}
                                value={section.instructor_quality}
                            />
                        )}
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
    );
}

Section.propTypes = {
    // eslint-disable-next-line
    section: PropTypes.object.isRequired,
    cart: PropTypes.objectOf(PropTypes.func),
    inCart: PropTypes.bool,
};
