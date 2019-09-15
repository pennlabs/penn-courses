import {ADD_CART_ITEM, TOGGLE_CHECK} from "../actions";

const initialState = {cartCourses: []};

export const cart = (state = initialState, action) => {
    const {cartCourses} = state;
    switch (action.type) {
        case TOGGLE_CHECK:
            const {courseId} = action;
            return {
                ...state,
                cartCourses: cartCourses.map(course => ({
                    ...course,
                    checked: course.section.id === courseId ? !course.checked : course.checked
                }))
            };
        case ADD_CART_ITEM:
            const {section} = action;
            return {...state, cartCourses: [...cartCourses, {section, checked: false}]};
        default:
            return state
    }
};