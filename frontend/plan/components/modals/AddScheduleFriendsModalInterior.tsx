import React, { useState, useEffect } from "react";
import {
    handleFriendshipRequestResponse,
    validateInput,
} from "./modal_actions";
import { User } from "../../types";

interface AddScheduleFriendsModalInteriorProps {
    user: User;
    existingData: string[] | User[];
    namingFunction: (_: string) => void;
    sendFriendRequest: (
        user: User,
        pennkey: string,
        activeFriendName: string,
        callback: (res: any) => void
    ) => void;
    close: () => void;
    buttonName: string;
    defaultValue: string;
    placeholder: string;
    overwriteDefault: boolean;
    mode: string;
    activeFriendName: string;
}

const AddScheduleFriendsModalInterior = ({
    user,
    existingData,
    namingFunction,
    sendFriendRequest,
    close,
    buttonName,
    defaultValue,
    placeholder,
    overwriteDefault = false,
    mode,
    activeFriendName,
}: AddScheduleFriendsModalInteriorProps) => {
    const [inputRef, setInputRef] = useState<HTMLInputElement | null>(null);
    const [userInput, setUserInput] = useState(defaultValue);
    const [changed, setChanged] = useState(false);
    const [errorObj, setErrorObj] = useState({ message: "", error: false });

    useEffect(() => {
        console.log(existingData)
        validateInput(
            user,
            userInput,
            existingData as string[],
            mode,
            changed,
            setErrorObj
        );
    }, [userInput]);

    const submit = () => {
        if (!inputRef) {
            return;
        }

        if (!errorObj.error) {
            if (mode == "friend") {
                sendFriendRequest(
                    user,
                    inputRef.value,
                    activeFriendName,
                    (res: any) => {
                        const responseResult = handleFriendshipRequestResponse(
                            res,
                            inputRef.value,
                            existingData as User[]
                        );
                        if (responseResult.error) {
                            setErrorObj(responseResult);
                        } else {
                            close();
                        }
                    }
                );
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
