import {
    LOAD_ATTRIBUTES,
    ADD_SCHOOL_ATTR,
    REM_SCHOOL_ATTR,
    UPDATE_SEARCH_TEXT,
    UPDATE_RANGE_FILTER,
    CLEAR_FILTER,
    CLEAR_ALL,
    UPDATE_CHECKBOX_FILTER,
    UPDATE_BUTTON_FILTER,
} from "../actions";

export const initialState = {
    schoolAttrs: {
        SAS: [],
        SEAS: [],
        NURS: [],
        WH: [],
        LPS: [],
        DSGN: [],
        GSE: [],
        LAW: [],
        MED: [],
        VET: [],
        MODE: [],
    },
    filterData: {
        searchString: "",
        searchType: "courseIDSearch",
        selectedAttrs: null,
        difficulty: [0, 4],
        course_quality: [0, 4],
        instructor_quality: [0, 4],
        activity: {
            LAB: false,
            REC: false,
            SEM: false,
            STU: false,
        },
        cu: {
            0.5: false,
            1: false,
            1.5: false,
        },
        days: {
            M: true,
            T: true,
            W: true,
            R: true,
            F: true,
            S: true,
            U: true,
        },
        time: [1.5, 17],
        "schedule-fit": -1,
        is_open: 0,
    },
    defaultAttrs: null,
};

export const filters = (state = initialState, action) => {
    switch (action.type) {
        case LOAD_ATTRIBUTES:
            return {
                ...state,
                schoolAttrs: action.obj,
                filterData: {
                    ...state.filterData,
                    selectedAttrs: action.selObj,
                },
                defaultAttrs: action.selObj,
            };

        case UPDATE_SEARCH_TEXT:
            return {
                ...state,
                filterData: {
                    ...state.filterData,
                    searchString: action.s,
                },
            };

        case ADD_SCHOOL_ATTR:
            return {
                ...state,
                filterData: {
                    ...state.filterData,
                    selectedAttrs: {
                        ...state.filterData.selectedAttrs,
                        [action.attrCode]: 1,
                    },
                },
            };

        case REM_SCHOOL_ATTR:
            return {
                ...state,
                filterData: {
                    ...state.filterData,
                    selectedAttrs: {
                        ...state.filterData.selectedAttrs,
                        [action.attrCode]: 0,
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

        // for filter buttons that toggle
        case UPDATE_BUTTON_FILTER:
            return {
                ...state,
                filterData: {
                    ...state.filterData,
                    [action.field]: action.value,
                },
            };

        case CLEAR_FILTER:
            if (action.propertyName === "selectedAttrs") {
                return {
                    ...state,
                    filterData: {
                        ...state.filterData,
                        selectedAttrs: state.defaultAttrs,
                    },
                };
            }

            return {
                ...state,
                filterData: {
                    ...state.filterData,
                    [action.propertyName]:
                        initialState.filterData[action.propertyName],
                },
            };

        case CLEAR_ALL:
            return {
                ...initialState,
                filterData: {
                    ...initialState.filterData,
                    searchString: state.filterData.searchString,
                    selectedAttrs: state.defaultAttrs,
                },
                defaultAttrs: state.defaultAttrs,
                schoolAttrs: state.schoolAttrs,
            };
        default:
            return state;
    }
};
