import { doAPIRequest, setStateReadOnly } from ".";
import getCsrf from "../components/csrf";

export const SWITCH_ACTIVE_FRIEND = "SWITCH_ACTIVE_FRIEND";
export const UPDATE_FRIENDSHIPS_ON_FRONTEND = "UPDATE_FRIENDSHIPS_ON_FRONTEND";

export const switchActiveFriend = (friend, found, sections) => ({
    type: SWITCH_ACTIVE_FRIEND,
    friend,
    found,
    sections,
});

export const updateFriendshipsOnFrontend = (
    backendRequestsReceived,
    backendRequestsSent,
    backendAcceptedFriends
) => ({
    type: UPDATE_FRIENDSHIPS_ON_FRONTEND,
    received: backendRequestsReceived,
    sent: backendRequestsSent,
    friends: backendAcceptedFriends,
});

/**
 * Pulls user's friends from the backend
 */
export const fetchBackendFriendships = (user, activeFriendName) => (
    dispatch
) => {
    doAPIRequest("/base/friendship")
        .then((res) => {
            return res.json();
        })
        .then((friendships) => {
            const backendRequestsReceived = [];
            const backendRequestsSent = [];
            const backendAcceptedFriends = [];

            friendships.forEach((fs) => {
                if (fs.status === "S" && fs.sender.username !== user.username) {
                    backendRequestsReceived.push(fs);
                } else if (
                    fs.status === "S" &&
                    fs.sender.username === user.username
                ) {
                    backendRequestsSent.push(fs);
                } else if (fs.status === "A") {
                    backendAcceptedFriends.push(
                        fs.recipient.username === user.username
                            ? fs.sender
                            : fs.recipient
                    );
                }
            });

            dispatch(
                updateFriendshipsOnFrontend(
                    backendRequestsReceived,
                    backendRequestsSent,
                    backendAcceptedFriends
                )
            );

            if (
                !backendAcceptedFriends.reduce(
                    (acc, friend) =>
                        acc || friend.username === activeFriendName,
                    false
                )
            ) {
                dispatch(setStateReadOnly(false));
            }
        })
        .catch((error) => console.log(error));
};

export const deleteFriendshipOnBackend = (
    user,
    friendPennkey,
    activeFriendName
) => (dispatch) => {
    const init = {
        method: "DELETE",
        credentials: "include",
        mode: "same-origin",
        headers: {
            Accept: "application/json",
            "Content-Type": "application/json",
            "X-CSRFToken": getCsrf(),
        },
        body: JSON.stringify({
            pennkey: friendPennkey,
        }),
    };
    doAPIRequest("/base/friendship/", init)
        .then(() => {
            dispatch(fetchBackendFriendships(user, activeFriendName));
        })
        .catch((error) => console.log(error));
};

export const sendFriendRequest = (
    user,
    friendPennkey,
    activeFriendName,
    onComplete
) => (dispatch) => {
    const init = {
        method: "POST",
        credentials: "include",
        mode: "same-origin",
        headers: {
            Accept: "application/json",
            "Content-Type": "application/json",
            "X-CSRFToken": getCsrf(),
        },
        body: JSON.stringify({
            pennkey: friendPennkey,
        }),
    };
    doAPIRequest("/base/friendship/", init).then((res) => {
        dispatch(fetchBackendFriendships(user, activeFriendName));
        onComplete(res);
    });
};

export const fetchFriendPrimarySchedule = (friend) => (dispatch) => {
    doAPIRequest("/plan/primary-schedules/")
        .then((res) => res.json())
        .then((schedules) => {
            return schedules.find(
                (sched) => sched.user.username === friend.username
            );
        })
        .then((foundSched) => {
            if (foundSched) {
                dispatch(
                    switchActiveFriend(
                        foundSched.user,
                        true,
                        foundSched.schedule.sections
                    )
                );
            } else {
                dispatch(switchActiveFriend(friend, false, []));
            }
            dispatch(setStateReadOnly(true));
        })
        .catch((error) => console.log(error));
};
