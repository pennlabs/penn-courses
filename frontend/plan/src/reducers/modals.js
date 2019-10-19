import { CLOSE_MODAL, OPEN_MODAL } from "../actions";

// this file contains the reducers for modals

/* the modal state contains the contents of the modal
 being shown (as an object with a modal name and a title) or null */
const initialState = {
    modal: null,
};

export const modals = (state = initialState, action) => {
    switch (action.type) {
        case OPEN_MODAL:
            return {
                ...state,
                modal: action.modal,
            };
        case CLOSE_MODAL:
            return {
                ...state,
                modal: null,
            };
        default:
            return state;
    }
};
