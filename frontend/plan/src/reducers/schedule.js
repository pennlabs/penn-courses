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
    ATTEMPT_DELETION, ATTEMPT_SCHEDULE_CREATION, UNSUCCESSFUL_SCHEDULE_CREATION, TOGGLE_STAR
} from "../actions";
import { meetingsContainSection } from "../meetUtil";

const DEFAULT_SCHEDULE_NAME = "Schedule";

// returns the default empty schedule
const generateDefaultSchedule = () => (
    {
        meetings: [],
        colorPalette: [],
        LocAdded: false,
        pushedToBackend: false,
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
    schedules: { [DEFAULT_SCHEDULE_NAME]: generateDefaultSchedule() },
    scheduleSelected: DEFAULT_SCHEDULE_NAME,
    cartSections: [],
    cartPushedToBackend: false,
    deletedSchedules: [],
    cartUpdated: false,
};

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
        schedulesFromBackend.forEach(({
            id: scheduleId, name, sections, semester, ...rest
        }) => {
            const cloudUpdated = new Date(rest.updated_at).getTime();
            if (name === "cart") {
                newState.cartId = scheduleId;
                if (!state.cartUpdated || cloudUpdated > state.cartUpdated) {
                    newCart = sections;
                }
            } else if (state.schedules[name]) {
                newScheduleObject[name].id = scheduleId;
                newScheduleObject[name].backendCreationState = false;
                const selectedSched = state.schedules[name];
                if (!selectedSched.updated_at || cloudUpdated > selectedSched.updated_at) {
                    newScheduleObject[name].meetings = sections;
                }
            } else {
                newScheduleObject[name] = {
                    meetings: sections,
                    semester,
                    id: scheduleId,
                    pushedToBackend: true,
                    updated_at: cloudUpdated,
                };
            }
        });
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
 * @returns {{scheduleSelected: (*), deletedSchedules: {}, schedules: *}}
 */
const processScheduleDeletion = (state, scheduleName) => {
    const newSchedules = removeSchedule(scheduleName, state.schedules);
    if (Object.keys(newSchedules).length === 0) {
        newSchedules["Empty Schedule"] = generateDefaultSchedule();
    }
    return {
        ...state,
        deletedSchedules: {
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

export const schedule = (state = initialState, action) => {
    const { cartSections } = state;
    switch (action.type) {
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
                    [action.scheduleName]: generateDefaultSchedule(),
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
                return state;
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
                        attempts: 1,
                    },
                },
            };
        case DELETION_ATTEMPT_SUCCEEDED: {
            // deletion API call was successful
            const newDeletedSchedules = { ...(state.deletedSchedules || []) };
            delete newDeletedSchedules[action.scheduleId];
            return {
                ...state,
                deletedSchedules: newDeletedSchedules,
            };
        }
        case DELETION_ATTEMPT_FAILED: {
            // a call to the deletion API route was completed with a failure
            return {
                ...state,
                deletedSchedules: state.deletedSchedules ? {
                    ...state.deletedSchedules,
                    [action.deletedScheduleId]: {
                        attempts: state.deletedSchedules[action.deletedScheduleId].attempts + 1,
                        deletionQueued: false,
                    },
                } : {
                    [action.deletedScheduleId]: {
                        attempts: 1,
                        deletionQueued: false,
                    },
                },
            };
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

        case TOGGLE_STAR:
            return {
                ...state,
                cartSections: state.cartSections.map((section) => {
                    const modifiedSection = section;
                    if (section.id === action.id) {
                        modifiedSection.starred = !section.starred;
                    }
                    return modifiedSection;
                }),
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
            return {
                ...state,
                cartUpdated: Date.now(),
                cartSections: state.cartSections.filter(({ id }) => id !== action.sectionId),
                cartPushedToBackend: false,
            };
        default:
            return {
                ...state,
            };
    }
};
