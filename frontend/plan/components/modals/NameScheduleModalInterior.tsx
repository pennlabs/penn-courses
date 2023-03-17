import React, { useState, useEffect } from "react";
import { validateInput } from "./input_validation";

interface NameScheduleModalInteriorProps {
    existingData: string[];
    namingFunction: (_: string) => void;
    close: () => void;
    buttonName: string;
    defaultValue: string;
    overwriteDefault: boolean;
    mode: string;
}

const NameScheduleModalInterior = ({
    existingData,
    namingFunction,
    close,
    buttonName,
    defaultValue,
    overwriteDefault = false,
    mode,
}: NameScheduleModalInteriorProps) => {
    const [inputRef, setInputRef] = useState<HTMLInputElement | null>(null);
    const [userInput, setUserInput] = useState("");
    const [changed, setChanged] = useState(false);
    const { error, message: errorMessage } = validateInput(
        userInput,
        existingData,
        mode,
        changed
    );
    
    const submit = () => {
        if (!inputRef) {
            return;
        }
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
                ref={(ref) => setInputRef(ref)}
                style={{ backgroundColor: error ? "#f9dcda" : "#f1f1f1" }}
                onChange={() => {
                    setUserInput(inputRef?.value || "");
                    setChanged(true)
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
            <p className="error_message">{errorMessage}</p>
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
