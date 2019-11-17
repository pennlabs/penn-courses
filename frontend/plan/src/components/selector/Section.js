import React from "react";
import PropTypes from "prop-types";
import "bulma-popover/css/bulma-popver.min.css";

import Badge from "../Badge";

import { getTimeString } from "../../meetUtil";

export default function Section({
    section, cart, inCart,
}) {
    const { instructors, meetings, status } = section;
    return (
        <div className="course_section">
            <li style={{
                display: "flex", alignItems: "center", marginBottom: "0", borderBottom: "1px solid rgb(230, 230, 230)",
            }}
            >
                <div style={{
                    display: "flex", flexDirection: "column", flexGrow: "1", padding: "1em", paddingRight: "0",
                }}
                >
                    <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center" }}>
                        <div style={{ fontSize: "1rem", fontWeight: "bold", marginRight: "1em", display: "flex", alignItems: "center" }}>
                            {`${section.id.split("-").pop()} `}
                            <span style={{ fontSize: "0.70rem", marginLeft: "0.5em", fontWeight: "normal" }}>{section.activity}</span>
                        </div>
                        <div style={{
                            fontSize: "0.85rem", fontWeight: "bold", textOverflow: "ellipsis", flexGrow: "6",
                        }}
                        >
                            {instructors.length > 0
                                ? (
                                    <>
                                        {instructors.map((elem, ind) => (
                                            <>
                                                {ind !== 0 ? <br /> : null}
                                                {ind !== instructors.length - 1 ? `${elem},` : elem}
                                            </>
                                        ))}
                                    </>
                                )
                                : <div> N/A </div>
                            }
                        </div>
                    </div>
                    <div style={{
                        marginTop: "0.5em", display: "grid", fontSize: "0.7rem", gridTemplateColumns: "40% 15% 40%",
                    }}
                    >
                        <div>
                            {getTimeString(meetings)}
                        </div>
                        <div>
                            {`${section.credits} CU`}
                        </div>
                        <div>
                            {meetings.length > 0 ? (
                                <div>
                                    <i className="fas fa-map-marker-alt grey-text" />
                            &nbsp;
                                    {((l) => { // formats location names
                                        const ret = new Set();
                                        l.forEach(({ room }) => ret.add(room.trim()));
                                        return Array.from(ret);
                                    })(meetings).join(", ")}
                                </div>
                            ) : null}
                        </div>
                    </div>
                </div>
                <div style={{ display: "flex", flexDirection: "column", alignItems: "center" }}>
                    <div>
                        {instructors.length > 0 ? (
                            <div className="popover is-popover-left">
                                <Badge
                                    baseColor={[43, 236, 56]}
                                    value={section.instructor_quality}
                                />
                                <span className="popover-content">
                                    Instructor Quality
                                </span>
                            </div>
                        ) : (
                            <Badge
                                baseColor={[43, 236, 56]}
                                value={section.instructor_quality}
                            />
                        )}
                    </div>
                    { status == "C"
                        ? (
                            <div className="popover is-popover-left">
                                <a className="bell" target="_blank" href={`https://penncoursealert.com/?course=${section.id}`}>
                                    <i style={{ fontSize: "1rem" }} className="far fa-bell" />
                                </a>

                                <span className="popover-content"> Course is closed. Sign up for an alert! </span>
                            </div>
                        )
                        : <div />
                    }
                </div>
                <div
                    role="button"
                    onClick={inCart ? cart.remove : cart.add}
                    style={{ padding: "1.8em", paddingLeft: "1em", width: "2.5em" }}
                >
                    {inCart ? (
                        <div className="hover-switch">
                            <i className="fas fa-check" />
                            <i className="fas fa-times" />
                        </div>
                    ) : <i className="fas fa-plus" />}
                </div>

            </li>
        </div>
    );
}

Section.propTypes = {
    // eslint-disable-next-line
    section: PropTypes.object.isRequired,
    cart: PropTypes.objectOf(PropTypes.func),
    inCart: PropTypes.bool,
};
