import React, { useState, useEffect } from "react";
import {
    handleFriendshipRequestResponse,
    validateInput,
} from "./modal_actions";
import { User } from "../../types";
import { showToast } from "../../pages";

interface AddScheduleFriendsModalInteriorProps {
    user: User;
    existingData: string[] | User[];
    namingFunction: (_: string) => void;
    sendFriendRequest: (
        user: User,
        pennkey: string,
        callback: (res: any) => void
    ) => void;
    close: () => void;
    buttonName: string;
    defaultValue: string;
    placeholder: string;
    overwriteDefault: boolean;
    requestType: string;
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
    requestType,
}: AddScheduleFriendsModalInteriorProps) => {
    const [inputRef, setInputRef] = useState<HTMLInputElement | null>(null);
    const [userInput, setUserInput] = useState(defaultValue);
    const [errorObj, setErrorObj] = useState({ message: "", error: false });

    useEffect(() => {
        validateInput(
            user,
            userInput,
            existingData as string[],
            requestType,
            setErrorObj
        );
    }, [userInput]);

    const submit = () => {
        if (!inputRef) {
            return;
        }

        if (!errorObj.error) {
            if (requestType == "friend") {
                sendFriendRequest(
                    user,
                    inputRef.value,
                    (res: any) => {
                        const responseResult = handleFriendshipRequestResponse(
                            res,
                            inputRef.value,
                            existingData as User[]
                        );
                        if (responseResult.error) {
                            setErrorObj(responseResult);
                        } else {
                            showToast(
                                "Success! Your friend request was sent.",
                                false
                            );
                            close();
                        }
                    }
                );
            } else if (requestType == "schedule") {
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
