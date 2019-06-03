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
} from "../../../actions";
import { meetingSetsIntersect } from "../../../meetUtil";

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


class Sections extends Component {
    scheduleContains = (sectionID) => {
        const { scheduleMeetings } = this.props;
        return scheduleMeetings.map(section => section.id).indexOf(sectionID) !== -1;
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
                            return meetingSetsIntersect(
                                // get all meetings from the current schedule.
                                scheduleMeetings
                                    .map(sec => sec.meetings)
                                    .reduce((acc, val) => acc.concat(val), []),
                                // and see if they intersect with this section's meeting times.
                                section.meetings
                            );
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
