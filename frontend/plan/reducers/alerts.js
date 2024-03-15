import {
    ADD_ALERT_ITEM,
    REMOVE_ALERT_ITEM,
    UPDATE_CONTACT_INFO,
} from "../actions";

const initialState = {
    alertedCourses: [],
    contactInfo: {
        email: "",
        phone: "",
    },
};
export const alerts = (state = initialState, action) => {
    switch (action.type) {
        case ADD_ALERT_ITEM:
            return {
                ...state,
                alertedCourses: [...state.alertedCourses, action.alert],
            };
        case REMOVE_ALERT_ITEM:
            return {
                ...state,
                alertedCourses: state.alertedCourses.filter(
                    ({ section }) => section !== action.sectionId
                ),
            };
        case UPDATE_CONTACT_INFO:
            return {
                ...state,
                contactInfo: action.contactInfo,
            };
        default:
            return {
                ...state,
            };
    }
};
