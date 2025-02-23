import React from "react";
import dynamic from "next/dynamic";
import {
    renameSchedule,
    downloadSchedule,
    createScheduleOnBackend,
    updateContactInfo,
    registerAlertItem,
    reactivateAlertItem,
} from "../../actions";
import {
    sendFriendRequest,
    deleteFriendshipOnBackend,
} from "../../actions/friendshipUtil";
import NameScheduleModalInterior from "./AddScheduleFriendsModalInterior";
import PendingRequestsModalInterior from "./PendingRequestsModalInterior";
import WelcomeModalInterior from "./WelcomeModalInterior";
import CalendarModal from "./CalendarModal";
import AlertFormModal from "./AlertFormModal";

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
export const generateModalInterior = (reduxState) => {
    const Map = dynamic(() => import("./MapModal"), {
        ssr: false,
    });

    switch (reduxState.modals.modalKey) {
        case "SEMESTER_FETCH_ERROR":
            return (
                <div>
                    <p>Please refresh the page.</p>
                </div>
            );
        case "RENAME_SCHEDULE":
            return (
                <NameScheduleModalInterior
                    buttonName="Rename"
                    existingData={Object.keys(reduxState.schedule.schedules)}
                    requestType="schedule"
                    overwriteDefault={true}
                />
            );
        case "CREATE_SCHEDULE":
            return (
                <NameScheduleModalInterior
                    buttonName="Create"
                    existingData={Object.keys(reduxState.schedule.schedules)}
                    requestType="schedule"
                    overwriteDefault={true}
                />
            );
        case "ADD_FRIEND":
            return (
                <NameScheduleModalInterior
                    user={reduxState.login.user}
                    buttonName="Request"
                    existingData={reduxState.friendships.acceptedFriends}
                    requestType="friend"
                    placeholder="Enter your friend's PennKey"
                />
            );
        case "SHOW_REQUESTS":
            return (
                <PendingRequestsModalInterior
                    user={reduxState.login.user}
                    received={reduxState.friendships.requestsReceived}
                    sent={reduxState.friendships.requestsSent}
                />
            );
        case "WELCOME":
            return (
                <WelcomeModalInterior
                    usedScheduleNames={Object.keys(
                        reduxState.schedule.schedules
                    )}
                />
            );
        case "DOWNLOAD_SCHEDULE":
            return (
                <CalendarModal
                    $schedulePk={
                        reduxState.schedule.schedules[
                            reduxState.schedule.scheduleSelected
                        ].id
                    }
                />
            );
        case "MULTITAB":
            return (
                <div>
                    <p>
                        You have another tab of Penn Course Plan open. Please
                        use Penn Course Plan in a single tab.
                    </p>
                </div>
            );
        case "ALERT_FORM":
            return (
                <AlertFormModal contactInfo={reduxState.alerts.contactInfo} />
            );
        case "MAP":
            return <Map />;
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
            return {
                namingFunction: (newName) =>
                    dispatch(renameSchedule(modalProps.scheduleName, newName)),
            };
        case "CREATE_SCHEDULE":
            return {
                namingFunction: (newName) =>
                    dispatch(createScheduleOnBackend(newName)),
            };
        case "ADD_FRIEND":
            return {
                sendFriendRequest: (user, friendPennkey, onComplete) =>
                    dispatch(
                        sendFriendRequest(user, friendPennkey, onComplete)
                    ),
            };
        case "SHOW_REQUESTS":
            return {
                sendFriendRequest: (user, friendPennkey) =>
                    dispatch(
                        sendFriendRequest(user, friendPennkey, (res) => {
                            if (!res.ok) {
                                console.log(res);
                            }
                        })
                    ),
                deleteFriendshipOnBackend: (user, friendPennkey) =>
                    dispatch(deleteFriendshipOnBackend(user, friendPennkey)),
            };
        case "DOWNLOAD_SCHEDULE":
            return {
                namingFunction: (newName) =>
                    dispatch(downloadSchedule(newName)),
            };
        case "ALERT_FORM":
            return {
                onContactInfoChange: (email, phone) =>
                    dispatch(updateContactInfo({ email, phone })),
                addAlert: () => {
                    if (modalProps.alertId) {
                        dispatch(
                            reactivateAlertItem(
                                modalProps.sectionId,
                                modalProps.alertId
                            )
                        );
                    } else {
                        dispatch(registerAlertItem(modalProps.sectionId));
                    }
                },
            };
        default:
            return {};
    }
};
