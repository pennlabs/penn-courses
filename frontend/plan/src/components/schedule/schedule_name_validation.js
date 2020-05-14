const illegalCharacters = /[^a-zA-Z\d\s-_]/;

/**
 *
 * @param scheduleName The potential new schedule name
 * @param existingScheduleNames
 * @returns {{message: string, error: boolean}}
 */
export const validateScheduleName = (scheduleName, existingScheduleNames) => {
    if (scheduleName === "") {
        return { message: "Name cannot be empty", error: true };
    }
    if (scheduleName.match(illegalCharacters)) {
        return {
            message:
                "Name can only contain spaces, underscores, dashes, letters, and numbers",
            error: true,
        };
    }
    if (scheduleName.length > 25) {
        return { message: "Name is too long", error: true };
    }
    if (existingScheduleNames.indexOf(scheduleName) !== -1) {
        return {
            message: "Schedule with this name already exists",
            error: true,
        };
    }
    return { error: false, message: null };
};
