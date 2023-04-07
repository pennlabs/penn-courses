import React from "react";
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

import {
    Section,
    User,
    Schedule as ScheduleType,
    FriendshipState,
} from "../../types";
import ScheduleDisplay from "./ScheduleDisplay";
import {
    deleteFriendshipOnBackend,
    fetchBackendFriendships,
    fetchFriendPrimarySchedule,
} from "../../actions/friendshipUtil";

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
    readOnly: boolean;
    friendshipState: FriendshipState;
    removeSection: (idDashed: string) => void;
    focusSection: (id: string) => void;
    switchSchedule: (scheduleName: string) => void;
    setStateReadOnly: (readOnly: boolean) => void;
    setTab?: (_: number) => void;
    friendshipMutators: {
        fetchFriendSchedule: (friend: User) => void;
        fetchBackendFriendships: (user: User, activeFriendName: string) => void;
        deleteFriendshipOnBackend: (
            user: User,
            friendPennkey: string,
            activeFriendName: string
        ) => void;
    };
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
}

const Schedule = ({
    user,
    currScheduleData,
    allSchedules,
    primaryScheduleId,
    friendshipState,
    readOnly,
    removeSection,
    focusSection,
    switchSchedule,
    setStateReadOnly,
    setTab,
    friendshipMutators,
    schedulesMutator,
    activeScheduleName,
}: ScheduleProps) => {
    return (
        <ScheduleContainer>
            <ScheduleDropdownHeader>
                <ScheduleSelectorDropdown
                    user={user}
                    allSchedules={allSchedules}
                    activeName={activeScheduleName}
                    friendshipState={friendshipState}
                    primaryScheduleId={primaryScheduleId}
                    readOnly={readOnly}
                    displayOwnSchedule={(name: string) => {
                        switchSchedule(name);
                        setStateReadOnly(false);
                    }}
                    friendshipMutators={friendshipMutators}
                    schedulesMutators={schedulesMutator}
                />
            </ScheduleDropdownHeader>
            <ScheduleDisplay
                schedData={currScheduleData}
                friendshipState={friendshipState}
                readOnly={readOnly}
                focusSection={focusSection}
                removeSection={removeSection}
                setTab={setTab}
            />
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
        friendshipState: state.friendships,
        readOnly: state.schedule.readOnly,
    };
};

const mapDispatchToProps = (dispatch: ThunkDispatch<any, any, any>) => ({
    removeSection: (idDashed: string) => dispatch(removeSchedItem(idDashed)),
    focusSection: (id: string) => dispatch(fetchCourseDetails(id)),
    switchSchedule: (scheduleName: string) =>
        dispatch(changeSchedule(scheduleName)),
    setStateReadOnly: (displayingFriend: boolean) =>
        dispatch(setStateReadOnly(displayingFriend)),
    friendshipMutators: {
        fetchFriendSchedule: (friend: User) =>
            dispatch(fetchFriendPrimarySchedule(friend)),
        fetchBackendFriendships: (user: User, activeFriendName: string) =>
            dispatch(fetchBackendFriendships(user, activeFriendName)),
        deleteFriendshipOnBackend: (
            user: User,
            friendPennkey: string,
            activeFriendName: string
        ) =>
            dispatch(
                deleteFriendshipOnBackend(user, friendPennkey, activeFriendName)
            ),
    },
    schedulesMutator: {
        setPrimary: (user: User, scheduleId: string) =>
            dispatch(setCurrentUserPrimarySchedule(user, scheduleId)),
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
            dispatch(openModal("SHOW_REQUESTS", {}, "Pending Requests")),
    },
});

export default connect(mapStateToProps, mapDispatchToProps)(Schedule);
