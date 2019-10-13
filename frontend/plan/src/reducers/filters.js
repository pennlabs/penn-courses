import {
    LOAD_REQUIREMENTS, ADD_SCHOOL_REQ, REM_SCHOOL_REQ, UPDATE_SEARCH_TEXT
} from "../actions";

const initialState = {
    schoolReq: {
        SAS: [],
        SEAS: [],
        NURS: [],
        WH: [],
    },
    filterData: {
        searchString: "",
        searchType: "courseIDSearch",
        selectedReq: null,
        difficulty: null,
        quality: null,
        time: null,
        type: null,
        cu: null,
    },
};

export const filters = (state = initialState, action) => {
    switch (action.type) {
        case LOAD_REQUIREMENTS:
            return {
                ...state,
                schoolReq: action.obj,
                filterData: {
                    ...state.filterData,
                    selectedReq: action.selObj,
                },
            };
        
        case UPDATE_SEARCH_TEXT:
            return {
                ...state,
                filterData: {
                    ...state.filterData,
                    searchString: action.s,
                }
            }

        case ADD_SCHOOL_REQ:
            return {
                ...state,
                filterData: {
                    ...state.filterData,
                    selectedReq: {
                        ...state.filterData.selectedReq,
                        [action.reqID]: 1,
                    },
                },
            };

        case REM_SCHOOL_REQ:
            return {
                ...state,
                filterData: {
                    ...state.filterData,
                    selectedReq: {
                        ...state.filterData.selectedReq,
                        [action.reqID]: 0,
                    },
                },
            };

        default:
            return state;
    }
}