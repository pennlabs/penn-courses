const illegalCharacters = /[^a-zA-Z\d\s-_]/;

export const validateScheduleName = (scheduleName, existingScheduleNames) => {
    if (scheduleName === "") {
        return "Name cannot be empty";
    }
    if (scheduleName.match(illegalCharacters)) {
        return "Name can only contain spaces, underscores, dashes, letters, and numbers";
    }
    if (scheduleName.length > 25) {
        return "Name is too long";
    }
    if (existingScheduleNames.indexOf(scheduleName) !== -1) {
        return "Schedule with this name already exists";
    }
    return "";
};
