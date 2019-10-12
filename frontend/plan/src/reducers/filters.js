import {
    LOAD_REQUIREMENTS, ADD_SCHOOL_REQ, REM_SCHOOL_REQ
} from "../actions";

const initialState = {
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

export const filters = (state = initialState, action) => {
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

        case ADD_SCHOOL_REQ:
            return {
                ...state,
                filterSearch: {
                    ...state.filterSearch,
                    selectedReq: {
                        ...state.filterSearch.selectedReq,
                        [action.reqID]: 1,
                    },
                },
            };

        case REM_SCHOOL_REQ:
            return {
                ...state,
                filterSearch: {
                    ...state.filterSearch,
                    selectedReq: {
                        ...state.filterSearch.selectedReq,
                        [action.reqID]: 0,
                    },
                },
            };

        default:
            return state;
    }
}