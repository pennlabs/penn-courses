import { CLOSE_MODAL, OPEN_MODAL } from "../actions";

// this file contains the reducers for modals

const initialState = {
    modalTitle: null,
    modalKey: null,
    modalProps: null,
};

export const modals = (state = initialState, action) => {
    switch (action.type) {
        case OPEN_MODAL:
            return {
                ...state,
                modalTitle: action.modalTitle,
                modalKey: action.modalKey,
                modalProps: action.modalProps,
            };
        case CLOSE_MODAL:
            return {
                ...state,
                modalTitle: null,
                modalKey: null,
                modalProps: null,
            };
        default:
            return state;
    }
};
