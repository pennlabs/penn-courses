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
    changed: boolean
) => {
    if (changed) {
        if (mode === "schedule") {
            if (input === "") {
                return { message: "Name cannot be empty", error: true };
            }
            if (input.match(scheduleIllegalCharacters)) {
                return {
                    message:
                        "Name can only contain spaces, underscores, dashes, letters, and numbers",
                    error: true,
                };
            }
            if (input.length > 25) {
                return { message: "Name is too long", error: true };
            }
            if (existingData.indexOf(input) !== -1) {
                return {
                    message: "Schedule with this name already exists",
                    error: true,
                };
            }
        } else if (mode === "friend") {
            if (changed && input === "") {
                return {
                    message: "Friend's pennkey cannot be empty",
                    error: true,
                };
            }
            if (input.match(friendIllegalCharacters)) {
                return {
                    message:
                        "Friend's pennkey can only contain letters and numbers",
                    error: true,
                };
            }
            if (existingData.indexOf(input) !== -1) {
                return {
                    message: "Already friends with this user!",
                    error: true,
                };
            }
        }
    }

    return { error: false, message: null };
};
