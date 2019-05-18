import React from "react";
import PropTypes from "prop-types";
import SectionDisplay from "./SectionDisplay";
import { sectionInfoA } from "../../sections_data";

export default function SectionList(props) {
    const {
        updateSectionInfo,
        sections,
        scheduleContains,
        overlaps,
        addSchedItem,
        removeSchedItem,
        listRef,
    } = props;
    const sectionsArr = [];
    for (let i = 0; i < sections.length; i += 1) {
        const section = sections[i];
        sectionsArr.push(
            <SectionDisplay
                inSchedule={scheduleContains(section.idDashed)}
                overlap={overlaps(section)}
                addSchedItem={addSchedItem}
                removeSchedItem={removeSchedItem}
                section={section}
                key={i}
                openSection={() => {
                    updateSectionInfo(sectionInfoA);
                }}
            />
        );
        /* if (($scope.showAct === section.actType || $scope.showAct === 'noFilter') &&
            (section.isOpen || $scope.showClosed) &&
            ($scope.currentCourse || $scope.starSections.indexOf(section.idDashed) > -1)) {
            sectionsArr.push(<SectionDisplay section={section} key={i}/>);
        } */
    }

    return (
        <div id="SectionList" ref={listRef}>
            <ul>
                {sectionsArr}
            </ul>
        </div>
    );
}

SectionList.propTypes = {
    updateSectionInfo: PropTypes.func.isRequired,
    sections: PropTypes.arrayOf(PropTypes.object),
    scheduleContains: PropTypes.func.isRequired,
    overlaps: PropTypes.func.isRequired,
    addSchedItem: PropTypes.func,
    removeSchedItem: PropTypes.func,
    listRef: PropTypes.shape({
        current: PropTypes.object,
    }),
};

SectionList.defaultProps = {
    sections: [],
};
