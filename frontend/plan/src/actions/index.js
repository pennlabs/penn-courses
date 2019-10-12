import fetch from "cross-fetch";

export const UPDATE_SEARCH = "UPDATE_SEARCH";

export const UPDATE_COURSE_INFO = "UPDATE_COURSE_INFO";
export const UPDATE_SECTIONS = "UPDATE_SECTIONS";
export const OPEN_SECTION_INFO = "OPEN_SECTION_INFO";
export const CHANGE_SCHEDULE = "CHANGE_SCHEDULE";
export const CREATE_SCHEDULE = "CREATE_SCHEDULE";

export const OPEN_MODAL = "OPEN_MODAL";
export const CLOSE_MODAL = "CLOSE_MODAL";
export const ACTION_BUTTON_PRESSED = "ACTION_BUTTON_PRESSED";

export const ADD_SCHED_ITEM = "ADD_SCHED_ITEM";
export const REMOVE_SCHED_ITEM = "REMOVE_SCHED_ITEM";
export const DELETE_SCHEDULE = "DELETE_SCHEDULE";
export const RENAME_SCHEDULE = "RENAME_SCHEDULE";
export const DUPLICATE_SCHEDULE = "DUPLICATE_SCHEDULE";
export const CLEAR_SCHEDULE = "CLEAR_SCHEDULE";

export const COURSE_SEARCH_ERROR = "COURSE_SEARCH_ERROR";
export const COURSE_SEARCH_LOADING = "COURSE_SEARCH_LOADING";
export const COURSE_SEARCH_SUCCESS = "COURSE_SEARCH_SUCCESS";

export const LOAD_REQUIREMENTS = "LOAD_REQUIREMENTS";
export const ADD_SCHOOL_REQ = "ADD_SCHOOL_REQ";
export const REM_SCHOOL_REQ = "REM_SCHOOL_REQ";

export const SECTION_INFO_SEARCH_ERROR = "SECTION_INFO_SEARCH_ERROR";
export const SECTION_INFO_SEARCH_LOADING = "SECTION_INFO_SEARCH_LOADING";
export const SECTION_INFO_SEARCH_SUCCESS = "SECTION_INFO_SEARCH_SUCCESS";


export const duplicateSchedule = scheduleName => (
    {
        type: DUPLICATE_SCHEDULE,
        scheduleName,
    }
);

export const deleteSchedule = () => (
    {
        type: DELETE_SCHEDULE,
    }
);

export const renameSchedule = scheduleName => (
    {
        type: RENAME_SCHEDULE,
        scheduleName,
    }
);

export const changeSchedule = scheduleId => (
    {
        type: CHANGE_SCHEDULE,
        scheduleId,
    }
);

export const addSchedItem = section => (
    {
        type: ADD_SCHED_ITEM,
        section,
    }
);

export const removeSchedItem = id => (
    {
        type: REMOVE_SCHED_ITEM,
        id,
    }
);

export const updateSearch = searchResults => (
    {
        type: UPDATE_SEARCH,
        searchResults,
    }
);

export const updateSections = sections => (
    {
        type: UPDATE_SECTIONS,
        sections,
    }
);

export const updateSectionInfo = sectionInfo => (
    {
        type: OPEN_SECTION_INFO,
        sectionInfo,
    }
);

export const updateCourseInfo = course => (
    {
        type: UPDATE_COURSE_INFO,
        course,
    }
);

export const createSchedule = scheduleName => (
    {
        type: CREATE_SCHEDULE,
        scheduleName,
    }
);

export const openModal = modalShown => (
    {
        type: OPEN_MODAL,
        modalShown,
    }
);


export const closeModal = () => (
    {
        type: CLOSE_MODAL,
    }
);

export const triggerModalAction = modalAction => (
    {
        type: ACTION_BUTTON_PRESSED,
        modalAction,
    }
);

export const clearSchedule = () => (
    {
        type: CLEAR_SCHEDULE,
    }
);

export const loadRequirements = () => (
    dispatch => (
        fetch("/requirements")
            .then(
                response => response.json()
                    .then((data) => {
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
                    }, (error) => {
                        // eslint-disable-next-line no-console
                        console.log(error);
                    }),
                (error) => {
                // eslint-disable-next-line no-console
                    console.log(error);
                }
            )
    )
);

function buildCourseSearchUrl(searchData, filterData) {
    let queryString = `/courses/?search=${searchData.param}`;

    // Requirements filter
    const reqs = [];
    for (const key of Object.keys(filterData.selectedReq)) {
        if (filterData.selectedReq[key] === 1) {
            reqs.push(key);
        }
    }

    if (reqs.length > 0) {
        queryString += `&requirement=${reqs[0]}`;
        for (let i = 1; i < reqs.length; i += 1) {
            queryString += `+${reqs[i]}`;
        }
    }

    return queryString;
}

function buildSectionInfoSearchUrl(searchData) {
    return `/courses/${searchData.param}`;
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

export function fetchCourseSearch(searchData, filterData) {
    return dispatch => (
        fetch(buildCourseSearchUrl(searchData, filterData)).then(
            response => response.json().then(
                json => dispatch(updateSearch(json)),
                error => dispatch(courseSearchError(error)),
            ),
            error => dispatch(courseSearchError(error)),
        )
    );
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
    }
}


export function fetchCourseDetails(courseId) {
    return dispatch => (
        fetch(`/courses/${courseId}`)
            .then(res => res.json())
            .then(course => dispatch(updateCourseInfo(course)))
            .catch(error => dispatch(sectionInfoSearchError(error)))
    );
}

export function fetchSectionInfo(searchData) {
    return dispatch => (
        fetch(buildSectionInfoSearchUrl(searchData)).then(
            response => response.json().then(
                (json) => {
                    const info = {
                        id: json.id,
                        description: json.description,
                        crosslistings: json.crosslistings,
                    };
                    const { sections } = json;
                    dispatch(updateCourseInfo(sections, info));
                },
                error => dispatch(sectionInfoSearchError(error)),
            ),
            error => dispatch(sectionInfoSearchError(error)),
        )
    );
}

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
