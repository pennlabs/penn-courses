import React from "react";
import PropTypes from "prop-types";

import "bulma-popover/css/bulma-popver.min.css";

import { getTimeString } from "../../meetUtil";

const getSectionId = id => (tokens => tokens[tokens.length - 1])(id.split("-"));
const getClassCode = id => (tokens => tokens.slice(0, tokens.length - 1).join("-"))(id.split("-"));

export default function SectionDetails({ section, isOpen }) {
    const { id, instructors, meetings } = section;
    return (
        <li style={{ display: isOpen ? "block" : "none" }}>
            <div style={{
                margin: ".5em .5em .5em 3.25em", maxHeight: "40%", fontSize: ".75em", display: "block",
            }}
            >
                <div style={{ display: "flex", justifyContent: "flex-start" }}>
                    <h3
                        className="title is-6 section-details-title"
                        style={{
                            marginRight: "1em",
                        }}
                    >
                        <b>{`${getSectionId(id)}`}</b>
                    </h3>
                    <h3 className="title is-6 section-details-title" style={{ textOverflow: "ellipsis" }}>
                        {instructors.map((elem, ind) => (
                            <>
                                {ind !== 0 ? <br /> : null}
                                {ind !== instructors.length - 1 ? `${elem},` : elem}
                            </>
                        ))}
                    </h3>
                    <a
                        style={{
                            marginLeft: "auto",
                            marginRight: "2em",
                        }}
                        className="popover is-popover-left"
                        href={`https://penncoursereview.com/course/${getClassCode(id)}`}
                        target="_blank"
                        rel="noopener noreferrer"
                    >
                        <img
                            className="popover-trigger pcr-svg"
                            alt="PCR"
                            src="/static/pcr.svg"
                        />
                        <span className="popover-content">
                            View course on Penn Course Review
                        </span>
                    </a>
                </div>
                <br />
                <i className="far fa-clock grey-text" />
                &nbsp;
                {getTimeString(meetings)}
                &nbsp;&nbsp;
                {meetings.length > 0 ? (
                    <>
                        <i className="fas fa-map-marker-alt grey-text" />
                    &nbsp;
                        {((l) => {
                            const ret = new Set();
                            l.forEach(({ room }) => ret.add(room.trim()));
                            return Array.from(ret);
                        })(meetings).join(", ")}
                    </>
                ) : null}
            </div>
        </li>
    );
}

SectionDetails.propTypes = {
    // eslint-disable-next-line
    section: PropTypes.object.isRequired,
    isOpen: PropTypes.bool.isRequired,
};
