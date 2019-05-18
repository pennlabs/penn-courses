import {
    COURSE_SEARCH_ERROR,
    OPEN_SECTION_INFO,
    TOGGLE_SEARCH_FILTER,
    UPDATE_SEARCH,
    UPDATE_SECTIONS
} from "../actions";
import { sectionsDataA } from "../sections_data";

// This file contains the reducers for everything related to sections and courses

// The state contains the following:
// 1. The list of sections displayed in the sections display
// 2. The list of search results displayed in the search results display
// 3. The SectionInfo object displayed under the sections list
// 4. Whether to display the search filter
// 5. The coordinates of the search filter button
const initialState = {
    sections: sectionsDataA,
    searchResults: [],
    sectionInfo: undefined,
    showSearchFilter: false,
    searchFilterLocation: undefined,
};

export const sections = (state = initialState, action) => {
    switch (action.type) {
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
        case TOGGLE_SEARCH_FILTER:
            return {
                ...state,
                showSearchFilter: !state.showSearchFilter,
                showSearchFilterLocation: action.location,
            };
        case COURSE_SEARCH_ERROR:
            // console.log(action.error);
            return state;
        default:
            return state;
    }
};
