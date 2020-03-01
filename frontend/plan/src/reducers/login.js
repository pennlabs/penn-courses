import { LOGIN, LOGOUT } from "../actions/login";

export const login = (state = { user: null }, action) => {
    switch (action.type) {
        case LOGOUT:
            return {
                ...state,
                user: null,
            };
        case LOGIN:
            return {
                ...state,
                user: action.user,
            };
        default:
            return { ...state };
    }
};
