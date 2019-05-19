import React, { Component } from "react";
import PropTypes from "prop-types";

import Badge from "../Badge";

export default class SectionDisplay extends Component {
    stripTime = (s) => {
        let newS = s.replace(" to ", "-");
        newS = newS.replace("on", "");
        return newS;
    };

    getTimeString = (meetings) => {
        const intToTime = (t) => {
            let hour = Math.floor(t % 12);
            let min = Math.round((t % 1) * 100);
            if (hour === 0) {
                hour = 12;
            }
            if (min === 0) {
                min = "00";
            }
            return `${hour}:${min}`;
        };
        const times = {};
        let maxcount = 0;
        let maxrange = null;
        meetings.forEach((meeting) => {
            const rangeId = `${meeting.start}-${meeting.end}`;
            if (!times[rangeId]) {
                times[rangeId] = [meeting.day];
            } else {
                times[rangeId].push(meeting.day);
            }
            if (times[rangeId].length > maxcount) {
                maxcount = times[rangeId].length;
                maxrange = rangeId;
            }
        });

        const days = ["M", "T", "W", "R", "F", "S", "U"];
        let daySet = "";
        days.forEach((day) => {
            times[maxrange].forEach((d) => {
                if (d === day) {
                    daySet += day;
                }
            });
        })

        return `${intToTime(maxrange.split("-")[0])}-${intToTime(maxrange.split("-")[1])} ${daySet}`;
    };

    justSection = s => s.substring(s.lastIndexOf(" ") + 1);

    getAddRemoveIcon = () => {
        const {
            addSchedItem,
            removeSchedItem,
            section,
            inSchedule,
        } = this.props;

        let className = "fas";
        if (!inSchedule) {
            className += " fa-plus";
        } else {
            className += " fa-times";
        }
        let onClick;

        if (!inSchedule) {
            onClick = () => {
                addSchedItem(section);
            };
        } else {
            onClick = () => {
                removeSchedItem(section.id);
            };
        }

        return (
            <span className="icon">
                <i className={className} onClick={onClick} role="button" />
            </span>
        );
    }

    getPcaButton = () => {
        let onClick;
        return (
            <i
                className="far fa-bell"
                onClick={onClick}
                title="Penn Course Alert"
                role="button"
            />
        );
    }

    getInstructorReview = () => (
        <Badge
            baseColor={[46, 204, 113]}
            value={3}
        />
    );

    render() {
        const {
            section,
            overlap,
            openSection,
        } = this.props;

        // let className = section.actType;
        let className = "";
        // Not quite sure why className is actType
        // TODO: implement activeItem based on sectionInfo schema in the future
        // if (section === section.idSpaced.replace(" ", "").replace(" ", "")) {
        //     className += " activeItem";
        // }

        if (overlap) {
            className += " hideSec";
        }
        return (
            <li
                id={section.id}
                className={className}
                onClick={openSection}
                style={{ cursor: "pointer" }}
                role="menuitem"
                // could be incorporated to css
            >
                <div className="columns is-gapless">
                    <div className="column is-one-fifth">
                        { this.getAddRemoveIcon() }
                        <span className="icon">
                            {!section.isOpen ? this.getPcaButton()
                                : (
                                    <i className="fas fa-square has-text-success" />
                                )
                            }
                        </span>

                    </div>

                    <div className="column is-one-fifth">
                        { this.getInstructorReview() }
                    </div>

                    <div className="column is-one-fifth" style={{ marginLeft: "0.4rem", marginTop: "2px" }}>
                        <span
                            className="sectionText"
                        >
                            { this.justSection(section.id.replace(/-/g, " ")) }
                        </span>
                    </div>

                    <div className="column" style={{ marginTop: "2px" }}>
                        <span
                            className="sectionText"
                        >
                            { this.getTimeString(section.meetings) }
                        </span>
                    </div>
                </div>
            </li>
        );
    }
}

SectionDisplay.propTypes = {
    addSchedItem: PropTypes.func.isRequired,
    removeSchedItem: PropTypes.func.isRequired,
    openSection: PropTypes.func.isRequired,
    inSchedule: PropTypes.bool.isRequired,
    overlap: PropTypes.bool.isRequired,
    section: PropTypes.shape({
        revs: PropTypes.object,
        pcrIShade: PropTypes.number,
        pcrIColor: PropTypes.string,
    }),
};
