import React, { useState } from "react";
import PropTypes from "prop-types";

const CreateScheduleModalInterior = ({ usedScheduleNames, createSchedule }) => {
    const [inputRef, setInputRef] = useState(null);
    return <div>
        <input type={"text"} ref={ref => setInputRef(ref)}/>
        <div role={"button"} onClick={() => {
            createSchedule(inputRef.value);
        }}>Rename</div>
    </div>;
};

CreateScheduleModalInterior.propTypes = {
    usedScheduleNames: PropTypes.arrayOf(PropTypes.string).isRequired,
    createSchedule: PropTypes.func,
};

export default CreateScheduleModalInterior;
