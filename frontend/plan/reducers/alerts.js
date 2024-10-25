import {
    REGISTER_ALERT_ITEM,
    DELETE_ALERT_ITEM,
    UPDATE_CONTACT_INFO,
    REACTIVATE_ALERT_ITEM,
    DEACTIVATE_ALERT_ITEM,
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
        case REGISTER_ALERT_ITEM:
            return {
                ...state,
                alertedCourses: [...state.alertedCourses, action.alert],
            };
        case REACTIVATE_ALERT_ITEM:
            return {
                ...state,
                alertedCourses: state.alertedCourses.map((alert) => {
                    if (alert.section === action.sectionId)
                        return { ...alert, cancelled: false };
                    return alert;
                }),
            };
        case DEACTIVATE_ALERT_ITEM:
            return {
                ...state,
                alertedCourses: state.alertedCourses.map((alert) => {
                    if (alert.section === action.sectionId)
                        return { ...alert, cancelled: true };
                    return alert;
                }),
            };
        case DELETE_ALERT_ITEM:
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
