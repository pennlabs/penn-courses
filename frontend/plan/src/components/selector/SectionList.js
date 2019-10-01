import React from "react";
import PropTypes from "prop-types";
import connect from "react-redux/es/connect/connect";

import Section from "./Section";
import { addCartItem, addSchedItem, removeSchedItem } from "../../actions";


function SectionList({ sections, scheduleSections, manageSchedule }) {
    const isInSchedule = ({ id }) => scheduleSections.indexOf(id) !== -1;
    return (
        [
            <div className="section-row segment">
                <div className="header">SECT</div>
                <div className="header">TYPE</div>
                <div className="header">TIME</div>
                <div className="header">INSTR</div>
            </div>,
            <ul className="scrollable">
                {sections.map(s => (
                    <Section
                        section={s}
                        schedule={manageSchedule(s)}
                        inSchedule={isInSchedule(s)}
                    />
                ))}
            </ul>
        ]
    );
}

SectionList.propTypes = {
    sections: PropTypes.arrayOf(PropTypes.object).isRequired,
};

const mapStateToProps = (state, ownProps) => (
    {
        ...ownProps,
        scheduleSections: state.schedule.schedules[state.schedule.scheduleSelected].meetings
            .map(sec => sec.id),
    }
);


const mapDispatchToProps = dispatch => (
    {
        manageSchedule: section => ({
            add: () => dispatch(addCartItem(section)),
            remove: () => dispatch(removeSchedItem(section.id)),
        }),
    }
);


export default connect(mapStateToProps, mapDispatchToProps)(SectionList);
