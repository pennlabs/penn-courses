import { User } from "../../types";

const scheduleIllegalCharacters = /[^a-zA-Z\d\s-_]/;
const friendIllegalCharacters = /[^a-zA-Z0-9]/;

/**
 *
 * @param input The potential new schedule name
 * @param existingData
 * @returns {{message: string, error: boolean}}
 */
export const validateInput = (
    user: User,
    input: string,
    existingData: string[],
    mode: string,
    callback: React.Dispatch<
        React.SetStateAction<{
            message: string;
            error: boolean;
        }>
    >
) => {
    if (mode === "schedule") {
        if (input === "") {
            callback({ message: "Name cannot be empty", error: true });
        } else if (input.match(scheduleIllegalCharacters)) {
            callback({
                message:
                    "Name can only contain spaces, underscores, dashes, letters, and numbers",
                error: true,
            });
        } else if (input.length > 25) {
            callback({ message: "Name is too long", error: true });
        } else if (existingData.indexOf(input) !== -1) {
            callback({
                message: "Schedule with this name already exists",
                error: true,
            });
        } else if (input === "cart") {
            callback({
                message: "'cart' is not a valid schedule name",
                error: true,
            });
        } else if (input === "Path Registration") {
            callback({
                message: "'Path Registration' is not a valid schedule name",
                error: true,
            });
        } else {
            callback({
                message: "",
                error: false,
            });
        }
    } else if (mode === "friend") {
        if (input === "") {
            callback({
                message: "Friend's pennkey cannot be empty",
                error: true,
            });
        } else if (input.match(friendIllegalCharacters)) {
            callback({
                message:
                    "Friend's pennkey can only contain letters and numbers",
                error: true,
            });
        } else if (input === user.username) {
            callback({
                message: "Cannot request friendship with yourself",
                error: true,
            });
        } else {
            callback({
                message: "",
                error: false,
            });
        }
    } else {
        callback({
            message: "",
            error: false,
        });
    }
};

export const handleFriendshipRequestResponse = (
    res: any,
    requestedFriend: string,
    existingData: User[]
) => {
    if (res.status == 200) {
        return {
            message: "",
            error: false,
        };
    }
    if (res.status == 201) {
        return {
            message: "",
            error: false,
        };
    }
    if (res.status == 404) {
        return {
            message: "User not found.",
            error: true,
        };
    }
    if (res.status == 409) {
        if (
            existingData.find(
                (friend) => friend.username === requestedFriend
            )
        ) {
            return {
                message: "Already friends with this user.",
                error: true,
            };
        } else {
            return {
                message: "Friendship request still pending.",
                error: true,
            };
        }
    }
    return { message: "", error: false };
};
