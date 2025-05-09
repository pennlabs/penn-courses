import fetch from "cross-fetch";
import AwesomeDebouncePromise from "awesome-debounce-promise";
import { batch } from "react-redux";
import { parsePhoneNumberFromString } from "libphonenumber-js";
import getCsrf from "../components/csrf";
import { MIN_FETCH_INTERVAL } from "../constants/sync_constants";
import { PATH_REGISTRATION_SCHEDULE_NAME } from "../constants/constants";

export const UPDATE_SEARCH = "UPDATE_SEARCH";
export const UPDATE_SEARCH_REQUEST = "UPDATE_SEARCH_REQUEST";

export const UPDATE_COURSE_INFO_SUCCESS = "UPDATE_COURSE_INFO_SUCCESS";
export const UPDATE_COURSE_INFO_REQUEST = "UPDATE_COURSE_INFO_REQUEST";

export const UPDATE_SCROLL_POS = "UPDATE_SCROLL_POS";

export const UPDATE_SECTIONS = "UPDATE_SECTIONS";
export const OPEN_SECTION_INFO = "OPEN_SECTION_INFO";

export const OPEN_MODAL = "OPEN_MODAL";
export const CLOSE_MODAL = "CLOSE_MODAL";

export const COURSE_SEARCH_ERROR = "COURSE_SEARCH_ERROR";
export const COURSE_SEARCH_LOADING = "COURSE_SEARCH_LOADING";
export const COURSE_SEARCH_SUCCESS = "COURSE_SEARCH_SUCCESS";

export const LOAD_REQUIREMENTS = "LOAD_REQUIREMENTS";
export const ADD_SCHOOL_REQ = "ADD_SCHOOL_REQ";
export const REM_SCHOOL_REQ = "REM_SCHOOL_REQ";
export const UPDATE_SEARCH_TEXT = "UPDATE_SEARCH_TEXT";

export const UPDATE_RANGE_FILTER = "UPDATE_RANGE_FILTER";
export const UPDATE_CHECKBOX_FILTER = "UPDATE_CHECKBOX_FILTER";
export const UPDATE_BUTTON_FILTER = "UPDATE_BUTTON_FILTER";
export const CLEAR_FILTER = "CLEAR_FILTER";
export const CLEAR_ALL = "CLEAR_ALL";

export const SECTION_INFO_SEARCH_ERROR = "SECTION_INFO_SEARCH_ERROR";
export const SECTION_INFO_SEARCH_LOADING = "SECTION_INFO_SEARCH_LOADING";
export const SECTION_INFO_SEARCH_SUCCESS = "SECTION_INFO_SEARCH_SUCCESS";

export const ADD_CART_ITEM = "ADD_CART_ITEM";
export const REMOVE_CART_ITEM = "REMOVE_CART_ITEM";
export const CHANGE_SORT_TYPE = "CHANGE_SORT_TYPE";

export const REGISTER_ALERT_ITEM = "REGISTER_ALERT_ITEM";
export const REACTIVATE_ALERT_ITEM = "REACTIVATE_ALERT_ITEM";
export const DEACTIVATE_ALERT_ITEM = "DEACTIVATE_ALERT_ITEM";
export const DELETE_ALERT_ITEM = "DELETE_ALERT_ITEM";
export const UPDATE_CONTACT_INFO = "UPDATE_CONTACT_INFO";

export const MARK_ALERTS_SYNCED = "MARK_ALERTS_SYNCED";

export const TOGGLE_CHECK = "TOGGLE_CHECK";
export const REMOVE_SCHED_ITEM = "REMOVE_SCHED_ITEM";

export const CLEAR_ALL_SCHEDULE_DATA = "CLEAR_ALL_SCHEDULE_DATA";
export const CREATE_CART_ON_FRONTEND = "CREATE_CART_ON_FRONTEND";
export const CREATE_SCHEDULE_ON_FRONTEND = "CREATE_SCHEDULE_ON_FRONTEND";
export const DELETE_SCHEDULE_ON_FRONTEND = "DELETE_SCHEDULE_ON_FRONTEND";
export const CHANGE_MY_SCHEDULE = "CHANGE_MY_SCHEDULE";
export const RENAME_SCHEDULE = "RENAME_SCHEDULE";
export const CLEAR_SCHEDULE = "CLEAR_SCHEDULE";
export const DOWNLOAD_SCHEDULE = "DOWNLOAD_SCHEDULE";

export const UPDATE_SCHEDULES_ON_FRONTEND = "UPDATE_SCHEDULES_ON_FRONTEND";
export const MARK_SCHEDULE_SYNCED = "MARK_SCHEDULE_SYNCED";
export const MARK_CART_SYNCED = "MARK_CART_SYNCED";
export const DELETION_ATTEMPTED = "DELETION_ATTEMPTED";
export const SET_STATE_READ_ONLY = "SET_STATE_READ_ONLY";
export const SET_PRIMARY_SCHEDULE_ID_ON_FRONTEND =
    "SET_PRIMARY_SCHEDULE_ID_ON_FRONTEND";

export const doAPIRequest = (path, options = {}) =>
    fetch(`/api${path}`, options);

export const renameSchedule = (oldName, newName) => ({
    type: RENAME_SCHEDULE,
    oldName,
    newName,
});

export const changeMySchedule = (scheduleName) => ({
    type: CHANGE_MY_SCHEDULE,
    scheduleName,
});

export const createCartOnFrontend = (cartId, cartSections) => ({
    type: CREATE_CART_ON_FRONTEND,
    cartId,
    cartSections,
});

export const markScheduleSynced = (scheduleName) => ({
    scheduleName,
    type: MARK_SCHEDULE_SYNCED,
});

export const markCartSynced = () => ({
    type: MARK_CART_SYNCED,
});

export const downloadSchedule = (scheduleName) => ({
    type: DOWNLOAD_SCHEDULE,
    scheduleName,
});

export const addCartItem = (section) => ({
    type: ADD_CART_ITEM,
    section,
});

export const removeSchedItem = (id) => ({
    type: REMOVE_SCHED_ITEM,
    id,
});

export const updateSearch = (searchResults) => ({
    type: UPDATE_SEARCH,
    searchResults,
});

const updateSearchRequest = () => ({
    type: UPDATE_SEARCH_REQUEST,
});

export const updateSections = (sections) => ({
    type: UPDATE_SECTIONS,
    sections,
});

export const updateSectionInfo = (sectionInfo) => ({
    type: OPEN_SECTION_INFO,
    sectionInfo,
});

const updateCourseInfoRequest = () => ({
    type: UPDATE_COURSE_INFO_REQUEST,
});

export const updateCourseInfo = (course) => ({
    type: UPDATE_COURSE_INFO_SUCCESS,
    course,
});

export const updateScrollPos = (scrollPos = 0) => ({
    type: UPDATE_SCROLL_POS,
    scrollPos,
});

export const createScheduleOnFrontend = (
    scheduleName,
    scheduleId,
    scheduleSections
) => ({
    type: CREATE_SCHEDULE_ON_FRONTEND,
    scheduleName,
    scheduleId,
    scheduleSections,
});

export const clearAllScheduleData = () => ({ type: CLEAR_ALL_SCHEDULE_DATA });

export const openModal = (modalKey, modalProps, modalTitle) => ({
    type: OPEN_MODAL,
    modalKey,
    modalProps,
    modalTitle,
});

export const closeModal = () => ({
    type: CLOSE_MODAL,
});

export const clearSchedule = () => ({
    type: CLEAR_SCHEDULE,
});

export const setPrimaryScheduleIdOnFrontend = (scheduleId) => ({
    scheduleId,
    type: SET_PRIMARY_SCHEDULE_ID_ON_FRONTEND,
});

export const checkForDefaultSchedules = (schedulesFromBackend) => (
    dispatch
) => {
    if (!schedulesFromBackend.find((acc, { name }) => acc || name === "cart")) {
        dispatch(createScheduleOnBackend("cart"));
    }
    // if the user doesn't have an initial schedule, create it
    if (
        schedulesFromBackend.length === 0 ||
        (schedulesFromBackend.length === 1 &&
            schedulesFromBackend[0].name === "cart")
    ) {
        dispatch(createScheduleOnBackend("Schedule"));
    }
};

export const loadRequirements = () => (dispatch) =>
    doAPIRequest("/base/current/requirements/").then(
        (response) =>
            response.json().then(
                (data) => {
                    const obj = {
                        SAS: [],
                        SEAS: [],
                        WH: [],
                        NURS: [],
                    };
                    const selObj = {};
                    data.forEach((element) => {
                        obj[element.school].push(element);
                        selObj[element.id] = 0;
                    });
                    dispatch({
                        type: LOAD_REQUIREMENTS,
                        obj,
                        selObj,
                    });
                },
                (error) => {
                    // eslint-disable-next-line no-console
                    console.log(error);
                }
            ),
        (error) => {
            // eslint-disable-next-line no-console
            console.log(error);
        }
    );

function buildCourseSearchUrl(filterData) {
    let queryString = `/base/current/search/courses/?search=${filterData.searchString}`;

    // Requirements filter
    const reqs = [];
    if (filterData.selectedReq) {
        for (const key of Object.keys(filterData.selectedReq)) {
            if (filterData.selectedReq[key]) {
                reqs.push(key);
            }
        }

        if (reqs.length > 0) {
            queryString += `&requirements=${reqs[0]}`;
            for (let i = 1; i < reqs.length; i += 1) {
                queryString += `,${reqs[i]}`;
            }
        }
    }

    // Range filters
    const filterFields = [
        "difficulty",
        "course_quality",
        "instructor_quality",
        "time",
    ];
    const defaultFilters = [
        [0, 4],
        [0, 4],
        [0, 4],
        [1.5, 17],
    ];
    const decimalToTime = (t) => {
        const hour = Math.floor(t);
        const mins = parseFloat(((t % 1) * 0.6).toFixed(2));
        return Math.min(23.59, hour + mins);
    };
    for (let i = 0; i < filterFields.length; i += 1) {
        if (
            filterData[filterFields[i]] &&
            JSON.stringify(filterData[filterFields[i]]) !==
                JSON.stringify(defaultFilters[i])
        ) {
            const filterRange = filterData[filterFields[i]];
            if (filterFields[i] === "time") {
                const start = decimalToTime(24 - filterRange[1]);
                const end = decimalToTime(24 - filterRange[0]);
                queryString += `&${filterFields[i]}=${
                    start === 7 ? "" : start
                }-${end === 10.3 ? "" : end}`;
            } else {
                queryString += `&${filterFields[i]}=${filterRange[0]}-${filterRange[1]}`;
            }
        }
    }

    // Checkbox Filters
    const checkboxFields = ["cu", "activity", "days"];
    const checkboxDefaultFields = [
        {
            0.5: 0,
            1: 0,
            1.5: 0,
        },
        {
            LAB: 0,
            REC: 0,
            SEM: 0,
            STU: 0,
        },
        {
            M: 1,
            T: 1,
            W: 1,
            R: 1,
            F: 1,
            S: 1,
            U: 1,
        },
    ];
    for (let i = 0; i < checkboxFields.length; i += 1) {
        if (
            filterData[checkboxFields[i]] &&
            JSON.stringify(filterData[checkboxFields[i]]) !==
                JSON.stringify(checkboxDefaultFields[i])
        ) {
            const applied = [];
            Object.keys(filterData[checkboxFields[i]]).forEach((item) => {
                // eslint-disable-line
                if (filterData[checkboxFields[i]][item]) {
                    applied.push(item);
                }
            });
            if (applied.length > 0) {
                if (checkboxFields[i] === "days") {
                    queryString +=
                        applied.length < 7 ? `&days=${applied.join("")}` : "";
                } else {
                    queryString += `&${checkboxFields[i]}=${applied[0]}`;
                    for (let j = 1; j < applied.length; j += 1) {
                        queryString += `,${applied[j]}`;
                    }
                }
            }
        }
    }

    // toggle button filters
    const buttonFields = ["schedule-fit", "is_open"];
    const buttonDefaultFields = [-1, 0];

    for (let i = 0; i < buttonFields.length; i += 1) {
        if (
            filterData[buttonFields[i]] &&
            JSON.stringify(filterData[buttonFields[i]]) !==
                JSON.stringify(buttonDefaultFields[i])
        ) {
            // get each filter's value
            const applied = filterData[buttonFields[i]];
            if (applied !== undefined && applied !== "" && applied !== null) {
                queryString += `&${buttonFields[i]}=${applied}`;
            }
        }
    }

    return queryString;
}

const courseSearch = (_, filterData) =>
    doAPIRequest(buildCourseSearchUrl(filterData));

const debouncedCourseSearch = AwesomeDebouncePromise(courseSearch, 500);

export function fetchCourseSearch(filterData) {
    return (dispatch) => {
        dispatch(updateSearchRequest());
        debouncedCourseSearch(dispatch, filterData)
            .then((res) => res.json())
            .then((res) => res.filter((course) => course.num_sections > 0))
            .then((res) =>
                batch(() => {
                    dispatch(updateScrollPos());
                    dispatch(updateSearch(res));
                    if (res.length === 1)
                        dispatch(fetchCourseDetails(res[0].id));
                })
            )
            .catch((error) => dispatch(courseSearchError(error)));
    };
}

export function updateSearchText(s) {
    return {
        type: UPDATE_SEARCH_TEXT,
        s,
    };
}

function buildSectionInfoSearchUrl(searchData) {
    return `/base/current/courses/${searchData.param}/`;
}

export function courseSearchError(error) {
    return {
        type: COURSE_SEARCH_ERROR,
        error,
    };
}

export function sectionInfoSearchError(error) {
    return {
        type: SECTION_INFO_SEARCH_ERROR,
        error,
    };
}

export function addSchoolReq(reqID) {
    return {
        type: ADD_SCHOOL_REQ,
        reqID,
    };
}

export function remSchoolReq(reqID) {
    return {
        type: REM_SCHOOL_REQ,
        reqID,
    };
}

export function updateRangeFilter(field, values) {
    return {
        type: UPDATE_RANGE_FILTER,
        field,
        values,
    };
}

export function updateCheckboxFilter(field, value, toggleState) {
    return {
        type: UPDATE_CHECKBOX_FILTER,
        field,
        value,
        toggleState,
    };
}

export function updateButtonFilter(field, value) {
    return {
        type: UPDATE_BUTTON_FILTER,
        field,
        value,
    };
}

export function clearFilter(propertyName) {
    return {
        type: CLEAR_FILTER,
        propertyName,
    };
}

export const deletionAttempted = (scheduleName) => ({
    type: DELETION_ATTEMPTED,
    scheduleName,
});

export const deleteScheduleOnFrontend = (scheduleName) => ({
    type: DELETE_SCHEDULE_ON_FRONTEND,
    scheduleName,
});

export function clearAll() {
    return {
        type: CLEAR_ALL,
    };
}

export const updateSchedulesOnFrontend = (schedulesFromBackend) => ({
    type: UPDATE_SCHEDULES_ON_FRONTEND,
    schedulesFromBackend,
});

export const setStateReadOnly = (readOnly) => ({
    type: SET_STATE_READ_ONLY,
    readOnly,
});

export function courseSearchLoading() {
    return {
        type: COURSE_SEARCH_LOADING,
    };
}

export function courseSearchSuccess(items) {
    return {
        type: COURSE_SEARCH_SUCCESS,
        items,
    };
}

export const toggleCheck = (course) => ({
    type: TOGGLE_CHECK,
    course,
});

export const removeCartItem = (sectionId) => ({
    type: REMOVE_CART_ITEM,
    sectionId,
});

export const registerAlertFrontend = (alert) => ({
    type: REGISTER_ALERT_ITEM,
    alert,
});

export const reactivateAlertFrontend = (sectionId) => ({
    type: REACTIVATE_ALERT_ITEM,
    sectionId,
});

export const deactivateAlertFrontend = (sectionId) => ({
    type: DEACTIVATE_ALERT_ITEM,
    sectionId,
});

export const deleteAlertFrontend = (sectionId) => ({
    type: DELETE_ALERT_ITEM,
    sectionId,
});

export const updateContactInfoFrontend = (contactInfo) => ({
    type: UPDATE_CONTACT_INFO,
    contactInfo,
});

export const markAlertsSynced = () => ({
    type: MARK_ALERTS_SYNCED,
});

export const changeSortType = (sortMode) => ({
    type: CHANGE_SORT_TYPE,
    sortMode,
});

let lastFetched = 0;
/**
 * Ensure that fetches don't happen too frequently by requiring that it has been 250ms
 * since the last rate-limited fetch.
 * @param url The url to fetch
 * @param init The init to apply to the url
 * @returns {Promise<unknown>}
 */

const rateLimitedFetch = (url, init) =>
    new Promise((resolve, reject) => {
        // Wraps the fetch in a new promise that conditionally rejects if
        // the required amount of time has not elapsed
        const now = Date.now();
        if (now - lastFetched > MIN_FETCH_INTERVAL) {
            doAPIRequest(url, init)
                .then((result) => {
                    resolve(result);
                })
                .catch((err) => {
                    reject(err);
                });
            lastFetched = now;
        } else {
            reject(new Error("minDelayNotElapsed"));
        }
    });

export const deduplicateCourseMeetings = (course) => {
    const deduplicatedCourse = {
        ...course,
        sections: course.sections.map((section) => {
            const meetings = [];

            section.meetings.forEach((meeting) => {
                const exists = meetings.some(
                    (existingMeeting) =>
                        existingMeeting.day === meeting.day &&
                        existingMeeting.start === meeting.start &&
                        existingMeeting.end === meeting.end
                );

                if (!exists) {
                    meetings.push(meeting);
                }
            });

            return { ...section, meetings };
        }),
    };

    return deduplicatedCourse;
};

export function fetchCourseDetails(courseId) {
    return (dispatch) => {
        dispatch(updateCourseInfoRequest());
        doAPIRequest(`/base/current/courses/${courseId}/?include_location=True`)
            .then((res) => res.json())
            .then((data) => deduplicateCourseMeetings(data))
            .then((course) => dispatch(updateCourseInfo(course)))
            .catch((error) => dispatch(sectionInfoSearchError(error)));
    };
}

/**
 * Pulls schedules from the backend
 * @param onComplete The function to call when initialization has been completed (with the schedules
 * from the backend)
 * @returns {Function}
 */
export const fetchBackendSchedules = (onComplete) => (dispatch) => {
    doAPIRequest("/plan/schedules/")
        .then((res) => res.json())
        .then((data) => data.map((course) => deduplicateCourseMeetings(course)))
        .then((schedules) => {
            onComplete(schedules);
        })
        // eslint-disable-next-line no-console
        .catch((error) => console.log(error, "Not logged in"));
};

/**
 * Updates a schedule on the backend
 * Skips if the id is not yet initialized for the schedule
 * Once the schedule has been updated, the schedule is marked as updated locally
 * @param name The name of the schedule
 * @param schedule The schedule object
 */
export const updateScheduleOnBackend = (name, schedule) => (dispatch) => {
    const updatedScheduleObj = {
        ...schedule,
        name,
        sections: schedule.sections,
    };
    doAPIRequest(`/plan/schedules/${schedule.id}/`, {
        method: "PUT",
        credentials: "include",
        mode: "same-origin",
        headers: {
            Accept: "application/json",
            "Content-Type": "application/json",
            "X-CSRFToken": getCsrf(),
        },
        body: JSON.stringify(updatedScheduleObj),
    })
        .then(() => {
            if (name === "cart") {
                dispatch(markCartSynced());
            } else {
                dispatch(markScheduleSynced(name));
            }
        })
        .catch(() => {});
};

export function fetchSectionInfo(searchData) {
    return (dispatch) =>
        doAPIRequest(buildSectionInfoSearchUrl(searchData)).then(
            (response) =>
                response.json().then(
                    (json) => {
                        const info = {
                            id: json.id,
                            description: json.description,
                            crosslistings: json.crosslistings,
                        };
                        const { sections } = json;
                        dispatch(updateCourseInfo(sections, info));
                    },
                    (error) => dispatch(sectionInfoSearchError(error))
                ),
            (error) => dispatch(sectionInfoSearchError(error))
        );
}

/**
 * Creates a schedule on the backend
 * @param name The name of the schedule
 * @param sections The list of sections for the schedule
 * @returns {Function}
 */
export const createScheduleOnBackend = (name, sections = []) => (dispatch) => {
    const scheduleObj = {
        name,
        sections,
    };
    doAPIRequest("/plan/schedules/", {
        method: "POST",
        credentials: "include",
        mode: "same-origin",
        headers: {
            Accept: "application/json",
            "Content-Type": "application/json",
            "X-CSRFToken": getCsrf(),
        },
        body: JSON.stringify(scheduleObj),
    })
        .then((response) => response.json())
        .then(({ id }) => {
            dispatch(createScheduleOnFrontend(name, id, sections));
        })
        .catch((error) => console.log(error));
};

export const deleteScheduleOnBackend = (user, scheduleName, scheduleId) => (
    dispatch
) => {
    if (
        scheduleName === "cart" ||
        scheduleName === PATH_REGISTRATION_SCHEDULE_NAME
    ) {
        return;
    }

    dispatch(deletionAttempted(scheduleName));
    rateLimitedFetch(`/plan/schedules/${scheduleId}/`, {
        method: "DELETE",
        credentials: "include",
        mode: "same-origin",
        headers: {
            Accept: "application/json",
            "Content-Type": "application/json",
            "X-CSRFToken": getCsrf(),
        },
    })
        .then(() => {
            dispatch(deleteScheduleOnFrontend(scheduleName));
            dispatch(findOwnPrimarySchedule(user));
            dispatch(
                fetchBackendSchedules((schedulesFromBackend) => {
                    dispatch(checkForDefaultSchedules(schedulesFromBackend));
                })
            );
        })
        .catch((error) => console.log(error));
};

export const findOwnPrimarySchedule = (user) => (dispatch) => {
    doAPIRequest("/plan/primary-schedules/").then((res) =>
        res
            .json()
            .then((schedules) => {
                return schedules.find(
                    (sched) => sched.user.username === user.username
                );
            })
            .then((foundSched) => {
                dispatch(
                    setPrimaryScheduleIdOnFrontend(foundSched?.schedule.id)
                );
            })
            .catch((error) => console.log(error))
    );
};

export const setCurrentUserPrimarySchedule = (user, scheduleId) => (
    dispatch
) => {
    const scheduleIdObj = {
        schedule_id: scheduleId,
    };
    const init = {
        method: "POST",
        credentials: "include",
        mode: "same-origin",
        headers: {
            Accept: "application/json",
            "Content-Type": "application/json",
            "X-CSRFToken": getCsrf(),
        },
        body: JSON.stringify(scheduleIdObj),
    };

    doAPIRequest("/plan/primary-schedules/", init)
        .then(() => {
            dispatch(findOwnPrimarySchedule(user));
        })
        .catch((error) => console.log(error));
};

export const registerAlertItem = (sectionId) => (dispatch) => {
    const registrationObj = {
        section: sectionId,
        auto_resubscribe: true,
        close_notification: false,
    };
    const init = {
        method: "POST",
        credentials: "include",
        mode: "same-origin",
        headers: {
            Accept: "application/json",
            "Content-Type": "application/json",
            "X-CSRFToken": getCsrf(),
        },
        body: JSON.stringify(registrationObj),
    };
    doAPIRequest("/alert/registrations/", init)
        .then((res) => res.json())
        .then((data) => {
            dispatch(
                registerAlertFrontend({
                    ...registrationObj,
                    id: data.id,
                    cancelled: false,
                    status: "C",
                })
            );
        });
};

export const reactivateAlertItem = (sectionId, alertId) => (dispatch) => {
    const updateObj = {
        resubscribe: true,
    };
    const init = {
        method: "PUT",
        credentials: "include",
        mode: "same-origin",
        headers: {
            Accept: "application/json",
            "Content-Type": "application/json",
            "X-CSRFToken": getCsrf(),
        },
        body: JSON.stringify(updateObj),
    };
    doAPIRequest(`/alert/registrations/${alertId}/`, init).then((res) => {
        if (res.ok) {
            dispatch(reactivateAlertFrontend(sectionId));
        }
    });
};

export const deactivateAlertItem = (sectionId, alertId) => (dispatch) => {
    const updateObj = {
        cancelled: true,
    };
    const init = {
        method: "PUT",
        credentials: "include",
        mode: "same-origin",
        headers: {
            Accept: "application/json",
            "Content-Type": "application/json",
            "X-CSRFToken": getCsrf(),
        },
        body: JSON.stringify(updateObj),
    };
    doAPIRequest(`/alert/registrations/${alertId}/`, init).then((res) => {
        if (res.ok) {
            dispatch(deactivateAlertFrontend(sectionId));
        }
    });
};

export const deleteAlertItem = (sectionId, alertId) => (dispatch) => {
    const updateObj = {
        deleted: true,
    };
    const init = {
        method: "PUT",
        credentials: "include",
        mode: "same-origin",
        headers: {
            Accept: "application/json",
            "Content-Type": "application/json",
            "X-CSRFToken": getCsrf(),
        },
        body: JSON.stringify(updateObj),
    };
    doAPIRequest(`/alert/registrations/${alertId}/`, init).then((res) => {
        if (res.ok) {
            dispatch(deleteAlertFrontend(sectionId));
        }
    });
};

export const fetchAlerts = () => (dispatch) => {
    const init = {
        method: "GET",
        credentials: "include",
        mode: "same-origin",
        headers: {
            Accept: "application/json",
            "Content-Type": "application/json",
            "X-CSRFToken": getCsrf(),
        },
    };
    doAPIRequest("/alert/registrations/", init)
        .then((res) => res.json())
        .then((alerts) => {
            alerts.forEach((alert) => {
                dispatch(
                    registerAlertFrontend({
                        id: alert.id,
                        section: alert.section,
                        cancelled: alert.cancelled,
                        auto_resubscribe: alert.auto_resubscribe,
                        close_notification: alert.close_notification,
                        status: alert.section_status,
                    })
                );
            });
        })
        .catch((error) => console.log(error));
};

export const fetchContactInfo = () => (dispatch) => {
    fetch("/accounts/me/", {
        method: "GET",
        credentials: "include",
        mode: "same-origin",
        headers: {
            Accept: "application/json",
            "Content-Type": "application/json",
            "X-CSRFToken": getCsrf(),
        },
    })
        .then((res) => res.json())
        .then((data) => {
            dispatch(
                updateContactInfoFrontend({
                    email: data.profile.email,
                    phone: data.profile.phone,
                })
            );
        })
        // eslint-disable-next-line no-console
        .catch((error) => console.log(error));
};

export const updateContactInfo = (contactInfo) => (dispatch) => {
    const profile = {
        email: contactInfo.email,
        phone:
            parsePhoneNumberFromString(contactInfo.phone, "US")?.number ?? "",
    };
    fetch("/accounts/me/", {
        method: "PATCH",
        credentials: "include",
        mode: "same-origin",
        headers: {
            Accept: "application/json",
            "Content-Type": "application/json",
            "X-CSRFToken": getCsrf(),
        },
        body: JSON.stringify({
            profile,
        }),
    }).then((res) => {
        if (!res.ok) {
            throw new Error(JSON.stringify(res));
        } else {
            dispatch(updateContactInfoFrontend(profile));
        }
    });
};
