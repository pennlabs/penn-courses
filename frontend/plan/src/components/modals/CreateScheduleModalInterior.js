import React, { useState } from "react";
import PropTypes from "prop-types";
import { validateScheduleName } from "../schedule/schedule_name_validation";

const CreateScheduleModalInterior = ({ usedScheduleNames, createSchedule, close }) => {
    const [inputRef, setInputRef] = useState(null);
    const [userInput, setUserInput] = useState("");
    const { error, message: errorMessage } = validateScheduleName(userInput, usedScheduleNames);
    const submit = () => {
        const scheduleName = inputRef.value;
        if (!error) {
            createSchedule(scheduleName);
            close();
        }
    };
    return (
        <div>
            <input
                type="text"
                ref={ref => setInputRef(ref)}
                onChange={() => setUserInput(inputRef.value)}
                onKeyUp={(e) => {
                    if (e.keyCode === 13) {
                        submit();
                    }
                }}
            />
            <p className="error_message">{errorMessage}</p>
            <button
                type="button"
                className="button is-link"
                role="button"
                onClick={() => {
                    submit();
                }}
            >
Create
            </button>
        </div>
    );
};

CreateScheduleModalInterior.propTypes = {
    usedScheduleNames: PropTypes.arrayOf(PropTypes.string).isRequired,
    createSchedule: PropTypes.func,
    close: PropTypes.func,
};

export default CreateScheduleModalInterior;
