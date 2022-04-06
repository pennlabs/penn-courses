import {
    COURSE_SEARCH_ERROR,
    OPEN_SECTION_INFO,
    UPDATE_SEARCH,
    UPDATE_SECTIONS,
    UPDATE_COURSE_INFO_SUCCESS,
    UPDATE_COURSE_INFO_REQUEST,
    UPDATE_SEARCH_REQUEST,
    UPDATE_SCROLL_POS,
    CHANGE_SORT_TYPE,
} from "../actions";

// This file contains the reducers for everything related to sections and courses

// The state contains the following:
// 1. The list of sections displayed in the sections display
// 2. The list of search results displayed in the search results display
// 3. The SectionInfo object displayed under the sections list
// 4. Whether to display the search filter
// 5. The coordinates of the search filter button
const initialState = {
    course: null,
    sections: [],
    searchResults: [],
    sectionInfo: undefined,
    courseInfoLoading: false,
    searchInfoLoading: false,
    sortMode: "Name",
    scrollPos: 0,
};

export const sections = (state = initialState, { type, ...action }) => {
    switch (type) {
        case CHANGE_SORT_TYPE:
            return {
                ...state,
                sortMode: action.sortMode,
            };
        case UPDATE_COURSE_INFO_SUCCESS:
            return {
                ...state,
                course: action.course,
                courseInfoLoading: false,
            };
        case UPDATE_COURSE_INFO_REQUEST:
            return {
                ...state,
                courseInfoLoading: true,
            };
        case UPDATE_SEARCH_REQUEST:
            return {
                ...state,
                searchInfoLoading: true,
            };
        case OPEN_SECTION_INFO:
            return {
                ...state,
                sectionInfo: action.sectionInfo,
            };
        case UPDATE_SECTIONS:
            return {
                ...state,
                sections: action.sections,
            };
        case UPDATE_SEARCH:
            return {
                ...state,
                searchResults: action.searchResults,
                sections: undefined,
                course: null,
                searchInfoLoading: false,
            };
        case UPDATE_SCROLL_POS: {
            const { scrollPos = 0 } = action;
            return {
                ...state,
                scrollPos,
            };
        }
        case COURSE_SEARCH_ERROR:
            return state;
        default:
            return state;
    }
};
