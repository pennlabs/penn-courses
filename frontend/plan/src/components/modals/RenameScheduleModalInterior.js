import React, { useState } from "react";
import PropTypes from "prop-types";
import { validateScheduleName } from "../schedule/schedule_name_validation";

const RenameScheduleModalInterior = ({ usedScheduleNames, renameSchedule, close }) => {
    const [inputRef, setInputRef] = useState(null);
    const [userInput, setUserInput] = useState("");
    const { error, message: errorMessage } = validateScheduleName(userInput, usedScheduleNames);
    const submit = () => {
        const scheduleName = inputRef.value;
        if (!error) {
            renameSchedule(scheduleName);
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
                className="button is-link"
                role="button"
                type="button"
                onClick={() => {
                    submit();
                }}
            >
            Rename
            </button>
        </div>
    );
};

RenameScheduleModalInterior.propTypes = {
    usedScheduleNames: PropTypes.arrayOf(PropTypes.string).isRequired,
    renameSchedule: PropTypes.func,
    close: PropTypes.func,
};

export default RenameScheduleModalInterior;
