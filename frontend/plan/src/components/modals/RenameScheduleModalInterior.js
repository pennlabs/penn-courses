import React, { useState } from "react";
import PropTypes from "prop-types";

const RenameScheduleModalInterior = ({ usedScheduleNames, renameSchedule }) => {
    const [inputRef, setInputRef] = useState(null);
    return <div>
        <input type={"text"} ref={ref => setInputRef(ref)}/>
        <div role={"button"} onClick={() => {
            renameSchedule(inputRef.value);
        }}>Rename</div>
    </div>;
};

RenameScheduleModalInterior.propTypes = {
    usedScheduleNames: PropTypes.arrayOf(PropTypes.string).isRequired,
    renameSchedule: PropTypes.func,
};

export default RenameScheduleModalInterior;
