/* eslint-disable react/prop-types */
import React, { Component } from "react";
import GenericModal from "./generic_modal_container";
import { validateScheduleName } from "../schedule/schedule_name_validation";

export const NEW_SCHEDULE_MODAL_NAME = "new_schedule_modal";


class NewScheduleModalInterior extends Component {
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
            createNewSchedule,
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
                createNewSchedule(currentName);
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

export default function NewScheduleModal() {
    return (
        <GenericModal
            modalName="new_schedule_modal"
            title="New Schedule"
            containedContent={[<NewScheduleModalInterior />]}
            successButton="Ok"
        />
    );
}
