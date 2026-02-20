import ReactGA from "react-ga";
import {
    ADD_SCHOOL_REQ,
    REM_SCHOOL_REQ,
    UPDATE_SEARCH_TEXT,
    UPDATE_RANGE_FILTER,
    CHANGE_MY_SCHEDULE,
    RENAME_SCHEDULE,
    CREATE_SCHEDULE_ON_FRONTEND,
    DELETE_SCHEDULE_ON_FRONTEND,
    SET_PRIMARY_SCHEDULE_ID_ON_FRONTEND,
} from "../actions";
import { SWITCH_ACTIVE_FRIEND } from "../actions/friendshipUtil";

export const initGA = () => {
    ReactGA.initialize("UA-21029575-15");
};
export const logPageView = () => {
    ReactGA.set({ page: window.location.pathname });
    ReactGA.pageview(window.location.pathname);
};
export const logEvent = (category = "", action = "", label = "") => {
    if (category && action) {
        ReactGA.event({ category, action, label });
    }
};
export const logException = (description = "", fatal = false) => {
    if (description) {
        ReactGA.exception({ description, fatal });
    }
};

const filterActions = [ADD_SCHOOL_REQ, REM_SCHOOL_REQ, UPDATE_RANGE_FILTER];
const schedActions = [
    CHANGE_MY_SCHEDULE,
    RENAME_SCHEDULE,
    CREATE_SCHEDULE_ON_FRONTEND,
    DELETE_SCHEDULE_ON_FRONTEND,
];
const schedShareActions = [
    SET_PRIMARY_SCHEDULE_ID_ON_FRONTEND, // Changing schedule to share
    SWITCH_ACTIVE_FRIEND // Viewing friend's schedule
]

// TODO: confirm type of store, next, and action
export const analyticsMiddleware = (store: any) => (next: (_: any) => void) => (
    action: any
) => {
    if (filterActions.includes(action.type)) {
        logEvent("filter", action.type, JSON.stringify(action));
    } else if (schedActions.includes(action.type)) {
        logEvent("schedule", action.type, JSON.stringify(action));
    } else if (schedShareActions.includes(action.type)) {
        logEvent("schedule share", action.type, JSON.stringify(action));
    } else if (action.type === UPDATE_SEARCH_TEXT) {
        logEvent("search", action.s);
    }

    return next(action);
};
