import React, { useState, useEffect } from "react";
import { validateInput } from "./modal_actions";
import { sendFriendRequest } from "../../actions/friendshipUtil";

interface AddScheduleFriendsModalInteriorProps {
    existingData: string[];
    namingFunction: (_: string) => void;
    close: () => void;
    buttonName: string;
    defaultValue: string;
    placeholder: string;
    overwriteDefault: boolean;
    mode: string;
}

const AddScheduleFriendsModalInterior = ({
    existingData,
    namingFunction,
    close,
    buttonName,
    defaultValue,
    placeholder,
    overwriteDefault = false,
    mode,
}: AddScheduleFriendsModalInteriorProps) => {
    const [inputRef, setInputRef] = useState<HTMLInputElement | null>(null);
    const [userInput, setUserInput] = useState(defaultValue);
    const [changed, setChanged] = useState(false);
    const [errorObj, setErrorObj] = useState({ message: "", error: false });

    useEffect(() => {
        validateInput(userInput, existingData, mode, changed, setErrorObj);
    }, [userInput]);

    const submit = () => {
        if (!inputRef) {
            return;
        }

        if (!errorObj.error) {
            if (mode == "friend") {
                sendFriendRequest(inputRef.value).then((res) => {
                    if (res.error) {
                        setErrorObj(res);
                    } else {
                        close();
                    }
                });
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
                style={{
                    backgroundColor: errorObj.error ? "#f9dcda" : "#f1f1f1",
                }}
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
                placeholder={placeholder}
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

export default AddScheduleFriendsModalInterior;
