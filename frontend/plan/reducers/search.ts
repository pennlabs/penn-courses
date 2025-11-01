import { UPDATE_SEARCH_FILTER, CLEAR_ALL, UPDATE_SEARCH_TEXT, CLEAR_FILTER } from "../actions";
import { AdvancedSearchData } from "../types";

export const initialState = {
    query: "",
    filters: {
        op: "AND",
        children: [],
    }
} as AdvancedSearchData;

export const search = (state = initialState, action: any): AdvancedSearchData => {
    switch (action.type) {
        case UPDATE_SEARCH_TEXT:
            return {
                ...state,
                query: action.s,
            };
        case UPDATE_SEARCH_FILTER:
            return {
                ...state,
                filters: action.filters,
            }
        case CLEAR_ALL:
            return initialState;
        default:
            return state;
    }
}