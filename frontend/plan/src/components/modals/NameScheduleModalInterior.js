import React, { useState } from "react";
import PropTypes from "prop-types";
import { validateScheduleName } from "../schedule/schedule_name_validation";

const NameScheduleModalInterior = ({
    usedScheduleNames, namingFunction, close, buttonName, defaultValue, overwriteDefault = false,
}) => {
    const [inputRef, setInputRef] = useState(null);
    const [userInput, setUserInput] = useState(defaultValue);
    const { error, message: errorMessage } = validateScheduleName(userInput, usedScheduleNames);
    const submit = () => {
        const scheduleName = inputRef.value;
        if (!error) {
            namingFunction(scheduleName);
            close();
        }
    };
    return (
        <div>
            <input
                value={userInput}
                type="text"
                ref={ref => setInputRef(ref)}
                style={{ backgroundColor: error ? "#f9dcda" : "white" }}
                onChange={() => setUserInput(inputRef.value)}
                onClick={() => {
                    if (overwriteDefault && userInput === defaultValue) {
                        setUserInput("");
                    }
                }}
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
                {buttonName}
            </button>
        </div>
    );
};

NameScheduleModalInterior.propTypes = {
    usedScheduleNames: PropTypes.arrayOf(PropTypes.string).isRequired,
    namingFunction: PropTypes.func,
    close: PropTypes.func,
    buttonName: PropTypes.string,
    defaultValue: PropTypes.string,
    overwriteDefault: PropTypes.bool,
};

export default NameScheduleModalInterior;
