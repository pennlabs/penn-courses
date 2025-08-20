import { ADD_BREAK, REMOVE_BREAK, UPDATE_BREAK } from '../actions';

const initialState = {
    breaks: [],
    loading: false,
};

export const breaks = (state = initialState, { type, ...action }) => {
   switch (type) {
        case ADD_BREAK:
            if (!action.breakItem) {
                return state; // No break item to add
            }
            if (state.breaks.some(b => b.id === action.breakItem.id)) {
                return state; // Break already exists
            }
            return {
                ...state,
                breaks: [...state.breaks, action.breakItem],
            };
        case REMOVE_BREAK:
            return {
                ...state,
                breaks: state.breaks.filter((b) => b.id !== action.id),
            };
        case UPDATE_BREAK:
            return {
                ...state,
                breaks: state.breaks.map((b) =>
                    b.id === action.breakItem.id ? action.breakItem : b
                ),
            };
        default:
            return {
                ...state,
            };
    } 
}
