import { doAPIRequest } from ".";
import getCsrf from "../components/csrf";

function compareFriendships(a, b) {
    if (a.getTime() < b.getTime() && a < b) {
        return -1;
    } else {
        return 1;
    }
}

/**
 * Pulls user's friends from the backend
 */
export const fetchFriendships = (callback, user) => {
    doAPIRequest("/base/friendship")
        .then((res) => {
            return res.json();
        })
        .then((friendships) => {
            console.log(friendships);
            const requestsReceived = friendships.filter(
                (fs) => fs.status == "S" && fs.sender.username != user.username
            );

            const requestsSent = friendships.filter(
                (fs) => fs.status == "S" && fs.sender.username == user.username
            );

            const friendshipsAccepted = friendships.filter(
                (fs) => fs.status == "A"
            );

            callback({
                received: requestsReceived,
                sent: requestsSent,
                accepted: friendshipsAccepted,
            });
        })
        .catch((error) => console.log(error));
};

export const sendFriendRequest = (pennkey) => {
    const pennIdObj = {
        pennkey: pennkey,
    };

    const init = {
        method: "POST",
        credentials: "include",
        mode: "same-origin",
        headers: {
            Accept: "application/json",
            "Content-Type": "application/json",
            "X-CSRFToken": getCsrf(),
        },
        body: JSON.stringify(pennIdObj),
    };
    return doAPIRequest("/base/friendship/", init).then((res) => {
        if (res.status == 200) {
            // request accepted
            // blob friendship created successfully?
            return {
                message: "",
                error: false,
            };
        } else if (res.status == 201) {
            // friendship not requested before
            // request created
            // blob friendship request sent

            // friendship requested before
            // request created
            // blob friendship request sent

            return {
                message: "",
                error: false,
            };
        } else if (res.status == 404) {
            // pennkey not found
            // blob pennkey not found

            return {
                message: "User not found.",
                error: true,
            };
        } else if (res.status == 409) {
            // request pending
            // blob friendship request pending
            return {
                message: "Friendship request still pending.",
                error: true,
            };
        }
        return { message: "", error: false };
    });
};

export const rejectFriendRequest = (pennkey) => {
    const pennIdObj = {
        pennkey: pennkey,
    };

    const init = {
        method: "DELETE",
        credentials: "include",
        mode: "same-origin",
        headers: {
            Accept: "application/json",
            "Content-Type": "application/json",
            "X-CSRFToken": getCsrf(),
        },
        body: JSON.stringify(pennIdObj),
    };
    return doAPIRequest("/base/friendship/", init).catch((error) =>
        console.log(error)
    );
};
