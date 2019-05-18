import fetch from "cross-fetch";

export const UPDATE_SEARCH = "UPDATE_SEARCH";
export const UPDATE_SECTIONS = "UPDATE_SECTIONS";

export const OPEN_SECTION_INFO = "OPEN_SECTION_INFO";
export const CHANGE_SCHEDULE = "CHANGE_SCHEDULE";
export const CREATE_SCHEDULE = "CREATE_SCHEDULE";


export const TOGGLE_SEARCH_FILTER = "TOGGLE_SEARCH_FILTER";
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
export const REQUEST_SEARCH = "REQUEST_SEARCH";

export const SECTION_INFO_SEARCH_ERROR = "SECTION_INFO_SEARCH_ERROR";
export const SECTION_INFO_SEARCH_LOADING = "SECTION_INFO_SEARCH_LOADING";
export const SECTION_INFO_SEARCH_SUCCESS = "SECTION_INFO_SEARCH_SUCCESS";
export const REQUEST_SECTION_INFO_SEARCH = "REQUEST_SECTION_INFO_SEARCH";


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

export const addSchedItem = courseObj => (
    {
        type: ADD_SCHED_ITEM,
        courseObj,
    }
);

export const removeSchedItem = idDashed => (
    {
        type: REMOVE_SCHED_ITEM,
        idDashed,
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

export const createSchedule = scheduleName => (
    {
        type: CREATE_SCHEDULE,
        scheduleName,
    }
);

export const toggleSearchFilterShown = location => (
    {
        type: TOGGLE_SEARCH_FILTER,
        location,
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

export function requestSearch(searchData) {
    return {
        type: REQUEST_SEARCH,
        searchData,
    };
}


export function requestSectionInfo(courseData) {
    return {
        type: REQUEST_SECTION_INFO_SEARCH,
        courseData,
    };
}


const preprocessCourseSearchData = (searchData) => {
    const data = searchData;
    data.param = data.param.replace(/\s/, "");
    if (/\d/.test(searchData.param)) {
        data.resultType = "numbSearch";
    } else {
        data.resultType = "deptSearch";
    }
    return data;
};

const preprocessSectionSearchData = (searchData) => {
    const data = searchData;
    data.param = searchData.param.toLowerCase().replace(/\s/, "");
    data.resultType = "sectSearch";
    return data;
};


function buildCourseSearchUrl(initSearchData) {
    let searchData = initSearchData;
    searchData = preprocessCourseSearchData(searchData);
    const url = `/Search?searchType=${searchData.searchType}&resultType=${searchData.resultType}&searchParam=${searchData.param}`;
    // console.log(url);
    return url;
}

function buildSectionInfoSearchUrl(initCourseData) {
    let searchData = initCourseData;
    searchData = preprocessSectionSearchData(searchData);
    const url = `/Search?searchType=${searchData.searchType}&resultType=${searchData.resultType}&searchParam=${searchData.param}`;
    // console.log(url);
    return url;
}

const processSearchData = searchData => searchData.map((item) => {
    const newItem = item;
    const qFrac = newItem.revs.cQ / 4;
    const dFrac = newItem.revs.cD / 4;
    const iFrac = newItem.revs.cI / 4;
    newItem.pcrQShade = (qFrac ** 3) * 2; // This is the opacity of the PCR block
    newItem.pcrDShade = (dFrac ** 3) * 2;
    newItem.pcrIShade = (iFrac ** 3) * 2;
    if (qFrac < 0.50) {
        newItem.pcrQColor = "black";
    } else {
        newItem.pcrQColor = "white";
    } // It's hard to see white text on a light background
    if (dFrac < 0.50) {
        newItem.pcrDColor = "black";
    } else {
        newItem.pcrDColor = "white";
    }
    if (iFrac < 0.50) {
        newItem.pcrIColor = "black";
    } else {
        newItem.pcrIColor = "white";
    }
    // This is my way of calculating if a class is "good and easy."
    // R > 1 means good and easy, < 1 means bad and hard
    newItem.revs.QDratio = newItem.revs.cQ - newItem.revs.cD;

    // Cleanup to keep incomplete data on the bottom;
    if (Number.isNaN(item.revs.QDratio) || !Number.isFinite(item.revs.QDratio)) {
        newItem.revs.QDratio = 0;
    }
    // the rating as a string - let's us make the actual rating
    // something else and still show the correct number
    newItem.revs.cQT = newItem.revs.cQ.toFixed(2);
    if (newItem.revs.cQ === 0) {
        newItem.revs.cQT = "";
    }
    newItem.revs.cDT = newItem.revs.cD.toFixed(2);
    if (newItem.revs.cD === 0) {
        newItem.revs.cDT = "";
        newItem.revs.QDratio = -100;
        newItem.revs.cD = 100;
    }
    return newItem;
});


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

export function fetchCourseSearch(searchData) {
    return (dispatch) => {
        dispatch(requestSearch(searchData));
        return fetch(buildCourseSearchUrl(searchData)).then(
            response => response.json().then(
                json => dispatch(updateSearch(processSearchData(json))),
                error => dispatch(courseSearchError(error)),
            ),
            error => dispatch(courseSearchError(error)),
        );
    };
}

export function fetchSectionInfo(searchData) {
    return (dispatch) => {
        dispatch(requestSectionInfo(searchData));
        return fetch(buildSectionInfoSearchUrl(searchData)).then(
            response => response.json().then(
                json => dispatch(updateSectionInfo(json)),
                error => dispatch(sectionInfoSearchError(error)),
            ),
            error => dispatch(sectionInfoSearchError(error)),
        );
    };
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
