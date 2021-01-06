import fetch from "cross-fetch";
import AwesomeDebouncePromise from "awesome-debounce-promise";
import { batch } from "react-redux";
import getCsrf from "../components/csrf";
import { MIN_FETCH_INTERVAL } from "../constants/sync_constants";

export const UPDATE_SEARCH = "UPDATE_SEARCH";
export const UPDATE_SEARCH_REQUEST = "UPDATE_SEARCH_REQUEST";

export const UPDATE_COURSE_INFO_SUCCESS = "UPDATE_COURSE_INFO_SUCCESS";
export const UPDATE_COURSE_INFO_REQUEST = "UPDATE_COURSE_INFO_REQUEST";

export const UPDATE_SCROLL_POS = "UPDATE_SCROLL_POS";

export const UPDATE_SECTIONS = "UPDATE_SECTIONS";
export const OPEN_SECTION_INFO = "OPEN_SECTION_INFO";
export const CHANGE_SCHEDULE = "CHANGE_SCHEDULE";
export const CREATE_SCHEDULE = "CREATE_SCHEDULE";

export const OPEN_MODAL = "OPEN_MODAL";
export const CLOSE_MODAL = "CLOSE_MODAL";

export const ADD_SCHED_ITEM = "ADD_SCHED_ITEM";
export const REMOVE_SCHED_ITEM = "REMOVE_SCHED_ITEM";
export const DELETE_SCHEDULE = "DELETE_SCHEDULE";
export const RENAME_SCHEDULE = "RENAME_SCHEDULE";
export const DUPLICATE_SCHEDULE = "DUPLICATE_SCHEDULE";
export const CLEAR_SCHEDULE = "CLEAR_SCHEDULE";
export const ENFORCE_SEMESTER = "ENFORCE_SEMESTER";
export const CLEAR_ALL_SCHEDULE_DATA = "CLEAR_ALL_SCHEDULE_DATA";

export const COURSE_SEARCH_ERROR = "COURSE_SEARCH_ERROR";
export const COURSE_SEARCH_LOADING = "COURSE_SEARCH_LOADING";
export const COURSE_SEARCH_SUCCESS = "COURSE_SEARCH_SUCCESS";

export const LOAD_REQUIREMENTS = "LOAD_REQUIREMENTS";
export const ADD_SCHOOL_REQ = "ADD_SCHOOL_REQ";
export const REM_SCHOOL_REQ = "REM_SCHOOL_REQ";
export const UPDATE_SEARCH_TEXT = "UPDATE_SEARCH_TEXT";

export const UPDATE_RANGE_FILTER = "UPDATE_RANGE_FILTER";
export const UPDATE_CHECKBOX_FILTER = "UPDATE_CHECKBOX_FILTER";
export const CLEAR_FILTER = "CLEAR_FILTER";
export const CLEAR_ALL = "CLEAR_ALL";

export const SECTION_INFO_SEARCH_ERROR = "SECTION_INFO_SEARCH_ERROR";
export const SECTION_INFO_SEARCH_LOADING = "SECTION_INFO_SEARCH_LOADING";
export const SECTION_INFO_SEARCH_SUCCESS = "SECTION_INFO_SEARCH_SUCCESS";

export const TOGGLE_CHECK = "TOGGLE_CHECK";

export const ADD_CART_ITEM = "ADD_CART_ITEM";
export const REMOVE_CART_ITEM = "REMOVE_CART_ITEM";
export const CHANGE_SORT_TYPE = "CHANGE_SORT_TYPE";

// Backend accounts integration
export const UPDATE_SCHEDULES = "UPDATE_SCHEDULES";
export const CREATION_SUCCESSFUL = "CREATION_SUCCESSFUL";
export const MARK_SCHEDULE_SYNCED = "MARK_SCHEDULE_SYNCED";
export const MARK_CART_SYNCED = "MARK_CART_SYNCED";
export const DELETION_ATTEMPT_FAILED = "DELETION_ATTEMPT_FAILED";
export const DELETION_ATTEMPT_SUCCEEDED = "DELETION_ATTEMPT_SUCCEEDED";
export const ATTEMPT_DELETION = "ATTEMPT_DELETION";
export const ATTEMPT_SCHEDULE_CREATION = "ATTEMPT_SCHEDULE_CREATION";
export const UNSUCCESSFUL_SCHEDULE_CREATION = "UNSUCCESSFUL_SCHEDULE_CREATION";

export const markScheduleSynced = (scheduleName) => ({
    scheduleName,
    type: MARK_SCHEDULE_SYNCED,
});

export const markCartSynced = () => ({
    type: MARK_CART_SYNCED,
});

const doAPIRequest = (path, options = {}) => fetch(`/api/plan${path}`, options);

export const duplicateSchedule = (scheduleName) => ({
    type: DUPLICATE_SCHEDULE,
    scheduleName,
});

export const deleteSchedule = (scheduleName) => ({
    type: DELETE_SCHEDULE,
    scheduleName,
});

export const renameSchedule = (oldName, newName) => ({
    type: RENAME_SCHEDULE,
    oldName,
    newName,
});

export const changeSchedule = (scheduleId) => ({
    type: CHANGE_SCHEDULE,
    scheduleId,
});

export const addSchedItem = (section) => ({
    type: ADD_SCHED_ITEM,
    section,
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

export const enforceSemester = (semester) => ({
    type: ENFORCE_SEMESTER,
    semester,
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

export const createScheduleOnFrontend = (scheduleName) => ({
    type: CREATE_SCHEDULE,
    scheduleName,
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

export const loadRequirements = () => (dispatch) =>
    fetch("/api/courses/current/requirements/").then(
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
    let queryString = `/api/courses/current/search/courses/?search=${filterData.searchString}`;

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
    const filterFields = ["difficulty", "course_quality", "instructor_quality"];
    const defaultFilters = [
        [0, 4],
        [0, 4],
        [0, 4],
        [0.5, 2],
    ];
    for (let i = 0; i < filterFields.length; i += 1) {
        if (
            filterData[filterFields[i]] &&
            JSON.stringify(filterData[filterFields[i]]) !==
                JSON.stringify(defaultFilters[i])
        ) {
            const filterRange = filterData[filterFields[i]];
            queryString += `&${filterFields[i]}=${filterRange[0]}-${filterRange[1]}`;
        }
    }

    // Checkbox Filters
    const checkboxFields = ["cu", "activity"];
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
                queryString += `&${checkboxFields[i]}=${applied[0]}`;
                for (let j = 1; j < applied.length; j += 1) {
                    queryString += `,${applied[j]}`;
                }
            }
        }
    }

    return queryString;
}

const courseSearch = (_, filterData) => fetch(buildCourseSearchUrl(filterData));

const debouncedCourseSearch = AwesomeDebouncePromise(courseSearch, 500);

export function fetchCourseSearch(filterData) {
    return (dispatch) => {
        console.log("in fetchCourseSearch ", filterData);
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
    return `/api/courses/current/search/courses/${searchData.param}`;
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

export function clearFilter(propertyName) {
    return {
        type: CLEAR_FILTER,
        propertyName,
    };
}

export const deletionAttemptFailed = (deletedScheduleId) => ({
    type: DELETION_ATTEMPT_FAILED,
    deletedScheduleId,
});

export const deletionSuccessful = (deletedScheduleId) => ({
    type: DELETION_ATTEMPT_SUCCEEDED,
    deletedScheduleId,
});

export const creationUnsuccessful = (createdScheduleName) => ({
    type: UNSUCCESSFUL_SCHEDULE_CREATION,
    scheduleName: createdScheduleName,
});

export const creationAttempted = (createdScheduleName) => ({
    type: UNSUCCESSFUL_SCHEDULE_CREATION,
    scheduleName: createdScheduleName,
});

export const attemptDeletion = (deletedScheduleId) => ({
    type: ATTEMPT_DELETION,
    deletedScheduleId,
});

export function clearAll() {
    return {
        type: CLEAR_ALL,
    };
}

export const updateSchedules = (schedulesFromBackend) => ({
    type: UPDATE_SCHEDULES,
    schedulesFromBackend,
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

export function fetchCourseDetails(courseId) {
    return (dispatch) => {
        dispatch(updateCourseInfoRequest());
        fetch(`/api/courses/current/search/courses/${courseId}`)
            .then((res) => res.json())
            .then((course) => dispatch(updateCourseInfo(course)))
            .catch((error) => dispatch(sectionInfoSearchError(error)));
    };
}

/**
 * Pulls schedules from the backend
 * If the cart isn't included, it creates a cart
 * @param cart The courses in the cart
 * @param shouldInitCart Whether to initialize the cart
 * @param onComplete The function to call when initialization has been completed (with the schedules
 * from the backend)
 * @returns {Function}
 */
export const fetchBackendSchedulesAndInitializeCart = (
    cart,
    shouldInitCart,
    onComplete = () => null
) => (dispatch) => {
    doAPIRequest("/schedules/")
        .then((res) => res.json())
        .then((schedules) => {
            if (schedules) {
                dispatch(updateSchedules(schedules));
            }
            // if the cart doesn't exist on the backend, create it
            if (
                shouldInitCart &&
                !schedules.reduce(
                    (acc, { name }) => acc || name === "cart",
                    false
                )
            ) {
                dispatch(createScheduleOnBackend("cart", cart));
            }
            onComplete(schedules);
        })
        // eslint-disable-next-line no-console
        .catch((error) => console.log(error, "Not logged in"));
};

export const creationSuccessful = (name, id) => ({
    type: CREATION_SUCCESSFUL,
    name,
    id,
});

/**
 * Updates a schedule on the backend
 * Skips if the id is not yet initialized for the schedule
 * Once the schedule has been updated, the schedule is marked as updated locally
 * @param name The name of the schedule
 * @param schedule The schedule object
 */
export const updateScheduleOnBackend = (name, schedule) => (dispatch) => {
    const { id } = schedule;
    if (!id || schedule.backendCreationState) {
        return;
    }
    const updatedScheduleObj = {
        ...schedule,
        name,
        sections: schedule.meetings,
    };
    doAPIRequest(`/schedules/${id}/`, {
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
        fetch(buildSectionInfoSearchUrl(searchData)).then(
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
export const createScheduleOnBackend = (name, sections) => (dispatch) => {
    dispatch(creationAttempted(name));
    rateLimitedFetch("/schedules/", {
        method: "POST",
        credentials: "include",
        mode: "same-origin",
        headers: {
            Accept: "application/json",
            "Content-Type": "application/json",
            "X-CSRFToken": getCsrf(),
        },
        body: JSON.stringify({
            name,
            sections,
        }),
    })
        .then((response) => response.json())
        .then(({ id }) => {
            if (id) {
                dispatch(creationSuccessful(name, id));
            }
        })
        .catch(({ message }) => {
            if (message !== "minDelayNotElapsed") {
                dispatch(creationUnsuccessful(name));
            }
        });
};

export const deleteScheduleOnBackend = (deletedScheduleId) => (dispatch) => {
    dispatch(attemptDeletion(deletedScheduleId));
    rateLimitedFetch(`/schedules/${deletedScheduleId}/`, {
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
            dispatch(deletionSuccessful(deletedScheduleId));
        })
        .catch(({ message }) => {
            if (message !== "minDelayNotElapsed") {
                dispatch(deletionAttemptFailed(deletedScheduleId));
            }
        });
};

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

export const changeSortType = (sortMode) => ({
    type: CHANGE_SORT_TYPE,
    sortMode,
});
