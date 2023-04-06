import React, { useEffect, useState } from "react";
import styled from "styled-components";
import { connect } from "react-redux";
import { ThunkDispatch } from "redux-thunk";

import {
    removeSchedItem,
    fetchCourseDetails,
    changeSchedule,
    createScheduleOnBackend,
    deleteScheduleOnBackend,
    openModal,
    setStateReadOnly,
    setCurrentUserPrimarySchedule,
} from "../../actions";
import ScheduleSelectorDropdown from "./ScheduleSelectorDropdown";

import { Section, User, Schedule as ScheduleType } from "../../types";
import ScheduleDisplay from "./ScheduleDisplay";
import { fetchFriendPrimarySchedule } from "../../actions/friendshipUtil";

const ScheduleContainer = styled.div`
    display: flex;
    flex-direction: column;
    flex-basis: 0;
    flex-grow: 1;
    flex-shrink: 1;
    padding: 0;
`;

const ScheduleDropdownHeader = styled.h3`
    display: flex;
    font-weight: 700;
    margin-bottom: 0.5rem;
    color: #333;
`;

interface ScheduleProps {
    user: User;
    activeScheduleName: string;
    currScheduleData: { sections: Section[] };
    allSchedules: ScheduleType[];
    primaryScheduleId: string;
    removeSection: (idDashed: string) => void;
    focusSection: (id: string) => void;
    switchSchedule: (scheduleName: string) => void;
    setReadOnly: (readOnly: boolean) => void;
    schedulesMutator: {
        setPrimary: (user: User, scheduleId: string) => void;
        copy: (scheduleName: string) => void;
        remove: (user: User, scheduleName: string, scheduleId: string) => void;
        rename: (oldName: string) => void;

        // NOT IN ORIGINAL PROPS
        createSchedule: () => void;
        addFriend: () => void;
        showRequests: () => void;
    };
    setTab?: (_: number) => void;
}

const Schedule = ({
    user,
    currScheduleData,
    allSchedules,
    primaryScheduleId,
    removeSection,
    focusSection,
    switchSchedule,
    schedulesMutator,
    activeScheduleName,
    setReadOnly,
}: ScheduleProps) => {
    const [displayState, setDisplayState] = useState("Self");
    const [friendPrimarySchedule, setFriendPrimarySchedule] = useState<{
        sections: Section[];
    }>();

    useEffect(() => {
        setReadOnly(displayState !== "Self");
    }, [displayState]);

    return (
        <ScheduleContainer>
            <ScheduleDropdownHeader>
                <ScheduleSelectorDropdown
                    user={user}
                    allSchedules={allSchedules}
                    activeName={activeScheduleName}
                    primaryScheduleId={primaryScheduleId}
                    displayState={displayState}
                    displayOwnSchedule={(name: string) => {
                        switchSchedule(name);
                        setDisplayState("Self");
                    }}
                    displayFriendSchedule={(username: string) => {
                        fetchFriendPrimarySchedule(
                            username,
                            setDisplayState,
                            setFriendPrimarySchedule
                        );
                    }}
                    mutators={schedulesMutator}
                />
            </ScheduleDropdownHeader>
            {displayState === "Self" && (
                <ScheduleDisplay
                    readOnly={false}
                    displayState={displayState}
                    schedData={currScheduleData}
                    focusSection={focusSection}
                    removeSection={removeSection}
                />
            )}
            {displayState !== "Self" && friendPrimarySchedule && (
                <ScheduleDisplay
                    readOnly={true}
                    displayState={displayState}
                    schedData={friendPrimarySchedule}
                    focusSection={focusSection}
                    removeSection={removeSection}
                />
            )}
        </ScheduleContainer>
    );
};

const mapStateToProps = (state: any) => {
    return {
        user: state.login.user,
        activeScheduleName: state.schedule.scheduleSelected,
        primaryScheduleId: state.schedule.primaryScheduleId,
        allSchedules: state.schedule.schedules,
        currScheduleData:
            state.schedule.schedules[state.schedule.scheduleSelected],
    };
};

const mapDispatchToProps = (dispatch: ThunkDispatch<any, any, any>) => ({
    removeSection: (idDashed: string) => dispatch(removeSchedItem(idDashed)),
    focusSection: (id: string) => dispatch(fetchCourseDetails(id)),
    switchSchedule: (scheduleName: string) =>
        dispatch(changeSchedule(scheduleName)),
    setReadOnly: (displayingFriend: boolean) =>
        dispatch(setStateReadOnly(displayingFriend)),
    schedulesMutator: {
        copy: (scheduleName: string) =>
            dispatch(createScheduleOnBackend(scheduleName)),
        remove: (user: User, scheduleName: string, scheduleId: string) =>
            dispatch(deleteScheduleOnBackend(user, scheduleName, scheduleId)),
        rename: (oldName: string) =>
            dispatch(
                openModal(
                    "RENAME_SCHEDULE",
                    { scheduleName: oldName, defaultValue: oldName },
                    "Rename Schedule"
                )
            ),
        createSchedule: () =>
            dispatch(
                openModal(
                    "CREATE_SCHEDULE",
                    {
                        defaultValue: "Schedule name",
                    },
                    "Create Schedule"
                )
            ),
        addFriend: () =>
            dispatch(
                openModal("ADD_FRIEND", { defaultValue: "" }, "Add New Friend")
            ),
        showRequests: () =>
            dispatch(openModal("SHOW_REQUESTS", {}, "PENDING REQUESTS")),
        setPrimary: (user: User, scheduleId: string) =>
            dispatch(setCurrentUserPrimarySchedule(user, scheduleId)),
    },
});

export default connect(mapStateToProps, mapDispatchToProps)(Schedule);
