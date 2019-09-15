import {ADD_CART_ITEM} from "../actions";

const initialState = {cartCourses: []};

export const cart = (state = initialState, action) => {
    switch (action.type) {
        case ADD_CART_ITEM:
            const {cartCourses} = state;
            const {section} = action;
            return {...state, cartCourses: [...cartCourses, section]};
        default:
            return state
    }
};