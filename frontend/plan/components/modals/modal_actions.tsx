const scheduleIllegalCharacters = /[^a-zA-Z\d\s-_]/;
const friendIllegalCharacters = /[^a-zA-Z0-9]/;

/**
 *
 * @param input The potential new schedule name
 * @param existingData
 * @returns {{message: string, error: boolean}}
 */
export const validateInput = (
    input: string,
    existingData: string[],
    mode: string,
    changed: boolean,
    callback: React.Dispatch<
        React.SetStateAction<{
            message: string;
            error: boolean;
        }>
    >
) => {
    if (changed) {
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
    }
};