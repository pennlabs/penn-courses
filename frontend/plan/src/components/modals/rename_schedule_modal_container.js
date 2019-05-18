/* eslint-disable react/prop-types */
import React, { Component } from "react";
import GenericModal from "./generic_modal_container";
import { validateScheduleName } from "../schedule/schedule_name_validation";

export const RENAME_SCHEDULE_MODAL_NAME = "rename_schedule_modal";


class RenameScheduleModalInterior extends Component {
    constructor(props) {
        super(props);
        this.state = { currentName: "" };
    }

    render() {
        const {
            currentName,
        } = this.state;

        const {
            existingScheduleNames,
            modalActionState,
            renameSchedule,
            close,
            triggerModalAction,
        } = this.props;
        let newScheduleNameInput = null;
        const storeInputRef = (ref) => {
            newScheduleNameInput = ref;
        };
        const feedbackString = validateScheduleName(currentName, existingScheduleNames);
        if (modalActionState === "success") {
            if (feedbackString.length === 0) {
                renameSchedule(currentName);
                close();
            } else {
                triggerModalAction(null);
            }
        }
        return (
            <div>
                <input
                    type="text"
                    ref={storeInputRef}
                    onKeyUp={(e) => {
                        this.setState({ currentName: newScheduleNameInput.value });
                        if (e.key === "Enter") {
                            triggerModalAction("success");
                        }
                    }}
                />
                <div>
                    {feedbackString}
                </div>
            </div>
        );
    }
}

export default function RenameScheduleModal() {
    return (
        <GenericModal
            modalName={RENAME_SCHEDULE_MODAL_NAME}
            title="Rename Schedule"
            containedContent={[<RenameScheduleModalInterior />]}
            successButton="Ok"
        />
    );
}
