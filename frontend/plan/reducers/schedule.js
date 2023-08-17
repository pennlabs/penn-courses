import {
    CLEAR_ALL_SCHEDULE_DATA,
    SET_STATE_READ_ONLY,
    SET_PRIMARY_SCHEDULE_ID_ON_FRONTEND,
    CHANGE_SCHEDULE,
    RENAME_SCHEDULE,
    CLEAR_SCHEDULE,
    DOWNLOAD_SCHEDULE,
    MARK_CART_SYNCED,
    MARK_SCHEDULE_SYNCED,
    UPDATE_SCHEDULES_ON_FRONTEND,
    CREATE_SCHEDULE_ON_FRONTEND,
    DELETE_SCHEDULE_ON_FRONTEND,
    DELETION_ATTEMPTED,
    CREATE_CART_ON_FRONTEND,
    TOGGLE_CHECK,
    REMOVE_SCHED_ITEM,
    ADD_CART_ITEM,
    REMOVE_CART_ITEM,
} from "../actions";
import { scheduleContainsSection } from "../components/meetUtil";

import { MIN_TIME_DIFFERENCE } from "../constants/sync_constants";

// the state contains the following two pieces of data:
//  1. An object associating each schedule name with the schedule objecct
//  2. The name of the currently selected schedule
const initialState = {
    schedules: {},
    scheduleSelected: "",

    cartSections: [],
    cartPushedToBackend: false,
    deletedSchedules: [],
    cartUpdatedAt: Date.now(),

    readOnly: false,
    primaryScheduleId: "-1",
};

/**
 * Returns the next available schedule name that is similar to the given schedule name
 * Used for duplication
 * @param scheduleName: current schedule name
 * @param used: used schedule names stored in an object
 */
export const nextAvailable = (scheduleName, used) => {
    let newScheduleName = scheduleName;
    // compute the current number at the end of the string (if it exists)
    let endNum = 0;
    let numDigits = 0;
    let selectionIndex = newScheduleName.length - 1;
    while (
        selectionIndex >= 0 &&
        newScheduleName.charAt(selectionIndex) >= "0" &&
        newScheduleName.charAt(selectionIndex) <= 9
    ) {
        endNum +=
            Math.pow(10, numDigits) *
            parseInt(newScheduleName.charAt(selectionIndex), 10);
        numDigits += 1;
        selectionIndex -= 1;
    }
    // prevent double arithmetic issues
    endNum = Math.round(endNum);
    // search for the next available number
    const baseName = newScheduleName.substring(
        0,
        newScheduleName.length - numDigits
    );
    while (used[newScheduleName]) {
        endNum += 1;
        newScheduleName = baseName + endNum;
    }
    return newScheduleName;
};

/**
 * Returns a new schedule where the section is present if it was not previously, and vice-versa
 * @param sections
 * @param section
 */
const toggleSection = (scheduleSections, section) => {
    if (scheduleContainsSection(scheduleSections, section)) {
        return scheduleSections.filter((m) => m.id !== section.id);
    }
    return [...scheduleSections, section];
};

/**
 * A helper method for removing a schedule from a schedules object
 * @param scheduleKey The name of the schedule
 * @param initialSchedule The initial schedules object
 */
const removeSchedule = (scheduleKey, initialSchedule) => {
    const newSchedules = {};
    Object.keys(initialSchedule)
        .filter((schedName) => schedName !== scheduleKey)
        .forEach((schedName) => {
            newSchedules[schedName] = initialSchedule[schedName];
        });
    return newSchedules;
};

/**
 * Performs a deletion and returns the resulting state
 * @param state The redux state
 * @param scheduleName The name of the schedule to delete
 */
const handleScheduleDeletion = (state, scheduleName) => {
    const newSchedules = removeSchedule(scheduleName, state.schedules);

    return {
        ...state,
        schedules: newSchedules,
        scheduleSelected:
            scheduleName === state.scheduleSelected
                ? Object.keys(newSchedules)[0]
                : state.scheduleSelected,
        deletedSchedules: state.deletedSchedules.filter(
            (deletedScheduleName) => deletedScheduleName !== scheduleName
        ),
    };
};

/**
 * Takes in schedules from the backend; incorporates them into state; and returns the new state
 * @param state The redux state
 * @param schedulesFromBackend The schedules object sent by the backend
 * @returns {{cartSections: *, cartPushedToBackend: boolean, schedules: *}}
 */
const handleUpdateSchedulesOnFrontend = (state, schedulesFromBackend) => {
    let newState = { ...state };

    schedulesFromBackend.forEach((scheduleFromBackend) => {
        if (
            newState.deletedSchedules.reduce(
                (acc, schedule) => acc || schedule === scheduleFromBackend.name,
                false
            )
        ) {
            return;
        }

        const cloudUpdated = new Date(scheduleFromBackend.updated_at).getTime();

        if (scheduleFromBackend.name === "cart") {
            // If changes to the cart are still syncing, ignore the requested update
            if (
                newState.cartPushedToBackend &&
                cloudUpdated >= newState.cartUpdatedAt &&
                cloudUpdated - newState.cartUpdatedAt >= MIN_TIME_DIFFERENCE
            ) {
                newState = {
                    ...newState,
                    cartId: scheduleFromBackend.id,
                    cartSections: scheduleFromBackend.sections,
                    cartUpdatedAt: scheduleFromBackend.updated_at,
                };
            }
        } else {
            const foundSchedule = newState.schedules[scheduleFromBackend.name];
            // If changes to the schedule are still syncing, ignore the requested update
            if (
                !foundSchedule ||
                (foundSchedule &&
                    foundSchedule.pushedToBackend &&
                    cloudUpdated >= foundSchedule.updated_at &&
                    foundSchedule.updated_at - cloudUpdated >=
                        MIN_TIME_DIFFERENCE)
            ) {
                newState = {
                    ...newState,
                    scheduleSelected: newState.schedules[
                        newState.scheduleSelected
                    ]
                        ? newState.scheduleSelected
                        : scheduleFromBackend.name,
                    schedules: {
                        ...newState.schedules,
                        [scheduleFromBackend.name]: {
                            sections: scheduleFromBackend.sections,
                            id: scheduleFromBackend.id,
                            pushedToBackend: true,
                            updated_at: Date.now(),
                        },
                    },
                };
            }
        }
    });

    return newState;
};

/**
 * Handles removal of an item from the cart
 * @param sectionId
 * @param state
 * @return {{cartSections: *, cartPushedToBackend: boolean, cartUpdatedAt: *}}
 */
const handleRemoveCartItem = (sectionId, state) => ({
    ...state,
    cartUpdatedAt: Date.now(),
    cartSections: state.cartSections.filter(({ id }) => id !== sectionId),
    cartPushedToBackend: false,
});

export const schedule = (state = initialState, action) => {
    switch (action.type) {
        case CLEAR_ALL_SCHEDULE_DATA:
            return { ...initialState };
        // restrict schedules to ones from the current semester
        case SET_PRIMARY_SCHEDULE_ID_ON_FRONTEND:
            return {
                ...state,
                primaryScheduleId: action.scheduleId,
            };
        case SET_STATE_READ_ONLY:
            return { ...state, readOnly: action.readOnly };
        case MARK_SCHEDULE_SYNCED:
            return {
                ...state,
                schedules: {
                    ...state.schedules,
                    [action.scheduleName]: {
                        ...state.schedules[action.scheduleName],
                        pushedToBackend: true,
                        updated_at: Date.now(),
                    },
                },
            };
        case MARK_CART_SYNCED:
            return {
                ...state,
                cartPushedToBackend: true,
                cartUpdatedAt: Date.now(),
            };
        case CLEAR_SCHEDULE:
            return {
                ...state,
                schedules: {
                    ...state.schedules,
                    [state.scheduleSelected]: {
                        ...[state.scheduleSelected],
                        sections: [],
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
                scheduleSelected:
                    state.scheduleSelected === action.oldName
                        ? action.newName
                        : state.scheduleSelected,
            };
        case UPDATE_SCHEDULES_ON_FRONTEND:
            return handleUpdateSchedulesOnFrontend(
                state,
                action.schedulesFromBackend
            );
        case DOWNLOAD_SCHEDULE:
            return {
                ...state,
                clickedOnSchedule: state.schedules[action.scheduleName].id,
            };
        case CREATE_SCHEDULE_ON_FRONTEND:
            if (action.scheduleName === "cart") {
                return {
                    ...state,
                    cartUpdatedAt: Date.now(),
                    cartId: action.scheduleId,
                    cartPushedToBackend: true,
                    cartSections: action.scheduleSections,
                };
            }
            return {
                ...state,
                schedules: {
                    ...state.schedules,
                    [action.scheduleName]: {
                        sections: action.scheduleSections,
                        id: action.scheduleId,
                        pushedToBackend: true,
                        updated_at: Date.now(),
                    },
                },
                scheduleSelected: action.scheduleName,
            };
        case DELETE_SCHEDULE_ON_FRONTEND:
            return handleScheduleDeletion(state, action.scheduleName);
        case DELETION_ATTEMPTED:
            return {
                ...state,
                deletedSchedules: state.deletedSchedules.push(
                    action.scheduleName
                ),
            };
        case CREATE_CART_ON_FRONTEND:
            return {
                ...state,
                cartId: action.cartId,
                cartSections: action.cartSections,
                cartPushedToBackend: true,
                cartUpdatedAt: Date.now(),
            };
        case CHANGE_SCHEDULE:
            return {
                ...state,
                scheduleSelected: action.scheduleName,
            };
        case TOGGLE_CHECK:
            if (!state.readOnly) {
                return {
                    ...state,
                    schedules: {
                        ...state.schedules,
                        [state.scheduleSelected]: {
                            ...state.schedules[state.scheduleSelected],
                            updated_at: Date.now(),
                            sections: toggleSection(
                                state.schedules[state.scheduleSelected]
                                    .sections,
                                action.course
                            ),
                            pushedToBackend: false,
                        },
                    },
                };
            }
            return {
                ...state,
            };

        case REMOVE_SCHED_ITEM:
            if (!state.readOnly) {
                return {
                    ...state,
                    schedules: {
                        ...state.schedules,
                        [state.scheduleSelected]: {
                            ...state.schedules[state.scheduleSelected],
                            updated_at: Date.now(),
                            pushedToBackend: false,
                            sections: state.schedules[
                                state.scheduleSelected
                            ].sections.filter((m) => m.id !== action.id),
                        },
                    },
                };
            }
            return {
                ...state,
            };

        case ADD_CART_ITEM:
            return {
                ...state,
                cartUpdatedAt: Date.now(),
                cartSections: [...state.cartSections, action.section],
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
