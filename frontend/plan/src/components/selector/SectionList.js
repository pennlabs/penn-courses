import React from "react";
import PropTypes from "prop-types";

export default function SectionList({ sections }) {
    return (
        <div className="scroll-container">
            <div className="columns segment">
                <div className="column header">SECT</div>
                <div className="column header">INSTR</div>
                <div className="column header">TYPE</div>
                <div className="column header">TIME</div>
            </div>
            <div className="scrollable course-list">
                { /* Sections go in here */ }
            </div>
        </div>
    );
}

SectionList.propTypes = {
    sections: PropTypes.arrayOf(PropTypes.object).isRequired,
};
