import React from "react";
import PropTypes from "prop-types";
import { Dropdown } from "../dropdown";

export default function SchedulesDropdown({ scheduleNames, changeSchedule, scheduleSelected }) {
    return (
        <Dropdown
            contents={scheduleNames.map(name => [name, () => changeSchedule(name)])}
            updateLabel={true}
            defActive={scheduleNames.indexOf(scheduleSelected)}
            defText={scheduleSelected}
        />
    );
}

SchedulesDropdown.propTypes = {
    scheduleNames: PropTypes.arrayOf(PropTypes.string).isRequired,
    changeSchedule: PropTypes.func.isRequired,
    scheduleSelected: PropTypes.string.isRequired,
};
