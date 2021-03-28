import React, { useState, useEffect } from "react";
import { validateScheduleName } from "../schedule/schedule_name_validation";

interface NameScheduleModalInteriorProps {
    usedScheduleNames: string[];
    namingFunction: (_: string) => void;
    close: () => void;
    buttonName: string;
    defaultValue: string;
    overwriteDefault: boolean;
}

const NameScheduleModalInterior = ({
    usedScheduleNames,
    namingFunction,
    close,
    buttonName,
    defaultValue,
    overwriteDefault = false,
}: NameScheduleModalInteriorProps) => {
    const [inputRef, setInputRef] = useState<HTMLInputElement | null>(null);
    const [userInput, setUserInput] = useState(defaultValue);
    const { error, message: errorMessage } = validateScheduleName(
        userInput,
        usedScheduleNames
    );
    useEffect(() => {
        const listener = (event: MouseEvent) => {
            if (
                !userInput &&
                inputRef &&
                !inputRef.contains(event.target as Node)
            ) {
                setUserInput(defaultValue);
            }
        };
        document.addEventListener("click", listener);
        return () => {
            document.removeEventListener("click", listener);
        };
    });
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
                onChange={() => setUserInput(inputRef?.value || "")}
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
