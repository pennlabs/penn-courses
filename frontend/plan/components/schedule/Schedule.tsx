import React from "react";
import styled from "styled-components";
import { connect } from "react-redux";
import { ThunkDispatch } from "redux-thunk";

import {
  removeSchedItem,
  fetchCourseDetails,
  changeMySchedule,
  createScheduleOnBackend,
  deleteScheduleOnBackend,
  openModal,
  setCurrentUserPrimarySchedule,
} from "../../actions";
import ScheduleSelectorDropdown from "./ScheduleSelectorDropdown";
import {
  Section,
  Break,
  User,
  Schedule as ScheduleType,
  FriendshipState,
} from "../../types";
import ScheduleDisplay from "./ScheduleDisplay";
import {
  deleteFriendshipOnBackend,
  fetchBackendFriendships,
  fetchFriendPrimarySchedule,
  unsetActiveFriend
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
  currScheduleData: { sections: Section[], breaks: Break[] };
  allSchedules: { [key: string]: ScheduleType };
  primaryScheduleId: string;
  readOnly: boolean;
  friendshipState: FriendshipState;
  removeSection: (idDashed: string, idType: string) => void;
  focusSection: (id: string) => void;
  changeMySchedule: (scheduleName: string) => void;
  unsetActiveFriend: () => void;
  setTab?: (_: number) => void;
  friendshipMutators: {
    fetchFriendSchedule: (friend: User) => void;
    fetchBackendFriendships: (user: User) => void;
    deleteFriendshipOnBackend: (
      user: User,
      friendPennkey: string
    ) => void;
  };
  schedulesMutator: {
    setPrimary: (user: User, scheduleId: string | null) => void;
    copy: (scheduleName: string, sections: Section[]) => void;
    remove: (user: User, scheduleName: string, scheduleId: string) => void;
    rename: (oldName: string) => void;
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
  changeMySchedule,
  unsetActiveFriend,
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
            changeMySchedule(name);
            unsetActiveFriend();
          }}
          friendshipMutators={friendshipMutators}
          schedulesMutators={schedulesMutator}
        />
      </ScheduleDropdownHeader>
      <ScheduleDisplay
        schedName={activeScheduleName}
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
  removeSection: (idDashed: string, type: string) =>
    dispatch(removeSchedItem(idDashed, type)),
  focusSection: (id: string) => dispatch(fetchCourseDetails(id)),
  changeMySchedule: (scheduleName: string) =>
    dispatch(changeMySchedule(scheduleName)),
  unsetActiveFriend: () => dispatch(unsetActiveFriend()),
  friendshipMutators: {
    fetchFriendSchedule: (friend: User) =>
      dispatch(fetchFriendPrimarySchedule(friend)),
    fetchBackendFriendships: (user: User) =>
      dispatch(fetchBackendFriendships(user)),
    deleteFriendshipOnBackend: (user: User, friendPennkey: string) =>
      dispatch(deleteFriendshipOnBackend(user, friendPennkey)),
  },
  schedulesMutator: {
    setPrimary: (user: User, scheduleId: string | null) =>
      dispatch(setCurrentUserPrimarySchedule(user, scheduleId)),
    copy: (scheduleName: string, sections: Section[]) =>
      dispatch(createScheduleOnBackend(scheduleName, sections)),
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
