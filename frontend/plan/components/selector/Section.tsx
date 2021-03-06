import React from "react";
import scrollIntoView from "scroll-into-view-if-needed";

import Badge from "../Badge";

import { getTimeString } from "../meetUtil";
import { Section as SectionType } from "../../types";

interface SectionProps {
    section: SectionType;
    cart: {
        add: () => void;
        remove: () => void;
    };
    inCart: boolean;
}

export default function Section({ section, cart, inCart }: SectionProps) {
    const { instructors, meetings, status } = section;
    const cartAdd = () => {
        cart.add();
        setTimeout(() => {
            const target = document.getElementById(section.id);
            if (target !== null) {
                scrollIntoView(target, {
                    behavior: "smooth",
                    block: "end",
                    scrollMode: "if-needed",
                });
            }
        }, 50);
    };
    return (
        <div className="course_section">
            <li
                style={{
                    display: "flex",
                    alignItems: "center",
                    marginBottom: "0",
                    borderBottom: "1px solid rgb(230, 230, 230)",
                }}
            >
                <div
                    style={{
                        display: "flex",
                        flexDirection: "row",
                        flexWrap: "wrap",
                        flexGrow: 1,
                        justifyContent: "space-between",
                        padding: "1em",
                        paddingRight: "0",
                    }}
                >
                    <div
                        style={{
                            display: "flex",
                            justifyContent: "space-between",
                            alignItems: "center",
                        }}
                    >
                        <div
                            style={{
                                fontSize: "1rem",
                                fontWeight: "bold",
                                marginRight: "1em",
                                display: "flex",
                                alignItems: "center",
                            }}
                        >
                            {`${section.id.split("-").pop()} `}
                            <span
                                style={{
                                    fontSize: "0.70rem",
                                    marginLeft: "0.5em",
                                    fontWeight: "normal",
                                }}
                            >
                                {section.activity}
                            </span>
                        </div>
                        <div
                            style={{
                                fontSize: "0.85rem",
                                fontWeight: "bold",
                                textOverflow: "ellipsis",
                                flexGrow: 6,
                            }}
                        >
                            {instructors.length > 0 ? (
                                <>
                                    {instructors.map((elem, ind) => (
                                        <div key={elem.id}>
                                            {ind !== 0 ? <br /> : null}
                                            {ind !== instructors.length - 1
                                                ? `${elem.name},`
                                                : elem.name}
                                        </div>
                                    ))}
                                </>
                            ) : (
                                <div> N/A </div>
                            )}
                        </div>
                    </div>
                    <div
                        style={{
                            minWidth: "200px",
                            marginTop: "0.5em",
                            display: "grid",
                            fontSize: "0.7rem",
                            gridTemplateColumns: "40% 15% 40%",
                        }}
                    >
                        <div>{meetings && getTimeString(meetings)}</div>
                        <div>{`${section.credits} CU`}</div>
                        <div>
                            {meetings && meetings.length > 0 ? (
                                <div>
                                    <i className="fas fa-map-marker-alt grey-text" />
                                    &nbsp;
                                    {((l) => {
                                        // formats location names
                                        const ret = new Set();
                                        l.forEach(({ room }) =>
                                            ret.add(room.trim())
                                        );
                                        return Array.from(ret);
                                    })(meetings).join(", ")}
                                </div>
                            ) : null}
                        </div>
                    </div>
                </div>
                <div
                    style={{
                        display: "flex",
                        flexDirection: "row",
                        flexWrap: "wrap",
                        justifyContent: "center",
                        alignItems: "center",
                    }}
                >
                    <div>
                        {instructors.length > 0 ? (
                            <div className="popover is-popover-left">
                                <Badge value={section.instructor_quality} />
                                <span className="popover-content">
                                    Instructor Quality
                                </span>
                            </div>
                        ) : (
                            <Badge value={section.instructor_quality} />
                        )}
                    </div>
                    {status === "C" ? (
                        <div className="popover is-popover-left">
                            <a
                                className="bell"
                                target="_blank"
                                rel="noopener noreferrer"
                                href={`https://penncoursealert.com/?course=${section.id}`}
                            >
                                <i
                                    style={{ fontSize: "1rem" }}
                                    className="far fa-bell"
                                />
                            </a>

                            <span className="popover-content">
                                {" "}
                                Course is closed. Sign up for an alert!{" "}
                            </span>
                        </div>
                    ) : (
                        <div />
                    )}
                </div>
                <div
                    role="button"
                    onClick={inCart ? cart.remove : () => cartAdd()}
                    style={{
                        padding: "1.8em",
                        paddingLeft: "1em",
                        width: "2.5em",
                    }}
                >
                    {inCart ? (
                        <div className="hover-switch">
                            <i className="fas fa-check" />
                            <i className="fas fa-times" />
                        </div>
                    ) : (
                        <i className="fas fa-plus" />
                    )}
                </div>
            </li>
        </div>
    );
}
