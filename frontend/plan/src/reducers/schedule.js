import {
    CHANGE_SCHEDULE,
    CREATE_SCHEDULE,
    DELETE_SCHEDULE,
    REMOVE_SCHED_ITEM,
    RENAME_SCHEDULE,
    DUPLICATE_SCHEDULE,
    CLEAR_SCHEDULE,
    TOGGLE_CHECK,
    ADD_CART_ITEM,
    REMOVE_CART_ITEM,
    UPDATE_SCHEDULES,
    CREATION_SUCCESSFUL,
    MARK_CART_SYNCED,
    MARK_SCHEDULE_SYNCED,
    DELETION_ATTEMPT_FAILED,
    DELETION_ATTEMPT_SUCCEEDED,
    ATTEMPT_DELETION,
    ATTEMPT_SCHEDULE_CREATION,
    UNSUCCESSFUL_SCHEDULE_CREATION,
    ENFORCE_SEMESTER,
    CLEAR_ALL_SCHEDULE_DATA
} from "../actions";
import { meetingsContainSection } from "../meetUtil";
import {
    MAX_CREATION_ATTEMPTS,
    MAX_DELETION_ATTEMPTS,
    MIN_TIME_DIFFERENCE
} from "../sync_constants";

const DEFAULT_SCHEDULE_NAME = "Schedule";

// returns the default empty schedule
const generateEmptySchedule = (isDefault = true) => (
    {
        meetings: [],
        colorPalette: [],
        LocAdded: false,
        pushedToBackend: isDefault,
        backendCreationState: {
            creationQueued: false,
            creationAttempts: 0,
        },
        updated_at: 1,
    }
);

// the state contains the following two pieces of data:
//  1. An object associating each schedule name with the schedule objecct
//  2. The name of the currently selected schedule
const initialState = {
    schedules: { [DEFAULT_SCHEDULE_NAME]: generateEmptySchedule() },
    scheduleSelected: DEFAULT_SCHEDULE_NAME,
    cartSections: [],
    cartPushedToBackend: true,
    deletedSchedules: [],
    cartUpdated: 1,
};

/**
 * Resets the cart ID stored in state and returns the new state
 * @param state
 */
const resetCartId = (state) => {
    const newState = { ...state };
    delete newState.cartId;
    return newState;
};

/**
 * Resets the cart to be empty, and assumes that it has not been pushed
 * @param state The old state
 * @return {{cartSections: [], cartPushedToBackend: boolean, cartUpdated: boolean}} New state
 */
const resetCart = state => (resetCartId({
    ...state,
    cartSections: [],
    cartPushedToBackend: true,
    cartUpdated: false,
}));

/**
 * A helper method for removing a schedule from a schedules object
 * @param scheduleKey The name of the schedule
 * @param initialSchedule The initial schedules object
 */
const removeSchedule = (scheduleKey, initialSchedule) => {
    const newSchedules = {};
    Object.keys(initialSchedule)
        .filter(schedName => schedName !== scheduleKey)
        .forEach((schedName) => {
            newSchedules[schedName] = initialSchedule[schedName];
        });
    return newSchedules;
};

/**
 * Returns a new schedule where the section is present if it was not previously, and vice-versa
 * @param meetings
 * @param section
 */
const toggleSection = (meetings, section) => {
    if (meetingsContainSection(meetings, section)) {
        return meetings.filter(m => m.id !== section.id);
    }
    return [...meetings, section];
};

/**
 * Returns a copy of th given schedule without its id
 * @param schedule
 */
const withoutId = (schedule) => {
    const newSchedule = { ...schedule };
    delete newSchedule.id;
    return newSchedule;
};

/**
 * Returns the next available schedule name that is similar to the given schedule name
 * Used for duplication
 * @param scheduleName: current schedule name
 * @param used: used schedule names stored in an object
 */
const nextAvailable = (scheduleName, used) => {
    let newScheduleName = scheduleName;
    // compute the current number at the end of the string (if it exists)
    let endNum = 0;
    let numDigits = 0;
    let selectionIndex = newScheduleName.length - 1;
    while (selectionIndex >= 0 && newScheduleName.charAt(selectionIndex) >= "0"
    && newScheduleName.charAt(selectionIndex) <= 9) {
        endNum += Math.pow(10, numDigits) * parseInt(newScheduleName.charAt(selectionIndex), 10);
        numDigits += 1;
        selectionIndex -= 1;
    }
    // prevent double arithmetic issues
    endNum = Math.round(endNum);
    // search for the next available number
    const baseName = newScheduleName.substring(0, newScheduleName.length - numDigits);
    while (used[newScheduleName]) {
        endNum += 1;
        newScheduleName = baseName + endNum;
    }
    return newScheduleName;
};

/**
 * Returns the new state following the creation of a schedule
 * @param state The redux state
 * @param scheduleName The name of the schedule
 * @returns {{schedules}}
 */
const processScheduleCreation = (state, scheduleName) => {
    const schedule = state.schedules[scheduleName];
    if (schedule.backendCreationState.creationAttempts >= MAX_CREATION_ATTEMPTS) {
        return processScheduleDeletion(state, scheduleName, true);
    }
    return {
        ...state,
        schedules: {
            ...state.schedules,
            [scheduleName]: {
                ...schedule,
                backendCreationState: {
                    creationQueued: true,
                    creationAttempts: schedule.backendCreationState.creationAttempts + 1,
                },
            },
        },
    };
};

/**
 * Handle a successful deletion on the backend
 * @param state The previous state
 * @param deletedScheduleId The id of the deleted schedule
 * @return {{deletedSchedules: {}}} The new state
 */
const registerSuccessfulDeletion = (state, deletedScheduleId) => {
    const newDeletedSchedules = { ...(state.deletedSchedules || []) };
    delete newDeletedSchedules[deletedScheduleId];
    return {
        ...state,
        deletedSchedules: newDeletedSchedules,
    };
};

/**
 * Handle a failed deletion on the backend
 * @param state The previous state
 * @param deletedScheduleId The id of the deleted schedule
 * @return {{deletedSchedules: {}}} The new state
 */
const registerFailedDeletion = (state, deletedScheduleId) => {
    const oldDeletedSchedules = state.deletedSchedules || {};
    const oldDeletionState = oldDeletedSchedules[deletedScheduleId] || { attempts: 0 };
    const { attempts: oldAttempts } = oldDeletionState;
    if (oldAttempts >= MAX_DELETION_ATTEMPTS) {
        // assume this was a successful deletion and end attempts at deleting the schedule
        return registerSuccessfulDeletion(state, deletedScheduleId);
    }
    return {
        ...state,
        deletedSchedules: {
            ...oldDeletedSchedules,
            [deletedScheduleId]: {
                ...oldDeletionState,
                attempts: oldAttempts + 1,
                deletionQueued: false,
            },
        },
    };
};

/**
 * Takes in schedules from the backend; incorporates them into state; and returns the new state
 * @param state The redux state
 * @param schedulesFromBackend The schedules object sent by the backend
 * @returns {{cartSections: *, cartPushedToBackend: boolean, schedules: *}}
 */
const processScheduleUpdate = (state, schedulesFromBackend) => {
    const newScheduleObject = { ...(state.schedules || {}) };
    let newCart = [...(state.cartSections || [])];
    const newState = { ...state };
    if (schedulesFromBackend) {
        for (const {
            id: scheduleId, name, sections, semester, ...rest
        } of schedulesFromBackend) {
            const cloudUpdated = new Date(rest.updated_at).getTime();
            if (name === "cart") {
                const { cartUpdated } = state;
                const cartPushed = state.cartPushedToBackend;
                // If changes to the cart are still syncing, ignore the requested update
                if (!cartPushed && (cloudUpdated - cartUpdated) < MIN_TIME_DIFFERENCE) {
                    return state;
                }
                newState.cartId = scheduleId;
                if (!cartUpdated || cloudUpdated > cartUpdated) {
                    newCart = sections;
                }
            } else if (state.schedules[name]) {
                const selectedSched = state.schedules[name];
                const updated = selectedSched.updated_at;
                // If changes to the schedule are still syncing, ignore the requested update
                const pushed = selectedSched.pushedToBackend;
                if (!pushed && updated && (updated - cloudUpdated) < MIN_TIME_DIFFERENCE) {
                    return state;
                }
                newScheduleObject[name].id = scheduleId;
                newScheduleObject[name].backendCreationState = false;
                if (!updated || cloudUpdated > updated) {
                    newScheduleObject[name].meetings = sections;
                }
            } else if (!state.deletedSchedules[scheduleId]) {
                newScheduleObject[name] = {
                    meetings: sections,
                    semester,
                    id: scheduleId,
                    pushedToBackend: true,
                    updated_at: cloudUpdated,
                };
            }
        }
    }
    return {
        ...newState,
        schedules: newScheduleObject,
        cartSections: newCart,
        cartPushedToBackend: true,
    };
};

/**
 * Performs a deletion and returns the resulting state
 * @param state The redux state
 * @param scheduleName The name of the schedule to delete
 * @param localOnly Whether to only make this change on the frontend
 * Returns the new state
 */
const processScheduleDeletion = (state, scheduleName, localOnly = false) => {
    const newSchedules = removeSchedule(scheduleName, state.schedules);
    if (scheduleName === "cart") {
        return resetCart(state);
    }
    if (Object.keys(newSchedules).length === 0) {
        newSchedules[DEFAULT_SCHEDULE_NAME] = generateEmptySchedule();
    }
    return {
        ...state,
        deletedSchedules: localOnly ? state.deletedSchedules
            : {
                ...(state.deletedSchedules || {}),
                [state.schedules[scheduleName].id]: {
                    deletionQueued: false,
                    attempts: 0,
                },
            },
        schedules: newSchedules,
        scheduleSelected: scheduleName === state.scheduleSelected
            ? Object.keys(newSchedules)[0] : state.scheduleSelected,
    };
};

/**
 * Returns whether the given array of meetings/sections contains
 * courses not from the current semester.
 * @param meetings
 * @param currentSemester
 */
const containsOldSemester = (meetings, currentSemester) => meetings
    .reduce((acc, { semester }) => acc || (semester && (semester !== currentSemester)), false);

/**
 * Handles removal of an item from the cart
 * @param sectionId
 * @param state
 * @return {{cartSections: *, cartPushedToBackend: boolean, cartUpdated: *}}
 */
const handleRemoveCartItem = (sectionId, state) => ({
    ...state,
    cartUpdated: Date.now(),
    cartSections: state.cartSections.filter(({ id }) => id !== sectionId),
    cartPushedToBackend: false,
});

/**
 * Resets the cart and filters out old cart sections
 * if it contains classes from the previous semester
 * @param currentSemester
 * @param state
 * @return {{cartSections: *[], cartPushedToBackend: boolean, cartUpdated: boolean}|*}
 */
const enforceCartSemester = (currentSemester, state) => {
    const hasOldCartSections = containsOldSemester(state.cartSections, currentSemester);
    if (hasOldCartSections) {
        return state.cartSections
            .filter(({ semester }) => semester && (semester !== currentSemester))
            .reduce((acc, { id }) => handleRemoveCartItem(id, acc), resetCartId(state));
    }
    return state;
};


export const schedule = (state = initialState, action) => {
    const { cartSections } = state;
    switch (action.type) {
        case CLEAR_ALL_SCHEDULE_DATA:
            return { ...initialState };
        // restrict schedules to ones from the current semester
        case ENFORCE_SEMESTER:
            return Object.entries(state.schedules)
                .filter(([_, { meetings }]) => containsOldSemester(meetings, action.semester))
                .reduce((acc, [name, _]) => processScheduleDeletion(acc, name, true),
                    enforceCartSemester(action.semester, state));
        case MARK_SCHEDULE_SYNCED:
            return {
                ...state,
                schedules: {
                    ...state.schedules,
                    [action.scheduleName]: {
                        ...state.schedules[action.scheduleName],
                        pushedToBackend: true,
                        backendCreationState: false,
                    },
                },
            };
        case MARK_CART_SYNCED:
            return {
                ...state,
                cartPushedToBackend: true,
            };
        case CREATION_SUCCESSFUL:
            if (action.name === "cart") {
                return {
                    ...state,
                    cartId: action.id,
                    cartPushedToBackend: true,
                };
            }
            return {
                ...state,
                schedules: {
                    ...state.schedules,
                    [action.name]: {
                        ...state.schedules[action.name],
                        id: action.id,
                        pushedToBackend: true,
                        backendCreationState: false,
                    },
                },
            };

        case UPDATE_SCHEDULES:
            return processScheduleUpdate(state, action.schedulesFromBackend);
        case CLEAR_SCHEDULE:
            return {
                ...state,
                schedules: {
                    ...state.schedules,
                    [state.scheduleSelected]: {
                        ...[state.scheduleSelected],
                        meetings: [],
                        updated_at: Date.now(),
                        pushedToBackend: false,
                    },
                },
            };
        case RENAME_SCHEDULE:
            return {
                ...state,
                schedules: {
                    ...removeSchedule(action.oldName, state.schedules),
                    [action.newName]: {
                        ...state.schedules[action.oldName],
                        updated_at: Date.now(),
                        pushedToBackend: false,
                    },
                },
                scheduleSelected: state.scheduleSelected === action.oldName
                    ? action.newName : state.scheduleSelected,
            };
        case DUPLICATE_SCHEDULE:
            return {
                ...state,
                schedules: {
                    ...state.schedules,
                    [nextAvailable(action.scheduleName, state.schedules)]:
                        {
                            ...withoutId(state.schedules[action.scheduleName]),
                            pushedToBackend: false,
                            updated_at: Date.now(),
                            backendCreationState: {
                                creationQueued: false,
                                creationAttempts: 0,
                            },
                        },
                },
            };
        case CREATE_SCHEDULE:
            return {
                ...state,
                schedules: {
                    ...state.schedules,
                    [action.scheduleName]: generateEmptySchedule(false),
                },
                scheduleSelected: action.scheduleName,
            };
        case ATTEMPT_SCHEDULE_CREATION:
            if (action.scheduleName === "cart") {
                return state;
            }
            return processScheduleCreation(state, action.scheduleName);
        case UNSUCCESSFUL_SCHEDULE_CREATION:
            if (action.scheduleName === "cart") {
                return resetCart(state);
            }
            return {
                ...state,
                schedules: {
                    ...state.schedules,
                    [action.scheduleName]: {
                        ...state.schedules[action.scheduleName],
                        backendCreationState: {
                            ...state.schedules[action.scheduleName].backendCreationState,
                            creationQueued: false,
                        },
                    },
                },
            };
        case DELETE_SCHEDULE:
            return processScheduleDeletion(state, action.scheduleName);
        case ATTEMPT_DELETION:
            // attempt deletion API call
            return {
                ...state,
                deletedSchedules: {
                    ...state.deletedSchedules,
                    [action.deletedScheduleId]: {
                        deletionQueued: true,
                        attempts: (state.deletedSchedules[action.deletedScheduleId]
                            && state.deletedSchedules[action.deletedScheduleId].attempts) + 1,
                    },
                },
            };
        case DELETION_ATTEMPT_SUCCEEDED: {
            // deletion API call was successful
            return registerSuccessfulDeletion(state, action.deletedScheduleId);
        }
        case DELETION_ATTEMPT_FAILED: {
            // a call to the deletion API route was completed with a failure
            return registerFailedDeletion(state, action.deletedScheduleId);
        }
        case CHANGE_SCHEDULE:
            return {
                ...state,
                scheduleSelected: action.scheduleId,
            };
        case TOGGLE_CHECK:
            return {
                ...state,
                schedules: {
                    ...state.schedules,
                    [state.scheduleSelected]: {
                        ...state.schedules[state.scheduleSelected],
                        updated_at: Date.now(),
                        meetings: toggleSection(state.schedules[state.scheduleSelected].meetings,
                            action.course),
                        pushedToBackend: false,
                    },
                },
            };
        case REMOVE_SCHED_ITEM:
            return {
                ...state,
                schedules: {
                    ...state.schedules,
                    [state.scheduleSelected]: {
                        ...state.schedules[state.scheduleSelected],
                        updated_at: Date.now(),
                        pushedToBackend: false,
                        meetings: state.schedules[state.scheduleSelected].meetings
                            .filter(m => m.id !== action.id),
                    },
                },
            };
        case ADD_CART_ITEM:
            return {
                ...state,
                cartUpdated: Date.now(),
                cartSections: [...cartSections, action.section],
                lastAdded: action.section,
                cartPushedToBackend: false,
            };
        case REMOVE_CART_ITEM:
            return handleRemoveCartItem(action.sectionId, state);
        default:
            return {
                ...state,
            };
    }
};
