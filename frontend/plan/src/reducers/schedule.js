import {
    CHANGE_SCHEDULE,
    CREATE_SCHEDULE,
    DELETE_SCHEDULE,
    REMOVE_SCHED_ITEM,
    RENAME_SCHEDULE,
    DUPLICATE_SCHEDULE,
    CLEAR_SCHEDULE, TOGGLE_CHECK, ADD_CART_ITEM, REMOVE_CART_ITEM
} from "../actions";
import { meetingsContainSection } from "../meetUtil";

const DEFAULT_SCHEDULE_NAME = "Schedule";

// returns the default empty schedule
const generateDefaultSchedule = () => (
    {
        term: "2019A",
        meetings: [],
        colorPalette: [],
        LocAdded: false,
    }
);

// the state contains the following two pieces of data:
//  1. An object associating each schedule name with the schedule objecct
//  2. The name of the currently selected schedule
const initialState = {
    schedules: { [DEFAULT_SCHEDULE_NAME]: generateDefaultSchedule() },
    scheduleSelected: DEFAULT_SCHEDULE_NAME,
    cartCourses: [],
};

/**
 * A helper method for removing a schedule from a schedules object
 * @param scheduleKey The name of the schedule
 * @param initialSchedule The initial schedules object
 */
const removeSchedule = (scheduleKey, initialSchedule) => {
    const newSchedules = {};
    Object.keys(initialSchedule).filter(schedName => schedName !== scheduleKey)
        .forEach((schedName) => { newSchedules[schedName] = initialSchedule[schedName]; });
    return newSchedules;
};

/**
 * Returns a new schedule where the course is present if it was not previously, and vice-versa
 * @param course
 * @param meetings
 */
const toggleCourse = (course, meetings) => {
    if (meetingsContainSection(meetings, course)) {
        return meetings.filter(m => m.id !== course.id);
    }
    return [...meetings, course];
};


export const schedule = (state = initialState, action) => {
    const { cartCourses } = state;
    switch (action.type) {
        case CLEAR_SCHEDULE:
            return {
                ...state,
                schedules: {
                    ...state.schedules,
                    [state.scheduleSelected]: {
                        ...[state.scheduleSelected],
                        meetings: [],
                    },
                },
            };
        case RENAME_SCHEDULE:
            return {
                ...state,
                schedules: {
                    ...removeSchedule(state.scheduleSelected, state.schedules),
                    [action.scheduleName]: state.schedules[state.scheduleSelected],
                },
                scheduleSelected: action.scheduleName,
            };
        case DUPLICATE_SCHEDULE:
            return {
                ...state,
                schedules: {
                    ...state.schedules,
                    [action.scheduleName]: state.schedules[state.scheduleSelected],
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
        case DELETE_SCHEDULE: {
            const newSchedule = removeSchedule(state.scheduleSelected, state.schedules);
            return {
                ...state,
                schedules: removeSchedule(state.scheduleSelected, state.schedules),
                scheduleSelected: Object.keys(newSchedule)[0],
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
                        ...state[state.scheduleSelected],
                        meetings: toggleCourse(action.course, state.schedules[state.scheduleSelected].meetings),
                    },
                },
            };
        case REMOVE_SCHED_ITEM:
            return {
                ...state,
                schedules: {
                    ...state.schedules,
                    [state.scheduleSelected]: {
                        ...state[state.scheduleSelected],
                        meetings: state.schedules[state.scheduleSelected].meetings
                            .filter(m => m.id !== action.id),
                    },
                },
            };
        case ADD_CART_ITEM:
            const { section } = action;
            return { ...state, cartCourses: [...cartCourses, section] };
        case REMOVE_CART_ITEM:
            const { sectionId } = action;
            return { ...state, cartCourses: state.cartCourses.filter(({id}) => id !== sectionId)};
        default:
            return {
                ...state,
            };
    }
};
