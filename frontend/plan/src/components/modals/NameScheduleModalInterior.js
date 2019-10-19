import React, { useState } from "react";
import PropTypes from "prop-types";
import { validateScheduleName } from "../schedule/schedule_name_validation";

const NameScheduleModalInterior = ({
    usedScheduleNames, namingFunction, close, buttonName,
}) => {
    const [inputRef, setInputRef] = useState(null);
    const [userInput, setUserInput] = useState("");
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
};

export default NameScheduleModalInterior;
