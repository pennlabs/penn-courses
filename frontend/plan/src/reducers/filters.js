import {
    LOAD_REQUIREMENTS
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
        default:
            return state;
    }
}