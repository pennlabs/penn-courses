import {
    LOAD_REQUIREMENTS, ADD_SCHOOL_REQ, REM_SCHOOL_REQ, UPDATE_SEARCH_TEXT,
    UPDATE_RANGE_FILTER, CLEAR_FILTER, CLEAR_ALL, UPDATE_CHECKBOX_FILTER
} from "../actions";

export const initialState = {
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
        difficulty: [0, 4],
        course_quality: [0, 4],
        instructor_quality: [0, 4],
        time: null,
        type: {
            LAB: 0,
            REC: 0,
            SEM: 0,
            STU: 0,
        },
        cu: {
            0.5: 0,
            1: 0,
            1.5: 0,
        },
    },
    defaultReqs: null,
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
                defaultReqs: action.selObj,
            };

        case UPDATE_SEARCH_TEXT:
            return {
                ...state,
                filterData: {
                    ...state.filterData,
                    searchString: action.s,
                },
            };

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

        case UPDATE_RANGE_FILTER:
            return {
                ...state,
                filterData: {
                    ...state.filterData,
                    [action.field]: action.values,
                },
            };

        case UPDATE_CHECKBOX_FILTER:
            return {
                ...state,
                filterData: {
                    ...state.filterData,
                    [action.field]: {
                        ...state.filterData[action.field],
                        [action.value]: action.toggleState,
                    },
                },
            };

        case CLEAR_FILTER:
            if (action.propertyName === "selectedReq") {
                return {
                    ...state,
                    filterData: {
                        ...state.filterData,
                        selectedReq: state.defaultReqs,
                    },
                };
            }

            return {
                ...state,
                filterData: {
                    ...state.filterData,
                    [action.propertyName]: initialState.filterData[action.propertyName],
                },
            };

        case CLEAR_ALL:
            return {
                ...initialState,
                filterData: {
                    ...initialState.filterData,
                    searchString: state.filterData.searchString,
                    selectedReq: state.defaultReqs,
                },
                defaultReqs: state.defaultReqs,
                schoolReq: state.schoolReq,
            };
        default:
            return state;
    }
};
