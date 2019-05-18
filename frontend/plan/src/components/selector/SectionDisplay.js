import React, { Component } from "react";
import PropTypes from "prop-types";

export default class SectionDisplay extends Component {
    stripTime = (s) => {
        let newS = s.replace(" to ", "-");
        newS = newS.replace("on", "");
        return newS;
    }

    justSection = s => s.substring(s.lastIndexOf(" ") + 1);

    getAddRemoveIcon = () => {
        const {
            addSchedItem,
            removeSchedItem,
            section: {
                revs,
                fullSchedInfo,
            },
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
                addSchedItem({ ...fullSchedInfo[0], revs });
            };
        } else {
            onClick = () => {
                removeSchedItem(fullSchedInfo[0].fullID);
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

    getInstructorReview = () => {
        const {
            section: {
                revs,
                pcrIShade,
                pcrIColor,
            },
        } = this.props;

        const bgColor = `rgba(46, 204, 113, ${pcrIShade})`;
        return (
            <span
                className="PCR Inst"
                style={{ background: bgColor, color: pcrIColor, marginTop: "2px" }}
            >
                { revs.cI }
            </span>
        );
    }

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
        /* if((!$scope.sched.SecOverlap(this.section)
            && $scope.schedSections.indexOf(this.section.idDashed) === -1)){
            className += "hideSec";
        } */
        return (
            <li
                id={section.idDashed}
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
                            { this.justSection(section.idSpaced) }
                        </span>
                    </div>

                    <div className="column" style={{ marginTop: "2px" }}>
                        <span
                            className="sectionText"
                        >
                            { this.stripTime(section.timeInfo) }
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
