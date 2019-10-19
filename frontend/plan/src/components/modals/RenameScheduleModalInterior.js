import React from "react";
import PropTypes from "prop-types";

const RenameScheduleModalInterior = ({usedScheduleNames, renameSchedule}) => {
    return null;
};

RenameScheduleModalInterior.propTypes = {
    usedScheduleNames: PropTypes.arrayOf(PropTypes.string).isRequired,
    renameSchedule: PropTypes.func,
};

export default RenameScheduleModalInterior;
