import React, { Component } from "react";
import PropTypes from "prop-types";

export default class SectionInfoDisplay extends Component {
    static getStar = () => {
        const className = "fa fa-star";

        /* if($scope.starSections.indexOf($scope.currentSectionDashed) === -1){
            className += "-o";
        } */

        return (
            <i
                style={{ float: "right", marginRight: "2rem", color: "gold" }}
                className={className}
                // onClick={function () {
                //     //$scope.star.AddRem($scope.currentSectionDashed)
                //     }
                // }
            />
        );
    }

    render() {
        const {
            sectionInfo: {
                timeInfo,
                reqsFilled,
                associatedSections,
                fullID,
                title,
                instructor,
                description,
                prereqs,
                associatedType,
            },
        } = this.props;
        let timeInfoDisplay;
        if (timeInfo) {
            const meetings = [];
            for (let i = 0; i < timeInfo.length; i += 1) {
                const meeting = meetings[i];
                meetings.push(
                    <span key={i}>
                        {meeting}
                        <br />
                    </span>
                );
            }

            timeInfoDisplay = (
                <p style={{ display: "block" }}>
                    {meetings}
                </p>
            );
        }

        let requirementsDisplay;
        if (reqsFilled) {
            const reqs = [];
            for (let i = 0; i < reqsFilled.length; i += 1) {
                const req = reqsFilled[i];
                reqs.push(
                    <span key={i}>
                        {req}
                        <br />
                    </span>
                );
            }
            requirementsDisplay = (
                <span>
                    Requirements Fulfilled:
                    <br />
                    {reqs}
                    <br />
                </span>
            );
        }

        const assocSectionsDisp = [];
        if (associatedSections) {
            for (let i = 0; i < associatedSections.length; i += 1) {
                const associatedSection = associatedSections[i];
                assocSectionsDisp.push(
                    <li
                        key={i}
                        id={associatedSection.replace(" ", "-").replace(" ", "-")}
                        // onClick={function () {
                        //     //$scope.get.SectionInfo(self.state.sectionInfo
                        // .associatedSections[i].replace(" ", "-").replace(' ', '-'));
                        // }}
                    >
                        {associatedSection}
                        <br />
                    </li>
                );
            }
            assocSectionsDisp.push(<br key={associatedSections.length + 1} />);
        }

        return (
            <div id="SectionInfo">
                {fullID && (
                    <p style={{ fontSize: "1.25em" }}>
                        {(`${fullID}-${title}`)}
                        {associatedSections && this.getStar()}
                    </p>
                )}
                {timeInfoDisplay}
                {instructor && (
                    <p>
                        {`Instructor: ${instructor}`}
                        <br />
                        <br />
                    </p>
                )}
                {associatedSections && assocSectionsDisp}
                {description && (
                    <span>
                        {`Description: ${description}`}
                        <br />
                        <br />
                    </span>
                )}
                {requirementsDisplay}
                {prereqs && (
                    <span>
                        {`Prerequisites: ${prereqs}`}
                        <br />
                        <br />
                    </span>
                )}
                {associatedType && (
                    <span>
                        {`You must also sign up for a ${associatedType}.`}
                        <br />
                        {`Associated ${associatedType}s:`}
                        <br />
                    </span>
                )}
                <ul>
                    {assocSectionsDisp}
                </ul>
            </div>
        );
    }
}

SectionInfoDisplay.propTypes = {
    sectionInfo: PropTypes.shape({
        timeInfo: PropTypes.array,
        reqsFilled: PropTypes.array,
        associatedSections: PropTypes.array,
        fullID: PropTypes.string,
        title: PropTypes.string,
        instructor: PropTypes.string,
        description: PropTypes.string,
        prereqs: PropTypes.string,
        associatedType: PropTypes.string,
    }),
};
