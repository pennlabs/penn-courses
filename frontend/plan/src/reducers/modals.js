import { CLOSE_MODAL, OPEN_MODAL, ACTION_BUTTON_PRESSED } from "../actions";

// this file contains the reducers for modals

// the modal state contains the name of the modal being shown and a string representing the most
// recent action triggered by the modal
const initialState = {
    modalShown: null,
    modalAction: null,
};

export const modals = (state = initialState, action) => {
    switch (action.type) {
        case OPEN_MODAL:
            return {
                ...state,
                modalShown: action.modalShown,
            };
        case CLOSE_MODAL:
            return {
                ...state,
                modalShown: null,
                modalAction: null,
            };
        case ACTION_BUTTON_PRESSED:
            return {
                ...state,
                modalAction: action.modalAction,
            };
        default:
            return state;
    }
};
