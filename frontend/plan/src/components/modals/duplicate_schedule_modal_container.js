/* eslint-disable react/prop-types */
import React, { Component } from "react";
import GenericModal from "./generic_modal_container";
import { validateScheduleName } from "../schedule/schedule_name_validation";

export const DUPLICATE_SCHEDULE_MODAL_NAME = "duplicate_schedule_modal";


class DuplicateScheduleModalInterior extends Component {
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
            close,
            duplicateSchedule,
            triggerModalAction,
        } = this.props;

        let newScheduleNameInput = null;
        const storeInputRef = (ref) => {
            newScheduleNameInput = ref;
        };
        const feedbackString = validateScheduleName(currentName, existingScheduleNames);
        if (modalActionState === "success") {
            if (feedbackString.length === 0) {
                duplicateSchedule(currentName);
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

export default function DuplicateScheduleModal() {
    return (
        <GenericModal
            modalName={DUPLICATE_SCHEDULE_MODAL_NAME}
            title="Duplicate Schedule"
            containedContent={[<DuplicateScheduleModalInterior />]}
            successButton="Ok"
        />
    );
}
