import React, { useState, useEffect } from "react";
import { validateInput } from "./input_validation";
import { sendFriendRequest } from "../../actions/index.js";

interface NameScheduleModalInteriorProps {
    existingData: string[];
    namingFunction: (_: string) => void;
    requestFunction: (_: string) => {message: string, error: boolean}
    close: () => void;
    buttonName: string;
    defaultValue: string;
    overwriteDefault: boolean;
    mode: string;
}

const NameScheduleModalInterior = ({
    existingData,
    namingFunction,
    requestFunction,
    close,
    buttonName,
    defaultValue,
    overwriteDefault = false,
    mode,
}: NameScheduleModalInteriorProps) => {
    const [inputRef, setInputRef] = useState<HTMLInputElement | null>(null);
    const [userInput, setUserInput] = useState("");
    const [changed, setChanged] = useState(false);
    const [errorObj, setErrorObj] = useState(
        validateInput(userInput, existingData, mode, changed)
    );

    const submit = () => {
        if (!inputRef) {
            return;
        }

        if (!errorObj.error) {
            if (mode == "friend") {
                const requestResult = requestFunction(inputRef.value)
                if (requestResult.error) {
                    console.log(requestResult);
                    setErrorObj(requestResult);
                } else {
                    close();
                }
            } else if (mode == "schedule") {
                namingFunction(inputRef.value);
                close();
            }
            
        }
    };
    return (
        <div>
            <input
                value={userInput}
                type="text"
                ref={(ref) => setInputRef(ref)}
                style={{ backgroundColor: errorObj.error ? "#f9dcda" : "#f1f1f1" }}
                onChange={() => {
                    setUserInput(inputRef?.value || "");
                    setChanged(true);
                }}
                onClick={() => {
                    if (overwriteDefault && userInput === defaultValue) {
                        setUserInput("");
                    }
                }}
                onKeyUp={(e) => {
                    if (e.key === "Enter") {
                        submit();
                    }
                }}
                placeholder={defaultValue}
            />
            <p className="error_message">{errorObj.message}</p>
            <button
                className="button is-link"
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

export default NameScheduleModalInterior;
