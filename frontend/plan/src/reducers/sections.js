import {
    COURSE_SEARCH_ERROR,
    OPEN_SECTION_INFO,
    UPDATE_SEARCH,
    UPDATE_SECTIONS,
    UPDATE_COURSE_INFO,
    LOAD_REQUIREMENTS
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
    schoolReq: {
        SAS: [],
        SEAS: [],
        NURS: [],
        WH: [],
    },
    filterSearch: {
        selectedReq: null,
        difficulty: null,
        quality: null,
        time: null,
        type: null,
        cu: null,
    },
};

export const sections = (state = initialState, action) => {
    switch (action.type) {
        case LOAD_REQUIREMENTS:
            return {
                ...state,
                schoolReq: action.obj,
                filterSearch: {
                    ...state.filterSearch,
                    selectedReq: action.selObj,
                },
            };
        case UPDATE_COURSE_INFO:
            return {
                ...state,
                course: action.course,
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
            // console.log("UPDATING SEARCH");
            return {
                ...state,
                searchResults: action.searchResults,
                sections: undefined,
            };

        case COURSE_SEARCH_ERROR:
            // console.log(action.error);
            return state;
        default:
            return state;
    }
};
