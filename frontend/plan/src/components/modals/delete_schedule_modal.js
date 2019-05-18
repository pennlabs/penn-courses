/* eslint-disable react/prop-types */
import React from "react";
import GenericModal from "./generic_modal_container";

export const DELETE_SCHEDULE_MODAL_NAME = "delete_schedule_modal";


function DeleteScheduleModalInterior({
    existingScheduleNames, modalActionState,
    deleteSchedule, close, restoreAction, clearAction,
}) {
    if (existingScheduleNames.length > 1) {
        if (modalActionState === "success") {
            deleteSchedule();
            close();
        }
        restoreAction();
        return <div>Are you sure you want to delete?</div>;
    }

    clearAction();
    return <div>You can&apos;t delete your only schedule.</div>;
}

export default function DeleteScheduleModal() {
    return (
        <GenericModal
            modalName="delete_schedule_modal"
            title="Delete Schedule"
            containedContent={[<DeleteScheduleModalInterior />]}
            successButton="ok"
        />
    );
}
