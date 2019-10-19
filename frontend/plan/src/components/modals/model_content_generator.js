import React from "react";
import { renameSchedule } from "../../actions";
import RenameScheduleModalInterior from "./RenameScheduleModalInterior";

/**
 * Generates a modal interior component based on the redux state.
 * The entire redux state is given because some modals may need to
 * make use of redux state besides the modal-specific state (e.g., which schedules exist already).
 *
 * Each component that is returned will be reconstructed with access to particular actions it needs
 * to be able to dispatch
 * @param reduxState
 * @returns A component
 */
export const generateModalInterior = reduxState => {
    switch (reduxState.modals.modalKey) {
        case "RENAME_SCHEDULE":
            return <RenameScheduleModalInterior
                usedScheduleNames={Object.keys(reduxState.schedule.schedules)}/>;
        default:
            return null;
    }
};

/**
 * Returns the actions for the modal with the given key
 * @param dispatch The redux dispatch function
 * @param modalKey The key for the modal
 * @param modalProps Any additional information needed to generate the modal
 */
export const generateModalActions = (dispatch, modalKey, modalProps) => {
    switch (modalKey) {
        case "RENAME_SCHEDULE":
            return { renameSchedule: (newName) =>
                    dispatch(renameSchedule(modalProps.scheduleName, newName)), };
        default:
            return {};

    }
};
