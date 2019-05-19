import React, { Component } from "react";
import connect from "react-redux/es/connect/connect";
import PropTypes from "prop-types";
import SectionInfoDisplay from "./SectionInfoDisplay";
import SectionList from "./SectionList";
import {
    addSchedItem,
    removeSchedItem,
    updateSearch,
    updateSectionInfo,
    updateSections
} from "../../actions";

const mapDispatchToProps = dispatch => (
    {
        addSchedItem: schedItem => dispatch(addSchedItem(schedItem)),
        removeSchedItem: fullID => dispatch(removeSchedItem(fullID)),
        updateSearch: searchResults => dispatch(updateSearch(searchResults)),
        updateSections: sections => dispatch(updateSections(sections)),
        updateSectionInfo: sectionInfo => dispatch(updateSectionInfo(sectionInfo)),
    }
);

const mapStateToProps = state => (
    {
        sectionInfo: state ? state.sections.sectionInfo : undefined,
        sections: state ? state.sections.sections : undefined,
        scheduleMeetings: state ? state.schedule.schedules[state.schedule.scheduleSelected]
            .meetings : [],
    }
);

// finds intersections between meeting times
const meetingTimeIntersection = (meetingTimesA, meetingTimesB) => {
    const overlap = (m1, m2) => {
        const start1 = m1.start;
        const start2 = m2.start;
        const end1 = m1.end;
        const end2 = m2.end;
        return m1.day === m2.day && !(end1 <= start2 || end2 <= start1);
    };
    for (let i = 0; i < meetingTimesA.length; i += 1) {
        for (let j = 0; j < meetingTimesB.length; j += 1) {
            const meetingA = meetingTimesA[i];
            const meetingB = meetingTimesB[j];
            if (overlap(meetingA, meetingB)) {
                return true;
            }
        }
    }
    return false;
};


class Sections extends Component {
    scheduleContains = (sectionID) => {
        const {
            scheduleMeetings,
        } = this.props;
        return scheduleMeetings.map(section => section.sectionId).indexOf(sectionID) !== -1;
    }

    render() {
        /* eslint-disable no-shadow */
        const {
            sectionInfo,
            updateSectionInfo,
            scheduleMeetings,
            sections,
            addSchedItem,
            removeSchedItem,
        } = this.props;
        /* eslint-enable no-shadow */
        return (
            <div
                id="SectionCol"
                className="box column is-half"
            >
                <div id="Sections">
                    <div
                        className="columns is-gapless"
                        style={{
                            marginBottom: "0.6em",
                            overflow: "hidden",
                            textOverflow: "ellipsis",
                            whiteSpace: "nowrap",
                        }}
                    >
                        <div
                            className="tooltip column is-one-fifth"
                            title="Section status (open or closed)"
                        >
                            O/C
                        </div>
                        <div
                            className="PCR Inst tooltip column is-one-fifth"
                            title="Instructor Quality rating"
                            style={{ background: "rgba(46, 204, 113, 0.85)" }}
                        >
                            Inst
                        </div>
                        <div className="tooltip column is-one-fifth" title="Section ID">
                            Sect
                        </div>
                        <div
                            className="tooltip column"
                            title="Meeting Time"
                        >
                            Time
                        </div>
                    </div>
                    <SectionList
                        updateSectionInfo={updateSectionInfo}
                        scheduleContains={this.scheduleContains}
                        overlaps={(section) => {
                            if (this.scheduleContains(section.id)) {
                                return false;
                            }
                            return meetingTimeIntersection(scheduleMeetings, section.meetings);
                        }}
                        sections={sections}
                        addSchedItem={addSchedItem}
                        removeSchedItem={removeSchedItem}
                    />
                </div>
                {sectionInfo && <SectionInfoDisplay sectionInfo={sectionInfo} />}
            </div>
        );
    }
}

export default connect(
    mapStateToProps,
    mapDispatchToProps
)(Sections);

Sections.propTypes = {
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
    updateSectionInfo: PropTypes.func.isRequired,
    scheduleMeetings: PropTypes.arrayOf(PropTypes.object).isRequired,
    sections: PropTypes.arrayOf(PropTypes.object).isRequired,
    addSchedItem: PropTypes.func.isRequired,
    removeSchedItem: PropTypes.func.isRequired,
};
