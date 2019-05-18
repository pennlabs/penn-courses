import React from "react";
import GenericModal from "./generic_modal_container";
// import {validateScheduleName} from "../schedule/schedule_name_validation";

export const CLEAR_SCHEDULE_MODAL_NAME = "clear_schedule_modal";


function ClearScheduleModalInterior({ modalActionState, clearSchedule, close }) {
    if (modalActionState === "success") {
        clearSchedule();
        close();
    }
    return null;
}

export default function ClearScheduleModal() {
    return (
        <GenericModal
            modalName={CLEAR_SCHEDULE_MODAL_NAME}
            title="Clear Schedule?"
            containedContent={[<ClearScheduleModalInterior />]}
            successButton="Ok"
        />
    );
}
